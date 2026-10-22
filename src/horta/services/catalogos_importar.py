"""Importación dos catálogos oficiais do FEGA (portal público SIEX, XLSX).

Idempotente: o mesmo ficheiro (mesmo sha256) non se reimporta. Nunca borra
códigos: os que desaparecen quedan con data_baixa (conservación legal).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex

# clave interna -> (ficheiro no portal FEGA, columna do código, columna da descrición;
# None = 2ª columna). Verificado contra os ficheiros descargados o 2026-10-22.
CATALOGOS_XERAIS: dict[str, tuple[str, str, str | None]] = {
    "praga": ("PLAGAS", "Código SIEX", "Nombre científico"),
    "enfermidade": ("ENFERMEDADES", "Código SIEX", "Nombre científico"),
    "mala_herba": ("MALAS_HIERBAS", "Código SIEX", "Nombre científico"),
    "regulador": ("REGULADORES_CRECIMIENTO", "Código SIEX",
                  "Nombre científico / Denominación en inglés"),
    "xustificacion": ("JUSTIFICACION_ACTUACION", "Código SIEX", None),
    "estado_fenoloxico": ("EST_FENOLOGICO", "Código SIEX", "Estado fenológico"),
    "unidade_medida": ("UNIDADES_MEDIDA", "Código SIEX", None),
    "eficacia": ("EFICACIA_TRATAMIENTO", "Código SIEX", None),
    "tipo_produto": ("TIPO_PRODFITO", "Código SIEX", None),
    "tipo_medida_fito": ("TIPO_MEDIDA_FITOSANITARIA", "Código SIEX", None),
    "tipo_maquinaria_une": ("TIPO_MAQUINA_UNE", "Código UNE", None),
    "tipo_enerxia": ("TIPENERGIA", "Código", None),
    "boas_practicas": ("BUENAS_PRACTICAS_AMBITOS", "Código SIEX", None),
}


@dataclass
class InformeImportacion:
    catalogo: str
    altas: int = 0
    baixas: int = 0
    cambios: int = 0
    xa_importado: bool = False


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _ler_xlsx(ruta: Path) -> tuple[list[str], list[dict[str, Any]]]:
    wb = load_workbook(ruta, read_only=False, data_only=True)
    ws = wb.active
    filas = [f for f in ws.iter_rows(values_only=True) if any(c is not None for c in f)]
    cabeceira = [str(c).strip() if c is not None else "" for c in filas[0]]
    return cabeceira, [dict(zip(cabeceira, f)) for f in filas[1:]]


def _data(valor: Any) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), "%d/%m/%Y").date()


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _codigo(valor: Any) -> str:
    texto = str(valor).strip()
    return texto[:-2] if texto.endswith(".0") else texto


def _nova_version(
    session: Session, catalogo: str, ruta: Path, filas: int
) -> CatalogoVersion | None:
    sha = _sha256(ruta)
    if session.query(CatalogoVersion).filter_by(catalogo=catalogo, sha256=sha).first():
        return None
    version = CatalogoVersion(catalogo=catalogo, nome_ficheiro=ruta.name, sha256=sha, filas=filas)
    session.add(version)
    session.flush()
    return version


def importar_catalogo(
    session: Session, catalogo: str, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    if catalogo not in CATALOGOS_XERAIS:
        raise ValueError(f"Catálogo descoñecido: {catalogo}")
    hoxe = hoxe or date.today()
    _, columna_codigo, columna_descricion = CATALOGOS_XERAIS[catalogo]
    cabeceira, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo=catalogo)
    version = _nova_version(session, catalogo, ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    columna = columna_descricion or cabeceira[1]
    existentes = {v.codigo: v for v in session.query(CatalogoValor).filter_by(catalogo=catalogo)}
    vistos: set[str] = set()
    for fila in filas:
        codigo = _codigo(fila[columna_codigo])
        vistos.add(codigo)
        datos = {
            "descricion": _texto(fila.get(columna)) or "",
            "codigo_eppo": _texto(fila.get("EPPO cd")),
            "categoria": _texto(fila.get("Categoría")),
            "data_alta": _data(fila.get("Fecha de alta")),
            "data_baixa": _data(fila.get("Fecha de baja")),
        }
        actual = existentes.get(codigo)
        if actual is None:
            session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, version_id=version.id,
                                      **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
    for codigo, valor in existentes.items():
        if codigo not in vistos and valor.data_baixa is None:
            valor.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe


def importar_cultivos(
    session: Session, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    hoxe = hoxe or date.today()
    _, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo="cultivo")
    version = _nova_version(session, "cultivo", ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    existentes = {c.codigo: c for c in session.query(CultivoSiex)}
    vistos: set[int] = set()
    for fila in filas:
        codigo = int(_codigo(fila["Código"]))
        vistos.add(codigo)
        datos = {
            "nome_oficial": _texto(fila.get("Cultivo")) or "",
            "nome_latin": _texto(fila.get("Latín")),
            "codigo_eppo": _texto(fila.get("EPPO")),
            "codigo_upov": _texto(fila.get("C. UPOV")),
            "horticola": _texto(fila.get("Hortícola")) == "SI",
            "integrado": _texto(fila.get("Integrado")) == "SI",
            "data_alta": _data(fila.get("Fecha de alta")),
            "data_baixa": _data(fila.get("Fecha de baja")),
        }
        actual = existentes.get(codigo)
        if actual is None:
            session.add(CultivoSiex(codigo=codigo, version_id=version.id, **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
    for codigo, cultivo in existentes.items():
        if codigo not in vistos and cultivo.data_baixa is None:
            cultivo.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe


def importar_variedades(
    session: Session, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    hoxe = hoxe or date.today()
    _, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo="variedade")
    version = _nova_version(session, "variedade", ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    cultivos = {c for (c,) in session.query(CultivoSiex.codigo)}
    existentes = {(v.cultivo_codigo, v.codigo): v for v in session.query(VariedadeSiex)}
    vistos: set[tuple[int, int]] = set()
    for fila in filas:
        cultivo = int(_codigo(fila["Código cultivo"]))
        if cultivo not in cultivos:
            continue  # variedade dun cultivo que non está no catálogo de cultivos
        clave = (cultivo, int(_codigo(fila["Código Variedad/ Especie/ Tipo"])))
        vistos.add(clave)
        nome = _texto(fila.get("Variedad/ Especie/ Tipo")) or ""
        baixa = _data(fila.get("Fecha de baja"))
        actual = existentes.get(clave)
        if actual is None:
            session.add(VariedadeSiex(cultivo_codigo=clave[0], codigo=clave[1], nome_oficial=nome,
                                      data_baixa=baixa, version_id=version.id))
            informe.altas += 1
        elif actual.nome_oficial != nome or actual.data_baixa != baixa:
            actual.nome_oficial, actual.data_baixa, actual.version_id = nome, baixa, version.id
            informe.cambios += 1
    for clave, variedade in existentes.items():
        if clave not in vistos and variedade.data_baixa is None:
            variedade.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe

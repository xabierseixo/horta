# Tarefa 072c — Catálogos: recoñecer os ficheiros e revisalos en lote

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072a3. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Servizo que recoñece cada ficheiro do FEGA polo contido (código do portal, nome do ZIP anual ou título da folla), expande ZIP e revisa ou aplica un lote nunha soa transacción. Probado no navegador e co rexistro real. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/catalogos_ficheiros.py` (**ficheiro novo**)
- `tests/services/test_catalogos_ficheiros.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/catalogos_ficheiros.py`

Contido completo:
```python
"""Recoñece os ficheiros de catálogos do FEGA e impórtaos en lote, con revisión previa.

Os ficheiros chegan do portal (PLAGAS.xlsx), do ZIP anual da circular PAC («20260311
Actividad agraria.xlsx», folla «Datos») ou co nome que lle poña o navegador, así que se
recoñecen polo contido: código do portal, nome sen data ou título da folla (Excel córtao
aos 31 caracteres). Deseño: docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md
"""

from __future__ import annotations

import re
import unicodedata
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoVersion
from horta.services.catalogos_importar import (
    InformeImportacion,
    importar_catalogo,
    importar_cultivos,
    importar_variedades,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes_importar import importar_fertilizantes

DIRECTORIO_APP = Path(__file__).resolve().parent.parent / "data" / "catalogos_fega"
PORTAL_FEGA = "https://www3.sede.fega.gob.es/bdcsixpor/catalogos"

# clave -> (código no portal do FEGA, título da folla, nome en galego). Os cultivos van
# antes das variedades: a importación das variedades precisa os cultivos.
CATALOGOS_APP: dict[str, tuple[str, str, str]] = {
    "cultivo": ("PRODUCTOS", "Cultivo", "Cultivos"),
    "variedade": ("VARIEDAD_ESPECIE_TIPO", "Variedad  Especie  Tipo", "Variedades"),
    "fertilizante": ("DETALLE_MATERIAL_FERT", "Detalle material fertilizante", "Abonos"),
    "praga": ("PLAGAS", "Artrópodos y gasterópodos", "Pragas"),
    "enfermidade": ("ENFERMEDADES", "Enfermedades", "Enfermidades"),
    "mala_herba": ("MALAS_HIERBAS", "Malas hierbas", "Malas herbas"),
    "regulador": ("REGULADORES_CRECIMIENTO", "Reguladores de crecimiento, ro",
                  "Reguladores de crecemento"),
    "xustificacion": ("JUSTIFICACION_ACTUACION", "Justificación de la actuación",
                      "Xustificacións"),
    "estado_fenoloxico": ("EST_FENOLOGICO", "Estado fenológico", "Estados fenolóxicos"),
    "unidade_medida": ("UNIDADES_MEDIDA", "Unidades de medida", "Unidades de medida"),
    "eficacia": ("EFICACIA_TRATAMIENTO", "Eficacia del tratamiento", "Eficacia"),
    "tipo_produto": ("TIPO_PRODFITO", "Tipo de producto fitosanitario", "Tipos de produto"),
    "tipo_medida_fito": ("TIPO_MEDIDA_FITOSANITARIA", "Tipo de medida fitosanitaria",
                         "Medidas non químicas"),
    "tipo_maquinaria_une": ("TIPO_MAQUINA_UNE", "Tipo de maquinaria UNE", "Maquinaria UNE"),
    "tipo_enerxia": ("TIPENERGIA", "Tipo de energía", "Tipos de enerxía"),
    "boas_practicas": ("BUENAS_PRACTICAS_AMBITOS", "Buenas prácticas", "Boas prácticas"),
    "sistema_cultivo": ("SIST_CULTIVO", "Sistema de cultivo", "Sistemas de cultivo"),
    "destino_cultivo": ("DESTINO_CULTIVO", "Destino del cultivo", "Destinos do cultivo"),
    "certificacion_ecoloxica": ("TIPO_CERTIFICACION_ECOLOGICA",
                                "Certificación producción ecoló", "Certificación ecolóxica"),
    "sistema_explotacion": ("SIST_EXPLOTACION", "Sistema de explotación",
                            "Sistemas de explotación"),
    "actividade_agraria": ("ACTIVIDAD_AGRARIA", "Actividad agraria", "Actividade agraria"),
    "causa_baixa": ("CAUSA_BAJA", "Causas de baja", "Causas de baixa"),
    "procedencia_material_vexetal": ("PROC_VEGETAL", "Procedencia del material veget",
                                     "Procedencia do material vexetal"),
    "tipo_cobertura_solo": ("TIPO_COBERTURA_SUELO", "Tipo de cobertura del suelo",
                            "Cobertura do solo"),
    "rexime_tenencia": ("REGIMEN_TENENCIA", "Régimen de tenencia", "Réxime de tenencia"),
    "destino_colleita": ("DEST_COSECHA", "Finalidad de la cosecha", "Destino da colleita"),
    "destino_restos": ("DEST_RES_VEG", "Destino del resto vegetal", "Destino dos restos"),
    "material_fertilizante": ("MAT_FERTI", "Material fertilizante", "Materiais fertilizantes"),
    "tipo_fertilizacion": ("TIPO_FERITILIZACION", "Tipo de fertilización",
                           "Tipos de fertilización"),
    "metodo_fertilizacion": ("METODO_APLICACION_FERTILIZANTE", "Método de aplicación de fertil",
                             "Métodos de abonado"),
    "tratamento_estercos": ("TRAT_ESTIERCOLES", "Tratamiento de estiércoles",
                            "Tratamento de estercos"),
    "material_analizado": ("MATERIAL_ANALIZADO", "Material analizado", "Material analizado"),
    "tipo_analise": ("TIPO_ANALISIS", "Tipo de análisis", "Tipos de análise"),
    "orixe_auga": ("ORIGEN_AGUA_RIEGO", "Procedencia del agua de riego", "Orixe da auga"),
    "sistema_rega": ("SIST_RIEGO", "Sistema de riego", "Sistemas de rega"),
    "substancia_activa": ("SUST_ACTIVAS", "Sustancias activas detectadas ",
                          "Substancias activas"),
    "tipo_labor": ("TIPO_LABOR", "Tipo de labor", "Labores"),
    "especie_animal": ("ESPECIE_ANIMAL", "Especies animales", "Especies animais"),
    "raza": ("RAZAS", "Catálogo oficial de razas de g", "Razas"),
}
_LONXITUDE_CORTADA = 29  # Excel corta o título da folla aos 31 caracteres


@dataclass
class Revision:
    ficheiro: str
    catalogo: str | None
    informe: InformeImportacion | None = None
    erro: str | None = None


def _normal(texto: str) -> str:
    sen_acentos = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                          if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", sen_acentos).strip()


def _coincide(nome: str, titulo: str) -> bool:
    nome, titulo = _normal(nome), _normal(titulo)
    return bool(nome) and (nome == titulo or (len(titulo) >= _LONXITUDE_CORTADA
                                              and nome.startswith(titulo)))


def identificar_catalogo(ruta: Path) -> str | None:
    """Clave do catálogo dun ficheiro do FEGA, ou None se non é un que use a app."""
    nome = re.sub(r"^\d{8}[ _-]*", "", ruta.stem)
    nome = re.sub(r"\s*integrado\s+si\s*$", "", nome, flags=re.I)
    for clave, (codigo, titulo, _) in CATALOGOS_APP.items():
        if _normal(ruta.stem) == _normal(codigo) or _coincide(nome, titulo):
            return clave
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            folla = load_workbook(ruta, read_only=True).active.title
    except Exception:
        return None
    return next((clave for clave, (_, titulo, _) in CATALOGOS_APP.items()
                 if _coincide(folla, titulo)), None)


def expandir(rutas: list[Path], destino: Path) -> list[Path]:
    """Os .xlsx tal cal e o contido dos .zip, extraído en destino."""
    saida: list[Path] = []
    for ruta in rutas:
        if ruta.suffix.lower() == ".zip":
            with zipfile.ZipFile(ruta) as z:
                for membro in z.namelist():
                    if membro.lower().endswith(".xlsx") and not membro.startswith("__MACOSX"):
                        ficheiro = destino / Path(membro).name
                        ficheiro.write_bytes(z.read(membro))
                        saida.append(ficheiro)
        elif ruta.suffix.lower() == ".xlsx":
            saida.append(ruta)
    return saida


def _importar(session: Session, clave: str, ruta: Path, aplicar: bool) -> InformeImportacion:
    if clave == "cultivo":
        return importar_cultivos(session, ruta, aplicar=aplicar)
    if clave == "variedade":
        return importar_variedades(session, ruta, aplicar=aplicar)
    if clave == "fertilizante":
        return importar_fertilizantes(session, ruta, aplicar=aplicar)
    return importar_catalogo(session, clave, ruta, aplicar=aplicar)


def revisar(session: Session, rutas: list[Path], aplicar: bool = False) -> list[Revision]:
    """Altas, baixas e cambios de cada ficheiro. Con aplicar=False non se garda nada: o lote
    revísase nunha soa transacción que se desfai ao final."""
    identificados: list[tuple[str, Path]] = []
    revisions: list[Revision] = []
    for ruta in rutas:
        clave = identificar_catalogo(ruta)
        if clave is None:
            revisions.append(Revision(ruta.name, None, erro="Non é un catálogo dos que usa a "
                                                            "app (ou non o recoñezo)"))
        else:
            identificados.append((clave, ruta))
    orde = list(CATALOGOS_APP)
    for clave, ruta in sorted(identificados, key=lambda par: orde.index(par[0])):
        try:
            revisions.append(Revision(ruta.name, clave, _importar(session, clave, ruta,
                                                                   aplicar)))
        except (OperacionNonPermitidaError, KeyError, ValueError) as erro:
            session.rollback()
            texto = str(erro) if isinstance(erro, OperacionNonPermitidaError) else (
                f"Non se puido ler {ruta.name} ({erro}). O FEGA puido cambiar o formato: hai "
                "que adaptar a app.")
            revisions.append(Revision(ruta.name, clave, erro=texto))
    if not aplicar:
        session.rollback()
    return revisions


def importar_da_app(session: Session) -> list[Revision]:
    """Importa os catálogos que leva a propia app (instalación nova ou sen internet)."""
    return revisar(session, sorted(DIRECTORIO_APP.glob("*.xlsx")), aplicar=True)


def sen_catalogos(session: Session) -> bool:
    return session.query(CatalogoVersion.id).filter(
        CatalogoVersion.catalogo.in_(list(CATALOGOS_APP))).first() is None
```

### Paso 2 — crear o ficheiro `tests/services/test_catalogos_ficheiros.py`

Contido completo:
```python
import zipfile

from openpyxl import Workbook

from horta.models.catalogo import CatalogoValor, CultivoSiex, VariedadeSiex
from horta.services.catalogos_ficheiros import (
    expandir,
    identificar_catalogo,
    revisar,
    sen_catalogos,
)


def _xlsx(ruta, folla, cabeceira, filas):
    libro = Workbook()
    ws = libro.active
    ws.title = folla
    ws.append(cabeceira)
    for fila in filas:
        ws.append(fila)
    libro.save(ruta)
    return ruta


def _pragas(ruta, codigos, folla="Artrópodos y gasterópodos"):
    return _xlsx(ruta, folla, ["Código SIEX", "Nombre científico"],
                 [[str(c), f"Especie {c}"] for c in codigos])


def test_identifica_portal_zip_e_titulo_da_folla(tmp_path):
    assert identificar_catalogo(_pragas(tmp_path / "PLAGAS.xlsx", [1])) == "praga"
    assert identificar_catalogo(
        _xlsx(tmp_path / "20260311 Actividad agraria.xlsx", "Datos", ["Código SIEX"], [])
    ) == "actividade_agraria"
    assert identificar_catalogo(
        _xlsx(tmp_path / "20260508_CULTIVO_INTEGRADO SI.xlsx", "Hoja1", ["Código"], [])
    ) == "cultivo"
    # Nome calquera do navegador: recoñécese polo título da folla (cortado a 31 caracteres)
    assert identificar_catalogo(_pragas(tmp_path / "descarga (3).xlsx", [1])) == "praga"
    assert identificar_catalogo(
        _xlsx(tmp_path / "x.xlsx", "Certificación producción ecoló", ["Código SIEX"], [])
    ) == "certificacion_ecoloxica"
    assert identificar_catalogo(
        _xlsx(tmp_path / "Tipo de titular.xlsx", "Datos", ["Código SIEX"], [])) is None


def test_revisar_non_garda_e_aplicar_si(session, tmp_path):
    ficheiro = _pragas(tmp_path / "PLAGAS.xlsx", [1, 2])
    [revision] = revisar(session, [ficheiro])
    assert (revision.catalogo, revision.informe.altas) == ("praga", 2)
    assert session.query(CatalogoValor).count() == 0
    assert sen_catalogos(session)
    revisar(session, [ficheiro], aplicar=True)
    assert session.query(CatalogoValor).count() == 2
    assert not sen_catalogos(session)


def test_formato_novo_non_importa_nada(session, tmp_path):
    ficheiro = _xlsx(tmp_path / "PLAGAS.xlsx", "Artrópodos y gasterópodos",
                     ["Codigo", "Nombre científico"], [["1", "x"]])
    [revision] = revisar(session, [ficheiro], aplicar=True)
    assert "fáltalle a columna «Código SIEX»" in revision.erro
    assert "hai que adaptar a app" in revision.erro
    assert session.query(CatalogoValor).count() == 0


def test_moitas_baixas_marcanse_como_sospeitosas(session, tmp_path):
    revisar(session, [_pragas(tmp_path / "PLAGAS.xlsx", range(1, 21))], aplicar=True)
    [revision] = revisar(session, [_pragas(tmp_path / "PLAGAS.xlsx", [1, 2])])
    assert revision.informe.baixas == 18 and revision.informe.sospeitoso
    [revision] = revisar(session, [_pragas(tmp_path / "PLAGAS.xlsx", range(1, 20))])
    assert revision.informe.baixas == 1 and not revision.informe.sospeitoso


def test_cultivos_e_variedades_no_mesmo_lote(session, tmp_path):
    cultivos = _xlsx(tmp_path / "PRODUCTOS.xlsx", "Cultivo", ["Código", "Cultivo"],
                     [[99, "PATATA"]])
    variedades = _xlsx(tmp_path / "VARIEDAD_ESPECIE_TIPO.xlsx", "Variedad  Especie  Tipo",
                       ["Código cultivo", "Código Variedad/ Especie/ Tipo",
                        "Variedad/ Especie/ Tipo"], [[99, 1, "KENNEBEC"]])
    revisions = revisar(session, [variedades, cultivos])
    assert [(r.catalogo, r.erro, r.informe.altas) for r in revisions] == [
        ("cultivo", None, 1), ("variedade", None, 1)]
    assert session.query(CultivoSiex).count() == 0
    revisar(session, [variedades, cultivos], aplicar=True)
    assert session.query(VariedadeSiex).one().nome_oficial == "KENNEBEC"


def test_ficheiro_que_non_e_catalogo(session, tmp_path):
    [revision] = revisar(session, [_xlsx(tmp_path / "notas.xlsx", "Folla1", ["a"], [])])
    assert revision.catalogo is None and "Non é un catálogo" in revision.erro


def test_expandir_zip(tmp_path):
    pragas = _pragas(tmp_path / "PLAGAS.xlsx", [1])
    with zipfile.ZipFile(tmp_path / "c.zip", "w") as z:
        z.write(pragas, "Catálogos 2026/PLAGAS.xlsx")
        z.writestr("Catálogos 2026/leme.txt", "x")
    destino = tmp_path / "saida"
    destino.mkdir()
    assert [p.name for p in expandir([tmp_path / "c.zip"], destino)] == ["PLAGAS.xlsx"]
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Catálogos: recoñecer os ficheiros e revisalos en lote: feito.

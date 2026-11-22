"""Importa o rexistro de fitosanitarios do MAPA (ProductosAutorizados.json e Cultivos.json).

Os usos e as pontes cos códigos SIEX substitúense enteiros en cada importación. Os produtos
consérvanse aínda que deixen de figurar, para poder describir os tratamentos antigos.
Importar despois dos catálogos do FEGA: as pontes cruzan cos cultivos e pragas do SIEX.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CultivoSiex
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.services.catalogos_importar import InformeImportacion, _nova_version
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_normalizar import (
    aplicacions_max,
    clave,
    data,
    intervalo_min_dias,
    nome_cientifico,
    numero,
    prazo_seguridade,
    texto,
    unidade_dose,
)

NON_FIGURA = "Non figura"


def _ler(ruta: Path) -> Any:
    if not ruta.exists():
        raise OperacionNonPermitidaError(f"Falta o ficheiro {ruta.name}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _uso(num_rexistro: str, u: dict[str, Any]) -> dict[str, Any]:
    dose_min, dose_max = numero(u.get("Dosis_Min")), numero(u.get("Dosis_Max"))
    ps_tipo, ps_dias = prazo_seguridade(u.get("Plazo Seguridad"))
    return {
        "num_rexistro": num_rexistro,
        "codigo_cultivo": str(u["CodigoCultivo"]),
        "cultivo": texto(u.get("Cultivo")) or "",
        "codigo_agente": str(u["CodigoAgente"]),
        "agente": texto(u.get("Agente")) or "",
        "tipo_usuario": texto(u.get("TipoUsuario")),
        "sistema_cultivo": texto(u.get("SistemaCultivo")),
        "dose_min": dose_min,
        "dose_max": dose_max if dose_max is not None else dose_min,
        "unidade_dose": unidade_dose(u.get("Unidad Medida dosis")),
        "ps_tipo": ps_tipo,
        "ps_dias": ps_dias,
        "aplicacions_max": aplicacions_max(u.get("Aplicaciones")),
        "intervalo_min_dias": intervalo_min_dias(u.get("IntervaloAplicaciones")),
        "condicionamento": (texto(u.get("CondicionamientoEspecifico")) or "")[:2000] or None,
    }


def _pontes(session: Session, cultivos_mapa: list[dict[str, Any]],
            axentes: dict[str, str]) -> None:
    session.query(FitoPonteCultivo).delete()
    session.query(FitoPonteAxente).delete()
    por_eppo: dict[str, list[str]] = {}
    for c in cultivos_mapa:
        for eppo in (c.get("CodigoEppo") or "").split(","):
            if eppo.strip():
                por_eppo.setdefault(eppo.strip().upper(), []).append(str(c["CodigoCultivo"]))
    for siex in session.query(CultivoSiex).filter(CultivoSiex.codigo_eppo.is_not(None)):
        for codigo in por_eppo.get((siex.codigo_eppo or "").upper(), []):
            session.add(FitoPonteCultivo(cultivo_siex_codigo=siex.codigo, codigo_cultivo=codigo))
    por_nome: dict[str, list[str]] = {}
    for codigo_agente, agente in axentes.items():
        por_nome.setdefault(nome_cientifico(agente), []).append(codigo_agente)
    for valor in session.query(CatalogoValor).filter(CatalogoValor.catalogo.in_(TIPOS_PROBLEMA)):
        for codigo_agente in por_nome.get(clave(valor.descricion), []):
            session.add(FitoPonteAxente(catalogo=valor.catalogo, codigo=valor.codigo,
                                        codigo_agente=codigo_agente))


def importar_fitosanitarios(session: Session, directorio: Path) -> InformeImportacion:
    ruta = directorio / "ProductosAutorizados.json"
    produtos = _ler(ruta)["Productos"]
    cultivos_mapa = _ler(directorio / "Cultivos.json")
    informe = InformeImportacion(catalogo="fitosanitarios")
    version = _nova_version(session, "fitosanitarios", ruta, len(produtos))
    if version is None:
        informe.xa_importado = True
        return informe
    existentes = {p.num_rexistro: p for p in session.query(FitoProduto)}
    session.query(FitoUso).delete()
    session.query(FitoMateria).delete()
    vistos: set[str] = set()
    todos_usos: list[dict[str, Any]] = []
    materias: list[FitoMateria] = []
    for p in produtos:
        d = p["DATOSPRODUCTO"]
        num = texto(d["Num_Registro"]) or ""
        if num in vistos:
            continue  # o MAPA repite ás veces un produto con outro IdProducto e os mesmos usos
        vistos.add(num)
        datos = {
            "nome": texto(d.get("Nombre")) or num,
            "titular": texto(d.get("Titular")),
            "estado": texto(d.get("Estado")),
            "data_caducidade": data(d.get("Fecha_Caducidad")),
            "data_cancelacion": data(d.get("Fecha_Cancelacion")),
            "data_limite_venda": data(d.get("Fecha_LimiteVenta")),
        }
        actual = existentes.get(num)
        if actual is None:
            session.add(FitoProduto(num_rexistro=num, version_id=version.id, **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
        for c in p.get("COMPOSICION") or []:
            if texto(c.get("Nombre Sustancia")):
                materias.append(FitoMateria(num_rexistro=num,
                                            sustancia=texto(c.get("Nombre Sustancia")),
                                            concentracion=numero(c.get("Concentracion")),
                                            unidade=texto(c.get("DescripcionNota"))))
        todos_usos += [_uso(num, u) for u in p.get("USOS") or []]
    for num, produto in existentes.items():
        if num not in vistos and produto.estado != NON_FIGURA:
            produto.estado = NON_FIGURA
            informe.baixas += 1
    session.flush()
    session.add_all(materias)
    session.bulk_insert_mappings(FitoUso, todos_usos)  # type: ignore[arg-type]
    axentes = {u["codigo_agente"]: u["agente"] for u in todos_usos}
    _pontes(session, cultivos_mapa, axentes)
    session.commit()
    return informe

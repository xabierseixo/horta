from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from horta.models.abonado import AbonadoCultivo
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import LaborCultivo
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
from horta.models.rega import RegaCultivo
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen, persoa_co_papel

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_cultivo. Queda fóra id,
# parcela_id e created_at: mover un cultivo a outra parcela saltaría o
# control de permisos, que se fai coa parcela_id actual.
CAMPOS_EDITABLES_CULTIVO = frozenset(
    {
        "especie",
        "variedade",
        "data_colleita_prevista",
        "notas",
        "cultivo_siex_codigo",
        "variedade_siex_id",
        "variedade_local_id",
        "superficie_ha",
        "tipo_inicio",
        "data_inicio",
        "data_fin",
        "causa_baixa",
        "sistema_cultivo",
        "sistema_explotacion",
        "destino",
        "actividade_agraria",
        "certificacion_ecoloxica",
        "data_inicio_conversion",
        "producion_integrada",
        "procedencia_material",
        "provedor_material_id",
        "lote_material",
        "pasaporte_fitosanitario",
        "num_arbores",
        "marco_plantacion",
        "ano_plantacion",
        "unidades_produtivas",
        "ciclos_ano",
        "duracion_ciclo_dias",
        "cultivo_anterior_codigo",
        "obxectivo_colleita_kg_ha",
        "plan_necesidade_n",
        "plan_necesidade_p2o5",
        "plan_necesidade_k2o",
        "plan_ferramenta_sostibilidade",
        "plan_data",
        "plan_auga_n_nitrico",
        "plan_auga_p2o5",
        "tipo_mvr",
        "detalle_mvr",
        "empresa_semente",
        "sementeira_directa",
        "tipo_cobertura_solo",
        "num_castineiros",
        "num_abeleiras",
        "num_nogueiras",
        "num_amendoeiras",
        "num_outros_froitos_casca",
        "data_fin_sementeira",
        "cantidade_semente_kg",
        "dose_sementeira_kg_ha",
        "densidade_plantas_ha",
        "material_tratado",
        "semente_tratamento_produto",
        "semente_tratamento_num_rexistro",
        "material_adquirido",
        "data_adquisicion_material",
        "sementeira_persoa_id",
        "sementeira_horas",
    }
)


def _horta_id_da_parcela(session: Session, parcela_id: int) -> int | None:
    return session.query(Parcela.horta_id).filter_by(id=parcela_id).scalar()


_CATALOGOS_CULTIVO = {
    "sistema_cultivo": "sistema_cultivo",
    "sistema_explotacion": "sistema_explotacion",
    "destino": "destino_cultivo",
    "actividade_agraria": "actividade_agraria",
    "certificacion_ecoloxica": "certificacion_ecoloxica",
    "causa_baixa": "causa_baixa",
    "procedencia_material": "procedencia_material_vexetal",
    "tipo_cobertura_solo": "tipo_cobertura_solo",
}
_EN_CONVERSION = "3"
_CAMPOS_REA = (
    "superficie_ha", "tipo_inicio", "data_inicio", "data_fin", "data_colleita_prevista",
    "num_arbores", "marco_plantacion", "data_inicio_conversion", "data_fin_sementeira",
    "cantidade_semente_kg", "dose_sementeira_kg_ha", "densidade_plantas_ha",
    "material_adquirido", "data_adquisicion_material", "lote_material", *_CATALOGOS_CULTIVO,
)


def estado_cultivo(cultivo: Cultivo, primeira_colleita: date | None = None,
                   hoxe: date | None = None) -> str:
    """planificado / en_curso / rematado: sae dos traballos do cultivo, non se escribe.

    En curso desde a sementeira ou plantación (data de inicio) ou desde a primeira colleita;
    rematado coa data de fin."""
    hoxe = hoxe or date.today()
    if cultivo.data_fin is not None and cultivo.data_fin <= hoxe:
        return "rematado"
    comezo = min((d for d in (cultivo.data_inicio, primeira_colleita) if d is not None),
                 default=None)
    if comezo is not None and comezo <= hoxe:
        return "en_curso"
    return "planificado"


def estados_cultivos(session: Session, actor: Usuario, horta_id: int,
                     hoxe: date | None = None) -> dict[int, str]:
    """O estado de cada cultivo da explotación (ver estado_cultivo)."""
    cultivos = listar_cultivos(session, actor, horta_id)
    primeiras: dict[int, date] = {
        cultivo_id: data
        for cultivo_id, data in session.query(Colleita.cultivo_id, func.min(Colleita.data))
        .filter(Colleita.cultivo_id.in_([c.id for c in cultivos]), Colleita.baixa.is_(False))
        .group_by(Colleita.cultivo_id)
    }
    return {c.id: estado_cultivo(c, primeiras.get(c.id), hoxe) for c in cultivos}


def _valores_rea(cultivo: Cultivo | None, cambios: dict[str, Any]) -> dict[str, Any]:
    return {c: cambios.get(c, getattr(cultivo, c, None)) for c in _CAMPOS_REA}


def _validar_rea(session: Session, valores: dict[str, Any], parcela: Parcela | None) -> None:
    superficie = valores["superficie_ha"]
    if superficie is not None:
        if superficie <= 0:
            raise OperacionNonPermitidaError("A superficie do cultivo ten que ser maior que 0")
        if parcela is not None and parcela.superficie and superficie > parcela.superficie:
            raise OperacionNonPermitidaError("A superficie do cultivo é maior ca da parcela")
    if valores["tipo_inicio"] not in (None, "sementeira", "plantacion"):
        raise OperacionNonPermitidaError("Tipo de inicio non válido")
    inicio = valores["data_inicio"]
    for campo, texto in (("data_fin", "de fin"), ("data_colleita_prevista", "de colleita")):
        if inicio is not None and valores[campo] is not None and valores[campo] < inicio:
            raise OperacionNonPermitidaError(f"A data {texto} non pode ser anterior á de inicio")
    if inicio is not None and valores["data_fin_sementeira"] is not None:
        if valores["data_fin_sementeira"] < inicio:
            raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    # CUE 6: cantidade, dose, densidade e marco exclúense entre si
    medidas = [c for c in ("cantidade_semente_kg", "dose_sementeira_kg_ha",
                           "densidade_plantas_ha", "marco_plantacion") if valores[c]]
    if len(medidas) > 1:
        raise OperacionNonPermitidaError(
            "Indica só un: cantidade de semente, dose por hectárea, plantas por hectárea "
            "ou marco de plantación"
        )
    if valores["material_adquirido"] and valores["data_adquisicion_material"] is None:
        raise OperacionNonPermitidaError("Indica a data en que se adquiriu a semente ou planta")
    if valores["num_arbores"] is not None and valores["marco_plantacion"]:
        raise OperacionNonPermitidaError(
            "Indica o número de árbores ou o marco de plantación, non os dous"
        )
    if (
        valores["data_inicio_conversion"] is not None
        and valores["certificacion_ecoloxica"] != _EN_CONVERSION
    ):
        raise OperacionNonPermitidaError(
            "A data de conversión só se indica se o cultivo está en conversión a ecolóxico"
        )
    na_data = inicio or date.today()
    for campo, catalogo in _CATALOGOS_CULTIVO.items():
        if valores[campo]:
            validar_codigo(session, catalogo, str(valores[campo]), na_data)


def crear_cultivo(
    session: Session,
    actor: Usuario,
    parcela_id: int,
    especie: str,
    **campos: Any,
) -> Cultivo:
    horta_id = _horta_id_da_parcela(session, parcela_id)
    if horta_id is None:
        raise ValueError("Esa parcela non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_rea(session, _valores_rea(None, campos), session.get(Parcela, parcela_id))
    comprobar_quen(session, horta_id, campos.get("sementeira_persoa_id"),
                   campos.get("sementeira_horas"), obrigatoria=False)
    persoa_co_papel(session, horta_id, campos.get("provedor_material_id"), "provedor")
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, **campos)
    session.add(cultivo)
    session.commit()
    return cultivo


def actualizar_cultivo(
    session: Session,
    actor: Usuario,
    cultivo: Cultivo,
    **cambios: Any,
) -> Cultivo:
    non_editables = set(cambios) - CAMPOS_EDITABLES_CULTIVO
    if non_editables:
        raise ValueError(f"Campos non editables nun cultivo: {', '.join(sorted(non_editables))}")
    horta_id = _horta_id_da_parcela(session, cultivo.parcela_id)
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    parcela = session.get(Parcela, cultivo.parcela_id)
    _validar_rea(session, _valores_rea(cultivo, cambios), parcela)
    comprobar_quen(session, horta_id, cambios.get("sementeira_persoa_id"),
                   cambios.get("sementeira_horas"), obrigatoria=False)
    persoa_co_papel(session, horta_id, cambios.get("provedor_material_id"), "provedor")
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
    session.commit()
    return cultivo


def eliminar_cultivo(session: Session, actor: Usuario, cultivo: Cultivo) -> None:
    """Elimina o cultivo e, en cascada, os seus tratamentos e fertilizacións.

    A diferenza de eliminar_tratamento/eliminar_fertilizacion (baixa lóxica),
    aquí bórranse fisicamente: non ten sentido conservar por baixa lóxica un
    tratamento cuxo cultivo xa non existe.
    """
    horta_id = _horta_id_da_parcela(session, cultivo.parcela_id)
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if session.query(TratamentoCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten tratamentos fitosanitarios rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(AbonadoCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten abonados rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(RegaCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(LaborCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten labores rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten colleitas rexistradas e debe conservarse. "
            "Podes marcalo como rematado."
        )
    if session.query(PastoreoLeira).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten pastoreos rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
    session.query(Analise).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
    session.flush()
    session.delete(cultivo)
    session.commit()


def listar_cultivos(session: Session, actor: Usuario, horta_id: int) -> list[Cultivo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Cultivo)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
        .order_by(Cultivo.especie)
        .all()
    )

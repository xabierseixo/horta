from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_cultivo. Queda fóra id,
# parcela_id e created_at: mover un cultivo a outra parcela saltaría o
# control de permisos, que se fai coa parcela_id actual.
CAMPOS_EDITABLES_CULTIVO = frozenset(
    {
        "especie",
        "variedade",
        "data_sementeira",
        "data_plantacion",
        "data_colleita_prevista",
        "data_colleita_real",
        "cantidade",
        "unidade",
        "notas",
        "estado",
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
        "provedor_material",
        "lote_material",
        "pasaporte_fitosanitario",
        "ropveg",
        "num_arbores",
        "marco_plantacion",
        "ano_plantacion",
        "unidades_produtivas",
        "ciclos_ano",
        "duracion_ciclo_dias",
        "cultivo_anterior_codigo",
        "obxectivo_colleita_kg_ha",
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
        "material_adquirido",
        "data_adquisicion_material",
    }
)


def _horta_id_da_parcela(session: Session, parcela_id: int) -> int | None:
    return session.query(Parcela.horta_id).filter_by(id=parcela_id).scalar()


def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 0:
            raise OperacionNonPermitidaError("A cantidade non pode ser negativa")


def _validar_datas(sementeira: Any, colleita: Any) -> None:
    if sementeira is not None and colleita is not None and colleita < sementeira:
        raise OperacionNonPermitidaError(
            "A data de colleita non pode ser anterior á de sementeira"
        )


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


def calcular_estado(cultivo: Cultivo, hoxe: date | None = None) -> str:
    """planificado / en_curso / rematado segundo as datas de inicio e fin."""
    hoxe = hoxe or date.today()
    if cultivo.data_fin is not None and cultivo.data_fin <= hoxe:
        return "rematado"
    if cultivo.data_inicio is not None and cultivo.data_inicio <= hoxe:
        return "en_curso"
    return "planificado"


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
    _validar_cantidade(campos)
    _validar_datas(campos.get("data_sementeira"), campos.get("data_colleita_real"))
    _validar_rea(session, _valores_rea(None, campos), session.get(Parcela, parcela_id))
    estado = campos.pop("estado", None)
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, **campos)
    cultivo.estado = estado or calcular_estado(cultivo)
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
    _validar_cantidade(cambios)
    _validar_datas(
        cambios.get("data_sementeira", cultivo.data_sementeira),
        cambios.get("data_colleita_real", cultivo.data_colleita_real),
    )
    parcela = session.get(Parcela, cultivo.parcela_id)
    _validar_rea(session, _valores_rea(cultivo, cambios), parcela)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
    if "estado" not in cambios and {"data_inicio", "data_fin"} & set(cambios):
        cultivo.estado = calcular_estado(cultivo)
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
    if session.query(Abonado).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten abonados rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Rega).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten colleitas rexistradas e debe conservarse. "
            "Podes marcalo como rematado."
        )
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
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

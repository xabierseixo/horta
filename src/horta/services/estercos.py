"""Movementos de esterco e purín: cesións e recepcións (RD 1051/2022)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.esterco import MovementoEsterco
from horta.models.horta import RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.animais import ESPECIES
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import ESTERCOS
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_MOVEMENTO = {"cesion", "recepcion"}
UNIDADES = {"t", "m3"}

ORIXES_COMPOSICION: dict[str, str] = {
    "analise": "Análise de laboratorio",
    "programa": "Programa de cálculo recoñecido",
    "condutivimetro": "Condutivímetro (purín)",
}

CAMPOS_EDITABLES_MOVEMENTO = frozenset({
    "tipo",
    "data",
    "outra_parte_id",
    "outra_parte_rega",
    "tipo_explotacion",
    "tipo_animais",
    "material",
    "cantidade",
    "unidade",
    "n_total",
    "p2o5",
    "k2o",
    "materia_organica",
    "orixe_composicion",
    "parcelas_destino",
    "notas",
    "persoa_id",
    "horas",
})


def _validar_movemento(
    session: Session,
    horta_id: int,
    tipo: str,
    data: date,
    outra_parte_id: int,
    tipo_explotacion: str,
    tipo_animais: str,
    material: str,
    cantidade: float,
    unidade: str,
    n_total: float | None,
    p2o5: float | None,
    k2o: float | None,
    materia_organica: float | None,
    orixe_composicion: str | None,
    persoa_id: int | None,
    horas: float | None,
) -> None:
    if tipo not in TIPOS_MOVEMENTO:
        raise OperacionNonPermitidaError(
            f"O tipo de movemento ten que ser 'cesion' ou 'recepcion', non {tipo!r}"
        )
    if cantidade is None or cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    if unidade not in UNIDADES:
        raise OperacionNonPermitidaError(f"A unidade ten que ser 't' ou 'm3', non {unidade!r}")

    persoa = session.get(Persoa, outra_parte_id)
    if persoa is None or persoa.horta_id != horta_id:
        raise OperacionNonPermitidaError("A outra parte ten que ser unha persoa da explotación")

    if material not in ESTERCOS:
        raise OperacionNonPermitidaError("O material ten que ser un esterco ou purín")
    validar_codigo(session, "material_fertilizante", material, data)

    if tipo_animais not in ESPECIES and tipo_animais not in ESPECIES.values():
        raise OperacionNonPermitidaError("O tipo de animais ten que ser unha especie da lista")
    if not tipo_explotacion or not str(tipo_explotacion).strip():
        raise OperacionNonPermitidaError("Indica o tipo de explotación")

    for nome_campo, val in (
        ("N total", n_total),
        ("P₂O₅", p2o5),
        ("K₂O", k2o),
        ("Materia orgánica", materia_organica),
    ):
        if val is not None and not (0 <= val <= 100):
            raise OperacionNonPermitidaError(
                f"A porcentaxe de {nome_campo} ten que estar entre 0 e 100 %"
            )

    if tipo == "cesion":
        if n_total is None:
            raise OperacionNonPermitidaError(
                "Nunha cesión o contido de N total é obrigatorio (RD 1051/2022 anexo VII)"
            )
        if not orixe_composicion or orixe_composicion not in ORIXES_COMPOSICION:
            raise OperacionNonPermitidaError(
                "Nunha cesión a orixe da composición é obrigatoria (RD 1051/2022 anexo VII)"
            )
    elif orixe_composicion is not None and orixe_composicion not in ORIXES_COMPOSICION:
        raise OperacionNonPermitidaError("A orixe da composición indicada non é válida")

    comprobar_quen(session, horta_id, persoa_id, horas, obrigatoria=False)


def crear_movemento(
    session: Session,
    actor: Usuario,
    horta_id: int,
    tipo: str,
    data: date,
    outra_parte_id: int,
    tipo_explotacion: str,
    tipo_animais: str,
    material: str,
    cantidade: float,
    unidade: str,
    *,
    outra_parte_rega: str | None = None,
    n_total: float | None = None,
    p2o5: float | None = None,
    k2o: float | None = None,
    materia_organica: float | None = None,
    orixe_composicion: str | None = None,
    parcelas_destino: str | None = None,
    notas: str | None = None,
    persoa_id: int | None = None,
    horas: float | None = None,
    **kwargs: Any,
) -> MovementoEsterco:
    """Rexistra un novo movemento (cesión ou recepción) de esterco ou purín."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_movemento(
        session,
        horta_id,
        tipo,
        data,
        outra_parte_id,
        tipo_explotacion,
        tipo_animais,
        material,
        cantidade,
        unidade,
        n_total,
        p2o5,
        k2o,
        materia_organica,
        orixe_composicion,
        persoa_id,
        horas,
    )
    mov = MovementoEsterco(
        horta_id=horta_id,
        tipo=tipo,
        data=data,
        outra_parte_id=outra_parte_id,
        outra_parte_rega=outra_parte_rega.strip() if outra_parte_rega else None,
        tipo_explotacion=tipo_explotacion.strip(),
        tipo_animais=tipo_animais,
        material=material,
        cantidade=float(cantidade),
        unidade=unidade,
        n_total=n_total,
        p2o5=p2o5,
        k2o=k2o,
        materia_organica=materia_organica,
        orixe_composicion=orixe_composicion,
        parcelas_destino=parcelas_destino.strip() if parcelas_destino else None,
        notas=notas.strip() if notas and notas.strip() else None,
        persoa_id=persoa_id,
        horas=horas,
        creado_por=actor.id,
    )
    session.add(mov)
    session.commit()
    return mov


def actualizar_movemento(
    session: Session,
    actor: Usuario,
    movemento: MovementoEsterco,
    **cambios: Any,
) -> MovementoEsterco:
    """Actualiza os datos dun movemento de esterco vixente."""
    if movemento.baixa:
        raise OperacionNonPermitidaError("Un movemento dado de baixa non se pode modificar")
    comprobar_rol_horta(session, movemento.horta_id, actor, _ROLES_ESCRITURA)

    non_editables = set(cambios) - CAMPOS_EDITABLES_MOVEMENTO
    if non_editables:
        raise ValueError(
            f"Campos non editables nun movemento: {', '.join(sorted(non_editables))}"
        )

    tipo = cambios.get("tipo", movemento.tipo)
    data = cambios.get("data", movemento.data)
    outra_parte_id = cambios.get("outra_parte_id", movemento.outra_parte_id)
    tipo_explotacion = cambios.get("tipo_explotacion", movemento.tipo_explotacion)
    tipo_animais = cambios.get("tipo_animais", movemento.tipo_animais)
    material = cambios.get("material", movemento.material)
    cantidade = cambios.get("cantidade", movemento.cantidade)
    unidade = cambios.get("unidade", movemento.unidade)
    n_total = cambios.get("n_total", movemento.n_total)
    p2o5 = cambios.get("p2o5", movemento.p2o5)
    k2o = cambios.get("k2o", movemento.k2o)
    materia_organica = cambios.get("materia_organica", movemento.materia_organica)
    orixe_composicion = cambios.get("orixe_composicion", movemento.orixe_composicion)
    persoa_id = cambios.get("persoa_id", movemento.persoa_id)
    horas = cambios.get("horas", movemento.horas)

    _validar_movemento(
        session,
        movemento.horta_id,
        tipo,
        data,
        outra_parte_id,
        tipo_explotacion,
        tipo_animais,
        material,
        cantidade,
        unidade,
        n_total,
        p2o5,
        k2o,
        materia_organica,
        orixe_composicion,
        persoa_id,
        horas,
    )

    for campo, valor in cambios.items():
        if campo in ("outra_parte_rega", "tipo_explotacion", "parcelas_destino", "notas"):
            setattr(movemento, campo, valor.strip() if valor and str(valor).strip() else None)
        else:
            setattr(movemento, campo, valor)

    session.commit()
    return movemento


def dar_de_baixa_movemento(
    session: Session,
    actor: Usuario,
    movemento: MovementoEsterco,
) -> None:
    """Dá de baixa lóxica un movemento de esterco."""
    comprobar_rol_horta(session, movemento.horta_id, actor, _ROLES_ESCRITURA)
    movemento.baixa = True
    session.commit()


def listar_movementos(
    session: Session,
    actor: Usuario,
    horta_id: int,
    ano: int | None = None,
    tipo: str | None = None,
) -> list[MovementoEsterco]:
    """Lista movementos de esterco vixentes, das máis novas ás máis vellas."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(MovementoEsterco).filter(
        MovementoEsterco.horta_id == horta_id,
        MovementoEsterco.baixa.is_(False),
    )
    if ano is not None:
        desde = date(ano, 1, 1)
        ata = date(ano, 12, 31)
        consulta = consulta.filter(MovementoEsterco.data >= desde, MovementoEsterco.data <= ata)
    if tipo is not None:
        consulta = consulta.filter(MovementoEsterco.tipo == tipo)
    return list(
        consulta.order_by(MovementoEsterco.data.desc(), MovementoEsterco.id.desc()).all()
    )


def faltas_documento(mov: MovementoEsterco) -> list[str]:
    """Comproba os datos do anexo VII punto 1 do RD 1051/2022 que faltan nun movemento."""
    faltas: list[str] = []
    if not getattr(mov, "tipo_explotacion", None):
        faltas.append("Tipo de explotación")
    if not getattr(mov, "tipo_animais", None):
        faltas.append("Tipo de animais")
    cantidade = getattr(mov, "cantidade", None)
    if cantidade is None or cantidade <= 0:
        faltas.append("Cantidade")
    if getattr(mov, "n_total", None) is None:
        faltas.append("Nitróxeno total (N)")
    if getattr(mov, "p2o5", None) is None:
        faltas.append("Fósforo (P₂O₅)")
    if getattr(mov, "k2o", None) is None:
        faltas.append("Potasio (K₂O)")
    if getattr(mov, "materia_organica", None) is None:
        faltas.append("Materia orgánica")
    if not getattr(mov, "orixe_composicion", None):
        faltas.append("Orixe da composición")
    return faltas

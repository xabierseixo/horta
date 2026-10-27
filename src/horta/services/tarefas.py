from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.db import Base
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.parcela import Parcela
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Queda fóra id, horta_id e created_at: horta_id non se edita (control de
# permisos baseado nel), created_at non ten sentido editar. estado e
# data_feita tampouco: só cambian dende marcar_feita/marcar_pendente.
CAMPOS_EDITABLES_TAREFA = frozenset(
    {
        "parcela_id",
        "cultivo_id",
        "descricion",
        "data",
        "data_limite",
        "prioridade",
        "notas",
        "tipo",
        "persoa_id",
    }
)

# Tipos de traballo que se poden planificar como tarefa, coa táboa e a data de cada un. A
# sementeira non: un cultivo con data de sementeira futura xa é a sementeira por facer.
_TABOA_E_DATA: dict[str, tuple[type[Base], str]] = {
    "tratamento": (TratamentoFito, "data_inicio"),
    "abonado": (Abonado, "data_inicio"),
    "rega": (Rega, "data_inicio"),
    "labor": (Labor, "data_inicio"),
    "colleita": (Colleita, "data"),
    "analise": (Analise, "data_mostraxe"),
    "tratamento_instalacion": (TratamentoInstalacion, "data"),
}
TIPOS_TAREFA = tuple(_TABOA_E_DATA)


def _validar_datas(data: date | None, data_limite: date | None) -> None:
    if data is not None and data_limite is not None and data_limite < data:
        raise OperacionNonPermitidaError("A data límite non pode ser anterior á data prevista")


def _validar_tipo_e_quen(
    session: Session, horta_id: int, tipo: str | None, persoa_id: int | None
) -> None:
    if tipo is not None and tipo not in _TABOA_E_DATA:
        raise OperacionNonPermitidaError("Ese tipo de traballo non se pode planificar")
    comprobar_quen(session, horta_id, persoa_id, None, obrigatoria=False)


def crear_tarefa(
    session: Session,
    actor: Usuario,
    horta_id: int,
    descricion: str,
    **campos: Any,
) -> Tarefa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_datas(campos.get("data"), campos.get("data_limite"))
    _validar_tipo_e_quen(session, horta_id, campos.get("tipo"), campos.get("persoa_id"))
    prioridade = campos.pop("prioridade", "media")
    tarefa = Tarefa(horta_id=horta_id, descricion=descricion, prioridade=prioridade, **campos)
    session.add(tarefa)
    session.commit()
    return tarefa


def actualizar_tarefa(
    session: Session,
    actor: Usuario,
    tarefa: Tarefa,
    **cambios: Any,
) -> Tarefa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_TAREFA
    if non_editables:
        raise ValueError(f"Campos non editables nunha tarefa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    _validar_datas(
        cambios.get("data", tarefa.data),
        cambios.get("data_limite", tarefa.data_limite),
    )
    if tarefa.traballo_id is not None and cambios.get("tipo", tarefa.tipo) != tarefa.tipo:
        raise OperacionNonPermitidaError(
            "Esta tarefa xa ten o traballo apuntado: non se pode cambiar o tipo")
    _validar_tipo_e_quen(session, tarefa.horta_id, cambios.get("tipo", tarefa.tipo),
                         cambios.get("persoa_id", tarefa.persoa_id))
    for campo, valor in cambios.items():
        setattr(tarefa, campo, valor)
    session.commit()
    return tarefa


def marcar_feita(
    session: Session, actor: Usuario, tarefa: Tarefa, persoa_id: int | None,
    data: date | None = None, horas: float | None = None,
) -> Tarefa:
    """Unha tarefa sen tipo (outro traballo) feita: quen a fixo, cando e cantas horas."""
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    if tarefa.tipo is not None:
        raise OperacionNonPermitidaError("Esta tarefa apúntase no formulario do seu tipo")
    comprobar_quen(session, tarefa.horta_id, persoa_id, horas)
    tarefa.estado = "feito"
    tarefa.data_feita = data or date.today()
    tarefa.persoa_id = persoa_id
    tarefa.horas = horas
    session.commit()
    return tarefa


def facer_tarefa(session: Session, actor: Usuario, tarefa: Tarefa, rexistro: Base) -> Tarefa:
    """A tarefa fíxose: queda feita e ligada ao traballo apuntado no formulario do seu tipo."""
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    taboa, campo_data = _TABOA_E_DATA.get(tarefa.tipo or "", (None, ""))
    if taboa is None or not isinstance(rexistro, taboa):
        raise OperacionNonPermitidaError("O traballo apuntado non é do tipo da tarefa")
    if isinstance(rexistro, Colleita):
        cultivo = session.get(Cultivo, rexistro.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        horta_id = parcela.horta_id if parcela else None
    else:
        horta_id = getattr(rexistro, "horta_id", None)
    if horta_id != tarefa.horta_id:
        raise OperacionNonPermitidaError("O traballo apuntado non é desta explotación")
    tarefa.estado = "feito"
    tarefa.data_feita = getattr(rexistro, campo_data)
    tarefa.traballo_id = getattr(rexistro, "id")
    session.commit()
    return tarefa


def marcar_pendente(session: Session, actor: Usuario, tarefa: Tarefa) -> Tarefa:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    if tarefa.traballo_id is not None:
        raise OperacionNonPermitidaError(
            "Esta tarefa xa ten o traballo apuntado: para cambiala, edita ese traballo")
    tarefa.estado = "pendente"
    tarefa.data_feita = None
    session.commit()
    return tarefa


def eliminar_tarefa(session: Session, actor: Usuario, tarefa: Tarefa) -> None:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(tarefa)
    session.commit()


def listar_tarefas(session: Session, actor: Usuario, horta_id: int) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Tarefa).filter_by(horta_id=horta_id).order_by(Tarefa.data).all())


def listar_tarefas_pendentes_hoxe(session: Session, actor: Usuario, horta_id: int) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tarefa)
        .filter_by(horta_id=horta_id, estado="pendente", data=date.today())
        .order_by(Tarefa.prioridade)
        .all()
    )


def listar_tarefas_proximas(
    session: Session, actor: Usuario, horta_id: int, limite: int = 5
) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tarefa)
        .filter(
            Tarefa.horta_id == horta_id,
            Tarefa.estado == "pendente",
            Tarefa.data > date.today(),
        )
        .order_by(Tarefa.data)
        .limit(limite)
        .all()
    )


def listar_tarefas_atrasadas(session: Session, actor: Usuario, horta_id: int) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tarefa)
        .filter(
            Tarefa.horta_id == horta_id,
            Tarefa.estado == "pendente",
            Tarefa.data_limite.is_not(None),
            Tarefa.data_limite < date.today(),
        )
        .order_by(Tarefa.data_limite)
        .all()
    )


def contar_tarefas_pendentes(session: Session, actor: Usuario, horta_id: int) -> int:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return session.query(Tarefa).filter_by(horta_id=horta_id, estado="pendente").count()

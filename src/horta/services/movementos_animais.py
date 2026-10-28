"""Entradas e saídas de animais (libro de rexistro gandeiro, RD 787/2023 anexo V 9 e 10). A
cantidade, a data de baixa e o estado de cada grupo saen dos seus movementos. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.movemento_animal import MovementoAnimal
from horta.models.usuario import Usuario
from horta.services.coidados_animais import en_tempo_espera
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# O inicial créase só, ao dar de alta o grupo (services.animais.crear_animal)
TIPOS_MOVEMENTO: dict[str, str] = {
    "nacemento": "Nacemento",
    "entrada": "Entrada (compra, cesión)",
    "saida": "Saída (venda, cesión, matadoiro)",
    "morte": "Morte ou sacrificio na casa",
}
INICIAL = "inicial"
SUMAN = (INICIAL, "nacemento", "entrada")
CON_OUTRA_EXPLOTACION = ("entrada", "saida")


@dataclass
class DatosMovemento:
    animal_id: int
    data: date
    tipo: str
    cantidade: int
    persoa_id: int | None
    identificacion: str | None = None
    titular: str | None = None
    rega: str | None = None
    codigo_movemento: str | None = None
    causa: str | None = None
    horas: float | None = None
    notas: str | None = None
    maquina_id: int | None = None


def _movementos(session: Session, animal_id: int) -> list[MovementoAnimal]:
    return list(session.query(MovementoAnimal).filter_by(animal_id=animal_id, baixa=False)
                .order_by(MovementoAnimal.data, MovementoAnimal.id))


def recalcular(session: Session, animal: Animal) -> None:
    """Cantidade, data de alta, baixa e estado do grupo a partir dos seus movementos. Ningún
    día pode quedar en negativo; a 0 o grupo queda de baixa."""
    session.flush()
    total = 0
    ultima: date | None = None
    # O mesmo día, primeiro o que entra e despois o que sae
    for mov in sorted(_movementos(session, animal.id),
                      key=lambda m: (m.data, m.tipo not in SUMAN, m.id)):
        if mov.tipo == INICIAL:
            animal.data_alta = mov.data
        total += mov.cantidade if mov.tipo in SUMAN else -mov.cantidade
        if total < 0:
            raise OperacionNonPermitidaError(
                f"O {mov.data:%d/%m/%Y} sairían máis animais dos que había no grupo")
        ultima = mov.data
    animal.cantidade = total
    animal.estado = "activo" if total > 0 else "baixa"
    animal.data_baixa = None if total > 0 else ultima


def crear_inicial(session: Session, animal: Animal, cantidade: int) -> None:
    session.add(MovementoAnimal(horta_id=animal.horta_id, animal_id=animal.id,
                                data=animal.data_alta, tipo=INICIAL, cantidade=cantidade))


def cambiar_data_alta(session: Session, animal: Animal, data_alta: date) -> None:
    inicial = session.query(MovementoAnimal).filter_by(
        animal_id=animal.id, tipo=INICIAL, baixa=False).first()
    if inicial is not None:
        inicial.data = data_alta
    animal.data_alta = data_alta


def _animal(session: Session, animal_id: int) -> Animal:
    animal = session.get(Animal, animal_id)
    if animal is None:
        raise OperacionNonPermitidaError("Ese grupo de animais non existe")
    return animal


def _validar(session: Session, datos: DatosMovemento, animal: Animal, hoxe: date) -> None:
    if datos.tipo not in TIPOS_MOVEMENTO:
        raise OperacionNonPermitidaError("Escolle se é unha entrada, unha saída…")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data < animal.data_alta:
        raise OperacionNonPermitidaError(
            f"O grupo deuse de alta o {animal.data_alta:%d/%m/%Y}: a data non pode ser anterior")
    if datos.cantidade is None or datos.cantidade < 1:
        raise OperacionNonPermitidaError("Indica cantos animais (polo menos 1)")
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, animal.horta_id, datos.maquina_id)


def _copiar(mov: MovementoAnimal, datos: DatosMovemento, animal: Animal) -> None:
    outra = datos.tipo in CON_OUTRA_EXPLOTACION
    mov.horta_id = animal.horta_id
    mov.animal_id = animal.id
    mov.data = datos.data
    mov.tipo = datos.tipo
    mov.cantidade = datos.cantidade
    mov.identificacion = datos.identificacion or None
    # Cada tipo garda só os seus datos
    mov.titular = (datos.titular or None) if outra else None
    mov.rega = (datos.rega or None) if outra else None
    mov.codigo_movemento = (datos.codigo_movemento or None) if outra else None
    mov.causa = (datos.causa or None) if datos.tipo == "morte" else None
    mov.persoa_id = datos.persoa_id
    mov.horas = datos.horas
    mov.maquina_id = datos.maquina_id
    mov.notas = datos.notas or None


def _gardar(session: Session, animais: list[Animal]) -> None:
    try:
        for animal in animais:
            recalcular(session, animal)
    except OperacionNonPermitidaError:
        session.rollback()
        raise
    session.commit()


def crear_movemento(
    session: Session, actor: Usuario, datos: DatosMovemento, hoxe: date | None = None
) -> MovementoAnimal:
    animal = _animal(session, datos.animal_id)
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, animal, hoxe or date.today())
    mov = MovementoAnimal(creado_por=actor.id)
    _copiar(mov, datos, animal)
    session.add(mov)
    _gardar(session, [animal])
    return mov


def actualizar_movemento(
    session: Session, actor: Usuario, mov: MovementoAnimal, datos: DatosMovemento,
    hoxe: date | None = None,
) -> MovementoAnimal:
    if mov.baixa or mov.tipo == INICIAL:
        raise OperacionNonPermitidaError("Este movemento non se pode modificar")
    comprobar_rol_horta(session, mov.horta_id, actor, _ROLES_ESCRITURA)
    animal = _animal(session, datos.animal_id)
    if animal.horta_id != mov.horta_id:
        raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")
    _validar(session, datos, animal, hoxe or date.today())
    anterior = _animal(session, mov.animal_id)
    _copiar(mov, datos, animal)
    _gardar(session, [anterior] if anterior.id == animal.id else [anterior, animal])
    return mov


def dar_de_baixa_movemento(session: Session, actor: Usuario, mov: MovementoAnimal) -> None:
    if mov.tipo == INICIAL:
        raise OperacionNonPermitidaError("Os animais iniciais cámbianse na ficha do grupo")
    comprobar_rol_horta(session, mov.horta_id, actor, _ROLES_ESCRITURA)
    mov.baixa = True
    _gardar(session, [_animal(session, mov.animal_id)])


def listar_movementos(
    session: Session, actor: Usuario, horta_id: int, animal_id: int | None = None
) -> list[MovementoAnimal]:
    """Os movementos apuntados (sen os iniciais), do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = (session.query(MovementoAnimal).filter_by(horta_id=horta_id, baixa=False)
                .filter(MovementoAnimal.tipo != INICIAL))
    if animal_id is not None:
        consulta = consulta.filter_by(animal_id=animal_id)
    return list(consulta.order_by(MovementoAnimal.data.desc(), MovementoAnimal.id.desc()))


def ten_movementos(session: Session, animal_id: int) -> bool:
    """Se o grupo ten movementos apuntados ademais do inicial."""
    return session.query(MovementoAnimal).filter(
        MovementoAnimal.animal_id == animal_id, MovementoAnimal.tipo != INICIAL
    ).first() is not None


def aviso_tempo_espera(
    session: Session, actor: Usuario, horta_id: int, animal_id: int | None, tipo: str | None,
    data: date | None,
) -> str | None:
    """Avisa (sen bloquear) se saen animais dun grupo en tempo de espera por un medicamento."""
    if animal_id is None or tipo not in ("saida", "morte") or data is None:
        return None
    fin = en_tempo_espera(session, actor, horta_id, hoxe=data).get(animal_id)
    if fin is None:
        return None
    return f"Este grupo está en tempo de espera ata o {fin:%d/%m/%Y}"

import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.tarefas import actualizar_tarefa, crear_tarefa


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_crear_tarefa_con_parcela_doutra_explotacion_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta_a = crear_horta(session, ana, "Horta A")
    horta_b = crear_horta(session, ana, "Horta B")
    parcela_b = crear_parcela(session, ana, horta_b.id, "Parcela B")

    with pytest.raises(OperacionNonPermitidaError, match="Esa parcela non é desta explotación"):
        crear_tarefa(session, ana, horta_a.id, "Regar", parcela_id=parcela_b.id)


def test_crear_tarefa_con_cultivo_doutra_explotacion_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta_a = crear_horta(session, ana, "Horta A")
    horta_b = crear_horta(session, ana, "Horta B")
    parcela_b = crear_parcela(session, ana, horta_b.id, "Parcela B")
    cultivo_b = crear_cultivo(session, ana, parcela_b.id, "Tomate")

    with pytest.raises(OperacionNonPermitidaError, match="Ese cultivo non é desta explotación"):
        crear_tarefa(session, ana, horta_a.id, "Coidar tomate", cultivo_id=cultivo_b.id)


def test_actualizar_tarefa_con_parcela_doutra_explotacion_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta_a = crear_horta(session, ana, "Horta A")
    horta_b = crear_horta(session, ana, "Horta B")
    parcela_b = crear_parcela(session, ana, horta_b.id, "Parcela B")
    tarefa = crear_tarefa(session, ana, horta_a.id, "Regar")

    with pytest.raises(OperacionNonPermitidaError, match="Esa parcela non é desta explotación"):
        actualizar_tarefa(session, ana, tarefa, parcela_id=parcela_b.id)


def test_actualizar_tarefa_con_cultivo_doutra_explotacion_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta_a = crear_horta(session, ana, "Horta A")
    horta_b = crear_horta(session, ana, "Horta B")
    parcela_b = crear_parcela(session, ana, horta_b.id, "Parcela B")
    cultivo_b = crear_cultivo(session, ana, parcela_b.id, "Tomate")
    tarefa = crear_tarefa(session, ana, horta_a.id, "Regar")

    with pytest.raises(OperacionNonPermitidaError, match="Ese cultivo non é desta explotación"):
        actualizar_tarefa(session, ana, tarefa, cultivo_id=cultivo_b.id)


def test_tarefa_con_parcela_e_cultivo_da_propia_explotacion_permitese(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela1 = crear_parcela(session, ana, horta.id, "Parcela 1")
    parcela2 = crear_parcela(session, ana, horta.id, "Parcela 2")
    cultivo = crear_cultivo(session, ana, parcela1.id, "Cenoria")

    tarefa = crear_tarefa(
        session,
        ana,
        horta.id,
        "Regar cenorias",
        parcela_id=parcela1.id,
        cultivo_id=cultivo.id,
    )
    assert tarefa.id is not None
    assert tarefa.parcela_id == parcela1.id
    assert tarefa.cultivo_id == cultivo.id

    actualizada = actualizar_tarefa(session, ana, tarefa, parcela_id=parcela2.id)
    assert actualizada.parcela_id == parcela2.id


def test_parcela_ou_cultivo_inexistentes_rexeitanse(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(OperacionNonPermitidaError, match="Esa parcela non é desta explotación"):
        crear_tarefa(session, ana, horta.id, "Regar", parcela_id=99999)

    with pytest.raises(OperacionNonPermitidaError, match="Ese cultivo non é desta explotación"):
        crear_tarefa(session, ana, horta.id, "Regar", cultivo_id=99999)

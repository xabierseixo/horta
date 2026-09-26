from datetime import date, timedelta

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.tarefas import (
    actualizar_tarefa,
    contar_tarefas_pendentes,
    crear_tarefa,
    eliminar_tarefa,
    listar_tarefas,
    listar_tarefas_atrasadas,
    listar_tarefas_pendentes_hoxe,
    listar_tarefas_proximas,
    marcar_feita,
    marcar_pendente,
)


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


def test_admin_pode_crear_tarefa(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    tarefa = crear_tarefa(session, ana, horta.id, "Regar tomates")

    assert tarefa.id is not None
    assert tarefa.horta_id == horta.id
    assert tarefa.estado == "pendente"
    assert tarefa.prioridade == "media"


def test_editor_pode_crear_tarefa_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_tarefa(session, bea, horta.id, "Regar")

    with pytest.raises(PermisoDenegadoError):
        crear_tarefa(session, carlos, horta.id, "Podar")


def test_listar_tarefas_devolve_as_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    crear_tarefa(session, ana, horta.id, "Regar")
    crear_tarefa(session, ana, outra_horta.id, "Sementar")

    tarefas = listar_tarefas(session, ana, horta.id)

    assert [t.descricion for t in tarefas] == ["Regar"]


def test_admin_pode_actualizar_e_eliminar_tarefa(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    tarefa = crear_tarefa(session, ana, horta.id, "Regar")

    actualizada = actualizar_tarefa(
        session, ana, tarefa, descricion="Regar tomates", prioridade="alta"
    )
    assert actualizada.descricion == "Regar tomates"
    assert actualizada.prioridade == "alta"

    eliminar_tarefa(session, ana, tarefa)
    assert listar_tarefas(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_tarefa(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    tarefa = crear_tarefa(session, ana, horta.id, "Regar")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_tarefa(session, carlos, tarefa, descricion="Cambiado")

    with pytest.raises(PermisoDenegadoError):
        eliminar_tarefa(session, carlos, tarefa)


@pytest.mark.parametrize(
    "campo", ["horta_id", "id", "created_at", "estado", "data_feita", "campo_inexistente"]
)
def test_actualizar_tarefa_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    tarefa = crear_tarefa(session, ana, horta.id, "Regar")
    id_orixinal = tarefa.id

    with pytest.raises(ValueError):
        actualizar_tarefa(session, ana, tarefa, descricion="Cambiado", **{campo: outra_horta.id})

    session.refresh(tarefa)
    assert tarefa.id == id_orixinal
    assert tarefa.horta_id == horta.id
    assert tarefa.descricion == "Regar"


def test_marcar_feita_e_marcar_pendente(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    tarefa = crear_tarefa(session, ana, horta.id, "Regar")

    feita = marcar_feita(session, ana, tarefa)
    assert feita.estado == "feito"
    assert feita.data_feita == date.today()

    pendente = marcar_pendente(session, ana, tarefa)
    assert pendente.estado == "pendente"
    assert pendente.data_feita is None


def test_listar_tarefas_pendentes_hoxe(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    hoxe = crear_tarefa(session, ana, horta.id, "Regar hoxe", data=date.today())
    crear_tarefa(session, ana, horta.id, "Regar mañá", data=date.today() + timedelta(days=1))
    feita_hoxe = crear_tarefa(session, ana, horta.id, "Xa feita hoxe", data=date.today())
    marcar_feita(session, ana, feita_hoxe)

    tarefas = listar_tarefas_pendentes_hoxe(session, ana, horta.id)

    assert [t.id for t in tarefas] == [hoxe.id]


def test_listar_tarefas_proximas_limita_e_ordena(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    for i in range(1, 8):
        crear_tarefa(session, ana, horta.id, f"Tarefa {i}", data=date.today() + timedelta(days=i))

    proximas = listar_tarefas_proximas(session, ana, horta.id, limite=5)

    assert [t.descricion for t in proximas] == [f"Tarefa {i}" for i in range(1, 6)]


def test_listar_tarefas_atrasadas(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    atrasada = crear_tarefa(
        session, ana, horta.id, "Atrasada", data_limite=date.today() - timedelta(days=1)
    )
    crear_tarefa(session, ana, horta.id, "A tempo", data_limite=date.today() + timedelta(days=1))

    atrasadas = listar_tarefas_atrasadas(session, ana, horta.id)

    assert [t.id for t in atrasadas] == [atrasada.id]


def test_contar_tarefas_pendentes(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    crear_tarefa(session, ana, horta.id, "Unha")
    feita = crear_tarefa(session, ana, horta.id, "Outra")
    marcar_feita(session, ana, feita)

    assert contar_tarefas_pendentes(session, ana, horta.id) == 1

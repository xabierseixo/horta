import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.hortas import crear_horta
from horta.services.maquinaria import actualizar_maquina, crear_maquina, listar_maquinas


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(nome=email.split("@")[0], email=email, password_hash="hash-falso",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


def test_crear_maquina_con_roma(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    maquina = crear_maquina(session, ana, horta.id, "Atomizador", num_roma="ES123456789")
    assert [m.alias for m in listar_maquinas(session, ana, horta.id)] == ["Atomizador"]
    assert maquina.propia is True


def test_so_un_identificador_permitido(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="só un identificador"):
        crear_maquina(session, ana, horta.id, "Mochila", num_roma="A", num_reganip="B")


def test_actualizar_non_permite_dous_identificadores(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    maquina = crear_maquina(session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1")
    with pytest.raises(ValueError, match="só un identificador"):
        actualizar_maquina(session, ana, maquina, num_roma="ES1")

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


def test_aviso_de_inspeccion_dos_equipos_de_tratamento():
    from datetime import date

    from horta.models.maquina import Maquina
    from horta.services.maquinaria import aviso_inspeccion

    hoxe = date(2026, 10, 30)
    assert aviso_inspeccion(Maquina(alias="a", activa=True,
                                    data_ultima_inspeccion=date(2024, 1, 1)), hoxe) is None
    assert aviso_inspeccion(Maquina(alias="a", activa=True,
                                    data_ultima_inspeccion=date(2023, 2, 1)), hoxe) == (
        "Inspección vencida o 01/02/2026")
    # Nova: ten 5 anos para a primeira
    assert aviso_inspeccion(Maquina(alias="a", activa=True,
                                    data_adquisicion=date(2022, 3, 1)), hoxe) is None
    assert aviso_inspeccion(Maquina(alias="a", activa=True,
                                    data_adquisicion=date(2020, 2, 29)), hoxe) == (
        "Primeira inspección vencida o 28/02/2025")
    assert aviso_inspeccion(Maquina(alias="a", activa=True), hoxe) == "Sen inspección apuntada"
    # A mochila non se inscribe no ROMA: fóra
    assert aviso_inspeccion(Maquina(alias="m", activa=True, id_equipo_non_inscribible="M-1"),
                            hoxe) is None

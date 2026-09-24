import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
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


def test_admin_da_horta_pode_crear_parcela(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=500.0)

    assert parcela.id is not None
    assert parcela.horta_id == horta.id
    assert parcela.estado == "activa"


def test_editor_pode_crear_parcela_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_parcela(session, bea, horta.id, "Parcela de Bea")

    with pytest.raises(PermisoDenegadoError):
        crear_parcela(session, carlos, horta.id, "Parcela de Carlos")


def test_lector_pode_listar_pero_non_actualizar_nin_eliminar(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    parcelas = listar_parcelas(session, carlos, horta.id)
    assert [p.nome for p in parcelas] == ["Parcela Norte"]

    with pytest.raises(PermisoDenegadoError):
        actualizar_parcela(session, carlos, parcela, nome="Outro nome")

    with pytest.raises(PermisoDenegadoError):
        eliminar_parcela(session, carlos, parcela)


def test_admin_pode_actualizar_e_eliminar_parcela(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    actualizada = actualizar_parcela(session, ana, parcela, nome="Parcela Sur", superficie=800.0)
    assert actualizada.nome == "Parcela Sur"
    assert actualizada.superficie == 800.0

    eliminar_parcela(session, ana, parcela)
    assert listar_parcelas(session, ana, horta.id) == []


def test_campos_sigpac_son_opcionais_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    assert parcela.sigpac_provincia is None
    assert parcela.secano_regadio is None


@pytest.mark.parametrize("campo", ["horta_id", "id", "created_at", "campo_inexistente"])
def test_actualizar_parcela_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    id_orixinal = parcela.id

    with pytest.raises(ValueError):
        actualizar_parcela(session, ana, parcela, nome="Cambiado", **{campo: outra_horta.id})

    session.refresh(parcela)
    assert parcela.id == id_orixinal
    assert parcela.horta_id == horta.id
    assert parcela.nome == "Parcela Norte"

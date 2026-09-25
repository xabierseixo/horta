from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela
from horta.services.tratamentos import (
    actualizar_tratamento,
    crear_tratamento,
    eliminar_tratamento,
    listar_tratamentos,
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


def _crear_cultivo(session, actor, horta_id):
    parcela = crear_parcela(session, actor, horta_id, "Parcela Norte")
    return crear_cultivo(session, actor, parcela.id, "Tomate")


def test_admin_pode_crear_tratamento(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )

    assert tratamento.id is not None
    assert tratamento.cultivo_id == cultivo.id
    assert tratamento.baixa is False


def test_editor_pode_crear_tratamento_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_tratamento(session, bea, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Bea")

    with pytest.raises(PermisoDenegadoError):
        crear_tratamento(session, carlos, cultivo.id, date(2026, 5, 2), "Pulgón", "Xabón", "Carlos")


def test_crear_tratamento_en_cultivo_inexistente_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError):
        crear_tratamento(session, ana, 9999, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier")


def test_crear_tratamento_en_cultivo_doutra_horta_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta_ana = crear_horta(session, ana, "Horta de Ana")
    horta_carlos = crear_horta(session, carlos, "Horta de Carlos")
    cultivo_de_ana = _crear_cultivo(session, ana, horta_ana.id)
    engadir_membro(session, carlos, horta_carlos.id, ana, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        crear_tratamento(
            session, carlos, cultivo_de_ana.id, date(2026, 5, 1), "Mildeu", "Cobre", "Carlos"
        )


def test_eliminar_tratamento_e_baixa_loxica_non_borrado_fisico(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )

    eliminar_tratamento(session, ana, tratamento)

    session.refresh(tratamento)
    assert tratamento.baixa is True
    assert listar_tratamentos(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_tratamento(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_tratamento(session, carlos, tratamento, praga="Pulgón")

    with pytest.raises(PermisoDenegadoError):
        eliminar_tratamento(session, carlos, tratamento)


@pytest.mark.parametrize("campo", ["cultivo_id", "id", "created_at", "baixa", "campo_inexistente"])
def test_actualizar_tratamento_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    outro_cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    id_orixinal = tratamento.id

    valor = outro_cultivo.id if campo == "cultivo_id" else True
    with pytest.raises(ValueError):
        actualizar_tratamento(session, ana, tratamento, praga="Cambiado", **{campo: valor})

    session.refresh(tratamento)
    assert tratamento.id == id_orixinal
    assert tratamento.cultivo_id == cultivo.id
    assert tratamento.praga == "Mildeu"
    assert tratamento.baixa is False

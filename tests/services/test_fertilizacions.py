from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.fertilizacions import (
    actualizar_fertilizacion,
    crear_fertilizacion,
    eliminar_fertilizacion,
    listar_fertilizacions,
)
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela


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


def test_admin_pode_crear_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )

    assert fertilizacion.id is not None
    assert fertilizacion.cultivo_id == cultivo.id
    assert fertilizacion.baixa is False


@pytest.mark.parametrize("campo", ["superficie", "n", "p", "k", "carbono_organico"])
def test_valor_negativo_ao_crear_fertilizacion(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    with pytest.raises(ValueError, match=f"O campo {campo} non pode ser negativo"):
        crear_fertilizacion(
            session,
            ana,
            cultivo.id,
            date(2026, 4, 1),
            "abonado_fondo",
            "Compost",
            **{campo: -1.0},
        )


def test_valor_negativo_ao_actualizar_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost", n=10.0
    )

    with pytest.raises(ValueError, match="O campo n non pode ser negativo"):
        actualizar_fertilizacion(session, ana, fertilizacion, n=-3.0)

    session.refresh(fertilizacion)
    assert fertilizacion.n == 10.0


def test_editor_pode_crear_fertilizacion_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_fertilizacion(session, bea, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost")

    with pytest.raises(PermisoDenegadoError):
        crear_fertilizacion(session, carlos, cultivo.id, date(2026, 4, 2), "cobertoira", "Xurro")


def test_crear_fertilizacion_en_cultivo_inexistente_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError):
        crear_fertilizacion(session, ana, 9999, date(2026, 4, 1), "abonado_fondo", "Compost")


def test_crear_fertilizacion_en_cultivo_doutra_horta_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta_ana = crear_horta(session, ana, "Horta de Ana")
    horta_carlos = crear_horta(session, carlos, "Horta de Carlos")
    cultivo_de_ana = _crear_cultivo(session, ana, horta_ana.id)
    engadir_membro(session, carlos, horta_carlos.id, ana, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        crear_fertilizacion(
            session, carlos, cultivo_de_ana.id, date(2026, 4, 1), "abonado_fondo", "Compost"
        )


def test_eliminar_fertilizacion_e_baixa_loxica_non_borrado_fisico(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )

    eliminar_fertilizacion(session, ana, fertilizacion)

    session.refresh(fertilizacion)
    assert fertilizacion.baixa is True
    assert listar_fertilizacions(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_fertilizacion(session, carlos, fertilizacion, produto="Cambiado")

    with pytest.raises(PermisoDenegadoError):
        eliminar_fertilizacion(session, carlos, fertilizacion)


@pytest.mark.parametrize("campo", ["cultivo_id", "id", "created_at", "baixa", "campo_inexistente"])
def test_actualizar_fertilizacion_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    outro_cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    id_orixinal = fertilizacion.id

    valor = outro_cultivo.id if campo == "cultivo_id" else True
    with pytest.raises(ValueError):
        actualizar_fertilizacion(session, ana, fertilizacion, produto="Cambiado", **{campo: valor})

    session.refresh(fertilizacion)
    assert fertilizacion.id == id_orixinal
    assert fertilizacion.cultivo_id == cultivo.id
    assert fertilizacion.produto == "Compost"
    assert fertilizacion.baixa is False

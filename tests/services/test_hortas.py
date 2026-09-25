import datetime

import pytest

from horta.models.animal import Animal
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fertilizacions import crear_fertilizacion
from horta.services.hortas import (
    actualizar_horta,
    cambiar_rol_membro,
    crear_horta,
    eliminar_horta,
    engadir_membro,
    listar_hortas_usuario,
    quitar_membro,
)
from horta.services.parcelas import crear_parcela
from horta.services.tratamentos import crear_tratamento


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


def test_crear_horta_fai_ao_creador_admin_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")

    horta = crear_horta(session, ana, "A miña horta")

    [(horta_listada, rol)] = listar_hortas_usuario(session, ana)
    assert horta_listada.id == horta.id
    assert rol == RolHorta.ADMIN


def test_admin_da_horta_pode_engadir_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)

    hortas_de_bea = listar_hortas_usuario(session, bea)
    assert hortas_de_bea == [(horta, RolHorta.EDITOR)]


def test_non_admin_non_pode_engadir_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)

    with pytest.raises(PermisoDenegadoError):
        engadir_membro(session, bea, horta.id, carlos, RolHorta.LECTOR)


def test_admin_pode_cambiar_rol_e_quitar_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)

    cambiar_rol_membro(session, ana, horta.id, bea.id, RolHorta.EDITOR)
    assert listar_hortas_usuario(session, bea) == [(horta, RolHorta.EDITOR)]

    quitar_membro(session, ana, horta.id, bea.id)
    assert listar_hortas_usuario(session, bea) == []


def test_usuario_sen_relacion_non_ve_a_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    crear_horta(session, ana, "A miña horta")

    assert listar_hortas_usuario(session, carlos) == []


def test_non_se_pode_quitar_ao_unico_admin_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(OperacionNonPermitidaError):
        quitar_membro(session, ana, horta.id, ana.id)

    assert listar_hortas_usuario(session, ana) == [(horta, RolHorta.ADMIN)]


def test_non_se_pode_degradar_ao_unico_admin_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(OperacionNonPermitidaError):
        cambiar_rol_membro(session, ana, horta.id, ana.id, RolHorta.EDITOR)

    assert listar_hortas_usuario(session, ana) == [(horta, RolHorta.ADMIN)]


def test_admin_pode_deixar_de_selo_se_queda_outro_admin(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.ADMIN)

    cambiar_rol_membro(session, ana, horta.id, ana.id, RolHorta.LECTOR)
    assert listar_hortas_usuario(session, ana) == [(horta, RolHorta.LECTOR)]

    quitar_membro(session, bea, horta.id, ana.id)
    assert listar_hortas_usuario(session, ana) == []


def test_cambiar_rol_a_non_membro_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(OperacionNonPermitidaError):
        cambiar_rol_membro(session, ana, horta.id, bea.id, RolHorta.EDITOR)


def test_admin_da_horta_pode_actualizar_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    actualizada = actualizar_horta(
        session, ana, horta, nome="Horta Nova", descricion="Preto do río", uso_profesional=True
    )

    assert actualizada.nome == "Horta Nova"
    assert actualizada.descricion == "Preto do río"
    assert actualizada.uso_profesional is True


def test_editor_e_lector_non_poden_actualizar_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_horta(session, bea, horta, nome="Outro nome")
    with pytest.raises(PermisoDenegadoError):
        actualizar_horta(session, carlos, horta, nome="Outro nome")


def test_actualizar_horta_rexeita_campos_non_editables(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    id_orixinal = horta.id

    with pytest.raises(ValueError):
        actualizar_horta(session, ana, horta, id=999)

    assert horta.id == id_orixinal
    assert horta.nome == "A miña horta"


def test_admin_pode_eliminar_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    eliminar_horta(session, ana, horta)

    assert listar_hortas_usuario(session, ana) == []
    assert session.get(Horta, horta.id) is None


def test_editor_e_lector_non_poden_eliminar_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        eliminar_horta(session, bea, horta)
    with pytest.raises(PermisoDenegadoError):
        eliminar_horta(session, carlos, horta)

    assert session.get(Horta, horta.id) is not None


def test_non_membro_non_pode_eliminar_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    denis = _crear_usuario(session, "denis@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(PermisoDenegadoError):
        eliminar_horta(session, denis, horta)

    assert session.get(Horta, horta.id) is not None


def test_eliminar_horta_elimina_tamen_parcelas_animais_e_membros(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    animal = crear_animal(session, ana, horta.id, "galiñas", datetime.date.today())

    # Unha segunda horta, allea á que se vai eliminar, para comprobar que o
    # borrado en cascada non lle afecta.
    outra_horta = crear_horta(session, ana, "Outra horta")
    outra_parcela = crear_parcela(session, ana, outra_horta.id, "Outra parcela")

    eliminar_horta(session, ana, horta)

    assert session.get(Parcela, parcela.id) is None
    assert session.get(Animal, animal.id) is None
    assert session.get(HortaMembro, (horta.id, ana.id)) is None

    assert session.get(Horta, outra_horta.id) is not None
    assert session.get(Parcela, outra_parcela.id) is not None
    assert session.get(HortaMembro, (outra_horta.id, ana.id)) is not None


def test_eliminar_horta_borra_en_cascada_cultivos_e_tratamentos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, datetime.date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    cultivo_id, tratamento_id = cultivo.id, tratamento.id

    eliminar_horta(session, ana, horta)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None


def test_eliminar_horta_borra_en_cascada_fertilizacions(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, datetime.date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    cultivo_id, fertilizacion_id = cultivo.id, fertilizacion.id

    eliminar_horta(session, ana, horta)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Fertilizacion, fertilizacion_id) is None

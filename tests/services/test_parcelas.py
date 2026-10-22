from datetime import date

import pytest

from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.fertilizacions import crear_fertilizacion
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.services.tarefas import crear_tarefa
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


def test_eliminar_parcela_desliga_tarefas_sen_borralas(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    tarefa = crear_tarefa(session, ana, horta.id, "Regar", parcela_id=parcela.id)

    eliminar_parcela(session, ana, parcela)

    session.refresh(tarefa)
    assert tarefa.parcela_id is None


def test_eliminar_parcela_borra_en_cascada_cultivos_e_tratamentos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    cultivo_id, tratamento_id = cultivo.id, tratamento.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None


def test_eliminar_parcela_borra_en_cascada_cultivo_con_tratamento_e_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "Orgánica", "Esterco"
    )
    cultivo_id, tratamento_id, fertilizacion_id = cultivo.id, tratamento.id, fertilizacion.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None
    assert session.get(Fertilizacion, fertilizacion_id) is None

def test_crear_parcela_con_coordenadas(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", lat=42.88, lon=-8.54)

    assert parcela.lat == 42.88
    assert parcela.lon == -8.54


def test_actualizar_campos_xeograficos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    actualizada = actualizar_parcela(
        session,
        ana,
        parcela,
        lat=42.88,
        lon=-8.54,
        geometria='{"type": "Polygon", "coordinates": []}',
        imaxe="parcelas/norte.jpg",
    )

    assert actualizada.lat == 42.88
    assert actualizada.lon == -8.54
    assert actualizada.geometria == '{"type": "Polygon", "coordinates": []}'
    assert actualizada.imaxe == "parcelas/norte.jpg"


def test_latitude_fora_de_rango(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A latitude debe estar entre -90 e 90"):
        crear_parcela(session, ana, horta.id, "Parcela Norte", lat=91)


def test_lonxitude_fora_de_rango(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    lon_orixinal = -180
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", lon=lon_orixinal)

    with pytest.raises(ValueError, match="A lonxitude debe estar entre -180 e 180"):
        actualizar_parcela(session, ana, parcela, lon=-181)

    session.refresh(parcela)
    assert parcela.lon == lon_orixinal

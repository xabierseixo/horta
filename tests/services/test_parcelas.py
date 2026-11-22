from datetime import date

import pytest

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.services.persoas import crear_contacto
from horta.services.tarefas import crear_tarefa


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


def test_eliminar_parcela_borra_en_cascada_cultivos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    cultivo_id = cultivo.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None


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


def test_superficie_negativa_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A superficie non pode ser negativa"):
        crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=-1.0)


def test_superficie_negativa_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=500.0)

    with pytest.raises(ValueError, match="A superficie non pode ser negativa"):
        actualizar_parcela(session, ana, parcela, superficie=-10.0)

    session.refresh(parcela)
    assert parcela.superficie == 500.0


def test_non_se_pode_eliminar_parcela_con_tratamentos_fito(session):
    from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    tratamento = TratamentoFito(
        horta_id=horta.id, data_inicio=date(2026, 5, 1), data_fin=date(2026, 5, 1)
    )
    tratamento.cultivos.append(TratamentoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1))
    session.add(tratamento)
    session.commit()

    with pytest.raises(ValueError, match="tratamentos fitosanitarios"):
        eliminar_parcela(session, ana, parcela)


@pytest.mark.parametrize(
    ("campos", "mensaxe"),
    [
        ({"arrendador_id": 999}, "non é desta explotación"),
        ({"data_alta": date(2026, 5, 1), "data_baixa": date(2026, 4, 1)}, "anterior á de alta"),
        ({"rexime_tenencia": "99"}, "non existe"),
    ],
)
def test_validacions_rea_da_parcela(session, campos, mensaxe):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_parcela(session, ana, horta.id, "P1", **campos)


def test_parcela_garda_sigpac_completo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", sigpac_agregado="0",
                            sigpac_zona="0", referencia_catastral="15078A00100023")
    arrendador = crear_contacto(session, ana, horta.id, "Arrendador", None, nif="12345678Z")
    actualizar_parcela(session, ana, parcela, arrendador_id=arrendador.id)
    assert (parcela.sigpac_zona, parcela.arrendador_id) == ("0", arrendador.id)


def test_xeometria_debuxada():
    from horta.services.parcelas import puntos_da_xeometria, xeometria_debuxada

    # Un cadrado de ~100 m de lado en Galicia (0,0009º de lat ≈ 100 m)
    puntos = [(42.8, -8.0), (42.8009, -8.0), (42.8009, -7.99878), (42.8, -7.99878)]
    geojson, hectareas, centro = xeometria_debuxada(puntos)
    assert 0.95 < hectareas < 1.05
    assert puntos_da_xeometria(geojson) == puntos
    assert centro == (42.80045, -7.99939)

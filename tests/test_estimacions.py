"""Probas do servizo de estimacións de colleita."""

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.estimacions import (
    borrar_estimacion,
    crear_estimacion,
    kg_ha_por_mostraxe,
    listar_estimacions,
    resumo_estimacion,
)
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 7, 10)


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


def _escenario(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(
        session,
        ana,
        cultivo,
        superficie_ha=0.5,
        obxectivo_colleita_kg_ha=10000.0,
        data_inicio=date(2026, 3, 1),
    )
    return ana, horta, cultivo


def test_calculo_por_mostraxe():
    # 10 000 plantas/ha, 2 froitos/planta, 250 g/froito -> 5 000 kg/ha
    assert kg_ha_por_mostraxe(10000.0, 2.0, 250.0) == 5000.0

    # Redondeo a 1 decimal: 33 333 * 1.5 * 120 / 1000 = 5999.94 -> 5999.9
    assert kg_ha_por_mostraxe(33333.0, 1.5, 120.0) == 5999.9

    # Valores menores ou iguais a cero levantan erro
    with pytest.raises(OperacionNonPermitidaError):
        kg_ha_por_mostraxe(0.0, 2.0, 250.0)
    with pytest.raises(OperacionNonPermitidaError):
        kg_ha_por_mostraxe(10000.0, -1.0, 250.0)
    with pytest.raises(OperacionNonPermitidaError):
        kg_ha_por_mostraxe(10000.0, 2.0, 0.0)


def test_crear_e_listar_estimacion_mostraxe(session):
    ana, _, cultivo = _escenario(session)
    est = crear_estimacion(
        session,
        ana,
        cultivo_id=cultivo.id,
        data=HOXE,
        metodo="mostraxe",
        plantas_ha=40000.0,
        unidades_planta=3.0,
        peso_unidade_g=150.0,
        notas="Mostraxe no sector norte",
    )
    assert est.kg_ha == 18000.0
    assert est.plantas_ha == 40000.0
    assert est.unidades_planta == 3.0
    assert est.peso_unidade_g == 150.0
    assert est.notas == "Mostraxe no sector norte"

    lista = listar_estimacions(session, ana, cultivo.id)
    assert len(lista) == 1
    assert lista[0].id == est.id


def test_crear_e_listar_estimacion_directa(session):
    ana, _, cultivo = _escenario(session)
    est = crear_estimacion(
        session,
        ana,
        cultivo_id=cultivo.id,
        data=HOXE,
        metodo="directa",
        kg_ha=12500.0,
    )
    assert est.kg_ha == 12500.0
    assert est.plantas_ha is None
    assert est.unidades_planta is None
    assert est.peso_unidade_g is None

    # A máis recente aparece de primeira na lista
    crear_estimacion(
        session,
        ana,
        cultivo_id=cultivo.id,
        data=date(2026, 7, 12),
        metodo="directa",
        kg_ha=13000.0,
    )
    lista = listar_estimacions(session, ana, cultivo.id)
    assert len(lista) == 2
    assert lista[0].kg_ha == 13000.0
    assert lista[1].kg_ha == 12500.0


@pytest.mark.parametrize(
    ("args", "mensaxe"),
    [
        ({"metodo": "outro", "kg_ha": 5000.0}, "Método non válido"),
        ({"metodo": "mostraxe", "plantas_ha": None, "unidades_planta": 2, "peso_unidade_g": 100},
         "plantas por hectárea"),
        ({"metodo": "mostraxe", "plantas_ha": 0, "unidades_planta": 2, "peso_unidade_g": 100},
         "plantas por hectárea"),
        ({"metodo": "mostraxe", "plantas_ha": 1000, "unidades_planta": None, "peso_unidade_g": 100},
         "unidades por planta"),
        ({"metodo": "mostraxe", "plantas_ha": 1000, "unidades_planta": -1, "peso_unidade_g": 100},
         "unidades por planta"),
        ({"metodo": "mostraxe", "plantas_ha": 1000, "unidades_planta": 2, "peso_unidade_g": None},
         "peso por unidade"),
        ({"metodo": "mostraxe", "plantas_ha": 1000, "unidades_planta": 2, "peso_unidade_g": 0},
         "peso por unidade"),
        ({"metodo": "directa", "kg_ha": None}, "kg/ha"),
        ({"metodo": "directa", "kg_ha": 0}, "kg/ha"),
        ({"metodo": "directa", "kg_ha": -500}, "kg/ha"),
    ],
)
def test_validacions_crear_estimacion(session, args, mensaxe):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_estimacion(
            session,
            ana,
            cultivo_id=cultivo.id,
            data=HOXE,
            **args,
        )


def test_cultivo_inexistente(session):
    ana = _crear_usuario(session, "ana@example.com")
    with pytest.raises(OperacionNonPermitidaError, match="cultivo non existe"):
        crear_estimacion(session, ana, cultivo_id=9999, data=HOXE, metodo="directa", kg_ha=1000.0)


def test_borrar_estimacion(session):
    ana, _, cultivo = _escenario(session)
    est = crear_estimacion(
        session, ana, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=5000.0
    )
    borrar_estimacion(session, ana, est.id)
    assert listar_estimacions(session, ana, cultivo.id) == []

    with pytest.raises(OperacionNonPermitidaError, match="non existe"):
        borrar_estimacion(session, ana, est.id)


def test_resumo_con_superficie_e_colleitas(session):
    ana, horta, cultivo = _escenario(session)
    # Sen estimacións
    res_baleiro = resumo_estimacion(session, ana, cultivo.id)
    assert res_baleiro.obxectivo_kg_ha == 10000.0
    assert res_baleiro.estimado_kg_ha is None
    assert res_baleiro.estimado_total_kg is None
    assert res_baleiro.colleitado_kg_ha is None
    assert res_baleiro.porcentaxe_colleitada is None

    # Engadimos estimación de 8 000 kg/ha
    crear_estimacion(
        session, ana, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=8000.0
    )
    res_con_est = resumo_estimacion(session, ana, cultivo.id)
    assert res_con_est.obxectivo_kg_ha == 10000.0
    assert res_con_est.estimado_kg_ha == 8000.0
    assert res_con_est.estimado_total_kg == 4000.0  # 8000 * 0.5 ha
    assert res_con_est.colleitado_kg_ha is None
    assert res_con_est.porcentaxe_colleitada is None

    # Apuntamos colleita real de 2 000 kg (sobre 0.5 ha son 4 000 kg/ha)
    datos_c = DatosColleita(
        cultivo_id=cultivo.id,
        data=HOXE,
        cantidade=2000.0,
        unidade="kg",
        lote="2026-PATACA-001",
        persoa_id=1,
    )
    crear_colleita(session, ana, datos_c, hoxe=HOXE)

    res_final = resumo_estimacion(session, ana, cultivo.id)
    assert res_final.colleitado_kg_ha == 4000.0
    # 4000 / 8000 * 100 = 50 %
    assert res_final.porcentaxe_colleitada == 50.0


def test_resumo_sen_superficie(session):
    ana, _, cultivo = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, superficie_ha=None)

    crear_estimacion(
        session, ana, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=8000.0
    )
    res = resumo_estimacion(session, ana, cultivo.id)
    assert res.estimado_kg_ha == 8000.0
    assert res.estimado_total_kg is None
    assert res.colleitado_kg_ha is None
    assert res.porcentaxe_colleitada is None


def test_permisos_usuario_alleo(session):
    ana, _, cultivo = _escenario(session)
    est = crear_estimacion(
        session, ana, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=5000.0
    )
    alleo = _crear_usuario(session, "alleo@example.com")

    with pytest.raises(PermisoDenegadoError):
        listar_estimacions(session, alleo, cultivo.id)

    with pytest.raises(PermisoDenegadoError):
        resumo_estimacion(session, alleo, cultivo.id)

    with pytest.raises(PermisoDenegadoError):
        crear_estimacion(
            session, alleo, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=4000.0
        )

    with pytest.raises(PermisoDenegadoError):
        borrar_estimacion(session, alleo, est.id)


def test_permisos_lector(session):
    ana, horta, cultivo = _escenario(session)
    est = crear_estimacion(
        session, ana, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=5000.0
    )
    lector = _crear_usuario(session, "lector@example.com")
    engadir_membro(session, ana, horta.id, lector, RolHorta.LECTOR)

    # Lector pode consultar pero non modificar
    assert len(listar_estimacions(session, lector, cultivo.id)) == 1
    assert resumo_estimacion(session, lector, cultivo.id).estimado_kg_ha == 5000.0

    with pytest.raises(PermisoDenegadoError):
        crear_estimacion(
            session, lector, cultivo_id=cultivo.id, data=HOXE, metodo="directa", kg_ha=6000.0
        )

    with pytest.raises(PermisoDenegadoError):
        borrar_estimacion(session, lector, est.id)

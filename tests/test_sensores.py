"""Probas para o servizo de sensores IoT, lecturas e avisos (tarefa 183a)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest

from horta.models.horta import RolHorta
from horta.models.sensor import LecturaDiaria, LecturaSensor
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.instalacions import crear_instalacion
from horta.services.parcelas import crear_parcela
from horta.services.sensores import (
    actualizar_sensor,
    avisos_sensores,
    baixa_sensor,
    compactar,
    consumo_periodo,
    crear_sensor,
    lecturas,
    listar_sensores,
    nova_clave,
    rexistrar_lecturas,
    sensor_da_clave,
    ultima_lectura,
)


def _crear_usuario(session, email: str, rol: RolGlobal = RolGlobal.USUARIO) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=rol,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _crear_usuario(session, "ana@example.com")
    pepe = _crear_usuario(session, "pepe@example.com")
    luis = _crear_usuario(session, "luis@example.com")
    alleo = _crear_usuario(session, "alleo@example.com")

    horta = crear_horta(session, ana, "Horta do Val")
    engadir_membro(session, ana, horta.id, pepe, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)
    return ana, pepe, luis, alleo, horta


def test_clave_e_hash(session):
    ana, _, _, _, horta = _escenario(session)

    sensor, clave = crear_sensor(session, ana, horta.id, "Sonda Chan 1", "humidade_chan")
    assert sensor.id is not None
    assert sensor.clave_hash != clave
    assert len(clave) >= 32

    # Recuperar sensor pola clave
    s_recuperado = sensor_da_clave(session, clave)
    assert s_recuperado is not None
    assert s_recuperado.id == sensor.id

    # Clave incorrecta devolve None
    assert sensor_da_clave(session, "clave-inventada") is None
    assert sensor_da_clave(session, "") is None

    # Xeración de nova clave invalida a anterior
    nova = nova_clave(session, ana, sensor.id)
    assert nova != clave
    assert sensor_da_clave(session, clave) is None
    assert sensor_da_clave(session, nova) is not None

    # Sensor dado de baixa non se recupera pola clave nin permite nova clave
    baixa_sensor(session, ana, sensor)
    assert sensor_da_clave(session, nova) is None
    with pytest.raises(OperacionNonPermitidaError):
        nova_clave(session, ana, sensor.id)


def test_rango_rexeitado(session):
    ana, _, _, _, horta = _escenario(session)

    sensor, _ = crear_sensor(
        session, ana, horta.id, "Termómetro Aire", "temperatura_aire"
    )
    agora = datetime(2026, 11, 9, 10, 0)

    # Rango válido: -40 a 60
    assert rexistrar_lecturas(session, sensor, [(agora, 21.5)], agora=agora) == 1

    # Valor menor ca o mínimo (-40)
    with pytest.raises(OperacionNonPermitidaError):
        rexistrar_lecturas(session, sensor, [(agora, -45.0)], agora=agora)

    # Valor maior ca o máximo (60)
    with pytest.raises(OperacionNonPermitidaError):
        rexistrar_lecturas(session, sensor, [(agora, 65.0)], agora=agora)

    # Momento máis de 10 minutos no futuro
    no_futuro = agora + timedelta(minutes=11)
    with pytest.raises(OperacionNonPermitidaError):
        rexistrar_lecturas(session, sensor, [(no_futuro, 22.0)], agora=agora)

    # Momento dentro do limiar de 10 minutos no futuro permítese
    futuro_proximo = agora + timedelta(minutes=5)
    assert rexistrar_lecturas(session, sensor, [(futuro_proximo, 22.0)], agora=agora) == 1

    # Tipo 'outro' sen límites acepta calquera valor
    outro_s, _ = crear_sensor(session, ana, horta.id, "Sensor Especial", "outro")
    assert rexistrar_lecturas(session, outro_s, [(agora, 99999.0)], agora=agora) == 1


def test_duplicados_ignorados(session):
    ana, _, _, _, horta = _escenario(session)

    sensor, _ = crear_sensor(session, ana, horta.id, "Higrómetro", "humidade_chan")
    t1 = datetime(2026, 11, 9, 8, 0)
    t2 = datetime(2026, 11, 9, 8, 30)
    t3 = datetime(2026, 11, 9, 9, 0)

    # Rexistro inicial de dúas lecturas
    gardadas = rexistrar_lecturas(session, sensor, [(t1, 40.0), (t2, 45.0)], agora=t3)
    assert gardadas == 2

    # Rexistro posterior: t2 é duplicado, só se garda t3
    gardadas2 = rexistrar_lecturas(session, sensor, [(t2, 45.0), (t3, 50.0)], agora=t3)
    assert gardadas2 == 1

    # Lote con duplicados internos
    t4 = datetime(2026, 11, 9, 9, 30)
    gardadas3 = rexistrar_lecturas(
        session, sensor, [(t4, 55.0), (t4, 55.0)], agora=t4
    )
    assert gardadas3 == 1

    # O total de lecturas gardadas na base de datos son 4
    total = session.query(LecturaSensor).filter_by(sensor_id=sensor.id).count()
    assert total == 4
    assert sensor.ultima_lectura_en == t4


def test_compactacion_lecturas_vellas(session):
    ana, _, _, _, horta = _escenario(session)

    sensor, _ = crear_sensor(
        session, ana, horta.id, "Sonda Compactación", "temperatura_chan"
    )
    hoxe = date(2026, 11, 9)
    d_vella = hoxe - timedelta(days=95)
    d_recente = hoxe - timedelta(days=10)

    t_vella_1 = datetime.combine(d_vella, time(8, 0))
    t_vella_2 = datetime.combine(d_vella, time(14, 0))
    t_vella_3 = datetime.combine(d_vella, time(20, 0))
    t_recente = datetime.combine(d_recente, time(12, 0))

    # Inserir lecturas vellas e recente
    session.add(LecturaSensor(sensor_id=sensor.id, momento=t_vella_1, valor=10.0))
    session.add(LecturaSensor(sensor_id=sensor.id, momento=t_vella_2, valor=20.0))
    session.add(LecturaSensor(sensor_id=sensor.id, momento=t_vella_3, valor=30.0))
    session.add(LecturaSensor(sensor_id=sensor.id, momento=t_recente, valor=15.0))
    session.commit()

    # Compactar para a data de hoxe
    compactar(session, sensor, hoxe)
    assert sensor.compactado_ata == hoxe

    # As 3 vellas borráronse de LecturaSensor e pasaron a LecturaDiaria
    cruas_restantes = (
        session.query(LecturaSensor).filter_by(sensor_id=sensor.id).all()
    )
    assert len(cruas_restantes) == 1
    assert cruas_restantes[0].momento == t_recente

    diaria = (
        session.query(LecturaDiaria)
        .filter_by(sensor_id=sensor.id, data=d_vella)
        .one()
    )
    assert diaria.minimo == 10.0
    assert diaria.maximo == 30.0
    assert diaria.media == 20.0
    assert diaria.n == 3

    # A función lecturas devolve tanto a compactada (ás 12:00) como a crua
    todas = lecturas(
        session,
        ana,
        sensor.id,
        desde=datetime(2026, 1, 1),
        ata=datetime(2026, 12, 31),
    )
    assert len(todas) == 2
    assert todas[0] == (datetime.combine(d_vella, time(12, 0)), 20.0)
    assert todas[1] == (t_recente, 15.0)


def test_consumo_contador(session):
    ana, _, _, _, horta = _escenario(session)

    sensor, _ = crear_sensor(
        session, ana, horta.id, "Contador Rega", "contador_auga"
    )
    t1 = datetime(2026, 11, 1, 8, 0)
    t2 = datetime(2026, 11, 2, 8, 0)
    t3 = datetime(2026, 11, 3, 8, 0)

    rexistrar_lecturas(
        session,
        sensor,
        [(t1, 120.0), (t2, 145.5), (t3, 170.0)],
        agora=t3,
    )

    consumo = consumo_periodo(session, ana, sensor.id, desde=t1, ata=t3)
    assert consumo == pytest.approx(50.0)

    # Sensor non acumulado devolve None
    sensor_non_acum, _ = crear_sensor(
        session, ana, horta.id, "Higro 2", "humidade_chan"
    )
    rexistrar_lecturas(
        session,
        sensor_non_acum,
        [(t1, 50.0), (t2, 60.0)],
        agora=t2,
    )
    assert consumo_periodo(session, ana, sensor_non_acum.id, desde=t1, ata=t2) is None


def test_avisos_limite_e_sen_datos(session):
    ana, _, _, _, horta = _escenario(session)

    sensor, _ = crear_sensor(
        session,
        ana,
        horta.id,
        "Sensor Invernadoiro",
        "temperatura_camara",
        limiar_min=5.0,
        limiar_max=25.0,
    )
    t1 = datetime(2026, 11, 8, 10, 0)

    # Lectura por debaixo do límite
    rexistrar_lecturas(session, sensor, [(t1, 2.0)], agora=t1)
    avisos_baixo = avisos_sensores(session, ana, horta.id, agora=t1)
    assert any("por debaixo do límite (5)" in a for a in avisos_baixo)

    # Lectura por riba do límite
    t2 = datetime(2026, 11, 8, 12, 0)
    rexistrar_lecturas(session, sensor, [(t2, 28.5)], agora=t2)
    avisos_riba = avisos_sensores(session, ana, horta.id, agora=t2)
    assert any("por riba do límite (25)" in a for a in avisos_riba)

    # Lectura sen datos desde hai máis de 24 h
    t_futuro_25h = t2 + timedelta(hours=25)
    avisos_sen_datos = avisos_sensores(session, ana, horta.id, agora=t_futuro_25h)
    assert any("sen datos desde 08/11 12:00" in a for a in avisos_sen_datos)

    # Dentro das 24 h non sae o aviso de sen datos
    t_futuro_5h = t2 + timedelta(hours=5)
    avisos_recente = avisos_sensores(session, ana, horta.id, agora=t_futuro_5h)
    assert not any("sen datos desde" in a for a in avisos_recente)


def test_permisos(session):
    ana, pepe, luis, alleo, horta = _escenario(session)

    # ADMIN (ana) pode crear, editar, dar de baixa e xerar nova clave
    sensor, clave = crear_sensor(
        session, ana, horta.id, "Sensor Permisos", "humidade_aire"
    )
    assert sensor.id is not None

    actualizar_sensor(session, ana, sensor, nome="Sensor Renomeado")
    assert sensor.nome == "Sensor Renomeado"

    nova = nova_clave(session, ana, sensor.id)
    assert nova is not None

    # LECTURA: ADMIN, EDITOR e LECTOR poden listar e ler
    assert len(listar_sensores(session, ana, horta.id)) == 1
    assert len(listar_sensores(session, pepe, horta.id)) == 1
    assert len(listar_sensores(session, luis, horta.id)) == 1

    t0 = datetime(2026, 11, 9, 8, 0)
    rexistrar_lecturas(session, sensor, [(t0, 70.0)], agora=t0)

    assert len(lecturas(session, luis, sensor.id, desde=t0, ata=t0)) == 1
    assert ultima_lectura(session, luis, sensor.id) is not None
    assert isinstance(avisos_sensores(session, luis, horta.id, agora=t0), list)

    # EDITOR (pepe) NON pode crear, editar, dar de baixa nin pedir nova clave
    with pytest.raises(PermisoDenegadoError):
        crear_sensor(session, pepe, horta.id, "Sensor Pepe", "humidade_aire")

    with pytest.raises(PermisoDenegadoError):
        actualizar_sensor(session, pepe, sensor, nome="Intento Pepe")

    with pytest.raises(PermisoDenegadoError):
        nova_clave(session, pepe, sensor.id)

    with pytest.raises(PermisoDenegadoError):
        baixa_sensor(session, pepe, sensor)

    # LECTOR (luis) tampouco ten permisos de escrita
    with pytest.raises(PermisoDenegadoError):
        crear_sensor(session, luis, horta.id, "Sensor Luis", "humidade_aire")

    with pytest.raises(PermisoDenegadoError):
        actualizar_sensor(session, luis, sensor, nome="Intento Luis")

    with pytest.raises(PermisoDenegadoError):
        nova_clave(session, luis, sensor.id)

    with pytest.raises(PermisoDenegadoError):
        baixa_sensor(session, luis, sensor)

    # Persoa allea non pode facer nada
    with pytest.raises(PermisoDenegadoError):
        listar_sensores(session, alleo, horta.id)

    with pytest.raises(PermisoDenegadoError):
        crear_sensor(session, alleo, horta.id, "Sensor Alleo", "humidade_aire")

    with pytest.raises(PermisoDenegadoError):
        lecturas(session, alleo, sensor.id, desde=t0, ata=t0)


def test_validacions_recursos_e_limiares(session):
    ana, _, _, _, horta = _escenario(session)
    outra_horta = crear_horta(session, ana, "Outra Horta Distinta")

    # Nome obrigatorio e tipo válido
    with pytest.raises(OperacionNonPermitidaError):
        crear_sensor(session, ana, horta.id, "", "humidade_chan")

    with pytest.raises(OperacionNonPermitidaError):
        crear_sensor(session, ana, horta.id, "S1", "tipo_inexistente")

    # Limiar min non pode ser maior ca max
    with pytest.raises(OperacionNonPermitidaError):
        crear_sensor(
            session,
            ana,
            horta.id,
            "S2",
            "temperatura_aire",
            limiar_min=30.0,
            limiar_max=10.0,
        )

    # Parcela doutra explotación
    parcela_allea = crear_parcela(session, ana, outra_horta.id, "Parcela Outra")
    with pytest.raises(OperacionNonPermitidaError):
        crear_sensor(
            session,
            ana,
            horta.id,
            "S3",
            "humidade_chan",
            parcela_id=parcela_allea.id,
        )

    # Instalación doutra explotación
    inst_allea = crear_instalacion(
        session, ana, outra_horta.id, tipo="almacen", nome="Almacén Outra"
    )
    with pytest.raises(OperacionNonPermitidaError):
        crear_sensor(
            session,
            ana,
            horta.id,
            "S4",
            "temperatura_camara",
            instalacion_id=inst_allea.id,
        )


def test_duplicado_con_zona_horaria_ignorase(session) -> None:
    """A mesma lectura con e sen zona horaria (UTC) gárdase unha vez."""
    from datetime import datetime, timezone

    from horta.services.sensores import crear_sensor, rexistrar_lecturas

    ana, _, _, _, horta = _escenario(session)
    sensor, _ = crear_sensor(session, ana, horta.id, "Chan", "humidade_chan")
    agora = datetime(2026, 11, 9, 12, 0)
    momento = datetime(2026, 11, 9, 10, 0)
    assert rexistrar_lecturas(session, sensor, [(momento, 30.0)], agora=agora) == 1
    con_zona = momento.replace(tzinfo=timezone.utc)
    assert rexistrar_lecturas(session, sensor, [(con_zona, 30.0)], agora=agora) == 0

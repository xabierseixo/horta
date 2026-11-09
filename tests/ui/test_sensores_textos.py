"""Probas das funcións puras de sensores e do rexistro da sección (tarefa 183c)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from horta.models.sensor import Sensor
from horta.services.necesidades_rega import NecesidadeRega
from horta.ui.layout import SECCIONS, normalizar_seccion, seccions_visibles, url_seccion
from horta.ui.necesidades_rega import texto_humidade_chan, texto_necesidade
from horta.ui.pages.sensores import (
    estado_sensor,
    opcions_grafica_sensor,
    texto_localizacion,
    texto_ultima_lectura,
)


def _crear_sensor_proba(
    nome: str = "Sensor 1",
    tipo: str = "humidade_chan",
    unidade: str = "%",
    limiar_min: float | None = None,
    limiar_max: float | None = None,
    cultivo_id: int | None = None,
    parcela_id: int | None = None,
    instalacion_id: int | None = None,
) -> Sensor:
    return Sensor(
        id=1,
        horta_id=1,
        nome=nome,
        tipo=tipo,
        unidade=unidade,
        clave_hash="hash-proba",
        limiar_min=limiar_min,
        limiar_max=limiar_max,
        cultivo_id=cultivo_id,
        parcela_id=parcela_id,
        instalacion_id=instalacion_id,
        activo=True,
    )


def test_rexistro_seccion_sensores():
    """Comproba que a sección sensores estea rexistrada despois de animais no menú."""
    claves = [s.clave for s in SECCIONS]
    assert "sensores" in claves
    idx_animais = claves.index("animais")
    idx_sensores = claves.index("sensores")
    assert idx_sensores == idx_animais + 1

    seccion_sen = next(s for s in SECCIONS if s.clave == "sensores")
    assert seccion_sen.etiqueta == "Sensores"
    assert seccion_sen.icona == "sensors"
    assert seccion_sen.grupo == "Produción"

    assert normalizar_seccion("sensores") == "sensores"
    assert url_seccion(3, "sensores") == "/hortas/3/sensores"

    visibles_lector = [s.clave for s in seccions_visibles(e_horta_admin=False)]
    assert "sensores" in visibles_lector

    visibles_admin = [s.clave for s in seccions_visibles(e_horta_admin=True)]
    assert "sensores" in visibles_admin


def test_estado_sensor_sen_datos():
    """Un sensor sen lecturas ou con lecturas de máis de 24 h ten estado «Sen datos»."""
    sensor = _crear_sensor_proba()
    agora = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)

    # Sen lectura
    assert estado_sensor(sensor, None, agora=agora) == "Sen datos"

    # Lectura de hai máis de 24 horas
    lectura_vella = (agora - timedelta(hours=25), 50.0)
    assert estado_sensor(sensor, lectura_vella, agora=agora) == "Sen datos"


def test_estado_sensor_fora_de_limite():
    """Un sensor con valor fóra dos limiares mínimo ou máximo ten estado «Fóra de límite»."""
    sensor = _crear_sensor_proba(limiar_min=20.0, limiar_max=80.0)
    agora = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
    recente = agora - timedelta(minutes=15)

    # Por debaixo do mínimo
    assert estado_sensor(sensor, (recente, 15.0), agora=agora) == "Fóra de límite"

    # Por riba do máximo
    assert estado_sensor(sensor, (recente, 85.0), agora=agora) == "Fóra de límite"


def test_estado_sensor_ben():
    """Un sensor con lecturas recentes dentro de límites ten estado «Ben»."""
    sensor = _crear_sensor_proba(limiar_min=20.0, limiar_max=80.0)
    agora = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
    recente = agora - timedelta(hours=2)

    # Dentro de límites
    assert estado_sensor(sensor, (recente, 45.0), agora=agora) == "Ben"

    # Sen límites configurados
    sensor_sen_limiar = _crear_sensor_proba(limiar_min=None, limiar_max=None)
    assert estado_sensor(sensor_sen_limiar, (recente, 99.0), agora=agora) == "Ben"


def test_texto_ultima_lectura():
    """Formata valor e momento da última lectura."""
    assert texto_ultima_lectura(None) == "—"

    momento = datetime(2026, 11, 9, 10, 30)
    assert texto_ultima_lectura((momento, 23.5), "°C") == "23.5 °C (09/11 10:30)"
    assert texto_ultima_lectura((momento, 40.0), "%") == "40 % (09/11 10:30)"
    assert texto_ultima_lectura((momento, 12.0), "") == "12 (09/11 10:30)"

    sensor = _crear_sensor_proba(unidade="mm")
    assert texto_ultima_lectura(sensor, (momento, 5.2)) == "5.2 mm (09/11 10:30)"


def test_texto_localizacion():
    """Indica se o sensor está nun cultivo, parcela, instalación ou xeral."""
    parcelas = {10: "Leira Grande"}
    cultivos = {20: "Tomateiros"}
    instalacions = {30: "Invernadoiro"}

    s_cultivo = _crear_sensor_proba(cultivo_id=20)
    assert (
        texto_localizacion(s_cultivo, parcelas, cultivos, instalacions)
        == "Cultivo: Tomateiros"
    )

    s_parcela = _crear_sensor_proba(parcela_id=10)
    assert (
        texto_localizacion(s_parcela, parcelas, cultivos, instalacions)
        == "Parcela: Leira Grande"
    )

    s_inst = _crear_sensor_proba(instalacion_id=30)
    assert (
        texto_localizacion(s_inst, parcelas, cultivos, instalacions)
        == "Instalación: Invernadoiro"
    )

    s_xeral = _crear_sensor_proba()
    assert texto_localizacion(s_xeral, parcelas, cultivos, instalacions) == "Xeral"


def test_opcions_grafica_sensor():
    """Xera a configuración de echart con datos e markLine para os límites."""
    sensor = _crear_sensor_proba(unidade="°C", limiar_min=10.0, limiar_max=30.0)

    # Sen lecturas devolve None
    assert opcions_grafica_sensor(sensor, []) is None

    # Con lecturas
    t1 = datetime(2026, 11, 9, 8, 0)
    t2 = datetime(2026, 11, 9, 9, 0)
    lecturas = [(t1, 15.2), (t2, 18.7)]

    opcions = opcions_grafica_sensor(sensor, lecturas)
    assert opcions is not None
    assert opcions["xAxis"]["data"] == ["09/11 08:00", "09/11 09:00"]
    assert opcions["yAxis"]["name"] == "°C"
    assert len(opcions["series"]) == 1

    serie = opcions["series"][0]
    assert serie["name"] == "Sensor 1"
    assert serie["data"] == [15.2, 18.7]
    assert "markLine" in serie
    mark_data = serie["markLine"]["data"]
    assert len(mark_data) == 2
    assert {"yAxis": 10.0, "name": "Mínimo"} in mark_data
    assert {"yAxis": 30.0, "name": "Máximo"} in mark_data


def test_opcions_grafica_sensor_sen_limiares():
    """Un sensor sen límites non inclúe markLine na gráfica."""
    sensor = _crear_sensor_proba(limiar_min=None, limiar_max=None)
    t1 = datetime(2026, 11, 9, 8, 0)
    opcions = opcions_grafica_sensor(sensor, [(t1, 20.0)])
    assert opcions is not None
    assert "markLine" not in opcions["series"][0]


def test_texto_humidade_chan_e_necesidade():
    """Comproba os textos de humidade do chan no servizo de necesidades de rega."""
    txt = texto_humidade_chan("Sonda Chan 1", 35.0)
    assert txt == "Humidade do chan agora: 35 % (sensor Sonda Chan 1)"

    n_ok = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=25.0,
        choiva_efectiva_mm=5.0,
        rega_mm=0.0,
        falta_mm=20.0,
        kc_actual=1.1,
        aproximado=False,
        dias_con_datos=7,
        et0_estimada=False,
    )

    # Sen sensor
    texto_sen = texto_necesidade(n_ok)
    assert "Faltan uns 20 l/m²" in texto_sen
    assert "Humidade do chan agora" not in texto_sen

    # Con sensor
    texto_con = texto_necesidade(n_ok, humidade_chan=38.4, nome_sensor="Sonda 2")
    assert "Faltan uns 20 l/m²" in texto_con
    assert "Humidade do chan agora: 38.4 % (sensor Sonda 2)" in texto_con

    # Con tupla
    texto_tupla = texto_necesidade(n_ok, humidade_chan=("Sonda 3", 42.0))
    assert "Humidade do chan agora: 42 % (sensor Sonda 3)" in texto_tupla

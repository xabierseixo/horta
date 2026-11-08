from __future__ import annotations

from datetime import date

from horta.models.cultivo import Cultivo
from horta.models.horta import Horta
from horta.models.observacion import LimiarPraga, ObservacionPraga
from horta.models.parcela import Parcela


def _crear_cultivo(session) -> Cultivo:
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()
    parcela = Parcela(horta_id=horta.id, nome="Parcela Norte", estado="activa")
    session.add(parcela)
    session.flush()
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.commit()
    return cultivo


def test_crear_e_ler_observacion_praga(session):
    cultivo = _crear_cultivo(session)
    parcela = session.get(Parcela, cultivo.parcela_id)
    assert parcela is not None
    horta_id = parcela.horta_id

    obs = ObservacionPraga(
        horta_id=horta_id,
        cultivo_id=cultivo.id,
        data=date(2026, 5, 10),
        problema_tipo="praga",
        problema_codigo="TUTA_ABSOLUTA",
        metodo="trampa",
        conto=12.5,
        unidade_conto="capturas por trampa",
        nivel="medio",
        estado_fenoloxico="floracion",
        notas="Trampa delta no centro da parcela",
    )
    session.add(obs)
    session.commit()

    recuperada = session.query(ObservacionPraga).filter_by(id=obs.id).one()
    assert recuperada.horta_id == horta_id
    assert recuperada.cultivo_id == cultivo.id
    assert recuperada.data == date(2026, 5, 10)
    assert recuperada.problema_tipo == "praga"
    assert recuperada.problema_codigo == "TUTA_ABSOLUTA"
    assert recuperada.metodo == "trampa"
    assert recuperada.conto == 12.5
    assert recuperada.unidade_conto == "capturas por trampa"
    assert recuperada.nivel == "medio"
    assert recuperada.estado_fenoloxico == "floracion"
    assert recuperada.notas == "Trampa delta no centro da parcela"
    assert recuperada.baixa is False


def test_observacion_praga_valores_por_defecto(session):
    cultivo = _crear_cultivo(session)
    parcela = session.get(Parcela, cultivo.parcela_id)
    assert parcela is not None

    obs = ObservacionPraga(
        horta_id=parcela.horta_id,
        cultivo_id=cultivo.id,
        data=date(2026, 6, 1),
        problema_tipo="enfermidade",
        problema_codigo="MILDIU",
        metodo="sintomas",
    )
    session.add(obs)
    session.commit()

    recuperada = session.get(ObservacionPraga, obs.id)
    assert recuperada is not None
    assert recuperada.conto is None
    assert recuperada.unidade_conto is None
    assert recuperada.nivel is None
    assert recuperada.estado_fenoloxico is None
    assert recuperada.notas is None
    assert recuperada.baixa is False


def test_crear_e_ler_limiar_praga(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.commit()

    limiar = LimiarPraga(
        horta_id=horta.id,
        cultivo_siex_codigo=101,
        problema_tipo="praga",
        problema_codigo="TUTA_ABSOLUTA",
        metodo="trampa",
        unidade_conto="capturas por trampa",
        valor=10.0,
        fonte="Guía GIP de solanáceas do MAPA, 2019",
    )
    session.add(limiar)
    session.commit()

    recuperado = session.query(LimiarPraga).filter_by(id=limiar.id).one()
    assert recuperado.horta_id == horta.id
    assert recuperado.cultivo_siex_codigo == 101
    assert recuperado.problema_tipo == "praga"
    assert recuperado.problema_codigo == "TUTA_ABSOLUTA"
    assert recuperado.metodo == "trampa"
    assert recuperado.unidade_conto == "capturas por trampa"
    assert recuperado.valor == 10.0
    assert recuperado.fonte == "Guía GIP de solanáceas do MAPA, 2019"
    assert recuperado.baixa is False


def test_limiar_praga_xeral_sen_cultivo_siex(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.commit()

    limiar = LimiarPraga(
        horta_id=horta.id,
        cultivo_siex_codigo=None,
        problema_tipo="mala_herba",
        problema_codigo="XERAL",
        metodo="mostraxe",
        unidade_conto="% de plantas",
        valor=20.0,
        fonte="Guía GIP xeral",
    )
    session.add(limiar)
    session.commit()

    recuperado = session.get(LimiarPraga, limiar.id)
    assert recuperado is not None
    assert recuperado.cultivo_siex_codigo is None
    assert recuperado.baixa is False

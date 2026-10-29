"""O tempo. As probas nunca usan a rede:
len exemplos gardados de MeteoGalicia (tests/datos/meteogalicia)."""

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from horta.models.persoa import Persoa
from horta.models.tempo import TempoDia, onde_e_cando
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.meteogalicia import (
    SenTempo,
    ler_avisos,
    ler_dias,
    ler_estacions,
    ler_predicion,
)
from horta.services.outros_traballos import DatosOutroTraballo, crear_outro_traballo
from horta.services.parcelas import crear_parcela
from horta.services.tempo import (
    aviso_distancia,
    avisos,
    avisos_tarefas,
    concellos,
    consultar_tempo,
    encher_tempo,
    gardar_lugar,
    por_distancia,
    tempo_do_traballo,
)

DATOS = Path(__file__).resolve().parents[1] / "datos" / "meteogalicia"
HOXE = date(2026, 10, 29)
MABEGONDO, TORRE, XIPRO = 10045, 10157, 10136


def _ler(nome):
    return json.loads((DATOS / nome).read_text(encoding="utf-8"))


class Exemplo:
    """MeteoGalicia de mentira: os exemplos gardados, e conta as consultas."""

    def __init__(self, falla=False):
        self.falla = falla
        self.consultas = []

    def estacions(self):
        return ler_estacions(_ler("estacions.json"))

    def dias(self, estacion_id, desde, ata):
        self.consultas.append((estacion_id, desde, ata))
        if self.falla:
            raise SenTempo("sen conexión")
        return [d for d in ler_dias(_ler("dias.json"))
                if d.estacion_id == estacion_id and desde <= d.data <= ata]

    def predicion(self, concello_ine):
        return ler_predicion(_ler("predicion.json"))

    def avisos(self, concello_ine):
        return ler_avisos(_ler("avisos.json"))


def _estacion(id_):
    return next(e for e in Exemplo().estacions() if e.id == id_)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    return ana, horta, quen


def test_le_os_datos_de_meteogalicia():
    [dia1, dia2] = ler_dias(_ler("dias.json"))
    assert (dia1.estacion_id, dia1.data) == (MABEGONDO, date(2026, 10, 1))
    assert dia1.medidas == {"t_min": 8.55, "t_max": 20.46, "t_media": 13.94, "choiva": 0.0,
                            "vento_medio": 1.14, "refacho": 8.5, "humidade": 83.0,
                            "et0": 2.63, "t_chan": 17.87, "horas_frio": 0.0,
                            "horas_sol": 9.8019, "balance_hidrico": -2.63}
    # O refacho do día 2 non está validado: queda baleiro
    assert dia2.medidas["refacho"] is None and dia2.medidas["vento_medio"] == 0.86
    assert {e.id for e in Exemplo().estacions()} == {MABEGONDO, TORRE, XIPRO}
    [hoxe, mañá] = ler_predicion(_ler("predicion.json"))
    assert (hoxe.data, hoxe.t_min, hoxe.t_max, hoxe.choiva_pct) == (HOXE, 10, 20, 5)
    assert concellos()["15078"] == "Santiago de Compostela" and len(concellos()) == 313


def test_estacion_mais_proxima_e_lonxe():
    # Unha leira en Abegondo, a uns centos de metros de Mabegondo
    [(primeira, km), *_] = por_distancia(Exemplo().estacions(), 43.245, -8.265)
    assert primeira.id == MABEGONDO and km < 1
    xipro = SimpleNamespace(lat=_estacion(XIPRO).lat, lon=_estacion(XIPRO).lon)
    assert aviso_distancia(xipro, 43.245, -8.265).startswith("A estación está a ")
    assert aviso_distancia(SimpleNamespace(lat=43.241, lon=-8.262), 43.245, -8.265) is None


def test_lugar_da_explotacion_e_da_parcela(session):
    ana, horta, _ = _escenario(session)
    gardar_lugar(session, ana, horta, "15001", _estacion(TORRE))
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    with pytest.raises(OperacionNonPermitidaError, match="concello"):
        gardar_lugar(session, ana, parcela, "99999", None)
    cultivo = crear_cultivo(session, ana, parcela.id, "Millo")
    sen_estacion = SimpleNamespace(horta_id=horta.id, data_inicio=date(2026, 10, 1),
                                   leiras=[SimpleNamespace(cultivo_id=cultivo.id)])
    # Sen estación na parcela, a da explotación
    assert onde_e_cando(session, sen_estacion) == (horta.id, TORRE, date(2026, 10, 1))
    gardar_lugar(session, ana, parcela, None, _estacion(MABEGONDO))
    assert onde_e_cando(session, sen_estacion)[1] == MABEGONDO


def test_o_traballo_garda_o_tempo_do_seu_dia(session):
    ana, horta, quen = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    gardar_lugar(session, ana, parcela, None, _estacion(MABEGONDO))
    fonte = Exemplo()
    tempo = consultar_tempo(session, fonte, MABEGONDO, date(2026, 10, 1), HOXE)
    assert (tempo.t_max, tempo.fonte) == (20.46, "MeteoGalicia")
    # Xa gardado: non se volve consultar nin se duplica
    assert consultar_tempo(session, fonte, MABEGONDO, date(2026, 10, 1), HOXE) is tempo
    assert len(fonte.consultas) == 1
    # O día de hoxe aínda non rematou
    assert consultar_tempo(session, fonte, MABEGONDO, HOXE, HOXE) is None
    traballo = crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 1), descricion="Peche",
        parcela_id=parcela.id, persoa_id=quen.id), hoxe=HOXE)
    assert traballo.tempo_id == tempo.id


def test_sen_conexion_apuntase_e_enchese_despois(session):
    ana, horta, quen = _escenario(session)
    gardar_lugar(session, ana, horta, None, _estacion(MABEGONDO))

    def apuntar(dia):
        return crear_outro_traballo(session, ana, DatosOutroTraballo(
            horta_id=horta.id, data_inicio=dia, descricion="Limpar", persoa_id=quen.id),
            hoxe=HOXE)

    sen_rede = Exemplo(falla=True)
    assert tempo_do_traballo(session, sen_rede, "outro_traballo", MABEGONDO,
                             date(2026, 10, 1), HOXE) is None
    primeiro, segundo, de_hoxe = (apuntar(date(2026, 10, 1)), apuntar(date(2026, 10, 2)),
                                  apuntar(HOXE))
    assert primeiro.tempo_id is None
    assert encher_tempo(session, ana, horta.id, sen_rede, HOXE) == 0
    fonte = Exemplo()
    assert encher_tempo(session, ana, horta.id, fonte, HOXE) == 2
    # Unha soa consulta para os dous días
    assert fonte.consultas == [(MABEGONDO, date(2026, 10, 1), date(2026, 10, 2))]
    assert primeiro.tempo_id and segundo.tempo_id and de_hoxe.tempo_id is None
    assert session.query(TempoDia).count() == 2


def test_avisos():
    def tempo(**medidas):
        return TempoDia(data=date(2026, 10, 1), **{"choiva": 0, "t_min": 5,
                                                   "vento_medio": 1, **medidas})

    assert avisos("abonado", tempo()) == []
    assert [a.split(":")[0] for a in avisos("abonado", tempo(choiva=12, t_min=-1))] == [
        "Choveu 12 l/m² ese día", "Xeou ese día"]
    assert "risco de deriva" in avisos("tratamento", tempo(vento_medio=4.2))[0]
    assert avisos("tratamento", tempo(vento_medio=3)) == []
    assert avisos("rega", tempo(), choiva_antes=8.5) == [
        "Choveron 8.5 l/m² nos dous días anteriores"]
    assert avisos("rega", tempo(), choiva_antes=0) == []


def test_avisos_das_tarefas_coa_predicion():
    from horta.models.tarefa import Tarefa
    from horta.services.meteogalicia import DiaPredicion

    predicion = [DiaPredicion(HOXE, 10, 20, 80, None), DiaPredicion(date(2026, 10, 30), 8, 21,
                                                                       10, None)]
    tarefas = [Tarefa(descricion="Cobre", tipo="tratamento", data=HOXE, estado="pendente"),
               Tarefa(descricion="Rega", tipo="rega", data=HOXE, estado="pendente"),
               Tarefa(descricion="Xofre", tipo="tratamento", data=date(2026, 10, 30),
                      estado="pendente")]
    assert avisos_tarefas(tarefas, predicion) == [
        "«Cobre» o 29/10: probabilidade de choiva do 80 %"]


def test_ceo_vento_uv_avisos_e_lua():
    from horta.services.lua import fase_lua
    from horta.services.meteogalicia import vento_texto

    [hoxe, _] = ler_predicion(_ler("predicion.json"))
    assert (hoxe.ceo, hoxe.vento, hoxe.uv) == ("Nubes altas", "Vento frouxo do Sudoeste", 3)
    assert (vento_texto(299), vento_texto(332), vento_texto(-9999)) == (
        "Calma", "Vento moi forte do Noroeste", None)
    # O nivel 0 (normalidade) non é aviso
    [aviso] = Exemplo().avisos("15078")
    assert (aviso.nivel, aviso.tipo, aviso.inicio.hour) == (1, "Refacho máximo de vento", 6)
    assert (fase_lua(date(2026, 10, 26)), fase_lua(date(2026, 11, 9))) == ("Lúa chea",
                                                                            "Lúa nova")


def test_rega_con_evapotranspiracion_e_horas_de_frio(session):
    from horta.services.tempo import horas_frio

    ana, horta, _ = _escenario(session)
    gardar_lugar(session, ana, horta, None, _estacion(MABEGONDO))
    fonte = Exemplo()
    tempo = tempo_do_traballo(session, fonte, "rega", MABEGONDO, date(2026, 10, 2), HOXE)
    assert tempo.info == [
        "Evapotranspiración ese día: 1.8 l/m² (a auga que perden o chan e as plantas)",
        "Balance hídrico dos 7 días: -4.4 l/m² (negativo: falta auga)"]
    # Unha soa consulta para os 7 días
    assert len(fonte.consultas) == 1
    assert horas_frio(session, fonte, MABEGONDO, HOXE) is None  # en outubro, aínda non

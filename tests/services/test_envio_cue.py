"""Envíos ao CUE da Xunta: só o novo e o cambiado, borrados, leiras alleas unha vez, faltas
fóra e o estado de cada actividade."""

import base64
import json
from datetime import date

import pytest
from test_cue import ATA, DESDE, HOXE, _escenario

from horta.models.envio_cue import RexistroCue
from horta.services.envio_cue import (
    avisos_cue,
    comprobar,
    enviar,
    estado_cue,
    preparar_envio,
    proxima_data_limite,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.leiras import LeiraTraballo
from horta.services.regas import DatosRega, crear_rega, dar_de_baixa_rega
from horta.services.xeaga import Mensaxe, Resultado, ler_token


def _token(nif="12345678Z"):
    carga = base64.urlsafe_b64encode(json.dumps({"cif": nif, "exp": 4_000_000_000})
                                     .encode()).decode().rstrip("=")
    return ler_token(f"c.{carga}.s")


class _Xeaga:
    """Fai de Xunta: garda o enviado e responde co que se lle diga."""

    def __init__(self):
        self.enviados, self.estado = [], None

    def crear(self, token, cuaderno):
        self.enviados.append(cuaderno)
        return 100 + len(self.enviados)

    def comprobar_estado(self, token, peticion):
        return self.estado


def _rega(session, ana, leira, quen, cantidade=20):
    return crear_rega(session, ana, DatosRega(
        leiras=[LeiraTraballo(leira.id)], data_inicio=date(2026, 6, 1), sistema_rega="6",
        cantidade=cantidade, unidade="3", persoa_id=quen.id), hoxe=HOXE)


def test_so_vai_o_novo_e_o_cambiado(session):
    ana, horta, quen, (uno, _) = _escenario(session)
    _rega(session, ana, uno, quen)
    xunta = _Xeaga()
    primeiro = enviar(session, ana, horta.id, DESDE, ATA, xunta, _token())
    assert primeiro.peticion == 101
    [cuaderno] = xunta.enviados
    # As dúas leiras teñen sementeira no período
    assert len(cuaderno["DatosExplotacion"]["AltaDGC"]) == 2
    assert len(cuaderno["ActividadesExplotacion"]["Riego"]) == 1
    # Sen cambios, non hai nada que enviar
    assert enviar(session, ana, horta.id, DESDE, ATA, xunta, _token()) is None


def test_a_baixa_dun_enviado_vai_con_borrar_e_a_leira_non_se_repite(session):
    ana, horta, quen, (uno, _) = _escenario(session)
    rega = _rega(session, ana, uno, quen)
    xunta = _Xeaga()
    enviar(session, ana, horta.id, DESDE, ATA, xunta, _token())
    dar_de_baixa_rega(session, ana, rega)
    preparado = preparar_envio(session, ana, horta.id, DESDE, ATA)
    [borrar] = preparado.cuaderno["ActividadesExplotacion"]["Riego"]
    assert borrar["Borrar"] is True and borrar["IdAjenaRiego"] == rega.id * 100
    # A sementeira segue igual e a leira allea xa foi: non se repiten
    assert "AltaDGC" not in preparado.cuaderno["DatosExplotacion"]
    assert "SiembraPlantacion" not in preparado.cuaderno["ActividadesExplotacion"]


def test_o_que_ten_faltas_queda_fora(session):
    ana, horta, quen, (uno, _) = _escenario(session)
    crear_rega(session, ana, DatosRega(leiras=[LeiraTraballo(uno.id)],
                                       data_inicio=date(2026, 6, 1), persoa_id=quen.id),
               hoxe=HOXE)
    preparado = preparar_envio(session, ana, horta.id, DESDE, ATA)
    assert "Riego" not in preparado.cuaderno["ActividadesExplotacion"]
    assert {f.falta for f in preparado.fora} >= {"o sistema de rega", "a cantidade"}


def test_so_envia_o_titular(session):
    ana, horta, quen, (uno, _) = _escenario(session)
    _rega(session, ana, uno, quen)
    with pytest.raises(OperacionNonPermitidaError, match="non é o titular"):
        enviar(session, ana, horta.id, DESDE, ATA, _Xeaga(), _token("99999999R"))


def test_comprobar_anota_aceptado_erro_e_pechado(session):
    ana, horta, quen, (uno, dous) = _escenario(session)
    boa, mala = _rega(session, ana, uno, quen), _rega(session, ana, dous, quen, 30)
    xunta = _Xeaga()
    envio = enviar(session, ana, horta.id, DESDE, ATA, xunta, _token())
    xunta.estado = Resultado("PARCIAL", [Mensaxe(12, "Recinto non válido")], cuaderno=[{
        "ActividadesExplotacion": {"Riego": [
            {"IdAjenaRiego": boa.id * 100, "esValida": True, "IdCuaderno": 36},
            {"IdAjenaRiego": mala.id * 100, "esValida": False, "IdCuaderno": 36}]}}])
    comprobar(session, ana, envio, xunta, _token())
    estados = estado_cue(session, ana, horta.id)
    assert estados[("rega", boa.id)] == "aceptado"
    assert estados[("rega", mala.id)] == "erro"
    erro = session.query(RexistroCue).filter_by(bloque="Riego", id_ajena=mala.id * 100).one()
    assert "Recinto" in erro.mensaxe
    # A actividade con erro vólvese enviar; a aceptada non
    [reenvio] = preparar_envio(session, ana, horta.id, DESDE, ATA).cuaderno[
        "ActividadesExplotacion"]["Riego"]
    assert reenvio["IdAjenaRiego"] == mala.id * 100


def test_datas_limite_e_avisos(session):
    assert proxima_data_limite(date(2026, 10, 30)) == date(2027, 3, 31)
    assert proxima_data_limite(date(2026, 9, 30)) == date(2026, 9, 30)
    ana, horta, quen, (uno, dous) = _escenario(session)
    # Sen ningún envío desde horta, Inicio non avisa
    assert avisos_cue(session, ana, horta.id, date(2026, 9, 10)) == []
    _rega(session, ana, uno, quen)
    enviar(session, ana, horta.id, DESDE, ATA, _Xeaga(), _token())
    _rega(session, ana, dous, quen, 30)
    assert any("30/09/2026" in a for a in avisos_cue(session, ana, horta.id, date(2026, 9, 10)))
    assert avisos_cue(session, ana, horta.id, date(2026, 7, 1)) == []

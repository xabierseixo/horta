"""Caderno, folla 5: a venda dun lote mesturado leva as parcelas de todas as orixes."""

from datetime import date
from io import BytesIO

from openpyxl import load_workbook
from test_cue_lote_mesturado import HOXE, _escenario

from horta.models.lote import Lote, Mestura, MesturaOrixe
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.lotes import DatosSaida, crear_saida, ficha_para


def test_venda_dun_lote_mesturado(session):
    ana, horta, quen, c1, c2 = _escenario(session)
    lotes = [crear_colleita(session, ana, DatosColleita(
        cultivo_id=c.id, data=date(2026, 8, 1), cantidade=50.0, unidade="kg", lote=codigo,
        persoa_id=quen.id), hoxe=HOXE).lote_id for c, codigo in ((c1, "L-T"), (c2, "L-P"))]
    ficha = ficha_para(session, horta.id, "Mestura", "kg")
    mesturado = Lote(horta_id=horta.id, codigo="L-M", produto="Mestura", unidade="kg",
                     produto_venda_id=ficha.id, data=date(2026, 8, 3))
    session.add(mesturado)
    session.flush()
    session.add(Mestura(horta_id=horta.id, data=date(2026, 8, 3), lote_id=mesturado.id,
                        orixes=[MesturaOrixe(lote_id=lote, cantidade=10.0) for lote in lotes]))
    session.commit()
    crear_saida(session, ana, DatosSaida(
        lote_id=mesturado.id, data=date(2026, 8, 4), tipo="venda", cantidade=15.0,
        unidade="kg", canle="mercado", persoa_id=quen.id), hoxe=HOXE)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["5 Colleita"].iter_rows(min_row=5, values_only=True)))
    assert fila[3] == "1, 2"

"""Z11: vender en 2027 o colleitado en 2026 leva no caderno de 2027 a parcela de orixe."""

from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.parcelas import crear_parcela

QUEN = 1


def test_venda_do_ano_seguinte_sae_coa_parcela(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P")
    vello = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, vello, data_inicio=date(2026, 3, 1),
                       data_fin=date(2026, 9, 30))
    colleita = crear_colleita(session, ana, DatosColleita(
        persoa_id=QUEN, cultivo_id=vello.id, data=date(2026, 9, 1), cantidade=200,
        unidade="kg", lote="2026-PATACA-001"), hoxe=date(2026, 10, 25))
    crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2027, 2, 3), tipo="venda", cantidade=150,
        unidade="kg", canle="mercado", persoa_id=QUEN), hoxe=date(2027, 3, 1))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2027, 1, 1),
                                                date(2027, 12, 31))))
    fila = list(next(libro["5 Colleita"].iter_rows(min_row=5, values_only=True)))
    assert fila[3] == "1"
    # O número 1 ten que estar na folla 2, onde se di que cultivo e parcela é
    numeros = [f[0] for f in libro["2 Parcelas"].iter_rows(min_row=5, values_only=True)
               if f[0] is not None]
    assert 1 in numeros

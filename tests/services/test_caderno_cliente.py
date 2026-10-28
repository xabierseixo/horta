"""Caderno, folla 5 (colleita comercializada): sae das vendas dos lotes de colleitas, co
cliente da súa ficha."""

from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1


def test_cliente_da_venda_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Pataca")
    colleita = crear_colleita(session, ana, DatosColleita(
        persoa_id=QUEN, cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=200,
        unidade="kg", lote="2026-PATACA-001"), hoxe=date(2026, 10, 25))
    cliente = crear_contacto(session, ana, horta.id, "Froitas Melide SL", "cliente",
                             tipo="entidade", nif="B15000000", enderezo="Rúa do Mercado 2")
    crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2026, 9, 3), tipo="venda", cantidade=150,
        unidade="kg", canle="almacen", comprador_id=cliente.id, albaran_factura="A-7",
        persoa_id=QUEN), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["5 Colleita"].iter_rows(min_row=5, values_only=True)))
    assert fila[2] == 150
    assert fila[4:9] == ["A-7", "2026-PATACA-001", "Froitas Melide SL", "B15000000",
                         "Rúa do Mercado 2"]

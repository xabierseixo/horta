"""Transformación e páxina pública do lote (paso 17)."""

from datetime import date

import pytest

from horta.models.lote import Lote
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.clasificacions import (
    DatosTransformacion,
    InsumoTransformacion,
    OrixeMestura,
    crear_transformacion,
)
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.lotes import DatosSaida, crear_saida, queda
from horta.services.parcelas import crear_parcela
from horta.services.produtos import DatosEntrada, crear_entrada, crear_produto, existencias
from horta.services.trazabilidade import publicar_lote, trazabilidade_publica

HOXE = date(2026, 10, 28)


def test_transformar_e_publicar(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta da Ana")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Leira").id,
                            "Pemento")
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=30, unidade="kg", lote="P-1",
        persoa_id=quen.id), hoxe=HOXE)
    aceite = crear_produto(session, ana, horta.id, "outro", "Aceite", "litros")
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=aceite.id, data=date(2026, 8, 1), persoa_id=quen.id, cantidade=5,
        unidade="litros", lote_provedor="AC-77"), hoxe=HOXE)
    datos = DatosTransformacion(
        data=date(2026, 9, 3), produto="Conserva de pemento", unidade="unidades",
        cantidade=40, entradas=[OrixeMestura(lote_id=colleita.lote_id, cantidade=20)],
        insumos=[InsumoTransformacion(produto_id=aceite.id, cantidade=2,
                                      entrada_id=compra.id)], persoa_id=quen.id)
    tr = crear_transformacion(session, ana, horta.id, datos, hoxe=HOXE)
    conserva = session.get(Lote, tr.lote_id)
    assert queda(session, conserva) == 40
    assert queda(session, session.get(Lote, colleita.lote_id)) == 10
    assert existencias(session, aceite).queda == 3
    with pytest.raises(OperacionNonPermitidaError, match="só quedan 10"):
        crear_transformacion(session, ana, horta.id, DatosTransformacion(
            data=date(2026, 9, 4), produto="Conserva de pemento", unidade="unidades",
            cantidade=5, entradas=[OrixeMestura(lote_id=colleita.lote_id, cantidade=11)],
            persoa_id=quen.id),
            hoxe=HOXE)
    crear_saida(session, ana, DatosSaida(
        lote_id=conserva.id, data=date(2026, 9, 5), tipo="venda", cantidade=10,
        unidade="unidades", persoa_id=quen.id, canle="explotacion"), hoxe=HOXE)
    token = publicar_lote(session, ana, conserva)
    traz, explotacion = trazabilidade_publica(session, token)
    textos = " ".join(ln.texto for ln in traz.orixe)
    assert explotacion == "Horta da Ana"
    assert "do lote P-1" in textos and "lote do provedor AC-77" in textos
    assert "Colleita de Pemento" in textos
    # A quen se vendeu non sae nunca na páxina pública
    assert traz.saidas == []
    assert trazabilidade_publica(session, "inventado") is None

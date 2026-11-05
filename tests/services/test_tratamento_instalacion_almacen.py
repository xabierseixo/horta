"""Z8: o produto dun tratamento de almacén, local ou transporte desconta das existencias."""

from datetime import date

import pytest
from test_tratamentos_instalacion import HOXE, _datos, _escenario

from horta.models.persoa import Persoa
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.produtos import (
    DatosEntrada,
    crear_entrada,
    crear_produto,
    dar_de_baixa_entrada,
    existencias,
)
from horta.services.tratamentos_instalacion import (
    crear_tratamento_instalacion,
    dar_de_baixa_tratamento_instalacion,
)


def _compra(session, ana, horta, nome="Biocida X"):
    produto = crear_produto(session, ana, horta.id, "fitosanitario", nome, "litros")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).first()
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 3, 1), persoa_id=quen.id, cantidade=10,
        unidade="litros"), hoxe=HOXE)
    return produto, compra


def test_desconta_o_produto_usado(session):
    ana, horta = _escenario(session)
    produto, compra = _compra(session, ana, horta)
    t = crear_tratamento_instalacion(session, ana, horta.id, _datos(
        produto_id=produto.id, entrada_id=compra.id, cantidade_utilizada=2, unidade="4"),
        hoxe=HOXE)
    assert existencias(session, produto).queda == 8
    with pytest.raises(OperacionNonPermitidaError, match="xa se usou"):
        dar_de_baixa_entrada(session, ana, compra)
    dar_de_baixa_tratamento_instalacion(session, ana, t)
    assert existencias(session, produto).queda == 10


def test_o_produto_ten_que_ser_da_explotacion(session):
    ana, horta = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    produto, _ = _compra(session, ana, outra)
    with pytest.raises(OperacionNonPermitidaError, match="Ese produto non é"):
        crear_tratamento_instalacion(session, ana, horta.id, _datos(produto_id=produto.id),
                                     hoxe=HOXE)


def test_a_compra_ten_que_ser_do_produto(session):
    ana, horta = _escenario(session)
    produto, _ = _compra(session, ana, horta)
    _, outra_compra = _compra(session, ana, horta, "Biocida Y")
    with pytest.raises(OperacionNonPermitidaError, match="doutro produto"):
        crear_tratamento_instalacion(session, ana, horta.id, _datos(
            produto_id=produto.id, entrada_id=outra_compra.id), hoxe=HOXE)


"""Abonos líquidos: o gasto desconta en litros (G3) e o abono propio pódese corrixir e
retirar (Z4)."""

from datetime import date

import pytest
from test_produtos import HOXE, _escenario

from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import (
    DatosFertilizante,
    actualizar_fertilizante,
    crear_fertilizante,
    listar_fertilizantes,
    retirar_fertilizante,
)
from horta.services.produtos import DatosEntrada, crear_entrada, existencias, listar_produtos


def _purin(session, ana, horta, densidade=None):
    return crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Purín", material="14", liquido=True, densidade=densidade))


def _compra_e_abonado(session, ana, horta, quen, cultivo, purin, dose, unidade):
    [produto] = listar_produtos(session, ana, horta.id, tipo="abono")
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 3, 1), persoa_id=quen.id,
        cantidade=5000, unidade="litros"), hoxe=HOXE)
    crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=date(2026, 3, 10), fertilizante_id=purin.id,
        dose=dose, unidade=unidade, entrada_id=compra.id, persoa_id=quen.id), hoxe=HOXE)
    return existencias(session, produto)


def test_liquido_en_litros_por_hectarea_desconta_sen_densidade(session):
    ana, horta, quen, cultivo = _escenario(session)
    # 10 000 L/ha en 0,1 ha: 1000 L
    conta = _compra_e_abonado(session, ana, horta, quen, cultivo, _purin(session, ana, horta),
                              10000, "18")
    assert (conta.usado, conta.queda, conta.sen_contar) == (1000, 4000, 0)


def test_liquido_en_m3_por_hectarea(session):
    ana, horta, quen, cultivo = _escenario(session)
    conta = _compra_e_abonado(session, ana, horta, quen, cultivo, _purin(session, ana, horta),
                              20, "19")
    assert conta.usado == 2000


def test_liquido_en_kg_por_hectarea_coa_densidade(session):
    ana, horta, quen, cultivo = _escenario(session)
    # 2000 kg/ha en 0,1 ha = 200 kg; con 1,25 kg/L son 160 L
    conta = _compra_e_abonado(session, ana, horta, quen, cultivo,
                              _purin(session, ana, horta, densidade=1.25), 2000, "17")
    assert conta.usado == pytest.approx(160)


def test_corrixir_o_abono(session):
    ana, horta, _, _ = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco de vca", material="14", n_pct=5))
    actualizar_fertilizante(session, ana, abono, DatosFertilizante(
        nome="Esterco de vaca", material="14", n_pct=0.5, liquido=True, densidade=1.1))
    assert (abono.nome, abono.n_pct, abono.liquido, abono.densidade) == (
        "Esterco de vaca", 0.5, True, 1.1)
    [produto] = listar_produtos(session, ana, horta.id, tipo="abono")
    assert (produto.nome, produto.unidade) == ("Esterco de vaca", "litros")


def test_non_se_cambia_a_liquido_se_xa_ten_compras(session):
    ana, horta, quen, _ = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco", material="14"))
    [produto] = listar_produtos(session, ana, horta.id, tipo="abono")
    crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 3, 1), persoa_id=quen.id, cantidade=100,
        unidade="kg"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="compras ou usos"):
        actualizar_fertilizante(session, ana, abono, DatosFertilizante(
            nome="Esterco", material="14", liquido=True))


def test_nome_repetido_ao_corrixir(session):
    ana, horta, _, _ = _escenario(session)
    crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="A", material="14"))
    b = crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="B", material="14"))
    with pytest.raises(OperacionNonPermitidaError, match="Xa tes un abono chamado A"):
        actualizar_fertilizante(session, ana, b, DatosFertilizante(nome="A", material="14"))


def test_retirar_o_abono(session):
    ana, horta, _, _ = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Vello", material="14"))
    retirar_fertilizante(session, ana, abono)
    assert listar_fertilizantes(session, ana, horta.id) == []
    assert listar_fertilizantes(session, ana, horta.id, incluir_inactivos=True) == [abono]

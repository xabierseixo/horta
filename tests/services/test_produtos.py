"""Produtos e entradas (compras) e as existencias
."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.animais import crear_animal
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.cue import xerar_cue
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
from horta.services.produtos import (
    DatosEntrada,
    crear_entrada,
    crear_produto,
    existencias,
    listar_produtos,
)

HOXE = date(2026, 10, 29)


def _escenario(session):
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="f" * 64, filas=0)
    session.add(version)
    session.flush()
    session.add(CatalogoValor(catalogo="material_fertilizante", codigo="14", descricion="14",
                              version_id=version.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Millo")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.1)
    return ana, horta, quen, cultivo


def test_compra_e_uso_dun_abono(session):
    ana, horta, quen, cultivo = _escenario(session)
    npk = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK 15-15-15", material="14", n_pct=15))
    [produto] = listar_produtos(session, ana, horta.id, tipo="abono")
    coop = crear_contacto(session, ana, horta.id, "Coop. Ulla", "provedor", tipo="entidade")
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 3, 1), persoa_id=quen.id, provedor_id=coop.id,
        cantidade=25, unidade="kg", albaran_factura="A-1", importe=30), hoxe=HOXE)
    # 200 kg/ha en 0,1 ha: 20 kg
    crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=date(2026, 3, 10), fertilizante_id=npk.id,
        dose=200, unidade="17", entrada_id=compra.id, persoa_id=quen.id), hoxe=HOXE)
    conta = existencias(session, produto)
    assert (conta.entrou, conta.usado, conta.queda, conta.sen_contar) == (25, 20, 5, 0)
    # O CUE colle o provedor e o albará da compra
    [ferti] = xerar_cue(session, ana, horta.id, date(2026, 1, 1),
                        date(2026, 12, 31)).datos["ActividadesExplotacion"]["Fertilizacion"]
    assert ferti["MaterialFertilizante"]["EmpresaSuministradora"] == "Coop. Ulla"
    assert ferti["AplicacionMaterialFertilizante"]["AlbaranFactura"] == "A-1"


def test_a_compra_ten_que_ser_do_mesmo_produto(session):
    ana, horta, quen, cultivo = _escenario(session)
    npk = crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="NPK", material="14"))
    penso = crear_produto(session, ana, horta.id, "penso", "Penso galiñas", "kg")
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=penso.id, data=date(2026, 3, 1), persoa_id=quen.id, cantidade=10),
        hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="doutro produto"):
        crear_abonado(session, ana, DatosAbonado(
            cultivo_id=cultivo.id, data_inicio=date(2026, 3, 10), fertilizante_id=npk.id,
            dose=100, unidade="17", entrada_id=compra.id, persoa_id=quen.id), hoxe=HOXE)


def test_medicamento_e_uso_sen_cantidade(session):
    ana, horta, quen, _ = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=quen.id, medicamento="Oxitetraciclina", tempo_espera_dias=7), hoxe=HOXE)
    [medicamento] = listar_produtos(session, ana, horta.id, tipo="medicamento")
    assert medicamento.nome == "Oxitetraciclina"
    # Un uso sen cantidade non se conta: o que queda non é seguro
    assert existencias(session, medicamento).sen_contar == 1


def test_medicamento_conversion_e_resta_de_existencias(session):
    ana, horta, quen, _ = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    liquido = crear_produto(session, ana, horta.id, "medicamento", "Ivermectina", "litros")
    crear_entrada(session, ana, DatosEntrada(
        produto_id=liquido.id, data=date(2026, 3, 1), persoa_id=quen.id, cantidade=1),
        hoxe=HOXE)
    for cantidade, unidade in ((250, "ml"), (0.5, "L")):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
            persoa_id=quen.id, produto_id=liquido.id, cantidade=cantidade, unidade=unidade,
            tempo_espera_dias=7), hoxe=HOXE)
    # Tamén conta o que xa estaba gardado co código do catálogo ("4" = L)
    vello = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 21), tipo="medicamento",
        persoa_id=quen.id, produto_id=liquido.id, cantidade=0.1, tempo_espera_dias=7),
        hoxe=HOXE)
    vello.unidade = "4"
    session.commit()
    conta_l = existencias(session, liquido)
    assert (conta_l.entrou, conta_l.usado, conta_l.queda, conta_l.sen_contar) == (
        1.0, 0.85, 0.15, 0)

    po = crear_produto(session, ana, horta.id, "medicamento", "Amoxicilina", "kg")
    crear_entrada(session, ana, DatosEntrada(
        produto_id=po.id, data=date(2026, 3, 1), persoa_id=quen.id, cantidade=1), hoxe=HOXE)
    for cantidade, unidade in ((200, "g"), (0.3, "kg")):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
            persoa_id=quen.id, produto_id=po.id, cantidade=cantidade, unidade=unidade,
            tempo_espera_dias=7), hoxe=HOXE)
    conta_kg = existencias(session, po)
    assert (conta_kg.entrou, conta_kg.usado, conta_kg.queda, conta_kg.sen_contar) == (
        1.0, 0.5, 0.5, 0)

    # Unidade incompatible co produto (g nun produto en litros) → queda sen contar
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 22), tipo="medicamento",
        persoa_id=quen.id, produto_id=liquido.id, cantidade=100, unidade="g",
        tempo_espera_dias=7), hoxe=HOXE)
    assert existencias(session, liquido).sen_contar == 1


def test_validacions_da_entrada(session):
    ana, horta, quen, _ = _escenario(session)
    penso = crear_produto(session, ana, horta.id, "penso", "Penso", "kg")
    for cambios, erro in (({"cantidade": -1}, "maior que 0"), ({"unidade": "unidades"}, "kg"),
                          ({"data": date(2026, 11, 1)}, "futura"), ({"persoa_id": None}, "quen")):
        datos = {"produto_id": penso.id, "data": date(2026, 3, 1), "persoa_id": quen.id,
                 "cantidade": 10, "unidade": "kg", **cambios}
        with pytest.raises(OperacionNonPermitidaError, match=erro):
            crear_entrada(session, ana, DatosEntrada(**datos), hoxe=HOXE)


def test_diario_e_explotacion_con_compras(session):
    ana, horta, quen, _ = _escenario(session)
    penso = crear_produto(session, ana, horta.id, "penso", "Penso", "kg")
    crear_entrada(session, ana, DatosEntrada(produto_id=penso.id, data=date(2026, 3, 1),
                                             persoa_id=quen.id, cantidade=50), hoxe=HOXE)
    [traballo] = [t for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)
                  if t.tipo == "entrada_produto"]
    assert traballo.que == "Entrada: 50 kg de Penso"
    with pytest.raises(OperacionNonPermitidaError, match="compras"):
        eliminar_horta(session, ana, horta)

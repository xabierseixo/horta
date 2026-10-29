"""Lotes e saídas."""

from datetime import date

import pytest

from horta.models.lote import ProdutoVenda
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.colleitas import (
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    dar_de_baixa_colleita,
)
from horta.services.cultivos import crear_cultivo
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.lotes import (
    DatosSaida,
    actualizar_ficha,
    actualizar_lote,
    avisos_saida,
    converter,
    crear_saida,
    dar_de_baixa_saida,
    listar_lotes,
    queda,
    resumo_lotes,
)
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
from horta.services.producions_animais import DatosProducion, crear_producion
from horta.services.tarefas import crear_tarefa

HOXE = date(2026, 10, 28)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Leira").id,
                            "Pataca")
    return ana, horta, quen, cultivo


def _colleita(session, ana, cultivo, quen, cantidade=100.0, unidade="kg", lote="L-1"):
    return crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=cantidade, unidade=unidade,
        lote=lote, persoa_id=quen.id), hoxe=HOXE)


def _saida(colleita, quen, **cambios):
    datos = {"lote_id": colleita.lote_id, "data": date(2026, 9, 5), "tipo": "casa",
             "cantidade": 10, "unidade": "kg", "persoa_id": quen.id}
    datos.update(cambios)
    return DatosSaida(**datos)


def test_converter_unidades():
    assert converter(2, "t", "kg") == 2000
    assert converter(3, "ducias", "unidades") == 36
    assert converter(1, "kg", "unidades") is None


def test_o_que_queda_no_lote(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    _colleita(session, ana, cultivo, quen, cantidade=0.05, unidade="t")
    crear_saida(session, ana, _saida(colleita, quen, cantidade=30), hoxe=HOXE)
    [lote] = listar_lotes(session, ana, horta.id)
    assert resumo_lotes(session, ana, horta.id)[lote.id] == (150, 30, 120)
    with pytest.raises(OperacionNonPermitidaError, match="só quedan 120"):
        crear_saida(session, ana, _saida(colleita, quen, cantidade=121), hoxe=HOXE)


def test_cada_tipo_garda_so_os_seus_datos(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    bar = crear_contacto(session, ana, horta.id, "Bar Central", "cliente")
    venda = crear_saida(session, ana, _saida(
        colleita, quen, tipo="venda", canle="mercado", lugar="Lalín", comprador_id=bar.id,
        importe=25), hoxe=HOXE)
    assert (venda.canle, venda.lugar, venda.importe) == ("mercado", "Lalín", 25)
    casa = crear_saida(session, ana, _saida(colleita, quen, canle="mercado", importe=5),
                       hoxe=HOXE)
    assert (casa.canle, casa.importe) == (None, None)


@pytest.mark.parametrize("cambios, erro", [
    ({"tipo": "venda"}, "a quen"),
    ({"tipo": "venda", "canle": "tenda"}, "tenda"),
    ({"data": date(2026, 8, 1)}, "anterior"),
    ({"data": date(2026, 10, 29)}, "futura"),
    ({"cantidade": 0}, "maior que 0"),
    ({"unidade": "unidades"}, "vai en kg"),
    ({"persoa_id": None}, "quen"),
])
def test_validacions(session, cambios, erro):
    ana, _, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        crear_saida(session, ana, _saida(colleita, quen, **cambios), hoxe=HOXE)


def test_os_ovos_non_van_a_tendas_e_avisa_do_maximo(session):
    ana, horta, quen, _ = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=50)
    ovos = crear_producion(session, ana, DatosProducion(
        animal_id=galinas.id, data=date(2026, 9, 1), produto="ovos", cantidade=1100,
        unidade="ducias", persoa_id=quen.id), hoxe=HOXE)
    tenda = crear_contacto(session, ana, horta.id, "Ultramarinos", "cliente")
    with pytest.raises(OperacionNonPermitidaError, match="ovos"):
        crear_saida(session, ana, DatosSaida(
            lote_id=ovos.lote_id, data=date(2026, 9, 2), tipo="venda", cantidade=10,
            unidade="ducias", canle="tenda", comprador_id=tenda.id, persoa_id=quen.id),
            hoxe=HOXE)
    datos = DatosSaida(lote_id=ovos.lote_id, data=date(2026, 9, 2), tipo="venda",
                       cantidade=1050, unidade="ducias", canle="mercado", persoa_id=quen.id)
    [aviso] = avisos_saida(session, ana, datos)
    assert "1050 ducias" in aviso and "1000 ducias" in aviso


def test_maximo_en_invernadoiro(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen, cantidade=25, unidade="t")
    [lote] = listar_lotes(session, ana, horta.id)
    ficha = session.get(ProdutoVenda, lote.produto_venda_id)
    actualizar_ficha(session, ana, ficha, ficha.nome, "hortalizas", [], "colleita")
    actualizar_lote(session, ana, lote, protexido=False)
    venda = _saida(colleita, quen, tipo="venda", canle="explotacion", cantidade=21,
                   unidade="t")
    assert avisos_saida(session, ana, venda)
    actualizar_lote(session, ana, lote, protexido=True)
    assert avisos_saida(session, ana, venda) == []


def test_aviso_tempo_de_espera(session):
    ana, horta, quen, _ = _escenario(session)
    vacas = crear_animal(session, ana, horta.id, "Vacas", date(2026, 1, 1), cantidade=3)
    crear_coidado(session, ana, DatosCoidado(
        animal_id=vacas.id, data_inicio=date(2026, 9, 1), tipo="medicamento",
        persoa_id=quen.id, medicamento="Penicilina", tempo_espera_dias=10), hoxe=HOXE)
    leite = crear_producion(session, ana, DatosProducion(
        animal_id=vacas.id, data=date(2026, 9, 3), produto="leite", cantidade=40,
        unidade="litros", persoa_id=quen.id), hoxe=HOXE)
    avisos = avisos_saida(session, ana, DatosSaida(
        lote_id=leite.lote_id, data=date(2026, 9, 4), tipo="casa", cantidade=5,
        unidade="litros", persoa_id=quen.id))
    assert any("tempo de espera" in a for a in avisos)


def test_unha_entrada_non_baixa_por_debaixo_do_saido(session):
    ana, _, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    saida = crear_saida(session, ana, _saida(colleita, quen, cantidade=80), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa saíron 80"):
        actualizar_colleita(session, ana, colleita, DatosColleita(
            cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=50, unidade="kg",
            lote="L-1", persoa_id=quen.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa saíron"):
        dar_de_baixa_colleita(session, ana, colleita)
    dar_de_baixa_saida(session, ana, saida)
    dar_de_baixa_colleita(session, ana, colleita)
    assert queda(session, saida_lote(session, saida)) == 0


def saida_lote(session, saida):
    from horta.models.lote import Lote
    return session.get(Lote, saida.lote_id)


def test_diario_e_tarefa(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    bar = crear_contacto(session, ana, horta.id, "Bar Central", "cliente")
    crear_saida(session, ana, _saida(colleita, quen, tipo="venda", canle="domicilio",
                                     comprador_id=bar.id), hoxe=HOXE)
    [traballo] = [t for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)
                  if t.tipo == "lote_saida"]
    assert traballo.que == "Venda: 10 kg de Pataca · lote L-1" and traballo.onde == "Bar Central"
    tarefa = crear_tarefa(session, ana, horta.id, "Levar patacas ao bar", tipo="lote_saida")
    assert tarefa.tipo == "lote_saida"

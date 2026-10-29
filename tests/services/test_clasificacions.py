"""Clasificación, mestura e agrupación dos lotes."""

from datetime import date

import pytest

from horta.models.lote import Lote, ProdutoVenda
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.clasificacions import (
    DatosClasificacion,
    DatosMestura,
    OrixeMestura,
    actualizar_clasificacion,
    crear_clasificacion,
    crear_mestura,
    dar_de_baixa_clasificacion,
    orixes_do_lote,
)
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.lotes import (
    DatosSaida,
    actualizar_ficha,
    codigo_por_agrupacion,
    crear_saida,
    queda,
    queda_por_clase,
)
from horta.services.parcelas import crear_parcela
from horta.services.producions_animais import DatosProducion, crear_producion, propor_lote

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


def _colleita(session, ana, cultivo, quen, lote="L-1", cantidade=300.0):
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=cantidade, unidade="kg",
        lote=lote, persoa_id=quen.id), hoxe=HOXE)
    return colleita.lote_id


def _clasificar(lote_id, quen, clases, refugo=10.0):
    return DatosClasificacion(lote_id=lote_id, data=date(2026, 9, 2), clases=clases,
                              refugo=refugo, persoa_id=quen.id, horas=2)


def _venda(lote_id, quen, cantidade, clase=None):
    return DatosSaida(lote_id=lote_id, data=date(2026, 9, 3), tipo="venda",
                      cantidade=cantidade, unidade="kg", persoa_id=quen.id,
                      canle="explotacion", clase=clase)


def test_clasificar_e_vender_por_clase(session):
    ana, horta, quen, cultivo = _escenario(session)
    lote_id = _colleita(session, ana, cultivo, quen)
    lote = session.get(Lote, lote_id)
    crear_clasificacion(session, ana, _clasificar(
        lote_id, quen, {"Grande": 150, "Mediana": 100, "Miúda": 40}), hoxe=HOXE)
    assert queda_por_clase(session, lote) == {None: 0, "Grande": 150, "Mediana": 100,
                                              "Miúda": 40}
    # O refugo conta como saída: quedan 290
    assert queda(session, lote) == 290
    crear_saida(session, ana, _venda(lote_id, quen, 100, "Grande"), hoxe=HOXE)
    assert queda_por_clase(session, lote)["Grande"] == 50
    with pytest.raises(OperacionNonPermitidaError, match="só quedan 50 kg de Grande"):
        crear_saida(session, ana, _venda(lote_id, quen, 60, "Grande"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="non ten a clase"):
        crear_saida(session, ana, _venda(lote_id, quen, 1, "Extra"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="sen clasificar"):
        crear_saida(session, ana, _venda(lote_id, quen, 1), hoxe=HOXE)


def test_non_se_clasifica_mais_do_que_hai(session):
    ana, horta, quen, cultivo = _escenario(session)
    lote_id = _colleita(session, ana, cultivo, quen)
    with pytest.raises(OperacionNonPermitidaError, match="só quedan 300"):
        crear_clasificacion(session, ana, _clasificar(lote_id, quen, {"Grande": 300}),
                            hoxe=HOXE)


def test_clases_da_ficha(session):
    ana, horta, quen, cultivo = _escenario(session)
    lote_id = _colleita(session, ana, cultivo, quen)
    ficha = session.query(ProdutoVenda).one()
    actualizar_ficha(session, ana, ficha, "Pataca", None, ["Grande", "Miúda"], "colleita")
    with pytest.raises(OperacionNonPermitidaError, match="Grande, Miúda"):
        crear_clasificacion(session, ana, _clasificar(lote_id, quen, {"Extra": 10}),
                            hoxe=HOXE)


def test_cambiar_ou_baixa_sen_deixar_vendas_no_aire(session):
    ana, horta, quen, cultivo = _escenario(session)
    lote_id = _colleita(session, ana, cultivo, quen)
    cl = crear_clasificacion(session, ana, _clasificar(lote_id, quen, {"Grande": 150}),
                             hoxe=HOXE)
    crear_saida(session, ana, _venda(lote_id, quen, 100, "Grande"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="Xa saíron"):
        actualizar_clasificacion(session, ana, cl, _clasificar(lote_id, quen, {"Grande": 50}),
                                 hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="Xa saíron"):
        dar_de_baixa_clasificacion(session, ana, cl)
    actualizar_clasificacion(session, ana, cl, _clasificar(lote_id, quen, {"Grande": 120}),
                             hoxe=HOXE)


def test_mestura_crea_un_lote_novo_coas_orixes(session):
    ana, horta, quen, cultivo = _escenario(session)
    lote1 = _colleita(session, ana, cultivo, quen, "L-1", 100)
    lote2 = _colleita(session, ana, cultivo, quen, "L-2", 50)
    mestura = crear_mestura(session, ana, horta.id, DatosMestura(
        data=date(2026, 9, 5), orixes=[OrixeMestura(lote_id=lote1, cantidade=30),
                                       OrixeMestura(lote_id=lote2, cantidade=50)],
        persoa_id=quen.id), hoxe=HOXE)
    novo = session.get(Lote, mestura.lote_id)
    assert queda(session, novo) == 80
    assert queda(session, session.get(Lote, lote1)) == 70
    assert queda(session, session.get(Lote, lote2)) == 0
    assert {lt.codigo for lt, _, _ in orixes_do_lote(session, novo.id)} == {"L-1", "L-2"}
    with pytest.raises(OperacionNonPermitidaError, match="dous lotes"):
        crear_mestura(session, ana, horta.id, DatosMestura(
            data=date(2026, 9, 5), orixes=[OrixeMestura(lote_id=lote1, cantidade=1)],
            persoa_id=quen.id), hoxe=HOXE)


def test_codigo_segundo_a_agrupacion(session):
    ana, horta, quen, _ = _escenario(session)
    ficha = ProdutoVenda(horta_id=horta.id, nome="Ovos", unidade="unidades",
                         produto_animal="ovos", agrupacion="semana")
    session.add(ficha)
    session.commit()
    dia = date(2026, 10, 28)
    assert codigo_por_agrupacion(session, ficha, dia) == "2026-OVOS-S44"
    ficha.agrupacion = "dia"
    assert codigo_por_agrupacion(session, ficha, dia) == "2026-OVOS-1028"
    ficha.agrupacion = "mes"
    assert codigo_por_agrupacion(session, ficha, dia) == "2026-OVOS-M10"
    ficha.agrupacion = "semana"
    session.commit()
    # Os ovos da semana van ao mesmo lote
    galinas = crear_animal(session, ana, horta.id, "Galiña", cantidade=10,
                           data_alta=date(2026, 1, 1))
    for dia_posta in (date(2026, 10, 26), date(2026, 10, 27)):
        crear_producion(session, ana, DatosProducion(
            animal_id=galinas.id, data=dia_posta, produto="ovos", cantidade=8,
            unidade="unidades", persoa_id=quen.id,
            lote=propor_lote(session, ana, horta.id, "ovos", dia_posta)), hoxe=HOXE)
    [lote] = session.query(Lote).all()
    assert lote.codigo == "2026-OVOS-S44" and queda(session, lote) == 16


def test_trazabilidade_do_lote(session):
    from horta.services.trazabilidade import trazabilidade

    ana, horta, quen, cultivo = _escenario(session)
    lote1 = _colleita(session, ana, cultivo, quen, "L-1", 100)
    lote2 = _colleita(session, ana, cultivo, quen, "L-2", 50)
    crear_clasificacion(session, ana, _clasificar(lote1, quen, {"Grande": 60}, refugo=0),
                        hoxe=HOXE)
    crear_saida(session, ana, _venda(lote1, quen, 20, "Grande"), hoxe=HOXE)
    mestura = crear_mestura(session, ana, horta.id, DatosMestura(
        data=date(2026, 9, 5), orixes=[OrixeMestura(lote_id=lote1, cantidade=10,
                                                    clase="Grande"),
                                       OrixeMestura(lote_id=lote2, cantidade=50)],
        persoa_id=quen.id), hoxe=HOXE)
    t1 = trazabilidade(session, ana, lote1)
    assert [ln.texto for ln in t1.orixe] == ["Colleita de Pataca na leira Leira: 100 kg"]
    assert t1.dentro[0].texto == "Clasificación: Grande 60"
    assert [ln.texto.split(":")[0] for ln in t1.saidas] == ["Venda", "Mesturado"]
    # O lote da mestura chega ata as colleitas de orixe
    t2 = trazabilidade(session, ana, mestura.lote_id)
    textos = " ".join(ln.texto for ln in t2.orixe)
    assert "do lote L-1" in textos and "[L-2] Colleita de Pataca" in textos

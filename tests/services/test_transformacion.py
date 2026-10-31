"""Transformación e páxina pública do lote (paso 17)."""

from datetime import date

import pytest

from horta.models.abonado import Abonado, AbonadoCultivo, Fertilizante
from horta.models.lote import Lote
from horta.models.persoa import Persoa
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
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
from horta.services.producions_animais import DatosProducion, crear_producion
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


def test_lote_publico_plantacion_abonados_e_animais(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta da Ana")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    quen.nif = "12345678Z"
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pemento", tipo_inicio="plantacion",
                            data_inicio=date(2026, 5, 10), notas="nota secreta")
    cultivo.certificacion_ecoloxica = "2"
    abono = Fertilizante(horta_id=horta.id, nome="Esterco de vaca", material="5")
    session.add(abono)
    session.flush()
    session.add(Abonado(
        horta_id=horta.id, data_inicio=date(2026, 6, 1), data_fin=date(2026, 6, 1),
        fertilizante_id=abono.id, tipo_fertilizacion="1", persoa_id=quen.id,
        notas="nota do abonado", leiras=[AbonadoCultivo(cultivo_id=cultivo.id)],
    ))
    session.add(TratamentoFito(
        horta_id=horta.id, data_inicio=date(2026, 7, 15), data_fin=date(2026, 7, 15),
        notas="nota do tratamento", cultivos=[TratamentoCultivo(cultivo_id=cultivo.id)],
        produtos=[TratamentoProduto(tipo_produto="1", nome_comercial="Cobre",
                                    num_rexistro="12345", unidade="17")],
    ))
    session.commit()
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=30, unidade="kg", lote="P-2",
        persoa_id=quen.id), hoxe=HOXE)
    lote = session.get(Lote, colleita.lote_id)
    token = publicar_lote(session, ana, lote)
    traz, _ = trazabilidade_publica(session, token)
    assert [(ln.data, ln.texto) for ln in traz.orixe] == [
        (date(2026, 5, 10), "Plantación de Pemento na leira Leira · ecolóxico (certificado)"),
        (date(2026, 9, 1), "Colleita de Pemento na leira Leira: 30 kg"),
    ]
    assert [(ln.data, ln.texto) for ln in traz.fixose] == [
        (date(2026, 6, 1),
         "Abonado: Esterco de vaca · Esterco sólido de bovino · Abonado de fondo"),
        (date(2026, 7, 15), "Tratamento: Cobre (nº 12345)"),
    ]
    todo = " ".join(ln.texto for ln in [*traz.orixe, *traz.fixose])
    assert "12345678Z" not in todo and "nota" not in todo

    # Os lotes de produtos animais seguen como ata agora
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=20)
    ovos = crear_producion(session, ana, DatosProducion(
        animal_id=galinas.id, data=date(2026, 9, 2), produto="ovos", cantidade=12,
        unidade="ducias", persoa_id=quen.id), hoxe=HOXE)
    lote_ovos = session.get(Lote, ovos.lote_id)
    traz_ovos, _ = trazabilidade_publica(session, publicar_lote(session, ana, lote_ovos))
    assert [ln.texto for ln in traz_ovos.orixe] == ["Produción de Galiñas: 12 ducias"]
    assert traz_ovos.fixose == []

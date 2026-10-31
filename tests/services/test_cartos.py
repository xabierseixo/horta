"""Os cartos."""

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cartos import (
    DatosApunte,
    actualizar_apunte,
    crear_apunte,
    dar_de_baixa_apunte,
    listar_apuntes,
    pendente_por_persoa,
    periodo,
    periodos_recentes,
    resumo_ano,
    resumo_periodo,
)
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.equipo import historial
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.maquinaria import crear_maquina
from horta.services.outros_traballos import DatosOutroTraballo, crear_outro_traballo
from horta.services.parcelas import crear_parcela
from horta.services.persoas import actualizar_persoa, crear_contacto
from horta.services.produtos import DatosEntrada, crear_entrada, crear_produto

HOXE = date(2026, 10, 28)


def _usuario(session, nome):
    usuario = Usuario(nome=nome, email=f"{nome}@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _usuario(session, "ana")
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    return ana, horta, quen


def _apunte(**cambios):
    datos = {"tipo": "gasto", "categoria": "seguro", "concepto": "Seguro da leira",
             "data": date(2026, 3, 1), "importe": 120.0}
    datos.update(cambios)
    return DatosApunte(**datos)


def _venda(session, ana, horta, quen, importe, data_pago=None, cliente=None):
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Leira").id,
                            "Pataca")
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=100, unidade="kg",
        lote="L-1", persoa_id=quen.id), hoxe=HOXE)
    return crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2026, 9, 5), tipo="venda", cantidade=10,
        unidade="kg", persoa_id=quen.id, canle="explotacion", comprador_id=cliente,
        importe=importe, data_pago=data_pago), hoxe=HOXE)


def test_apunte_crear_editar_e_baixa(session):
    ana, horta, _ = _escenario(session)
    apunte = crear_apunte(session, ana, horta.id, _apunte(), hoxe=HOXE)
    actualizar_apunte(session, ana, apunte, _apunte(importe=150.0), hoxe=HOXE)
    assert listar_apuntes(session, ana, horta.id)[0].importe == 150
    dar_de_baixa_apunte(session, ana, apunte)
    assert listar_apuntes(session, ana, horta.id) == []


@pytest.mark.parametrize("cambios, erro", [
    ({"importe": 0}, "maior que 0"),
    ({"categoria": "xoias"}, "categoría"),
    ({"tipo": "debeda"}, "gasto ou un ingreso"),
    ({"concepto": " "}, "concepto"),
    ({"data": date(2026, 11, 1)}, "futura"),
    ({"data_pago": date(2026, 2, 1)}, "anterior"),
    ({"data_pago": date(2026, 11, 1)}, "futura"),
])
def test_apunte_validacions(session, cambios, erro):
    ana, horta, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        crear_apunte(session, ana, horta.id, _apunte(**cambios), hoxe=HOXE)


def test_persoa_doutra_explotacion(session):
    ana, horta, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    alguen = crear_contacto(session, ana, outra.id, "Seguros SA", "provedor")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta"):
        crear_apunte(session, ana, horta.id, _apunte(persoa_id=alguen.id), hoxe=HOXE)


def test_quen_so_mira_non_ve_os_cartos(session):
    ana, horta, _ = _escenario(session)
    luis = _usuario(session, "luis")
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        resumo_ano(session, luis, horta.id, 2026)
    with pytest.raises(PermisoDenegadoError):
        listar_apuntes(session, luis, horta.id)


def test_pendente_por_persoa(session):
    ana, horta, quen = _escenario(session)
    cliente = crear_contacto(session, ana, horta.id, "Tenda", "cliente")
    provedor = crear_contacto(session, ana, horta.id, "Agro SL", "provedor")
    _venda(session, ana, horta, quen, 50.0, cliente=cliente.id)
    crear_apunte(session, ana, horta.id, _apunte(persoa_id=cliente.id, importe=15.0),
                 hoxe=HOXE)
    produto = crear_produto(session, ana, horta.id, "abono", "Esterco", "kg")
    crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 2, 1), persoa_id=quen.id,
        provedor_id=provedor.id, importe=30.0), hoxe=HOXE)
    crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 2, 2), persoa_id=quen.id,
        provedor_id=provedor.id, importe=99.0, data_pago=date(2026, 2, 2)), hoxe=HOXE)
    crear_apunte(session, ana, horta.id, _apunte(persoa_id=provedor.id, importe=10.0),
                 hoxe=HOXE)
    # Sen persoa: axuda pendente de cobrar e seguro pendente de pagar non se restan
    crear_apunte(session, ana, horta.id, _apunte(tipo="ingreso", categoria="axuda",
                                                 concepto="Axuda", importe=600.0), hoxe=HOXE)
    crear_apunte(session, ana, horta.id, _apunte(importe=120.0), hoxe=HOXE)
    assert pendente_por_persoa(session, ana, horta.id) == {
        cliente.id: (50.0, 15.0),
        provedor.id: (0.0, 40.0),
        None: (600.0, 120.0),
    }
    feitos = historial(session, ana, provedor)
    assert sorted(f.importe for f in feitos if f.pendente) == [10.0, 30.0]


def test_cobro_non_pode_ser_antes_da_venda(session):
    ana, horta, quen = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="anterior"):
        _venda(session, ana, horta, quen, 50.0, data_pago=date(2026, 9, 1))


def test_resumo_do_ano(session):
    ana, horta, quen = _escenario(session)
    actualizar_persoa(session, ana, quen, custo_hora=10.0, vinculo="titular")
    xan = crear_contacto(session, ana, horta.id, "Xan", "servizos", custo_hora=20.0)
    tractor = crear_maquina(session, ana, horta.id, "Tractor", custo_hora=15.0)
    _venda(session, ana, horta, quen, 200.0, data_pago=date(2026, 9, 6))
    crear_apunte(session, ana, horta.id, _apunte(), hoxe=HOXE)
    crear_apunte(session, ana, horta.id, _apunte(tipo="ingreso", categoria="axuda",
                                                 concepto="Axuda", importe=300.0), hoxe=HOXE)
    # Outro ano: non conta
    crear_apunte(session, ana, horta.id, _apunte(data=date(2025, 3, 1)), hoxe=HOXE)
    crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 5, 1), descricion="Peche", persoa_id=quen.id,
        horas=2.0, maquina_id=tractor.id), hoxe=HOXE)
    crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 5, 2), descricion="Poda", persoa_id=xan.id,
        horas=1.0), hoxe=HOXE)
    resumo = resumo_ano(session, ana, horta.id, 2026)
    assert resumo.ingresos == {"Vendas": 200.0, "Axuda ou subvención": 300.0}
    # Man de obra: 2 h × 10 + 1 h × 20; máquina: 2 h × 15
    assert resumo.gastos == {"Seguro": 120.0, "Man de obra": 40.0, "Máquinas": 30.0}
    assert resumo.resultado == 310.0
    assert resumo.resultado_sen_man_propia == 330.0
    assert resumo.custos.sen_custo == 0


def test_periodos():
    dia = date(2026, 10, 29)  # xoves
    semana = periodo("semana", dia)
    assert (semana.desde, semana.ata) == (date(2026, 10, 26), date(2026, 11, 1))
    decembro = periodo("mes", date(2026, 12, 5))
    assert (decembro.desde, decembro.ata) == (date(2026, 12, 1), date(2026, 12, 31))
    assert periodo("mes", date(2028, 2, 5)).ata == date(2028, 2, 29)
    trimestre = periodo("trimestre", dia)
    assert (trimestre.desde, trimestre.ata, trimestre.nome) == (
        date(2026, 10, 1), date(2026, 12, 31), "4.º trimestre de 2026")
    assert [p.desde for p in periodos_recentes("trimestre", dia, 3)] == [
        date(2026, 10, 1), date(2026, 7, 1), date(2026, 4, 1)]


def test_resumo_dun_mes(session):
    ana, horta, _ = _escenario(session)
    crear_apunte(session, ana, horta.id, _apunte(data=date(2026, 3, 1)), hoxe=HOXE)
    crear_apunte(session, ana, horta.id, _apunte(data=date(2026, 4, 1), importe=7.0),
                 hoxe=HOXE)
    marzo = resumo_periodo(session, ana, horta.id, periodo("mes", date(2026, 3, 15)))
    assert marzo.gastos == {"Seguro": 120.0}

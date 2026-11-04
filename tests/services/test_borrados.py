from __future__ import annotations

from datetime import date

import pytest

from horta.models.abonado import Abonado, AbonadoCultivo, Fertilizante
from horta.models.cartos import ApunteCartos
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.envio_cue import EnvioCue
from horta.models.foto import Foto
from horta.models.horta import Horta
from horta.models.instalacion import Instalacion
from horta.models.lote import Lote, ProdutoVenda
from horta.models.parcela import Parcela
from horta.models.plan_empresa import PlanEmpresa, PlanInvestimento, PlanOferta
from horta.models.rega import Rega, RegaCultivo
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito
from horta.models.usuario import RolGlobal, Usuario
from horta.models.zona import ParcelaZona
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela
from horta.services.persoas import crear_persoa


def _crear_usuario(session, email: str = "ana@example.com") -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_eliminar_horta_con_lote_colleita_foto_cartos_e_zona(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela 1")

    zona = ParcelaZona(parcela_id=parcela.id, nome="Bancal A")
    session.add(zona)
    session.flush()

    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate", zona_id=zona.id)

    pv = ProdutoVenda(horta_id=horta.id, nome="Tomate", unidade="kg")
    session.add(pv)
    session.flush()

    lote = Lote(
        horta_id=horta.id,
        codigo="2026-TOMATE-001",
        produto="Tomate",
        unidade="kg",
        produto_venda_id=pv.id,
        data=date(2026, 6, 1),
    )
    session.add(lote)
    session.flush()

    colleita = Colleita(
        cultivo_id=cultivo.id,
        lote_id=lote.id,
        data=date(2026, 6, 1),
        cantidade=50.0,
        unidade="kg",
    )
    session.add(colleita)

    foto = Foto(
        horta_id=horta.id,
        que="parcela",
        ref_id=parcela.id,
        ficheiro="foto1.jpg",
        data=date(2026, 6, 1),
    )
    session.add(foto)

    apunte = ApunteCartos(
        horta_id=horta.id,
        tipo="gasto",
        categoria="auga",
        concepto="Factura auga",
        data=date(2026, 6, 1),
        importe=50.0,
    )
    session.add(apunte)
    session.commit()

    eliminar_horta(session, ana, horta)

    assert session.get(Horta, horta.id) is None
    assert session.query(Parcela).filter_by(horta_id=horta.id).count() == 0
    assert session.query(Cultivo).filter_by(id=cultivo.id).count() == 0
    assert session.query(ParcelaZona).filter_by(id=zona.id).count() == 0
    assert session.query(Colleita).filter_by(id=colleita.id).count() == 0
    assert session.query(Lote).filter_by(id=lote.id).count() == 0
    assert session.query(ProdutoVenda).filter_by(id=pv.id).count() == 0
    assert session.query(Foto).filter_by(id=foto.id).count() == 0
    assert session.query(ApunteCartos).filter_by(id=apunte.id).count() == 0


def test_eliminar_parcela_con_colleita_rexeita_operacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela 1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")

    pv = ProdutoVenda(horta_id=horta.id, nome="Pataca", unidade="kg")
    session.add(pv)
    session.flush()

    lote = Lote(
        horta_id=horta.id,
        codigo="2026-PATACA-001",
        produto="Pataca",
        unidade="kg",
        produto_venda_id=pv.id,
        data=date(2026, 7, 1),
    )
    session.add(lote)
    session.flush()

    colleita = Colleita(
        cultivo_id=cultivo.id,
        lote_id=lote.id,
        data=date(2026, 7, 1),
        cantidade=100.0,
        unidade="kg",
    )
    session.add(colleita)
    session.commit()

    with pytest.raises(OperacionNonPermitidaError, match="colleitas rexistradas"):
        eliminar_parcela(session, ana, parcela)

    assert session.get(Parcela, parcela.id) is not None


def test_tres_borrados_rexeitan_se_hai_abonado(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela 1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Cenoria")

    fert = Fertilizante(horta_id=horta.id, nome="Compost", material="organico")
    session.add(fert)
    session.flush()

    abonado = Abonado(
        horta_id=horta.id,
        data_inicio=date(2026, 5, 1),
        data_fin=date(2026, 5, 1),
        fertilizante_id=fert.id,
    )
    abonado.leiras.append(AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1))
    session.add(abonado)
    session.commit()

    with pytest.raises(OperacionNonPermitidaError, match="abonados rexistrados"):
        eliminar_cultivo(session, ana, cultivo)

    with pytest.raises(OperacionNonPermitidaError, match="abonados rexistrados"):
        eliminar_parcela(session, ana, parcela)

    with pytest.raises(OperacionNonPermitidaError, match="abonados rexistrados"):
        eliminar_horta(session, ana, horta)


def test_tres_borrados_rexeitan_se_hai_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela 1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Cebola")

    rega = Rega(
        horta_id=horta.id,
        data_inicio=date(2026, 6, 1),
        data_fin=date(2026, 6, 1),
        unidade="m3",
    )
    rega.leiras.append(RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.1))
    session.add(rega)
    session.commit()

    with pytest.raises(OperacionNonPermitidaError, match="regas rexistradas"):
        eliminar_cultivo(session, ana, cultivo)

    with pytest.raises(OperacionNonPermitidaError, match="regas rexistradas"):
        eliminar_parcela(session, ana, parcela)

    with pytest.raises(OperacionNonPermitidaError, match="regas rexistradas"):
        eliminar_horta(session, ana, horta)


def test_tres_borrados_rexeitan_se_hai_tratamento_fito(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela 1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pemento")

    tratamento = TratamentoFito(
        horta_id=horta.id,
        data_inicio=date(2026, 5, 1),
        data_fin=date(2026, 5, 1),
    )
    tratamento.cultivos.append(TratamentoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1))
    session.add(tratamento)
    session.commit()

    with pytest.raises(OperacionNonPermitidaError, match="tratamentos fitosanitarios"):
        eliminar_cultivo(session, ana, cultivo)

    with pytest.raises(OperacionNonPermitidaError, match="tratamentos fitosanitarios"):
        eliminar_parcela(session, ana, parcela)

    with pytest.raises(OperacionNonPermitidaError, match="tratamentos fitosanitarios"):
        eliminar_horta(session, ana, horta)


def test_eliminar_horta_con_plan_empresa_instalacion_envio_cue(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Provedor SL")

    plan = PlanEmpresa(horta_id=horta.id, titulo="Plan 2026", ano_inicio=2026)
    inv = PlanInvestimento(partida="02", concepto="Invernadoiro", importe_sen_iva=1000.0)
    plan.investimentos.append(inv)
    session.add(plan)
    session.flush()

    oferta = PlanOferta(investimento_id=inv.id, provedor_id=persoa.id, importe_sen_iva=1000.0)
    session.add(oferta)
    session.flush()

    instalacion = Instalacion(horta_id=horta.id, tipo="almacen", nome="Almacén central")
    session.add(instalacion)

    envio = EnvioCue(horta_id=horta.id, usuario_id=ana.id, desde=date(2026, 1, 1), ata=date(2026, 1, 31))
    session.add(envio)
    session.commit()

    eliminar_horta(session, ana, horta)

    assert session.get(Horta, horta.id) is None
    assert session.query(PlanEmpresa).filter_by(horta_id=horta.id).count() == 0
    assert session.query(PlanInvestimento).count() == 0
    assert session.query(PlanOferta).count() == 0
    assert session.query(Instalacion).filter_by(horta_id=horta.id).count() == 0
    assert session.query(EnvioCue).filter_by(horta_id=horta.id).count() == 0

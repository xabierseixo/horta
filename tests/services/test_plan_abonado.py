from datetime import date

from horta.models.abonado import Abonado
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.plan_abonado import balance_do_cultivo


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="material_fertilizante", codigo="14", descricion="m",
                              version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2, plan_necesidade_n=120)
    npk = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK", material="14", n_pct=15, p2o5_pct=15, k2o_pct=15))
    liquido = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Líquido", material="14", n_pct=20, liquido=True))
    return ana, horta, cultivo, npk, liquido


def _abonado(session, horta, cultivo, abono, superficie, dose, unidade="17"):
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=superficie,
                        fertilizante_id=abono.id, dose=dose, unidade=unidade,
                        tipo_fertilizacion="1", metodo="1"))
    session.commit()


def test_balance_pondera_pola_superficie_abonada(session):
    ana, horta, cultivo, npk, _ = _escenario(session)
    _abonado(session, horta, cultivo, npk, 0.2, 200)   # todo o cultivo: 30 kg N/ha
    _abonado(session, horta, cultivo, npk, 0.1, 200)   # a metade: 15 kg N/ha no cultivo
    balance = balance_do_cultivo(session, ana, horta.id, cultivo)
    assert balance.aplicado == (45.0, 45.0, 45.0)
    assert balance.necesidade == (120, None, None)
    assert balance.sen_calcular == 0


def test_liquido_sen_densidade_non_se_conta(session):
    ana, horta, cultivo, _, liquido = _escenario(session)
    _abonado(session, horta, cultivo, liquido, 0.2, 100, unidade="18")
    balance = balance_do_cultivo(session, ana, horta.id, cultivo)
    assert balance.aplicado == (0.0, 0.0, 0.0)
    assert balance.sen_calcular == 1

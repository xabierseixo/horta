"""Apuntar un traballo só obriga ao mínimo (que, onde, cando e quen); o resto é opcional e o
caderno avisa do que falta."""

from datetime import date

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.faltas_caderno import Falta, faltas_caderno
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1


HOXE = date(2026, 10, 26)


def _cultivo_sen_superficie(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("material_fertilizante", "13"), ("tipo_labor", "7")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x", rol=RolGlobal.USUARIO,
                  activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta da casa")
    parcela = crear_parcela(session, ana, horta.id, "Horta")
    return ana, horta, crear_cultivo(session, ana, parcela.id, "Tomate")


def test_rega_so_con_cultivo_e_data(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    rega = crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE,
                                              persoa_id=QUEN), hoxe=HOXE)
    assert rega.sistema_rega is None and rega.cantidade is None and rega.superficie_ha is None


def test_abonado_so_co_abono(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost da casa", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(persoa_id=QUEN,
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id), hoxe=HOXE)
    assert abonado.tipo_fertilizacion is None and abonado.metodo is None
    assert abonado.dose is None and abonado.unidade is None and abonado.boas_practicas == []


def test_colleita_pon_o_lote_soa(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    colleita = crear_colleita(session, ana, DatosColleita(persoa_id=QUEN,
        cultivo_id=cultivo.id, data=HOXE, cantidade=5, unidade="kg", lote=""), hoxe=HOXE)
    assert colleita.lote == "2026-TOMATE-001"


def test_labor_sen_superficie(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    labor = crear_labor(session, ana, DatosLabor(persoa_id=QUEN,
        cultivo_id=cultivo.id, data_inicio=HOXE, tipo_labor="7"), hoxe=HOXE)
    assert labor.superficie_ha is None


def test_sen_rexistros_non_falta_nada(session):
    ana, horta, _ = _cultivo_sen_superficie(session)
    assert faltas_caderno(session, ana, horta.id) == []


def test_conta_o_que_falta_en_cada_rega(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    for _ in range(2):
        crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE,
                                           persoa_id=QUEN), hoxe=HOXE)
    assert faltas_caderno(session, ana, horta.id) == [
        Falta("Regas", "superficie", 2), Falta("Regas", "sistema de rega", 2),
        Falta("Regas", "cantidade de auga", 2)]


def test_so_mira_o_periodo(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE, persoa_id=QUEN),
               hoxe=HOXE)
    assert faltas_caderno(session, ana, horta.id, desde=date(2027, 1, 1)) == []

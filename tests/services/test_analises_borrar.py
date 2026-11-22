from datetime import date

from horta.models.analise import Analise, AnaliseTipo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    analise = Analise(horta_id=horta.id, material_analizado="3",
                      data_mostraxe=date(2026, 3, 1), parcela_id=parcela.id,
                      cultivo_id=cultivo.id, tipos=[AnaliseTipo(codigo="5")])
    session.add(analise)
    session.commit()
    return ana, horta, parcela, cultivo, analise


def test_borrar_cultivo_conserva_a_analise(session):
    ana, _, _, cultivo, analise = _escenario(session)
    eliminar_cultivo(session, ana, cultivo)
    session.refresh(analise)
    assert analise.cultivo_id is None and analise.parcela_id is not None


def test_borrar_parcela_conserva_a_analise(session):
    ana, _, parcela, _, analise = _escenario(session)
    eliminar_parcela(session, ana, parcela)
    session.refresh(analise)
    assert analise.parcela_id is None and analise.cultivo_id is None


def test_borrar_explotacion_borra_as_analises(session):
    ana, horta, _, _, _ = _escenario(session)
    eliminar_horta(session, ana, horta)
    assert session.query(Analise).count() == 0
    assert session.query(AnaliseTipo).count() == 0

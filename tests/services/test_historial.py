"""Historial de cada recurso e rotación (paso 12)."""

from datetime import date

from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.historial import historial_animal, historial_maquina, rotacion
from horta.services.hortas import crear_horta
from horta.services.maquinaria import crear_maquina
from horta.services.outros_traballos import DatosOutroTraballo, crear_outro_traballo
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 28)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    return ana, horta, quen


def test_historial_do_animal_e_da_maquina(session):
    ana, horta, quen = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiña", cantidade=10,
                           data_alta=date(2026, 1, 1))
    tractor = crear_maquina(session, ana, horta.id, "Tractor")
    crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 5, 1), descricion="Limpar o galiñeiro",
        animal_id=galinas.id, maquina_id=tractor.id, persoa_id=quen.id), hoxe=HOXE)
    # Tamén a alta do grupo (o seu movemento inicial)
    assert [f.que for f in historial_animal(session, ana, galinas)] == [
        "Outro traballo", "Entrada ou saída de animais"]
    [feito] = historial_maquina(session, ana, tractor)
    assert (feito.que, feito.data) == ("Outro traballo", date(2026, 5, 1))


def test_rotacion(session):
    ana, horta, _ = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    for ano, especie in ((2023, "Pataca"), (2025, "Pataca"), (2026, "Millo")):
        cultivo = crear_cultivo(session, ana, parcela.id, especie)
        actualizar_cultivo(session, ana, cultivo, data_inicio=date(ano, 4, 1))
    avisos = [(c.cultivo.especie, c.aviso is not None) for c in rotacion(session, ana, parcela)]
    assert avisos == [("Millo", False), ("Pataca", True), ("Pataca", False)]


def test_rotacion_por_familia(session):
    ana, horta, _ = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    for ano, especie in ((2025, "Pataca"), (2026, "Tomate de colgar")):
        cultivo = crear_cultivo(session, ana, parcela.id, especie)
        actualizar_cultivo(session, ana, cultivo, data_inicio=date(ano, 4, 1))
    [tomate, pataca] = rotacion(session, ana, parcela)
    assert "mesma familia (Solanáceas)" in (tomate.aviso or "") and pataca.aviso is None

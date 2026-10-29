"""Estatísticas (paso 15)."""

from datetime import date

from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.clasificacions import DatosClasificacion, crear_clasificacion
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.estatisticas import clases_do_ano, producion_por_ano
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 28)


def test_producion_e_clases(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Leira").id,
                            "Pataca")
    for data, cantidade, unidade, lote in ((date(2025, 9, 1), 200, "kg", "A"),
                                           (date(2026, 9, 1), 0.3, "t", "B")):
        colleita = crear_colleita(session, ana, DatosColleita(
            cultivo_id=cultivo.id, data=data, cantidade=cantidade, unidade=unidade, lote=lote,
            persoa_id=quen.id), hoxe=HOXE)
    assert producion_por_ano(session, ana, horta.id, 2026) == {"Pataca": {2025: 200, 2026: 300}}
    crear_clasificacion(session, ana, DatosClasificacion(
        lote_id=colleita.lote_id, data=date(2026, 9, 2), clases={"Grande": 0.2}, refugo=0.05,
        persoa_id=quen.id), hoxe=HOXE)
    assert clases_do_ano(session, ana, horta.id, 2026) == {
        "Pataca (t)": {"Grande": 0.2, "Refugo": 0.05}}

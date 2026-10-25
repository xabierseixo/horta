from horta.models.cultivo import Cultivo
from horta.models.horta import Horta
from horta.models.parcela import Parcela


def _crear_parcela(session) -> Parcela:
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()
    parcela = Parcela(horta_id=horta.id, nome="Parcela Norte", estado="activa")
    session.add(parcela)
    session.commit()
    return parcela


def test_crear_cultivo_con_valores_por_defecto(session):
    parcela = _crear_parcela(session)

    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.commit()

    atopado = session.query(Cultivo).filter_by(especie="Tomate").one()
    assert atopado.parcela_id == parcela.id
    assert atopado.estado == "planificado"
    assert atopado.variedade is None

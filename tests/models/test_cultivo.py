from datetime import date

from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
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
    assert atopado.data_sementeira is None


def test_crear_tratamento_con_baixa_por_defecto_false(session):
    parcela = _crear_parcela(session)
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.flush()

    tratamento = Tratamento(
        cultivo_id=cultivo.id,
        data=date(2026, 5, 1),
        praga="Mildeu",
        produto="Cobre",
        aplicador="Xabier",
    )
    session.add(tratamento)
    session.commit()

    atopado = session.query(Tratamento).filter_by(praga="Mildeu").one()
    assert atopado.baixa is False
    assert atopado.cultivo_id == cultivo.id


def test_crear_fertilizacion_con_baixa_por_defecto_false(session):
    parcela = _crear_parcela(session)
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.flush()

    fertilizacion = Fertilizacion(
        cultivo_id=cultivo.id,
        data=date(2026, 4, 1),
        tipo="abonado_fondo",
        produto="Compost",
    )
    session.add(fertilizacion)
    session.commit()

    atopada = session.query(Fertilizacion).filter_by(produto="Compost").one()
    assert atopada.baixa is False
    assert atopada.n is None

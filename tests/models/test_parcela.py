from horta.models.horta import Horta
from horta.models.parcela import Parcela, SecanoRegadio


def test_crear_parcela_con_campos_opcionais_baleiros(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()

    parcela = Parcela(horta_id=horta.id, nome="Parcela Norte", estado="activa")
    session.add(parcela)
    session.commit()

    atopada = session.query(Parcela).filter_by(nome="Parcela Norte").one()
    assert atopada.horta_id == horta.id
    assert atopada.superficie is None
    assert atopada.sigpac_provincia is None
    assert atopada.secano_regadio is None


def test_crear_parcela_con_campos_sigpac(session):
    horta = Horta(nome="Explotación", uso_profesional=True)
    session.add(horta)
    session.flush()

    parcela = Parcela(
        horta_id=horta.id,
        nome="Parcela 1",
        estado="activa",
        superficie=1200.5,
        secano_regadio=SecanoRegadio.REGADIO,
        sigpac_provincia="15",
        sigpac_concello="30",
        sigpac_poligono="4",
        sigpac_parcela="120",
        sigpac_subparcela="a",
    )
    session.add(parcela)
    session.commit()

    atopada = session.query(Parcela).filter_by(nome="Parcela 1").one()
    assert atopada.secano_regadio == SecanoRegadio.REGADIO
    assert atopada.sigpac_provincia == "15"

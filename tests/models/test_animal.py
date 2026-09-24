import datetime

from horta.models.animal import Animal
from horta.models.horta import Horta


def test_crear_animal_lote(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()

    animal = Animal(
        horta_id=horta.id,
        especie="galiñas",
        raza="Rubia Galega",
        cantidade=6,
        data_alta=datetime.date(2026, 2, 10),
        estado="activo",
    )
    session.add(animal)
    session.commit()

    atopado = session.query(Animal).filter_by(especie="galiñas").one()
    assert atopado.horta_id == horta.id
    assert atopado.cantidade == 6
    assert atopado.data_baixa is None

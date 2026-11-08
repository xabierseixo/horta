"""Probas para a ficha do grupo de animais (datos_animal)."""

from __future__ import annotations

from datetime import date

from horta.models.animal import Animal
from horta.ui.ficha_animal import datos_animal


def _describir_proba(catalogo: str, codigo: str) -> str:
    taboa = {
        ("especie_animal", "06"): "Galiñas",
        ("especie_animal", "01"): "Vacas",
    }
    return taboa.get((catalogo, codigo), codigo)


def test_datos_animal_completo() -> None:
    """Un grupo de animais con todos os datos mostra as súas etiquetas e valores formatados."""
    animal = Animal(
        especie="Galiñas de Mos",
        especie_codigo="06",
        raza="Mos",
        cantidade=20,
        data_alta=date(2026, 1, 15),
        data_baixa=date(2026, 10, 31),
        estado="baixa",
        notas="Galiñeiro pequeno",
    )
    datos = datos_animal(animal, _describir_proba)

    esperados = [
        ("Especie", "Galiñas"),
        ("Raza", "Mos"),
        ("Cantidade", "20"),
        ("Data de alta", "15/01/2026"),
        ("Data de baixa", "31/10/2026"),
        ("Estado", "De baixa"),
        ("Notas", "Galiñeiro pequeno"),
    ]
    assert datos == esperados


def test_datos_animal_minimo() -> None:
    """Un grupo de animais só coa especie devolve unicamente a parella de Especie."""
    animal = Animal(especie="Ovellas")
    datos = datos_animal(animal, _describir_proba)

    assert datos == [("Especie", "Ovellas")]


def test_datos_animal_activo() -> None:
    """Un grupo activo mostra De alta no estado e non mostra data de baixa se non a ten."""
    animal = Animal(
        especie="Galiñas",
        especie_codigo="06",
        estado="activo",
        data_baixa=None,
    )
    datos = datos_animal(animal, _describir_proba)
    etiquetas = [e for e, _ in datos]

    assert ("Estado", "De alta") in datos
    assert "Data de baixa" not in etiquetas


def test_datos_animal_especie_en_galego() -> None:
    """A especie sae co nome galego aínda que o catálogo a dea en castelán."""
    animal = Animal(especie="Poñedoras", especie_codigo="06")
    datos = datos_animal(animal, lambda _cat, _cod: "Gallinas")
    assert ("Especie", "Galiñas") in datos

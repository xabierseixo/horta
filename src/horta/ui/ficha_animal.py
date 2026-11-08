"""Ficha do grupo de animais: datos, historial e fotos."""

from __future__ import annotations

from collections.abc import Callable

from horta.db import get_session
from horta.models.animal import Animal
from horta.services.animais import ESPECIES, listar_animais
from horta.services.catalogos import describir
from horta.services.fotos import MODELOS
from horta.services.historial import historial_animal
from horta.ui.ficha import abrir_ficha
from horta.ui.fotos import abrir_fotos
from horta.ui.numeros import texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual

_ESTADOS_ANIMAL = {"activo": "De alta", "baixa": "De baixa"}


def datos_animal(
    animal: Animal,
    describir_codigo: Callable[[str, str], str],
) -> list[tuple[str, str]]:
    """Devolve as parellas etiqueta/valor que teñan valor para a ficha do grupo de animais."""
    resultado: list[tuple[str, str]] = []

    if getattr(animal, "especie_codigo", None) is not None and str(animal.especie_codigo).strip():
        codigo = str(animal.especie_codigo).strip()
        # O nome galego da pantalla de Animais; o catálogo do FEGA só vén en castelán
        esp = ESPECIES.get(codigo) or describir_codigo("especie_animal", codigo)
        if esp and esp.strip():
            resultado.append(("Especie", esp.strip()))
    elif getattr(animal, "especie", None) is not None and str(animal.especie).strip():
        resultado.append(("Especie", str(animal.especie).strip()))

    if getattr(animal, "raza", None) is not None and str(animal.raza).strip():
        resultado.append(("Raza", str(animal.raza).strip()))

    if getattr(animal, "cantidade", None) is not None:
        resultado.append(("Cantidade", str(animal.cantidade)))

    if getattr(animal, "data_alta", None) is not None:
        data_alta_txt = texto_data(animal.data_alta)
        if data_alta_txt:
            resultado.append(("Data de alta", data_alta_txt))

    if getattr(animal, "data_baixa", None) is not None:
        data_baixa_txt = texto_data(animal.data_baixa)
        if data_baixa_txt:
            resultado.append(("Data de baixa", data_baixa_txt))

    if getattr(animal, "estado", None) is not None and str(animal.estado).strip():
        val = str(animal.estado).strip()
        resultado.append(("Estado", _ESTADOS_ANIMAL.get(val, val)))

    if getattr(animal, "notas", None) is not None and str(animal.notas).strip():
        resultado.append(("Notas", str(animal.notas).strip()))

    return resultado


def abrir_ficha_animal(
    horta_id: int,
    animal_id: int,
    pode_editar: bool,
    accions: list[tuple[str, str, Callable[[], None]]] | None = None,
) -> None:
    """Abre o diálogo coa ficha do grupo de animais: datos, historial e fotos."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        animais = listar_animais(session, actor, horta_id)
        animal = next((a for a in animais if a.id == animal_id), None)
        if animal is None:
            return

        titulo = animal.especie
        datos = datos_animal(animal, lambda cat, cod: describir(session, cat, cod))
        feitos = historial_animal(session, actor, animal)
        linas_historial = [
            f"{texto_data(f.data)} · {f.que}" if f.data else f.que
            for f in feitos
        ]

    accion_fotos = (
        (lambda: abrir_fotos(horta_id, "animal", animal_id, titulo, pode_editar))
        if "animal" in MODELOS
        else None
    )
    abrir_ficha(titulo, datos, linas_historial, fotos=accion_fotos, accions=accions)

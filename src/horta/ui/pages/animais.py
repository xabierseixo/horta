"""Sección Animais: os grupos de animais. A cantidade sae das entradas e saídas; os coidados e
os movementos teñen as súas táboas."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.animal import Animal
from horta.services.animais import (
    ESPECIES,
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.catalogos import valores_vixentes
from horta.services.coidados_animais import en_tempo_espera
from horta.services.errors import OperacionNonPermitidaError
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def _razas(valores: list[tuple[str, str]], especie: str | None) -> list[str]:
    """As razas oficiais dunha especie: o seu código é o da especie seguido de 4 cifras
    (p.ex. Galiña de Mos 60040, galiñas 06)."""
    if not especie:
        return []
    return [nome for codigo, nome in valores if codigo[:-4] == str(int(especie))]


def seccion_animais(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        animais = listar_animais(session, actor, horta_id)
        espera = en_tempo_espera(session, actor, horta_id)
        razas = [(v.codigo, v.descricion) for v in valores_vixentes(session, "raza")]

    with ui.row().classes("w-full items-center gap-4"):
        ui.link("Ver as entradas e saídas", url_seccion(horta_id, "movementos"))
        ui.link("Ver os coidados", url_seccion(horta_id, "coidados"))

    todas_as_filas = [{
        "id": a.id,
        "nome": a.especie,
        "especie": ESPECIES.get(a.especie_codigo or "", ""),
        "raza": a.raza or "",
        "cantidade": a.cantidade,
        "estado": a.estado,
        "espera": f"En tempo de espera ata {espera[a.id]:%d/%m/%Y}" if a.id in espera else "",
    } for a in animais]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca = ui.input("Buscar").props("dense clearable")
        estado = ui.select({"": "Todos", "activo": "De alta", "baixa": "De baixa"},
                           label="Estado", value="activo").props("dense")

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Grupo"), ("especie", "Especie"), ("raza", "Raza"),
            ("cantidade", "Cantos"), ("espera", "Medicamentos"))],
        rows=todas_as_filas, row_key="id", selection="single" if pode_editar else None,
        pagination=10,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai animais" {TEXTOS_TABOA}')

    def refrescar() -> None:
        taboa.rows = filtrar_filas(todas_as_filas, busca.value or "",
                                   ["nome", "especie", "raza"], {"estado": estado.value or None})
        taboa.update()

    busca.on_value_change(refrescar)
    estado.on_value_change(refrescar)
    refrescar()

    if not pode_editar:
        return
    abrir_movemento = dialogo_movemento(horta_id)
    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(34rem, 94vw)"):
        titulo = ui.label("Novo grupo de animais").classes("text-h6")
        nome = ui.input("Nome do grupo (p.ex. Galiñas do galiñeiro de abaixo)").classes(
            "w-full")
        especie = ui.select(ESPECIES, label="Especie", with_input=True).classes("w-full")
        raza = ui.select([], label="Raza (opcional; pódese escribir outra)", with_input=True,
                         new_value_mode="add-unique", clearable=True).classes("w-full")
        with ui.row().classes("w-full no-wrap") as fila_inicio:
            cantidade = ui.input("Cantos animais hai").classes("col")
        data_alta = campo_data("Data de alta", date.today().isoformat())
        cantos_actuais = ui.label("").classes("texto-suave")
        notas = ui.textarea("Notas").classes("w-full")

        def razas_da_especie() -> None:
            opcions = _razas(razas, especie.value)
            if raza.value and raza.value not in opcions:
                opcions.append(raza.value)
            raza.set_options(opcions, value=raza.value)

        especie.on_value_change(razas_da_especie)

        def gardar() -> None:
            if not nome.value or especie.value is None:
                ui.notify("Escribe o nome do grupo e escolle a especie", type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    alta = parsear_data(data_alta.value)
                    if alta is None:
                        raise OperacionNonPermitidaError("Indica a data de alta")
                    existente = session.get(Animal, editando["id"]) if editando["id"] else None
                    if existente is None:
                        cantos = parsear_decimal(cantidade.value)
                        crear_animal(session, actor_actual, horta_id, nome.value, alta,
                                     especie_codigo=especie.value, raza=raza.value or None,
                                     cantidade=int(cantos) if cantos is not None else 0,
                                     notas=notas.value or None)
                    else:
                        actualizar_animal(session, actor_actual, existente, especie=nome.value,
                                          especie_codigo=especie.value,
                                          raza=raza.value or None, data_alta=alta,
                                          notas=notas.value or None)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(animal: Animal | None) -> None:
        editando["id"] = animal.id if animal else None
        titulo.text = "Editar grupo de animais" if animal else "Novo grupo de animais"
        nome.value = animal.especie if animal else ""
        especie.value = animal.especie_codigo if animal else None
        raza.value = animal.raza if animal else None
        razas_da_especie()
        cantidade.value = ""
        fila_inicio.set_visibility(animal is None)
        cantos_actuais.text = (f"Agora hai {animal.cantidade}. Para cambialo, apunta unha "
                               "entrada ou saída." if animal else "")
        cantos_actuais.set_visibility(animal is not None)
        data_alta.value = (animal.data_alta if animal else date.today()).isoformat()
        notas.value = (animal.notas or "") if animal else ""
        dialogo.open()

    def seleccionado() -> Animal | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un grupo na táboa", type="warning")
            return None
        with get_session() as session:
            return session.get(Animal, taboa.selected[0]["id"])

    def editar() -> None:
        animal = seleccionado()
        if animal is not None:
            abrir(animal)

    def movemento() -> None:
        abrir_movemento(None, None, taboa.selected[0]["id"] if taboa.selected else None)

    def eliminar() -> None:
        animal = seleccionado()
        if animal is None:
            return

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                obxectivo = session.get(Animal, animal.id)
                if actor_actual is None or obxectivo is None:
                    return
                ok = executar_accion(session, lambda: eliminar_animal(
                    session, actor_actual, obxectivo))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            f"Eliminar o grupo «{animal.especie}»? Só se pode se non ten nada apuntado.",
            confirmar)

    with ui.row():
        ui.button("Novo grupo", icon="add", on_click=lambda: abrir(None))
        ui.button("Entrada ou saída", icon="swap_horiz", on_click=movemento).props("outline")
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Eliminar", icon="delete", on_click=eliminar).props(
            "outline color=negative")

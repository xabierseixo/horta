"""Sección Animais: os grupos de animais. A cantidade sae das entradas e saídas; os coidados,
os movementos, a produción e o pastoreo teñen as súas táboas."""

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
from horta.services.instalacions import listar_instalacions
from horta.services.pastoreos import no_pasto, nomes_leiras
from horta.services.persoas import listar_persoas, nome_completo
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.fotos import abrir_fotos
from horta.ui.historial import abrir_historial
from horta.ui.identificados import abrir_identificados
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.pages.pastoreos import dialogo_pastoreo, dialogo_saida
from horta.ui.pages.producions_animais import dialogo_producion
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
        pastos = {animal_id: (pa.id, f"No pasto: {nomes_leiras(session, pa)} desde o "
                                     f"{pa.data_inicio:%d/%m}")
                  for animal_id, pa in no_pasto(session, actor, horta_id).items()}
        razas = [(v.codigo, v.descricion) for v in valores_vixentes(session, "raza")]

    with ui.row().classes("w-full items-center gap-4"):
        ui.link("Ver as entradas e saídas", url_seccion(horta_id, "movementos"))
        ui.link("Ver os coidados", url_seccion(horta_id, "coidados"))
        ui.link("Ver a produción", url_seccion(horta_id, "producion"))
        ui.link("Ver o pastoreo", url_seccion(horta_id, "pastoreo"))

    todas_as_filas = [{
        "id": a.id,
        "nome": a.especie,
        "especie": ESPECIES.get(a.especie_codigo or "", ""),
        "raza": a.raza or "",
        "cantidade": a.cantidade,
        "estado": a.estado,
        "espera": f"En tempo de espera ata {espera[a.id]:%d/%m/%Y}" if a.id in espera else "",
        "pasto": pastos[a.id][1] if a.id in pastos else "",
    } for a in animais]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca = ui.input("Buscar").props("dense clearable")
        estado = ui.select({"": "Todos", "activo": "De alta", "baixa": "De baixa"},
                           label="Estado", value="activo").props("dense")

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Grupo"), ("especie", "Especie"), ("raza", "Raza"),
            ("cantidade", "Cantos"), ("espera", "Medicamentos"), ("pasto", "Pasto"))],
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
    abrir_producion = dialogo_producion(horta_id)
    abrir_pastoreo = dialogo_pastoreo(horta_id)
    abrir_saida = dialogo_saida()
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
        instalacion = ui.select({}, label="Onde están (instalación)", clearable=True).classes(
            "w-full")
        titular_animais = ui.select({}, label="Titular dos animais, se non é o da explotación",
                                    with_input=True, clearable=True).classes("w-full")
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
                                     notas=notas.value or None,
                                     instalacion_id=instalacion.value,
                                     titular_animais_id=titular_animais.value)
                    else:
                        actualizar_animal(session, actor_actual, existente, especie=nome.value,
                                          especie_codigo=especie.value,
                                          raza=raza.value or None, data_alta=alta,
                                          notas=notas.value or None,
                                          instalacion_id=instalacion.value,
                                          titular_animais_id=titular_animais.value)

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
        with get_session() as session:
            actor_actual = usuario_actual(session)
            opcions = ({i.id: i.nome for i in listar_instalacions(session, actor_actual, horta_id)
                        if i.activa or (animal and i.id == animal.instalacion_id)}
                       if actor_actual else {})
            persoas = ({p.id: nome_completo(p) for p in listar_persoas(session, actor_actual,
                                                                      horta_id, False)}
                       if actor_actual else {})
        instalacion.set_options(opcions, value=animal.instalacion_id if animal else None)
        titular_animais.set_options(persoas,
                                    value=animal.titular_animais_id if animal else None)
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

    def producion() -> None:
        abrir_producion(None, None, taboa.selected[0]["id"] if taboa.selected else None)

    def ao_pasto() -> None:
        abrir_pastoreo(None, None, taboa.selected[0]["id"] if taboa.selected else None)

    def saida_do_pasto() -> None:
        animal = seleccionado()
        if animal is None:
            return
        if animal.id not in pastos:
            ui.notify("Este grupo non está no pasto", type="warning")
            return
        abrir_saida(pastos[animal.id][0])

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
        ui.button("Produción", icon="egg", on_click=producion).props("outline")
        ui.button("Ao pasto", icon="landscape", on_click=ao_pasto).props("outline")
        ui.button("Saíron do pasto", icon="logout", on_click=saida_do_pasto).props("outline")
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Identificados", icon="badge", on_click=lambda: abrir_identificados(
            horta_id, taboa.selected[0]["id"]) if taboa.selected else ui.notify(
            "Escolle primeiro un grupo na táboa", type="warning")).props("outline")
        ui.button("Historial", icon="history", on_click=lambda: abrir_historial(
            "animal", taboa.selected[0]["id"]) if taboa.selected else ui.notify(
            "Escolle primeiro un grupo na táboa", type="warning")).props("outline")
        ui.button("Fotos", icon="photo_camera", on_click=lambda: abrir_fotos(
            horta_id, "animal", taboa.selected[0]["id"], "grupo de animais", pode_editar)
            if taboa.selected else ui.notify("Escolle primeiro un grupo na táboa",
                                             type="warning")).props("outline")
        ui.button("Eliminar", icon="delete", on_click=eliminar).props(
            "outline color=negative")

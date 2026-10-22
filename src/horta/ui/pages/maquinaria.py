from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.services.maquinaria import crear_maquina, listar_maquinas
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual


def seccion_maquinaria(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        maquinas = listar_maquinas(session, actor, horta_id, so_activas=False)

    filas = [
        {"id": m.id, "alias": m.alias, "marca": m.marca_modelo or "",
         "ident": m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "",
         "inspeccion": f"{m.data_ultima_inspeccion:%d/%m/%Y}" if m.data_ultima_inspeccion else "",
         "propia": "si" if m.propia else "non"}
        for m in maquinas
    ]
    ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("alias", "Nome"), ("marca", "Marca e modelo"), ("ident", "ROMA / REGANIP / ID"),
            ("inspeccion", "Última inspección"), ("propia", "Propia"))],
        rows=filas, row_key="id",
    ).classes("w-full")

    if not pode_editar:
        return

    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        ui.label("Nova máquina").classes("text-h6")
        alias = ui.input("Nome")
        marca = ui.input("Marca e modelo")
        tipo_id = ui.select({"roma": "Nº ROMA", "reganip": "Nº REGANIP",
                             "outro": "Equipo non inscribible"}, value="roma",
                            label="Identificador")
        ident = ui.input("Número / identificador")
        propia = ui.checkbox("Propia", value=True)
        potencia = ui.input("Potencia")
        inspeccion = ui.input("Data última inspección (AAAA-MM-DD)")

        def gardar() -> None:
            if not alias.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            campo = {"roma": "num_roma", "reganip": "num_reganip",
                     "outro": "id_equipo_non_inscribible"}[tipo_id.value]
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                ok = executar_accion(session, lambda: crear_maquina(
                    session, actor, horta_id, alias.value, marca_modelo=marca.value or None,
                    propia=propia.value, potencia=parsear_decimal(potencia.value),
                    data_ultima_inspeccion=parsear_data(inspeccion.value),
                    **({campo: ident.value} if ident.value else {})))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    ui.button("Nova máquina", icon="agriculture", on_click=dialogo.open)

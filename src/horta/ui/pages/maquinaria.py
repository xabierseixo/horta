from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.models.maquina import Maquina
from horta.services.catalogos import valores_vixentes
from horta.services.maquinaria import (
    UNIDADES_POTENCIA,
    actualizar_maquina,
    aviso_inspeccion,
    crear_maquina,
    listar_maquinas,
    maquinas_de_tratamento,
)
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.ficha_maquina import abrir_ficha_maquina
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_maquinaria(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        maquinas = listar_maquinas(session, actor, horta_id, so_activas=False)
        de_tratamento = maquinas_de_tratamento(session, horta_id)
        tipos_une = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "tipo_maquinaria_une")}
        unidades_cat = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                        for v in valores_vixentes(session, "unidade_medida")}
        unidades_potencia = {c: unidades_cat.get(c, texto_catalogo("unidade_medida", c, c))
                             for c in UNIDADES_POTENCIA}
        enerxias = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                    for v in valores_vixentes(session, "tipo_enerxia")}

    filas = [
        {"id": m.id, "alias": m.alias, "marca": m.marca_modelo or "",
         "ident": m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "",
         "inspeccion": f"{m.data_ultima_inspeccion:%d/%m/%Y}" if m.data_ultima_inspeccion else "",
         "aviso": (aviso_inspeccion(m) or "") if m.id in de_tratamento else "",
         "propia": "si" if m.propia else "non", "activa": "si" if m.activa else "non"}
        for m in maquinas
    ]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("alias", "Nome"), ("marca", "Marca e modelo"), ("ident", "ROMA / REGANIP / ID"),
            ("inspeccion", "Última inspección"), ("aviso", "Inspección (RD 1702/2011)"),
            ("propia", "Propia"), ("activa", "Activa"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai máquinas rexistradas" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().classes("w-96"):
        titulo = ui.label("Nova máquina").classes("text-h6")
        activa = ui.checkbox("Activa (desmárcaa se xa non está na explotación)", value=True)
        alias = ui.input("Nome")
        tipo_une = ui.select(tipos_une, label="Tipo de máquina (UNE)", with_input=True,
                             clearable=True)
        marca = ui.input("Marca e modelo")
        tipo_id = ui.select({"roma": "Nº ROMA", "reganip": "Nº REGANIP",
                             "outro": "Equipo non inscribible"}, value="roma",
                            label="Identificador")
        ident = ui.input("Número / identificador")
        propia = ui.checkbox("Propia", value=True)
        potencia = ui.input("Potencia")
        unidade_potencia = ui.select(unidades_potencia, label="Unidade da potencia",
                                     clearable=True)
        tipo_enerxia = ui.select(enerxias, label="Tipo de enerxía", clearable=True)
        custo_hora = ui.input("Custo da hora (€)")
        inspeccion = campo_data("Data última inspección")
        adquisicion = campo_data("Data de adquisición")

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
                datos = {"tipo_une": tipo_une.value or None,
                         "marca_modelo": marca.value or None, "propia": propia.value,
                         "potencia": parsear_decimal(potencia.value),
                         "unidade_potencia": unidade_potencia.value or None,
                         "tipo_enerxia": tipo_enerxia.value or None,
                         "custo_hora": parsear_decimal(custo_hora.value),
                         "data_ultima_inspeccion": parsear_data(inspeccion.value),
                         "data_adquisicion": parsear_data(adquisicion.value),
                         "activa": activa.value, "num_roma": None, "num_reganip": None,
                         "id_equipo_non_inscribible": None, campo: ident.value or None}

                def accion() -> None:
                    maquina = session.get(Maquina, editando["id"]) if editando["id"] else None
                    if maquina is None:
                        crear_maquina(session, actor, horta_id, alias.value, **datos)
                    else:
                        actualizar_maquina(session, actor, maquina, alias=alias.value, **datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(m: Maquina | None) -> None:
        editando["id"] = m.id if m else None
        titulo.text = "Editar máquina" if m else "Nova máquina"
        alias.value, marca.value = (m.alias, m.marca_modelo or "") if m else ("", "")
        tipo_une.value = m.tipo_une if m else None
        tipo_id.value = ("reganip" if m and m.num_reganip else
                         "outro" if m and m.id_equipo_non_inscribible else "roma")
        ident.value = ((m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "")
                       if m else "")
        propia.value, activa.value = (m.propia, m.activa) if m else (True, True)
        potencia.value = f"{m.potencia:g}" if m and m.potencia is not None else ""
        unidade_potencia.value = m.unidade_potencia if m else None
        tipo_enerxia.value = m.tipo_enerxia if m else None
        custo_hora.value = f"{m.custo_hora:g}" if m and m.custo_hora is not None else ""
        inspeccion.value = (m.data_ultima_inspeccion.isoformat()
                            if m and m.data_ultima_inspeccion else "")
        adquisicion.value = m.data_adquisicion.isoformat() if m and m.data_adquisicion else ""
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha máquina na táboa", type="warning")
            return
        abrir(next(m for m in maquinas if m.id == taboa.selected[0]["id"]))

    with ui.row():
        ui.button("Nova máquina", icon="agriculture", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Ficha", icon="description", on_click=lambda: abrir_ficha_maquina(
            horta_id, taboa.selected[0]["id"], pode_editar) if taboa.selected else ui.notify(
            "Escolle primeiro unha máquina na táboa", type="warning")).props("outline")

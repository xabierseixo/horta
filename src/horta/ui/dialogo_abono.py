"""Diálogo «Novo abono»: dende o catálogo oficial ou a man (estercos, compost...)."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.services.catalogos import valores_vixentes
from horta.services.fertilizantes import (
    ESTERCOS,
    RESIDUOS,
    DatosFertilizante,
    crear_fertilizante,
    datos_desde_siex,
    opcions_siex,
)
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

_IDENTIFICADORES = {"provedor_nif": "NIF", "provedor_rega": "REGA", "provedor_nima": "NIMA"}


def dialogo_novo_abono(horta_id: int, ao_crear: Callable[[int, str], None]) -> ui.dialog:
    """Crea o diálogo (pechado). Ao gardar chama a `ao_crear(id, nome)`."""
    with get_session() as session:
        oficiais = opcions_siex(session)
        materiais = {v.codigo: v.descricion
                     for v in valores_vixentes(session, "material_fertilizante")}
        tratamentos = {v.codigo: v.descricion
                       for v in valores_vixentes(session, "tratamento_estercos")}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        ui.label("Novo abono").classes("text-h6")
        oficial = ui.select(oficiais, label="Buscar no catálogo oficial (abonos comerciais)",
                            with_input=True, clearable=True).classes("w-full")
        ui.label("Ou, se non está (esterco, compost...), enche os datos:").classes(
            "text-caption")
        nome = ui.input("Nome (p.ex. Esterco de vaca)").classes("w-full")
        material = ui.select(materiais, label="Tipo de material", with_input=True).classes(
            "w-full")
        with ui.row().classes("w-full no-wrap"):
            n = ui.input("N %").classes("col")
            p = ui.input("P₂O₅ %").classes("col")
            k = ui.input("K₂O %").classes("col")
        with ui.column().classes("w-full") as provedor:
            provedor_nome = ui.input("De onde vén (casa, granxa ou empresa)").classes("w-full")
            with ui.row().classes("w-full no-wrap"):
                tipo_id = ui.select(_IDENTIFICADORES, value="provedor_nif",
                                    label="Identificador").classes("col")
                ident = ui.input("Número (opcional)").classes("col")
            tratamento = ui.select(tratamentos, label="Tratamento do esterco (opcional)",
                                   clearable=True).classes("w-full")
        provedor.bind_visibility_from(material, "value",
                                      backward=lambda v: v in ESTERCOS | RESIDUOS)

        def encher_dende_oficial() -> None:
            if oficial.value is not None:
                with get_session() as session:
                    d = datos_desde_siex(session, oficial.value)
                nome.value, material.value = d.nome, d.material
                n.value, p.value, k.value = (f"{x:g}" for x in (d.n_pct or 0, d.p2o5_pct or 0,
                                                                 d.k2o_pct or 0))
            for campo in (nome, material, n, p, k):
                campo.set_enabled(oficial.value is None)

        oficial.on_value_change(encher_dende_oficial)

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                if oficial.value is not None:
                    datos = datos_desde_siex(session, oficial.value)
                else:
                    datos = DatosFertilizante(
                        nome=nome.value or "", material=material.value or "",
                        n_pct=parsear_decimal(n.value), p2o5_pct=parsear_decimal(p.value),
                        k2o_pct=parsear_decimal(k.value))
                if datos.material in ESTERCOS | RESIDUOS:
                    datos.provedor_nome = provedor_nome.value or None
                    if ident.value:
                        setattr(datos, tipo_id.value, ident.value)
                    datos.tratamento_estercos = tratamento.value
                creado: dict[str, int] = {}

                def accion() -> None:
                    creado["id"] = crear_fertilizante(session, actor, horta_id, datos).id

                if executar_accion(session, accion):
                    dialogo.close()
                    ao_crear(creado["id"], datos.nome.strip())

        with ui.row():
            ui.button("Gardar abono", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")
    return dialogo

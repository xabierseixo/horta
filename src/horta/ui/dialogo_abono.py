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
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

_FORMAS = (("n_organico_pct", "N orgánico %"), ("n_ureico_pct", "N ureico %"),
           ("n_nitrico_pct", "N nítrico %"), ("n_amoniacal_pct", "N amoniacal %"),
           ("p2o5_soluble_pct", "P₂O₅ soluble %"), ("materia_organica_pct",
                                                    "Materia orgánica % (estercos)"))
_METAIS = (("cadmio", "Cadmio"), ("cobre", "Cobre"), ("niquel", "Níquel"),
           ("chumbo", "Chumbo"), ("zinc", "Cinc"), ("mercurio", "Mercurio"),
           ("cromo_vi", "Cromo VI"), ("arsenico", "Arsénico"), ("cromo", "Cromo total"))


def dialogo_novo_abono(horta_id: int, ao_crear: Callable[[int, str], None]) -> ui.dialog:
    """Crea o diálogo (pechado). Ao gardar chama a `ao_crear(id, nome)`."""
    with get_session() as session:
        oficiais = opcions_siex(session)
        materiais = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "material_fertilizante")}
        tratamentos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                       for v in valores_vixentes(session, "tratamento_estercos")}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(36rem, 94vw)"):
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
        # De onde vén (empresa, granxa ou casa) apúntase en cada compra (Produtos)
        tratamento = ui.select(tratamentos, label="Tratamento do esterco (opcional)",
                               clearable=True).classes("w-full")
        tratamento.bind_visibility_from(material, "value", backward=lambda v: v in ESTERCOS)
        with ui.expansion("Valor agronómico (se o sabes)").classes("w-full"):
            formas = {c: ui.input(e).classes("w-full") for c, e in _FORMAS}
        with ui.expansion("Metais pesados do residuo (mg/kg)").classes("w-full") as metais_bloque:
            metais = {c: ui.input(e).classes("w-full") for c, e in _METAIS}
        metais_bloque.bind_visibility_from(material, "value", backward=lambda v: v in RESIDUOS)

        def encher_dende_oficial() -> None:
            if oficial.value is not None:
                with get_session() as session:
                    d = datos_desde_siex(session, oficial.value)
                nome.value, material.value = d.nome, d.material
                n.value, p.value, k.value = (f"{x:g}" for x in (d.n_pct or 0, d.p2o5_pct or 0,
                                                                 d.k2o_pct or 0))
                for chave, entrada in formas.items():
                    valor = getattr(d, chave)
                    entrada.value = f"{valor:g}" if valor else ""
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
                for campo, entrada in formas.items():
                    if entrada.value:
                        setattr(datos, campo, parsear_decimal(entrada.value))
                if datos.material in RESIDUOS:
                    for campo, entrada in metais.items():
                        setattr(datos, campo, parsear_decimal(entrada.value))
                if datos.material in ESTERCOS:
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

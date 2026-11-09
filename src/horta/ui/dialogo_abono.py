"""Diálogo «Novo abono»: dende o catálogo oficial ou a man (estercos, compost...)."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.abonado import Fertilizante
from horta.services.catalogos import valores_vixentes
from horta.services.fertilizantes import (
    ESTERCOS,
    RESIDUOS,
    DatosFertilizante,
    actualizar_fertilizante,
    crear_fertilizante,
    datos_desde_siex,
    opcions_siex,
)
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

_FORMAS = (
    ("n_organico_pct", N_("N orgánico %")),
    ("n_ureico_pct", N_("N ureico %")),
    ("n_nitrico_pct", N_("N nítrico %")),
    ("n_amoniacal_pct", N_("N amoniacal %")),
    ("p2o5_soluble_pct", N_("P₂O₅ soluble %")),
    ("materia_organica_pct", N_("Materia orgánica % (estercos)")),
)
_METAIS = (
    ("cadmio", N_("Cadmio")),
    ("cobre", N_("Cobre")),
    ("niquel", N_("Níquel")),
    ("chumbo", N_("Chumbo")),
    ("zinc", N_("Cinc")),
    ("mercurio", N_("Mercurio")),
    ("cromo_vi", N_("Cromo VI")),
    ("arsenico", N_("Arsénico")),
    ("cromo", N_("Cromo total")),
)


def dialogo_novo_abono(horta_id: int, ao_crear: Callable[[int, str], None],
                       fertilizante: Fertilizante | None = None) -> ui.dialog:
    """Crea o diálogo (pechado). Ao gardar chama a `ao_crear(id, nome)`.

    Con `fertilizante`, corrixe ese abono en vez de crear un novo (Z4)."""
    with get_session() as session:
        oficiais = opcions_siex(session)
        materiais = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "material_fertilizante")}
        tratamentos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                       for v in valores_vixentes(session, "tratamento_estercos")}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        ui.label(_("Corrixir abono") if fertilizante else _("Novo abono")).classes("text-h6")
        oficial = ui.select(
            oficiais,
            label=_("Buscar no catálogo oficial (abonos comerciais)"),
            with_input=True,
            clearable=True,
        ).classes("w-full")
        oficial.set_visibility(fertilizante is None)
        if fertilizante is None:
            ui.label(_("Ou, se non está (esterco, compost...), enche os datos:")).classes(
                "text-caption"
            )
        nome = ui.input(_("Nome (p.ex. Esterco de vaca)")).classes("w-full")
        material = ui.select(
            materiais, label=_("Tipo de material"), with_input=True
        ).classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            n = ui.input(_("N %")).classes("col")
            p = ui.input(_("P₂O₅ %")).classes("col")
            k = ui.input(_("K₂O %")).classes("col")
        # Os líquidos (xurro, purín...) cóntanse en litros; a densidade pasa a kg (Z2)
        liquido = ui.checkbox(_("É líquido (xurro, purín...)"))
        densidade = ui.input(_("Densidade (kg por litro, se a sabes)")).classes("w-full")
        densidade.bind_visibility_from(liquido, "value")
        # De onde vén (empresa, granxa ou casa) apúntase en cada compra (Produtos)
        tratamento = ui.select(
            tratamentos, label=_("Tratamento do esterco (opcional)"), clearable=True
        ).classes("w-full")
        tratamento.bind_visibility_from(material, "value", backward=lambda v: v in ESTERCOS)
        with ui.expansion(_("Valor agronómico (se o sabes)")).classes("w-full"):
            formas = {c: ui.input(_(e)).classes("w-full") for c, e in _FORMAS}
        with ui.expansion(
            _("Metais pesados do residuo (mg/kg)")
        ).classes("w-full") as metais_bloque:
            metais = {c: ui.input(_(e)).classes("w-full") for c, e in _METAIS}
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
                liquido.value = d.liquido
                densidade.value = f"{d.densidade:g}" if d.densidade else ""
            for campo in (nome, material, n, p, k, liquido, densidade):
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
                        k2o_pct=parsear_decimal(k.value), liquido=bool(liquido.value),
                        densidade=parsear_decimal(densidade.value) if liquido.value else None)
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
                    if fertilizante is not None:
                        vello = session.get(Fertilizante, fertilizante.id)
                        if vello is None:
                            return
                        datos.fertilizante_siex_codigo = vello.fertilizante_siex_codigo
                        creado["id"] = actualizar_fertilizante(session, actor, vello, datos).id
                    else:
                        creado["id"] = crear_fertilizante(session, actor, horta_id, datos).id

                if executar_accion(session, accion):
                    dialogo.close()
                    ao_crear(creado["id"], datos.nome.strip())

        if fertilizante is not None:
            f = fertilizante
            nome.value, material.value = f.nome, f.material
            n.value, p.value, k.value = (f"{x:g}" if x is not None else ""
                                         for x in (f.n_pct, f.p2o5_pct, f.k2o_pct))
            liquido.value = f.liquido
            densidade.value = f"{f.densidade:g}" if f.densidade else ""
            tratamento.value = f.tratamento_estercos
            for chave, entrada in {**formas, **metais}.items():
                valor = getattr(f, chave)
                entrada.value = f"{valor:g}" if valor is not None else ""

        with ui.row():
            ui.button(_("Gardar abono"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")
    return dialogo

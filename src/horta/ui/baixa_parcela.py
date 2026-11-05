"""Dar de baixa unha parcela con historial en vez de borrala (D4)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.parcela import Parcela
from horta.services.catalogos import valores_vixentes
from horta.services.errors import OperacionNonPermitidaError
from horta.services.parcelas import dar_de_baixa_parcela
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual


def dialogo_baixa_parcela(parcela_id: int, ao_rematar: Callable[[], None]) -> None:
    """Abre o diálogo: data e causa da baixa. Ao gardar chama a `ao_rematar`."""
    with get_session() as session:
        parcela = session.get(Parcela, parcela_id)
        causas = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                  for v in valores_vixentes(session, "causa_baixa")}
    if parcela is None:
        return
    with ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
        ui.label(f"Dar de baixa «{parcela.nome}»").classes("text-h6")
        ui.label("Ten traballos apuntados que hai que conservar, así que non se borra: "
                 "queda de baixa e segue saíndo nos informes dos anos pasados."
                 ).classes("text-caption")
        data = campo_data("Data de baixa", date.today().isoformat())
        causa = ui.select(causas, label="Causa da baixa").classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                p = session.get(Parcela, parcela_id)
                if actor is None or p is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if dia is None:
                        raise OperacionNonPermitidaError("Indica a data de baixa")
                    dar_de_baixa_parcela(session, actor, p, dia, causa.value)

                ok = executar_accion(session, accion)
            if ok:
                dialogo.close()
                ao_rematar()

        with ui.row():
            ui.button("Dar de baixa", icon="archive", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")
    dialogo.open()

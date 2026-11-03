"""Calendario e mapa da explotación (paso 13): os traballos e tarefas por día, e as parcelas
no mapa: as leiras (Catastro + SIGPAC) fanse parcelas premendo nelas."""

from __future__ import annotations

from datetime import date, timedelta
from functools import partial

from nicegui import ui

from horta.db import get_session
from horta.services.diario import listar_traballos
from horta.services.persoas import listar_persoas
from horta.ui.campos import LOCALE_GL
from horta.ui.pages.diario import Formularios, tarxeta
from horta.ui.sesion import pechar_sesion, usuario_actual

# capa → (nome, atribución, orde, zoom mínimo)
CAPAS = {
    "pnoa": ("Ortofoto (PNOA)", "PNOA © IGN", 1, 0),
    "sigpac": ("Recintos SIGPAC", "SIGPAC © FEGA", 10, 15),
    "catastro": ("Catastro (propiedade)", "© Dirección Xeral do Catastro", 11, 15),
}
# Centro de Galicia, se a explotación non ten coordenadas
_GALICIA = (42.75, -8.0)


def seccion_calendario(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        traballos = listar_traballos(session, actor, horta_id,
                                     desde=date.today() - timedelta(days=365))
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}
    formularios = Formularios(horta_id) if pode_editar else None
    por_dia: dict[str, list] = {}
    for t in traballos:
        if t.data is not None:
            por_dia.setdefault(t.data.isoformat(), []).append(t)

    calendario = ui.date(value=date.today().isoformat(), mask="YYYY-MM-DD")
    calendario._props["events"] = [d.replace("-", "/") for d in por_dia]
    calendario._props["locale"] = LOCALE_GL

    @ui.refreshable
    def do_dia() -> None:
        dia = calendario.value
        if not dia:
            return
        ui.label(f"{date.fromisoformat(dia):%d/%m/%Y}").classes(
            "text-subtitle1 text-weight-bold q-mt-md")
        lista = por_dia.get(dia, [])
        if not lista:
            ui.label("Nada apuntado nin por facer este día.").classes("texto-suave")
        with ui.column().classes("w-full gap-2"):
            for t in lista:
                tarxeta(t, partial(formularios.editar, t) if formularios else lambda: None,
                        persoas, horta_id, pode_editar, 0)

    calendario.on_value_change(do_dia.refresh)
    do_dia()



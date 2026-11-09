"""Administración → Copias de seguridade: a app fai unha cada día; aquí descárganse."""

from __future__ import annotations

from datetime import datetime

from nicegui import run, ui

from horta.db import engine, get_session
from horta.idiomas import _
from horta.models.usuario import RolGlobal, Usuario
from horta.services.copias import COPIAS_GARDADAS, facer_copia, ficheiro_da_copia, listar_copias
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual


@ui.page("/admin/copias")
def admin_copias_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        if actor.rol != RolGlobal.ADMIN:
            cabeceira_paxina()
            ui.label(_("Non tes acceso a esta páxina")).classes("text-negative")
            return
        actor_id = actor.id
        copias = listar_copias(actor)

    cabeceira_paxina(mostrar_admin=True)
    ui.label(_("Copias de seguridade")).classes("text-h6")
    ui.label(
        _(
            "A app garda cada día unha copia dos datos e das fotos, e conserva as últimas "
            "{limite}. Están neste mesmo ordenador: descarga unha de cando en vez "
            "e gárdaa noutro sitio (un pendrive, outro ordenador)."
        ).format(limite=COPIAS_GARDADAS)
    ).classes("texto-suave")

    def descargar(nome: str) -> None:
        with get_session() as session:
            actor_thread = session.get(Usuario, actor_id)
            assert actor_thread is not None
            ruta = ficheiro_da_copia(actor_thread, nome)
        if ruta is None:
            ui.notify(_("Esa copia xa non está"), type="negative")
            return
        ui.download.file(ruta)

    async def copia_agora() -> None:
        boton.disable()
        await run.io_bound(facer_copia, engine, datetime.now())
        ui.navigate.reload()

    boton = ui.button(
        _("Facer unha copia agora"), icon="backup", on_click=copia_agora
    ).props("outline")
    if not copias:
        ui.label(_("Aínda non hai ningunha copia."))
    for copia in copias:
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{copia.data:%d/%m/%Y %H:%M} · {copia.tamano / 1_000_000:.1f} MB")
            ui.button(icon="download", on_click=lambda nome=copia.nome: descargar(nome)).props(
                "flat dense").tooltip(_("Descargar"))

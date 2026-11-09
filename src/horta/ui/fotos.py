"""Botón de fotos (paso 11a): abre as fotos dun traballo, parcela, animal ou lote e deixa
engadir máis. No móbil, «Engadir foto» ofrece a cámara."""

from __future__ import annotations

from nicegui import events, ui

from horta.db import get_session
from horta.idiomas import _
from horta.models.foto import Foto
from horta.services.fotos import dar_de_baixa_foto, gardar_foto, listar_fotos
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.sesion import pechar_sesion, usuario_actual


def abrir_fotos(horta_id: int, que: str, ref_id: int, titulo: str, pode_editar: bool) -> None:
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        ui.label(_("Fotos: {titulo}").format(titulo=titulo)).classes("text-h6")

        @ui.refreshable
        def galeria() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                fotos = listar_fotos(session, actor, horta_id, que, ref_id)
            if not fotos:
                ui.label(_("Aínda non hai fotos.")).classes("texto-suave")
            with ui.grid().classes("w-full grid-cols-2 sm:grid-cols-3 gap-2"):
                for foto in fotos:
                    with ui.column().classes("gap-0"):
                        ui.image(f"/fotos/{foto.id}").classes("w-full rounded").on(
                            "click", lambda f=foto: ui.navigate.to(f"/fotos/{f.id}",
                                                                    new_tab=True))
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label(f"{foto.data:%d/%m/%Y}").classes("text-caption")
                            if pode_editar:
                                ui.button(icon="delete", on_click=lambda f=foto: (
                                    confirmar_eliminacion(_("Dar de baixa esta foto?"),
                                                          lambda: baixa(f.id)))).props(
                                    "flat dense round size=sm color=negative")

        def baixa(foto_id: int) -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                foto = session.get(Foto, foto_id)
                if actor is None or foto is None:
                    return
                if executar_accion(session, lambda: dar_de_baixa_foto(session, actor, foto)):
                    galeria.refresh()

        async def subir(e: events.UploadEventArguments) -> None:
            contido = await e.file.read()
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                if executar_accion(session, lambda: gardar_foto(
                        session, actor, horta_id, que, ref_id, contido, e.file.name)):
                    galeria.refresh()
            subida.reset()

        galeria()
        if pode_editar:
            subida = ui.upload(label=_("Engadir foto"), on_upload=subir, auto_upload=True,
                               multiple=True, max_file_size=10 * 1024 * 1024).props(
                'accept="image/*" flat bordered').classes("w-full")
        ui.button(_("Pechar"), on_click=dialogo.close).props("flat")
    dialogo.open()


def boton_fotos(horta_id: int, que: str, ref_id: int, titulo: str, pode_editar: bool,
                cantas: int = 0) -> None:
    """Icona de cámara co número de fotos; non abre o que hai debaixo (stop)."""
    with ui.button(icon="photo_camera", on_click=lambda: abrir_fotos(
            horta_id, que, ref_id, titulo, pode_editar)).props(
            "flat round dense").on("click.stop", lambda: None):
        if cantas:
            ui.badge(str(cantas)).props("floating color=primary")

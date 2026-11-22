"""Administración → Catálogos oficiais: estado, aviso e subida revisada dos ficheiros do FEGA.

O portal do FEGA ten captcha: os ficheiros descárgaos unha persoa no seu navegador e
súbeos aquí. O rexistro do MAPA actualízase só (ver horta.actualizacions).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from nicegui import events, run, ui

from horta.db import get_session
from horta.models.catalogo import CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.catalogos_estado import (
    actualizar_rexistro_mapa,
    avisos_catalogos,
    estado_catalogos,
    revisar_ficheiros,
)
from horta.services.catalogos_ficheiros import CATALOGOS_APP, PORTAL_FEGA, Revision, expandir
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fito_descargar import CATALOGO as FITOSANITARIOS
from horta.services.fito_descargar import ultima_comprobacion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def _data(valor: Any) -> str:
    return f"{valor:%d/%m/%Y}" if valor else "—"


def _texto_revision(r: Revision) -> str:
    if r.erro:
        return r.erro
    assert r.informe is not None
    if r.informe.xa_importado:
        return "Igual ca o que xa ten a app"
    if r.informe.sospeitoso:
        return (f"Ollo: daría de baixa {r.informe.baixas} de {r.informe.existentes} códigos. "
                "Comproba que é o ficheiro correcto.")
    return ""


@ui.page("/admin/catalogos")
def admin_catalogos_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        if actor.rol != RolGlobal.ADMIN:
            cabeceira_paxina()
            ui.label("Non tes acceso a esta páxina").classes("text-negative")
            return
        actor_id = actor.id
        estados = estado_catalogos(session)
        avisos = avisos_catalogos(session)
        fito = ultima_comprobacion(session)
        copia_fito = (session.query(CatalogoVersion).filter_by(catalogo=FITOSANITARIOS)
                      .order_by(CatalogoVersion.data_importacion.desc()).first())

    cabeceira_paxina(mostrar_admin=True)
    ui.label("Catálogos oficiais").classes("text-h6")
    for aviso in avisos:
        with ui.row().classes("items-center gap-2"):
            ui.icon("warning").classes("text-warning")
            ui.label(aviso)

    directorio = Path(tempfile.mkdtemp(prefix="horta-catalogos-"))
    subidos: list[Path] = []
    estado: dict[str, Any] = {"revisions": None}

    def executar(accion: Any) -> Any:
        with get_session() as session:
            actor_thread = session.get(Usuario, actor_id)
            assert actor_thread is not None
            return accion(session, actor_thread)

    with ui.card().classes("w-full"):
        ui.label("Rexistro de fitosanitarios do MAPA").classes("text-subtitle1 text-bold")
        ui.label("Actualízase só cada semana desde o MAPA.").classes("texto-suave")
        ui.label(f"Copia do {_data(copia_fito.data_importacion if copia_fito else None)} · "
                 f"última comprobación: {_data(fito.data if fito else None)}")
        if fito is not None and fito.erro:
            ui.label(fito.erro).classes("text-negative text-sm")

        async def comprobar_mapa() -> None:
            boton_mapa.disable()
            try:
                informe = await run.io_bound(executar, actualizar_rexistro_mapa)
            except (OperacionNonPermitidaError, PermisoDenegadoError) as erro:
                ui.notify(str(erro), type="negative")
                boton_mapa.enable()
                return
            if informe is None:  # a app estase a pechar
                return
            ui.notify("Sen cambios no rexistro" if informe.xa_importado else
                      f"Rexistro actualizado: {informe.altas} altas, {informe.baixas} baixas, "
                      f"{informe.cambios} cambios", type="positive")
            ui.navigate.reload()

        boton_mapa = ui.button("Comprobar agora", icon="sync", on_click=comprobar_mapa).props(
            "outline")

    with ui.card().classes("w-full"):
        ui.label("Catálogos do FEGA").classes("text-subtitle1 text-bold")
        ui.label("O portal do FEGA pide un captcha, así que os ficheiros descárgaos unha persoa "
                 "no seu navegador e súbeos aquí. Vale tamén o ZIP anual da circular PAC."
                 ).classes("texto-suave")
        ui.link("Abrir o portal do FEGA", PORTAL_FEGA, new_tab=True)
        with ui.expansion("Ficheiros que hai que baixar").classes("w-full"):
            ui.label(", ".join(f"{codigo}.xlsx" for codigo, _, _ in CATALOGOS_APP.values())
                     ).classes("text-sm")
        ui.upload(label="Subir os ficheiros (.xlsx ou .zip)", multiple=True, auto_upload=True,
                  on_upload=lambda e: gardar(e)).props('accept=".xlsx,.zip"').classes("w-full")

        @ui.refreshable
        def lista_subidos() -> None:
            if subidos:
                ui.label(f"{len(subidos)} ficheiros subidos").classes("text-sm")

        lista_subidos()

        async def gardar(e: events.UploadEventArguments) -> None:
            ruta = directorio / Path(e.file.name).name
            await e.file.save(ruta)
            subidos.append(ruta)
            estado["revisions"] = None
            lista_subidos.refresh()
            resultado.refresh()

        async def revisar_subidos() -> None:
            if not subidos:
                ui.notify("Sube primeiro os ficheiros", type="warning")
                return
            rutas = expandir(subidos, directorio)
            try:
                estado["revisions"] = await run.io_bound(
                    executar, lambda s, a: revisar_ficheiros(s, a, rutas))
            except PermisoDenegadoError as erro:
                ui.notify(str(erro), type="negative")
                return
            resultado.refresh()

        async def aplicar() -> None:
            rutas = expandir(subidos, directorio)
            revisions = await run.io_bound(
                executar, lambda s, a: revisar_ficheiros(s, a, rutas, aplicar=True))
            if revisions is None:
                return
            erros = [r for r in revisions if r.erro and r.catalogo]
            ui.notify(f"Catálogos actualizados{f' ({len(erros)} con erros)' if erros else ''}",
                      type="warning" if erros else "positive")
            shutil.rmtree(directorio, ignore_errors=True)
            ui.navigate.reload()

        @ui.refreshable
        def resultado() -> None:
            revisions: list[Revision] | None = estado["revisions"]
            if revisions is None:
                return
            nomes = {clave: nome for clave, (_, _, nome) in CATALOGOS_APP.items()}
            ui.table(
                columns=[{"name": k, "label": etiqueta, "field": k, "align": "left"}
                         for k, etiqueta in (("ficheiro", "Ficheiro"), ("catalogo", "Catálogo"),
                                             ("altas", "Novos"), ("baixas", "De baixa"),
                                             ("cambios", "Cambiados"), ("aviso", "Aviso"))],
                rows=[{"ficheiro": r.ficheiro, "catalogo": nomes.get(r.catalogo or "", "—"),
                       "altas": r.informe.altas if r.informe else "",
                       "baixas": r.informe.baixas if r.informe else "",
                       "cambios": r.informe.cambios if r.informe else "",
                       "aviso": _texto_revision(r)} for r in revisions],
                row_key="ficheiro",
            ).classes("w-full").props(f"flat bordered dense {TEXTOS_TABOA}")
            sospeitosos = [r for r in revisions if r.informe and r.informe.sospeitoso]
            confirmar = ui.checkbox("Comprobei os ficheiros: as baixas son correctas")
            confirmar.set_visibility(bool(sospeitosos))
            boton = ui.button("Aplicar", icon="check", on_click=aplicar)
            if sospeitosos:
                boton.bind_enabled_from(confirmar, "value")

        with ui.row():
            ui.button("Revisar", icon="fact_check", on_click=revisar_subidos)
        resultado()

    with ui.card().classes("w-full"):
        ui.label("Estado").classes("text-subtitle1 text-bold")
        ui.table(
            columns=[{"name": k, "label": etiqueta, "field": k, "align": "left"}
                     for k, etiqueta in (("nome", "Catálogo"), ("ficheiro", "Ficheiro do FEGA"),
                                         ("codigos", "Códigos"), ("importado", "Importado"))],
            rows=[{"nome": e.nome, "ficheiro": e.ficheiro, "codigos": e.codigos,
                   "importado": _data(e.importado)} for e in estados],
            row_key="ficheiro",
        ).classes("w-full").props(f"flat bordered dense {TEXTOS_TABOA}")

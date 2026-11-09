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
from horta.idiomas import _, ngettext
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
        return _("Igual ca o que xa ten a app")
    if r.informe.sospeitoso:
        return _(
            "Ollo: daría de baixa {baixas} de {existentes} códigos. "
            "Comproba que é o ficheiro correcto."
        ).format(baixas=r.informe.baixas, existentes=r.informe.existentes)
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
            ui.label(_("Non tes acceso a esta páxina")).classes("text-negative")
            return
        actor_id = actor.id
        estados = estado_catalogos(session)
        avisos = avisos_catalogos(session)
        fito = ultima_comprobacion(session)
        copia_fito = (session.query(CatalogoVersion).filter_by(catalogo=FITOSANITARIOS)
                      .order_by(CatalogoVersion.data_importacion.desc()).first())

    cabeceira_paxina(mostrar_admin=True)
    ui.label(_("Catálogos oficiais")).classes("text-h6")
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
        ui.label(_("Rexistro de fitosanitarios do MAPA")).classes("text-subtitle1 text-bold")
        ui.label(_("Actualízase só cada semana desde o MAPA.")).classes("texto-suave")
        ui.label(
            _("Copia do {copia} · última comprobación: {comprobacion}").format(
                copia=_data(copia_fito.data_importacion if copia_fito else None),
                comprobacion=_data(fito.data if fito else None),
            )
        )
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
            ui.notify(
                _("Sen cambios no rexistro")
                if informe.xa_importado
                else _(
                    "Rexistro actualizado: {altas} altas, {baixas} baixas, {cambios} cambios"
                ).format(
                    altas=informe.altas,
                    baixas=informe.baixas,
                    cambios=informe.cambios,
                ),
                type="positive",
            )
            ui.navigate.reload()

        boton_mapa = ui.button(
            _("Comprobar agora"), icon="sync", on_click=comprobar_mapa
        ).props("outline")

    with ui.card().classes("w-full"):
        ui.label(_("Catálogos do FEGA")).classes("text-subtitle1 text-bold")
        ui.label(
            _(
                "O portal do FEGA pide un captcha, así que os ficheiros descárgaos unha persoa "
                "no seu navegador e súbeos aquí. Vale tamén o ZIP anual da circular PAC."
            )
        ).classes("texto-suave")
        ui.link(_("Abrir o portal do FEGA"), PORTAL_FEGA, new_tab=True)
        with ui.expansion(_("Ficheiros que hai que baixar")).classes("w-full"):
            ui.label(", ".join(f"{codigo}.xlsx" for codigo, _x, _e in CATALOGOS_APP.values())
                     ).classes("text-sm")
        ui.upload(
            label=_("Subir os ficheiros (.xlsx ou .zip)"),
            multiple=True,
            auto_upload=True,
            on_upload=lambda e: gardar(e),
        ).props('accept=".xlsx,.zip"').classes("w-full")

        @ui.refreshable
        def lista_subidos() -> None:
            if subidos:
                ui.label(
                    ngettext(
                        "{n} ficheiro subido", "{n} ficheiros subidos", len(subidos)
                    ).format(n=len(subidos))
                ).classes("text-sm")

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
                ui.notify(_("Sube primeiro os ficheiros"), type="warning")
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
            ui.notify(
                _("Catálogos actualizados ({n} con erros)").format(n=len(erros))
                if erros
                else _("Catálogos actualizados"),
                type="warning" if erros else "positive",
            )
            shutil.rmtree(directorio, ignore_errors=True)
            ui.navigate.reload()

        @ui.refreshable
        def resultado() -> None:
            revisions: list[Revision] | None = estado["revisions"]
            if revisions is None:
                return
            nomes = {clave: _(nome) for clave, (_x, _e, nome) in CATALOGOS_APP.items()}
            ui.table(
                columns=[{"name": k, "label": etiqueta, "field": k, "align": "left"}
                         for k, etiqueta in (("ficheiro", _("Ficheiro")),
                                             ("catalogo", _("Catálogo")),
                                             ("altas", _("Novos")),
                                             ("baixas", _("De baixa")),
                                             ("cambios", _("Cambiados")),
                                             ("aviso", _("Aviso")))],
                rows=[{"ficheiro": r.ficheiro, "catalogo": nomes.get(r.catalogo or "", "—"),
                       "altas": r.informe.altas if r.informe else "",
                       "baixas": r.informe.baixas if r.informe else "",
                       "cambios": r.informe.cambios if r.informe else "",
                       "aviso": _texto_revision(r)} for r in revisions],
                row_key="ficheiro",
            ).classes("w-full").props(f"flat bordered dense {TEXTOS_TABOA}")
            sospeitosos = [r for r in revisions if r.informe and r.informe.sospeitoso]
            confirmar = ui.checkbox(_("Comprobei os ficheiros: as baixas son correctas"))
            confirmar.set_visibility(bool(sospeitosos))
            boton = ui.button(_("Aplicar"), icon="check", on_click=aplicar)
            if sospeitosos:
                boton.bind_enabled_from(confirmar, "value")

        with ui.row():
            ui.button(_("Revisar"), icon="fact_check", on_click=revisar_subidos)
        resultado()

    with ui.card().classes("w-full"):
        ui.label(_("Estado")).classes("text-subtitle1 text-bold")
        ui.table(
            columns=[{"name": k, "label": etiqueta, "field": k, "align": "left"}
                     for k, etiqueta in (("nome", _("Catálogo")),
                                         ("ficheiro", _("Ficheiro do FEGA")),
                                         ("codigos", _("Códigos")),
                                         ("importado", _("Importado")))],
            rows=[{"nome": _(e.nome), "ficheiro": e.ficheiro, "codigos": e.codigos,
                   "importado": _data(e.importado)} for e in estados],
            row_key="ficheiro",
        ).classes("w-full").props(f"flat bordered dense {TEXTOS_TABOA}")

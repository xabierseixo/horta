"""Sección de visitas de campo do persoal asesor técnico (GIP / mellora N7)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, time

from nicegui import ui
from sqlalchemy import func

from horta.db import get_session
from horta.idiomas import N_, _, ngettext
from horta.models.observacion import ObservacionPraga
from horta.models.persoa import Persoa
from horta.models.recomendacion import Recomendacion
from horta.models.visita import VisitaCampo
from horta.services.catalogos import describir
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.observacions import METODOS, NIVEIS
from horta.services.persoas import listar_persoas, nome_completo
from horta.services.visitas import (
    actualizar_visita,
    contido_visita,
    crear_visita,
    dar_de_baixa_visita,
    informe_visita,
    listar_visitas,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.formato_descarga import descargar_informe, selector_formato
from horta.ui.fotos import abrir_fotos
from horta.ui.lista_tarxetas import lista_tarxetas
from horta.ui.numeros import parsear_data, parsear_hora
from horta.ui.pages.observacions import dialogo_observacion
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

COLUMNAS_TABOA = [
    {"name": "data", "label": N_("Data"), "field": "data", "align": "left"},
    {"name": "asesor", "label": N_("Persoa asesora"), "field": "asesor", "align": "left"},
    {"name": "cultivos", "label": N_("Cultivos"), "field": "cultivos", "align": "left"},
    {
        "name": "num_observacions",
        "label": N_("Nº de observacións"),
        "field": "num_observacions",
        "align": "right",
    },
    {
        "name": "num_recomendacions",
        "label": N_("Nº de recomendacións"),
        "field": "num_recomendacions",
        "align": "right",
    },
    {
        "name": "proxima_visita",
        "label": N_("Próxima visita"),
        "field": "proxima_visita",
        "align": "left",
    },
]


def texto_proxima_visita(data_visita: date | None) -> str:
    """Formata a data da próxima visita para a táboa ou '—' se non hai."""
    return f"{data_visita:%d/%m/%Y}" if data_visita else "—"


def texto_aviso_proxima_visita(data_visita: date) -> str:
    """Texto do aviso en Inicio para unha próxima visita."""
    return _("Visita da persoa técnica o {data}").format(data=f"{data_visita:%d/%m}")


def texto_cultivos_visitados(nomes: list[str]) -> str:
    """Xunta os nomes dos cultivos visitados ou '—' se non hai ningún."""
    nomes_limpos = [n for n in nomes if n and n.strip()]
    return ", ".join(nomes_limpos) if nomes_limpos else "—"


def texto_hora_visita(hora_visita: time | None) -> str:
    """Devolve a hora formateada en HH:MM ou cadea baleira se non se indicou."""
    return f"{hora_visita:%H:%M}" if hora_visita else ""


def texto_resumo_contos(n_obs: int, n_rec: int) -> str:
    """Texto descritivo do número de observacións e recomendacións dunha visita."""
    obs_txt = ngettext("{n} observación", "{n} observacións", n_obs).format(n=n_obs)
    rec_txt = ngettext("{n} recomendación", "{n} recomendacións", n_rec).format(n=n_rec)
    return f"{obs_txt} · {rec_txt}"


def dialogo_visita(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo para engadir ou editar unha visita de campo."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_x: None
        persoas_todas = listar_persoas(session, actor, horta_id, so_activas=True)
        opcions_asesores = {
            p.id: nome_completo(p) for p in persoas_todas if p.ten_papel("asesor")
        }
        if not opcions_asesores:
            opcions_asesores = {p.id: nome_completo(p) for p in persoas_todas}
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        opcions_cultivos = {c.id: nome_cultivo(c) for c in cultivos_horta}

    editando: dict[str, int | None] = {"id": None}

    with (
        ui.dialog().props("persistent") as dialogo,
        ui.card().style("width: min(40rem, 94vw)"),
    ):
        titulo = ui.label(_("Nova visita")).classes("text-h6")

        if not any(p.ten_papel("asesor") for p in persoas_todas):
            ui.label(
                _("Aviso: non hai persoas co papel «Asesor/a» rexistradas en Equipo.")
            ).classes("text-caption text-warning")

        asesor = ui.select(
            opcions_asesores,
            label=_("Persoa asesora"),
            value=next(iter(opcions_asesores), None),
            with_input=True,
        ).classes("w-full")

        with ui.row().classes("w-full no-wrap gap-2"):
            data = campo_data(_("Data"), date.today().isoformat())
            hora = ui.input(_("Hora"), placeholder="HH:MM").classes("col")

        cultivos = ui.select(
            opcions_cultivos,
            label=_("Cultivos visitados (selección múltiple)"),
            multiple=True,
            with_input=True,
        ).classes("w-full")

        estado_xeral = ui.textarea(
            _("Estado xeral"),
            placeholder=_("Descrición do estado xeral dos cultivos e da explotación"),
        ).classes("w-full")

        conclusions = ui.textarea(
            _("Conclusións"),
            placeholder=_("Conclusións e indicacións da visita"),
        ).classes("w-full")

        proxima_visita = campo_data(_("Próxima visita"), "")

        def gardar() -> None:
            data_val = parsear_data(data.value)
            if data_val is None:
                ui.notify(_("Indica a data da visita"), type="warning")
                return
            if not asesor.value:
                ui.notify(_("Escolle a persoa asesora"), type="warning")
                return
            hora_val = parsear_hora(hora.value)
            proxima_val = parsear_data(proxima_visita.value)
            if proxima_val is not None and proxima_val < data_val:
                ui.notify(
                    _("A data da próxima visita non pode ser anterior á data da visita"),
                    type="warning",
                )
                return
            cultivos_val = [int(cid) for cid in (cultivos.value or [])]
            est_val = (
                estado_xeral.value.strip()
                if estado_xeral.value and estado_xeral.value.strip()
                else None
            )
            conc_val = (
                conclusions.value.strip()
                if conclusions.value and conclusions.value.strip()
                else None
            )

            with get_session() as session_g:
                actor_g = usuario_actual(session_g)
                if actor_g is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    if editando["id"] is None:
                        crear_visita(
                            session_g,
                            actor_g,
                            horta_id,
                            asesor_persoa_id=int(asesor.value),
                            data=data_val,
                            cultivos=cultivos_val,
                            hora_inicio=hora_val,
                            estado_xeral=est_val,
                            conclusions=conc_val,
                            proxima_visita=proxima_val,
                        )
                    else:
                        actualizar_visita(
                            session_g,
                            actor_g,
                            editando["id"],
                            asesor_persoa_id=int(asesor.value),
                            data=data_val,
                            cultivos=cultivos_val,
                            hora_inicio=hora_val,
                            estado_xeral=est_val,
                            conclusions=conc_val,
                            proxima_visita=proxima_val,
                        )

                ok = executar_accion(session_g, accion)
            if ok:
                dialogo.close()
                ui.navigate.reload()

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    def abrir(v: VisitaCampo | None = None) -> None:
        if v is None:
            editando["id"] = None
            titulo.text = _("Nova visita")
            asesor.value = next(iter(opcions_asesores), None)
            data.value = date.today().isoformat()
            hora.value = ""
            cultivos.value = []
            estado_xeral.value = ""
            conclusions.value = ""
            proxima_visita.value = ""
        else:
            editando["id"] = v.id
            titulo.text = _("Editar visita")
            asesor.value = v.asesor_persoa_id
            data.value = v.data.isoformat()
            hora.value = texto_hora_visita(v.hora_inicio)
            cultivos.value = list(v.cultivos or [])
            estado_xeral.value = v.estado_xeral or ""
            conclusions.value = v.conclusions or ""
            proxima_visita.value = v.proxima_visita.isoformat() if v.proxima_visita else ""
        dialogo.open()

    return abrir


def seccion_visitas(horta_id: int, pode_editar: bool) -> None:
    """Pantalla principal de visitas de campo da persoa asesora técnica."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        visitas = listar_visitas(session, actor, horta_id)
        cultivos_horta = {
            c.id: nome_cultivo(c) for c in listar_cultivos(session, actor, horta_id)
        }
        nomes_persoas = {
            p.id: nome_completo(p)
            for p in listar_persoas(session, actor, horta_id, so_activas=False)
        }
        contos_obs: dict[int | None, int] = dict(
            session.query(ObservacionPraga.visita_id, func.count(ObservacionPraga.id))
            .filter(
                ObservacionPraga.horta_id == horta_id,
                ObservacionPraga.baixa.is_(False),
                ObservacionPraga.visita_id.is_not(None),
            )
            .group_by(ObservacionPraga.visita_id)
            .tuples()
            .all()
        )
        contos_rec: dict[int | None, int] = dict(
            session.query(Recomendacion.visita_id, func.count(Recomendacion.id))
            .filter(
                Recomendacion.horta_id == horta_id,
                Recomendacion.baixa.is_(False),
                Recomendacion.visita_id.is_not(None),
            )
            .group_by(Recomendacion.visita_id)
            .tuples()
            .all()
        )

    filas = []
    for v in visitas:
        c_nomes = [cultivos_horta.get(cid, "") for cid in (v.cultivos or [])]
        filas.append({
            "id": v.id,
            "data": f"{v.data:%d/%m/%Y}",
            "asesor": nomes_persoas.get(v.asesor_persoa_id, ""),
            "cultivos": texto_cultivos_visitados(c_nomes),
            "num_observacions": contos_obs.get(v.id, 0),
            "num_recomendacions": contos_rec.get(v.id, 0),
            "proxima_visita": texto_proxima_visita(v.proxima_visita),
        })

    columnas = [{**col, "label": _(col["label"])} for col in COLUMNAS_TABOA]
    taboa = (
        ui.table(
            columns=columnas,
            rows=filas,
            row_key="id",
            selection="single" if pode_editar else None,
        )
        .classes("w-full taboa so-ordenador")
        .props(
            'flat bordered '
            f'no-data-label="{_("Aínda non hai visitas de campo rexistradas")}" '
            f"{TEXTOS_TABOA}"
        )
    )

    doc_visita_id: dict[str, int | None] = {"id": None}
    with (
        ui.dialog().props("persistent") as dialogo_doc,
        ui.card().style("width: min(28rem, 94vw)"),
    ):
        ui.label(_("Informe da visita")).classes("text-h6")
        ui.label(_("Xerar e descargar o informe da visita de campo.")).classes("text-caption")
        formato = selector_formato()

        def facer_descarga() -> None:
            v_id = doc_visita_id["id"]
            if not v_id:
                return
            with get_session() as session_doc:
                actor_doc = usuario_actual(session_doc)
                if actor_doc is None:
                    pechar_sesion()
                    return
                try:
                    visita_obj = session_doc.get(VisitaCampo, v_id)
                    if visita_obj is None:
                        ui.notify(_("Non existe a visita"), type="negative")
                        return
                    datos = informe_visita(session_doc, actor_doc, v_id)
                    data_str = f"{visita_obj.data:%Y%m%d}"
                except OperacionNonPermitidaError as erro:
                    ui.notify(str(erro), type="negative")
                    return
            descargar_informe(
                datos,
                formato.value or "xlsx",
                f"informe-visita-{v_id}-{data_str}",
                _("Informe da visita de campo"),
                "informe_visita",
            )
            dialogo_doc.close()

        with ui.row():
            ui.button(_("Descargar"), icon="download", on_click=facer_descarga)
            ui.button(_("Cancelar"), on_click=dialogo_doc.close).props("flat")

    def abrir_informe_de(v_id: int) -> None:
        doc_visita_id["id"] = v_id
        dialogo_doc.open()

    abrir_obs = dialogo_observacion(horta_id) if pode_editar else None
    abrir_rec = dialogo_tratamento_fito(horta_id) if pode_editar else None
    abrir_form_visita = dialogo_visita(horta_id) if pode_editar else None

    with (
        ui.dialog().props("persistent") as dialogo_ficha,
        ui.card().style("width: min(46rem, 94vw)"),
    ):
        titulo_ficha = ui.label(_("Ficha da visita")).classes("text-h6")
        contido_ficha = ui.column().classes("w-full gap-2")
        with ui.row().classes("w-full items-center justify-between q-mt-md flex-wrap gap-2"):
            botoes_ficha = ui.row().classes("items-center gap-2 flex-wrap")
            ui.button(_("Pechar"), on_click=dialogo_ficha.close).props("flat")

    def abrir_ficha_visita(visita_id: int) -> None:
        with get_session() as session_f:
            actor_f = usuario_actual(session_f)
            if actor_f is None:
                pechar_sesion()
                return
            try:
                cv = contido_visita(session_f, actor_f, visita_id)
            except OperacionNonPermitidaError as err:
                ui.notify(str(err), type="warning")
                return

            v = cv.visita
            asesor_obj = session_f.get(Persoa, v.asesor_persoa_id)
            asesor_txt = nome_completo(asesor_obj) if asesor_obj else ""
            if asesor_obj and asesor_obj.ropo_numero:
                asesor_txt += f" (ROPO {asesor_obj.ropo_numero})"

            obs_lista = [
                (
                    describir(session_f, o.problema_tipo, o.problema_codigo),
                    _(METODOS.get(o.metodo, o.metodo)),
                    (
                        f"{o.conto:g} {o.unidade_conto or ''}".strip()
                        if o.conto is not None
                        else _(NIVEIS.get(o.nivel or "", o.nivel or ""))
                    ),
                    o.notas or "",
                )
                for o in cv.observacions
            ]

            recs_lista = []
            for r in cv.recomendacions:
                p_nomes = []
                for p in r.problemas or []:
                    pt = (
                        p.get("tipo", "")
                        if isinstance(p, dict)
                        else getattr(p, "tipo", "")
                    )
                    pc = (
                        p.get("codigo", "")
                        if isinstance(p, dict)
                        else getattr(p, "codigo", "")
                    )
                    if pt and pc:
                        p_nomes.append(describir(session_f, pt, pc))

                pr_nomes = []
                for p in r.produtos or []:
                    p_nom = (
                        p.get("nome_comercial")
                        if isinstance(p, dict)
                        else getattr(p, "nome_comercial", "")
                    ) or (
                        p.get("materia_activa")
                        if isinstance(p, dict)
                        else getattr(p, "materia_activa", "")
                    ) or (
                        f"Reg. {p.get('num_rexistro')}"
                        if isinstance(p, dict) and p.get("num_rexistro")
                        else ""
                    )
                    if p_nom:
                        pr_nomes.append(p_nom)

                recs_lista.append((
                    ", ".join(p_nomes) if p_nomes else _("Tratamento"),
                    ", ".join(pr_nomes) if pr_nomes else "-",
                    f"{r.valida_ata:%d/%m/%Y}" if r.valida_ata else "-",
                    r.estado,
                ))

        titulo_ficha.text = _("Ficha da visita — {data}").format(data=f"{v.data:%d/%m/%Y}")
        contido_ficha.clear()
        with contido_ficha:
            with ui.element("div").style(
                "display:grid; grid-template-columns:auto 1fr; gap:4px 12px"
            ):
                ui.label(_("Data e hora:")).classes("texto-suave")
                if v.hora_inicio:
                    texto_data_hora = _("{data} ás {hora}").format(
                        data=f"{v.data:%d/%m/%Y}",
                        hora=texto_hora_visita(v.hora_inicio),
                    )
                else:
                    texto_data_hora = f"{v.data:%d/%m/%Y}"
                ui.label(texto_data_hora)

                ui.label(_("Persoa asesora:")).classes("texto-suave")
                ui.label(asesor_txt)

                ui.label(_("Cultivos visitados:")).classes("texto-suave")
                ui.label(texto_cultivos_visitados(cv.nomes_cultivos))

                ui.label(_("Próxima visita:")).classes("texto-suave")
                ui.label(texto_proxima_visita(v.proxima_visita))

            ui.label(_("Estado xeral")).classes("text-subtitle2 text-weight-bold q-mt-sm")
            ui.label(
                v.estado_xeral or _("Sen observacións xerais do estado dos cultivos.")
            ).classes("texto-suave" if not v.estado_xeral else "")

            ui.label(
                _("Observacións de pragas ({n})").format(n=len(obs_lista))
            ).classes("text-subtitle2 text-weight-bold q-mt-sm")
            if obs_lista:
                with ui.column().classes("gap-1"):
                    for prob, met, conto, notas in obs_lista:
                        notas_txt = f" — {notas}" if notas else ""
                        ui.label(f"• {prob} ({met}): {conto}{notas_txt}")
            else:
                ui.label(_("Ningunha observación rexistrada nesta visita.")).classes(
                    "texto-suave text-caption"
                )

            ui.label(
                _("Recomendacións do asesor ({n})").format(n=len(recs_lista))
            ).classes("text-subtitle2 text-weight-bold q-mt-sm")
            if recs_lista:
                with ui.column().classes("gap-1"):
                    for prob, prods, val, est in recs_lista:
                        ui.label(
                            _("• {prob}: {prods} (válida ata {val}) [{est}]").format(
                                prob=prob, prods=prods, val=val, est=est
                            )
                        )
            else:
                ui.label(_("Ningunha recomendación rexistrada nesta visita.")).classes(
                    "texto-suave text-caption"
                )

            ui.label(_("Conclusións")).classes("text-subtitle2 text-weight-bold q-mt-sm")
            ui.label(
                v.conclusions or _("Sen conclusións anotadas.")
            ).classes("texto-suave" if not v.conclusions else "")

        botoes_ficha.clear()
        with botoes_ficha:
            if pode_editar and abrir_obs:
                ui.button(
                    _("Engadir observación"),
                    icon="bug_report",
                    on_click=lambda vid=v.id: (
                        dialogo_ficha.close(),
                        abrir_obs(visita_id=vid),
                    ),
                )
            if pode_editar and abrir_rec:
                ui.button(
                    _("Nova recomendación"),
                    icon="assignment",
                    on_click=lambda vid=v.id: (
                        dialogo_ficha.close(),
                        abrir_rec(modo="recomendacion", visita_id=vid),
                    ),
                )
            ui.button(
                _("Fotos"),
                icon="photo_camera",
                on_click=lambda vid=v.id, d=v.data: abrir_fotos(
                    horta_id,
                    "visita",
                    vid,
                    _("Visita do {data}").format(data=f"{d:%d/%m/%Y}"),
                    pode_editar,
                ),
            ).props("outline")
            ui.button(
                _("Informe da visita"),
                icon="download",
                on_click=lambda vid=v.id: abrir_informe_de(vid),
            ).props("outline")
            if pode_editar and abrir_form_visita:
                ui.button(
                    _("Editar"),
                    icon="edit",
                    on_click=lambda v_obj=v: (
                        dialogo_ficha.close(),
                        abrir_form_visita(v_obj),
                    ),
                ).props("outline")

        dialogo_ficha.open()

    elementos_tarxetas = [
        (
            int(str(f["id"])),
            f"{f['data']} · {f['asesor']}",
            _("{cultivos} · Próxima: {proxima}").format(
                cultivos=f["cultivos"], proxima=f["proxima_visita"]
            ),
        )
        for f in filas
    ]
    lista_tarxetas(
        elementos_tarxetas,
        ao_tocar=abrir_ficha_visita,
        baleiro=_("Aínda non hai visitas de campo rexistradas"),
    )

    taboa.on("rowClick", lambda e: abrir_ficha_visita(e.args[1]["id"]))

    def seleccionado() -> int | None:
        if not taboa.selected:
            ui.notify(_("Escolle primeiro unha visita na táboa"), type="warning")
            return None
        return int(taboa.selected[0]["id"])

    def ver_ficha_seleccionada() -> None:
        v_id = seleccionado()
        if v_id is not None:
            abrir_ficha_visita(v_id)

    def editar_seleccionada() -> None:
        v_id = seleccionado()
        if v_id is None or not abrir_form_visita:
            return
        with get_session() as session_e:
            v_obj = session_e.get(VisitaCampo, v_id)
            if v_obj is not None:
                abrir_form_visita(v_obj)

    def fotos_seleccionada() -> None:
        v_id = seleccionado()
        if v_id is None:
            return
        data_str = taboa.selected[0].get("data", "")
        abrir_fotos(
            horta_id,
            "visita",
            v_id,
            _("Visita do {data}").format(data=data_str),
            pode_editar,
        )

    def informe_seleccionada() -> None:
        v_id = seleccionado()
        if v_id is not None:
            abrir_informe_de(v_id)

    def dar_de_baixa_seleccionada() -> None:
        v_id = seleccionado()
        if v_id is None:
            return

        def confirmar() -> None:
            with get_session() as session_b:
                actor_b = usuario_actual(session_b)
                if actor_b is None:
                    pechar_sesion()
                    return
                ok = executar_accion(
                    session_b,
                    lambda: dar_de_baixa_visita(session_b, actor_b, v_id),
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            _("Dar de baixa esta visita? Non se borra: consérvase no histórico."),
            confirmar,
        )

    with ui.row().classes("gap-2 items-center"):
        if pode_editar and abrir_form_visita:
            ui.button(
                _("Nova visita"),
                icon="add",
                on_click=lambda: abrir_form_visita(None),
            )
        with ui.row().classes("so-ordenador gap-2"):
            ui.button(
                _("Ver ficha"), icon="visibility", on_click=ver_ficha_seleccionada
            ).props("outline")
            if pode_editar:
                ui.button(
                    _("Editar"), icon="edit", on_click=editar_seleccionada
                ).props("outline")
            ui.button(
                _("Fotos"), icon="photo_camera", on_click=fotos_seleccionada
            ).props("outline")
            ui.button(
                _("Informe da visita"),
                icon="download",
                on_click=informe_seleccionada,
            ).props("outline")
            if pode_editar:
                ui.button(
                    _("Dar de baixa"),
                    icon="archive",
                    on_click=dar_de_baixa_seleccionada,
                ).props("outline")


__all__ = [
    "COLUMNAS_TABOA",
    "dialogo_visita",
    "seccion_visitas",
    "texto_aviso_proxima_visita",
    "texto_cultivos_visitados",
    "texto_hora_visita",
    "texto_proxima_visita",
    "texto_resumo_contos",
]

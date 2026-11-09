"""Sección de certificacións, autoavaliación e informes de auditoría (tarefa 182c)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.certificacion import Certificacion, PuntoAutoavaliacion
from horta.services.certificacions import (
    ESQUEMAS,
    actualizar_certificacion,
    actualizar_punto,
    baixa_certificacion,
    borrar_punto,
    crear_certificacion,
    crear_punto,
    estado_certificacion,
    informe_auditoria_xlsx,
    listar_certificacions,
    listar_puntos,
)
from horta.services.documentos import listar_documentos
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.formato_descarga import descargar_informe, selector_formato
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def texto_estado(cert: Certificacion, hoxe: date | None = None) -> str:
    """Devolve a etiqueta do estado: Vixente, Caduca pronto ou Caducado."""
    est = estado_certificacion(cert, hoxe)
    if est == "caducado":
        return "Caducado"
    if est == "caduca_pronto":
        return "Caduca pronto"
    return "Vixente"


def seccion_certificacions(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        certificacions = listar_certificacions(session, actor, horta_id)
        docs = listar_documentos(session, actor, horta_id)

    por_id = {c.id: c for c in certificacions}
    docs_opcions = {0: "Ningún", **{d.id: d.nome for d in docs}}

    ano_actual = date.today().year
    anos_disponibles = list(range(ano_actual - 2, ano_actual + 3))

    filas_cert = []
    for c in certificacions:
        nome_display = c.nome or ESQUEMAS.get(c.esquema, c.esquema)
        validez_txt = ""
        if c.data_inicio and c.data_fin:
            validez_txt = f"{texto_data(c.data_inicio)} - {texto_data(c.data_fin)}"
        elif c.data_inicio:
            validez_txt = f"Desde {texto_data(c.data_inicio)}"
        elif c.data_fin:
            validez_txt = f"Ata {texto_data(c.data_fin)}"

        filas_cert.append({
            "id": c.id,
            "nome": nome_display,
            "numero": c.numero or "",
            "entidade": c.entidade or "",
            "validez": validez_txt,
            "estado": texto_estado(c),
        })

    columnas_cert = [
        {"name": "nome", "label": "Nome / Selo", "field": "nome", "align": "left"},
        {"name": "numero", "label": "Número / GGN", "field": "numero", "align": "left"},
        {"name": "entidade", "label": "Entidade", "field": "entidade", "align": "left"},
        {"name": "validez", "label": "Validez", "field": "validez", "align": "left"},
        {"name": "estado", "label": "Estado", "field": "estado", "align": "left"},
    ]

    ui.label("Selos e certificacións de calidade").classes("text-subtitle1 text-weight-bold")
    taboa = ui.table(
        columns=columnas_cert,
        rows=filas_cert,
        row_key="id",
        selection="single",
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Aínda non hai certificacións rexistradas" {TEXTOS_TABOA}'
    )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []

    def escollida() -> Certificacion | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha certificación na táboa", type="warning")
            return None
        return por_id.get(int(taboa.selected[0]["id"]))

    def abrir_detalle_cert() -> None:
        c = escollida()
        if c:
            actualizar_panel_autoavaliacion(c.id)

    accions_tarxeta.append(("Autoavaliación", "fact_check", abrir_detalle_cert))

    editar_cert: Callable[[], None] | None = None
    dar_baixa_cert: Callable[[], None] | None = None

    if pode_editar:
        editando_cert: dict[str, int | None] = {"id": None}
        with (
            ui.dialog().props("persistent") as dialogo_cert,
            ui.card().style("width: min(34rem, 94vw)"),
        ):
            titulo_dlg = ui.label("").classes("text-h6")
            esquema_input = ui.select(ESQUEMAS, label="Selo",
                                      value="ecoloxica").classes("w-full")
            nome_input = ui.input("Nome (obrigatorio en DOP/IGP e Outro)").classes("w-full")
            numero_input = ui.input("Número (GGN de 13 díxitos en GlobalG.A.P.)").classes("w-full")
            entidade_input = ui.input("Entidade certificadora ou reguladora").classes("w-full")
            data_ini_input = campo_data("Data de inicio")
            data_fin_input = campo_data("Data de fin")
            doc_input = ui.select(docs_opcions, label="Documento adxunto",
                value=0).classes("w-full")

            def gardar_c() -> None:
                with get_session() as sess:
                    act = usuario_actual(sess)
                    if act is None:
                        pechar_sesion()
                        return

                    def accion() -> None:
                        d_ini = parsear_data(data_ini_input.value)
                        d_fin = parsear_data(data_fin_input.value)
                        d_id = int(doc_input.value) if doc_input.value else None
                        existente = (
                            sess.get(Certificacion, editando_cert["id"])
                            if editando_cert["id"]
                            else None
                        )
                        if existente is None:
                            crear_certificacion(
                                sess,
                                act,
                                horta_id,
                                esquema=str(esquema_input.value),
                                nome=nome_input.value or None,
                                numero=numero_input.value or None,
                                entidade=entidade_input.value or None,
                                data_inicio=d_ini,
                                data_fin=d_fin,
                                documento_id=d_id,
                            )
                        else:
                            actualizar_certificacion(
                                sess,
                                act,
                                existente,
                                esquema=str(esquema_input.value),
                                nome=nome_input.value or None,
                                numero=numero_input.value or None,
                                entidade=entidade_input.value or None,
                                data_inicio=d_ini,
                                data_fin=d_fin,
                                documento_id=d_id,
                            )

                    ok = executar_accion(sess, accion)
                if ok:
                    ui.navigate.reload()

            with ui.row():
                ui.button("Gardar", icon="check", on_click=gardar_c)
                ui.button("Cancelar", on_click=dialogo_cert.close).props("flat")

        def abrir_form_cert(c: Certificacion | None) -> None:
            editando_cert["id"] = c.id if c else None
            titulo_dlg.text = "Editar certificación" if c else "Nova certificación"
            esquema_input.value = c.esquema if c else "ecoloxica"
            nome_input.value = c.nome or "" if c else ""
            numero_input.value = c.numero or "" if c else ""
            entidade_input.value = c.entidade or "" if c else ""
            data_ini_input.value = texto_data(c.data_inicio) if c else ""
            data_fin_input.value = texto_data(c.data_fin) if c else ""
            doc_input.value = (c.documento_id if c and c.documento_id in docs_opcions else 0)
            dialogo_cert.open()

        def editar_c() -> None:
            if (c := escollida()) is not None:
                abrir_form_cert(c)

        def dar_baixa_c() -> None:
            c = escollida()
            if c is None:
                return

            def ao_confirmar() -> None:
                with get_session() as sess:
                    act = usuario_actual(sess)
                    if act is None:
                        pechar_sesion()
                        return
                    obx = sess.get(Certificacion, c.id)
                    if obx is None:
                        ui.notify("Esa certificación xa non existe", type="negative")
                        return
                    ok = executar_accion(sess, lambda: baixa_certificacion(sess, act, obx))
                if ok:
                    ui.navigate.reload()

            nome_c = c.nome or ESQUEMAS.get(c.esquema, c.esquema)
            confirmar_eliminacion(f"Dar de baixa a certificación «{nome_c}»?", ao_confirmar)

        editar_cert = editar_c
        dar_baixa_cert = dar_baixa_c
        accions_tarxeta.append(("Editar", "edit", editar_c))
        accions_tarxeta.append(("Dar de baixa", "delete", dar_baixa_c))

    tarxetas_da_taboa(taboa, "nome", ["estado", "entidade", "validez"], accions_tarxeta)

    with ui.row().classes("w-full items-center gap-2 q-mt-sm"):
        if pode_editar:
            ui.button("Nova certificación", icon="add", on_click=lambda: abrir_form_cert(None))
        with ui.row().classes("so-ordenador items-center gap-2"):
            ui.button("Abrir autoavaliación", icon="fact_check", on_click=abrir_detalle_cert).props(
                "outline"
            )
            if pode_editar and editar_cert is not None and dar_baixa_cert is not None:
                ui.button("Editar", icon="edit", on_click=editar_cert).props("outline")
                ui.button(
                    "Dar de baixa", icon="delete", on_click=dar_baixa_cert
                ).props("outline color=negative")

    # Contedor para o detalle da autoavaliación e informe de auditoría
    auto_container = ui.column().classes("w-full q-mt-lg gap-4")

    # Diálogo para novo/editar punto de autoavaliación
    if pode_editar:
        editando_punto: dict[str, int | None] = {"id": None, "cert_id": None}
        with (
            ui.dialog().props("persistent") as dialogo_punto,
            ui.card().style("width: min(34rem, 94vw)"),
        ):
            titulo_dlg_p = ui.label("").classes("text-h6")
            p_data_input = campo_data("Data")
            p_codigo_input = ui.input("Punto / Código (ex: FV 5.1.1)").classes("w-full")
            p_resultado_input = ui.select(
                {"cumpre": "Cumpre", "non_cumpre": "Non cumpre", "non_aplica": "Non aplica"},
                label="Resultado",
                value="cumpre",
            ).classes("w-full")
            p_evidencia_input = ui.input("Evidencia").classes("w-full")
            p_doc_input = ui.select(docs_opcions, label="Documento adxunto",
                value=0).classes("w-full")
            p_accion_input = ui.input("Acción correctora (obrigatoria se non cumpre)").classes(
                "w-full"
            )
            p_data_corr_input = campo_data("Data de corrección")

            def gardar_p() -> None:
                with get_session() as sess:
                    act = usuario_actual(sess)
                    if act is None:
                        pechar_sesion()
                        return

                    def accion() -> None:
                        dt = parsear_data(p_data_input.value) or date.today()
                        dt_corr = parsear_data(p_data_corr_input.value)
                        d_id = int(p_doc_input.value) if p_doc_input.value else None
                        existente_p = (
                            sess.get(PuntoAutoavaliacion, editando_punto["id"])
                            if editando_punto["id"]
                            else None
                        )
                        if existente_p is None:
                            crear_punto(
                                sess,
                                act,
                                int(editando_punto["cert_id"] or 0),
                                data=dt,
                                punto=p_codigo_input.value or "",
                                resultado=str(p_resultado_input.value),
                                evidencia=p_evidencia_input.value or None,
                                documento_id=d_id,
                                accion_correctora=p_accion_input.value or None,
                                data_correccion=dt_corr,
                            )
                        else:
                            actualizar_punto(
                                sess,
                                act,
                                existente_p,
                                data=dt,
                                punto=p_codigo_input.value or None,
                                resultado=str(p_resultado_input.value),
                                evidencia=p_evidencia_input.value or None,
                                documento_id=d_id,
                                accion_correctora=p_accion_input.value or None,
                                data_correccion=dt_corr,
                            )

                    ok = executar_accion(sess, accion)
                if ok:
                    dialogo_punto.close()
                    if editando_punto["cert_id"]:
                        actualizar_panel_autoavaliacion(editando_punto["cert_id"])

            with ui.row():
                ui.button("Gardar", icon="check", on_click=gardar_p)
                ui.button("Cancelar", on_click=dialogo_punto.close).props("flat")

        def abrir_form_punto(cert_id: int, p: PuntoAutoavaliacion | None) -> None:
            editando_punto["id"] = p.id if p else None
            editando_punto["cert_id"] = cert_id
            titulo_dlg_p.text = "Editar punto" if p else "Novo punto de autoavaliación"
            p_data_input.value = texto_data(p.data) if p else texto_data(date.today())
            p_codigo_input.value = p.punto if p else ""
            p_resultado_input.value = p.resultado if p else "cumpre"
            p_evidencia_input.value = p.evidencia or "" if p else ""
            p_doc_input.value = (p.documento_id if p and p.documento_id in docs_opcions else 0)
            p_accion_input.value = p.accion_correctora or "" if p else ""
            p_data_corr_input.value = texto_data(p.data_correccion) if p else ""
            dialogo_punto.open()

    def actualizar_panel_autoavaliacion(cert_id: int) -> None:
        auto_container.clear()
        with get_session() as sess:
            act = usuario_actual(sess)
            if act is None:
                pechar_sesion()
                return
            c = sess.get(Certificacion, cert_id)
            if c is None:
                return
            nome_c = c.nome or ESQUEMAS.get(c.esquema, c.esquema)

        with auto_container:
            with ui.card().classes("w-full q-pa-md"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(f"Autoavaliación: {nome_c}").classes("text-h6 font-bold")
                    ano_select = ui.select(
                        anos_disponibles,
                        value=ano_actual,
                        label="Ano",
                    ).classes("w-32")

                corpo_auto = ui.column().classes("w-full gap-3 q-mt-md")

                def recargar_tabela_ano(ano: int) -> None:
                    corpo_auto.clear()
                    with get_session() as s_ano:
                        act_ano = usuario_actual(s_ano)
                        if act_ano is None:
                            return
                        pts = listar_puntos(s_ano, act_ano, cert_id, ano)
                        por_id_p = {p.id: p for p in pts}

                    n_cumpren = sum(1 for p in pts if p.resultado == "cumpre")
                    n_non_cumpren = sum(1 for p in pts if p.resultado == "non_cumpre")
                    n_non_aplican = sum(1 for p in pts if p.resultado == "non_aplica")
                    n_pendentes = sum(
                        1 for p in pts if p.resultado == "non_cumpre" and not p.data_correccion
                    )

                    with corpo_auto:
                        ui.label(
                            f"{n_cumpren} cumpren, {n_non_cumpren} non cumpren, "
                            f"{n_non_aplican} non aplican, {n_pendentes} correccións pendentes"
                        ).classes("text-subtitle2 font-bold texto-suave")

                        # Botón para descargar informe de auditoría
                        with ui.dialog().props("persistent") as dlg_informe, ui.card().style(
                            "width: min(28rem, 94vw)"
                        ):
                            ui.label("Informe para a auditoría").classes("text-h6")
                            ui.label(
                                f"Follas de rexistros e autoavaliación de {ano} para {nome_c.rstrip('.')}."
                            ).classes("text-caption")
                            fmt_selector = selector_formato()

                            def lanzar_descarga() -> None:
                                with get_session() as s_inf:
                                    act_inf = usuario_actual(s_inf)
                                    if act_inf is None:
                                        return
                                    xlsx_b = informe_auditoria_xlsx(s_inf, act_inf, cert_id, ano)
                                descargar_informe(
                                    xlsx_b,
                                    fmt_selector.value or "xlsx",
                                    f"auditoria-{c.esquema}-{ano}",
                                    f"Auditoría {nome_c} ({ano})",
                                    "auditoria",
                                )
                                dlg_informe.close()

                            with ui.row():
                                ui.button("Descargar", icon="download", on_click=lanzar_descarga)
                                ui.button("Cancelar", on_click=dlg_informe.close).props("flat")

                        with ui.row().classes("gap-2 items-center"):
                            ui.button(
                                "Informe para a auditoría",
                                icon="download",
                                on_click=dlg_informe.open,
                            ).props("outline")
                            if pode_editar:
                                ui.button(
                                    "Novo punto",
                                    icon="add",
                                    on_click=lambda: abrir_form_punto(cert_id, None),
                                )

                        filas_p = [
                            {
                                "id": p.id,
                                "data": texto_data(p.data),
                                "punto": p.punto,
                                "resultado": {
                                    "cumpre": "Cumpre",
                                    "non_cumpre": "Non cumpre",
                                    "non_aplica": "Non aplica",
                                }.get(p.resultado, p.resultado),
                                "evidencia": p.evidencia or "",
                                "documento": docs_opcions.get(p.documento_id or 0, ""),
                                "accion_correctora": p.accion_correctora or "",
                                "data_correccion": texto_data(p.data_correccion),
                            }
                            for p in pts
                        ]
                        col_p = [
                            {"name": "data", "label": "Data", "field": "data", "align": "left"},
                            {"name": "punto", "label": "Punto", "field": "punto", "align": "left"},
                            {
                                "name": "resultado",
                                "label": "Resultado",
                                "field": "resultado",
                                "align": "left",
                            },
                            {
                                "name": "evidencia",
                                "label": "Evidencia",
                                "field": "evidencia",
                                "align": "left",
                            },
                            {
                                "name": "documento",
                                "label": "Documento",
                                "field": "documento",
                                "align": "left",
                            },
                            {
                                "name": "accion_correctora",
                                "label": "Acción correctora",
                                "field": "accion_correctora",
                                "align": "left",
                            },
                            {
                                "name": "data_correccion",
                                "label": "Corrección",
                                "field": "data_correccion",
                                "align": "left",
                            },
                        ]
                        taboa_p = ui.table(
                            columns=col_p,
                            rows=filas_p,
                            row_key="id",
                            selection="single",
                        ).classes("w-full taboa").props(
                            'flat bordered no-data-label="Sen puntos de autoavaliación este ano" '
                            f'{TEXTOS_TABOA}'
                        )

                        def escollido_punto() -> PuntoAutoavaliacion | None:
                            if not taboa_p.selected:
                                ui.notify("Escolle primeiro un punto na táboa", type="warning")
                                return None
                            return por_id_p.get(int(taboa_p.selected[0]["id"]))

                        def editar_p() -> None:
                            if (pt := escollido_punto()) is not None:
                                abrir_form_punto(cert_id, pt)

                        def borrar_p() -> None:
                            pt = escollido_punto()
                            if pt is None:
                                return

                            def ao_conf_borrar() -> None:
                                with get_session() as s_del:
                                    act_del = usuario_actual(s_del)
                                    if act_del is None:
                                        return
                                    obx_p = s_del.get(PuntoAutoavaliacion, pt.id)
                                    if obx_p is None:
                                        ui.notify("Ese punto xa non existe", type="negative")
                                        return
                                    ok = executar_accion(
                                        s_del, lambda: borrar_punto(s_del, act_del, obx_p)
                                    )
                                if ok:
                                    recargar_tabela_ano(ano)

                            confirmar_eliminacion(
                                f"Borrar o punto «{pt.punto}» da autoavaliación?", ao_conf_borrar
                            )

                        if pode_editar:
                            with ui.row().classes("gap-2 q-mt-sm"):
                                ui.button("Editar punto", icon="edit", on_click=editar_p).props(
                                    "outline"
                                )
                                ui.button(
                                    "Borrar punto", icon="delete", on_click=borrar_p
                                ).props("outline color=negative")

                ano_select.on_value_change(lambda e: recargar_tabela_ano(int(e.value)))
                recargar_tabela_ano(int(ano_select.value))

    # Se hai algunha certificación escollida ou presente por defecto, abrimos a primeira
    taboa.on(
        "selection",
        lambda _e: (
            actualizar_panel_autoavaliacion(int(taboa.selected[0]["id"]))
            if taboa.selected
            else None
        ),
    )
    if certificacions:
        taboa.selected = [filas_cert[0]]
        actualizar_panel_autoavaliacion(certificacions[0].id)

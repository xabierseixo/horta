"""Sección Documentos e certificacións (paso N2)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from nicegui import events, ui

from horta.db import get_session
from horta.models.documento import Documento
from horta.services.animais import listar_animais
from horta.services.cultivos import listar_cultivos
from horta.services.documentos import (
    TIPOS_DOCUMENTO,
    actualizar_documento,
    crear_documento,
    dar_de_baixa_documento,
    estado_documento,
    gardar_ficheiro,
    listar_documentos,
)
from horta.services.instalacions import listar_instalacions
from horta.services.lotes import listar_lotes
from horta.services.maquinaria import listar_maquinas
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_persoas, nome_completo
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def texto_estado_documento(documento: Any, hoxe: date | None = None) -> str:
    """Devolve «Vixente», «Caduca en N días» (ou «Caduca hoxe») ou «Caducado»."""
    dia = hoxe or date.today()
    estado = estado_documento(documento, dia)
    if estado == "caducado":
        return "Caducado"
    if estado == "caduca_pronto":
        if getattr(documento, "data_caducidade", None) is not None:
            dias = (documento.data_caducidade - dia).days
            if dias <= 0:
                return "Caduca hoxe"
            if dias == 1:
                return "Caduca en 1 día"
            return f"Caduca en {dias} días"
    return "Vixente"


def texto_aviso_documento(documento: Any, hoxe: date | None = None) -> str:
    """Texto do aviso en Inicio: caducado ou días que lle quedan para caducar."""
    dia = hoxe or date.today()
    nome = getattr(documento, "nome", "")
    caducidade = getattr(documento, "data_caducidade", None)
    if caducidade and caducidade < dia:
        return f"O documento «{nome}» caducou o {caducidade:%d/%m/%Y}"
    if caducidade:
        dias = (caducidade - dia).days
        if dias <= 0:
            return f"O documento «{nome}» caduca hoxe"
        if dias == 1:
            return f"O documento «{nome}» caduca en 1 día"
        return f"O documento «{nome}» caduca en {dias} días"
    return f"O documento «{nome}»"


def obter_opcions_referencia(session: Any, actor: Any, horta_id: int) -> dict[str, str]:
    """Selector «De que é»: toda a explotación e cada un dos recursos dispoñibles."""
    opcions: dict[str, str] = {"": "Toda a explotación"}
    for p in listar_parcelas(session, actor, horta_id):
        opcions[f"parcela:{p.id}"] = f"Parcela: {p.nome}"
    for c in listar_cultivos(session, actor, horta_id):
        c_nome = f"{c.especie} ({c.variedade})" if c.variedade else c.especie
        opcions[f"cultivo:{c.id}"] = f"Cultivo: {c_nome}"
    for a in listar_animais(session, actor, horta_id):
        a_nome = f"{a.especie} ({a.raza})" if a.raza else a.especie
        opcions[f"animal:{a.id}"] = f"Animal: {a_nome}"
    for m in listar_maquinas(session, actor, horta_id, so_activas=False):
        opcions[f"maquina:{m.id}"] = f"Máquina: {m.alias}"
    for per in listar_persoas(session, actor, horta_id, so_activas=False):
        opcions[f"persoa:{per.id}"] = f"Persoa: {nome_completo(per)}"
    for lo in listar_lotes(session, actor, horta_id):
        opcions[f"lote:{lo.id}"] = f"Lote: {lo.codigo}"
    for i in listar_instalacions(session, actor, horta_id):
        opcions[f"instalacion:{i.id}"] = f"Instalación: {i.nome}"
    return opcions


def seccion_documentos(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        documentos = listar_documentos(session, actor, horta_id)
        opcions_ref = obter_opcions_referencia(session, actor, horta_id)

    por_id = {d.id: d for d in documentos}

    filas = [
        {
            "id": d.id,
            "tipo_clave": d.tipo,
            "nome": d.nome,
            "tipo": TIPOS_DOCUMENTO.get(d.tipo, d.tipo),
            "emisor": d.emisor or "",
            "caduca": texto_data(d.data_caducidade),
            "estado": texto_estado_documento(d),
            "de_que": opcions_ref.get(
                f"{d.que}:{d.ref_id}" if d.que and d.ref_id else "",
                "Toda a explotación",
            ),
        }
        for d in documentos
    ]

    with ui.row().classes("w-full items-center justify-between q-mb-sm"):
        filtro_tipo = ui.select(
            {"": "Todos", **TIPOS_DOCUMENTO},
            value="",
            label="Tipo",
        ).classes("w-64")

    taboa = ui.table(
        columns=[
            {"name": k, "label": e, "field": k, "align": "left"}
            for k, e in (
                ("nome", "Documento"),
                ("tipo", "Tipo"),
                ("emisor", "Emisor"),
                ("caduca", "Caduca"),
                ("estado", "Estado"),
                ("de_que", "De que é"),
            )
        ],
        rows=filas,
        row_key="id",
        selection="single",
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Aínda non hai documentos" {TEXTOS_TABOA}'
    )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    refrescar_tarxetas = tarxetas_da_taboa(
        taboa, "nome", ["estado", "de_que"], accions_tarxeta
    )

    def aplicar_filtro() -> None:
        tipo_escollido = filtro_tipo.value
        taboa.selected.clear()
        if not tipo_escollido:
            taboa.rows = filas
        else:
            taboa.rows = [f for f in filas if f["tipo_clave"] == tipo_escollido]
        refrescar_tarxetas.refresh()

    filtro_tipo.on_value_change(aplicar_filtro)

    def escollido() -> Documento | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un documento na táboa", type="warning")
            return None
        return por_id.get(int(taboa.selected[0]["id"]))

    def ver_ficheiro() -> None:
        doc = escollido()
        if doc is None:
            return
        if not doc.ficheiro:
            ui.notify("O documento non ten ningún ficheiro adxunto", type="warning")
            return
        ui.navigate.to(f"/documentos/{doc.id}", new_tab=True)

    accions_tarxeta.append(("Ver o ficheiro", "description", ver_ficheiro))

    editar: Callable[[], None] | None = None
    dar_baixa: Callable[[], None] | None = None

    if pode_editar:
        editando: dict[str, int | None] = {"id": None}
        ficheiro_pendente: dict[str, Any] = {"contido": None, "nome": None}

        with (
            ui.dialog().props("persistent") as dialogo,
            ui.card().style("width: min(34rem, 94vw)"),
        ):
            titulo = ui.label("").classes("text-h6")
            tipo = ui.select(TIPOS_DOCUMENTO, label="Tipo").classes("w-full")
            nome = ui.input("Nome").classes("w-full")
            emisor = ui.input("Emisor").classes("w-full")
            numero = ui.input("Número ou código").classes("w-full")
            data_emision = campo_data("Data de emisión")
            data_caducidade = campo_data("Data de caducidade")
            de_que = ui.select(opcions_ref, label="De que é", value="").classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

            async def ao_subir(e: events.UploadEventArguments) -> None:
                ficheiro_pendente["contido"] = await e.file.read()
                ficheiro_pendente["nome"] = e.file.name

            upload = (
                ui.upload(
                    label="Ficheiro (PDF ou imaxe)",
                    auto_upload=True,
                    multiple=False,
                    max_file_size=20 * 1024 * 1024,
                    on_upload=ao_subir,
                )
                .props('accept=".pdf,image/*" flat bordered')
                .classes("w-full")
            )

            def gardar() -> None:
                if not tipo.value:
                    ui.notify("Escolle o tipo de documento", type="warning")
                    return
                if not nome.value or not nome.value.strip():
                    ui.notify("O nome do documento é obrigatorio", type="warning")
                    return

                que_val: str | None = None
                ref_id_val: int | None = None
                if de_que.value:
                    partes = de_que.value.split(":", 1)
                    if len(partes) == 2:
                        que_val = partes[0]
                        ref_id_val = int(partes[1])

                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return

                    def accion() -> None:
                        d_emision = parsear_data(data_emision.value)
                        d_caducidade = parsear_data(data_caducidade.value)
                        existente = (
                            session.get(Documento, editando["id"])
                            if editando["id"]
                            else None
                        )
                        if existente is None:
                            doc = crear_documento(
                                session,
                                actor_actual,
                                horta_id,
                                tipo=tipo.value,
                                nome=nome.value or "",
                                emisor=emisor.value or None,
                                numero=numero.value or None,
                                data_emision=d_emision,
                                data_caducidade=d_caducidade,
                                que=que_val,
                                ref_id=ref_id_val,
                                notas=notas.value or None,
                            )
                        else:
                            doc = actualizar_documento(
                                session,
                                actor_actual,
                                existente,
                                tipo=tipo.value,
                                nome=nome.value or "",
                                emisor=emisor.value or None,
                                numero=numero.value or None,
                                data_emision=d_emision,
                                data_caducidade=d_caducidade,
                                que=que_val,
                                ref_id=ref_id_val,
                                notas=notas.value or None,
                            )
                        if ficheiro_pendente["contido"] is not None:
                            gardar_ficheiro(
                                session,
                                actor_actual,
                                doc,
                                ficheiro_pendente["contido"],
                                ficheiro_pendente["nome"],
                            )

                    ok = executar_accion(session, accion)
                if ok:
                    ui.navigate.reload()

            with ui.row():
                ui.button("Gardar", icon="check", on_click=gardar)
                ui.button("Cancelar", on_click=dialogo.close).props("flat")

        def abrir(documento: Documento | None) -> None:
            editando["id"] = documento.id if documento else None
            ficheiro_pendente["contido"] = None
            ficheiro_pendente["nome"] = None
            upload.reset()
            titulo.text = "Editar documento" if documento else "Novo documento"
            tipo.value = documento.tipo if documento else next(iter(TIPOS_DOCUMENTO.keys()))
            nome.value = documento.nome if documento else ""
            emisor.value = documento.emisor or "" if documento else ""
            numero.value = documento.numero or "" if documento else ""
            data_emision.value = texto_data(documento.data_emision) if documento else ""
            data_caducidade.value = texto_data(documento.data_caducidade) if documento else ""
            if documento and documento.que and documento.ref_id:
                de_que.value = f"{documento.que}:{documento.ref_id}"
            else:
                de_que.value = ""
            notas.value = documento.notas or "" if documento else ""
            dialogo.open()

        def editar() -> None:
            if (doc := escollido()) is not None:
                abrir(doc)

        def dar_baixa() -> None:
            doc = escollido()
            if doc is None:
                return

            def ao_confirmar() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    obxectivo = session.get(Documento, doc.id)
                    if obxectivo is None:
                        ui.notify("Ese documento xa non existe", type="negative")
                        return
                    ok = executar_accion(
                        session, lambda: dar_de_baixa_documento(session, actor_actual, obxectivo)
                    )
                if ok:
                    ui.navigate.reload()

            confirmar_eliminacion(f"Dar de baixa o documento «{doc.nome}»?", ao_confirmar)

        accions_tarxeta.append(("Editar", "edit", editar))
        accions_tarxeta.append(("Dar de baixa", "delete", dar_baixa))

    with ui.row().classes("w-full items-center gap-2 q-mt-sm"):
        if pode_editar:
            ui.button("Novo documento", icon="add", on_click=lambda: abrir(None))
        with ui.row().classes("so-ordenador items-center gap-2"):
            ui.button("Ver o ficheiro", icon="description", on_click=ver_ficheiro).props("outline")
            if pode_editar and editar is not None and dar_baixa is not None:
                ui.button("Editar", icon="edit", on_click=editar).props("outline")
                ui.button(
                    "Dar de baixa", icon="delete", on_click=dar_baixa
                ).props("outline color=negative")

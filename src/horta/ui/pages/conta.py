"""Páxina de xestión da conta de usuario e dereitos RGPD."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import segno
from nicegui import ui

from horta.db import get_session
from horta.models.dispositivo import Dispositivo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.dispositivos import (
    crear_dispositivo,
    listar_dispositivos,
    revogar_dispositivo,
)
from horta.services.legal import borrar_minha_conta, exportar_meus_datos
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual


def url_conexion_campo(orixe: str, clave: str) -> str:
    """Arma o enderezo para conectar un dispositivo móbil á app do campo."""
    base = orixe.rstrip("/")
    return f"{base}/campo/#clave={clave}"


def formato_data_alta(data: datetime | None) -> str:
    """Formata a data de alta do dispositivo móbil."""
    if data is None:
        return ""
    return f"{data:%d/%m/%Y}"


def formato_ultimo_uso(data: datetime | None) -> str:
    """Formata a data do último uso ou indica que non hai rexistro."""
    if data is None:
        return "Nunca"
    return f"{data:%d/%m/%Y}"


@ui.page("/conta")
def conta_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        actor_id = actor.id
        nome = actor.nome
        email = actor.email
        e_admin_global = actor.rol == RolGlobal.ADMIN
        data_politica = (
            f"Política aceptada o {actor.politica_aceptada_en:%d/%m/%Y}"
            if actor.politica_aceptada_en
            else "Política pendente de aceptación"
        )
        dispositivos = [d for d in listar_dispositivos(session, actor) if not d.revogado]

    cabeceira_paxina(mostrar_admin=e_admin_global)
    ui.label("A miña conta").classes("text-h6")

    def descargar_datos() -> None:
        with get_session() as session:
            actor_db = session.get(Usuario, actor_id)
            if actor_db is None:
                pechar_sesion()
                return
            contido = exportar_meus_datos(session, actor_db)
        ui.download.content(contido, "os-meus-datos.json")

    with ui.dialog() as dialog_borrar, ui.card().classes("w-full max-w-md"):
        ui.label("Borrar a miña conta").classes("text-h6 text-negative")
        ui.label(
            "A conta queda borrada e non poderás entrar máis. "
            "Os rexistros obrigatorios das explotacións consérvanse, como esixe a normativa."
        )
        campo_confirmar = ui.input(placeholder="BORRAR").classes("w-full")

        def confirmar_borrado() -> None:
            with get_session() as session:
                actor_db = session.get(Usuario, actor_id)
                if actor_db is None:
                    pechar_sesion()
                    return
                feito = executar_accion(
                    session, lambda: borrar_minha_conta(session, actor_db)
                )
            if feito:
                dialog_borrar.close()
                pechar_sesion()

        with ui.row().classes("justify-end gap-2 w-full q-mt-md"):
            ui.button("Cancelar", on_click=dialog_borrar.close).props("flat")
            boton_confirmar = ui.button(
                "Borrar a miña conta",
                icon="delete_forever",
                on_click=confirmar_borrado,
            ).props("color=negative")
            boton_confirmar.disable()

        def ao_escribir(e: Any) -> None:
            if (e.value or "").strip() == "BORRAR":
                boton_confirmar.enable()
            else:
                boton_confirmar.disable()

        campo_confirmar.on_value_change(ao_escribir)

    def abrir_dialogo_borrar() -> None:
        campo_confirmar.value = ""
        boton_confirmar.disable()
        dialog_borrar.open()

    with (
        ui.dialog().props("persistent") as dialog_qr,
        ui.card().classes("w-full max-w-md items-center text-center gap-3"),
    ):
        ui.label("Conectar o móbil").classes("text-h6 font-bold")
        ui.label(
            "Le o código coa cámara do teu móbil para abrir a app conectada:"
        ).classes("texto-suave text-caption")
        qr_img = ui.image().style("width: 14rem; height: 14rem")
        enderezo_label = ui.label("").classes(
            "text-caption text-weight-bold break-all q-px-sm"
        )
        url_actual: dict[str, str] = {}

        def copiar_enderezo() -> None:
            u = url_actual.get("url")
            if u:
                ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(u)})")
                ui.notify("Enderezo copiado ao portapapeis", type="positive")

        boton_copiar = ui.button(
            "Copiar enderezo", icon="content_copy", on_click=copiar_enderezo
        ).props("outline")
        ui.label(
            "Este código só se mostra agora. Se o perdes, crea outro."
        ).classes("text-warning text-caption")

        def pechar_qr() -> None:
            dialog_qr.close()
            ui.navigate.reload()

        ui.button("Pechar", on_click=pechar_qr).props("flat")

    def abrir_dialogo_qr(clave: str) -> None:
        enderezo_label.text = "Xerando código..."
        boton_copiar.disable()
        dialog_qr.open()

        async def amosar() -> None:
            orixe = await ui.run_javascript("window.location.origin")
            url = url_conexion_campo(str(orixe or ""), clave)
            url_actual["url"] = url
            enderezo_label.text = url
            qr_img.set_source(segno.make(url, error="m").svg_data_uri(scale=6))
            boton_copiar.enable()

        ui.timer(0.05, amosar, once=True)

    with (
        ui.dialog().props("persistent") as dialog_nome,
        ui.card().classes("w-full max-w-md"),
    ):
        ui.label("Conectar un móbil").classes("text-h6 font-bold")
        ui.label(
            "Indica un nome para identificar este móbil (por exemplo, «Móbil de Ana»):"
        ).classes("texto-suave text-caption")
        campo_nome = ui.input("Nome do móbil", placeholder="Móbil de Ana").classes("w-full")

        def crear() -> None:
            nome_disp = (campo_nome.value or "").strip()
            if not nome_disp:
                ui.notify("Indica o nome do dispositivo", type="warning")
                return
            with get_session() as s:
                actor_db = usuario_actual(s)
                if actor_db is None:
                    pechar_sesion()
                    return
                creado: list[tuple[Dispositivo, str]] = []
                feito = executar_accion(
                    s, lambda: creado.append(crear_dispositivo(s, actor_db, nome_disp))
                )
            if not feito or not creado:
                return
            _, clave = creado[0]
            dialog_nome.close()
            abrir_dialogo_qr(clave)

        campo_nome.on("keydown.enter", crear)

        with ui.row().classes("justify-end gap-2 w-full q-mt-md"):
            ui.button("Cancelar", on_click=dialog_nome.close).props("flat")
            ui.button("Conectar", icon="check", on_click=crear)

    def abrir_dialogo_nome() -> None:
        campo_nome.value = ""
        dialog_nome.open()

    def desconectar(disp_id: int, disp_nome: str) -> None:
        def confirmar() -> None:
            with get_session() as s:
                actor_db = usuario_actual(s)
                disp = s.get(Dispositivo, disp_id)
                if actor_db is None or disp is None:
                    return
                feito = executar_accion(
                    s, lambda: revogar_dispositivo(s, actor_db, disp)
                )
            if feito:
                ui.notify(f"Dispositivo «{disp_nome}» desconectado", type="positive")
                ui.navigate.reload()

        confirmar_eliminacion(
            f"Desconectar o dispositivo «{disp_nome}»? "
            "Non poderá volver acceder á app do campo.",
            confirmar,
            boton="Desconectar",
            icona="link_off",
        )

    with ui.card().classes("w-full max-w-xl q-pa-md gap-3"):
        ui.label(nome).classes("text-subtitle1 text-weight-bold")
        ui.label(email).classes("texto-suave")
        ui.label(data_politica).classes("texto-suave")

        with ui.row().classes("gap-4 q-my-sm"):
            ui.link("Aviso legal", "/legal/aviso", new_tab=True)
            ui.link("Política de privacidade", "/legal/privacidade", new_tab=True)

        with ui.row().classes("gap-3 q-mt-md wrap"):
            ui.button(
                "Descargar os meus datos",
                icon="download",
                on_click=descargar_datos,
            ).props("outline")
            ui.button(
                "Borrar a miña conta",
                icon="delete",
                on_click=abrir_dialogo_borrar,
            ).props("color=negative")

    with ui.card().classes("w-full max-w-xl q-pa-md gap-3 q-mt-md"):
        ui.label("App do campo (sen cobertura)").classes("text-subtitle1 text-weight-bold")
        ui.label(
            "Para apuntar no campo sen cobertura, conecta o teu móbil: "
            "le o código coa cámara e engade a app á pantalla de inicio."
        ).classes("texto-suave")

        with ui.row().classes("gap-3 items-center wrap"):
            ui.button(
                "Conectar un móbil",
                icon="smartphone",
                on_click=abrir_dialogo_nome,
            )
            ui.link("Abrir a app do campo", "/campo/", new_tab=True)

        ui.label("Móbiles conectados").classes("text-subtitle2 text-weight-bold q-mt-sm")

        with ui.column().classes("w-full gap-2"):
            if not dispositivos:
                ui.label("Aínda non hai ningún móbil conectado.").classes(
                    "texto-suave text-caption"
                )
            else:
                for disp in dispositivos:
                    with ui.card().classes("w-full q-pa-sm"):
                        with ui.row().classes("w-full items-center justify-between no-wrap"):
                            with ui.column().classes("gap-0"):
                                ui.label(disp.nome).classes("font-bold")
                                alta = formato_data_alta(disp.creado_en)
                                uso = formato_ultimo_uso(disp.ultimo_uso)
                                ui.label(
                                    f"Alta: {alta} · Último uso: {uso}"
                                ).classes("texto-suave text-caption")
                            ui.button(
                                "Desconectar",
                                icon="link_off",
                                on_click=lambda _=None, d=disp: desconectar(d.id, d.nome),
                            ).props("flat color=negative dense")

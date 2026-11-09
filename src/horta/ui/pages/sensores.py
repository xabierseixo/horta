"""Sección de sensores IoT, lecturas e avisos (tarefas 183a, 183b e 183c)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.sensor import Sensor
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.instalacions import listar_instalacions
from horta.services.parcelas import listar_parcelas
from horta.services.sensores import (
    TIPOS_SENSOR,
    actualizar_sensor,
    baixa_sensor,
    consumo_periodo,
    crear_sensor,
    importar_ficheiro,
    lecturas,
    listar_sensores,
    nova_clave,
    ultima_lectura,
)
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

URL_API_LECTURAS = "/api/sensores/lecturas"


def estado_sensor(
    sensor: Sensor,
    ult: tuple[datetime, float] | None = None,
    agora: datetime | None = None,
) -> str:
    """Devolve o estado do sensor: «Ben», «Fóra de límite» ou «Sen datos»."""
    if ult is None:
        return "Sen datos"
    momento, valor = ult
    if momento is None or valor is None:
        return "Sen datos"

    ref_agora = agora or datetime.now(timezone.utc)
    if ref_agora.tzinfo is not None and momento.tzinfo is None:
        momento_cmp = momento.replace(tzinfo=timezone.utc)
        agora_cmp = ref_agora
    elif ref_agora.tzinfo is None and momento.tzinfo is not None:
        momento_cmp = momento
        agora_cmp = ref_agora.replace(tzinfo=timezone.utc)
    else:
        momento_cmp = momento
        agora_cmp = ref_agora

    if agora_cmp - momento_cmp > timedelta(hours=24):
        return "Sen datos"
    if sensor.limiar_min is not None and valor < sensor.limiar_min:
        return "Fóra de límite"
    if sensor.limiar_max is not None and valor > sensor.limiar_max:
        return "Fóra de límite"
    return "Ben"


def texto_ultima_lectura(
    ult: tuple[datetime, float] | Sensor | None,
    unidade_ou_ult: str | tuple[datetime, float] | None = None,
) -> str:
    """Formata a última lectura con valor e hora (ex. «23.5 °C (09/11 10:00)»)."""
    if isinstance(ult, Sensor):
        sensor = ult
        lectura = unidade_ou_ult if isinstance(unidade_ou_ult, tuple) else None
        u = sensor.unidade or ""
    else:
        lectura = ult
        u = str(unidade_ou_ult) if isinstance(unidade_ou_ult, str) else ""

    if lectura is None:
        return "—"
    momento, valor = lectura
    u_str = f" {u}".rstrip() if u else ""
    hora_str = momento.strftime("%d/%m %H:%M")
    return f"{valor:g}{u_str} ({hora_str})"


def texto_localizacion(
    sensor: Sensor,
    parcelas: dict[int, str] | None = None,
    cultivos: dict[int, str] | None = None,
    instalacions: dict[int, str] | None = None,
) -> str:
    """Describe onde está instalado o sensor (cultivo, parcela ou instalación)."""
    p_map = parcelas or {}
    c_map = cultivos or {}
    i_map = instalacions or {}
    if sensor.cultivo_id:
        c_nome = c_map.get(sensor.cultivo_id) or f"Cultivo {sensor.cultivo_id}"
        return f"Cultivo: {c_nome}"
    if sensor.parcela_id:
        p_nome = p_map.get(sensor.parcela_id) or f"Parcela {sensor.parcela_id}"
        return f"Parcela: {p_nome}"
    if sensor.instalacion_id:
        i_nome = i_map.get(sensor.instalacion_id) or f"Instalación {sensor.instalacion_id}"
        return f"Instalación: {i_nome}"
    return "Xeral"


def opcions_grafica_sensor(
    sensor: Sensor,
    lecturas: list[tuple[datetime, float]],
) -> dict[str, Any] | None:
    """Configuración de ui.echart coa evolución temporal das lecturas dun sensor."""
    if not lecturas:
        return None

    datas_str = [m.strftime("%d/%m %H:%M") for m, _ in lecturas]
    valores = [float(v) for _, v in lecturas]

    serie: dict[str, Any] = {
        "name": sensor.nome,
        "type": "line",
        "data": valores,
        "connectNulls": True,
        "smooth": True,
    }

    mark_data: list[dict[str, Any]] = []
    if sensor.limiar_min is not None:
        mark_data.append({"yAxis": float(sensor.limiar_min), "name": "Mínimo"})
    if sensor.limiar_max is not None:
        mark_data.append({"yAxis": float(sensor.limiar_max), "name": "Máximo"})

    if mark_data:
        serie["markLine"] = {
            "lineStyle": {"type": "dashed", "color": "#e53935"},
            "data": mark_data,
        }

    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 0},
        "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
        "xAxis": {"type": "category", "data": datas_str},
        "yAxis": {"type": "value", "name": sensor.unidade or ""},
        "series": [serie],
    }


def _exemplo_curl(url_completa: str, clave: str) -> str:
    """Xera o comando curl de exemplo para enviar unha lectura."""
    return (
        f"curl -X POST {url_completa} \\\n"
        f'  -H "Content-Type: application/json" \\\n'
        f'  -H "X-Clave-Sensor: {clave}" \\\n'
        f'  -d \'{{"valor": 23.5}}\''
    )


def dialogo_clave_sensor() -> Callable[[str, str], None]:
    """Diálogo que amosa a clave do sensor unha soa vez, con URL e curl de exemplo."""
    with (
        ui.dialog().props("persistent") as dialog,
        ui.card().style("width: min(38rem, 94vw)"),
    ):
        titulo = ui.label("Clave do sensor").classes("text-h6 text-weight-bold")
        ui.label(
            "Garda a clave: non se volve amosar",
        ).classes("text-negative text-weight-bold q-my-xs")

        ui.label("Clave de autenticación (cabeceira X-Clave-Sensor):").classes(
            "text-caption texto-suave q-mt-sm"
        )
        clave_input = (
            ui.input(value="").props("readonly outlined dense").classes("w-full font-mono")
        )

        def copiar_clave() -> None:
            js = f"navigator.clipboard.writeText({json.dumps(clave_input.value)})"
            ui.run_javascript(js)
            ui.notify("Clave copiada ao portapapeis", type="positive")

        with ui.row().classes("w-full justify-end q-mb-sm"):
            ui.button(
                "Copiar clave",
                icon="content_copy",
                on_click=copiar_clave,
            ).props("outline dense")

        ui.label("URL para enviar lecturas (POST):").classes("text-caption texto-suave")
        url_input = (
            ui.input(value="").props("readonly outlined dense").classes("w-full font-mono")
        )

        ui.label("Exemplo con curl:").classes("text-caption texto-suave q-mt-sm")
        curl_area = (
            ui.textarea(value="")
            .props("readonly outlined rows=4")
            .classes("w-full font-mono text-caption")
        )

        def copiar_curl() -> None:
            js = f"navigator.clipboard.writeText({json.dumps(curl_area.value)})"
            ui.run_javascript(js)
            ui.notify("Comando curl copiado ao portapapeis", type="positive")

        with ui.row().classes("w-full items-center justify-between q-mt-md"):
            ui.button(
                "Copiar curl",
                icon="terminal",
                on_click=copiar_curl,
            ).props("flat dense")
            ui.button("Entendido / Pechar", on_click=dialog.close).props("flat")

    def abrir(nome_sensor: str, clave: str) -> None:
        titulo.text = f"Clave para «{nome_sensor}»"
        clave_input.value = clave
        url_defecto = f"https://o-teu-dominio{URL_API_LECTURAS}"
        url_input.value = url_defecto
        curl_area.value = _exemplo_curl(url_defecto, clave)

        async def actualizar_orixe() -> None:
            try:
                orixe = await ui.run_javascript("window.location.origin", timeout=1.0)
                if orixe and isinstance(orixe, str) and orixe.startswith("http"):
                    url_real = f"{orixe}{URL_API_LECTURAS}"
                    url_input.value = url_real
                    curl_area.value = _exemplo_curl(url_real, clave)
            except Exception:
                pass

        ui.timer(0.1, actualizar_orixe, once=True)
        dialog.open()

    return abrir


def dialogo_axuda_sensores() -> Callable[[], None]:
    """Diálogo explicativo de como conectar sensores e enviar lecturas."""
    with (
        ui.dialog() as dialog,
        ui.card().style("width: min(44rem, 94vw)"),
    ):
        ui.label("Como conectar sensores á aplicación").classes("text-h6 text-weight-bold")
        with ui.column().classes("w-full gap-2 text-body2"):
            ui.markdown(
                """
Podes conectar calquera dispositivo ou script para enviar lecturas automáticas:

1. **HTTP directo (ESP32, Raspberry Pi, Arduino)**:
   - Envía un `POST` a `/api/sensores/lecturas` coa cabeceira `X-Clave-Sensor: <a_tua_clave>`.
   - Corpo JSON: `{"valor": 23.5}` ou `[{"valor": 23.5, "momento": "2026-11-09T10:00:00"}]`.

2. **LoRaWAN con The Things Network (TTN v3)**:
   - Indica no formulario do sensor o nome da variable (`campo_payload`).
   - Crea un webhook en TTN apuntando a `/api/sensores/ttn` coa cabeceira `X-Clave-Sensor`.

3. **Ficheiros CSV ou JSON**:
   - Podes importar datos históricos premendo en «Importar CSV ou JSON» na ficha do sensor.
                """
            )
        with ui.row().classes("w-full justify-end q-mt-md"):
            ui.button("Pechar", on_click=dialog.close).props("flat")

    def abrir() -> None:
        dialog.open()

    return abrir


def dialogo_sensor(
    horta_id: int,
    on_gardado: Callable[[], None] | None = None,
    on_clave_xerada: Callable[[str, str], None] | None = None,
) -> Callable[[Sensor | None], None]:
    """Constrúe o formulario de alta ou edición dun sensor (só ADMIN)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in listar_parcelas(session, actor, horta_id)}
        cultivos = {
            c.id: f"{nome_cultivo(c)} — {parcelas.get(c.parcela_id, '')}"
            for c in listar_cultivos(session, actor, horta_id)
        }
        instalacions = {i.id: i.nome for i in listar_instalacions(session, actor, horta_id)}

    opcions_tipo = {
        k: f"{v.nome} ({v.unidade})" if v.unidade else v.nome
        for k, v in TIPOS_SENSOR.items()
    }

    editando: dict[str, int | None] = {"id": None}

    with (
        ui.dialog().props("persistent") as dialog,
        ui.card().style("width: min(38rem, 94vw)"),
    ):
        titulo = ui.label("Novo sensor").classes("text-h6 text-weight-bold")
        nome_input = ui.input("Nome do sensor").classes("w-full")
        tipo_input = ui.select(opcions_tipo, label="Tipo de sensor").classes("w-full")
        unidade_input = ui.input("Unidade de medida").classes("w-full")

        def ao_cambiar_tipo() -> None:
            t = tipo_input.value
            if t and t in TIPOS_SENSOR:
                u_defecto = TIPOS_SENSOR[t].unidade
                if u_defecto and not unidade_input.value:
                    unidade_input.value = u_defecto

        tipo_input.on_value_change(ao_cambiar_tipo)

        ui.label("Onde está instalado (escolle como máximo un):").classes(
            "text-caption texto-suave q-mt-sm"
        )
        parcela_input = ui.select(parcelas, label="Parcela", clearable=True).classes("w-full")
        cultivo_input = ui.select(cultivos, label="Cultivo", clearable=True).classes("w-full")
        instalacion_input = ui.select(
            instalacions, label="Instalación", clearable=True
        ).classes("w-full")

        with ui.row().classes("w-full no-wrap gap-2"):
            limiar_min_input = ui.input("Límite mínimo (opcional)").classes("col")
            limiar_max_input = ui.input("Límite máximo (opcional)").classes("col")

        campo_payload_input = (
            ui.input("Campo no payload LoRaWAN")
            .classes("w-full")
            .props('hint="Só se usas The Things Network" persistent-hint')
        )

        def gardar() -> None:
            if not nome_input.value or not nome_input.value.strip():
                ui.notify("O nome do sensor é obrigatorio", type="warning")
                return
            if not tipo_input.value:
                ui.notify("Escolle o tipo de sensor", type="warning")
                return

            v_min = parsear_decimal(limiar_min_input.value)
            v_max = parsear_decimal(limiar_max_input.value)
            if v_min is not None and v_max is not None and v_min > v_max:
                ui.notify("O límite mínimo non pode ser maior ca o máximo", type="warning")
                return

            with get_session() as s:
                act = usuario_actual(s)
                if act is None:
                    pechar_sesion()
                    return

                res_novo: list[tuple[Sensor, str]] = []

                def accion() -> None:
                    if editando["id"] is None:
                        s_creado, c_creada = crear_sensor(
                            s,
                            act,
                            horta_id,
                            nome=nome_input.value.strip(),
                            tipo=tipo_input.value,
                            unidade=unidade_input.value.strip() if unidade_input.value else None,
                            parcela_id=parcela_input.value,
                            cultivo_id=cultivo_input.value,
                            instalacion_id=instalacion_input.value,
                            campo_payload=campo_payload_input.value.strip()
                            if campo_payload_input.value
                            else None,
                            limiar_min=v_min,
                            limiar_max=v_max,
                        )
                        res_novo.append((s_creado, c_creada))
                    else:
                        sensor_existente = s.get(Sensor, editando["id"])
                        if sensor_existente is None:
                            return
                        actualizar_sensor(
                            s,
                            act,
                            sensor_existente,
                            nome=nome_input.value.strip(),
                            unidade=unidade_input.value.strip() if unidade_input.value else "",
                            parcela_id=parcela_input.value,
                            cultivo_id=cultivo_input.value,
                            instalacion_id=instalacion_input.value,
                            campo_payload=campo_payload_input.value.strip()
                            if campo_payload_input.value
                            else None,
                            limiar_min=v_min,
                            limiar_max=v_max,
                        )

                ok = executar_accion(s, accion)

            if ok:
                dialog.close()
                if res_novo and on_clave_xerada:
                    s_novo, c_nova = res_novo[0]
                    on_clave_xerada(s_novo.nome, c_nova)
                if on_gardado:
                    on_gardado()

        with ui.row().classes("w-full items-center justify-between q-mt-md"):
            with ui.row():
                ui.button("Gardar", icon="check", on_click=gardar)
                ui.button("Cancelar", on_click=dialog.close).props("flat")

    def abrir(s: Sensor | None) -> None:
        if s is None:
            editando["id"] = None
            titulo.text = "Novo sensor"
            nome_input.value = ""
            tipo_input.value = "humidade_chan"
            unidade_input.value = TIPOS_SENSOR["humidade_chan"].unidade
            parcela_input.value = None
            cultivo_input.value = None
            instalacion_input.value = None
            limiar_min_input.value = ""
            limiar_max_input.value = ""
            campo_payload_input.value = ""
            tipo_input.set_enabled(True)
        else:
            editando["id"] = s.id
            titulo.text = f"Editar «{s.nome}»"
            nome_input.value = s.nome
            tipo_input.value = s.tipo
            tipo_input.set_enabled(False)
            unidade_input.value = s.unidade
            parcela_input.value = s.parcela_id
            cultivo_input.value = s.cultivo_id
            instalacion_input.value = s.instalacion_id
            limiar_min_input.value = f"{s.limiar_min:g}" if s.limiar_min is not None else ""
            limiar_max_input.value = f"{s.limiar_max:g}" if s.limiar_max is not None else ""
            campo_payload_input.value = s.campo_payload or ""

        dialog.open()

    return abrir


def dialogo_ficha_sensor(
    horta_id: int,
    pode_editar: bool,
    e_horta_admin: bool,
    on_clave_xerada: Callable[[str, str], None] | None = None,
    on_editar_sensor: Callable[[Sensor], None] | None = None,
    on_cambio: Callable[[], None] | None = None,
) -> Callable[[Sensor], None]:
    """Ficha do sensor: gráfica echart, timer de actualización, consumo e importación."""
    sensor_actual: dict[str, Any] = {"sensor": None}

    with (
        ui.dialog().props("persistent") as dialog,
        ui.card().style("width: min(56rem, 96vw)"),
    ):
        with ui.row().classes("w-full items-start justify-between"):
            with ui.column().classes("gap-0"):
                titulo = ui.label("").classes("text-h6 text-weight-bold")
                subtitulo = ui.label("").classes("text-caption texto-suave")
            estado_badge = ui.label("").classes("etiqueta-ok")

        with ui.row().classes("w-full items-center justify-between q-mt-sm wrap gap-2"):
            periodo_selector = ui.select(
                {"24h": "24 h", "7d": "7 días", "30d": "30 días", "1a": "1 ano"},
                value="7d",
                label="Período",
            ).classes("w-36")
            consumo_label = ui.label("").classes("text-subtitle1 text-weight-bold text-primary")

        grafica_container = ui.column().classes("w-full q-my-sm")
        sen_datos_aviso = ui.label("Non hai lecturas rexistradas neste período").classes(
            "texto-suave q-my-md"
        )

        def debuxar_grafica() -> None:
            s: Sensor | None = sensor_actual["sensor"]
            if s is None:
                return

            p = periodo_selector.value or "7d"
            agora = datetime.now(timezone.utc)
            if p == "24h":
                desde = agora - timedelta(hours=24)
            elif p == "7d":
                desde = agora - timedelta(days=7)
            elif p == "30d":
                desde = agora - timedelta(days=30)
            elif p == "1a":
                desde = agora - timedelta(days=365)
            else:
                desde = agora - timedelta(days=7)

            with get_session() as session:
                act = usuario_actual(session)
                if act is None:
                    return
                # Recargar sensor fresco da base de datos
                sensor_db = session.get(Sensor, s.id)
                if sensor_db is None or not sensor_db.activo:
                    dialog.close()
                    return
                sensor_actual["sensor"] = sensor_db
                s = sensor_db

                lista_lecturas = lecturas(session, act, s.id, desde, agora)
                tipo_info = TIPOS_SENSOR.get(s.tipo)
                if tipo_info and tipo_info.acumulado:
                    consumo = consumo_periodo(session, act, s.id, desde, agora)
                    if consumo is not None:
                        consumo_label.text = f"Consumo no período: {consumo:g} {s.unidade}"
                        consumo_label.set_visibility(True)
                    else:
                        consumo_label.set_visibility(False)
                else:
                    consumo_label.set_visibility(False)

                ult = ultima_lectura(session, act, s.id)
                st = estado_sensor(s, ult)
                estado_badge.text = st
                clase = (
                    "etiqueta-ok"
                    if st == "Ben"
                    else ("etiqueta-aviso" if st == "Fóra de límite" else "texto-suave")
                )
                estado_badge.classes(replace=clase)

            opcions = opcions_grafica_sensor(s, lista_lecturas)
            grafica_container.clear()
            with grafica_container:
                if opcions:
                    sen_datos_aviso.set_visibility(False)
                    ui.echart(opcions).classes("w-full").style("height: 320px")
                else:
                    sen_datos_aviso.set_visibility(True)

        periodo_selector.on_value_change(lambda: debuxar_grafica())
        timer_actualizacion = ui.timer(60.0, debuxar_grafica, active=False)

        if pode_editar:
            with ui.expansion("Importar CSV ou JSON", icon="upload_file").classes("w-full q-mt-sm"):
                ui.label(
                    "Formatos: CSV (momento;valor) ou JSON ([{momento: ..., valor: ...}])."
                ).classes("text-caption texto-suave q-mb-xs")

                def manexar_subida(e: Any) -> None:
                    s_obj = sensor_actual["sensor"]
                    if s_obj is None:
                        return
                    try:
                        nome = e.name
                        contido = e.content.read()
                        with get_session() as session:
                            act = usuario_actual(session)
                            if act is None:
                                pechar_sesion()
                                return
                            gardadas = importar_ficheiro(session, act, s_obj.id, nome, contido)
                        ui.notify(f"Importáronse {gardadas} lecturas con éxito", type="positive")
                        debuxar_grafica()
                        if on_cambio:
                            on_cambio()
                    except Exception as err:
                        ui.notify(f"Erro na importación: {err}", type="negative")

                ui.upload(
                    label="Escoller ficheiro .csv ou .json",
                    auto_upload=True,
                    on_upload=manexar_subida,
                ).props('accept=".csv,.json" flat bordered').classes("w-full")

        def pechar_ficha() -> None:
            timer_actualizacion.deactivate()
            dialog.close()

        with ui.row().classes("w-full items-center justify-between q-mt-md wrap gap-2"):
            with ui.row().classes("gap-2 wrap"):
                if e_horta_admin:

                    def pedir_nova_clave() -> None:
                        s_obj = sensor_actual["sensor"]
                        if s_obj is None:
                            return

                        def confirmar() -> None:
                            with get_session() as session:
                                act = usuario_actual(session)
                                if act is None:
                                    return
                                res: list[str] = []
                                ok = executar_accion(
                                    session,
                                    lambda: res.append(nova_clave(session, act, s_obj.id)),
                                )
                            if ok and res and on_clave_xerada:
                                on_clave_xerada(s_obj.nome, res[0])

                        confirmar_eliminacion(
                            f"Xerar unha nova clave para «{s_obj.nome}»? "
                            "A clave anterior deixará de funcionar inmediatamente.",
                            confirmar,
                        )

                    ui.button("Nova clave", icon="key", on_click=pedir_nova_clave).props(
                        "outline dense"
                    )

                    def abrir_edicion() -> None:
                        s_obj = sensor_actual["sensor"]
                        if s_obj and on_editar_sensor:
                            pechar_ficha()
                            on_editar_sensor(s_obj)

                    ui.button("Editar", icon="edit", on_click=abrir_edicion).props(
                        "outline dense"
                    )

            ui.button("Pechar", on_click=pechar_ficha).props("flat")

    def abrir(s: Sensor) -> None:
        sensor_actual["sensor"] = s
        tipo_str = TIPOS_SENSOR[s.tipo].nome if s.tipo in TIPOS_SENSOR else s.tipo
        titulo.text = f"{s.nome} ({s.unidade})" if s.unidade else s.nome
        subtitulo.text = f"{tipo_str} · {texto_localizacion(s)}"
        consumo_label.set_visibility(False)
        debuxar_grafica()
        timer_actualizacion.activate()
        dialog.open()

    return abrir


def seccion_sensores(horta_id: int, pode_editar: bool, e_horta_admin: bool = False) -> None:
    """Pantalla principal da sección de Sensores: lista, ficha e accións."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return

        sensores = listar_sensores(session, actor, horta_id, so_activos=True)
        parcelas = {p.id: p.nome for p in listar_parcelas(session, actor, horta_id)}
        cultivos = {
            c.id: f"{nome_cultivo(c)} — {parcelas.get(c.parcela_id, '')}"
            for c in listar_cultivos(session, actor, horta_id)
        }
        instalacions = {i.id: i.nome for i in listar_instalacions(session, actor, horta_id)}

        filas = []
        sensores_por_id: dict[int, Sensor] = {}
        for s in sensores:
            sensores_por_id[s.id] = s
            ult = ultima_lectura(session, actor, s.id)
            tipo_nome = TIPOS_SENSOR[s.tipo].nome if s.tipo in TIPOS_SENSOR else s.tipo
            filas.append(
                {
                    "id": s.id,
                    "nome": s.nome,
                    "tipo": tipo_nome,
                    "onde": texto_localizacion(s, parcelas, cultivos, instalacions),
                    "ultima": texto_ultima_lectura(s, ult),
                    "estado": estado_sensor(s, ult),
                }
            )

    abrir_clave = dialogo_clave_sensor()
    abrir_axuda = dialogo_axuda_sensores()

    abrir_ficha: Callable[[Sensor], None]
    abrir_formulario: Callable[[Sensor | None], None]

    def refrescar_todo() -> None:
        ui.navigate.reload()

    abrir_formulario = (
        dialogo_sensor(
            horta_id,
            on_gardado=refrescar_todo,
            on_clave_xerada=abrir_clave,
        )
        if e_horta_admin
        else (lambda _: None)
    )

    abrir_ficha = dialogo_ficha_sensor(
        horta_id,
        pode_editar=pode_editar,
        e_horta_admin=e_horta_admin,
        on_clave_xerada=abrir_clave,
        on_editar_sensor=abrir_formulario if e_horta_admin else None,
        on_cambio=refrescar_todo,
    )

    if not sensores:
        with ui.column().classes("tarxeta w-full gap-2 q-pa-md q-my-md"):
            ui.label("Aínda non tes sensores conectados nesta explotación").classes(
                "text-subtitle1 text-weight-bold"
            )
            ui.label(
                "Podes conectar sondas de humidade ou temperatura do solo, estacións de aire "
                "e choiva, contadores de auga para o control de regas ou niveis de depósitos."
            )
            with ui.row().classes("items-center gap-2 q-mt-sm wrap"):
                ui.button(
                    "Como conectar sensores",
                    icon="help_outline",
                    on_click=abrir_axuda,
                ).props("outline")
                if e_horta_admin:
                    ui.button(
                        "Novo sensor",
                        icon="add",
                        on_click=lambda: abrir_formulario(None),
                    )
        return

    with ui.row().classes("w-full items-center justify-between q-mb-sm wrap gap-2"):
        ui.label(f"{len(sensores)} sensores activos").classes("texto-suave")
        ui.button(
            "Como conectar sensores",
            icon="help_outline",
            on_click=abrir_axuda,
        ).props("flat dense")

    columnas = [
        {"name": "nome", "label": "Nome", "field": "nome"},
        {"name": "tipo", "label": "Tipo", "field": "tipo"},
        {"name": "onde", "label": "Localización", "field": "onde"},
        {"name": "ultima", "label": "Última lectura", "field": "ultima"},
        {"name": "estado", "label": "Estado", "field": "estado"},
    ]

    taboa = (
        ui.table(
            columns=columnas,
            rows=filas,
            row_key="id",
            selection="single",
        )
        .classes("w-full taboa so-ordenador")
        .props(f'flat bordered no-data-label="Non hai sensores" {TEXTOS_TABOA}')
    )

    taboa.add_slot(
        "body-cell-estado",
        """
        <q-td :props="props">
            <span :class="props.value === 'Ben' ? 'etiqueta-ok' :
                          (props.value === 'Fóra de límite' ? 'etiqueta-aviso' : 'texto-suave')">
                {{ props.value }}
            </span>
        </q-td>
        """,
    )

    def abrir_ficha_seleccionada() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un sensor na táboa", type="warning")
            return
        s_id = taboa.selected[0]["id"]
        s_obx = sensores_por_id.get(s_id)
        if s_obx is not None:
            abrir_ficha(s_obx)

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = [
        ("Ver ficha", "query_stats", abrir_ficha_seleccionada),
    ]

    if e_horta_admin:

        def editar_seleccionado() -> None:
            if not taboa.selected:
                ui.notify("Escolle primeiro un sensor na táboa", type="warning")
                return
            s_id = taboa.selected[0]["id"]
            s_obx = sensores_por_id.get(s_id)
            if s_obx is not None:
                abrir_formulario(s_obx)

        def nova_clave_seleccionado() -> None:
            if not taboa.selected:
                ui.notify("Escolle primeiro un sensor na táboa", type="warning")
                return
            s_id = taboa.selected[0]["id"]
            s_obx = sensores_por_id.get(s_id)
            if s_obx is None:
                return

            def confirmar() -> None:
                with get_session() as session:
                    act = usuario_actual(session)
                    if act is None:
                        return
                    res: list[str] = []
                    ok = executar_accion(
                        session,
                        lambda: res.append(nova_clave(session, act, s_obx.id)),
                    )
                if ok and res:
                    abrir_clave(s_obx.nome, res[0])

            confirmar_eliminacion(
                f"Xerar unha nova clave para «{s_obx.nome}»? "
                "A clave anterior deixará de funcionar inmediatamente.",
                confirmar,
            )

        def dar_de_baixa_seleccionado() -> None:
            if not taboa.selected:
                ui.notify("Escolle primeiro un sensor na táboa", type="warning")
                return
            s_id = taboa.selected[0]["id"]
            s_obx = sensores_por_id.get(s_id)
            if s_obx is None:
                return

            def confirmar() -> None:
                with get_session() as session:
                    act = usuario_actual(session)
                    if act is None:
                        return
                    sensor_db = session.get(Sensor, s_obx.id)
                    if sensor_db is None:
                        return
                    ok = executar_accion(session, lambda: baixa_sensor(session, act, sensor_db))
                if ok:
                    ui.notify(f"Sensor «{s_obx.nome}» dado de baixa", type="positive")
                    refrescar_todo()

            confirmar_eliminacion(
                f"Dar de baixa o sensor «{s_obx.nome}»? "
                "Non se borra: consérvase o histórico de lecturas.",
                confirmar,
            )

        accions_tarxeta.extend(
            [
                ("Editar", "edit", editar_seleccionado),
                ("Nova clave", "key", nova_clave_seleccionado),
                ("Dar de baixa", "archive", dar_de_baixa_seleccionado),
            ]
        )

    tarxetas_da_taboa(taboa, "nome", ["tipo", "onde", "ultima", "estado"], accions_tarxeta)

    with ui.row().classes("w-full items-center gap-2 q-mt-md"):
        if e_horta_admin:
            ui.button("Novo sensor", icon="add", on_click=lambda: abrir_formulario(None))
        ui.button(
            "Ver ficha e gráfica",
            icon="query_stats",
            on_click=abrir_ficha_seleccionada,
        ).props("outline")
        if e_horta_admin:
            ui.button(
                "Editar",
                icon="edit",
                on_click=editar_seleccionado,
            ).props("outline").classes("so-ordenador")
            ui.button(
                "Nova clave",
                icon="key",
                on_click=nova_clave_seleccionado,
            ).props("outline").classes("so-ordenador")
            ui.button(
                "Dar de baixa",
                icon="archive",
                on_click=dar_de_baixa_seleccionado,
            ).props("outline color=negative").classes("so-ordenador")

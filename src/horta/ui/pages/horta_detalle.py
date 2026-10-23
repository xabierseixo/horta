from __future__ import annotations

from datetime import date
from typing import Any

from loguru import logger
from nicegui import app, ui

from horta.db import get_session
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.auth import normalizar_email
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    listar_cultivos,
)
from horta.services.en_regra import requisitos_en_regra
from horta.services.errors import PermisoDenegadoError
from horta.services.fertilizacions import (
    actualizar_fertilizacion,
    crear_fertilizacion,
    eliminar_fertilizacion,
    listar_fertilizacions,
)
from horta.services.hortas import (
    actualizar_horta,
    cambiar_rol_membro,
    comprobar_rol_horta,
    eliminar_horta,
    engadir_membro,
    estado_rexistro,
    listar_hortas_usuario,
    quitar_membro,
)
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.services.tarefas import (
    actualizar_tarefa,
    contar_tarefas_pendentes,
    crear_tarefa,
    eliminar_tarefa,
    listar_tarefas,
    listar_tarefas_atrasadas,
    listar_tarefas_pendentes_hoxe,
    listar_tarefas_proximas,
    marcar_feita,
    marcar_pendente,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.layout import (
    SECCIONS,
    cabeceira_seccion,
    marco_horta,
    normalizar_seccion,
    url_seccion,
)
from horta.ui.nav import cabeceira_paxina
from horta.ui.pages.maquinaria import seccion_maquinaria
from horta.ui.pages.persoas import seccion_persoas
from horta.ui.pages.tratamentos_fito import seccion_tratamentos_fito
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie

_PROPS_TABOA = 'flat bordered no-data-label="Aínda non hai rexistros"'

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_ESTADOS_PARCELA = ("activa", "inactiva")
_ESTADOS_ANIMAL = ("activo", "baixa")
_ROLES_HORTA = ("admin", "editor", "lector")

_ESTADOS_CULTIVO = ("planificado", "sementado", "plantado", "colleitado", "finalizado")
_UNIDADES_CULTIVO = ("kg", "unidades", "ducias", "mazos")

_PRIORIDADES_TAREFA = ("baixa", "media", "alta")


@ui.page("/hortas/{horta_id}")
def horta_detalle_redirixir(horta_id: int) -> None:
    ui.navigate.to(url_seccion(horta_id, "resumo"))


@ui.page("/hortas/{horta_id}/{seccion}")
def horta_detalle_page(horta_id: int, seccion: str) -> None:
    seccion = normalizar_seccion(seccion)
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
            app.storage.user["ultima_horta"] = horta_id
        except PermisoDenegadoError:
            cabeceira_paxina()
            ui.label("Non tes acceso a esta explotación").classes("text-negative")
            return
        horta = session.get(Horta, horta_id)
        if horta is None:
            cabeceira_paxina()
            ui.label("Esta explotación xa non existe").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        fertilizacions = listar_fertilizacions(session, actor, horta_id)
        tarefas = listar_tarefas(session, actor, horta_id)
        tarefas_pendentes_hoxe = listar_tarefas_pendentes_hoxe(session, actor, horta_id)
        tarefas_proximas = listar_tarefas_proximas(session, actor, horta_id)
        tarefas_atrasadas = listar_tarefas_atrasadas(session, actor, horta_id)
        n_tarefas_pendentes = contar_tarefas_pendentes(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA
        e_horta_admin = membro.rol == RolHorta.ADMIN
        e_admin_global = actor.rol == RolGlobal.ADMIN
        horta_nome = horta.nome
        horta_descricion = horta.descricion
        horta_uso_profesional = horta.uso_profesional
        horta_titular_nome = horta.titular_nome or ""
        horta_titular_nif = horta.titular_nif or ""
        horta_codigo_reaga = horta.codigo_reaga or ""
        horta_codigo_rega = horta.codigo_rega or ""
        estado = estado_rexistro(horta)
        requisitos = requisitos_en_regra(session, actor, horta)
        hortas_usuario = {h.id: h.nome for h, _ in listar_hortas_usuario(session, actor)}
        nome_usuario = actor.nome

    marco_horta(
        horta_id=horta_id,
        seccion=seccion,
        hortas=hortas_usuario,
        nome_usuario=nome_usuario,
        e_horta_admin=e_horta_admin,
        e_admin_global=e_admin_global,
    )

    if e_horta_admin:
        with ui.dialog() as dialog_config_horta, ui.card():
            ui.label("Configurar explotación").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome).classes("w-full")
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "").classes(
                "w-full"
            )
            ui.label("Tipo de explotación").classes("text-caption texto-suave")
            tipo_radio = ui.radio(
                {True: "Profesional", False: "Non profesional"}, value=horta_uso_profesional
            ).props("inline")
            with ui.column().classes("w-full gap-1").bind_visibility_from(tipo_radio, "value"):
                titular_nome_input = ui.input(
                    "Titular (nome ou razón social)", value=horta_titular_nome
                ).classes("w-full")
                titular_nif_input = ui.input("NIF do titular", value=horta_titular_nif).classes(
                    "w-full"
                )
                reaga_input = ui.input(
                    "Nº REAGA (ES + 12 díxitos)", value=horta_codigo_reaga
                ).classes("w-full")
            rega_input = ui.input(
                "Nº REGA, se ten animais (ES + 12 díxitos)", value=horta_codigo_rega
            ).classes("w-full")

            def gardar_horta() -> None:
                if not nome_horta_input.value:
                    ui.notify("O nome é obrigatorio", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    horta_obxectivo = session.get(Horta, horta_id)
                    if horta_obxectivo is None:
                        ui.notify("Esta explotación xa non existe", type="negative")
                        return
                    gardado = executar_accion(
                        session,
                        lambda: actualizar_horta(
                            session,
                            actor_actual,
                            horta_obxectivo,
                            nome=nome_horta_input.value,
                            descricion=descricion_horta_input.value or None,
                            uso_profesional=tipo_radio.value,
                            titular_nome=titular_nome_input.value or None,
                            titular_nif=titular_nif_input.value or None,
                            codigo_reaga=reaga_input.value or None,
                            codigo_rega=rega_input.value or None,
                        ),
                    )
                if not gardado:
                    return
                ui.navigate.reload()

            def eliminar_horta_actual() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    horta_obxectivo = session.get(Horta, horta_id)
                    if horta_obxectivo is None:
                        ui.notify("Esta explotación xa non existe", type="negative")
                        return
                    eliminada = executar_accion(
                        session, lambda: eliminar_horta(session, actor_actual, horta_obxectivo)
                    )
                if not eliminada:
                    return
                ui.navigate.to("/")

            with ui.row().classes("w-full items-center justify-between"):
                with ui.row():
                    ui.button("Gardar", icon="check", on_click=gardar_horta)
                    ui.button("Cancelar", on_click=dialog_config_horta.close).props("flat")
                ui.button(
                    "Eliminar explotación",
                    icon="delete",
                    on_click=lambda: confirmar_eliminacion(
                        f"Eliminar «{horta_nome}» e TODAS as súas parcelas, animais e "
                        "membros? Esta acción non se pode desfacer.",
                        eliminar_horta_actual,
                    ),
                ).props("flat color=negative")

    if seccion == "membros" and not e_horta_admin:
        seccion = "resumo"
    etiquetas = {s.clave: s.etiqueta for s in SECCIONS}
    if seccion == "resumo":
        accions = cabeceira_seccion(horta_nome, horta_descricion or "Resumo da explotación")
        if e_horta_admin:
            with accions:
                ui.button(
                    "Configurar explotación", icon="settings", on_click=dialog_config_horta.open
                ).props("outline")
        texto_estado, clase_estado = {
            "rexistrada": ("Explotación rexistrada", "etiqueta-ok"),
            "en_preparacion": ("En preparación", "etiqueta-aviso"),
            "non_profesional": ("Non profesional", "etiqueta-ok"),
        }[estado]
        ui.label(texto_estado).classes(clase_estado)
        if requisitos:
            with ui.column().classes("tarxeta w-full gap-2 q-my-md"):
                ui.label("Para estar en regra").classes("text-subtitle1 text-weight-bold")
                for requisito in requisitos:
                    with ui.row().classes("items-center gap-2"):
                        if requisito.cumprido:
                            ui.icon("check_circle").classes("text-positive")
                        else:
                            ui.icon("radio_button_unchecked").classes("texto-suave")
                        ui.label(requisito.texto)
                        if not requisito.cumprido:
                            ui.label(requisito.axuda).classes("texto-suave text-caption")
        _seccion_dashboard(
            len(parcelas),
            len(cultivos),
            len(animais),
            n_tarefas_pendentes,
            tarefas_pendentes_hoxe,
            tarefas_proximas,
            tarefas_atrasadas,
        )
        return
    cabeceira_seccion(etiquetas[seccion], horta_nome)
    if seccion == "parcelas":
        _seccion_parcelas(horta_id, parcelas, pode_editar)
    elif seccion == "cultivos":
        _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
    elif seccion == "tratamentos":
        seccion_tratamentos_fito(horta_id, pode_editar)
    elif seccion == "fertilizacion":
        _seccion_fertilizacion(horta_id, fertilizacions, cultivos, parcelas, pode_editar)
    elif seccion == "tarefas":
        _seccion_tarefas(horta_id, tarefas, parcelas, cultivos, pode_editar)
    elif seccion == "animais":
        _seccion_animais(horta_id, animais, pode_editar)
    elif seccion == "persoas":
        seccion_persoas(horta_id, pode_editar)
    elif seccion == "maquinaria":
        seccion_maquinaria(horta_id, pode_editar)
    elif seccion == "membros":
        _seccion_membros(horta_id)


def _seccion_parcelas(horta_id: int, parcelas: list, pode_editar: bool) -> None:
    if pode_editar:
        with ui.dialog() as dialog_nova_parcela, ui.card():
            ui.label("Nova parcela").classes("text-md font-bold")
            nome_input = ui.input("Nome")
            superficie_input = CampoSuperficie("Superficie")
            lat_input = ui.number("Latitude", format="%.6f")
            lon_input = ui.number("Lonxitude", format="%.6f")

            def crear() -> None:
                if not nome_input.value:
                    ui.notify("O nome é obrigatorio", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creada = executar_accion(
                        session,
                        lambda: crear_parcela(
                            session,
                            actor_actual,
                            horta_id,
                            nome_input.value,
                            superficie=superficie_input.ha,
                            lat=lat_input.value,
                            lon=lon_input.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_parcela.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        if pode_editar:
            ui.button("Nova parcela", icon="add", on_click=dialog_nova_parcela.open)

    todas_as_filas = [
        {
            "id": p.id,
            "nome": p.nome,
            "superficie": formatar_superficie(p.superficie),
            "superficie_ha": p.superficie,
            "estado": p.estado,
            "lat": p.lat,
            "lon": p.lon,
        }
        for p in parcelas
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(
            ["Todos", *_ESTADOS_PARCELA], label="Estado", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "superficie", "label": "Superficie", "field": "superficie"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["nome", "superficie", "estado"],
            {"estado": estado_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar a parcela «{taboa.selected[0]['nome']}»? Isto tamén eliminará os "
                "cultivos, tratamentos e fertilizacións rexistrados nela. "
                "Non se pode desfacer.",
                eliminar_seleccionada,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar parcela").classes("text-md font-bold")
        nome_edit = ui.input("Nome")
        superficie_edit = CampoSuperficie("Superficie")
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")
        lat_edit = ui.number("Latitude", format="%.6f")
        lon_edit = ui.number("Lonxitude", format="%.6f")

        def gardar() -> None:
            if not taboa.selected:
                return
            parcela_id = taboa.selected[0]["id"]
            if not nome_edit.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        p
                        for p in listar_parcelas(session, actor_actual, horta_id)
                        if p.id == parcela_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Esa parcela xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_parcela(
                        session,
                        actor_actual,
                        obxectivo,
                        nome=nome_edit.value,
                        superficie=superficie_edit.ha,
                        estado=estado_edit.value,
                        lat=lat_edit.value,
                        lon=lon_edit.value,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        nome_edit.value = fila["nome"]
        superficie_edit.establecer(fila["superficie_ha"])
        estado_edit.value = fila["estado"]
        lat_edit.value = fila["lat"]
        lon_edit.value = fila["lon"]
        dialog_editar.open()

    def eliminar_seleccionada() -> None:
        if not taboa.selected:
            return
        parcela_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (p for p in listar_parcelas(session, actor_actual, horta_id) if p.id == parcela_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Esa parcela xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_parcela(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()


def _seccion_cultivos(horta_id: int, cultivos: list, parcelas: list, pode_editar: bool) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}

    if pode_editar:
        with ui.dialog() as dialog_novo_cultivo, ui.card():
            ui.label("Novo cultivo").classes("text-md font-bold")
            parcela_select = ui.select({p.id: p.nome for p in parcelas}, label="Parcela")
            especie_input = ui.input("Especie")
            variedade_input = ui.input("Variedade (opcional)")

            def crear() -> None:
                if not (parcela_select.value and especie_input.value):
                    ui.notify("Parcela e especie son obrigatorias", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creado = executar_accion(
                        session,
                        lambda: crear_cultivo(
                            session,
                            actor_actual,
                            parcela_select.value,
                            especie_input.value,
                            variedade=variedade_input.value or None,
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_cultivo.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        if pode_editar:
            ui.button("Novo cultivo", icon="add", on_click=dialog_novo_cultivo.open)

    todas_as_filas = [
        {
            "id": c.id,
            "parcela": parcelas_por_id.get(c.parcela_id, "?"),
            "especie": c.especie,
            "variedade": c.variedade or "",
            "estado": c.estado,
        }
        for c in cultivos
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(
            ["Todos", *_ESTADOS_CULTIVO], label="Estado", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "parcela", "label": "Parcela", "field": "parcela"},
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "variedade", "label": "Variedade", "field": "variedade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["parcela", "especie", "variedade", "estado"],
            {"estado": estado_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar o cultivo «{taboa.selected[0]['especie']}»? Isto tamén eliminará os "
                "seus tratamentos e fertilizacións rexistrados. "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar cultivo").classes("text-md font-bold")
        especie_edit = ui.input("Especie")
        variedade_edit = ui.input("Variedade")
        cantidade_edit = ui.number("Cantidade")
        unidade_edit = ui.select(list(_UNIDADES_CULTIVO), label="Unidade")
        data_sementeira_edit = campo_data("Data sementeira")
        data_plantacion_edit = campo_data("Data plantación")
        data_colleita_prevista_edit = campo_data("Data colleita prevista")
        data_colleita_real_edit = campo_data("Data colleita real")
        notas_edit = ui.textarea("Notas")
        estado_edit = ui.select(list(_ESTADOS_CULTIVO), label="Estado", value="planificado")

        def _parsear_data(texto: str) -> Any:
            if not texto:
                return None
            try:
                return date.fromisoformat(texto)
            except ValueError as erro:
                raise ValueError(f"Data non válida: {texto!r} (usa o formato AAAA-MM-DD)") from erro

        def gardar() -> None:
            if not taboa.selected:
                return
            cultivo_id = taboa.selected[0]["id"]
            if not especie_edit.value:
                ui.notify("A especie é obrigatoria", type="negative")
                return
            try:
                cambios = dict(
                    especie=especie_edit.value,
                    variedade=variedade_edit.value or None,
                    cantidade=cantidade_edit.value,
                    unidade=unidade_edit.value,
                    data_sementeira=_parsear_data(data_sementeira_edit.value),
                    data_plantacion=_parsear_data(data_plantacion_edit.value),
                    data_colleita_prevista=_parsear_data(data_colleita_prevista_edit.value),
                    data_colleita_real=_parsear_data(data_colleita_real_edit.value),
                    notas=notas_edit.value or None,
                    estado=estado_edit.value,
                )
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        c
                        for c in listar_cultivos(session, actor_actual, horta_id)
                        if c.id == cultivo_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese cultivo xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session, lambda: actualizar_cultivo(session, actor_actual, obxectivo, **cambios)
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        cultivo_id = fila["id"]
        cultivo_completo = next((c for c in cultivos if c.id == cultivo_id), None)
        if cultivo_completo is None:
            return
        especie_edit.value = cultivo_completo.especie
        variedade_edit.value = cultivo_completo.variedade or ""
        cantidade_edit.value = cultivo_completo.cantidade
        unidade_edit.value = cultivo_completo.unidade
        data_sementeira_edit.value = (
            cultivo_completo.data_sementeira.isoformat() if cultivo_completo.data_sementeira else ""
        )
        data_plantacion_edit.value = (
            cultivo_completo.data_plantacion.isoformat() if cultivo_completo.data_plantacion else ""
        )
        data_colleita_prevista_edit.value = (
            cultivo_completo.data_colleita_prevista.isoformat()
            if cultivo_completo.data_colleita_prevista
            else ""
        )
        data_colleita_real_edit.value = (
            cultivo_completo.data_colleita_real.isoformat()
            if cultivo_completo.data_colleita_real
            else ""
        )
        notas_edit.value = cultivo_completo.notas or ""
        estado_edit.value = cultivo_completo.estado
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        cultivo_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (c for c in listar_cultivos(session, actor_actual, horta_id) if c.id == cultivo_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese cultivo xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_cultivo(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()


def _seccion_fertilizacion(
    horta_id: int, fertilizacions: list, cultivos: list, parcelas: list, pode_editar: bool
) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}
    etiquetas_cultivo = {
        c.id: f"{c.especie} — {parcelas_por_id.get(c.parcela_id, '?')}" for c in cultivos
    }

    def _parsear_data(texto: str) -> Any:
        if not texto:
            raise ValueError("A data é obrigatoria")
        try:
            return date.fromisoformat(texto)
        except ValueError as erro:
            raise ValueError(f"Data non válida: {texto!r} (usa o formato AAAA-MM-DD)") from erro

    if pode_editar:
        with ui.dialog() as dialog_nova_fertilizacion, ui.card():
            ui.label("Nova fertilización").classes("text-md font-bold")
            cultivo_select = ui.select(etiquetas_cultivo, label="Cultivo")
            data_input = campo_data("Data")
            tipo_select = ui.select(["emenda", "abonado_fondo", "cobertoira"], label="Tipo")
            produto_input = ui.input("Produto")

            def crear() -> None:
                if not (
                    cultivo_select.value
                    and data_input.value
                    and tipo_select.value
                    and produto_input.value
                ):
                    ui.notify("Cultivo, data, tipo e produto son obrigatorios", type="negative")
                    return
                try:
                    data_valor = _parsear_data(data_input.value)
                except ValueError as erro:
                    ui.notify(str(erro), type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creada = executar_accion(
                        session,
                        lambda: crear_fertilizacion(
                            session,
                            actor_actual,
                            cultivo_select.value,
                            data_valor,
                            tipo_select.value,
                            produto_input.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_fertilizacion.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        if pode_editar:
            ui.button("Nova fertilización", icon="add", on_click=dialog_nova_fertilizacion.open)

    todas_as_filas = [
        {
            "id": f.id,
            "cultivo": etiquetas_cultivo.get(f.cultivo_id, "?"),
            "data": f.data.isoformat(),
            "tipo": f.tipo,
            "produto": f.produto,
        }
        for f in fertilizacions
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        tipo_filtro_select = ui.select(
            ["Todos", "emenda", "abonado_fondo", "cobertoira"], label="Tipo", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
                {"name": "data", "label": "Data", "field": "data"},
                {"name": "tipo", "label": "Tipo", "field": "tipo"},
                {"name": "produto", "label": "Produto", "field": "produto"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        tipo_filtro = None if tipo_filtro_select.value == "Todos" else tipo_filtro_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["cultivo", "data", "tipo", "produto"],
            {"tipo": tipo_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    tipo_filtro_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar a fertilización de «{taboa.selected[0]['produto']}»? "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionada,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar fertilización").classes("text-md font-bold")
        data_edit = campo_data("Data")
        tipo_edit = ui.select(["emenda", "abonado_fondo", "cobertoira"], label="Tipo")
        produto_edit = ui.input("Produto")
        dose_edit = ui.input("Dose")
        superficie_edit = CampoSuperficie("Superficie")
        n_edit = ui.number("N (%)")
        p_edit = ui.number("P (%)")
        k_edit = ui.number("K (%)")
        carbono_organico_edit = ui.number("Carbono orgánico (%)")
        micronutrientes_edit = ui.input("Micronutrientes")
        asesoramento_edit = ui.input("Asesoramento recibido")
        notas_edit = ui.textarea("Notas")

        def gardar() -> None:
            if not taboa.selected:
                return
            fertilizacion_id = taboa.selected[0]["id"]
            if not (tipo_edit.value and produto_edit.value):
                ui.notify("Tipo e produto son obrigatorios", type="negative")
                return
            try:
                data_valor = _parsear_data(data_edit.value)
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        f
                        for f in listar_fertilizacions(session, actor_actual, horta_id)
                        if f.id == fertilizacion_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Esa fertilización xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_fertilizacion(
                        session,
                        actor_actual,
                        obxectivo,
                        data=data_valor,
                        tipo=tipo_edit.value,
                        produto=produto_edit.value,
                        dose=dose_edit.value or None,
                        superficie=superficie_edit.ha,
                        n=n_edit.value,
                        p=p_edit.value,
                        k=k_edit.value,
                        carbono_organico=carbono_organico_edit.value,
                        micronutrientes=micronutrientes_edit.value or None,
                        asesoramento_recibido=asesoramento_edit.value or None,
                        notas=notas_edit.value or None,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fertilizacion_id = taboa.selected[0]["id"]
        fertilizacion_completa = next((f for f in fertilizacions if f.id == fertilizacion_id), None)
        if fertilizacion_completa is None:
            return
        data_edit.value = fertilizacion_completa.data.isoformat()
        tipo_edit.value = fertilizacion_completa.tipo
        produto_edit.value = fertilizacion_completa.produto
        dose_edit.value = fertilizacion_completa.dose or ""
        superficie_edit.establecer(fertilizacion_completa.superficie)
        n_edit.value = fertilizacion_completa.n
        p_edit.value = fertilizacion_completa.p
        k_edit.value = fertilizacion_completa.k
        carbono_organico_edit.value = fertilizacion_completa.carbono_organico
        micronutrientes_edit.value = fertilizacion_completa.micronutrientes or ""
        asesoramento_edit.value = fertilizacion_completa.asesoramento_recibido or ""
        notas_edit.value = fertilizacion_completa.notas or ""
        dialog_editar.open()

    def eliminar_seleccionada() -> None:
        if not taboa.selected:
            return
        fertilizacion_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (
                    f
                    for f in listar_fertilizacions(session, actor_actual, horta_id)
                    if f.id == fertilizacion_id
                ),
                None,
            )
            if obxectivo is None:
                ui.notify("Esa fertilización xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_fertilizacion(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()


def _seccion_animais(horta_id: int, animais: list, pode_editar: bool) -> None:
    if pode_editar:
        with ui.dialog() as dialog_novo_animal, ui.card():
            ui.label("Novo animal").classes("text-md font-bold")
            especie_input = ui.input("Especie (p.ex. galiñas, coellos)")
            raza_input = ui.input("Raza (opcional)")
            cantidade_input = ui.number("Cantidade", value=1)

            def crear() -> None:
                if not especie_input.value:
                    ui.notify("A especie é obrigatoria", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creado = executar_accion(
                        session,
                        lambda: crear_animal(
                            session,
                            actor_actual,
                            horta_id,
                            especie_input.value,
                            date.today(),
                            raza=raza_input.value or None,
                            cantidade=int(cantidade_input.value or 1),
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_animal.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        if pode_editar:
            ui.button("Novo animal", icon="add", on_click=dialog_novo_animal.open)

    todas_as_filas = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
        }
        for a in animais
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(["Todos", *_ESTADOS_ANIMAL], label="Estado", value="Todos").props(
            "dense"
        )

    taboa = (
        ui.table(
            columns=[
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "raza", "label": "Raza", "field": "raza"},
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["especie", "raza", "cantidade", "estado"],
            {"estado": estado_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f'Eliminar "{taboa.selected[0]["especie"]}"? Esta acción non se pode desfacer.',
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar animal").classes("text-md font-bold")
        especie_edit = ui.input("Especie")
        raza_edit = ui.input("Raza")
        cantidade_edit = ui.number("Cantidade")
        estado_edit = ui.select(list(_ESTADOS_ANIMAL), label="Estado", value="activo")

        def gardar() -> None:
            if not taboa.selected:
                return
            animal_id = taboa.selected[0]["id"]
            if not especie_edit.value:
                ui.notify("A especie é obrigatoria", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        a
                        for a in listar_animais(session, actor_actual, horta_id)
                        if a.id == animal_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese animal xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_animal(
                        session,
                        actor_actual,
                        obxectivo,
                        especie=especie_edit.value,
                        raza=raza_edit.value or None,
                        cantidade=int(cantidade_edit.value or 1),
                        estado=estado_edit.value,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        especie_edit.value = fila["especie"]
        raza_edit.value = fila["raza"]
        cantidade_edit.value = fila["cantidade"]
        estado_edit.value = fila["estado"]
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        animal_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (a for a in listar_animais(session, actor_actual, horta_id) if a.id == animal_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese animal xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_animal(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()


def _seccion_membros(horta_id: int) -> None:
    with get_session() as session:
        membros_bd = session.query(HortaMembro).filter_by(horta_id=horta_id).all()
        filas = []
        for m in membros_bd:
            usuario_membro = session.get(Usuario, m.usuario_id)
            if usuario_membro is None:
                logger.warning(
                    "HortaMembro horta_id={} usuario_id={} referencia un usuario inexistente",
                    horta_id,
                    m.usuario_id,
                )
                continue
            filas.append(
                {
                    "usuario_id": m.usuario_id,
                    "nome": usuario_membro.nome,
                    "email": usuario_membro.email,
                    "rol": m.rol.value,
                }
            )

    with ui.dialog() as dialog_engadir, ui.card():
        ui.label("Engadir membro").classes("text-md font-bold")
        email_input = ui.input("Email do usuario")
        rol_input = ui.select(list(_ROLES_HORTA), value="lector", label="Rol")

        def engadir() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                usuario_obxectivo = (
                    session.query(Usuario)
                    .filter_by(email=normalizar_email(email_input.value or ""))
                    .one_or_none()
                )
                if usuario_obxectivo is None:
                    ui.notify("Non existe ningún usuario con ese email", type="negative")
                    return
                engadido = executar_accion(
                    session,
                    lambda: engadir_membro(
                        session,
                        actor_actual,
                        horta_id,
                        usuario_obxectivo,
                        RolHorta(rol_input.value),
                    ),
                )
            if not engadido:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Engadir", icon="check", on_click=engadir)
            ui.button("Cancelar", on_click=dialog_engadir.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        ui.button("Engadir membro", icon="person_add", on_click=dialog_engadir.open)

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        rol_select = ui.select(["Todos", *_ROLES_HORTA], label="Rol", value="Todos").props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
            ],
            rows=filas,
            row_key="usuario_id",
            selection="single",
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        rol_filtro = None if rol_select.value == "Todos" else rol_select.value
        taboa.rows = filtrar_filas(
            filas,
            busca_input.value or "",
            ["nome", "email", "rol"],
            {"rol": rol_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    rol_select.on_value_change(refrescar_taboa)

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Cambiar rol", icon="edit", on_click=lambda: abrir_cambiar_rol())
        ui.button(
            "Quitar da explotación",
            icon="person_remove",
            on_click=lambda: confirmar_eliminacion(
                f'Quitar a "{taboa.selected[0]["nome"]}" desta horta?',
                quitar,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_cambiar_rol, ui.card():
        ui.label("Cambiar rol do membro").classes("text-md font-bold")
        rol_edit = ui.select(list(_ROLES_HORTA), value="lector", label="Rol")

        def cambiar_rol() -> None:
            if not taboa.selected:
                return
            usuario_obxectivo_id = taboa.selected[0]["usuario_id"]
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                cambiado = executar_accion(
                    session,
                    lambda: cambiar_rol_membro(
                        session,
                        actor_actual,
                        horta_id,
                        usuario_obxectivo_id,
                        RolHorta(rol_edit.value),
                    ),
                )
            if not cambiado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=cambiar_rol)
            ui.button("Cancelar", on_click=dialog_cambiar_rol.close).props("flat")

    def abrir_cambiar_rol() -> None:
        if not taboa.selected:
            return
        rol_edit.value = taboa.selected[0]["rol"]
        dialog_cambiar_rol.open()

    def quitar() -> None:
        if not taboa.selected:
            return
        usuario_obxectivo_id = taboa.selected[0]["usuario_id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            quitouse_a_si_mesmo = usuario_obxectivo_id == actor_actual.id
            quitado = executar_accion(
                session,
                lambda: quitar_membro(session, actor_actual, horta_id, usuario_obxectivo_id),
            )
        if not quitado:
            return
        if quitouse_a_si_mesmo:
            ui.navigate.to("/")
        else:
            ui.navigate.reload()


def _seccion_dashboard(
    n_parcelas: int,
    n_cultivos: int,
    n_animais: int,
    n_tarefas_pendentes: int,
    tarefas_hoxe: list,
    tarefas_proximas: list,
    tarefas_atrasadas: list,
) -> None:
    with ui.row().classes("w-full q-gutter-md q-mb-md"):
        with ui.card().classes("items-center"):
            ui.label(str(n_parcelas)).classes("text-h4 font-bold")
            ui.label("Parcelas").classes("text-caption text-grey")
        with ui.card().classes("items-center"):
            ui.label(str(n_cultivos)).classes("text-h4 font-bold")
            ui.label("Cultivos").classes("text-caption text-grey")
        with ui.card().classes("items-center"):
            ui.label(str(n_animais)).classes("text-h4 font-bold")
            ui.label("Animais").classes("text-caption text-grey")
        with ui.card().classes("items-center"):
            ui.label(str(n_tarefas_pendentes)).classes("text-h4 font-bold")
            ui.label("Tarefas pendentes").classes("text-caption text-grey")

    if tarefas_atrasadas:
        ui.label(f"⚠ Tes {len(tarefas_atrasadas)} tarefa(s) atrasada(s)").classes(
            "text-negative text-bold q-mb-md"
        )

    with ui.row().classes("w-full q-gutter-md"):
        with ui.column().classes("col"):
            ui.label("Tarefas de hoxe").classes("text-md font-bold")
            if tarefas_hoxe:
                for tarefa in tarefas_hoxe:
                    ui.label(f"☐ {tarefa.descricion}").classes("text-body2")
            else:
                ui.label("Non hai tarefas para hoxe.").classes("text-caption text-grey")
        with ui.column().classes("col"):
            ui.label("Próximas actividades").classes("text-md font-bold")
            if tarefas_proximas:
                for tarefa in tarefas_proximas:
                    data_texto = tarefa.data.isoformat() if tarefa.data else "?"
                    ui.label(f"{data_texto} — {tarefa.descricion}").classes("text-body2")
            else:
                ui.label("Non hai próximas actividades.").classes("text-caption text-grey")


def _seccion_tarefas(
    horta_id: int, tarefas: list, parcelas: list, cultivos: list, pode_editar: bool
) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}
    cultivos_por_id = {c.id: c.especie for c in cultivos}
    opcions_parcela = {"": "(sen parcela)", **{p.id: p.nome for p in parcelas}}
    opcions_cultivo = {"": "(sen cultivo)", **{c.id: c.especie for c in cultivos}}

    def _parsear_data(texto: str) -> Any:
        if not texto:
            return None
        try:
            return date.fromisoformat(texto)
        except ValueError as erro:
            raise ValueError(f"Data non válida: {texto!r} (usa o formato AAAA-MM-DD)") from erro

    if pode_editar:
        with ui.dialog() as dialog_nova_tarefa, ui.card():
            ui.label("Nova tarefa").classes("text-md font-bold")
            descricion_input = ui.input("Descrición")
            parcela_select = ui.select(opcions_parcela, label="Parcela", value="")
            cultivo_select = ui.select(opcions_cultivo, label="Cultivo", value="")
            data_input = campo_data("Data (opcional)")
            prioridade_select = ui.select(
                list(_PRIORIDADES_TAREFA), label="Prioridade", value="media"
            )

            def crear() -> None:
                if not descricion_input.value:
                    ui.notify("A descrición é obrigatoria", type="negative")
                    return
                try:
                    data_valor = _parsear_data(data_input.value)
                except ValueError as erro:
                    ui.notify(str(erro), type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creada = executar_accion(
                        session,
                        lambda: crear_tarefa(
                            session,
                            actor_actual,
                            horta_id,
                            descricion_input.value,
                            parcela_id=parcela_select.value or None,
                            cultivo_id=cultivo_select.value or None,
                            data=data_valor,
                            prioridade=prioridade_select.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_tarefa.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        if pode_editar:
            ui.button("Nova tarefa", icon="add", on_click=dialog_nova_tarefa.open)

    todas_as_filas = [
        {
            "id": t.id,
            "descricion": t.descricion,
            "parcela": parcelas_por_id.get(t.parcela_id, "") if t.parcela_id else "",
            "cultivo": cultivos_por_id.get(t.cultivo_id, "") if t.cultivo_id else "",
            "data": t.data.isoformat() if t.data else "",
            "data_limite": t.data_limite.isoformat() if t.data_limite else "",
            "prioridade": t.prioridade,
            "estado": t.estado,
        }
        for t in tarefas
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(
            ["Todos", "pendente", "feito"], label="Estado", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "descricion", "label": "Descrición", "field": "descricion"},
                {"name": "parcela", "label": "Parcela", "field": "parcela"},
                {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
                {"name": "data", "label": "Data", "field": "data"},
                {"name": "data_limite", "label": "Data límite", "field": "data_limite"},
                {"name": "prioridade", "label": "Prioridade", "field": "prioridade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["descricion", "parcela", "cultivo", "prioridade"],
            {"estado": estado_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Marcar feita/pendente",
            icon="check_circle",
            on_click=lambda: alternar_estado(),
        ).props("outline")
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar a tarefa «{taboa.selected[0]['descricion']}»? "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionada,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar tarefa").classes("text-md font-bold")
        descricion_edit = ui.input("Descrición")
        parcela_edit = ui.select(opcions_parcela, label="Parcela")
        cultivo_edit = ui.select(opcions_cultivo, label="Cultivo")
        data_edit = campo_data("Data (opcional)")
        data_limite_edit = campo_data("Data límite (opcional)")
        prioridade_edit = ui.select(list(_PRIORIDADES_TAREFA), label="Prioridade")
        notas_edit = ui.textarea("Notas")

        def gardar() -> None:
            if not taboa.selected:
                return
            tarefa_id = taboa.selected[0]["id"]
            if not descricion_edit.value:
                ui.notify("A descrición é obrigatoria", type="negative")
                return
            try:
                data_valor = _parsear_data(data_edit.value)
                data_limite_valor = _parsear_data(data_limite_edit.value)
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        t
                        for t in listar_tarefas(session, actor_actual, horta_id)
                        if t.id == tarefa_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Esa tarefa xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_tarefa(
                        session,
                        actor_actual,
                        obxectivo,
                        descricion=descricion_edit.value,
                        parcela_id=parcela_edit.value or None,
                        cultivo_id=cultivo_edit.value or None,
                        data=data_valor,
                        data_limite=data_limite_valor,
                        prioridade=prioridade_edit.value,
                        notas=notas_edit.value or None,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        tarefa_id = taboa.selected[0]["id"]
        tarefa_completa = next((t for t in tarefas if t.id == tarefa_id), None)
        if tarefa_completa is None:
            return
        descricion_edit.value = tarefa_completa.descricion
        parcela_edit.value = tarefa_completa.parcela_id or ""
        cultivo_edit.value = tarefa_completa.cultivo_id or ""
        data_edit.value = tarefa_completa.data.isoformat() if tarefa_completa.data else ""
        data_limite_edit.value = (
            tarefa_completa.data_limite.isoformat() if tarefa_completa.data_limite else ""
        )
        prioridade_edit.value = tarefa_completa.prioridade
        notas_edit.value = tarefa_completa.notas or ""
        dialog_editar.open()

    def alternar_estado() -> None:
        if not taboa.selected:
            return
        tarefa_id = taboa.selected[0]["id"]
        tarefa_completa = next((t for t in tarefas if t.id == tarefa_id), None)
        if tarefa_completa is None:
            return
        accion = marcar_pendente if tarefa_completa.estado == "feito" else marcar_feita
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (t for t in listar_tarefas(session, actor_actual, horta_id) if t.id == tarefa_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Esa tarefa xa non existe", type="negative")
                return
            feito = executar_accion(session, lambda: accion(session, actor_actual, obxectivo))
        if not feito:
            return
        ui.navigate.reload()

    def eliminar_seleccionada() -> None:
        if not taboa.selected:
            return
        tarefa_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (t for t in listar_tarefas(session, actor_actual, horta_id) if t.id == tarefa_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Esa tarefa xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_tarefa(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()

from __future__ import annotations

from datetime import date
from typing import Any

from loguru import logger
from nicegui import ui

from horta.db import get_session
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    listar_cultivos,
)
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
    quitar_membro,
)
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.services.tratamentos import (
    actualizar_tratamento,
    crear_tratamento,
    eliminar_tratamento,
    listar_tratamentos,
)
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual

_PROPS_TABOA = 'dense no-data-label="Non hai rexistros"'

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_ESTADOS_PARCELA = ("activa", "inactiva")
_ESTADOS_ANIMAL = ("activo", "baixa")
_ROLES_HORTA = ("admin", "editor", "lector")

_ESTADOS_CULTIVO = ("planificado", "sementado", "plantado", "colleitado", "finalizado")
_UNIDADES_CULTIVO = ("kg", "unidades", "ducias", "mazos")


@ui.page("/hortas/{horta_id}")
def horta_detalle_page(horta_id: int) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
        except PermisoDenegadoError:
            cabeceira_paxina()
            ui.label("Non tes acceso a esta horta").classes("text-negative")
            return
        horta = session.get(Horta, horta_id)
        if horta is None:
            cabeceira_paxina()
            ui.label("Esta horta xa non existe").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        tratamentos = listar_tratamentos(session, actor, horta_id)
        fertilizacions = listar_fertilizacions(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA
        e_horta_admin = membro.rol == RolHorta.ADMIN
        e_admin_global = actor.rol == RolGlobal.ADMIN
        horta_nome = horta.nome
        horta_descricion = horta.descricion
        horta_uso_profesional = horta.uso_profesional

    cabeceira_paxina(titulo_horta=horta_nome, mostrar_admin=e_admin_global)

    if e_horta_admin:
        with ui.dialog() as dialog_config_horta, ui.card():
            ui.label("Configurar horta").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome)
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "")
            uso_profesional_checkbox = ui.checkbox("Uso profesional", value=horta_uso_profesional)

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
                        ui.notify("Esta horta xa non existe", type="negative")
                        return
                    gardado = executar_accion(
                        session,
                        lambda: actualizar_horta(
                            session,
                            actor_actual,
                            horta_obxectivo,
                            nome=nome_horta_input.value,
                            descricion=descricion_horta_input.value or None,
                            uso_profesional=uso_profesional_checkbox.value,
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
                        ui.notify("Esta horta xa non existe", type="negative")
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
                    "Eliminar horta",
                    icon="delete",
                    on_click=lambda: confirmar_eliminacion(
                        f"Eliminar «{horta_nome}» e TODAS as súas parcelas, animais e "
                        "membros? Esta acción non se pode desfacer.",
                        eliminar_horta_actual,
                    ),
                ).props("flat color=negative")

    with ui.row().classes("w-full items-center justify-between"):
        with ui.column().classes("gap-0"):
            ui.label(horta_nome).classes("text-2xl font-bold")
            if horta_descricion:
                ui.label(horta_descricion).classes("text-body2 text-grey")
        if e_horta_admin:
            ui.button("Configurar horta", icon="settings", on_click=dialog_config_horta.open).props(
                "outline"
            )

    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_cultivos = ui.tab("Cultivos")
        pestana_tratamentos = ui.tab("Tratamentos")
        pestana_fertilizacion = ui.tab("Fertilización")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_cultivos):
            _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_tratamentos):
            _seccion_tratamentos(horta_id, tratamentos, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_fertilizacion):
            _seccion_fertilizacion(horta_id, fertilizacions, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)


def _seccion_parcelas(horta_id: int, parcelas: list, pode_editar: bool) -> None:
    if pode_editar:
        with ui.dialog() as dialog_nova_parcela, ui.card():
            ui.label("Nova parcela").classes("text-md font-bold")
            nome_input = ui.input("Nome")
            superficie_input = ui.number("Superficie (m²)")

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
                            superficie=superficie_input.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_parcela.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Parcelas").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Nova parcela", icon="add", on_click=dialog_nova_parcela.open)

    todas_as_filas = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
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
        superficie_edit = ui.number("Superficie (m²)")
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")

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
                        superficie=superficie_edit.value,
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
        nome_edit.value = fila["nome"]
        superficie_edit.value = fila["superficie"]
        estado_edit.value = fila["estado"]
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


def _seccion_cultivos(
    horta_id: int, cultivos: list, parcelas: list, pode_editar: bool
) -> None:
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
        ui.label("Cultivos").classes("text-lg font-bold")
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
        data_sementeira_edit = ui.input("Data sementeira (AAAA-MM-DD)")
        data_plantacion_edit = ui.input("Data plantación (AAAA-MM-DD)")
        data_colleita_prevista_edit = ui.input("Data colleita prevista (AAAA-MM-DD)")
        data_colleita_real_edit = ui.input("Data colleita real (AAAA-MM-DD)")
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


def _seccion_tratamentos(
    horta_id: int, tratamentos: list, cultivos: list, parcelas: list, pode_editar: bool
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
        with ui.dialog() as dialog_novo_tratamento, ui.card():
            ui.label("Novo tratamento").classes("text-md font-bold")
            cultivo_select = ui.select(etiquetas_cultivo, label="Cultivo")
            data_input = ui.input("Data (AAAA-MM-DD)")
            praga_input = ui.input("Praga")
            produto_input = ui.input("Produto")
            aplicador_input = ui.input("Aplicador")

            def crear() -> None:
                if not (
                    cultivo_select.value
                    and data_input.value
                    and praga_input.value
                    and produto_input.value
                    and aplicador_input.value
                ):
                    ui.notify(
                        "Cultivo, data, praga, produto e aplicador son obrigatorios",
                        type="negative",
                    )
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
                    creado = executar_accion(
                        session,
                        lambda: crear_tratamento(
                            session,
                            actor_actual,
                            cultivo_select.value,
                            data_valor,
                            praga_input.value,
                            produto_input.value,
                            aplicador_input.value,
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_tratamento.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Tratamentos").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Novo tratamento", icon="add", on_click=dialog_novo_tratamento.open)

    todas_as_filas = [
        {
            "id": t.id,
            "cultivo": etiquetas_cultivo.get(t.cultivo_id, "?"),
            "data": t.data.isoformat(),
            "praga": t.praga,
            "produto": t.produto,
            "aplicador": t.aplicador,
        }
        for t in tratamentos
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")

    taboa = (
        ui.table(
            columns=[
                {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
                {"name": "data", "label": "Data", "field": "data"},
                {"name": "praga", "label": "Praga", "field": "praga"},
                {"name": "produto", "label": "Produto", "field": "produto"},
                {"name": "aplicador", "label": "Aplicador", "field": "aplicador"},
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
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["cultivo", "data", "praga", "produto", "aplicador"],
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar o tratamento de «{taboa.selected[0]['praga']}»? "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar tratamento").classes("text-md font-bold")
        data_edit = ui.input("Data (AAAA-MM-DD)")
        praga_edit = ui.input("Praga")
        produto_edit = ui.input("Produto")
        numero_rexistro_edit = ui.input("Nº de rexistro do produto")
        dose_edit = ui.input("Dose")
        superficie_edit = ui.number("Superficie tratada (m²)")
        eficacia_edit = ui.input("Valoración da eficacia")
        aplicador_edit = ui.input("Aplicador")
        equipo_aplicador_edit = ui.input("Equipo aplicador")
        persoas_asesoramento_edit = ui.input("Persoas de asesoramento")
        notas_edit = ui.textarea("Notas")

        def gardar() -> None:
            if not taboa.selected:
                return
            tratamento_id = taboa.selected[0]["id"]
            if not (praga_edit.value and produto_edit.value and aplicador_edit.value):
                ui.notify("Praga, produto e aplicador son obrigatorios", type="negative")
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
                        t
                        for t in listar_tratamentos(session, actor_actual, horta_id)
                        if t.id == tratamento_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese tratamento xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_tratamento(
                        session,
                        actor_actual,
                        obxectivo,
                        data=data_valor,
                        praga=praga_edit.value,
                        produto=produto_edit.value,
                        numero_rexistro_produto=numero_rexistro_edit.value or None,
                        dose=dose_edit.value or None,
                        superficie_tratada=superficie_edit.value,
                        eficacia=eficacia_edit.value or None,
                        aplicador=aplicador_edit.value,
                        equipo_aplicador=equipo_aplicador_edit.value or None,
                        persoas_asesoramento=persoas_asesoramento_edit.value or None,
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
        tratamento_id = taboa.selected[0]["id"]
        tratamento_completo = next((t for t in tratamentos if t.id == tratamento_id), None)
        if tratamento_completo is None:
            return
        data_edit.value = tratamento_completo.data.isoformat()
        praga_edit.value = tratamento_completo.praga
        produto_edit.value = tratamento_completo.produto
        numero_rexistro_edit.value = tratamento_completo.numero_rexistro_produto or ""
        dose_edit.value = tratamento_completo.dose or ""
        superficie_edit.value = tratamento_completo.superficie_tratada
        eficacia_edit.value = tratamento_completo.eficacia or ""
        aplicador_edit.value = tratamento_completo.aplicador
        equipo_aplicador_edit.value = tratamento_completo.equipo_aplicador or ""
        persoas_asesoramento_edit.value = tratamento_completo.persoas_asesoramento or ""
        notas_edit.value = tratamento_completo.notas or ""
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        tratamento_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (
                    t
                    for t in listar_tratamentos(session, actor_actual, horta_id)
                    if t.id == tratamento_id
                ),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese tratamento xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_tratamento(session, actor_actual, obxectivo)
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
            data_input = ui.input("Data (AAAA-MM-DD)")
            tipo_select = ui.select(
                ["emenda", "abonado_fondo", "cobertoira"], label="Tipo"
            )
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
        ui.label("Fertilización").classes("text-lg font-bold")
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
        data_edit = ui.input("Data (AAAA-MM-DD)")
        tipo_edit = ui.select(["emenda", "abonado_fondo", "cobertoira"], label="Tipo")
        produto_edit = ui.input("Produto")
        dose_edit = ui.input("Dose")
        superficie_edit = ui.number("Superficie (m²)")
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
                        superficie=superficie_edit.value,
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
        fertilizacion_completa = next(
            (f for f in fertilizacions if f.id == fertilizacion_id), None
        )
        if fertilizacion_completa is None:
            return
        data_edit.value = fertilizacion_completa.data.isoformat()
        tipo_edit.value = fertilizacion_completa.tipo
        produto_edit.value = fertilizacion_completa.produto
        dose_edit.value = fertilizacion_completa.dose or ""
        superficie_edit.value = fertilizacion_completa.superficie
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
        ui.label("Animais").classes("text-lg font-bold")
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
        estado_select = ui.select(
            ["Todos", *_ESTADOS_ANIMAL], label="Estado", value="Todos"
        ).props("dense")

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
        rol_input = ui.select(list(_ROLES_HORTA), value="lector")

        def engadir() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                usuario_obxectivo = (
                    session.query(Usuario).filter_by(email=email_input.value).one_or_none()
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
        ui.label("Membros").classes("text-lg font-bold")
        ui.button("Engadir membro", icon="person_add", on_click=dialog_engadir.open)

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        rol_select = ui.select(
            ["Todos", *_ROLES_HORTA], label="Rol", value="Todos"
        ).props("dense")

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
            "Quitar da horta",
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
        rol_edit = ui.select(list(_ROLES_HORTA), value="lector")

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

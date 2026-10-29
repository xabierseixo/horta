"""Sección Coidados dos animais: coidados, enfermidades, cambios na produción, medicamentos e
visitas de cada grupo de animais (libro de rexistro gandeiro e medicamentos). Baixa lóxica."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.tarefa import Tarefa
from horta.services.animais import listar_animais
from horta.services.catalogos import valores_vixentes
from horta.services.coidados_animais import (
    CON_ANIMAIS,
    TIPOS_COIDADO,
    DatosCoidado,
    actualizar_coidado,
    crear_coidado,
    dar_de_baixa_coidado,
    fin_tempo_espera,
    listar_coidados,
)
from horta.services.diario import nome_grupo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas, listar_quen
from horta.services.produtos import listar_produtos
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campo_produto import CampoProduto, opcions_entradas
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def _enteiro(texto: str | None) -> int | None:
    valor = parsear_decimal(texto)
    return int(valor) if valor is not None else None


def seccion_coidados(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        coidados = listar_coidados(session, actor, horta_id)
        grupos = {a.id: nome_grupo(a.especie, a.raza)
                  for a in listar_animais(session, actor, horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}
        medicamentos = {p.id: p.nome for p in listar_produtos(
            session, actor, horta_id, tipo="medicamento", so_activos=False)}

    filas = []
    for co in coidados:
        fin = fin_tempo_espera(co)
        filas.append({
            "id": co.id,
            "data": f"{co.data_inicio:%d/%m/%Y}",
            "grupo": grupos.get(co.animal_id, ""),
            "que": TIPOS_COIDADO[co.tipo].split(" (")[0],
            "detalle": medicamentos.get(co.produto_id or 0) or persoas.get(co.visitante_id or 0)
            or co.descricion
            or "",
            "quen": persoas.get(co.persoa_id, "") if co.persoa_id else "",
            "espera": f"{fin:%d/%m/%Y}" if fin else "",
        })
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("grupo", "Animais"), ("que", "Que"), ("detalle", "Detalle"),
            ("quen", "Quen"), ("espera", "Tempo de espera ata"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai coidados apuntados" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_coidado(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        with get_session() as session:
            co = session.get(CoidadoAnimal, taboa.selected[0]["id"])
            if co is not None:
                abrir(co)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        coidado_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                co = session.get(CoidadoAnimal, coidado_id)
                if actor_actual is None or co is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_coidado(
                    session, actor_actual, co))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este rexistro? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar coidado", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_coidado(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar un coidado e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_: None
        animais = listar_animais(session, actor, horta_id)
        todos = {a.id: f"{nome_grupo(a.especie, a.raza)} · {a.cantidade}" for a in animais}
        de_alta = {a.id: todos[a.id] for a in animais if a.estado == "activo"}
        unidades = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar coidado de animais").classes("text-h6")
        if not todos:
            ui.label("Primeiro engade os animais en Explotación → Animais.").classes(
                "text-warning text-caption")
        grupo = ui.select(de_alta, label="Animais", with_input=True).classes("w-full")
        tipo = ui.select(TIPOS_COIDADO, label="Tipo", value="coidado").classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        descricion = ui.input("Que se fixo").classes("w-full")
        visitante = CampoPersoa(horta_id, None, "Quen veu (persoa ou empresa)")
        medicamento = CampoProduto(horta_id, "medicamento", "Medicamento")
        with ui.row().classes("w-full no-wrap") as fila_dose:
            cantidade = ui.input("Cantidade").classes("col")
            unidade = ui.select(unidades, label="Unidade", with_input=True,
                                clearable=True).classes("col")
        with ui.row().classes("w-full no-wrap") as fila_dias:
            tempo_espera = ui.input("Tempo de espera (días, 0 se non ten)").classes("col")
            duracion = ui.input("Duración (días)").classes("col")
        with ui.row().classes("w-full no-wrap") as fila_animais:
            num_animais = ui.input("Cantos animais").classes("col")
            identificacion = ui.input("Identificación (se a teñen)").classes("col")
        with ui.column().classes("w-full gap-0") as datos_medicamento:
            veterinario = CampoPersoa(horta_id, "veterinario", "Veterinario que o receitou")
            receita = ui.input("Nº de receita").classes("w-full")
            # Onde se mercou e a proba de compra: na compra (entrada) do medicamento
            compra = ui.select({}, label="De que compra (onde se mercou)", clearable=True
                               ).classes("w-full")
        matricula = ui.input("Matrícula do vehículo").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def cambiar_compras() -> None:
            compra.set_options(opcions_entradas(horta_id, medicamento.value)
                               if medicamento.value else {}, value=None)

        medicamento.select.on_value_change(cambiar_compras)

        def mostrar_campos() -> None:
            e_medicamento = tipo.value == "medicamento"
            e_visita = tipo.value == "visita"
            descricion.label = {"enfermidade": "Que se viu", "producion": "Que cambiou",
                                "visita": "Para que veu"}.get(tipo.value, "Que se fixo")
            descricion.set_visibility(not e_medicamento)
            visitante.set_visibility(e_visita)
            matricula.set_visibility(e_visita)
            for elemento in (medicamento, fila_dose, fila_dias, datos_medicamento):
                elemento.set_visibility(e_medicamento)
            fila_animais.set_visibility(tipo.value in CON_ANIMAIS)

        tipo.on_value_change(mostrar_campos)

        def gardar() -> None:
            if grupo.value is None or tipo.value is None:
                ui.notify("Escolle os animais e que se fixo", type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    inicio = parsear_data(data_inicio.value)
                    if inicio is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    datos = DatosCoidado(
                        animal_id=grupo.value, data_inicio=inicio, tipo=tipo.value,
                        persoa_id=persoa.value, descricion=descricion.value or None,
                        data_fin=parsear_data(data_fin.value),
                        num_animais=_enteiro(num_animais.value),
                        identificacion=identificacion.value or None,
                        produto_id=medicamento.value, entrada_id=compra.value,
                        cantidade=parsear_decimal(cantidade.value), unidade=unidade.value,
                        veterinario_id=veterinario.value, receita=receita.value or None,
                        tempo_espera_dias=_enteiro(tempo_espera.value),
                        duracion_dias=_enteiro(duracion.value),
                        visitante_id=visitante.value, matricula=matricula.value or None,
                        horas=parsear_decimal(horas.value), maquina_id=maquina.value,
                        notas=notas.value or None)
                    existente = (session.get(CoidadoAnimal, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_coidado(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_coidado(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(co: CoidadoAnimal | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = co.id if co else None
        titulo.text = "Editar coidado de animais" if co else "Apuntar coidado de animais"
        # Ao editar, o grupo pode estar xa de baixa: tamén se ofrece
        opcions = dict(de_alta)
        if co is not None and co.animal_id in todos:
            opcions[co.animal_id] = todos[co.animal_id]
        grupo.set_options(opcions)
        animal_tarefa = tarefa.animal_id if tarefa and tarefa.animal_id in de_alta else None
        grupo.value = co.animal_id if co else animal_tarefa
        tipo.value = co.tipo if co else "coidado"
        data_inicio.value = (co.data_inicio if co else date.today()).isoformat()
        data_fin.value = (co.data_fin.isoformat()
                          if co and co.data_fin != co.data_inicio else "")
        persoa.value = (co.persoa_id if co.persoa_id in persoas else None) if co else (
            proposta_quen(horta_id, tarefa))
        descricion.value = (co.descricion or "") if co else (tarefa.descricion if tarefa else "")
        visitante.value = co.visitante_id if co else None
        medicamento.value = co.produto_id if co else None
        cambiar_compras()
        compra.value = co.entrada_id if co and co.entrada_id in compra.options else None
        cantidade.value = f"{co.cantidade:g}" if co and co.cantidade else ""
        unidade.value = co.unidade if co and co.unidade in unidades else None
        tempo_espera.value = (str(co.tempo_espera_dias)
                              if co and co.tempo_espera_dias is not None else "")
        duracion.value = str(co.duracion_dias) if co and co.duracion_dias else ""
        num_animais.value = str(co.num_animais) if co and co.num_animais else ""
        identificacion.value = (co.identificacion or "") if co else ""
        veterinario.value = co.veterinario_id if co else None
        receita.value = (co.receita or "") if co else ""
        matricula.value = (co.matricula or "") if co else ""
        horas.value = f"{co.horas:g}" if co and co.horas else ""
        maquina.value = co.maquina_id if co and co.maquina_id in maquinas else None
        notas.value = (co.notas or "") if co else ""
        mostrar_campos()
        dialogo.open()

    return abrir

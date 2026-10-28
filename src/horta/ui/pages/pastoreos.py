"""Sección Pastoreo (CUE bloque 12): o gando nas leiras, propio ou doutra persoa. Baixa
lóxica."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.parcela import Parcela
from horta.models.pastoreo import Pastoreo
from horta.models.tarefa import Tarefa
from horta.services.animais import ESPECIES, listar_animais
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.diario import nome_grupo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.pastoreos import (
    NON_PASTAN,
    AnimaisPastoreo,
    DatosPastoreo,
    LeiraPastoreo,
    actualizar_pastoreo,
    animais_no_dia,
    aviso_prazo_pastoreo,
    crear_pastoreo,
    dar_de_baixa_pastoreo,
    listar_pastoreos,
    nomes_leiras,
    sairon_do_pasto,
)
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_pastoreo(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        grupos = {a.id: nome_grupo(a.especie, a.raza)
                  for a in listar_animais(session, actor, horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}
        filas = [{
            "id": pa.id,
            "inicio": f"{pa.data_inicio:%d/%m/%Y}",
            "fin": f"{pa.data_fin:%d/%m/%Y}" if pa.data_fin else "Aínda no pasto",
            "leiras": nomes_leiras(session, pa),
            "animais": ", ".join(
                f"{li.numero} {grupos.get(li.animal_id, '')}" if li.animal_id
                else f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} ({li.rega})"
                for li in pa.animais),
            "quen": persoas.get(pa.persoa_id, "") if pa.persoa_id else "",
        } for pa in listar_pastoreos(session, actor, horta_id)]

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("inicio", "Entrou"), ("fin", "Saíu"), ("leiras", "Leiras"),
            ("animais", "Animais"), ("quen", "Quen"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai pastoreo apuntado" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_pastoreo(horta_id)
    abrir_saida = dialogo_saida()

    def escollido() -> int | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return None
        return int(taboa.selected[0]["id"])

    def editar() -> None:
        pastoreo_id = escollido()
        if pastoreo_id is None:
            return
        with get_session() as session:
            pa = session.get(Pastoreo, pastoreo_id)
            if pa is not None:
                abrir(pa)

    def saida() -> None:
        pastoreo_id = escollido()
        if pastoreo_id is not None:
            abrir_saida(pastoreo_id)

    def dar_de_baixa() -> None:
        pastoreo_id = escollido()
        if pastoreo_id is None:
            return

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                pa = session.get(Pastoreo, pastoreo_id)
                if actor_actual is None or pa is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_pastoreo(
                    session, actor_actual, pa))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este rexistro? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar pastoreo", icon="add", on_click=lambda: abrir(None))
        ui.button("Saíron do pasto", icon="logout", on_click=saida).props("outline")
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_saida() -> Callable[[int], None]:
    """Diálogo que só pide o día en que o gando saíu do pasto. Devolve abrir(pastoreo_id)."""
    escollido: dict[str, int | None] = {"id": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(24rem, 94vw)"):
        ui.label("Saíron do pasto").classes("text-h6")
        data_fin = campo_data("Día en que saíron", date.today().isoformat())

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                pa = session.get(Pastoreo, escollido["id"]) if escollido["id"] else None
                if actor_actual is None or pa is None:
                    return

                def accion() -> None:
                    fin = parsear_data(data_fin.value)
                    if fin is None:
                        raise OperacionNonPermitidaError("Indica o día en que saíron")
                    sairon_do_pasto(session, actor_actual, pa, fin)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(pastoreo_id: int) -> None:
        escollido["id"] = pastoreo_id
        data_fin.value = date.today().isoformat()
        dialogo.open()

    return abrir


def dialogo_pastoreo(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar un pastoreo e devolve a función que o abre:
    abrir(pastoreo, tarefa=None, animal_id=None). O formulario leva un grupo propio e, se
    se quere, animais doutra persoa."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        grupos = {a.id: nome_grupo(a.especie, a.raza)
                  for a in listar_animais(session, actor, horta_id)
                  if a.especie_codigo not in NON_PASTAN}
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        leiras = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                  for c in listar_cultivos(session, actor, horta_id)}
        coberturas = {v.codigo: v.descricion
                      for v in valores_vixentes(session, "tipo_cobertura_solo")}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
    especies = {k: v for k, v in ESPECIES.items() if k not in NON_PASTAN}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}
    gardadas: dict[int, LeiraPastoreo] = {}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar pastoreo").classes("text-h6")
        if not leiras:
            ui.label("Primeiro engade as leiras e os seus cultivos.").classes(
                "text-warning text-caption")
        leira = ui.select(leiras, label="Leiras", multiple=True, with_input=True).props(
            "use-chips").classes("w-full")
        aviso = ui.label("").classes("etiqueta-aviso")
        with ui.row().classes("w-full no-wrap"):
            data = campo_data("Entraron o", date.today().isoformat()).classes(
                remove="w-full", add="col")
            data_fin = campo_data("Saíron o", "").classes(
                remove="w-full", add="col")
        with ui.row().classes("w-full no-wrap"):
            grupo = ui.select(grupos, label="Os teus animais", with_input=True,
                              clearable=True).classes("col")
            numero = ui.input("Cantos").classes("col")
        terceiros = ui.checkbox("Tamén animais doutra persoa")
        with ui.column().classes("w-full") as caixa_terceiros:
            with ui.row().classes("w-full no-wrap"):
                especie = ui.select(especies, label="Especie").classes("col")
                numero_terceiros = ui.input("Cantos").classes("col")
            rega = ui.input("REGA da súa explotación").classes("w-full")
        caixa_terceiros.bind_visibility_from(terceiros, "value")
        persoa = ui.select(persoas, label="Quen levou o gando").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            superficie = ui.input("Superficie pastada (ha), se foi só unha parte").classes(
                "w-full")
            cobertura = ui.select(coberturas, label="Cobertura do chan", clearable=True).classes(
                "w-full")
            horas = ui.input("Horas de traballo").classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def avisar() -> None:
            texto = None
            try:
                inicio = parsear_data(data.value)
            except ValueError:
                inicio = None
            if leira.value and inicio is not None:
                with get_session() as session:
                    texto = aviso_prazo_pastoreo(session, list(leira.value), inicio)
            aviso.text = texto or ""
            aviso.set_visibility(bool(texto))

        def cantos_ten() -> None:
            if editando["id"] is not None or grupo.value is None:
                return
            try:
                dia = parsear_data(data.value) or date.today()
            except ValueError:
                dia = date.today()
            with get_session() as session:
                numero.value = str(animais_no_dia(session, grupo.value, dia))

        def unha_leira() -> None:
            superficie.set_enabled(len(leira.value or []) == 1)
            avisar()

        leira.on_value_change(unha_leira)
        data.on_value_change(avisar)
        grupo.on_value_change(cantos_ten)

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    inicio = parsear_data(data.value)
                    if inicio is None:
                        raise OperacionNonPermitidaError("Indica cando entraron")
                    escollidas = list(leira.value or [])
                    sup = parsear_decimal(superficie.value) if len(escollidas) == 1 else None
                    lista_leiras = [LeiraPastoreo(
                        cultivo_id=c,
                        superficie_ha=sup if sup is not None else (
                            gardadas[c].superficie_ha if c in gardadas else None),
                        tipo_cobertura=cobertura.value or (
                            gardadas[c].tipo_cobertura if c in gardadas else None))
                        for c in escollidas]
                    animais = []
                    if grupo.value is not None:
                        cantos = parsear_decimal(numero.value)
                        animais.append(AnimaisPastoreo(
                            numero=int(cantos) if cantos is not None else 0,
                            animal_id=grupo.value))
                    if terceiros.value:
                        cantos = parsear_decimal(numero_terceiros.value)
                        animais.append(AnimaisPastoreo(
                            numero=int(cantos) if cantos is not None else 0,
                            rega=rega.value or None, especie_codigo=especie.value))
                    datos = DatosPastoreo(
                        horta_id=horta_id, data_inicio=inicio,
                        data_fin=parsear_data(data_fin.value), persoa_id=persoa.value,
                        leiras=lista_leiras, animais=animais,
                        horas=parsear_decimal(horas.value), notas=notas.value or None)
                    existente = (session.get(Pastoreo, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_pastoreo(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_pastoreo(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(pa: Pastoreo | None, tarefa: Tarefa | None = None,
              animal_id: int | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = None
        titulo.text = "Editar pastoreo" if pa else "Apuntar pastoreo"
        gardadas.clear()
        propio = next((li for li in pa.animais if li.animal_id), None) if pa else None
        alleo = next((li for li in pa.animais if li.animal_id is None), None) if pa else None
        if pa:
            gardadas.update({le.cultivo_id: LeiraPastoreo(le.cultivo_id, le.superficie_ha,
                                                          le.tipo_cobertura)
                             for le in pa.leiras})
            leira.value = [le.cultivo_id for le in pa.leiras if le.cultivo_id in leiras]
        elif tarefa and tarefa.cultivo_id in leiras:
            leira.value = [tarefa.cultivo_id]
        else:
            leira.value = []
        data.value = (pa.data_inicio if pa else date.today()).isoformat()
        data_fin.value = pa.data_fin.isoformat() if pa and pa.data_fin else ""
        animal_tarefa = tarefa.animal_id if tarefa and tarefa.animal_id in grupos else None
        grupo.value = (propio.animal_id if propio else None) if pa else (
            animal_id if animal_id in grupos else animal_tarefa)
        cantos_ten()
        if propio:
            numero.value = str(propio.numero)
        elif pa:
            numero.value = ""
        terceiros.value = alleo is not None
        especie.value = alleo.especie_codigo if alleo else None
        numero_terceiros.value = str(alleo.numero) if alleo else ""
        rega.value = (alleo.rega or "") if alleo else ""
        superficie.value = (f"{pa.leiras[0].superficie_ha:g}"
                            if pa and len(pa.leiras) == 1 and pa.leiras[0].superficie_ha
                            else "")
        cobertura.value = None
        persoa.value = (pa.persoa_id if pa.persoa_id in persoas else None) if pa else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{pa.horas:g}" if pa and pa.horas else ""
        notas.value = (pa.notas or "") if pa else ""
        editando["id"] = pa.id if pa else None
        unha_leira()
        dialogo.open()

    return abrir

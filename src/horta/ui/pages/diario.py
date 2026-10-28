"""Diario de traballos: todo o feito e o por facer nunha lista, e «Apuntar traballo»
(primeiro que se fixo, despois o formulario dese tipo)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from functools import partial

from nicegui import ui

from horta.db import Base, get_session
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.labor import Labor
from horta.models.movemento_animal import MovementoAnimal
from horta.models.parcela import Parcela
from horta.models.pastoreo import Pastoreo
from horta.models.producion_animal import ProducionAnimal
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.services.diario import TIPOS, Traballo, listar_traballos
from horta.services.persoas import listar_persoas
from horta.ui.campos import campo_data
from horta.ui.dialogo_tarefa import dialogo_nova_tarefa
from horta.ui.facer_tarefa import dialogo_tarefa_feita
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data
from horta.ui.pages.abonados import dialogo_abonado
from horta.ui.pages.analises import dialogo_analise
from horta.ui.pages.coidados_animais import dialogo_coidado
from horta.ui.pages.colleitas import dialogo_colleita
from horta.ui.pages.cultivos import dialogo_cultivo
from horta.ui.pages.labores import dialogo_labor
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.pages.pastoreos import dialogo_pastoreo
from horta.ui.pages.producions_animais import dialogo_producion
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets",
    "movemento_animal": "swap_horiz", "producion_animal": "egg", "pastoreo": "landscape",
    "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "producion_animal": "producion", "pastoreo": "pastoreo",
    "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
    "pastoreo": Pastoreo,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
    "producion_animal": dialogo_producion, "pastoreo": dialogo_pastoreo,
}
_DIAS_POR_DEFECTO = 90


class Formularios:
    """Os formularios de cada tipo de traballo. Constrúense a primeira vez que se usan."""

    def __init__(self, horta_id: int) -> None:
        self.horta_id = horta_id
        self._contedor = ui.element("div")
        self._abrir: dict[str, Callable[..., None]] = {}

    def _abridor(self, tipo: str) -> Callable[..., None]:
        if tipo not in self._abrir:
            with self._contedor:
                if tipo == "tarefa":
                    abrir_tarefa = dialogo_nova_tarefa(self.horta_id)
                    self._abrir[tipo] = lambda _: abrir_tarefa()
                elif tipo == "tarefa_feita":
                    self._abrir[tipo] = dialogo_tarefa_feita(self.horta_id)
                else:
                    self._abrir[tipo] = _CONSTRUTORES[tipo](self.horta_id)
        return self._abrir[tipo]

    def novo(self, tipo: str) -> None:
        self._abridor(tipo)(None)

    def facer(self, tarefa: Tarefa) -> None:
        """Facer unha tarefa: o formulario do seu tipo xa enchido ou, sen tipo, quen a fixo."""
        if tarefa.tipo:
            self._abridor(tarefa.tipo)(None, tarefa)
        else:
            self._abridor("tarefa_feita")(tarefa)

    def _escoller(self, tarefa: Tarefa) -> None:
        with self._contedor, ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
            ui.label(tarefa.descricion).classes("text-h6")

            def facela() -> None:
                dialogo.close()
                self.facer(tarefa)

            with ui.row():
                ui.button("Facela agora", icon="check", on_click=facela)
                ui.button("Editar a tarefa", icon="edit", on_click=lambda: ui.navigate.to(
                    url_seccion(self.horta_id, "tarefas"))).props("flat")
        dialogo.open()

    def editar(self, traballo: Traballo) -> None:
        if traballo.tipo == "tarefa":
            with get_session() as session:
                tarefa = session.get(Tarefa, traballo.id)
            if tarefa is not None and not traballo.feito:
                self._escoller(tarefa)
            else:
                ui.navigate.to(url_seccion(self.horta_id, "tarefas"))
            return
        abrir = self._abridor(traballo.tipo)
        with get_session() as session:
            rexistro = session.get(_MODELOS[traballo.tipo], traballo.id)
            if rexistro is not None:
                abrir(rexistro)


def boton_apuntar_traballo(formularios: Formularios) -> None:
    """Botón «Apuntar traballo» e, no móbil, o mesmo botón sempre á vista abaixo."""
    with ui.dialog() as escoller, ui.card().style("width: min(34rem, 94vw)"):
        ui.label("Que fixeches?").classes("text-h6")
        with ui.grid().classes("w-full grid-cols-2 sm:grid-cols-3 gap-2"):
            for tipo, etiqueta in TIPOS.items():
                texto = "Tarefa por facer" if tipo == "tarefa" else etiqueta

                def escollido(tipo: str = tipo) -> None:
                    escoller.close()
                    formularios.novo(tipo)

                ui.button(texto, icon=ICONAS[tipo], on_click=escollido).props(
                    "outline stack").classes("w-full")
        ui.button("Cancelar", on_click=escoller.close).props("flat")
    ui.button("Apuntar traballo", icon="add", on_click=escoller.open)
    with ui.page_sticky(position="bottom-right", x_offset=16, y_offset=16).classes("lt-md"):
        ui.button(icon="add", on_click=escoller.open).props(
            'fab color=primary aria-label="Apuntar traballo"')


def _data(t: Traballo) -> str:
    return f"{t.data:%d/%m/%Y}" if t.data else "sen data"


def _tarxeta(t: Traballo, ao_premer: Callable[[], None], nomes: dict[int, str]) -> None:
    with ui.row().classes("tarxeta w-full items-center no-wrap gap-3 cursor-pointer q-pa-sm").on(
            "click", ao_premer):
        ui.icon(ICONAS[t.tipo]).classes("text-h5 text-primary")
        with ui.column().classes("gap-0 col"):
            ui.label(TIPOS[t.tipo] + (f": {t.que}" if t.que else "")).classes(
                "text-weight-bold")
            quen = ", ".join(nomes.get(p, "") for p in t.persoas)
            if t.onde or quen:
                ui.label(" · ".join(x for x in (t.onde, quen) if x)).classes(
                    "texto-suave text-caption")
        with ui.column().classes("items-end gap-0"):
            ui.label(_data(t)).classes("text-caption")
            if t.atrasado:
                ui.label("atrasada").classes("etiqueta-aviso")


def seccion_diario(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}

    formularios = Formularios(horta_id) if pode_editar else None
    if formularios is not None:
        with ui.row().classes("q-mb-md"):
            boton_apuntar_traballo(formularios)

    hoxe = date.today()
    with ui.row().classes("w-full items-end gap-2 wrap q-mb-md"):
        tipo = ui.select({"": "Todos os traballos", **TIPOS}, value="", label="Tipo").classes(
            "w-56")
        parcela = ui.select({0: "Todas", **parcelas}, value=0, label="Parcela").classes("w-48")
        quen = ui.select({0: "Todas", **persoas}, value=0, label="Quen").classes("w-48")
        estado = ui.select({"": "Feitos e por facer", "por_facer": "Por facer",
                            "feito": "Feitos"}, value="", label="Estado").classes("w-48")
        desde = campo_data("Desde", (hoxe - timedelta(days=_DIAS_POR_DEFECTO)).isoformat()
                           ).classes(remove="w-full", add="w-40")
        ata = campo_data("Ata", hoxe.isoformat()).classes(remove="w-full", add="w-40")

    @ui.refreshable
    def lista() -> None:
        if tipo.value:
            ui.link(f"Ver a táboa de «{TIPOS[tipo.value]}» con todos os seus datos",
                    url_seccion(horta_id, SECCION_DO_TIPO[tipo.value]))
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                return
            try:
                inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
            except ValueError:
                inicio = fin = None
            traballos = listar_traballos(session, actor_actual, horta_id, inicio, fin)
        traballos = [
            t for t in traballos
            if (not tipo.value or t.tipo == tipo.value)
            and (not parcela.value or parcela.value in t.parcelas)
            and (not quen.value or quen.value in t.persoas)
            and (not estado.value or t.feito == (estado.value == "feito"))
        ]
        if not traballos:
            ui.label("Non hai traballos con estes filtros.").classes("texto-suave")
        por_facer = [t for t in traballos if not t.feito]
        feitos = [t for t in traballos if t.feito]
        for titulo, grupo in (("Por facer", por_facer), ("Feito", feitos)):
            if not grupo:
                continue
            ui.label(titulo).classes("text-subtitle1 text-weight-bold q-mt-md")
            with ui.column().classes("w-full gap-2"):
                for t in grupo:
                    if formularios is not None:
                        _tarxeta(t, partial(formularios.editar, t), persoas)
                    else:
                        _tarxeta(t, partial(ui.navigate.to,
                                            url_seccion(horta_id, SECCION_DO_TIPO[t.tipo])),
                                 persoas)

    for filtro in (tipo, parcela, quen, estado, desde, ata):
        filtro.on_value_change(lista.refresh)
    lista()

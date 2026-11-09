"""Diario de traballos: todo o feito e o por facer nunha lista, e «Apuntar traballo»
(primeiro que se fixo, despois o formulario dese tipo)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from functools import partial

from nicegui import ui

from horta.db import Base, get_session
from horta.idiomas import N_, _
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.esterco import MovementoEsterco
from horta.models.labor import Labor
from horta.models.lote import Clasificacion, LoteSaida, Mestura, Transformacion
from horta.models.movemento_animal import MovementoAnimal
from horta.models.observacion import ObservacionPraga
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela
from horta.models.pastoreo import Pastoreo
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.services.diario import TIPOS, Traballo, listar_traballos, tipos_para_apuntar
from horta.services.envio_cue import estado_cue
from horta.services.fotos import contar_fotos
from horta.services.persoas import listar_persoas
from horta.ui.campos import campo_data
from horta.ui.dialogo_tarefa import dialogo_nova_tarefa
from horta.ui.facer_tarefa import dialogo_tarefa_feita
from horta.ui.fotos import boton_fotos
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data
from horta.ui.pages.abonados import dialogo_abonado
from horta.ui.pages.analises import dialogo_analise
from horta.ui.pages.clasificacions import (
    dialogo_clasificacion,
    dialogo_mestura,
    dialogo_transformacion,
)
from horta.ui.pages.coidados_animais import dialogo_coidado
from horta.ui.pages.colleitas import dialogo_colleita
from horta.ui.pages.cultivos import dialogo_cultivo
from horta.ui.pages.estercos import dialogo_esterco
from horta.ui.pages.labores import dialogo_labor
from horta.ui.pages.lotes import dialogo_saida
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.pages.observacions import dialogo_observacion
from horta.ui.pages.outros_traballos import dialogo_outro_traballo
from horta.ui.pages.pastoreos import dialogo_pastoreo
from horta.ui.pages.producions_animais import dialogo_producion
from horta.ui.pages.produtos import dialogo_entrada
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.tempo import encher_tempo_que_falta

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "observacion": "bug_report",
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets",
    "movemento_animal": "swap_horiz", "producion_animal": "egg", "pastoreo": "landscape",
    "movemento_esterco": "compost",
    "lote_saida": "sell", "entrada_produto": "shopping_cart", "outro_traballo": "build",
    "clasificacion": "filter_list", "mestura": "merge", "transformacion": "blender",
    "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "observacion": "pragas",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "producion_animal": "producion", "pastoreo": "pastoreo",
    "movemento_esterco": "estercos",
    "lote_saida": "lotes", "entrada_produto": "produtos", "tarefa": "tarefas",
    "clasificacion": "lotes", "mestura": "lotes", "transformacion": "lotes",
    # Sen táboa propia: a súa lista é o propio Diario
    "outro_traballo": "diario",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "observacion": ObservacionPraga,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
    "pastoreo": Pastoreo, "movemento_esterco": MovementoEsterco,
    "lote_saida": LoteSaida, "entrada_produto": EntradaProduto,
    "clasificacion": Clasificacion, "mestura": Mestura, "transformacion": Transformacion,
    "outro_traballo": OutroTraballo,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "observacion": dialogo_observacion,
    "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
    "producion_animal": dialogo_producion, "pastoreo": dialogo_pastoreo,
    "movemento_esterco": dialogo_esterco,
    "lote_saida": dialogo_saida, "entrada_produto": dialogo_entrada,
    "clasificacion": dialogo_clasificacion, "mestura": dialogo_mestura,
    "transformacion": dialogo_transformacion,
    "outro_traballo": dialogo_outro_traballo,
}


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
                    self._abrir[tipo] = lambda _x: abrir_tarefa()
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
                ui.button(_("Facela agora"), icon="check", on_click=facela)
                ui.button(_("Editar a tarefa"), icon="edit", on_click=lambda: ui.navigate.to(
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
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return
        principais, outros = tipos_para_apuntar(session, actor, formularios.horta_id)

    def botons(tipos: list[str]) -> None:
        with ui.grid().classes("w-full grid-cols-2 sm:grid-cols-3 gap-2"):
            for tipo in tipos:
                texto = _("Tarefa por facer") if tipo == "tarefa" else _(TIPOS[tipo])

                def escollido(tipo: str = tipo) -> None:
                    escoller.close()
                    formularios.novo(tipo)

                ui.button(texto, icon=ICONAS[tipo], on_click=escollido).props(
                    "outline stack").classes("w-full")

    with ui.dialog() as escoller, ui.card().style("width: min(34rem, 94vw)"):
        ui.label(_("Que fixeches?")).classes("text-h6")
        botons(principais)
        with ui.expansion(_("Outros traballos")).classes("w-full"):
            botons(outros)
        ui.button(_("Cancelar"), on_click=escoller.close).props("flat")
    ui.button(_("Apuntar traballo"), icon="add", on_click=escoller.open)
    with ui.page_sticky(position="bottom-right", x_offset=16, y_offset=16).classes("lt-md"):
        ui.button(icon="add", on_click=escoller.open).props(
            f'fab color=primary aria-label="{_("Apuntar traballo")}"')


# Estado no CUE da Xunta (services.envio_cue.estado_cue)
_CUE = {"aceptado": N_("no CUE"), "enviado": N_("enviado ao CUE"), "erro": N_("erro no CUE"),
        "pechado": N_("pechado no CUE")}


def _data(t: Traballo) -> str:
    return f"{t.data:%d/%m/%Y}" if t.data else _("sen data")


def tarxeta(t: Traballo, ao_premer: Callable[[], None], nomes: dict[int, str],
             horta_id: int, pode_editar: bool, fotos: int, cue: str | None = None) -> None:
    with ui.row().classes("tarxeta w-full items-center no-wrap gap-3 cursor-pointer q-pa-sm").on(
            "click", ao_premer):
        ui.icon(ICONAS[t.tipo]).classes("text-h5 text-primary")
        nome_tipo = _(TIPOS[t.tipo]) if t.tipo in TIPOS else t.tipo
        texto_titulo = (
            _("{tipo}: {que}").format(tipo=nome_tipo, que=t.que) if t.que else nome_tipo
        )
        with ui.column().classes("gap-0 col"):
            ui.label(texto_titulo).classes(
                "text-weight-bold")
            quen = ", ".join(nomes.get(p, "") for p in t.persoas)
            if t.onde or quen:
                ui.label(" · ".join(x for x in (t.onde, quen) if x)).classes(
                    "texto-suave text-caption")
        with ui.column().classes("items-end gap-0"):
            ui.label(_data(t)).classes("text-caption")
            if t.atrasado:
                ui.label(_("atrasada")).classes("etiqueta-aviso")
            if cue is not None:
                ui.label(_(_CUE[cue])).classes("etiqueta-aviso" if cue in ("erro", "pechado")
                                            else "texto-suave text-caption")
        boton_fotos(horta_id, t.tipo, t.id, texto_titulo, pode_editar, fotos)


def seccion_diario(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}

    encher_tempo_que_falta(horta_id)
    formularios = Formularios(horta_id) if pode_editar else None
    if formularios is not None:
        with ui.row().classes("q-mb-md"):
            boton_apuntar_traballo(formularios)

    hoxe = date.today()
    # Pregados, para que no móbil se vexa o primeiro traballo sen baixar (X6)
    with ui.expansion(_("Filtrar"), icon="filter_list").classes("w-full q-mb-md").props(
            "dense"), ui.row().classes("w-full items-end gap-2 wrap"):
        opcions_tipo = {"": _("Todos os traballos"), **{k: _(v) for k, v in TIPOS.items()}}
        tipo = ui.select(opcions_tipo, value="", label=_("Tipo")).classes("w-56")
        parcela = ui.select(
            {0: _("Todas"), **parcelas}, value=0, label=_("Parcela")
        ).classes("w-48")
        quen = ui.select({0: _("Todas"), **persoas}, value=0, label=_("Quen")).classes("w-48")
        estado = ui.select({"": _("Feitos e por facer"), "por_facer": _("Por facer"),
                            "feito": _("Feitos")}, value="", label=_("Estado")).classes("w-48")
        # A campaña do caderno e do CUE é o ano natural
        desde = campo_data(_("Desde"), hoxe.replace(month=1, day=1).isoformat()
                           ).classes(remove="w-full", add="w-40")
        ata = campo_data(_("Ata"), hoxe.isoformat()).classes(remove="w-full", add="w-40")

    @ui.refreshable
    def lista() -> None:
        if tipo.value and SECCION_DO_TIPO[tipo.value] != "diario":
            ui.link(_("Ver a táboa de «{tipo}» con todos os seus datos").format(
                tipo=_(TIPOS[tipo.value])
            ), url_seccion(horta_id, SECCION_DO_TIPO[tipo.value]))
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                return
            try:
                inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
            except ValueError:
                inicio = fin = None
            traballos = listar_traballos(session, actor_actual, horta_id, inicio, fin)
            fotos = contar_fotos(session, actor_actual, horta_id)
            cue = estado_cue(session, actor_actual, horta_id)
        traballos = [
            t for t in traballos
            if (not tipo.value or t.tipo == tipo.value)
            and (not parcela.value or parcela.value in t.parcelas)
            and (not quen.value or quen.value in t.persoas)
            and (not estado.value or t.feito == (estado.value == "feito"))
        ]
        if not traballos:
            ui.label(_("Non hai traballos con estes filtros.")).classes("texto-suave")
        por_facer = [t for t in traballos if not t.feito]
        feitos = [t for t in traballos if t.feito]
        for titulo, grupo in ((_("Por facer"), por_facer), (_("Feito"), feitos)):
            if not grupo:
                continue
            ui.label(titulo).classes("text-subtitle1 text-weight-bold q-mt-md")
            with ui.column().classes("w-full gap-2"):
                for t in grupo:
                    if formularios is not None:
                        tarxeta(t, partial(formularios.editar, t), persoas, horta_id, True,
                                 fotos.get((t.tipo, t.id), 0), cue.get((t.tipo, t.id)))
                    else:
                        tarxeta(t, partial(ui.navigate.to,
                                            url_seccion(horta_id, SECCION_DO_TIPO[t.tipo])),
                                 persoas, horta_id, False, fotos.get((t.tipo, t.id), 0),
                                 cue.get((t.tipo, t.id)))

    for filtro in (tipo, parcela, quen, estado, desde, ata):
        filtro.on_value_change(lista.refresh)
    lista()

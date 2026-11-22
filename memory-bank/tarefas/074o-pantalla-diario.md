# Tarefa 074o — Diario e «Apuntar traballo»

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 074f a 074n. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Pantalla Diario (todo o feito e por facer, con filtros) e botón «Apuntar traballo» (que fixeches → formulario dese tipo). Pantalla Informes: caderno e o que lle falta. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/diario.py` (**ficheiro novo**)
- `src/horta/ui/pages/informes.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/pages/diario.py`

Contido completo:
```python
"""Diario de traballos: todo o feito e o por facer nunha lista, e «Apuntar traballo»
(primeiro que se fixo, despois o formulario dese tipo)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from functools import partial
from typing import Any

from nicegui import ui

from horta.db import Base, get_session
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.labor import Labor
from horta.models.parcela import Parcela
from horta.models.rega import Rega
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.services.diario import TIPOS, Traballo, listar_traballos
from horta.ui.campos import campo_data
from horta.ui.dialogo_tarefa import dialogo_nova_tarefa
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data
from horta.ui.pages.abonados import dialogo_abonado
from horta.ui.pages.analises import dialogo_analise
from horta.ui.pages.colleitas import dialogo_colleita
from horta.ui.pages.cultivos import dialogo_cultivo
from horta.ui.pages.labores import dialogo_labor
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "tratamento_instalacion": "warehouse", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[[Any], None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
}
_DIAS_POR_DEFECTO = 90


class Formularios:
    """Os formularios de cada tipo de traballo. Constrúense a primeira vez que se usan."""

    def __init__(self, horta_id: int) -> None:
        self.horta_id = horta_id
        self._contedor = ui.element("div")
        self._abrir: dict[str, Callable[[Any], None]] = {}

    def _abridor(self, tipo: str) -> Callable[[Any], None]:
        if tipo not in self._abrir:
            with self._contedor:
                if tipo == "tarefa":
                    abrir_tarefa = dialogo_nova_tarefa(self.horta_id)
                    self._abrir[tipo] = lambda _: abrir_tarefa()
                else:
                    self._abrir[tipo] = _CONSTRUTORES[tipo](self.horta_id)
        return self._abrir[tipo]

    def novo(self, tipo: str) -> None:
        self._abridor(tipo)(None)

    def editar(self, traballo: Traballo) -> None:
        if traballo.tipo == "tarefa":
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


def _tarxeta(t: Traballo, ao_premer: Callable[[], None]) -> None:
    with ui.row().classes("tarxeta w-full items-center no-wrap gap-3 cursor-pointer q-pa-sm").on(
            "click", ao_premer):
        ui.icon(ICONAS[t.tipo]).classes("text-h5 text-primary")
        with ui.column().classes("gap-0 col"):
            ui.label(TIPOS[t.tipo] + (f": {t.que}" if t.que else "")).classes(
                "text-weight-bold")
            if t.onde:
                ui.label(t.onde).classes("texto-suave text-caption")
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

    formularios = Formularios(horta_id) if pode_editar else None
    if formularios is not None:
        with ui.row().classes("q-mb-md"):
            boton_apuntar_traballo(formularios)

    hoxe = date.today()
    with ui.row().classes("w-full items-end gap-2 wrap q-mb-md"):
        tipo = ui.select({"": "Todos os traballos", **TIPOS}, value="", label="Tipo").classes(
            "w-56")
        parcela = ui.select({0: "Todas", **parcelas}, value=0, label="Parcela").classes("w-48")
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
                        _tarxeta(t, partial(formularios.editar, t))
                    else:
                        _tarxeta(t, partial(ui.navigate.to,
                                            url_seccion(horta_id, SECCION_DO_TIPO[t.tipo])))

    for filtro in (tipo, parcela, estado, desde, ata):
        filtro.on_value_change(lista.refresh)
    lista()
```

### Paso 2 — crear o ficheiro `src/horta/ui/pages/informes.py`

Contido completo:
```python
"""Informes: o que sae do traballo apuntado. Hoxe, o caderno de explotación e o que lle falta."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.faltas_caderno import faltas_caderno
from horta.ui.descarga_caderno import boton_caderno
from horta.ui.layout import url_seccion
from horta.ui.sesion import pechar_sesion, usuario_actual

_SECCION_DA_FALTA = {"Tratamentos": "tratamentos", "Abonados": "fertilizacion",
                     "Regas": "rega", "Labores": "labores"}


def seccion_informes(horta_id: int, uso_profesional: bool) -> None:
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md"):
        ui.label("Caderno de explotación").classes("text-subtitle1 text-weight-bold")
        ui.label("Modelo da Xunta en Excel, co período que escollas. Sae do que está apuntado."
                 ).classes("texto-suave")
        boton_caderno(horta_id)
    if not uso_profesional:
        ui.label("Explotación non profesional: o caderno non é obrigatorio, pero podes "
                 "descargalo se che serve.").classes("texto-suave q-mt-md")
        return
    inicio_ano = date(date.today().year, 1, 1)
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        faltas = faltas_caderno(session, actor, horta_id, desde=inicio_ano)
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md q-mt-md"):
        ui.label(f"Que lle falta ao caderno de {inicio_ano.year}").classes(
            "text-subtitle1 text-weight-bold")
        if not faltas:
            ui.label("Nada: o apuntado ten todo o que pide o caderno.").classes("etiqueta-ok")
            return
        ui.label("Non impide descargalo: complétao cando poidas.").classes("texto-suave")
        for falta in faltas:
            with ui.row().classes("items-center gap-2"):
                ui.icon("warning").classes("text-warning")
                ui.label(f"{falta.traballo}: {falta.cantos} sen {falta.dato}")
                ui.link("Ver", url_seccion(horta_id, _SECCION_DA_FALTA[falta.traballo]))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Diario e «Apuntar traballo»: feito.

# Tarefa 051c — Pantalla de Rega

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 051b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Nova sección Rega no menú (CADERNO, despois de Fertilización): táboa e diálogo rápido (cultivo, data, superficie, sistema, auga) co botón «Non sei os litros» que abre a calculadora. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §3. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/ui/pages/regas.py` (**ficheiro novo**)
- `src/horta/ui/layout.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/pages/regas.py`

Contido completo:
```python
"""Sección Rega: cada rega dun cultivo (CUE bloque 10). Baixa lóxica."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.parcela import Parcela
from horta.models.rega import Rega
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.regas import (
    UNIDADES_AUGA,
    DatosRega,
    actualizar_rega,
    crear_rega,
    dar_de_baixa_rega,
    listar_regas,
    litros_estimados,
    ultimo_sistema_rega,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA


def seccion_regas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        regas = listar_regas(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in listar_cultivos(session, actor, horta_id)}
        sistemas = {v.codigo: v.descricion for v in valores_vixentes(session, "sistema_rega")}
        orixes = {v.codigo: v.descricion for v in valores_vixentes(session, "orixe_auga")}
        unidades_cat = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat.get(c, c) for c in UNIDADES_AUGA}
        practicas = {v.codigo: v.descricion for v in valores_vixentes(session, "boas_practicas")
                     if "rega" in (v.categoria or "")}

    filas = [{
        "id": r.id,
        "data": f"{r.data_inicio:%d/%m/%Y}",
        "cultivo": cultivos.get(r.cultivo_id, ""),
        "sistema": sistemas.get(r.sistema_rega, r.sistema_rega),
        "auga": f"{r.cantidade:g} {unidades.get(r.unidade, '')}",
    } for r in regas]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivo", "Cultivo"), ("sistema", "Sistema"),
            ("auga", "Auga"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai regas" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    if not sistemas:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as calculadora, ui.card().style("width: min(28rem, 94vw)"):
        ui.label("Calcular os litros").classes("text-h6")
        ui.label("Con mangueira ou goteo:").classes("text-caption")
        with ui.row().classes("w-full no-wrap"):
            minutos = ui.input("Minutos").classes("col")
            litros_minuto = ui.input("Litros por minuto").classes("col")
        ui.label("Ou con regadeira:").classes("text-caption")
        with ui.row().classes("w-full no-wrap"):
            regadeiras = ui.input("Regadeiras").classes("col")
            litros_regadeira = ui.input("Litros de cada unha").classes("col")

        def usar() -> None:
            litros = litros_estimados(
                parsear_decimal(minutos.value), parsear_decimal(litros_minuto.value),
                parsear_decimal(regadeiras.value), parsear_decimal(litros_regadeira.value))
            if litros is None:
                ui.notify("Enche minutos e litros por minuto, ou regadeiras e litros",
                          type="warning")
                return
            cantidade.value, unidade.value = f"{litros:g}", "4"
            calculadora.close()

        with ui.row():
            ui.button("Usar estes litros", icon="check", on_click=usar)
            ui.button("Cancelar", on_click=calculadora.close).props("flat")

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar rega").classes("text-h6")
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        superficie = CampoSuperficie("Superficie regada (baleiro = a do cultivo)")
        sistema = ui.select(sistemas, label="Como se rega").classes("w-full")
        with ui.row().classes("w-full no-wrap items-center"):
            cantidade = ui.input("Auga").classes("col")
            unidade = ui.select(unidades, value="4", label="Unidade").classes("col")
        ui.button("Non sei os litros", icon="calculate", on_click=calculadora.open).props(
            "flat dense")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            orixe = ui.select(orixes, label="De onde vén a auga (baleiro = a da parcela)",
                              clearable=True).classes("w-full")
            contador = ui.input("Nº de contador").classes("w-full")
            boas = ui.select(practicas, multiple=True, label="Boas prácticas").classes(
                "w-full").props("use-chips")
            notas = ui.textarea("Notas").classes("w-full")

        def propor_sistema() -> None:
            if cultivo.value is not None and sistema.value is None:
                with get_session() as session:
                    sistema.value = ultimo_sistema_rega(session, cultivo.value)

        cultivo.on_value_change(propor_sistema)

        def gardar() -> None:
            if cultivo.value is None or sistema.value is None:
                ui.notify("Escolle o cultivo e como se rega", type="warning")
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
                    datos = DatosRega(
                        cultivo_id=cultivo.value, data_inicio=inicio,
                        data_fin=parsear_data(data_fin.value), superficie_ha=superficie.ha,
                        sistema_rega=sistema.value,
                        cantidade=parsear_decimal(cantidade.value) or 0,
                        unidade=unidade.value or "4", orixe_auga=orixe.value,
                        num_contador=contador.value or None,
                        boas_practicas=list(boas.value or []), notas=notas.value or None)
                    existente = session.get(Rega, editando["id"]) if editando["id"] else None
                    if existente is None:
                        crear_rega(session, actor_actual, datos)
                    else:
                        actualizar_rega(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(r: Rega | None) -> None:
        editando["id"] = r.id if r else None
        titulo.text = "Editar rega" if r else "Apuntar rega"
        sistema.value = r.sistema_rega if r else None
        cultivo.value = r.cultivo_id if r else None
        data_inicio.value = (r.data_inicio if r else date.today()).isoformat()
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        superficie.establecer(r.superficie_ha if r else None)
        cantidade.value = f"{r.cantidade:g}" if r else ""
        unidade.value = r.unidade if r else "4"
        orixe.value = r.orixe_auga if r else None
        contador.value = (r.num_contador or "") if r else ""
        boas.value = [b.codigo for b in r.boas_practicas] if r else []
        notas.value = (r.notas or "") if r else ""
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha rega na táboa", type="warning")
            return
        with get_session() as session:
            r = session.get(Rega, taboa.selected[0]["id"])
            if r is not None:
                _ = r.boas_practicas
                abrir(r)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha rega na táboa", type="warning")
            return
        rega_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                r = session.get(Rega, rega_id)
                if actor_actual is None or r is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_rega(
                    session, actor_actual, r))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta rega? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar rega", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")
```

### Paso 2 — `src/horta/ui/layout.py`: entrada no menú

Antes:
```python
    Seccion("fertilizacion", "Fertilización", "compost", "Caderno"),
```

Despois:
```python
    Seccion("fertilizacion", "Fertilización", "compost", "Caderno"),
    Seccion("rega", "Rega", "water_drop", "Caderno"),
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`: importar

Antes:
```python
from horta.ui.pages.tratamentos_fito import```

Despois:
```python
from horta.ui.pages.regas import seccion_regas
from horta.ui.pages.tratamentos_fito import```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`: mostrar a sección

Antes:
```python
    elif seccion == "tarefas":
```

Despois:
```python
    elif seccion == "rega":
        seccion_regas(horta_id, pode_editar)
    elif seccion == "tarefas":
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A sección Rega aparece no menú e permite apuntar regas.

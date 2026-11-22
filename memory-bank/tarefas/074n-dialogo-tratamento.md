# Tarefa 074n — Formularios separados: tratamento fitosanitario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do tratamento fitosanitario constrúese en dialogo_tratamento_fito, e o de nova tarefa en ui/dialogo_tarefa.py, para abrilos tamén desde «Apuntar traballo». Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/tratamentos.py`
- `src/horta/ui/dialogo_tarefa.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
from __future__ import annotations
```

Despois:
```python
from __future__ import annotations

from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
from horta.ui.accions import executar_accion
```

Despois:
```python
from horta.ui.accions import executar_accion
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
```

### Paso 3 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
            })
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        persoas = listar_persoas(session, actor, horta_id)
        opcions = OpcionsTratamento(
            cultivos={c.id: f"{c.especie} {c.variedade or ''} — "
                            f"{parcelas[c.parcela_id].nome}".strip() for c in cultivos_horta},
            problemas={tipo: _opcions(session, tipo) for tipo in TIPOS_PROBLEMA},
            xustificacions=_opcions(session, "xustificacion"),
            estados=_opcions(session, "estado_fenoloxico"),
            unidades=_opcions(session, "unidade_medida"),
            tipos_produto=_opcions(session, "tipo_produto"),
            tipos_medida=_opcions(session, "tipo_medida_fito"),
            eficacias=_opcions(session, "eficacia"),
            aplicadores={p.id: p.nome for p in persoas if p.e_aplicador},
            asesores={p.id: p.nome for p in persoas if p.e_asesor},
            maquinas={m.id: m.alias for m in listar_maquinas(session, actor, horta_id)},
            rexistro={p.num_rexistro: f"{p.nome} ({p.num_rexistro})"
                      for p in session.query(FitoProduto).order_by(FitoProduto.nome)},
        )
```

Despois:
```python
            })
```

### Paso 4 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
    if not opcions.problemas["enfermidade"]:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return
    if not opcions.rexistro:
        ui.label("Falta o rexistro de fitosanitarios do MAPA: sen el non se comproban os "
                 "produtos. Un administrador debe executar `horta-catalogos fitosanitarios`."
                 ).classes("text-warning")

    abrir = crear_dialogo_tratamento(horta_id, opcions)
```

Despois:
```python
    abrir = dialogo_tratamento_fito(horta_id)
```

### Paso 5 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
            "outline"
        )
```

Despois:
```python
            "outline"
        )


def dialogo_tratamento_fito(horta_id: int) -> Callable[[TratamentoFito | None], None]:
    """Constrúe o diálogo do tratamento fitosanitario e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        persoas = listar_persoas(session, actor, horta_id)
        opcions = OpcionsTratamento(
            cultivos={c.id: f"{c.especie} {c.variedade or ''} — "
                            f"{parcelas[c.parcela_id].nome}".strip() for c in cultivos_horta},
            problemas={tipo: _opcions(session, tipo) for tipo in TIPOS_PROBLEMA},
            xustificacions=_opcions(session, "xustificacion"),
            estados=_opcions(session, "estado_fenoloxico"),
            unidades=_opcions(session, "unidade_medida"),
            tipos_produto=_opcions(session, "tipo_produto"),
            tipos_medida=_opcions(session, "tipo_medida_fito"),
            eficacias=_opcions(session, "eficacia"),
            aplicadores={p.id: p.nome for p in persoas if p.e_aplicador},
            asesores={p.id: p.nome for p in persoas if p.e_asesor},
            maquinas={m.id: m.alias for m in listar_maquinas(session, actor, horta_id)},
            rexistro={p.num_rexistro: f"{p.nome} ({p.num_rexistro})"
                      for p in session.query(FitoProduto).order_by(FitoProduto.nome)},
        )
    if not opcions.problemas["enfermidade"]:
        ui.label(AVISO_SEN_CATALOGOS).classes("text-warning")
    if not opcions.rexistro:
        ui.label("Falta o rexistro de fitosanitarios do MAPA: sen el non se comproban os "
                 "produtos. Un administrador debe executar `horta-catalogos fitosanitarios`."
                 ).classes("text-warning")
    return crear_dialogo_tratamento(horta_id, opcions)
```

### Paso 6 — crear o ficheiro `src/horta/ui/dialogo_tarefa.py`

Contido completo:
```python
"""Diálogo «Nova tarefa»: un traballo por facer. Ábrese desde Tarefas e desde «Apuntar
traballo»."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.services.cultivos import listar_cultivos
from horta.services.parcelas import listar_parcelas
from horta.services.tarefas import crear_tarefa
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual

PRIORIDADES_TAREFA = ("baixa", "media", "alta")


def dialogo_nova_tarefa(horta_id: int) -> Callable[[], None]:
    """Constrúe o diálogo e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda: None
        opcions_parcela: dict[int | str, str] = {"": "(sen parcela)", **{
            p.id: p.nome for p in listar_parcelas(session, actor, horta_id)}}
        opcions_cultivo: dict[int | str, str] = {"": "(sen cultivo)", **{
            c.id: c.especie for c in listar_cultivos(session, actor, horta_id)}}

    with ui.dialog() as dialogo, ui.card():
        ui.label("Nova tarefa").classes("text-md font-bold")
        descricion = ui.input("Que hai que facer").classes("w-full")
        parcela = ui.select(opcions_parcela, label="Parcela", value="").classes("w-full")
        cultivo = ui.select(opcions_cultivo, label="Cultivo", value="").classes("w-full")
        data = campo_data("Data (opcional)")
        prioridade = ui.select(list(PRIORIDADES_TAREFA), label="Prioridade", value="media")

        def crear() -> None:
            if not descricion.value:
                ui.notify("Escribe que hai que facer", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                creada = executar_accion(session, lambda: crear_tarefa(
                    session, actor_actual, horta_id, descricion.value,
                    parcela_id=parcela.value or None, cultivo_id=cultivo.value or None,
                    data=parsear_data(data.value),
                    prioridade=prioridade.value))
            if creada:
                ui.navigate.reload()

        with ui.row():
            ui.button("Crear", icon="check", on_click=crear)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        descricion.value = ""
        parcela.value = cultivo.value = ""
        data.value = ""
        prioridade.value = "media"
        dialogo.open()

    return abrir
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios separados: tratamento fitosanitario: feito.

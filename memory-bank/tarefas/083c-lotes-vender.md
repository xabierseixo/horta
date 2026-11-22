# Tarefa 083c — Lotes (4/5): vender dende colleitas e produción

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 083b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Columna «Queda» e botón «Vender» nas colleitas e na produción dos animais. Deseño: `docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md` (paso 4 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/pages/producions_animais.py`
- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.lotes import listar_lotes, resumo_lotes
```

### Paso 2 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.lotes import dialogo_saida
```

### Paso 3 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
        producions = listar_producions(session, actor, horta_id)
```

Despois:
```python
        producions = listar_producions(session, actor, horta_id)
        queda = resumo_lotes(session, actor, horta_id)
        unidades_lote = {lo.id: lo.unidade for lo in listar_lotes(session, actor, horta_id)}
```

### Paso 4 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
        "quen": persoas.get(pr.persoa_id, "") if pr.persoa_id else "",
    } for pr in producions]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("grupo", "Animais"), ("produto", "Produto"),
            ("cantidade", "Canto"), ("retirada", "Retirado"), ("lote", "Lote"),
            ("quen", "Quen"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai produción apuntada" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_producion(horta_id)
```

Despois:
```python
        "queda": (f"{queda[pr.lote_id][2]:g} {unidades_lote[pr.lote_id]}"
                  if pr.lote_id in queda else ""),
        "quen": persoas.get(pr.persoa_id, "") if pr.persoa_id else "",
    } for pr in producions]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("grupo", "Animais"), ("produto", "Produto"),
            ("cantidade", "Canto"), ("retirada", "Retirado"), ("lote", "Lote"), ("queda", "Queda"),
            ("quen", "Quen"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai produción apuntada" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_producion(horta_id)

    abrir_saida = dialogo_saida(horta_id)

    def vender() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        pr_escollida = next(x for x in producions if x.id == taboa.selected[0]["id"])
        abrir_saida(None, None, pr_escollida.lote_id, "venda")
```

### Paso 5 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
        ui.button("Apuntar produción", icon="add", on_click=lambda: abrir(None))
```

Despois:
```python
        ui.button("Apuntar produción", icon="add", on_click=lambda: abrir(None))
        ui.button("Vender", icon="sell", on_click=vender).props("outline")
```

### Paso 6 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.services.lotes import listar_lotes, resumo_lotes
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.lotes import dialogo_saida
```

### Paso 7 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        colleitas = listar_colleitas(session, actor, horta_id)
```

Despois:
```python
        colleitas = listar_colleitas(session, actor, horta_id)
        queda = resumo_lotes(session, actor, horta_id)
        unidades_lote = {lo.id: lo.unidade for lo in listar_lotes(session, actor, horta_id)}
```

### Paso 8 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
            "lote": c.lote,
```

Despois:
```python
            "lote": c.lote,
        "queda": (f"{queda[c.lote_id][2]:g} {unidades_lote[c.lote_id]}"
                  if c.lote_id in queda else ""),
```

### Paso 9 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
            ("lote", "Lote"), ("destino", "Destino"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai colleitas" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return

    abrir = dialogo_colleita(horta_id)
```

Despois:
```python
            ("lote", "Lote"), ("queda", "Queda"), ("destino", "Destino"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai colleitas" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return

    abrir = dialogo_colleita(horta_id)

    abrir_saida = dialogo_saida(horta_id)

    def vender() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        c_escollida = next(x for x in colleitas if x.id == taboa.selected[0]["id"])
        abrir_saida(None, None, c_escollida.lote_id, "venda")
```

### Paso 10 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        ui.button("Apuntar colleita", icon="add", on_click=lambda: abrir(None))
```

Despois:
```python
        ui.button("Apuntar colleita", icon="add", on_click=lambda: abrir(None))
        ui.button("Vender", icon="sell", on_click=vender).props("outline")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Lotes (4/5): vender dende colleitas e produción: feito.

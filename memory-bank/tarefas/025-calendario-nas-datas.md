# Tarefa 025 — Calendario nos campos de data

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 024.

## Obxectivo

Hoxe as datas escríbense a man como `AAAA-MM-DD`. Engádese un campo de data reutilizable (`campo_data`) cun botón de calendario en galego (a semana empeza o luns; péchase só ao escoller o día). O valor segue sendo texto `AAAA-MM-DD`, así que a validación (`parsear_data` / `_parsear_data`) non cambia e tamén se pode seguir escribindo a man.

## Ficheiros a tocar

- `src/horta/ui/campos.py` (**ficheiro novo**)
- `src/horta/ui/pages/horta_detalle.py`
- `src/horta/ui/pages/persoas.py`
- `src/horta/ui/pages/maquinaria.py`
- `src/horta/ui/pages/tratamentos_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/campos.py`

Contido completo:

```python
"""Campos de formulario reutilizables."""

from __future__ import annotations

from nicegui import ui

_LOCALE_GL = {
    "days": ["Domingo", "Luns", "Martes", "Mércores", "Xoves", "Venres", "Sábado"],
    "daysShort": ["Dom", "Lun", "Mar", "Mér", "Xov", "Ven", "Sáb"],
    "months": [
        "Xaneiro", "Febreiro", "Marzo", "Abril", "Maio", "Xuño",
        "Xullo", "Agosto", "Setembro", "Outubro", "Novembro", "Decembro",
    ],
    "monthsShort": [
        "Xan", "Feb", "Mar", "Abr", "Mai", "Xuñ", "Xul", "Ago", "Set", "Out", "Nov", "Dec",
    ],
    "firstDayOfWeek": 1,
}


def campo_data(etiqueta: str, valor: str = "") -> ui.input:
    """Campo de data con calendario. O valor segue sendo texto AAAA-MM-DD (ver parsear_data)."""
    with ui.input(etiqueta, value=valor).classes("w-full") as campo:
        with ui.menu().props("no-parent-event") as menu:
            calendario = ui.date(mask="YYYY-MM-DD", on_change=lambda: menu.close())
            calendario.bind_value(campo).props("minimal")
            calendario._props["locale"] = _LOCALE_GL
        with campo.add_slot("append"):
            ui.icon("event").on("click", menu.open).classes("cursor-pointer")
    return campo
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        data_sementeira_edit = ui.input("Data sementeira (AAAA-MM-DD)")
```

Despois:
```python
        data_sementeira_edit = campo_data("Data sementeira")
```

### Paso 3 — mesmo ficheiro

Antes:
```python
        data_plantacion_edit = ui.input("Data plantación (AAAA-MM-DD)")
```

Despois:
```python
        data_plantacion_edit = campo_data("Data plantación")
```

### Paso 4 — mesmo ficheiro

Antes:
```python
        data_colleita_prevista_edit = ui.input("Data colleita prevista (AAAA-MM-DD)")
```

Despois:
```python
        data_colleita_prevista_edit = campo_data("Data colleita prevista")
```

### Paso 5 — mesmo ficheiro

Antes:
```python
        data_colleita_real_edit = ui.input("Data colleita real (AAAA-MM-DD)")
```

Despois:
```python
        data_colleita_real_edit = campo_data("Data colleita real")
```

### Paso 6 — mesmo ficheiro

Antes:
```python
            data_input = ui.input("Data (AAAA-MM-DD)")
```

Despois:
```python
            data_input = campo_data("Data")
```

### Paso 7 — mesmo ficheiro

Antes:
```python
        data_edit = ui.input("Data (AAAA-MM-DD)")
```

Despois:
```python
        data_edit = campo_data("Data")
```

### Paso 8 — mesmo ficheiro

Antes:
```python
            data_input = ui.input("Data (AAAA-MM-DD, opcional)")
```

Despois:
```python
            data_input = campo_data("Data (opcional)")
```

### Paso 9 — mesmo ficheiro

Antes:
```python
        data_edit = ui.input("Data (AAAA-MM-DD, opcional)")
```

Despois:
```python
        data_edit = campo_data("Data (opcional)")
```

### Paso 10 — mesmo ficheiro

Antes:
```python
        data_limite_edit = ui.input("Data límite (AAAA-MM-DD, opcional)")
```

Despois:
```python
        data_limite_edit = campo_data("Data límite (opcional)")
```

### Paso 11 — mesmo ficheiro

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
```

Despois:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
```

### Paso 12 — `src/horta/ui/pages/persoas.py`

Antes:
```python
        caducidade = ui.input("Caducidade do carné (AAAA-MM-DD)").classes("w-full")
```

Despois:
```python
        caducidade = campo_data("Caducidade do carné")
```

### Paso 13 — mesmo ficheiro

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_data
```

Despois:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
```

### Paso 14 — `src/horta/ui/pages/maquinaria.py`

Antes:
```python
        inspeccion = ui.input("Data última inspección (AAAA-MM-DD)")
```

Despois:
```python
        inspeccion = campo_data("Data última inspección")
```

### Paso 15 — mesmo ficheiro

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data, parsear_decimal
```

### Paso 16 — `src/horta/ui/pages/tratamentos_fito.py`

Antes:
```python
                data_inicio = ui.input("Data de inicio (AAAA-MM-DD)",
                                       value=date.today().isoformat()).classes("w-full")
                data_fin = ui.input(
                    "Data de fin (AAAA-MM-DD)", value=date.today().isoformat()
                ).classes("w-full")
```

Despois:
```python
                data_inicio = campo_data("Data de inicio", date.today().isoformat())
                data_fin = campo_data("Data de fin", date.today().isoformat())
```

### Paso 17 — mesmo ficheiro

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal, parsear_hora
```

Despois:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal, parsear_hora
```

## Criterios de aceptación

- Ningún campo de data da UI ten xa `(AAAA-MM-DD)` na etiqueta: `grep -rn 'ui.input("Data\|(AAAA-MM-DD)")' src/horta/ui` non devolve nada.
- Cada campo de data ten unha icona de calendario que abre un calendario en galego.
- Os tests pasan.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Paso 1**: Creouse `src/horta/ui/campos.py` con `campo_data()` e `_LOCALE_GL` (galés, semana comeza o luns).
- **Pasos 2–8** (`horta_detalle.py`): 4 campos de cultivo (`data_sementeira_edit`, `data_plantacion_edit`, `data_colleita_prevista_edit`, `data_colleita_real_edit`) + `data_input` da táboa + `data_limite_edit` cambiados de `ui.input` a `campo_data`. Importación actualizada.
- **Paso 9–10** (`persoas.py`): `caducidade` (carné ROPO) cambiado a `campo_data`. Importación actualizada.
- **Paso 11–12** (`maquinaria.py`): `inspeccion` cambiado a `campo_data`. Importación actualizada.
- **Paso 13–14** (`tratamentos_fito.py`): `data_inicio` e `data_fin` cambiados a `campo_data`. Importación actualizada.
- **Comprobacións**: `ruff check` ✅, `mypy` ✅, todos os módulos importanse sen erros.
- **Criterio grep**: `grep -rn 'ui.input("Data|(AAAA-MM-DD)")' src/horta/ui` non devolve nada.
- **Commit**: `smoth/calendario-nas-datas`

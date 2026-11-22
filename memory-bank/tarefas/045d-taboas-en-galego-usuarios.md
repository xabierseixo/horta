# Tarefa 045d — Táboa de usuarios en galego e botón Pechar

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 045. **Axente**: qwen-66 (mantemento).

## Obxectivo

As táboas mostraban textos de Quasar en inglés ("Records per page", "1-1 of 1", "1 record selected"); o galego é sempre a base. `ui/taboas.py` ten os textos en galego (`TEXTOS_TABOA`) e cada táboa engádeos ás súas props. Análise 2026-10-23, A4. Esta tarefa leva o cambio á táboa de usuarios da administración e cambia o botón "Cerrar" (castelán) por "Pechar".

## Ficheiros a tocar

- `src/horta/ui/admin/usuarios.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/admin/usuarios.py`: importar

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 2 — `src/horta/ui/admin/usuarios.py`: textos na táboa

Antes:
```python
_PROPS_TABOA = 'dense no-data-label="Non hai usuarios"'
```

Despois:
```python
_PROPS_TABOA = f'dense no-data-label="Non hai usuarios" {TEXTOS_TABOA}'
```

### Paso 3 — `src/horta/ui/admin/usuarios.py`: botón en galego

Antes:
```python
            ui.button("Cerrar", on_click=dialog_editar.close).props("flat")
```

Despois:
```python
            ui.button("Pechar", on_click=dialog_editar.close).props("flat")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A táboa de usuarios mostra os textos en galego e o diálogo de editar ten o botón "Pechar".

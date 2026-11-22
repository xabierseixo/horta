# Tarefa 021 — Resumo: estado da explotación e lista "para estar en regra"

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 018, 019 e 020.

## Obxectivo

Na sección Resumo, amosar o estado (rexistrada / en preparación / non profesional) e, se é profesional, a lista do que falta para estar en regra.

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — importar as funcións

Antes:
```python
from horta.services.errors import PermisoDenegadoError
```
Despois:
```python
from horta.services.en_regra import requisitos_en_regra
from horta.services.errors import PermisoDenegadoError
```

Antes:
```python
    engadir_membro,
    listar_hortas_usuario,
```
Despois:
```python
    engadir_membro,
    estado_rexistro,
    listar_hortas_usuario,
```

### Paso 2 — calcular estado e requisitos

Antes:
```python
        horta_codigo_rega = horta.codigo_rega or ""
```
Despois:
```python
        horta_codigo_rega = horta.codigo_rega or ""
        estado = estado_rexistro(horta)
        requisitos = requisitos_en_regra(session, actor, horta)
```

### Paso 3 — pintalos no Resumo

Antes:
```python
        _seccion_dashboard(
            len(parcelas),
```
Despois:
```python
        texto_estado, clase_estado = {
            "rexistrada": ("Explotación rexistrada", "etiqueta-ok"),
            "en_preparacion": ("En preparación", "etiqueta-aviso"),
            "non_profesional": ("Non profesional", "etiqueta-ok"),
        }[estado]
        ui.label(texto_estado).classes(clase_estado)
        if requisitos:
            with ui.column().classes("tarxeta w-full gap-2 q-my-md"):
                ui.label("Para estar en regra").classes("text-subtitle1 text-weight-bold")
                for requisito in requisitos:
                    with ui.row().classes("items-center gap-2"):
                        if requisito.cumprido:
                            ui.icon("check_circle").classes("text-positive")
                        else:
                            ui.icon("radio_button_unchecked").classes("texto-suave")
                        ui.label(requisito.texto)
                        if not requisito.cumprido:
                            ui.label(requisito.axuda).classes("texto-suave text-caption")
        _seccion_dashboard(
            len(parcelas),
```

## Criterios de aceptación

- O Resumo amosa a etiqueta do estado.
- Nas explotacións profesionais aparece a tarxeta "Para estar en regra" con cada requisito marcado ou pendente e a axuda nos pendentes.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- `src/horta/ui/pages/horta_detalle.py`:
  - **Paso 1**: importou `requisitos_en_regra` de `horta.services.en_regra` e `estado_rexistro` de `horta.services.hortas`.
  - **Paso 2**: calcula `estado = estado_rexistro(horta)` e `requisitos = requisitos_en_regra(session, actor, horta)` despois de cargar `horta_codigo_rega`.
  - **Paso 3**: na sección Resumo, amosa a etiqueta de estado (`Explotación rexistrada` / `En preparación` / `Non profesional`) e, cando hai requisitos, a tarxeta "Para estar en regra" con cada requisito marcado ou pendente e a axuda nos pendentes.
- ruff: All checks passed.
- mypy: Success: no issues found in 52 source files.
- pytest: 244 passed.
- Commit: `smoth/021-resumo-estado-e-en-regra`.

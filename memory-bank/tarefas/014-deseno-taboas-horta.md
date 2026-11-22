# Tarefa 014 — Deseño novo: táboas e títulos das seccións da explotación

**Estado**: feita (segundo intento: cada paso cambia un texto que aparece unha soa vez)

**Rama**: `deseno-visual`. Guía: `docs/superpowers/specs/2026-10-22-deseno-visual-design.md`.

## Obxectivo

Estilo novo para todas as táboas (dende o tema, sen tocar cada táboa) e quitar os títulos de sección repetidos.

## Ficheiros a tocar

- `src/horta/ui/tema.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. **Non crees scripts**: fai cada cambio coa túa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/tema.py`: o estilo de táboa vale para todas as táboas

Antes:
```python
.taboa { border-radius: 12px; border: 1px solid var(--cor-bordo); }
.taboa thead th { color: var(--cor-texto-suave); font-size: 12px; font-weight: 600;
```
Despois:
```python
.taboa, .q-table__container { border-radius: 12px; border: 1px solid var(--cor-bordo);
                               box-shadow: none; }
.taboa thead th, .q-table thead th { color: var(--cor-texto-suave); font-size: 12px;
                                      font-weight: 600;
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`: propiedades das táboas

Antes:
```python
_PROPS_TABOA = 'dense no-data-label="Non hai rexistros"'
```
Despois:
```python
_PROPS_TABOA = 'flat bordered no-data-label="Aínda non hai rexistros"'
```

### Paso 3 — mesmo ficheiro: quitar o título "Parcelas"

Antes:
```python
        ui.label("Parcelas").classes("text-lg font-bold")
```
Despois:
```python
        ui.space()
```

### Paso 4 — mesmo ficheiro: quitar o título "Cultivos"

Antes:
```python
        ui.label("Cultivos").classes("text-lg font-bold")
```
Despois:
```python
        ui.space()
```

### Paso 5 — mesmo ficheiro: quitar o título "Fertilización"

Antes:
```python
        ui.label("Fertilización").classes("text-lg font-bold")
```
Despois:
```python
        ui.space()
```

### Paso 6 — mesmo ficheiro: quitar o título "Animais"

Antes:
```python
        ui.label("Animais").classes("text-lg font-bold")
```
Despois:
```python
        ui.space()
```

### Paso 7 — mesmo ficheiro: quitar o título "Membros"

Antes:
```python
        ui.label("Membros").classes("text-lg font-bold")
```
Despois:
```python
        ui.space()
```

### Paso 8 — mesmo ficheiro: quitar o título "Tarefas"

Antes:
```python
        ui.label("Tarefas").classes("text-lg font-bold")
```
Despois:
```python
        ui.space()
```

## Criterios de aceptación

- Todas as táboas collen o estilo do tema (bordo suave, sen sombra, cabeceira en gris).
- `_PROPS_TABOA` ten `flat bordered`.
- Non queda ningunha das seis liñas `ui.label("…").classes("text-lg font-bold")` das seccións.
- Non se cambiou ningún outro ficheiro e non hai scripts novos no repositorio.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

Feitos os 8 pasos (tema CSS das táboas, props, seis títulos substituídos por `ui.space()`). ruff, mypy e pytest (237) en verde. O commit fíxoo Claude porque smoth esgotou o tempo xusto antes de facelo.

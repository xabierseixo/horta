# Tarefa 027c — (pantallas) Superficies en hectáreas, escritas en m² ou ha

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: a parte anterior desta tarefa.

## Obxectivo

O CUE pide as superficies en hectáreas, pero parcelas e fertilizacións gardábanas en m². Decisión do usuario (2026-10-23): a app garda **sempre hectáreas**, e cada campo de superficie ten un selector para escribir en **m² ou ha**. As táboas amosan m² se é menos dunha hectárea. Unha migración pasa os datos existentes de m² a ha.

## Ficheiros a tocar

- `src/horta/ui/campos.py`
- `alembic/versions/d4b8e2a6c1f3_superficies_en_hectareas.py` (**ficheiro novo**)
- `tests/ui/test_campos.py` (**ficheiro novo**)
- `src/horta/models/parcela.py`
- `src/horta/models/cultivo.py`
- `src/horta/services/tratamentos_fito.py`
- `tests/services/test_tratamentos_fito.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                        superficie=superficie_edit.value,
                        estado=estado_edit.value,
```

Despois:
```python
                        superficie=superficie_edit.ha,
                        estado=estado_edit.value,
```

### Paso 2 — mesmo ficheiro

Antes:
```python
        superficie_edit.value = fila["superficie"]
```

Despois:
```python
        superficie_edit.establecer(fila["superficie_ha"])
```

### Paso 3 — mesmo ficheiro: editar fertilización

Antes:
```python
        superficie_edit = ui.number("Superficie (m²)")
        n_edit = ui.number("N (%)")
```

Despois:
```python
        superficie_edit = CampoSuperficie("Superficie")
        n_edit = ui.number("N (%)")
```

### Paso 4 — mesmo ficheiro

Antes:
```python
                        superficie=superficie_edit.value,
                        n=n_edit.value,
```

Despois:
```python
                        superficie=superficie_edit.ha,
                        n=n_edit.value,
```

### Paso 5 — mesmo ficheiro

Antes:
```python
        superficie_edit.value = fertilizacion_completa.superficie
```

Despois:
```python
        superficie_edit.establecer(fertilizacion_completa.superficie)
```

## Criterios de aceptación

- En parcelas e fertilización, a superficie escríbese cun número e un selector m²/ha; ao cambiar a unidade, o número convértese.
- A táboa de parcelas amosa "250 m²" ou "1,50 ha".
- `uv run alembic upgrade head` e `uv run alembic downgrade -1` funcionan.
- Os tests novos de `tests/ui/test_campos.py` pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

# Tarefa 027b — (pantallas) Superficies en hectáreas, escritas en m² ou ha

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 027.

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

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`: importar

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie
```

### Paso 2 — mesmo ficheiro: nova parcela

Antes:
```python
            superficie_input = ui.number("Superficie (m²)")
```

Despois:
```python
            superficie_input = CampoSuperficie("Superficie")
```

### Paso 3 — mesmo ficheiro

Antes:
```python
                            superficie=superficie_input.value,
```

Despois:
```python
                            superficie=superficie_input.ha,
```

### Paso 4 — mesmo ficheiro: táboa de parcelas

Antes:
```python
            "superficie": p.superficie,
```

Despois:
```python
            "superficie": formatar_superficie(p.superficie),
            "superficie_ha": p.superficie,
```

### Paso 5 — mesmo ficheiro: editar parcela

Antes:
```python
        superficie_edit = ui.number("Superficie (m²)")
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")
```

Despois:
```python
        superficie_edit = CampoSuperficie("Superficie")
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

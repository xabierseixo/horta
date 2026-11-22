# Tarefa 040 — Superficie colleitada en m² ou ha

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

No diálogo de colleita, a superficie pedíase en hectáreas nun campo de texto. Agora usa `CampoSuperficie` (número + m²/ha), como parcelas e cultivos. Baleiro segue querendo dicir "a do cultivo". Revisión 2026-10-24, oco 3.

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`: importar

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie
```

### Paso 2 — mesmo ficheiro: o campo

Antes:
```python
        superficie = ui.input("Superficie colleitada (ha; baleiro = a do cultivo)").classes(
            "w-full")
```

Despois:
```python
        superficie = CampoSuperficie("Superficie colleitada (baleiro = a do cultivo)")
```

### Paso 3 — mesmo ficheiro: gardar en hectáreas

Antes:
```python
                        superficie_ha=parsear_decimal(superficie.value),
```

Despois:
```python
                        superficie_ha=superficie.ha,
```

### Paso 4 — mesmo ficheiro: baleirar ao apuntar unha nova

Antes:
```python
        for campo in (cantidade, lote, superficie, notas, data_fin, albaran):
            campo.value = ""
```

Despois:
```python
        for campo in (cantidade, lote, notas, data_fin, albaran):
            campo.value = ""
        superficie.establecer(None)
```

### Paso 5 — mesmo ficheiro: cargar ao editar

Antes:
```python
        superficie.value = "" if c.superficie_ha is None else f"{c.superficie_ha:g}"
```

Despois:
```python
        superficie.establecer(c.superficie_ha)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A superficie colleitada escríbese en m² ou ha e gárdase sempre en hectáreas.

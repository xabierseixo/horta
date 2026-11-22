# Tarefa 076e — Tarefas por facer (6/16): formulario do labor

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do labor ábrese xa enchido desde unha tarefa e, ao gardar, déixaa feita. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/labores.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/labores.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
```

### Paso 2 — `src/horta/ui/pages/labores.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
```

### Paso 3 — `src/horta/ui/pages/labores.py`

Antes:
```python
    editando: dict[str, int | None] = {"id": None}
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
```

### Paso 4 — `src/horta/ui/pages/labores.py`

Antes:
```python
                        crear_labor(session, actor_actual, datos)
```

Despois:
```python
                        novo = crear_labor(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
```

### Paso 5 — `src/horta/ui/pages/labores.py`

Antes:
```python
    def abrir(lab: Labor | None) -> None:
        editando["id"] = lab.id if lab else None
        titulo.text = "Editar labor" if lab else "Apuntar labor"
        tipo.value = lab.tipo_labor if lab else None
        cultivo.value = lab.cultivo_id if lab else None
```

Despois:
```python
    def abrir(lab: Labor | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = lab.id if lab else None
        titulo.text = "Editar labor" if lab else "Apuntar labor"
        tipo.value = lab.tipo_labor if lab else None
        cultivo.value = lab.cultivo_id if lab else (tarefa.cultivo_id if tarefa else None)
```

### Paso 6 — `src/horta/ui/pages/labores.py`

Antes:
```python
            proposta_quen(horta_id))
```

Despois:
```python
            proposta_quen(horta_id, tarefa))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (6/16): formulario do labor: feito.

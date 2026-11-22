# Tarefa 076g — Tarefas por facer (8/16): formulario da colleita

**Estado**: pendente

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario da colleita ábrese xa enchido desde unha tarefa e, ao gardar, déixaa feita. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from horta.models.colleita import Colleita
```

Despois:
```python
from horta.models.colleita import Colleita
from horta.models.tarefa import Tarefa
```

### Paso 2 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
```

### Paso 3 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
    editando: dict[str, int | None] = {"id": None}
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
```

### Paso 4 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
                        crear_colleita(session, actor, datos)
```

Despois:
```python
                        novo = crear_colleita(session, actor, datos)
                        rematar_tarefa(session, actor, editando["tarefa"], novo)
```

### Paso 5 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
    def abrir(c: Colleita | None) -> None:
        editando["id"] = c.id if c else None
        titulo.text = "Editar colleita" if c else "Apuntar colleita"
        cultivo.value = c.cultivo_id if c else None
        data.value = (c.data if c else date.today()).isoformat()
        persoa.value = (c.persoa_id if c.persoa_id in persoas else None) if c else (
            proposta_quen(horta_id))
```

Despois:
```python
    def abrir(c: Colleita | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = c.id if c else None
        titulo.text = "Editar colleita" if c else "Apuntar colleita"
        cultivo.value = c.cultivo_id if c else (tarefa.cultivo_id if tarefa else None)
        data.value = (c.data if c else date.today()).isoformat()
        persoa.value = (c.persoa_id if c.persoa_id in persoas else None) if c else (
            proposta_quen(horta_id, tarefa))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (8/16): formulario da colleita: feito.

# Tarefa 076i — Tarefas por facer (10/16): formulario do tratamento en instalacións

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do tratamento en instalacións ábrese xa enchido desde unha tarefa e, ao gardar, déixaa feita. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from horta.db import get_session
```

Despois:
```python
from horta.db import get_session
from horta.models.tarefa import Tarefa
```

### Paso 2 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
```

### Paso 3 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
    editando: dict[str, int | None] = {"id": None}
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
```

### Paso 4 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
                        crear_tratamento_instalacion(session, actor_actual, horta_id, datos)
```

Despois:
```python
                        novo = crear_tratamento_instalacion(session, actor_actual, horta_id, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
```

### Paso 5 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
    def abrir(t: TratamentoInstalacion | None) -> None:
        editando["id"] = t.id if t else None
        titulo.text = "Editar tratamento" if t else "Apuntar tratamento"
        tipo.value = t.tipo if t else "postcolleita"
        data.value = (t.data if t else date.today()).isoformat()
        persoa.value = (t.persoa_id if t.persoa_id in persoas else None) if t else (
            proposta_quen(horta_id))
```

Despois:
```python
    def abrir(t: TratamentoInstalacion | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = t.id if t else None
        titulo.text = "Editar tratamento" if t else "Apuntar tratamento"
        tipo.value = t.tipo if t else "postcolleita"
        data.value = (t.data if t else date.today()).isoformat()
        persoa.value = (t.persoa_id if t.persoa_id in persoas else None) if t else (
            proposta_quen(horta_id, tarefa))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (10/16): formulario do tratamento en instalacións: feito.

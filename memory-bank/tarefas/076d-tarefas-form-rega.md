# Tarefa 076d — Tarefas por facer (5/16): formulario da rega

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario da rega ábrese xa enchido desde unha tarefa e, ao gardar, déixaa feita. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/regas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.models.rega import Rega
```

Despois:
```python
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
```

### Paso 2 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
```

### Paso 3 — `src/horta/ui/pages/regas.py`

Antes:
```python
    editando: dict[str, int | None] = {"id": None}
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
```

### Paso 4 — `src/horta/ui/pages/regas.py`

Antes:
```python
                        crear_rega(session, actor_actual, datos)
```

Despois:
```python
                        novo = crear_rega(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
```

### Paso 5 — `src/horta/ui/pages/regas.py`

Antes:
```python
    def abrir(r: Rega | None) -> None:
        editando["id"] = r.id if r else None
        titulo.text = "Editar rega" if r else "Apuntar rega"
        sistema.value = r.sistema_rega if r else None
        cultivo.value = r.cultivo_id if r else None
        data_inicio.value = (r.data_inicio if r else date.today()).isoformat()
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        persoa.value = (r.persoa_id if r.persoa_id in persoas else None) if r else (
            proposta_quen(horta_id))
```

Despois:
```python
    def abrir(r: Rega | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = r.id if r else None
        titulo.text = "Editar rega" if r else "Apuntar rega"
        sistema.value = r.sistema_rega if r else None
        cultivo.value = r.cultivo_id if r else (tarefa.cultivo_id if tarefa else None)
        data_inicio.value = (r.data_inicio if r else date.today()).isoformat()
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        persoa.value = (r.persoa_id if r.persoa_id in persoas else None) if r else (
            proposta_quen(horta_id, tarefa))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (5/16): formulario da rega: feito.

# Tarefa 076h — Tarefas por facer (9/16): formulario da toma de mostras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario da toma de mostras ábrese xa enchido desde unha tarefa (parcela e cultivo) e, ao gardar, déixaa feita. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/analises.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/analises.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
```

### Paso 2 — `src/horta/ui/pages/analises.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
```

### Paso 3 — `src/horta/ui/pages/analises.py`

Antes:
```python
    editando: dict[str, int | None] = {"id": None}
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
```

### Paso 4 — `src/horta/ui/pages/analises.py`

Antes:
```python
                        crear_analise(session, actor_actual, horta_id, datos)
```

Despois:
```python
                        novo = crear_analise(session, actor_actual, horta_id, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
```

### Paso 5 — `src/horta/ui/pages/analises.py`

Antes:
```python
    def abrir(a: Analise | None) -> None:
        editando["id"] = a.id if a else None
        titulo.text = "Editar análise" if a else "Apuntar análise"
        material.value = a.material_analizado if a else None
        data.value = (a.data_mostraxe if a else date.today()).isoformat()
        persoa.value = (a.persoa_id if a.persoa_id in persoas else None) if a else (
            proposta_quen(horta_id))
        horas.value = f"{a.horas:g}" if a and a.horas else ""
        tipo.value = [t.codigo for t in a.tipos] if a else []
        substancia.value = [s.codigo for s in a.substancias] if a else []
        parcela.value = a.parcela_id if a else None
        cultivo.value = a.cultivo_id if a else None
```

Despois:
```python
    def abrir(a: Analise | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = a.id if a else None
        titulo.text = "Editar análise" if a else "Apuntar análise"
        material.value = a.material_analizado if a else None
        data.value = (a.data_mostraxe if a else date.today()).isoformat()
        persoa.value = (a.persoa_id if a.persoa_id in persoas else None) if a else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{a.horas:g}" if a and a.horas else ""
        tipo.value = [t.codigo for t in a.tipos] if a else []
        substancia.value = [s.codigo for s in a.substancias] if a else []
        parcela.value = a.parcela_id if a else (tarefa.parcela_id if tarefa else None)
        cultivo.value = a.cultivo_id if a else (tarefa.cultivo_id if tarefa else None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (9/16): formulario da toma de mostras: feito.

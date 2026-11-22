# Tarefa 050 — Probas de cultivos sen a fertilización vella

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 048b. **Axente**: qwen-66 (mantemento).

## Obxectivo

A fertilización vella (`Fertilizacion`, táboa `fertilizacion`) xa non a usa ningunha pantalla: a sección Fertilización usa os abonados novos (tarefas 047–048b). Esta cola quítaa. Paso 1: as probas de cultivos deixan de usala.

## Ficheiros a tocar

- `tests/services/test_cultivos.py`
- `tests/models/test_cultivo.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_cultivos.py`: importar

Antes:
```python
from horta.models.cultivo import Fertilizacion
```

Despois:
```python
```

### Paso 2 — `tests/services/test_cultivos.py`: quitar o servizo vello

Antes:
```python
from horta.services.fertilizacions import crear_fertilizacion
```

Despois:
```python
```

### Paso 3 — `tests/services/test_cultivos.py`: quitar a proba da fertilización vella

Antes:
```python
def test_eliminar_cultivo_borra_fisicamente_fertilizacions(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    fertilizacion_id = fertilizacion.id

    eliminar_cultivo(session, ana, cultivo)

    assert session.get(Fertilizacion, fertilizacion_id) is None


```

Despois:
```python
```

### Paso 4 — `tests/models/test_cultivo.py`: importar

Antes:
```python
from datetime import date

from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 5 — `tests/models/test_cultivo.py`: quitar a proba do modelo vello

Antes:
```python


def test_crear_fertilizacion_con_baixa_por_defecto_false(session):
    parcela = _crear_parcela(session)
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.flush()

    fertilizacion = Fertilizacion(
        cultivo_id=cultivo.id,
        data=date(2026, 4, 1),
        tipo="abonado_fondo",
        produto="Compost",
    )
    session.add(fertilizacion)
    session.commit()

    atopada = session.query(Fertilizacion).filter_by(produto="Compost").one()
    assert atopada.baixa is False
    assert atopada.n is None
```

Despois:
```python
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As probas de cultivos xa non usan a fertilización vella.

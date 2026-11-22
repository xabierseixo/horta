# Tarefa 050b — Probas de parcelas sen a fertilización vella

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 050. **Axente**: qwen-66 (mantemento).

## Obxectivo

A fertilización vella (`Fertilizacion`, táboa `fertilizacion`) xa non a usa ningunha pantalla: a sección Fertilización usa os abonados novos (tarefas 047–048b). Esta cola quítaa. Paso 2: as probas de parcelas deixan de usala.

## Ficheiros a tocar

- `tests/services/test_parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_parcelas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 2 — `tests/services/test_parcelas.py`: quitar o servizo vello

Antes:
```python
from horta.services.fertilizacions import crear_fertilizacion
```

Despois:
```python
```

### Paso 3 — `tests/services/test_parcelas.py`: quitar a proba da fertilización vella

Antes:
```python
def test_eliminar_parcela_borra_en_cascada_cultivo_con_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "Orgánica", "Esterco"
    )
    cultivo_id, fertilizacion_id = cultivo.id, fertilizacion.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Fertilizacion, fertilizacion_id) is None


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

As probas de parcelas xa non usan a fertilización vella.

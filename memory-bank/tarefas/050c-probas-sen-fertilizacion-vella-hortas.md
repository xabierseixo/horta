# Tarefa 050c — Probas de hortas sen a fertilización vella

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 050b. **Axente**: qwen-66 (mantemento).

## Obxectivo

A fertilización vella (`Fertilizacion`, táboa `fertilizacion`) xa non a usa ningunha pantalla: a sección Fertilización usa os abonados novos (tarefas 047–048b). Esta cola quítaa. Paso 3: as probas de hortas deixan de usala; a proba de dúas parcelas queda só cos cultivos.

## Ficheiros a tocar

- `tests/services/test_hortas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_hortas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 2 — `tests/services/test_hortas.py`: quitar o servizo vello

Antes:
```python
from horta.services.fertilizacions import crear_fertilizacion
from horta.services.hortas import (
```

Despois:
```python
from horta.services.hortas import (
```

### Paso 3 — `tests/services/test_hortas.py`: quitar a proba da fertilización vella

Antes:
```python
def test_eliminar_horta_borra_en_cascada_fertilizacions(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, datetime.date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    cultivo_id, fertilizacion_id = cultivo.id, fertilizacion.id

    eliminar_horta(session, ana, horta)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Fertilizacion, fertilizacion_id) is None


def test_eliminar_horta_borra_en_cascada_dous_cultivos_con_fertilizacion(session):
```

Despois:
```python
def test_eliminar_horta_borra_en_cascada_dous_cultivos_con_fertilizacion(session):
```

### Paso 4 — `tests/services/test_hortas.py`: dúas parcelas só cos cultivos

Antes:
```python
def test_eliminar_horta_borra_en_cascada_dous_cultivos_con_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela_1 = crear_parcela(session, ana, horta.id, "Parcela Norte")
    parcela_2 = crear_parcela(session, ana, horta.id, "Parcela Sur")
    cultivo_1 = crear_cultivo(session, ana, parcela_1.id, "Tomate")
    cultivo_2 = crear_cultivo(session, ana, parcela_2.id, "Pataca")

    fertilizacion_1 = crear_fertilizacion(
        session, ana, cultivo_1.id, datetime.date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    fertilizacion_2 = crear_fertilizacion(
        session, ana, cultivo_2.id, datetime.date(2026, 4, 2), "cobertoira", "Xurro"
    )

    ids_cultivos = [cultivo_1.id, cultivo_2.id]
    ids_fertilizacions = [fertilizacion_1.id, fertilizacion_2.id]

    eliminar_horta(session, ana, horta)

    for cultivo_id in ids_cultivos:
        assert session.get(Cultivo, cultivo_id) is None
    for fertilizacion_id in ids_fertilizacions:
        assert session.get(Fertilizacion, fertilizacion_id) is None
```

Despois:
```python
def test_eliminar_horta_borra_en_cascada_dous_cultivos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela_1 = crear_parcela(session, ana, horta.id, "Parcela Norte")
    parcela_2 = crear_parcela(session, ana, horta.id, "Parcela Sur")
    cultivo_1 = crear_cultivo(session, ana, parcela_1.id, "Tomate")
    cultivo_2 = crear_cultivo(session, ana, parcela_2.id, "Pataca")
    ids_cultivos = [cultivo_1.id, cultivo_2.id]

    eliminar_horta(session, ana, horta)

    for cultivo_id in ids_cultivos:
        assert session.get(Cultivo, cultivo_id) is None
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As probas de hortas xa non usan a fertilización vella.

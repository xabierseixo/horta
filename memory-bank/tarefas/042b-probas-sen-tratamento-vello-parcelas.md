# Tarefa 042b — Probas de parcelas sen o tratamento vello

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 042.

## Obxectivo

O modelo vello `Tratamento` (táboa `tratamento`) xa non o usa ningunha pantalla: os datos pasaron a `TratamentoFito` (caderno CUE). Esta cola quítao sen perder nada. Paso 2 de 5: as probas de parcelas deixan de usalo.

## Ficheiros a tocar

- `tests/services/test_parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_parcelas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 2 — `tests/services/test_parcelas.py`: quitar o servizo vello

Antes:
```python
from horta.services.tarefas import crear_tarefa
from horta.services.tratamentos import crear_tratamento
```

Despois:
```python
from horta.services.tarefas import crear_tarefa
```

### Paso 3 — `tests/services/test_parcelas.py`: a primeira proba de borrar só mira o cultivo

Antes:
```python
def test_eliminar_parcela_borra_en_cascada_cultivos_e_tratamentos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    cultivo_id, tratamento_id = cultivo.id, tratamento.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None
```

Despois:
```python
def test_eliminar_parcela_borra_en_cascada_cultivos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    cultivo_id = cultivo.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
```

### Paso 4 — `tests/services/test_parcelas.py`: a segunda proba de borrar mira cultivo e fertilización

Antes:
```python
def test_eliminar_parcela_borra_en_cascada_cultivo_con_tratamento_e_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "Orgánica", "Esterco"
    )
    cultivo_id, tratamento_id, fertilizacion_id = cultivo.id, tratamento.id, fertilizacion.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None
    assert session.get(Fertilizacion, fertilizacion_id) is None
```

Despois:
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

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As probas de parcelas xa non usan o modelo vello `Tratamento`.

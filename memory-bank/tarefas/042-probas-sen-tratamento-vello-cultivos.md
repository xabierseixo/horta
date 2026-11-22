# Tarefa 042 — Probas de cultivos sen o tratamento vello

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

O modelo vello `Tratamento` (táboa `tratamento`) xa non o usa ningunha pantalla: os datos pasaron a `TratamentoFito` (caderno CUE). Esta cola quítao sen perder nada. Paso 1 de 5: as probas de cultivos deixan de usalo.

## Ficheiros a tocar

- `tests/services/test_cultivos.py`
- `tests/models/test_cultivo.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_cultivos.py`: importar

Antes:
```python
from horta.models.cultivo import Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Fertilizacion
```

### Paso 2 — `tests/services/test_cultivos.py`: quitar o servizo vello

Antes:
```python
from horta.services.tarefas import crear_tarefa
from horta.services.tratamentos import crear_tratamento, eliminar_tratamento
```

Despois:
```python
from horta.services.tarefas import crear_tarefa
```

### Paso 3 — `tests/services/test_cultivos.py`: a proba de borrar só mira a fertilización

Antes:
```python
def test_eliminar_cultivo_borra_fisicamente_tratamentos_e_fertilizacions(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")

    tratamento_activo = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    tratamento_baixa = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 2), "Pulgón", "Xabón", "Xabier"
    )
    eliminar_tratamento(session, ana, tratamento_baixa)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )

    tratamento_activo_id = tratamento_activo.id
    tratamento_baixa_id = tratamento_baixa.id
    fertilizacion_id = fertilizacion.id

    eliminar_cultivo(session, ana, cultivo)

    assert session.get(Tratamento, tratamento_activo_id) is None
    assert session.get(Tratamento, tratamento_baixa_id) is None
    assert session.get(Fertilizacion, fertilizacion_id) is None
```

Despois:
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

### Paso 4 — `tests/models/test_cultivo.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 5 — `tests/models/test_cultivo.py`: quitar a proba do modelo vello

Antes:
```python
def test_crear_tratamento_con_baixa_por_defecto_false(session):
    parcela = _crear_parcela(session)
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.flush()

    tratamento = Tratamento(
        cultivo_id=cultivo.id,
        data=date(2026, 5, 1),
        praga="Mildeu",
        produto="Cobre",
        aplicador="Xabier",
    )
    session.add(tratamento)
    session.commit()

    atopado = session.query(Tratamento).filter_by(praga="Mildeu").one()
    assert atopado.baixa is False
    assert atopado.cultivo_id == cultivo.id


def test_crear_fertilizacion_con_baixa_por_defecto_false(session):
```

Despois:
```python
def test_crear_fertilizacion_con_baixa_por_defecto_false(session):
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As probas de cultivos xa non usan o modelo vello `Tratamento`.

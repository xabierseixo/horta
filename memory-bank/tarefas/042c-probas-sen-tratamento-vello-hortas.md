# Tarefa 042c — Probas de hortas sen o tratamento vello

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 042b.

## Obxectivo

O modelo vello `Tratamento` (táboa `tratamento`) xa non o usa ningunha pantalla: os datos pasaron a `TratamentoFito` (caderno CUE). Esta cola quítao sen perder nada. Paso 3 de 5: as probas de hortas deixan de usalo. A proba de dúas parcelas queda só con cultivos e fertilizacións.

## Ficheiros a tocar

- `tests/services/test_hortas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_hortas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 2 — `tests/services/test_hortas.py`: quitar o servizo vello

Antes:
```python
from horta.services.tarefas import crear_tarefa
from horta.services.tratamentos import crear_tratamento
```

Despois:
```python
from horta.services.tarefas import crear_tarefa
```

### Paso 3 — `tests/services/test_hortas.py`: quitar a proba de cultivos e tratamentos

Antes:
```python
def test_eliminar_horta_borra_en_cascada_cultivos_e_tratamentos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, datetime.date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    cultivo_id, tratamento_id = cultivo.id, tratamento.id

    eliminar_horta(session, ana, horta)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None


def test_eliminar_horta_borra_en_cascada_fertilizacions(session):
```

Despois:
```python
def test_eliminar_horta_borra_en_cascada_fertilizacions(session):
```

### Paso 4 — `tests/services/test_hortas.py`: dúas parcelas: sen tratamentos vellos

Antes:
```python
def test_eliminar_horta_borra_en_cascada_cultivo_con_tratamento_e_fertilizacion(session):
```

Despois:
```python
def test_eliminar_horta_borra_en_cascada_dous_cultivos_con_fertilizacion(session):
```

### Paso 5 — `tests/services/test_hortas.py`: quitar os tratamentos vellos de dúas parcelas

Antes:
```python
    tratamento_1 = crear_tratamento(
        session, ana, cultivo_1.id, datetime.date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    fertilizacion_1 = crear_fertilizacion(
        session, ana, cultivo_1.id, datetime.date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    tratamento_2 = crear_tratamento(
        session, ana, cultivo_2.id, datetime.date(2026, 5, 2), "Escaravello", "Piretrina", "Xabier"
    )
    fertilizacion_2 = crear_fertilizacion(
        session, ana, cultivo_2.id, datetime.date(2026, 4, 2), "cobertoira", "Xurro"
    )

    ids_cultivos = [cultivo_1.id, cultivo_2.id]
    ids_tratamentos = [tratamento_1.id, tratamento_2.id]
    ids_fertilizacions = [fertilizacion_1.id, fertilizacion_2.id]

    eliminar_horta(session, ana, horta)

    for cultivo_id in ids_cultivos:
        assert session.get(Cultivo, cultivo_id) is None
    for tratamento_id in ids_tratamentos:
        assert session.get(Tratamento, tratamento_id) is None
    for fertilizacion_id in ids_fertilizacions:
```

Despois:
```python
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
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As probas de hortas xa non usan o modelo vello `Tratamento`.

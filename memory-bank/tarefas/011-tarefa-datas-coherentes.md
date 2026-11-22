# Tarefa 011 — A data límite dunha tarefa non pode ser anterior á data prevista

**Estado**: feita

## Obxectivo

Que `crear_tarefa` e `actualizar_tarefa` rexeiten unha `data_limite` anterior á `data`. Ao actualizar, compárase co valor gardado se só cambia unha das dúas datas.

## Ficheiros a tocar

- `src/horta/services/tarefas.py`
- `tests/services/test_tarefas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`: importar o erro de dominio

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```
Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

### Paso 2 — mesmo ficheiro: nova función de validación

Antes:
```python
def crear_tarefa(
```
Despois:
```python
def _validar_datas(data: date | None, data_limite: date | None) -> None:
    if data is not None and data_limite is not None and data_limite < data:
        raise OperacionNonPermitidaError("A data límite non pode ser anterior á data prevista")


def crear_tarefa(
```

### Paso 3 — mesmo ficheiro: chamala ao crear

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    prioridade = campos.pop("prioridade", "media")
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_datas(campos.get("data"), campos.get("data_limite"))
    prioridade = campos.pop("prioridade", "media")
```

### Paso 4 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(tarefa, campo, valor)
```
Despois:
```python
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    _validar_datas(
        cambios.get("data", tarefa.data),
        cambios.get("data_limite", tarefa.data_limite),
    )
    for campo, valor in cambios.items():
        setattr(tarefa, campo, valor)
```

### Paso 5 — `tests/services/test_tarefas.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao **final do ficheiro** (despois da última liña), deixando dúas liñas en branco antes:

```python
def test_data_limite_anterior_ao_crear_tarefa(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A data límite non pode ser anterior"):
        crear_tarefa(
            session,
            ana,
            horta.id,
            "Regar",
            data=date(2026, 5, 10),
            data_limite=date(2026, 5, 1),
        )


def test_data_limite_anterior_ao_actualizar_tarefa(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    tarefa = crear_tarefa(session, ana, horta.id, "Regar", data=date(2026, 5, 10))

    with pytest.raises(ValueError, match="A data límite non pode ser anterior"):
        actualizar_tarefa(session, ana, tarefa, data_limite=date(2026, 5, 1))

    session.refresh(tarefa)
    assert tarefa.data_limite is None
```

## Criterios de aceptación

- Unha data límite anterior á data prevista (ao crear, ou ao actualizar comparando co valor gardado) lanza `OperacionNonPermitidaError`.
- Os tests novos pasan e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- `_validar_datas` en `src/horta/services/tarefas.py` rexeita `data_limite < data` tanto ao crear como ao actualizar (comparando co valor gardado).
- Importada `OperacionNonPermitidaError` de `horta.services.errors`.
- Engadidos 2 tests en `tests/services/test_tarefas.py`: `test_data_limite_anterior_ao_crear_tarefa` e `test_data_limite_anterior_ao_actualizar_tarefa`.
- Comprobacións: `ruff check` ✅, `mypy src` ✅, `pytest` **170 passed**.
- Commit: `30b6c94` — `docs: tarefa 011 para o modelo local`.

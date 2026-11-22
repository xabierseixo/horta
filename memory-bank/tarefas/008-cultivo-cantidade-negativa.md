# Tarefa 008 — Non permitir cantidade colleitada negativa nun cultivo

**Estado**: feita

## Obxectivo

Que `crear_cultivo` e `actualizar_cultivo` rexeiten unha `cantidade` negativa cunha mensaxe clara.

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `tests/services/test_cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: importar o erro de dominio

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
def crear_cultivo(
```
Despois:
```python
def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 0:
            raise OperacionNonPermitidaError("A cantidade non pode ser negativa")


def crear_cultivo(
```

### Paso 3 — mesmo ficheiro: chamala ao crear

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    estado = campos.pop("estado", "planificado")
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    estado = campos.pop("estado", "planificado")
```

### Paso 4 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(cambios)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
```

### Paso 5 — `tests/services/test_cultivos.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao final do ficheiro (despois da última liña, `    assert tarefa.cultivo_id is None`), deixando dúas liñas en branco antes:

```python
def test_cantidade_negativa_ao_crear_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    with pytest.raises(ValueError, match="A cantidade non pode ser negativa"):
        crear_cultivo(session, ana, parcela.id, "Tomate", cantidade=-1.0)


def test_cantidade_negativa_ao_actualizar_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate", cantidade=12.0)

    with pytest.raises(ValueError, match="A cantidade non pode ser negativa"):
        actualizar_cultivo(session, ana, cultivo, cantidade=-3.0)

    session.refresh(cultivo)
    assert cultivo.cantidade == 12.0
```

## Criterios de aceptación

- Crear ou actualizar un cultivo con `cantidade` negativa lanza `OperacionNonPermitidaError` coa mensaxe "A cantidade non pode ser negativa".
- Cantidade 0 ou `None` séguense aceptando.
- Os tests novos pasan e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **`src/horta/services/cultivos.py`**: importado `OperacionNonPermitidaError` de `horta.services.errors`; creada `_validar_cantidade(campos)` que rexeita `cantidade < 0`; chamada en `crear_cultivo` e `actualizar_cultivo` logo de `comprobar_rol_horta`.
- **`tests/services/test_cultivos.py`**: engadidos `test_cantidade_negativa_ao_crear_cultivo` e `test_cantidade_negativa_ao_actualizar_cultivo`.
- **Comprobacións**: `ruff check` — All checks passed. `mypy src` — no issues. `pytest tests/services/test_cultivos.py` — 14 passed.
- **Commit**: `smoth/008-cultivo-cantidade-negativa` co rodapé `Axente: smoth`.

# Tarefa 007 — A cantidade dun animal ten que ser polo menos 1

**Estado**: feita

## Obxectivo

Que `crear_animal` e `actualizar_animal` rexeiten unha `cantidade` menor que 1 cunha mensaxe clara.

## Ficheiros a tocar

- `src/horta/services/animais.py`
- `tests/services/test_animais.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/animais.py`: importar o erro de dominio

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
def crear_animal(
```
Despois:
```python
def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 1:
            raise OperacionNonPermitidaError("A cantidade ten que ser polo menos 1")


def crear_animal(
```

### Paso 3 — mesmo ficheiro: chamala ao crear

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    estado = campos.pop("estado", "activo")
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    estado = campos.pop("estado", "activo")
```

### Paso 4 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
```
Despois:
```python
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(cambios)
    for campo, valor in cambios.items():
```

### Paso 5 — `tests/services/test_animais.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao final do ficheiro (despois da última liña, `    assert animal.cantidade == 6`), deixando dúas liñas en branco antes:

```python
@pytest.mark.parametrize("cantidade", [0, -2])
def test_cantidade_menor_que_un_ao_crear(session, cantidade):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A cantidade ten que ser polo menos 1"):
        crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=cantidade)


def test_cantidade_menor_que_un_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    with pytest.raises(ValueError, match="A cantidade ten que ser polo menos 1"):
        actualizar_animal(session, ana, animal, cantidade=0)

    session.refresh(animal)
    assert animal.cantidade == 6
```

## Criterios de aceptación

- Crear ou actualizar un animal con `cantidade` menor que 1 lanza `OperacionNonPermitidaError` coa mensaxe "A cantidade ten que ser polo menos 1".
- Os tests novos pasan (3 casos) e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Paso 1** — Importación: engadido `from horta.services.errors import OperacionNonPermitidaError` antes de `from horta.services.hortas import comprobar_rol_horta` en `src/horta/services/animais.py`.
- **Paso 2** — Función de validación: engadido `_validar_cantidade(campos)` antes de `crear_animal` en `src/horta/services/animais.py`.
- **Paso 3** — Chamada ao crear: engadido `_validar_cantidade(campos)` despois de `comprobar_rol_horta` en `crear_animal`.
- **Paso 4** — Chamada ao actualizar: engadido `_validar_cantidade(cambios)` despois de `comprobar_rol_horta` en `actualizar_animal`.
- **Paso 5** — Tests: engadidos `test_cantidade_menor_que_un_ao_crear` (2 parametrizados: 0 e -2) e `test_cantidade_menor_que_un_ao_actualizar` ao final de `tests/services/test_animais.py`.
- **Comprobacións**: `uv run ruff check src tests` → All checks passed. `uv run mypy src` → Success. `uv run pytest tests/services/test_animais.py -q` → 11 passed.
- **Commit**: ver abaixo.

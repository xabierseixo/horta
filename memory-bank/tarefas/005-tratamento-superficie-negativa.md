# Tarefa 005 — Non permitir superficie tratada negativa nun tratamento

**Estado**: feita

## Obxectivo

Que `crear_tratamento` e `actualizar_tratamento` rexeiten unha `superficie_tratada` negativa cunha mensaxe clara.

## Ficheiros a tocar

- `src/horta/services/tratamentos.py`
- `tests/services/test_tratamentos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tratamentos.py`: importar o erro de dominio

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
def crear_tratamento(
```
Despois:
```python
def _validar_superficie_tratada(campos: dict[str, Any]) -> None:
    if "superficie_tratada" in campos and campos["superficie_tratada"] is not None:
        if campos["superficie_tratada"] < 0:
            raise OperacionNonPermitidaError("A superficie tratada non pode ser negativa")


def crear_tratamento(
```

### Paso 3 — mesmo ficheiro: chamala ao crear

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    tratamento = Tratamento(
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_superficie_tratada(campos)
    tratamento = Tratamento(
```

### Paso 4 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(tratamento, campo, valor)
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_superficie_tratada(cambios)
    for campo, valor in cambios.items():
        setattr(tratamento, campo, valor)
```

### Paso 5 — `tests/services/test_tratamentos.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao final do ficheiro (despois da última liña, `    assert tratamento.baixa is False`), deixando dúas liñas en branco antes:

```python
def test_superficie_tratada_negativa_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    with pytest.raises(ValueError, match="A superficie tratada non pode ser negativa"):
        crear_tratamento(
            session,
            ana,
            cultivo.id,
            date(2026, 5, 1),
            "Mildeu",
            "Cobre",
            "Xabier",
            superficie_tratada=-1.0,
        )


def test_superficie_tratada_negativa_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session,
        ana,
        cultivo.id,
        date(2026, 5, 1),
        "Mildeu",
        "Cobre",
        "Xabier",
        superficie_tratada=100.0,
    )

    with pytest.raises(ValueError, match="A superficie tratada non pode ser negativa"):
        actualizar_tratamento(session, ana, tratamento, superficie_tratada=-5.0)

    session.refresh(tratamento)
    assert tratamento.superficie_tratada == 100.0
```

## Criterios de aceptación

- Crear ou actualizar un tratamento con `superficie_tratada` negativa lanza `OperacionNonPermitidaError` coa mensaxe "A superficie tratada non pode ser negativa".
- Superficie 0 ou `None` séguense aceptando.
- Os dous tests novos pasan e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Paso 1**: Importación de `OperacionNonPermitidaError` en `src/horta/services/tratamentos.py` (despois de `from horta.services.hortas import comprobar_rol_horta`).
- **Paso 2**: Función `_validar_superficie_tratada` engadida antes de `crear_tratamento`. Rexeita `superficie_tratada < 0` con `OperacionNonPermitidaError`.
- **Paso 3**: Chamada `_validar_superficie_tratada(campos)` engadida en `crear_tratamento` despois de `comprobar_rol_horta`.
- **Paso 4**: Chamada `_validar_superficie_tratada(cambios)` engadida en `actualizar_tratamento` despois de `comprobar_rol_horta`.
- **Paso 5**: Dous tests novos engadidos ao final de `tests/services/test_tratamentos.py`: `test_superficie_tratada_negativa_ao_crear` e `test_superficie_tratada_negativa_ao_actualizar`.

**Comprobacións**:
- `uv run ruff check src tests` → All checks passed!
- `uv run mypy src` → Success: no issues found in 35 source files
- `uv run pytest -q` → 152 passed

**Commit**: `smoth/005-tratamento-superficie-negativa`
- Commit feito por Claude: o modelo local esgotou o tempo antes do commit; código revisado e en verde.

# Tarefa 010 — A data de baixa dun animal non pode ser anterior á de alta

**Estado**: pendente

**Depende de**: tarefa 007 (usa `_validar_cantidade` e o import que engade).

## Obxectivo

Que `crear_animal` e `actualizar_animal` rexeiten unha `data_baixa` anterior á `data_alta`. Ao actualizar, compárase co valor gardado se só cambia unha das dúas datas.

## Ficheiros a tocar

- `src/horta/services/animais.py`
- `tests/services/test_animais.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/animais.py`: nova función de validación

Antes:
```python
def crear_animal(
```
Despois:
```python
def _validar_datas(data_alta: date | None, data_baixa: date | None) -> None:
    if data_alta is not None and data_baixa is not None and data_baixa < data_alta:
        raise OperacionNonPermitidaError("A data de baixa non pode ser anterior á de alta")


def crear_animal(
```

### Paso 2 — mesmo ficheiro: chamala ao crear

Antes:
```python
    _validar_cantidade(campos)
    estado = campos.pop("estado", "activo")
```
Despois:
```python
    _validar_cantidade(campos)
    _validar_datas(data_alta, campos.get("data_baixa"))
    estado = campos.pop("estado", "activo")
```

### Paso 3 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    _validar_cantidade(cambios)
    for campo, valor in cambios.items():
```
Despois:
```python
    _validar_cantidade(cambios)
    _validar_datas(
        cambios.get("data_alta", animal.data_alta),
        cambios.get("data_baixa", animal.data_baixa),
    )
    for campo, valor in cambios.items():
```

### Paso 4 — `tests/services/test_animais.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao **final do ficheiro** (despois da última liña que haxa), deixando dúas liñas en branco antes:

```python
def test_baixa_anterior_a_alta_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A data de baixa non pode ser anterior"):
        crear_animal(
            session,
            ana,
            horta.id,
            "galiñas",
            _DATA_ALTA,
            data_baixa=datetime.date(2026, 1, 1),
        )


def test_baixa_anterior_a_alta_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA)

    with pytest.raises(ValueError, match="A data de baixa non pode ser anterior"):
        actualizar_animal(session, ana, animal, data_baixa=datetime.date(2026, 1, 1))

    session.refresh(animal)
    assert animal.data_baixa is None
```

## Criterios de aceptación

- Unha baixa anterior á alta (ao crear, ou ao actualizar comparando co valor gardado) lanza `OperacionNonPermitidaError` coa mensaxe "A data de baixa non pode ser anterior á de alta".
- Os tests novos pasan e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- Engadida `_validar_datas` en `src/horta/services/animais.py` (antes de `crear_animal`).
- Chamada a `_validar_datas` en `crear_animal` con `data_alta` e `campos.get("data_baixa")`.
- Chamada a `_validar_datas` en `actualizar_animal` con `cambios.get("data_alta", animal.data_alta)` e `cambios.get("data_baixa", animal.data_baixa)`.
- Engadidos 2 tests en `tests/services/test_animais.py`: `test_baixa_anterior_a_alta_ao_crear` e `test_baixa_anterior_a_alta_ao_actualizar`.
- **Comprobacións**: `uv run ruff check src tests` → All checks passed. `uv run mypy src` → Success. `uv run pytest -q` → **168 passed**.
- Commit: `1b8a70c` (antes) → novo commit con rodapé `Axente: smoth`.

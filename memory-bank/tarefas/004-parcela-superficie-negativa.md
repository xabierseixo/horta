# Tarefa 004 — Non permitir superficie negativa nunha parcela

**Estado**: feita

## Obxectivo

Que `crear_parcela` e `actualizar_parcela` rexeiten unha superficie negativa cunha mensaxe clara (agora gárdase sen queixarse).

## Ficheiros a tocar

- `src/horta/services/parcelas.py`
- `tests/services/test_parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/parcelas.py`: nova función de validación

Antes:
```python
            raise OperacionNonPermitidaError("A lonxitude debe estar entre -180 e 180")


def crear_parcela(
```
Despois:
```python
            raise OperacionNonPermitidaError("A lonxitude debe estar entre -180 e 180")


def _validar_superficie(campos: dict[str, Any]) -> None:
    if "superficie" in campos and campos["superficie"] is not None:
        if campos["superficie"] < 0:
            raise OperacionNonPermitidaError("A superficie non pode ser negativa")


def crear_parcela(
```

### Paso 2 — mesmo ficheiro: chamala ao crear

Antes:
```python
    _validar_coordenadas(campos)
    estado = campos.pop("estado", "activa")
```
Despois:
```python
    _validar_coordenadas(campos)
    _validar_superficie(campos)
    estado = campos.pop("estado", "activa")
```

### Paso 3 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    _validar_coordenadas(cambios)
    for campo, valor in cambios.items():
```
Despois:
```python
    _validar_coordenadas(cambios)
    _validar_superficie(cambios)
    for campo, valor in cambios.items():
```

### Paso 4 — `tests/services/test_parcelas.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao final do ficheiro (despois da última liña, `    assert parcela.lon == lon_orixinal`), deixando dúas liñas en branco antes:

```python
def test_superficie_negativa_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A superficie non pode ser negativa"):
        crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=-1.0)


def test_superficie_negativa_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=500.0)

    with pytest.raises(ValueError, match="A superficie non pode ser negativa"):
        actualizar_parcela(session, ana, parcela, superficie=-10.0)

    session.refresh(parcela)
    assert parcela.superficie == 500.0
```

## Criterios de aceptación

- Crear ou actualizar unha parcela con superficie negativa lanza `OperacionNonPermitidaError` coa mensaxe "A superficie non pode ser negativa".
- Superficie 0 ou `None` séguense aceptando.
- Os dous tests novos pasan e os 148 anteriores tamén (150 en total).
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- Engadida a función `_validar_superficie` en `src/horta/services/parcelas.py` (entre `_validar_coordenadas` e `crear_parcela`).
- Chamada a `_validar_superficie` no `crear_parcela` (despois de `_validar_coordenadas`).
- Chamada a `_validar_superficie` no `actualizar_parcela` (despois de `_validar_coordenadas`).
- Engadidos 2 tests: `test_superficie_negativa_ao_crear` e `test_superficie_negativa_ao_actualizar` en `tests/services/test_parcelas.py`.
- Superficie 0 ou `None` aceptáronse (sen queixarse).
- Comprobacións: `ruff check` OK, `mypy` OK, **150 tests pasan** (os 148 anteriores + os 2 novos).
- Commit: `smoth/004-parcela-superficie-negativa` co rodapé `Axente: smoth`.

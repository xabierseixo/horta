# Tarefa 009 — A colleita non pode ser anterior á sementeira

**Estado**: feita

**Depende de**: tarefa 008 (usa o import que engade).

## Obxectivo

Que `crear_cultivo` e `actualizar_cultivo` rexeiten unha `data_colleita_real` anterior á `data_sementeira`. Ao actualizar, compárase co valor que xa ten o cultivo se só cambia unha das dúas datas.

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `tests/services/test_cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: nova función de validación

Antes:
```python
def crear_cultivo(
```
Despois:
```python
def _validar_datas(sementeira: Any, colleita: Any) -> None:
    if sementeira is not None and colleita is not None and colleita < sementeira:
        raise OperacionNonPermitidaError(
            "A data de colleita non pode ser anterior á de sementeira"
        )


def crear_cultivo(
```

### Paso 2 — mesmo ficheiro: chamala ao crear

Antes:
```python
    _validar_cantidade(campos)
    estado = campos.pop("estado", "planificado")
```
Despois:
```python
    _validar_cantidade(campos)
    _validar_datas(campos.get("data_sementeira"), campos.get("data_colleita_real"))
    estado = campos.pop("estado", "planificado")
```

### Paso 3 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    _validar_cantidade(cambios)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
```
Despois:
```python
    _validar_cantidade(cambios)
    _validar_datas(
        cambios.get("data_sementeira", cultivo.data_sementeira),
        cambios.get("data_colleita_real", cultivo.data_colleita_real),
    )
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
```

### Paso 4 — `tests/services/test_cultivos.py`: engadir tres tests ao FINAL do ficheiro

Engade este texto ao final do ficheiro (despois da última liña, `    assert cultivo.cantidade == 12.0`), deixando dúas liñas en branco antes:

```python
def test_colleita_anterior_a_sementeira_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    with pytest.raises(ValueError, match="A data de colleita non pode ser anterior"):
        crear_cultivo(
            session,
            ana,
            parcela.id,
            "Tomate",
            data_sementeira=date(2026, 4, 1),
            data_colleita_real=date(2026, 3, 1),
        )


def test_colleita_anterior_a_sementeira_existente_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(
        session, ana, parcela.id, "Tomate", data_sementeira=date(2026, 4, 1)
    )

    with pytest.raises(ValueError, match="A data de colleita non pode ser anterior"):
        actualizar_cultivo(session, ana, cultivo, data_colleita_real=date(2026, 3, 1))

    session.refresh(cultivo)
    assert cultivo.data_colleita_real is None


def test_colleita_posterior_a_sementeira_acepta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(
        session, ana, parcela.id, "Tomate", data_sementeira=date(2026, 4, 1)
    )

    actualizar_cultivo(session, ana, cultivo, data_colleita_real=date(2026, 8, 15))

    assert cultivo.data_colleita_real == date(2026, 8, 15)
```

## Criterios de aceptación

- Unha colleita anterior á sementeira (ao crear, ou ao actualizar comparando co valor gardado) lanza `OperacionNonPermitidaError`.
- Se falta algunha das dúas datas, non se valida.
- Os tests novos pasan e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Función `_validar_datas`** engadida en `src/horta/services/cultivos.py` (liña 47): rexeita `data_colleita_real < data_sementeira` cando as dúas datas están presentes.
- Chamada ao **crear**: `_validar_datas(campos.get("data_sementeira"), campos.get("data_colleita_real"))` antes de `estado = campos.pop(...)`.
- Chamada ao **actualizar**: `_validar_datas(cambios.get("data_sementeira", cultivo.data_sementeira), cambios.get("data_colleita_real", cultivo.data_colleita_real))` antes de aplicar os cambios. Se só se cambia unha data, compárase co valor que xa ten o cultivo.
- **3 tests novos** en `tests/services/test_cultivos.py`:
  - `test_colleita_anterior_a_sementeira_ao_crear`: rexeita colleita < sementeira ao crear.
  - `test_colleita_anterior_a_sementeira_existente_ao_actualizar`: rexeita colleita < sementeira ao actualizar, mantendo a colleita anterior intacta.
  - `test_colleita_posterior_a_sementeira_acepta`: acepta colleita posterior á sementeira.
- **Comprobacións**: ruff OK, mypy OK, **166 tests pasan** (+22 novos).
- **Commit**: `591fb05 feat: rexeitar colleita anterior á sementeira ao crear e actualizar cultivo (tarefa 009)` (rodapé `Axente: smoth`).

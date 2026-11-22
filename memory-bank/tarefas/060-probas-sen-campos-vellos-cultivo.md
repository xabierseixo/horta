# Tarefa 060 — Probas sen os campos vellos do cultivo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: qwen-66 (mantemento).

## Obxectivo

O cultivo aínda ten cinco campos do deseño antigo que xa non usa ningunha pantalla: data_sementeira, data_plantacion, data_colleita_real, cantidade e unidade (agora hai data_inicio/data_fin e as colleitas son rexistros propios). Paso 1 de 3: as probas deixan de usalos.

## Ficheiros a tocar

- `tests/services/test_cultivos.py`
- `tests/models/test_cultivo.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_cultivos.py`

Antes:
```python
    assert tarefa.cultivo_id is None


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

Despois:
```python
    assert tarefa.cultivo_id is None


```

### Paso 2 — `tests/models/test_cultivo.py`

Antes:
```python
    assert atopado.variedade is None
    assert atopado.data_sementeira is None
```

Despois:
```python
    assert atopado.variedade is None
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As probas xa non usan os campos vellos do cultivo.

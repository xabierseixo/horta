# Tarefa 013 — Un código do catálogo non vale antes da súa data de alta

**Estado**: feita

## Obxectivo

Que `validar_codigo` rexeite un código cuxa `data_alta` sexa posterior á data do tratamento (un código creado despois non se pode usar nun tratamento anterior).

## Ficheiros a tocar

- `src/horta/services/catalogos.py`
- `tests/services/test_catalogos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/catalogos.py`

Antes:
```python
        .filter(CatalogoValor.catalogo == catalogo, CatalogoValor.codigo == codigo,
                _vixente(na_data))
```
Despois:
```python
        .filter(CatalogoValor.catalogo == catalogo, CatalogoValor.codigo == codigo,
                _vixente(na_data),
                or_(CatalogoValor.data_alta.is_(None), CatalogoValor.data_alta <= na_data))
```

### Paso 2 — `tests/services/test_catalogos.py`: engadir un test ao FINAL do ficheiro

Engade este texto ao **final do ficheiro** (despois da última liña que haxa), deixando dúas liñas en branco antes:

```python
def test_codigo_non_vale_antes_da_data_de_alta(session):
    _preparar(session)
    v = session.query(CatalogoVersion).first()
    session.add(CatalogoValor(catalogo="praga", codigo="3", descricion="Nova",
                              version_id=v.id, data_alta=date(2026, 6, 1)))
    session.commit()
    with pytest.raises(OperacionNonPermitidaError, match="non existe ou está de baixa"):
        validar_codigo(session, "praga", "3", date(2026, 5, 1))
    assert validar_codigo(session, "praga", "3", date(2026, 6, 1)).descricion == "Nova"
```

## Criterios de aceptación

- `validar_codigo` falla se a `data_alta` do código é posterior á data indicada, e acepta o código desde a data de alta.
- O test novo pasa e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

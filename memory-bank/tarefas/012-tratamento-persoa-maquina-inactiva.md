# Tarefa 012 — Non permitir aplicadores nin máquinas desactivados nun tratamento

**Estado**: feita

## Obxectivo

Que `crear_tratamento_fito` rexeite unha persoa aplicadora ou unha máquina marcadas como non activas (`activa=False`), cunha mensaxe clara. Hoxe só o evita a pantalla; o servizo debe ser a barreira.

## Ficheiros a tocar

- `src/horta/services/tratamentos_fito.py`
- `tests/services/test_tratamentos_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tratamentos_fito.py`: persoa desactivada

Antes:
```python
            raise _erro("O aplicador indicado non é un aplicador desta horta")
```
Despois:
```python
            raise _erro("O aplicador indicado non é un aplicador desta horta")
        if not persoa.activa:
            raise _erro(f"{persoa.nome} está desactivado/a e non pode figurar como aplicador")
```

### Paso 2 — mesmo ficheiro: máquina desactivada

Antes:
```python
                raise _erro("A máquina indicada non é desta horta")
```
Despois:
```python
                raise _erro("A máquina indicada non é desta horta")
            if not maquina.activa:
                raise _erro(f"A máquina {maquina.alias} está desactivada")
```

### Paso 3 — `tests/services/test_tratamentos_fito.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao **final do ficheiro** (despois da última liña que haxa), deixando dúas liñas en branco antes:

```python
def test_aplicador_desactivado_rexeitase(session):
    from horta.services.persoas import actualizar_persoa

    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    actualizar_persoa(session, ana, xan, activa=False)
    with pytest.raises(OperacionNonPermitidaError, match="está desactivado"):
        crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))


def test_maquina_desactivada_rexeitase(session):
    from horta.services.maquinaria import actualizar_maquina

    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    actualizar_maquina(session, ana, maquina, activa=False)
    with pytest.raises(OperacionNonPermitidaError, match="está desactivada"):
        crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
```

## Criterios de aceptación

- Un aplicador ou unha máquina con `activa=False` fan que `crear_tratamento_fito` lance `OperacionNonPermitidaError`.
- Os dous tests novos pasan e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

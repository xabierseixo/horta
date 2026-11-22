# Tarefa 034 — Ocos entre o deseño e o código (cultivos)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 033.

## Obxectivo

Revisión cruzada do deseño `2026-10-23-cultivo-e-colleitas-design.md` fronte ao código: (1) a superficie tratada non pode superar a do cultivo; (2) a actividade agraria gárdase por defecto como 1 (produción); (3) ao escoller a parcela nun cultivo novo, proponse a superficie libre da parcela e o secano/regadío da parcela.

## Ficheiros a tocar

- `src/horta/services/tratamentos_fito.py`
- `tests/services/test_tratamentos_fito.py`
- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tratamentos_fito.py`: superficie tratada ≤ superficie do cultivo

Antes:
```python
            if parcela.superficie and linha.superficie_ha > parcela.superficie:
                raise _erro(f"A superficie tratada é maior ca da parcela {parcela.nome}")
```

Despois:
```python
            if parcela.superficie and linha.superficie_ha > parcela.superficie:
                raise _erro(f"A superficie tratada é maior ca da parcela {parcela.nome}")
            if cultivo.superficie_ha and linha.superficie_ha > cultivo.superficie_ha:
                raise _erro(f"A superficie tratada é maior ca do cultivo {cultivo.especie}")
```

### Paso 2 — `tests/services/test_tratamentos_fito.py`: engadir ao final do ficheiro

```python
def test_superficie_maior_ca_cultivo_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.1)
    linhas = [LinhaCultivo(cultivo.id, 0.15)]
    with pytest.raises(OperacionNonPermitidaError, match="maior ca do cultivo"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, cultivos=linhas))
```

### Paso 3 — `tests/services/test_tratamentos_fito.py`: importar

Antes:
```python
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
```

Despois:
```python
from horta.services.cultivos import actualizar_cultivo, crear_cultivo, eliminar_cultivo
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`: actividade agraria por defecto (produción)

Antes:
```python
                causa_baixa=causa_baixa.value,
```

Despois:
```python
                causa_baixa=causa_baixa.value,
                actividade_agraria="1",
```

### Paso 5 — mesmo ficheiro: ao escoller a parcela nun cultivo novo, propor a superficie libre e o secano/regadío

Antes:
```python
        cultivo_oficial.on_value_change(cargar_variedades)
```

Despois:
```python
        cultivo_oficial.on_value_change(cargar_variedades)

        def propor_da_parcela() -> None:
            if editando["id"] is not None or parcela.value is None:
                return
            p = next(x for x in parcelas if x.id == parcela.value)
            if p.secano_regadio is not None:
                secano.value = "R" if p.secano_regadio.value == "regadio" else "S"
            if superficie.ha is None and p.superficie:
                ocupada = sum(c.superficie_ha or 0 for c in cultivos
                              if c.parcela_id == p.id and c.estado != "rematado")
                if p.superficie - ocupada > 0:
                    superficie.establecer(round(p.superficie - ocupada, 4))

        parcela.on_value_change(propor_da_parcela)
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

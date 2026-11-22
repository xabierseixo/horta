# Tarefa 071e — Limpeza: quitar cabe_no_formulario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 071c e o borrado da pantalla vella (feito por Claude). **Axente**: qwen-66 (limpeza).

## Obxectivo

O diálogo novo de tratamentos edita calquera tratamento, así que a función cabe_no_formulario xa non se usa en ningures. Quitala do servizo.

## Ficheiros a tocar

- `src/horta/services/tratamentos_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
    return tratamento


def cabe_no_formulario(tratamento: TratamentoFito) -> bool:
    """Se o formulario simple da app pode editalo sen borrar ningún dato."""
    return (len(tratamento.cultivos) <= 1 and len(tratamento.problemas) <= 1
            and len(tratamento.xustificacions) <= 1 and len(tratamento.produtos) <= 1
            and len(tratamento.aplicadores) <= 1 and not tratamento.medidas
            and tratamento.asesor is None and tratamento.actividade_cuberta is None)


```

Despois:
```python
    return tratamento


```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O servizo de tratamentos xa non ten cabe_no_formulario.

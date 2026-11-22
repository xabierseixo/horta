# Tarefa 075t — Formularios con quen (8/8): sementeira, editar e propor

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075s. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Ao editar un cultivo vense quen sementou e as horas; nun cultivo novo proponse quen fixo o último traballo. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 2 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                    data_adquisicion, castineiros, abeleiras, nogueiras, amendoeiras, outros_casca)
```

Despois:
```python
                    data_adquisicion, castineiros, abeleiras, nogueiras, amendoeiras, outros_casca,
                    horas_sementeira)
```

### Paso 3 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            tipo_inicio.value = "sementeira"
```

Despois:
```python
            tipo_inicio.value = "sementeira"
            quen.value = proposta_quen(horta_id)
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        data_inicio.value = _texto(c.data_inicio)
```

Despois:
```python
        data_inicio.value = _texto(c.data_inicio)
        quen.value = c.sementeira_persoa_id if c.sementeira_persoa_id in persoas else None
        horas_sementeira.value = "" if c.sementeira_horas is None else f"{c.sementeira_horas:g}"
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (8/8): sementeira, editar e propor: feito.

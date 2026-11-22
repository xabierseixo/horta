# Tarefa 041 — Saber se un tratamento cabe no formulario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

Para poder editar tratamentos (tarefa 041b) sen perder datos: o formulario da app só ten un cultivo, un problema, unha xustificación, un produto e un aplicador, e non mostra medidas, asesor nin actividade en cuberta. A función `cabe_no_formulario` di se un tratamento se pode editar alí sen borrar nada. Revisión 2026-10-24, oco 1.

## Ficheiros a tocar

- `src/horta/services/tratamentos_fito.py`
- `tests/services/test_tratamentos_fito_formulario.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tratamentos_fito.py`: a función

Antes:
```python
def dar_de_baixa_tratamento_fito(
```

Despois:
```python
def cabe_no_formulario(tratamento: TratamentoFito) -> bool:
    """Se o formulario simple da app pode editalo sen borrar ningún dato."""
    return (len(tratamento.cultivos) <= 1 and len(tratamento.problemas) <= 1
            and len(tratamento.xustificacions) <= 1 and len(tratamento.produtos) <= 1
            and len(tratamento.aplicadores) <= 1 and not tratamento.medidas
            and tratamento.asesor is None and tratamento.actividade_cuberta is None)


def dar_de_baixa_tratamento_fito(
```

### Paso 2 — crear o ficheiro `tests/services/test_tratamentos_fito_formulario.py`

Contido completo:
```python
from datetime import date

import horta.models  # noqa: F401
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoMedida
from horta.services.tratamentos_fito import cabe_no_formulario


def _tratamento() -> TratamentoFito:
    return TratamentoFito(horta_id=1, data_inicio=date(2026, 5, 1), data_fin=date(2026, 5, 1))


def test_un_cultivo_cabe_no_formulario():
    t = _tratamento()
    t.cultivos = [TratamentoCultivo(cultivo_id=1)]
    assert cabe_no_formulario(t)


def test_dous_cultivos_non_caben():
    t = _tratamento()
    t.cultivos = [TratamentoCultivo(cultivo_id=1), TratamentoCultivo(cultivo_id=2)]
    assert not cabe_no_formulario(t)


def test_con_medidas_non_cabe():
    t = _tratamento()
    t.medidas = [TratamentoMedida(tipo_medida="1")]
    assert not cabe_no_formulario(t)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

`cabe_no_formulario(tratamento)` di se o tratamento se pode editar no formulario da app.

# Tarefa 079b — Produción dos animais (3/11): lotes compartidos coas colleitas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Un lote de colleita non pode repetir un lote da produción dos animais, nin ao revés. Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/colleitas.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.services.persoas import comprobar_quen
from horta.services.producions_animais import lotes_da_horta
```

### Paso 2 — `src/horta/services/colleitas.py`

Antes:
```python
    consulta = (
        session.query(Colleita.lote)
        .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
    )
    if excepto_id is not None:
        consulta = consulta.filter(Colleita.id != excepto_id)
    return {lote for (lote,) in consulta}
```

Despois:
```python
    """Os lotes da explotación, tamén os da produción dos animais."""
    return lotes_da_horta(session, horta_id, excepto_colleita=excepto_id)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (3/11): lotes compartidos coas colleitas: feito.

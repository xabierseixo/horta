# Tarefa 079d — Produción dos animais (5/11): no Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Diario mostra a produción dos animais co produto, a cantidade, o retirado, o lote e quen. Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/diario.py`

Antes:
```python
from horta.services.movementos_animais import TIPOS_MOVEMENTO, listar_movementos
```

Despois:
```python
from horta.services.movementos_animais import TIPOS_MOVEMENTO, listar_movementos
from horta.services.producions_animais import PRODUTOS, listar_producions
```

### Paso 2 — `src/horta/services/diario.py`

Antes:
```python
    "movemento_animal": "Entrada ou saída de animais",
```

Despois:
```python
    "movemento_animal": "Entrada ou saída de animais",
    "producion_animal": "Produción dos animais",
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
                                  persoas=_quen(mo.persoa_id), sen_quen=mo.persoa_id is None))
```

Despois:
```python
                                  persoas=_quen(mo.persoa_id), sen_quen=mo.persoa_id is None))
    for pr in listar_producions(session, actor, horta_id):
        retirada = f" ({pr.retirada:g} retirados)" if pr.retirada else ""
        traballos.append(Traballo("producion_animal", pr.id, pr.data, True,
                                  f"{PRODUTOS[pr.produto]}: {pr.cantidade:g} {pr.unidade}"
                                  f"{retirada} · lote {pr.lote}",
                                  grupos.get(pr.animal_id, ""), frozenset(),
                                  persoas=_quen(pr.persoa_id), sen_quen=pr.persoa_id is None))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (5/11): no Diario: feito.

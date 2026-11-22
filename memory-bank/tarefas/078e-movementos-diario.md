# Tarefa 078e — Entradas e saídas de animais (6/11): no Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 078c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Diario mostra as entradas e saídas de animais (sen os movementos iniciais) co grupo e quen o fixo. Deseño: `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/diario.py`

Antes:
```python
from horta.services.labores import listar_labores
```

Despois:
```python
from horta.services.labores import listar_labores
from horta.services.movementos_animais import TIPOS_MOVEMENTO, listar_movementos
```

### Paso 2 — `src/horta/services/diario.py`

Antes:
```python
    "coidado_animal": "Coidado de animais",
```

Despois:
```python
    "coidado_animal": "Coidado de animais",
    "movemento_animal": "Entrada ou saída de animais",
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
                                  persoas=_quen(co.persoa_id), sen_quen=co.persoa_id is None))
```

Despois:
```python
                                  persoas=_quen(co.persoa_id), sen_quen=co.persoa_id is None))
    for mo in listar_movementos(session, actor, horta_id):
        traballos.append(Traballo("movemento_animal", mo.id, mo.data, True,
                                  f"{TIPOS_MOVEMENTO[mo.tipo].split(' (')[0]}: {mo.cantidade}",
                                  grupos.get(mo.animal_id, ""), frozenset(),
                                  persoas=_quen(mo.persoa_id), sen_quen=mo.persoa_id is None))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Entradas e saídas de animais (6/11): no Diario: feito.

# Tarefa 080d — Pastoreo (5/11): no Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 080a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Diario mostra o pastoreo cos animais, as leiras e se seguen no pasto. Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

## Ficheiros a tocar

- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/diario.py`

Antes:
```python
from horta.services.animais import listar_animais
from horta.services.catalogos import describir
from horta.services.coidados_animais import TIPOS_COIDADO, listar_coidados
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import listar_cultivos
from horta.services.labores import listar_labores
from horta.services.movementos_animais import TIPOS_MOVEMENTO, listar_movementos
```

Despois:
```python
from horta.services.animais import ESPECIES, listar_animais
from horta.services.catalogos import describir
from horta.services.coidados_animais import TIPOS_COIDADO, listar_coidados
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import listar_cultivos
from horta.services.labores import listar_labores
from horta.services.movementos_animais import TIPOS_MOVEMENTO, listar_movementos
from horta.services.pastoreos import listar_pastoreos
```

### Paso 2 — `src/horta/services/diario.py`

Antes:
```python
    "producion_animal": "Produción dos animais",
```

Despois:
```python
    "producion_animal": "Produción dos animais",
    "pastoreo": "Pastoreo",
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
                                  persoas=_quen(pr.persoa_id), sen_quen=pr.persoa_id is None))
```

Despois:
```python
                                  persoas=_quen(pr.persoa_id), sen_quen=pr.persoa_id is None))
    for pa in listar_pastoreos(session, actor, horta_id):
        animais = ", ".join(
            f"{li.numero} {grupos.get(li.animal_id, '')}" if li.animal_id else
            f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} ({li.rega})"
            for li in pa.animais)
        ata_cando = f"ata o {pa.data_fin:%d/%m/%Y}" if pa.data_fin else "aínda no pasto"
        ids = [le.cultivo_id for le in pa.leiras]
        traballos.append(Traballo("pastoreo", pa.id, pa.data_inicio, True,
                                  f"{animais} · {ata_cando}",
                                  onde(ids[0]) if len(ids) == 1 else f"{len(ids)} leiras",
                                  frozenset().union(*(parcela_de(i) for i in ids)),
                                  persoas=_quen(pa.persoa_id), sen_quen=pa.persoa_id is None))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (5/11): no Diario: feito.

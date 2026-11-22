# Tarefa 083a — Lotes (2/5): saídas no Diario e nas tarefas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 083. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Diario mostra as saídas dos lotes e unha tarefa pode ser unha saída de produto. Deseño: `docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md` (paso 4 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/services/diario.py`
- `src/horta/services/tarefas.py`

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
from horta.services.lotes import CANLES, TIPOS_SAIDA, listar_lotes, listar_saidas
```

### Paso 2 — `src/horta/services/diario.py`

Antes:
```python
    "pastoreo": "Pastoreo",
```

Despois:
```python
    "pastoreo": "Pastoreo",
    "lote_saida": "Saída de produto (venda, casa...)",
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
                                  persoas=_quen(pa.persoa_id), sen_quen=pa.persoa_id is None))
```

Despois:
```python
                                  persoas=_quen(pa.persoa_id), sen_quen=pa.persoa_id is None))
    lotes = {lo.id: lo for lo in listar_lotes(session, actor, horta_id)}
    for sa in listar_saidas(session, actor, horta_id):
        lote = lotes.get(sa.lote_id)
        produto = f" de {lote.produto}" if lote else ""
        codigo = f" · lote {lote.codigo}" if lote else ""
        traballos.append(Traballo(
            "lote_saida", sa.id, sa.data, True,
            f"{TIPOS_SAIDA[sa.tipo].split(' (')[0]}: {sa.cantidade:g} {sa.unidade}{produto}"
            f"{codigo}",
            nomes.get(sa.comprador_id or 0) or sa.lugar or CANLES.get(sa.canle or "", "") or "",
            frozenset(), persoas=_quen(sa.persoa_id), sen_quen=sa.persoa_id is None))
```

### Paso 4 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.labor import Labor
```

Despois:
```python
from horta.models.labor import Labor
from horta.models.lote import LoteSaida
```

### Paso 5 — `src/horta/services/tarefas.py`

Antes:
```python
    "pastoreo": (Pastoreo, "data_inicio"),
```

Despois:
```python
    "pastoreo": (Pastoreo, "data_inicio"),
    "lote_saida": (LoteSaida, "data"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Lotes (2/5): saídas no Diario e nas tarefas: feito.

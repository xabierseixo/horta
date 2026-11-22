# Tarefa 052c — Balance de nutrientes en Fertilización

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 052. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Enriba da táboa de Fertilización, unha liña por cultivo con abonados ou con plan: «Pataca: N 60 de 120 · P₂O₅ 60 · K₂O 60 kg/ha». Se hai abonados líquidos sen densidade, avísase de que non se contan. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §4. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/ui/pages/abonados.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/abonados.py`: importar

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_persoas
from horta.services.plan_abonado import balance_do_cultivo
```

### Paso 2 — `src/horta/ui/pages/abonados.py`: calcular os balances

Antes:
```python
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in listar_cultivos(session, actor, horta_id)}
```

Despois:
```python
        lista_cultivos = listar_cultivos(session, actor, horta_id)
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in lista_cultivos}
        abonados_cultivos = {a.cultivo_id for a in abonados}
        balances = {c.id: balance_do_cultivo(session, actor, horta_id, c) for c in lista_cultivos
                    if c.id in abonados_cultivos or c.plan_necesidade_n}
```

### Paso 3 — `src/horta/ui/pages/abonados.py`: mostralos enriba da táboa

Antes:
```python
    taboa = ui.table(
```

Despois:
```python
    for cultivo_id, balance in balances.items():
        partes = []
        for nome, feito, preciso in zip(("N", "P₂O₅", "K₂O"), balance.aplicado,
                                        balance.necesidade):
            if feito or preciso:
                partes.append(f"{nome} {feito:g}" + (f" de {preciso:g}" if preciso else ""))
        aviso = (f" (sen contar {balance.sen_calcular}: falta a densidade)"
                 if balance.sen_calcular else "")
        ui.label(f"{cultivos[cultivo_id]}: {' · '.join(partes) or 'nada'} kg/ha{aviso}").classes(
            "text-body2")
    taboa = ui.table(
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Fertilización mostra o aplicado fronte ao plan de cada cultivo.

# Tarefa 052b — Plan de abonado no diálogo do cultivo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 052. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No apartado «Plan de abonado» do cultivo pódense apuntar as necesidades (N, P₂O₅, K₂O en kg/ha), a data do plan, se se calculou cunha ferramenta e os nutrientes da auga de rega. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §4. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/cultivos.py`: plan de abonado

Antes:
```python
            obxectivo = ui.input("Colleita esperada (kg/ha)").classes("w-full")
```

Despois:
```python
            obxectivo = ui.input("Colleita esperada (kg/ha)").classes("w-full")
            ui.label("Necesidades do cultivo (kg/ha)").classes("text-caption")
            with ui.row().classes("w-full no-wrap"):
                necesidade_n = ui.input("N").classes("col")
                necesidade_p = ui.input("P₂O₅").classes("col")
                necesidade_k = ui.input("K₂O").classes("col")
            plan_data = campo_data("Data do plan")
            ferramenta = ui.checkbox("Calculouse cunha ferramenta de nutrientes")
            auga_n = ui.input("Nitróxeno nítrico da auga de rega (mg/l)").classes("w-full")
            auga_p = ui.input("P₂O₅ da auga de rega (mg/l)").classes("w-full")
```

### Paso 2 — `src/horta/ui/pages/cultivos.py`: plan de abonado

Antes:
```python
                obxectivo_colleita_kg_ha=parsear_decimal(obxectivo.value),
```

Despois:
```python
                obxectivo_colleita_kg_ha=parsear_decimal(obxectivo.value),
                plan_necesidade_n=parsear_decimal(necesidade_n.value),
                plan_necesidade_p2o5=parsear_decimal(necesidade_p.value),
                plan_necesidade_k2o=parsear_decimal(necesidade_k.value),
                plan_data=parsear_data(plan_data.value),
                plan_ferramenta_sostibilidade=ferramenta.value,
                plan_auga_n_nitrico=parsear_decimal(auga_n.value),
                plan_auga_p2o5=parsear_decimal(auga_p.value),
```

### Paso 3 — `src/horta/ui/pages/cultivos.py`: plan de abonado

Antes:
```python
                    ano_plantacion, unidades, ciclos, duracion, obxectivo, notas,
```

Despois:
```python
                    ano_plantacion, unidades, ciclos, duracion, obxectivo, notas,
                    necesidade_n, necesidade_p, necesidade_k, plan_data, auga_n, auga_p,
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`: plan de abonado

Antes:
```python
    casillas = (sementeira_directa, material_tratado, material_adquirido)
```

Despois:
```python
    casillas = (sementeira_directa, material_tratado, material_adquirido, ferramenta)
```

### Paso 5 — `src/horta/ui/pages/cultivos.py`: plan de abonado

Antes:
```python
        obxectivo.value = _texto(c.obxectivo_colleita_kg_ha)
```

Despois:
```python
        obxectivo.value = _texto(c.obxectivo_colleita_kg_ha)
        necesidade_n.value = _texto(c.plan_necesidade_n)
        necesidade_p.value = _texto(c.plan_necesidade_p2o5)
        necesidade_k.value = _texto(c.plan_necesidade_k2o)
        plan_data.value = _texto(c.plan_data)
        ferramenta.value = bool(c.plan_ferramenta_sostibilidade)
        auga_n.value = _texto(c.plan_auga_n_nitrico)
        auga_p.value = _texto(c.plan_auga_p2o5)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O diálogo do cultivo garda e mostra o plan de abonado.

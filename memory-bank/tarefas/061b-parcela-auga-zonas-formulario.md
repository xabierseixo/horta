# Tarefa 061b — Parcelas: auga e zonas no formulario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 061. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No diálogo da parcela, o apartado «Auga para consumo humano e zonas protexidas». Probado no navegador o 2026-10-25. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
                                    clearable=True).classes("w-full")
```

Despois:
```python
                                    clearable=True).classes("w-full")
        with ui.expansion("Auga para consumo humano e zonas protexidas").classes("w-full"):
            auga = ui.checkbox("Hai un pozo ou toma de auga para consumo humano na parcela "
                               "ou preto")
            with ui.column().classes("w-full gap-1").bind_visibility_from(auga, "value"):
                auga_dentro = ui.checkbox("Está dentro da parcela")
                auga_distancia = ui.input("Distancia á parcela (m)").classes("w-full")
                auga_utm = ui.input("Coordenadas UTM (opcional)").classes("w-full")
                auga_nome = ui.input("Nome do pozo ou da masa de auga").classes("w-full")
            zona = ui.select({"total": "Toda a parcela", "parcial": "Parte da parcela"},
                             label="Está nunha zona protexida (captación, hábitats, especies)",
                             clearable=True).classes("w-full")
            zona_ha = ui.input("Superficie afectada (ha), se se sabe").classes("w-full")
```

### Paso 2 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
                notas=notas.value or None,
```

Despois:
```python
                notas=notas.value or None,
                auga_consumo=auga.value, auga_consumo_na_parcela=auga_dentro.value,
                auga_consumo_distancia_m=parsear_decimal(auga_distancia.value),
                auga_consumo_utm=auga_utm.value or None,
                auga_consumo_denominacion=auga_nome.value or None,
                zona_especifica=zona.value, zona_especifica_ha=parsear_decimal(zona_ha.value),
```

### Paso 3 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
              *sigpac.values())
    selectores = (secano, orixe_auga, tenencia, causa_baixa)
```

Despois:
```python
              auga_distancia, auga_utm, auga_nome, zona_ha, *sigpac.values())
    selectores = (secano, orixe_auga, tenencia, causa_baixa, zona)
```

### Paso 4 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
        pequena.value = False
```

Despois:
```python
        pequena.value = auga.value = auga_dentro.value = False
```

### Paso 5 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
        notas.value = _texto(p.notas)
```

Despois:
```python
        notas.value = _texto(p.notas)
        auga.value, auga_dentro.value = p.auga_consumo, p.auga_consumo_na_parcela
        auga_distancia.value = _texto(p.auga_consumo_distancia_m)
        auga_utm.value = _texto(p.auga_consumo_utm)
        auga_nome.value = _texto(p.auga_consumo_denominacion)
        zona.value = p.zona_especifica
        zona_ha.value = _texto(p.zona_especifica_ha)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense apuntar os pozos e as zonas protexidas de cada parcela.

# Tarefa 044 — Ver o rendemento (kg/ha) en Colleitas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

`rendemento_kg_ha` xa se calculaba pero non se vía en ningures. Agora a sección Colleitas mostra enriba da táboa unha liña por cultivo con colleitas: "Pataca: 2400 kg/ha". Serve ao agricultor para comparar campañas e, máis adiante, para o plan de empresa (produción esperada). Só sae cando se pode calcular (cultivo con superficie e colleitas en kg ou t). Revisión 2026-10-24, oco 6.

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`: importar

Antes:
```python
    propor_lote,
)
```

Despois:
```python
    propor_lote,
    rendemento_kg_ha,
)
```

### Paso 2 — mesmo ficheiro: calcular o rendemento dos cultivos con colleitas

Antes:
```python
        restos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_restos")}
```

Despois:
```python
        restos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_restos")}
        con_colleitas = {c.cultivo_id for c in colleitas}
        rendementos = {c.id: rendemento_kg_ha(session, actor, c.id)
                       for c in cultivos if c.id in con_colleitas}
```

### Paso 3 — mesmo ficheiro: mostralo enriba da táboa

Antes:
```python
    taboa = ui.table(
```

Despois:
```python
    with ui.row().classes("gap-4"):
        for cultivo_id, kg_ha in rendementos.items():
            if kg_ha is not None:
                ui.label(f"{nome_cultivo[cultivo_id]}: {kg_ha:.0f} kg/ha").classes("text-body2")
    taboa = ui.table(
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Na sección Colleitas vese o rendemento en kg/ha de cada cultivo con colleitas.

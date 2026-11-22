# Tarefa 074p — Menú novo: Inicio, Diario, Informes e Explotación

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074o. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Menú: Inicio, Diario, Informes e o grupo Explotación (parcelas, cultivos, animais, equipo, maquinaria e datos da explotación). As táboas de cada tipo de traballo saen do menú e ábrense desde o Diario. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/layout.py`
- `tests/ui/test_layout.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/layout.py`

Antes:
```python
    so_admin_horta: bool = False
```

Despois:
```python
    so_admin_horta: bool = False
    no_menu: bool = False
```

### Paso 2 — `src/horta/ui/layout.py`

Antes:
```python
    Seccion("resumo", "Resumo", "dashboard", None),
    Seccion("parcelas", "Parcelas", "map", "Terra"),
    Seccion("cultivos", "Cultivos", "spa", "Terra"),
    Seccion("tratamentos", "Tratamentos", "sanitizer", "Caderno"),
    Seccion("fertilizacion", "Fertilización", "compost", "Caderno"),
    Seccion("rega", "Rega", "water_drop", "Caderno"),
    Seccion("labores", "Labores", "grass", "Caderno"),
    Seccion("analises", "Análises", "science", "Caderno"),
    Seccion("colleitas", "Colleitas", "inventory_2", "Caderno"),
    Seccion("tarefas", "Tarefas", "task_alt", "Caderno"),
    Seccion("animais", "Animais", "pets", "Gandaría"),
    Seccion("equipo", "Equipo", "groups", "Equipo"),
    Seccion("maquinaria", "Maquinaria", "agriculture", "Equipo"),
```

Despois:
```python
    Seccion("resumo", "Inicio", "home", None),
    Seccion("diario", "Diario", "event_note", None),
    Seccion("informes", "Informes", "description", None),
    Seccion("parcelas", "Parcelas", "map", "Explotación"),
    Seccion("cultivos", "Cultivos", "spa", "Explotación"),
    Seccion("animais", "Animais", "pets", "Explotación"),
    Seccion("equipo", "Equipo", "groups", "Explotación"),
    Seccion("maquinaria", "Maquinaria", "agriculture", "Explotación"),
    Seccion("explotacion", "Datos da explotación", "store", "Explotación", so_admin_horta=True),
    # A táboa de cada tipo de traballo: fóra do menú, chégase desde o Diario
    Seccion("tratamentos", "Tratamentos", "sanitizer", None, no_menu=True),
    Seccion("fertilizacion", "Abonados", "compost", None, no_menu=True),
    Seccion("rega", "Regas", "water_drop", None, no_menu=True),
    Seccion("labores", "Labores", "grass", None, no_menu=True),
    Seccion("analises", "Tomas de mostras", "science", None, no_menu=True),
    Seccion("colleitas", "Colleitas", "inventory_2", None, no_menu=True),
    Seccion("tarefas", "Tarefas", "task_alt", None, no_menu=True),
```

### Paso 3 — `src/horta/ui/layout.py`

Antes:
```python
    return [s for s in SECCIONS if e_horta_admin or not s.so_admin_horta]
```

Despois:
```python
    """As do menú: as táboas de cada tipo de traballo ábrense desde o Diario."""
    return [s for s in SECCIONS if (e_horta_admin or not s.so_admin_horta) and not s.no_menu]
```

### Paso 4 — `tests/ui/test_layout.py`

Antes:
```python
    assert grupos == ["Terra", "Caderno", "Gandaría", "Equipo"]
```

Despois:
```python
    assert grupos == ["Explotación"]


def test_menu_de_traballos_e_informes():
    claves = [s.clave for s in seccions_visibles(e_horta_admin=False)]
    assert claves[:3] == ["resumo", "diario", "informes"]
    assert "tratamentos" not in claves and "explotacion" not in claves
    assert normalizar_seccion("tratamentos") == "tratamentos"
    assert "explotacion" in [s.clave for s in seccions_visibles(e_horta_admin=True)]
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Menú novo: Inicio, Diario, Informes e Explotación: feito.

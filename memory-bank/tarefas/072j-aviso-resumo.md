# Tarefa 072j — Resumo: aviso dos catálogos para a administración

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072i. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na sección Resumo, a administración global ve os avisos dos catálogos (faltan, máis de 60 días sen revisar, fallou o MAPA) cunha ligazón á pantalla. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    listar_animais,
)
```

Despois:
```python
    listar_animais,
)
from horta.services.catalogos_estado import avisos_catalogos
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        e_admin_global = actor.rol == RolGlobal.ADMIN
```

Despois:
```python
        e_admin_global = actor.rol == RolGlobal.ADMIN
        avisos_admin = avisos_catalogos(session) if e_admin_global else []
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        ui.label(texto_estado).classes(clase_estado)
```

Despois:
```python
        ui.label(texto_estado).classes(clase_estado)
        for aviso in avisos_admin:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(aviso)
                ui.link("Catálogos oficiais", "/admin/catalogos")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Resumo: aviso dos catálogos para a administración: feito.

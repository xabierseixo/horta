# Tarefa 074q — Páxina da explotación: Inicio, Diario, Informes e Datos da explotación

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074p. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

A páxina da explotación mostra o Diario, os Informes e os Datos da explotación; o Inicio leva «Apuntar traballo». Probado no navegador (escritorio e móbil) o 2026-10-26. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.descarga_caderno import boton_caderno
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.pages.equipo import seccion_equipo
```

Despois:
```python
from horta.ui.pages.diario import Formularios, boton_apuntar_traballo, seccion_diario
from horta.ui.pages.equipo import seccion_equipo
from horta.ui.pages.informes import seccion_informes
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    etiquetas = {s.clave: s.etiqueta for s in SECCIONS}
    if seccion == "resumo":
        accions = cabeceira_seccion(horta_nome, horta_descricion or "Resumo da explotación")
        with accions:
            boton_caderno(horta_id)
        if e_horta_admin:
            with accions:
                ui.button(
                    "Configurar explotación", icon="settings", on_click=dialog_config_horta.open
                ).props("outline")
                boton_datos_caderno(horta_id)
```

Despois:
```python
    seccions = {s.clave: s for s in SECCIONS}
    if seccion == "resumo":
        accions = cabeceira_seccion(horta_nome, horta_descricion or "Inicio")
        if pode_editar:
            with accions:
                boton_apuntar_traballo(Formularios(horta_id))
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    cabeceira_seccion(etiquetas[seccion], horta_nome)
    if seccion == "parcelas":
```

Despois:
```python
    if seccions[seccion].no_menu:
        ui.link("← Diario", url_seccion(horta_id, "diario")).classes("text-caption")
    cabeceira_seccion(seccions[seccion].etiqueta, horta_nome)
    if seccion == "diario":
        seccion_diario(horta_id, pode_editar)
    elif seccion == "informes":
        seccion_informes(horta_id, horta_uso_profesional)
    elif seccion == "explotacion" and e_horta_admin:
        ui.label({"rexistrada": "Explotación rexistrada", "en_preparacion": "En preparación",
                  "non_profesional": "Non profesional"}[estado]).classes("q-mb-md")
        with ui.row().classes("gap-2"):
            ui.button("Configurar explotación", icon="settings",
                      on_click=dialog_config_horta.open).props("outline")
            boton_datos_caderno(horta_id)
    elif seccion == "parcelas":
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Páxina da explotación: Inicio, Diario, Informes e Datos da explotación: feito.

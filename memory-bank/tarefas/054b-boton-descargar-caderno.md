# Tarefa 054b — Botón «Descargar o caderno»

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 054. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No Resumo da explotación, un botón abre un diálogo co período (por defecto do 1 de xaneiro a hoxe) e descarga o Excel do caderno. Fontes: modelo oficial da Xunta (7/8/2026) e obrigas en `docs/referencia/caderno/README.md`. Non hai data de presentación: exportarse cando se queira, para o período escollido. Probado no navegador o 2026-10-25.

## Ficheiros a tocar

- `src/horta/ui/descarga_caderno.py` (**ficheiro novo**)
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/descarga_caderno.py`

Contido completo:
```python
"""Botón «Descargar o caderno»: Excel co modelo oficial da Xunta para o período escollido."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.caderno import xerar_caderno
from horta.services.errors import OperacionNonPermitidaError
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual


def boton_caderno(horta_id: int) -> None:
    hoxe = date.today()
    with ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
        ui.label("Descargar o caderno de explotación").classes("text-h6")
        ui.label("Excel co modelo oficial da Xunta. Podes descargalo cando queiras, "
                 "para o período que necesites.").classes("text-caption")
        desde = campo_data("Desde", date(hoxe.year, 1, 1).isoformat())
        ata = campo_data("Ata", hoxe.isoformat())

        def descargar() -> None:
            inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
            if inicio is None or fin is None:
                ui.notify("Indica as dúas datas", type="warning")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                try:
                    datos = xerar_caderno(session, actor, horta_id, inicio, fin)
                except OperacionNonPermitidaError as erro:
                    ui.notify(str(erro), type="negative")
                    return
            ui.download.content(datos, f"caderno-{inicio:%Y%m%d}-{fin:%Y%m%d}.xlsx")
            dialogo.close()

        with ui.row():
            ui.button("Descargar", icon="download", on_click=descargar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")
    ui.button("Descargar o caderno", icon="download", on_click=dialogo.open).props("outline")
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`: importar

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.descarga_caderno import boton_caderno
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`: botón no resumo

Antes:
```python
        accions = cabeceira_seccion(horta_nome, horta_descricion or "Resumo da explotación")
```

Despois:
```python
        accions = cabeceira_seccion(horta_nome, horta_descricion or "Resumo da explotación")
        with accions:
            boton_caderno(horta_id)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Desde o Resumo pódese descargar o caderno para calquera período.

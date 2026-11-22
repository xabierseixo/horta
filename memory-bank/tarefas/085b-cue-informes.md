# Tarefa 085b — CUE (3/3): en Informes

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 085a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Informes → Caderno dixital (CUE): descargar o Excel para o XEAGA e os datos en JSON, e ver o que falta por traballo. Probado no navegador (móbil) o 2026-10-29. Deseño: `docs/superpowers/specs/2026-10-29-cue-design.md` (paso 6 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/descarga_cue.py` (**ficheiro novo**)
- `src/horta/ui/pages/informes.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/descarga_cue.py`

Contido completo:
```python
"""Caderno dixital (CUE): descargar os datos co formato oficial (JSON) e o Excel para pasalos
ao caderno público da Xunta (XEAGA), e ver o que lles falta por traballo
(docs/superpowers/specs/2026-10-29-cue-design.md)."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.cue import excel_xeaga, json_cue, xerar_cue
from horta.ui.campos import campo_data
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data
from horta.ui.pages.diario import SECCION_DO_TIPO
from horta.ui.sesion import pechar_sesion, usuario_actual

# Onde se completa o que falta, para o que non é un traballo
_SECCION = {**SECCION_DO_TIPO, "cultivo": "cultivos", "explotacion": "explotacion"}


def seccion_cue(horta_id: int) -> None:
    hoxe = date.today()
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md q-mt-md"):
        ui.label("Caderno dixital (CUE)").classes("text-subtitle1 text-weight-bold")
        ui.label("Obrigatorio para as explotacións profesionais desde o 1/1/2027. O caderno "
                 "público da Xunta (XEAGA) non importa ficheiros: o Excel ten todo ordenado "
                 "para pasalo a man. Os datos en JSON son os que enviaría un CUE comercial."
                 ).classes("texto-suave")
        with ui.row().classes("w-full no-wrap"):
            desde = campo_data("Desde", date(hoxe.year, 1, 1).isoformat()).classes(
                remove="w-full", add="col")
            ata = campo_data("Ata", hoxe.isoformat()).classes(remove="w-full", add="col")

        def xerar(formato: str) -> None:
            inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
            if inicio is None or fin is None:
                ui.notify("Indica as dúas datas", type="warning")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                cue = xerar_cue(session, actor, horta_id, inicio, fin)
            nome = f"cue-{inicio:%Y%m%d}-{fin:%Y%m%d}"
            if formato == "json":
                ui.download.content(json_cue(cue), f"{nome}.json")
            else:
                ui.download.content(excel_xeaga(cue), f"{nome}-para-xeaga.xlsx")

        with ui.row():
            ui.button("Para pasar ao XEAGA (Excel)", icon="download",
                      on_click=lambda: xerar("excel")).props("outline")
            ui.button("Datos do CUE (JSON)", icon="data_object",
                      on_click=lambda: xerar("json")).props("outline flat")
        _faltas(horta_id, date(hoxe.year, 1, 1), hoxe)


def _faltas(horta_id: int, desde: date, ata: date) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return
        faltas = xerar_cue(session, actor, horta_id, desde, ata).faltas()
    if not faltas:
        ui.label(f"Ao CUE de {desde.year} non lle falta nada.").classes("etiqueta-ok")
        return
    ui.label(f"Que lle falta ao CUE de {desde.year} (non impide descargalo):").classes(
        "text-weight-medium")
    por_traballo: dict[tuple[str, int | None, str], list[str]] = {}
    for falta in faltas:
        chave = (falta.orixe.tipo, falta.orixe.id, falta.orixe.texto)
        por_traballo.setdefault(chave, [])
        if falta.falta not in por_traballo[chave]:
            por_traballo[chave].append(falta.falta)
    with ui.expansion(f"{len(por_traballo)} rexistros con datos que faltan").classes("w-full"):
        for (tipo, _, texto), que in por_traballo.items():
            with ui.row().classes("items-center gap-2 no-wrap"):
                ui.icon("warning").classes("text-warning")
                ui.label(f"{texto}: falta {', '.join(que)}").classes("text-body2")
                if tipo in _SECCION:
                    ui.link("Ver", url_seccion(horta_id, _SECCION[tipo]))
```

### Paso 2 — `src/horta/ui/pages/informes.py`

Antes:
```python
"""Informes: o que sae do traballo apuntado. Hoxe, o caderno de explotación, o que lle falta e
os traballos sen quen o fixo."""
```

Despois:
```python
"""Informes: o que sae do traballo apuntado. O caderno de explotación, o caderno dixital (CUE),
o que lles falta e os traballos sen quen o fixo."""
```

### Paso 3 — `src/horta/ui/pages/informes.py`

Antes:
```python
from horta.ui.descarga_caderno import boton_caderno
```

Despois:
```python
from horta.ui.descarga_caderno import boton_caderno
from horta.ui.descarga_cue import seccion_cue
```

### Paso 4 — `src/horta/ui/pages/informes.py`

Antes:
```python
    inicio_ano = date(date.today().year, 1, 1)
```

Despois:
```python
    inicio_ano = date(date.today().year, 1, 1)
    seccion_cue(horta_id)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

CUE (3/3): en Informes: feito.

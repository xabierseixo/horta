# Tarefa 055d — Caderno: diálogo «Datos do caderno» e data de adquisición

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 055b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No Resumo, quen administra a explotación ten o botón «Datos do caderno» (enderezo, email, tipo de representación e asesoramento). Nas máquinas, a data de adquisición. Probado no navegador o 2026-10-25. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`, bloque 1.

## Ficheiros a tocar

- `src/horta/ui/dialogo_datos_caderno.py` (**ficheiro novo**)
- `src/horta/ui/pages/horta_detalle.py`
- `src/horta/ui/pages/maquinaria.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/dialogo_datos_caderno.py`

Contido completo:
```python
"""Diálogo «Datos do caderno»: enderezo e asesoramento (modelo da Xunta, 1.1 e 1.4)."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.services.hortas import TIPOS_XIP, actualizar_horta
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual

_TEXTOS = (("enderezo", "Enderezo"), ("localidade", "Localidade"),
           ("codigo_postal", "Código postal"), ("provincia", "Provincia"), ("email", "Email"),
           ("tipo_representacion", "Tipo de representación (se asina un representante)"))
_ASESORAMENTO = (("asesoramento_nome", "Entidade ou agrupación de asesoramento"),
                 ("asesoramento_nif", "NIF da entidade"),
                 ("asesoramento_num", "Nº de identificación"))


def boton_datos_caderno(horta_id: int) -> None:
    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        ui.label("Datos do caderno").classes("text-h6")
        ui.label("Saen na primeira folla do caderno de explotación.").classes("text-caption")
        campos = {campo: ui.input(etiqueta).classes("w-full") for campo, etiqueta in _TEXTOS}
        ui.label("Asesoramento en xestión integrada de pragas").classes("text-subtitle2")
        tipo_xip = ui.select(TIPOS_XIP, label="Tipo de explotación", clearable=True).classes(
            "w-full")
        campos |= {campo: ui.input(etiqueta).classes("w-full")
                   for campo, etiqueta in _ASESORAMENTO}
        fertilizacion = ui.checkbox("Recibe asesoramento en fertilización")

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                horta = session.get(Horta, horta_id)
                if actor is None or horta is None:
                    pechar_sesion()
                    return
                cambios = {c: (i.value or None) for c, i in campos.items()}
                ok = executar_accion(session, lambda: actualizar_horta(
                    session, actor, horta, tipo_xip=tipo_xip.value,
                    asesoramento_fertilizacion=fertilizacion.value, **cambios))
            if ok:
                ui.notify("Gardado", type="positive")
                dialogo.close()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        with get_session() as session:
            horta = session.get(Horta, horta_id)
        if horta is None:
            return
        for campo, entrada in campos.items():
            entrada.value = getattr(horta, campo) or ""
        tipo_xip.value = horta.tipo_xip
        fertilizacion.value = horta.asesoramento_fertilizacion
        dialogo.open()

    ui.button("Datos do caderno", icon="badge", on_click=abrir).props("outline")
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.descarga_caderno import boton_caderno
```

Despois:
```python
from horta.ui.descarga_caderno import boton_caderno
from horta.ui.dialogo_datos_caderno import boton_datos_caderno
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                ).props("outline")
```

Despois:
```python
                ).props("outline")
                boton_datos_caderno(horta_id)
```

### Paso 4 — `src/horta/ui/pages/maquinaria.py`

Antes:
```python
        inspeccion = campo_data("Data última inspección")
```

Despois:
```python
        inspeccion = campo_data("Data última inspección")
        adquisicion = campo_data("Data de adquisición")
```

### Paso 5 — `src/horta/ui/pages/maquinaria.py`

Antes:
```python
                         "data_ultima_inspeccion": parsear_data(inspeccion.value),
```

Despois:
```python
                         "data_ultima_inspeccion": parsear_data(inspeccion.value),
                         "data_adquisicion": parsear_data(adquisicion.value),
```

### Paso 6 — `src/horta/ui/pages/maquinaria.py`

Antes:
```python
                            if m and m.data_ultima_inspeccion else "")
```

Despois:
```python
                            if m and m.data_ultima_inspeccion else "")
        adquisicion.value = m.data_adquisicion.isoformat() if m and m.data_adquisicion else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense encher os datos do caderno da explotación e a data de adquisición das máquinas.

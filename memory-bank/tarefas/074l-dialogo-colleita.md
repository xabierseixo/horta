# Tarefa 074l — Formularios separados (6/7): colleita

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario da colleita sepárase da súa páxina (dialogo_colleita), cunha soa función para abrilo novo ou para editar. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from __future__ import annotations

```

Despois:
```python
from __future__ import annotations

from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        destinos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_colleita")}
        restos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_restos")}
```

Despois:
```python
        destinos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_colleita")}
```

### Paso 3 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
    if not pode_editar:
        return
```

Despois:
```python
    if not pode_editar:
        return

    abrir = dialogo_colleita(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        abrir(next(x for x in colleitas if x.id == taboa.selected[0]["id"]))

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        colleita_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                colleita = session.get(Colleita, colleita_id)
                if actor is None or colleita is None:
                    return
                ok = executar_accion(
                    session, lambda: dar_de_baixa_colleita(session, actor, colleita)
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta colleita? Non se borra: consérvase no histórico.", confirmar
        )

    with ui.row():
        ui.button("Apuntar colleita", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_colleita(horta_id: int) -> Callable[[Colleita | None], None]:
    """Constrúe o diálogo de apuntar ou editar unha colleita e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        nome_cultivo = {c.id: f"{c.especie} {c.variedade or ''}".strip()
                        for c in listar_cultivos(session, actor, horta_id)}
        destinos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_colleita")}
        restos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_restos")}
```

### Paso 4 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Apuntar colleita"
        cultivo.value = None
        data.value = date.today().isoformat()
        for campo in (cantidade, lote, notas, data_fin, albaran, cliente_nome, cliente_nif,
                      cliente_enderezo, cliente_reaga):
            campo.value = ""
        superficie.establecer(None)
        sementes.value = plantas.value = sen_colleita.value = restos_solo.value = False
        unidade.value = "kg"
        destino.value = destino_restos.value = None
        dialogo.open()

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        c = next(x for x in colleitas if x.id == taboa.selected[0]["id"])
        editando["id"] = c.id
        titulo.text = "Editar colleita"
        cultivo.value = c.cultivo_id
        data.value = c.data.isoformat()
        cantidade.value = f"{c.cantidade:g}"
        unidade.value = c.unidade
        lote.value = c.lote
        superficie.establecer(c.superficie_ha)
        destino.value = c.destino_colleita
        destino_restos.value = c.destino_restos
        notas.value = c.notas or ""
        data_fin.value = c.data_fin.isoformat() if c.data_fin else ""
        albaran.value = c.albaran_factura or ""
        cliente_nome.value = c.cliente_nome or ""
        cliente_nif.value = c.cliente_nif or ""
        cliente_enderezo.value = c.cliente_enderezo or ""
        cliente_reaga.value = c.cliente_reaga or ""
        sementes.value = c.obten_sementes
        plantas.value = c.obten_plantas
        sen_colleita.value = c.sen_colleita_ambiental
        restos_solo.value = c.restos_no_solo
        dialogo.open()

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        colleita_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                colleita = session.get(Colleita, colleita_id)
                if actor is None or colleita is None:
                    return
                ok = executar_accion(
                    session, lambda: dar_de_baixa_colleita(session, actor, colleita)
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta colleita? Non se borra: consérvase no histórico.", confirmar
        )

    with ui.row():
        ui.button("Apuntar colleita", icon="add", on_click=abrir_nova)
        ui.button("Editar", icon="edit", on_click=abrir_edicion).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")
```

Despois:
```python
    def abrir(c: Colleita | None) -> None:
        editando["id"] = c.id if c else None
        titulo.text = "Editar colleita" if c else "Apuntar colleita"
        cultivo.value = c.cultivo_id if c else None
        data.value = (c.data if c else date.today()).isoformat()
        cantidade.value = f"{c.cantidade:g}" if c else ""
        unidade.value = c.unidade if c else "kg"
        lote.value = c.lote if c else ""
        superficie.establecer(c.superficie_ha if c else None)
        destino.value = c.destino_colleita if c else None
        destino_restos.value = c.destino_restos if c else None
        notas.value = (c.notas or "") if c else ""
        data_fin.value = c.data_fin.isoformat() if c and c.data_fin else ""
        albaran.value = (c.albaran_factura or "") if c else ""
        cliente_nome.value = (c.cliente_nome or "") if c else ""
        cliente_nif.value = (c.cliente_nif or "") if c else ""
        cliente_enderezo.value = (c.cliente_enderezo or "") if c else ""
        cliente_reaga.value = (c.cliente_reaga or "") if c else ""
        sementes.value = bool(c and c.obten_sementes)
        plantas.value = bool(c and c.obten_plantas)
        sen_colleita.value = bool(c and c.sen_colleita_ambiental)
        restos_solo.value = bool(c and c.restos_no_solo)
        dialogo.open()

    return abrir
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios separados (6/7): colleita: feito.

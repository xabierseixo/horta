# Tarefa 039 — Editar e dar de baixa máquinas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

Na sección Maquinaria só se podían crear máquinas. Agora: escoller unha fila e **Editar** (mesmo diálogo, con "Activa" para darla de baixa cando se vende ou se desbota). Cambiar o tipo de identificador borra os outros dous (só pode haber un). Revisión 2026-10-24, oco 2.

## Ficheiros a tocar

- `src/horta/ui/pages/maquinaria.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/maquinaria.py`: importar

Antes:
```python
from horta.services.maquinaria import crear_maquina, listar_maquinas
```

Despois:
```python
from horta.models.maquina import Maquina
from horta.services.maquinaria import actualizar_maquina, crear_maquina, listar_maquinas
```

### Paso 2 — mesmo ficheiro: táboa con selección e columna Activa

Antes:
```python
         "propia": "si" if m.propia else "non"}
        for m in maquinas
    ]
    ui.table(
```

Despois:
```python
         "propia": "si" if m.propia else "non", "activa": "si" if m.activa else "non"}
        for m in maquinas
    ]
    taboa = ui.table(
```

### Paso 3 — mesmo ficheiro: columnas e selección

Antes:
```python
            ("inspeccion", "Última inspección"), ("propia", "Propia"))],
        rows=filas, row_key="id",
```

Despois:
```python
            ("inspeccion", "Última inspección"), ("propia", "Propia"), ("activa", "Activa"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
```

### Paso 4 — mesmo ficheiro: título variable e campo Activa

Antes:
```python
    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        ui.label("Nova máquina").classes("text-h6")
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        titulo = ui.label("Nova máquina").classes("text-h6")
        activa = ui.checkbox("Activa (desmárcaa se xa non está na explotación)", value=True)
```

### Paso 5 — mesmo ficheiro: gardar crea ou actualiza

Antes:
```python
                ok = executar_accion(session, lambda: crear_maquina(
                    session, actor, horta_id, alias.value, marca_modelo=marca.value or None,
                    propia=propia.value, potencia=parsear_decimal(potencia.value),
                    data_ultima_inspeccion=parsear_data(inspeccion.value),
                    **({campo: ident.value} if ident.value else {})))
```

Despois:
```python
                datos = {"marca_modelo": marca.value or None, "propia": propia.value,
                         "potencia": parsear_decimal(potencia.value),
                         "data_ultima_inspeccion": parsear_data(inspeccion.value),
                         "activa": activa.value, "num_roma": None, "num_reganip": None,
                         "id_equipo_non_inscribible": None, campo: ident.value or None}

                def accion() -> None:
                    maquina = session.get(Maquina, editando["id"]) if editando["id"] else None
                    if maquina is None:
                        crear_maquina(session, actor, horta_id, alias.value, **datos)
                    else:
                        actualizar_maquina(session, actor, maquina, alias=alias.value, **datos)

                ok = executar_accion(session, accion)
```

### Paso 6 — mesmo ficheiro: abrir para crear ou editar

Antes:
```python
    ui.button("Nova máquina", icon="agriculture", on_click=dialogo.open)
```

Despois:
```python
    def abrir(m: Maquina | None) -> None:
        editando["id"] = m.id if m else None
        titulo.text = "Editar máquina" if m else "Nova máquina"
        alias.value, marca.value = (m.alias, m.marca_modelo or "") if m else ("", "")
        tipo_id.value = ("reganip" if m and m.num_reganip else
                         "outro" if m and m.id_equipo_non_inscribible else "roma")
        ident.value = ((m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "")
                       if m else "")
        propia.value, activa.value = (m.propia, m.activa) if m else (True, True)
        potencia.value = f"{m.potencia:g}" if m and m.potencia is not None else ""
        inspeccion.value = (m.data_ultima_inspeccion.isoformat()
                            if m and m.data_ultima_inspeccion else "")
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha máquina na táboa", type="warning")
            return
        abrir(next(m for m in maquinas if m.id == taboa.selected[0]["id"]))

    with ui.row():
        ui.button("Nova máquina", icon="agriculture", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Na sección Maquinaria pódese escoller unha máquina, editala e marcala como non activa.

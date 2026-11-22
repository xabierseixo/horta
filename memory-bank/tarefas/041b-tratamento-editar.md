# Tarefa 041b — Editar tratamentos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 041.

## Obxectivo

Na sección Tratamentos só se podía crear e dar de baixa. Agora: escoller unha fila e **Editar** no mesmo diálogo. Se o tratamento ten máis datos dos que mostra o formulario (`cabe_no_formulario` é falso), avísase e non se abre, para non borrar nada. O diálogo deixa de cortarse no móbil (`width: min(40rem, 94vw)`, análise §F). Revisión 2026-10-24, oco 1.

## Ficheiros a tocar

- `src/horta/ui/pages/tratamentos_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/tratamentos_fito.py`: importar

Antes:
```python
    Problema,
    crear_tratamento_fito,
```

Despois:
```python
    Problema,
    actualizar_tratamento_fito,
    cabe_no_formulario,
    crear_tratamento_fito,
```

### Paso 2 — mesmo ficheiro: escoller só valores que existen na lista

Antes:
```python
def seccion_tratamentos_fito(horta_id: int, pode_editar: bool) -> None:
```

Despois:
```python
def _escoller(campo: ui.select, valor: object) -> None:
    campo.value = valor if valor in campo.options else None


def seccion_tratamentos_fito(horta_id: int, pode_editar: bool) -> None:
```

### Paso 3 — mesmo ficheiro: lembrar que se edita e ancho no móbil

Antes:
```python
    with ui.dialog() as dialogo, ui.card().style("min-width: 40rem"):
```

Despois:
```python
    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
```

### Paso 4 — mesmo ficheiro: gardar crea ou actualiza

Antes:
```python
                            crear_tratamento_fito(session, actor_actual, horta_id, datos)
```

Despois:
```python
                            tratamento = (session.get(TratamentoFito, editando["id"])
                                          if editando["id"] else None)
                            if tratamento is None:
                                crear_tratamento_fito(session, actor_actual, horta_id, datos)
                            else:
                                actualizar_tratamento_fito(session, actor_actual, tratamento,
                                                           datos)
```

### Paso 5 — mesmo ficheiro: abrir novo ou para editar

Antes:
```python
    with ui.row():
        ui.button("Novo tratamento", icon="add", on_click=dialogo.open)
```

Despois:
```python
    def abrir(t: TratamentoFito | None) -> None:
        c = t.cultivos[0] if t and t.cultivos else None
        p = t.problemas[0] if t and t.problemas else None
        pr = t.produtos[0] if t and t.produtos else None
        a = t.aplicadores[0] if t and t.aplicadores else None
        editando["id"] = t.id if t else None
        hoxe = date.today().isoformat()
        data_inicio.value = t.data_inicio.isoformat() if t else hoxe
        data_fin.value = t.data_fin.isoformat() if t else hoxe
        hora.value = t.hora.strftime("%H:%M") if t and t.hora else ""
        _escoller(cultivo, c.cultivo_id if c else None)
        superficie.value = f"{c.superficie_ha:g}" if c and c.superficie_ha is not None else ""
        _escoller(estado, c.estado_fenoloxico if c else None)
        tipo_problema.value = p.tipo if p else "enfermidade"
        _escoller(problema, p.codigo if p else None)
        _escoller(xustificacion, t.xustificacions[0].codigo if t and t.xustificacions else None)
        if pr:
            _escoller(tipo_produto, pr.tipo_produto)
        nome_comercial.value = (pr.nome_comercial or "") if pr else ""
        num_rexistro.value = (pr.num_rexistro or "") if pr else ""
        materia_activa.value = (pr.materia_activa or "") if pr else ""
        dose.value = f"{pr.dose:g}" if pr and pr.dose is not None else ""
        _escoller(unidade, pr.unidade if pr else None)
        _escoller(aplicador, a.persoa_id if a else None)
        _escoller(maquina, a.maquina_id if a else None)
        _escoller(eficacia, t.eficacia if t else None)
        observacions.value = (t.observacions or "") if t else ""
        pasos.set_value("1. Que e onde")
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona un tratamento na táboa", type="warning")
            return
        with get_session() as session:
            t = session.get(TratamentoFito, taboa.selected[0]["id"])
            if t is None:
                return
            if not cabe_no_formulario(t):
                ui.notify("Este tratamento ten máis datos dos que mostra o formulario: "
                          "dáo de baixa e apúntao de novo", type="warning")
                return
            abrir(t)

    with ui.row():
        ui.button("Novo tratamento", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Na sección Tratamentos pódese escoller un tratamento e editalo; os que teñen máis datos dos que mostra o formulario avisan en vez de abrirse.

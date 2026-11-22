# Tarefa 084c — Varias leiras (4/5): colleita en varias leiras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 084b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar a colleita de varias leiras dunha vez, coa cantidade de cada unha: unha colleita por leira, no mesmo lote. Deseño: `docs/superpowers/specs/2026-10-28-varias-leiras-design.md` (paso 5 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/services/colleitas.py`
- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/colleitas.py`

Antes:
```python
from dataclasses import dataclass
```

Despois:
```python
from dataclasses import dataclass, replace
```

### Paso 2 — `src/horta/services/colleitas.py`

Antes:
```python
def crear_colleita(
    session: Session, actor: Usuario, datos: DatosColleita, hoxe: date | None = None
) -> Colleita:
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, datos.cultivo_id, datos.data)
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    if datos.superficie_ha is None:
        datos.superficie_ha = cultivo.superficie_ha
    colleita = Colleita(creado_por=actor.id, lote_id=_lote(session, datos, cultivo, horta_id))
    _copiar(colleita, datos)
    session.add(colleita)
    session.commit()
    return colleita
```

Despois:
```python
def _engadir(session: Session, actor: Usuario, datos: DatosColleita, hoxe: date) -> Colleita:
    """Valida e engade a colleita á sesión, sen gardar (commit)."""
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, datos.cultivo_id, datos.data)
    _validar(session, datos, cultivo, horta_id, hoxe)
    if datos.superficie_ha is None:
        datos.superficie_ha = cultivo.superficie_ha
    colleita = Colleita(creado_por=actor.id, lote_id=_lote(session, datos, cultivo, horta_id))
    _copiar(colleita, datos)
    session.add(colleita)
    session.flush()
    return colleita


def crear_colleita(
    session: Session, actor: Usuario, datos: DatosColleita, hoxe: date | None = None
) -> Colleita:
    colleita = _engadir(session, actor, datos, hoxe or date.today())
    session.commit()
    return colleita


def crear_colleitas(
    session: Session, actor: Usuario, datos: DatosColleita, cantidades: dict[int, float],
    hoxe: date | None = None,
) -> list[Colleita]:
    """A colleita de varias leiras dunha vez: unha colleita por leira (o CUE pídea por
    cultivo), coa cantidade de cada unha e todas no mesmo lote. As horas repártense pola
    cantidade. Ou se gardan todas ou ningunha."""
    if not cantidades:
        raise OperacionNonPermitidaError("Escolle polo menos unha leira")
    if any(c is None or c <= 0 for c in cantidades.values()):
        raise OperacionNonPermitidaError("Pon a cantidade colleitada en cada leira")
    cultivos = [session.get(Cultivo, c) for c in cantidades]
    if len({(c.cultivo_siex_codigo or c.especie.strip().lower()) for c in cultivos if c}) > 1:
        raise OperacionNonPermitidaError(
            "As leiras dunha mesma colleita van ao mesmo lote: teñen que ser do mesmo cultivo")
    total = sum(cantidades.values())
    colleitas = []
    try:
        for cultivo_id, cantidade in cantidades.items():
            parte = replace(
                datos, cultivo_id=cultivo_id, cantidade=cantidade, superficie_ha=None,
                horas=round(datos.horas * cantidade / total, 2) if datos.horas else None)
            colleitas.append(_engadir(session, actor, parte, hoxe or date.today()))
            # As seguintes van ao mesmo lote
            datos.lote = colleitas[0].lote
    except Exception:
        session.rollback()
        raise
    session.commit()
    return colleitas
```

### Paso 3 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
    crear_colleita,
```

Despois:
```python
    crear_colleita,
    crear_colleitas,
```

### Paso 4 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        cultivo = ui.select(nome_cultivo, label="Cultivo", with_input=True).classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col-grow")
            unidade = ui.select(list(UNIDADES_COLLEITA), value="kg", label="Unidade").classes(
                "w-28")
```

Despois:
```python
        # Varias leiras dunha vez: unha colleita por leira, coa súa cantidade e no mesmo lote
        cultivo = ui.select(nome_cultivo, label="Leiras (unha ou varias)", with_input=True,
                            multiple=True, value=[]).classes("w-full").props("use-chips")
        data = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col-grow")
            unidade = ui.select(list(UNIDADES_COLLEITA), value="kg", label="Unidade").classes(
                "w-28")
        cantidades: dict[int, ui.input] = {}

        @ui.refreshable
        def cantidades_por_leira() -> None:
            cantidades.clear()
            if len(cultivo.value or []) > 1:
                ui.label("Canto se colleu en cada leira").classes("text-caption")
                for cultivo_id in cultivo.value:
                    cantidades[cultivo_id] = ui.input(nome_cultivo.get(cultivo_id, "")).classes(
                        "w-full")

        cantidades_por_leira()
```

### Paso 5 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
            if editando["id"] is not None or cultivo.value is None:
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    return
                lote.value = propor_lote(session, actor, cultivo.value,
                                         parsear_data(data.value) or date.today())

        cultivo.on_value_change(propor)
        aviso_prazo = ui.label().classes("text-negative text-sm")

        def comprobar_prazo() -> None:
            dia = parsear_data(data.value) if data.value else None
            if cultivo.value is None or dia is None:
                aviso_prazo.text = ""
                return
            with get_session() as session:
                aviso_prazo.text = aviso_prazo_colleita(session, cultivo.value, dia) or ""

        cultivo.on_value_change(comprobar_prazo)
        data.on_value_change(comprobar_prazo)

        def gardar() -> None:
            if cultivo.value is None:
                ui.notify("Escolle o cultivo", type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    datos = DatosColleita(
                        cultivo_id=cultivo.value,
```

Despois:
```python
            varias = len(cultivo.value or []) > 1
            cantidade.set_visibility(not varias)
            superficie.set_visibility(len(cultivo.value or []) == 1)
            cantidades_por_leira.refresh()
            if editando["id"] is not None or not cultivo.value:
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    return
                lote.value = propor_lote(session, actor, cultivo.value[0],
                                         parsear_data(data.value) or date.today())

        cultivo.on_value_change(propor)
        aviso_prazo = ui.label().classes("text-negative text-sm")

        def comprobar_prazo() -> None:
            dia = parsear_data(data.value) if data.value else None
            if not cultivo.value or dia is None:
                aviso_prazo.text = ""
                return
            with get_session() as session:
                aviso_prazo.text = " ".join(
                    aviso for c in cultivo.value
                    if (aviso := aviso_prazo_colleita(session, c, dia))) or ""

        cultivo.on_value_change(comprobar_prazo)
        data.on_value_change(comprobar_prazo)

        def gardar() -> None:
            if not cultivo.value:
                ui.notify("Escolle as leiras", type="negative")
                return
            if editando["id"] is not None and len(cultivo.value) > 1:
                ui.notify("Unha colleita apuntada é dunha leira: para máis, apunta outra",
                          type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    datos = DatosColleita(
                        cultivo_id=cultivo.value[0],
```

### Paso 6 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
                    if editando["id"] is None:
```

Despois:
```python
                    if editando["id"] is None and len(cultivo.value) > 1:
                        novas = crear_colleitas(session, actor, datos, {
                            c: parsear_decimal(entrada.value) or 0
                            for c, entrada in cantidades.items()})
                        rematar_tarefa(session, actor, editando["tarefa"], novas[0])
                    elif editando["id"] is None:
```

### Paso 7 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        cultivo.value = c.cultivo_id if c else (tarefa.cultivo_id if tarefa else None)
```

Despois:
```python
        cultivo.value = ([c.cultivo_id] if c else
                         [tarefa.cultivo_id] if tarefa and tarefa.cultivo_id else [])
```

### Paso 8 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        restos_solo.value = bool(c and c.restos_no_solo)
```

Despois:
```python
        restos_solo.value = bool(c and c.restos_no_solo)
        propor()
        if c:
            lote.value = c.lote
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Varias leiras (4/5): colleita en varias leiras: feito.

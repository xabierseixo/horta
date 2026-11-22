# Tarefa 075u — Diario: filtro por persoa

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 075l a 075t. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No Diario, filtro «Quen» e o nome de quen o fixo en cada traballo. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.services.diario import TIPOS, Traballo, listar_traballos
```

Despois:
```python
from horta.services.diario import TIPOS, Traballo, listar_traballos
from horta.services.persoas import listar_persoas
```

### Paso 2 — `src/horta/ui/pages/diario.py`

Antes:
```python
def _tarxeta(t: Traballo, ao_premer: Callable[[], None]) -> None:
    with ui.row().classes("tarxeta w-full items-center no-wrap gap-3 cursor-pointer q-pa-sm").on(
            "click", ao_premer):
        ui.icon(ICONAS[t.tipo]).classes("text-h5 text-primary")
        with ui.column().classes("gap-0 col"):
            ui.label(TIPOS[t.tipo] + (f": {t.que}" if t.que else "")).classes(
                "text-weight-bold")
            if t.onde:
                ui.label(t.onde).classes("texto-suave text-caption")
```

Despois:
```python
def _tarxeta(t: Traballo, ao_premer: Callable[[], None], nomes: dict[int, str]) -> None:
    with ui.row().classes("tarxeta w-full items-center no-wrap gap-3 cursor-pointer q-pa-sm").on(
            "click", ao_premer):
        ui.icon(ICONAS[t.tipo]).classes("text-h5 text-primary")
        with ui.column().classes("gap-0 col"):
            ui.label(TIPOS[t.tipo] + (f": {t.que}" if t.que else "")).classes(
                "text-weight-bold")
            quen = ", ".join(nomes.get(p, "") for p in t.persoas)
            if t.onde or quen:
                ui.label(" · ".join(x for x in (t.onde, quen) if x)).classes(
                    "texto-suave text-caption")
```

### Paso 3 — `src/horta/ui/pages/diario.py`

Antes:
```python
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
```

Despois:
```python
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}
```

### Paso 4 — `src/horta/ui/pages/diario.py`

Antes:
```python
        parcela = ui.select({0: "Todas", **parcelas}, value=0, label="Parcela").classes("w-48")
```

Despois:
```python
        parcela = ui.select({0: "Todas", **parcelas}, value=0, label="Parcela").classes("w-48")
        quen = ui.select({0: "Todas", **persoas}, value=0, label="Quen").classes("w-48")
```

### Paso 5 — `src/horta/ui/pages/diario.py`

Antes:
```python
            and (not parcela.value or parcela.value in t.parcelas)
```

Despois:
```python
            and (not parcela.value or parcela.value in t.parcelas)
            and (not quen.value or quen.value in t.persoas)
```

### Paso 6 — `src/horta/ui/pages/diario.py`

Antes:
```python
                        _tarxeta(t, partial(formularios.editar, t))
                    else:
                        _tarxeta(t, partial(ui.navigate.to,
                                            url_seccion(horta_id, SECCION_DO_TIPO[t.tipo])))

    for filtro in (tipo, parcela, estado, desde, ata):
```

Despois:
```python
                        _tarxeta(t, partial(formularios.editar, t), persoas)
                    else:
                        _tarxeta(t, partial(ui.navigate.to,
                                            url_seccion(horta_id, SECCION_DO_TIPO[t.tipo])),
                                 persoas)

    for filtro in (tipo, parcela, quen, estado, desde, ata):
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Diario: filtro por persoa: feito.

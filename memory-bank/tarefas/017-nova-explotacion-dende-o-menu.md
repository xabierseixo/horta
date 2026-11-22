# Tarefa 017 — Crear unha explotación dende o selector do menú lateral

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 016.

## Obxectivo

Engadir ao selector "Explotación" do menú unha opción "+ Nova explotación" que leva á páxina `/` co diálogo de crear aberto (sen redirixir).

## Ficheiros a tocar

- `src/horta/ui/layout.py`
- `src/horta/ui/pages/dashboard.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/layout.py`: opción nova no selector

Antes:
```python
            ui.select(
                hortas,
                value=horta_id,
                label="Explotación",
                on_change=lambda e: ui.navigate.to(url_seccion(e.value, seccion)),
            ).props("dense outlined dark").classes("menu-selector w-full q-mb-sm")
```
Despois:
```python
            ui.select(
                {**hortas, NOVA_EXPLOTACION: "+ Nova explotación"},
                value=horta_id,
                label="Explotación",
                on_change=lambda e: ui.navigate.to(
                    "/?nova=1" if e.value == NOVA_EXPLOTACION else url_seccion(e.value, seccion)
                ),
            ).props("dense outlined dark").classes("menu-selector w-full q-mb-sm")
```

### Paso 2 — mesmo ficheiro: constante

Antes:
```python
_CLAVES = {s.clave for s in SECCIONS}
```
Despois:
```python
_CLAVES = {s.clave for s in SECCIONS}
NOVA_EXPLOTACION = -1  # valor especial do selector de explotación
```

### Paso 3 — `src/horta/ui/pages/dashboard.py`: parámetro `nova`

Antes:
```python
def dashboard_page() -> None:
```
Despois:
```python
def dashboard_page(nova: bool = False) -> None:
```

### Paso 4 — mesmo ficheiro: non redirixir se se pide crear unha nova

Antes:
```python
    if hortas:
        ids = [h.id for h, _ in hortas]
```
Despois:
```python
    if hortas and not nova:
        ids = [h.id for h, _ in hortas]
```

### Paso 5 — mesmo ficheiro: abrir o diálogo automaticamente

Antes:
```python
    with ui.row().classes("w-full items-center justify-between q-mb-md"):
        ui.label(f"Ola, {nome}").classes("text-xl font-bold")
```
Despois:
```python
    if nova:
        dialog_nova_horta.open()

    with ui.row().classes("w-full items-center justify-between q-mb-md"):
        ui.label(f"Ola, {nome}").classes("text-xl font-bold")
```

## Criterios de aceptación

- O selector do menú ten a opción "+ Nova explotación" ao final.
- Ao escollela, ábrese `/` co diálogo "Nova horta" aberto.
- Sen `?nova=1`, `/` segue redirixindo á última horta (tarefa 016).
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Paso 1** (`layout.py`): engadido `+ Nova explotación` ao selector co valor especial `NOVA_EXPLOTACION = -1`; cando se escolle, rediríxe a `/?nova=1` en vez de a unha sección.
- **Paso 2** (`layout.py`): constante `NOVA_EXPLOTACION = -1` definida liña 35.
- **Paso 3** (`dashboard.py`): sinatura `dashboard_page(nova: bool = False)`.
- **Paso 4** (`dashboard.py`): `if hortas and not nova:` — non redirixe cando se pide crear.
- **Paso 5** (`dashboard.py`): `if nova: dialog_nova_horta.open()` antes do cabeceiro.

**Comprobacións**: `ruff check` — OK; `mypy src` — OK; `pytest -q` — **237 passed**.

**Commit**: `smoth/017-nova-explotacion-dende-o-menu` (ver abaixo).

# Tarefa 016 — Pantalla única: ao entrar, ir directo á última horta

**Estado**: feita

**Rama**: `deseno-visual`.

## Obxectivo

Que a páxina `/` deixe de ser unha lista de hortas: se o usuario ten hortas, vai directo ao Resumo da última que usou (ou da primeira). Só se non ten ningunha se amosa a benvida con "Nova horta".

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`
- `src/horta/ui/pages/dashboard.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`: importar `app`

Antes:
```python
from nicegui import ui
```
Despois:
```python
from nicegui import app, ui
```

### Paso 2 — mesmo ficheiro: lembrar a última horta visitada

Antes:
```python
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
```
Despois:
```python
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
            app.storage.user["ultima_horta"] = horta_id
```

### Paso 3 — `src/horta/ui/pages/dashboard.py`: importar `app`

Antes:
```python
from nicegui import ui
```
Despois:
```python
from nicegui import app, ui
```

### Paso 4 — mesmo ficheiro: redirixir á última horta

Antes:
```python
    cabeceira_paxina(mostrar_admin=e_admin_global)
```
Despois:
```python
    if hortas:
        ids = [h.id for h, _ in hortas]
        ultima = app.storage.user.get("ultima_horta")
        destino = ultima if ultima in ids else ids[0]
        ui.navigate.to(f"/hortas/{destino}/resumo")
        return

    cabeceira_paxina(mostrar_admin=e_admin_global)
```

## Criterios de aceptación

- Un usuario con hortas que abre `/` acaba en `/hortas/<id>/resumo` (a última visitada, ou a primeira).
- Un usuario sen hortas segue vendo a benvida co botón "Nova horta".
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- `src/horta/ui/pages/horta_detalle.py`: importou `app` de nicegui (liña 7) e garda `app.storage.user["ultima_horta"] = horta_id` logo de `comprobar_rol_horta` (liña 104).
- `src/horta/ui/pages/dashboard.py`: importou `app` de nicegui (liña 3) e engadiu o bloque de redirixión (liñas 35-40) que, cando hai hortas, navega a `/hortas/<id>/resumo` (a última visitada ou a primeira) e retorna.
- ruff: All checks passed.
- mypy: no issues found.
- pytest: 237 passed.
- Commit: `smoth/016-pantalla-unica-entrada`.

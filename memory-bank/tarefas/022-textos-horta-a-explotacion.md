# Tarefa 022 — Textos visibles: "horta" → "explotación"

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 014–021 (faina ao final).

## Obxectivo

Que o usuario lea sempre "explotación" en vez de "horta". **Só se cambian textos entre comiñas**; os nomes de variables, funcións, modelos e enderezos (`horta_id`, `Horta`, `/hortas/...`) NON se tocan. Tampouco a marca "Horta" (logo e pantalla de acceso).

## Ficheiros a tocar

- `src/horta/services/hortas.py`
- `src/horta/services/tratamentos_fito.py`
- `src/horta/ui/pages/dashboard.py`
- `src/horta/ui/pages/horta_detalle.py`
- `tests/services/test_tratamentos_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Cada fila das táboas é un texto que aparece **unha soa vez** no ficheiro: cámbiao coa ferramenta de editar ficheiros. Os textos que aparecen máis dunha vez van en pasos separados (1b, 3b, 4b) co código de arredor para que cada cambio sexa único. Non crees scripts.

### Paso 1 — `src/horta/services/hortas.py`

| Antes | Despois |
|---|---|
| `"Non tes permiso suficiente nesta horta"` | `"Non tes permiso suficiente nesta explotación"` |
| `"Esta horta ten tratamentos fitosanitarios rexistrados e debe conservarse "` | `"Esta explotación ten tratamentos fitosanitarios rexistrados e debe conservarse "` |
| `"Ese usuario non é membro desta horta"` | `"Ese usuario non é membro desta explotación"` |

### Paso 1b — `src/horta/services/hortas.py` (o mesmo texto en dous sitios)

Primeiro sitio. Antes:
```python
    if novo_rol != RolHorta.ADMIN and _e_ultimo_admin_da_horta(session, membro):
        raise OperacionNonPermitidaError("A horta ten que ter polo menos un administrador")
```

Despois:
```python
    if novo_rol != RolHorta.ADMIN and _e_ultimo_admin_da_horta(session, membro):
        raise OperacionNonPermitidaError("A explotación debe ter polo menos un administrador")
```

Segundo sitio. Antes:
```python
        if _e_ultimo_admin_da_horta(session, membro):
            raise OperacionNonPermitidaError("A horta ten que ter polo menos un administrador")
```

Despois:
```python
        if _e_ultimo_admin_da_horta(session, membro):
            raise OperacionNonPermitidaError("A explotación debe ter polo menos un administrador")
```

### Paso 2 — `src/horta/services/tratamentos_fito.py`

| Antes | Despois |
|---|---|
| `"O cultivo indicado non pertence a esta horta"` | `"O cultivo indicado non pertence a esta explotación"` |
| `"O aplicador indicado non é un aplicador desta horta"` | `"O aplicador indicado non é un aplicador desta explotación"` |
| `"A máquina indicada non é desta horta"` | `"A máquina indicada non é desta explotación"` |
| `"O asesor indicado non é un asesor desta horta"` | `"O asesor indicado non é un asesor desta explotación"` |

### Paso 3 — `src/horta/ui/pages/dashboard.py`

| Antes | Despois |
|---|---|
| `"Aínda non tes ningunha horta."` | `"Aínda non tes ningunha explotación."` |

### Paso 3b — `src/horta/ui/pages/dashboard.py` ("Nova horta" en dous sitios)

Primeiro sitio. Antes:
```python
        ui.label("Nova horta").classes("text-md font-bold")
```

Despois:
```python
        ui.label("Nova explotación").classes("text-md font-bold")
```

Segundo sitio. Antes:
```python
        ui.button("Nova horta", icon="add", on_click=dialog_nova_horta.open)
```

Despois:
```python
        ui.button("Nova explotación", icon="add", on_click=dialog_nova_horta.open)
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

| Antes | Despois |
|---|---|
| `"Non tes acceso a esta horta"` | `"Non tes acceso a esta explotación"` |
| `"Eliminar horta"` | `"Eliminar explotación"` |
| `"Configurar horta", icon="settings"` (o botón do Resumo) | `"Configurar explotación", icon="settings"` |
| `"Quitar da horta"` | `"Quitar da explotación"` |

### Paso 4b — `src/horta/ui/pages/horta_detalle.py` ("Esta horta xa non existe" en tres sitios)

Primeiro sitio. Antes:
```python
            ui.label("Esta horta xa non existe").classes("text-negative")
```

Despois:
```python
            ui.label("Esta explotación xa non existe").classes("text-negative")
```

Segundo sitio (en `gardar_horta`). Antes:
```python
                        ui.notify("Esta horta xa non existe", type="negative")
                        return
                    gardado = executar_accion(
```

Despois:
```python
                        ui.notify("Esta explotación xa non existe", type="negative")
                        return
                    gardado = executar_accion(
```

Terceiro sitio (en `eliminar_horta_actual`). Antes:
```python
                        ui.notify("Esta horta xa non existe", type="negative")
                        return
                    eliminada = executar_accion(
```

Despois:
```python
                        ui.notify("Esta explotación xa non existe", type="negative")
                        return
                    eliminada = executar_accion(
```

### Paso 5 — `tests/services/test_tratamentos_fito.py`

| Antes | Despois |
|---|---|
| `match="non pertence a esta horta"` | `match="non pertence a esta explotación"` |

## Criterios de aceptación

- Este comando non devolve ningunha liña (os comentarios `"""..."""` non contan):
  `grep -rn '"[^"]*\bhorta\b[^"]*"' src/horta/services src/horta/ui | grep -v '/hortas\|horta-catalogos\|"""'`
- Non se cambiou ningún nome de variable, función nin enderezo.
- Os tests pasan.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Tarefa 022 completada** o 2026-10-23 polo modelo local (smoth).
- Todos os textos entre comiñas que mencionaban "horta" foron cambiados a "explotación" nos 5 ficheiros indicados:
  - `src/horta/services/hortas.py`: 4 textos (permiso, membro, 2x admin)
  - `src/horta/services/tratamentos_fito.py`: 4 textos (cultivo, aplicador, máquina, asesor)
  - `src/horta/ui/pages/dashboard.py`: 3 textos ("Aínda non tes...", "Nova explotación" en dous sitios)
  - `src/horta/ui/pages/horta_detalle.py`: 7 textos (acceso, eliminar, configurar, quitar, 3x "xa non existe")
  - `tests/services/test_tratamentos_fito.py`: 1 texto (match do test)
- Nomes de variables, funcións e enderezos (`horta_id`, `Horta`, `/hortas/...`) non se tocaron.
- Ningún outro ficheiro foi modificado.
- Comprobacións: `uv run ruff check src tests` — All checks passed. `uv run mypy src` — Success: no issues found in 52 source files. `uv run pytest -q` — 244 passed.
- Commit: `smoth/022-textos-horta-a-explotacion` co rodapé `Axente: smoth`.

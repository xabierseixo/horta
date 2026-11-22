# Tarefa 024 — Campos dos formularios a todo o ancho e selectores con nome

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 014.

## Obxectivo

Nas ventás (diálogos) moitos campos quedan estreitos e non se ve o seu nome (p.ex. "Parcela" en Novo cultivo). Arránxase con **unha regra CSS** no tema: os campos que van directamente dentro da tarxeta dun diálogo ocupan todo o ancho, e a tarxeta ten un ancho mínimo. Ademais, catro selectores de rol non teñen etiqueta: póñenlla.

## Ficheiros a tocar

- `src/horta/ui/tema.py`
- `src/horta/ui/admin/usuarios.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/tema.py`: regra para os diálogos

Antes:
```python
.texto-suave { color: var(--cor-texto-suave); }
```

Despois:
```python
.texto-suave { color: var(--cor-texto-suave); }

/* Diálogos: ancho mínimo e campos a todo o ancho (só os fillos directos da tarxeta) */
.q-dialog .q-card { min-width: min(400px, 92vw); }
.q-dialog .q-card > .q-field { width: 100%; }
```

### Paso 2 — `src/horta/ui/admin/usuarios.py`: rol ao crear usuario

Antes:
```python
        rol_select = ui.select(list(_ROLES_USUARIO), value="usuario")
```

Despois:
```python
        rol_select = ui.select(list(_ROLES_USUARIO), value="usuario", label="Rol")
```

### Paso 3 — mesmo ficheiro: rol ao editar usuario

Antes:
```python
        rol_edit = ui.select(list(_ROLES_USUARIO), value="usuario")
```

Despois:
```python
        rol_edit = ui.select(list(_ROLES_USUARIO), value="usuario", label="Rol")
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`: rol ao engadir membro

Antes:
```python
        rol_input = ui.select(list(_ROLES_HORTA), value="lector")
```

Despois:
```python
        rol_input = ui.select(list(_ROLES_HORTA), value="lector", label="Rol")
```

### Paso 5 — mesmo ficheiro: rol ao editar membro

Antes:
```python
        rol_edit = ui.select(list(_ROLES_HORTA), value="lector")
```

Despois:
```python
        rol_edit = ui.select(list(_ROLES_HORTA), value="lector", label="Rol")
```

## Criterios de aceptación

- En "Novo cultivo" vese a etiqueta "Parcela" e o selector ocupa todo o ancho.
- Os selectores de rol amosan "Rol".
- Os tests pasan.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- `src/horta/ui/tema.py`: engadida regra CSS en `.texto-suave { color: var(--cor-texto-suave); }` — diálogos con ancho mínimo `min(400px, 92vw)` e campos a todo o ancho (fillos directos da tarxeta).
- `src/horta/ui/admin/usuarios.py`: dous selectores de rol (`rol_select` ao crear e `rol_edit` ao editar) agora teñen `label="Rol"`.
- `src/horta/ui/pages/horta_detalle.py`: dous selectores de rol (`rol_input` ao engadir membro e `rol_edit` ao cambiar rol) agora teñen `label="Rol"`.
- Comprobacións: `ruff check` ✅, `mypy src` ✅, `pytest -q` → **246 passed**.
- Commit: `smoth/024-campos-formularios-a-todo-o-ancho-e-selectores-rol`.

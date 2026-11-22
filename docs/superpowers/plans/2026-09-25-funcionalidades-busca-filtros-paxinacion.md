# Busca, filtros e paxinación — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Engadir busca de texto libre, filtros estruturados (Estado/Rol/Activo) e paxinación (10 filas por páxina) ás catro táboas existentes (Parcelas, Animais, Membros, Usuarios), combinables entre si, sen tocar a capa de servizos nin a BD.

**Architecture:** Filtrado 100% en Python sobre a lista de filas xa cargada por cada páxina; unha función pura compartida (`filtrar_filas`) aplica busca de texto + filtros estruturados; a paxinación é o parámetro nativo `pagination` de `ui.table` (NiceGUI/QTable), independente do filtrado.

**Tech Stack:** Python 3.11, NiceGUI (QTable nativo — sen dependencias novas), pytest.

**Spec:** `docs/superpowers/specs/2026-09-25-funcionalidades-busca-filtros-paxinacion-design.md`

## Global Constraints

- Identificadores, mensaxes e textos da UI en galego.
- Filtrado 100% en Python sobre a lista de filas xa cargada — non modificar `services/` nin a BD, sen dependencias novas.
- Busca por subcadea sen distinguir maiúsculas/minúsculas (`casefold()`), sen normalización de acentos (límite coñecido e aceptado: "rio" non atopa "Río").
- Na UI, o selector estruturado usa `"Todos"` coma sentinela de "sen filtro"; tradúcese a `None` antes de chamar a `filtrar_filas` (que xa trata `None`/`""` coma "non filtrar por esta clave").
- Crear/editar/eliminar seguen facendo `ui.navigate.reload()` coma hoxe; isto recarga a lista completa e reinicia os filtros a "sen filtro" — comportamento aceptado, non hai que preservalo.
- 10 filas por páxina por defecto en todas as táboas (`pagination=10` no construtor de `ui.table`).
- A busca/filtro debe estar dispoñible tamén para quen só ten permiso de lectura (`pode_editar=False` en Parcelas/Animais) — non pode quedar detrás do `if not pode_editar: return` que corta o resto de cada sección.

## Review Focus

- Buscar un termo que coincide nunha fila, pero esa fila non cumpre o filtro estruturado activo (Estado/Rol/Activo) → non debe aparecer; busca e filtro estruturado combínanse en AND, non son alternativas. [Task 1]
- Cambiar o selector de volta a "Todos" despois de ter un filtro activo → deben volver aparecer todas as filas que cumpran só o resto de criterios — o sentinela ten que funcionar tamén ao "desactivar" o filtro, non só ao cargar a páxina por primeira vez. [Task 1 + verificación manual en Tasks 2-5]
- Baleirar o input de busca (botón "clear" ou borrar todo o texto) → deben volver aparecer todas as filas, non quedar "atascado" no último termo buscado. [Task 1 + verificación manual]
- Unha táboa con máis de 10 filas, cun filtro activo que deixa máis de 10 resultado → a paxinación ten que actuar sobre as filas xa filtradas (filtrar primeiro, paxinar despois), non amosar páxinas baseadas na lista completa sen filtrar. [Verificación manual en Tasks 2-3, con datos de proba temporais]
- Un usuario só con permiso de lectura nunha horta (`pode_editar=False`) ten que poder buscar/filtrar Parcelas e Animais igual que un editor — a UI de busca/filtro non pode quedar oculta ou omitida polo camiño de "só lectura". [Tasks 2-3, comprobación explícita na orde do código]

---

## Task 1: `filtrar_filas()` — función pura de filtrado

**Files:**
- Create: `src/horta/ui/filtros.py`
- Test: `tests/ui/test_filtros.py`

**Interfaces:**
- Produces: `horta.ui.filtros.filtrar_filas(filas: list[dict], texto: str, campos_busca: list[str], filtros_estruturados: dict[str, str | None] | None = None) -> list[dict]`. As Tasks 2-5 importan e chaman esta función; a sinatura e o comportamento do sentinela (`None`/`""` non filtra por esa clave) son os que consomen.

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/ui/test_filtros.py`:

```python
from horta.ui.filtros import filtrar_filas

_FILAS = [
    {"nome": "Parcela do Alto", "estado": "activa"},
    {"nome": "Parcela do Río", "estado": "inactiva"},
    {"nome": "Horta Vella", "estado": "activa"},
]


def test_filtrar_filas_texto_baleiro_devolve_todo():
    assert filtrar_filas(_FILAS, "", ["nome"]) == _FILAS


def test_filtrar_filas_busca_por_subcadea_sen_distinguir_maiusculas():
    resultado = filtrar_filas(_FILAS, "ALTO", ["nome"])
    assert resultado == [_FILAS[0]]


def test_filtrar_filas_busca_sen_coincidencias():
    assert filtrar_filas(_FILAS, "inexistente", ["nome"]) == []


def test_filtrar_filas_so_filtro_estruturado():
    resultado = filtrar_filas(_FILAS, "", ["nome"], {"estado": "activa"})
    assert resultado == [_FILAS[0], _FILAS[2]]


def test_filtrar_filas_texto_e_filtro_combinados():
    resultado = filtrar_filas(_FILAS, "horta", ["nome"], {"estado": "activa"})
    assert resultado == [_FILAS[2]]


def test_filtrar_filas_sentinela_todos_non_filtra():
    assert filtrar_filas(_FILAS, "", ["nome"], {"estado": None}) == _FILAS
    assert filtrar_filas(_FILAS, "", ["nome"], {"estado": ""}) == _FILAS


def test_filtrar_filas_non_normaliza_acentos():
    # Límite coñecido e aceptado: buscar sen til non atopa "Río".
    assert filtrar_filas(_FILAS, "rio", ["nome"]) == []
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/ui/test_filtros.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.ui.filtros'`)

- [ ] **Step 3: Implementar `src/horta/ui/filtros.py`**

```python
from __future__ import annotations


def filtrar_filas(
    filas: list[dict],
    texto: str,
    campos_busca: list[str],
    filtros_estruturados: dict[str, str | None] | None = None,
) -> list[dict]:
    """Filtra unha lista de filas por busca de texto (subcadea, sen distinguir
    maiúsculas/minúsculas) e por criterios estruturados de coincidencia exacta
    (p.ex. {"estado": "activa"}). Unha clave con valor None ou "" en
    filtros_estruturados non filtra por ese campo (sentinela "sen filtro")."""
    texto_normalizado = texto.casefold()
    filtros = {
        campo: valor for campo, valor in (filtros_estruturados or {}).items() if valor
    }

    def coincide(fila: dict) -> bool:
        if texto_normalizado and not any(
            texto_normalizado in str(fila.get(campo, "")).casefold() for campo in campos_busca
        ):
            return False
        return all(str(fila.get(campo)) == valor for campo, valor in filtros.items())

    return [fila for fila in filas if coincide(fila)]
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/ui/test_filtros.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/horta/ui/filtros.py tests/ui/test_filtros.py
git commit -m "feat: engadir filtrar_filas() para busca e filtros de táboas"
```

---

## Task 2: Busca, filtro e paxinación en Parcelas

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.ui.filtros.filtrar_filas` (Task 1).
- Produces: constantes de módulo `_ESTADOS_PARCELA`, `_ESTADOS_ANIMAL`, `_ROLES_HORTA` (as tres engádense nesta tarefa, aínda que só `_ESTADOS_PARCELA` se usa aquí) — as Tasks 3 e 4 consomen `_ESTADOS_ANIMAL` e `_ROLES_HORTA` respectivamente, xa presentes tras esta tarefa.

- [ ] **Step 1: Engadir o import e as constantes de módulo**

En `src/horta/ui/pages/horta_detalle.py`, engadir o import despois de `from horta.ui.confirmacion import confirmar_eliminacion`:

```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.nav import cabeceira_paxina
```

Engadir estas tres constantes despois de `_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}` (liña 40):

```python
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_ESTADOS_PARCELA = ("activa", "inactiva")
_ESTADOS_ANIMAL = ("activo", "baixa")
_ROLES_HORTA = ("admin", "editor", "lector")
```

- [ ] **Step 2: Engadir busca, filtro de Estado e paxinación á táboa de Parcelas**

Dentro de `_seccion_parcelas`, substituír este bloque:

```python
    rows = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
        for p in parcelas
    ]
    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "superficie", "label": "Superficie", "field": "superficie"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=rows,
            row_key="id",
            selection="single" if pode_editar else None,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    if not pode_editar:
        return
```

por:

```python
    todas_as_filas = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
        for p in parcelas
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(
            ["Todos", *_ESTADOS_PARCELA], label="Estado", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "superficie", "label": "Superficie", "field": "superficie"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["nome", "superficie", "estado"],
            {"estado": estado_filtro},
        )
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return
```

Nota: a fila de busca/filtro e a definición de `refrescar_taboa` van **antes** do `if not pode_editar: return` — quen só ten permiso de lectura tamén ten que poder buscar e filtrar.

- [ ] **Step 3: Reutilizar a constante no selector de Estado do diálogo de edición**

Substituír:

```python
        estado_edit = ui.select(["activa", "inactiva"], label="Estado", value="activa")
```

por:

```python
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")
```

- [ ] **Step 4: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (todos os tests existentes, sen regresións — esta tarefa non engade tests novos, xa que as páxinas NiceGUI non se testean unitariamente neste proxecto)

- [ ] **Step 5: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 6: Verificación manual**

Run: `uv run python src/horta/main.py` (en segundo plano)

Con sesión dun usuario con acceso a unha horta con parcelas:
1. Ir a `/hortas/{id}`, pestana Parcelas. Escribir no input "Buscar" un termo que coincida co nome dunha parcela → a táboa amosa só as que coinciden. Baleirar o input (botón clear ou borrar todo) → volven aparecer todas.
2. Cambiar o selector "Estado" a "activa" → só as parcelas activas. Volver a "Todos" → todas de novo.
3. Combinar busca + selector Estado á vez → só as que cumpren ambos criterios.
4. Se a horta ten 10 ou menos parcelas, crear temporalmente (vía o modelo/servizo, non a UI, coma se fixo na iteración anterior) parcelas de proba abondo para superar as 10, recargar a páxina e confirmar que aparece a paxinación e que funciona á vez cun filtro activo (filtra primeiro, pagina despois). Eliminar as parcelas de proba ao terminar, deixando a BD como estaba.
5. Se o usuario de proba só ten rol de lector nesa horta, confirmar que a busca/filtro tamén funciona (non só para editores).

Parar o servidor despois de verificar.

- [ ] **Step 7: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir busca, filtro de estado e paxinación en Parcelas"
```

---

## Task 3: Busca, filtro e paxinación en Animais

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.ui.filtros.filtrar_filas` (Task 1); `_ESTADOS_ANIMAL` (constante xa engadida na Task 2).

- [ ] **Step 1: Engadir busca, filtro de Estado e paxinación á táboa de Animais**

Dentro de `_seccion_animais`, substituír este bloque:

```python
    rows = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
        }
        for a in animais
    ]
    taboa = (
        ui.table(
            columns=[
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "raza", "label": "Raza", "field": "raza"},
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=rows,
            row_key="id",
            selection="single" if pode_editar else None,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    if not pode_editar:
        return
```

por:

```python
    todas_as_filas = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
        }
        for a in animais
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(
            ["Todos", *_ESTADOS_ANIMAL], label="Estado", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "raza", "label": "Raza", "field": "raza"},
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["especie", "raza", "cantidade", "estado"],
            {"estado": estado_filtro},
        )
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return
```

Nota: mesma orde que na Task 2 — busca/filtro antes do `if not pode_editar: return`.

- [ ] **Step 2: Reutilizar a constante no selector de Estado do diálogo de edición**

Substituír:

```python
        estado_edit = ui.select(["activo", "baixa"], label="Estado", value="activo")
```

por:

```python
        estado_edit = ui.select(list(_ESTADOS_ANIMAL), label="Estado", value="activo")
```

- [ ] **Step 3: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións)

- [ ] **Step 4: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 5: Verificación manual**

Mesmo procedemento que na Task 2, Step 6, pero na pestana Animais (busca por especie/raza, filtro por Estado activo/baixa, combinación, paxinación con datos de proba temporais, e confirmar que funciona tamén para un lector).

- [ ] **Step 6: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir busca, filtro de estado e paxinación en Animais"
```

---

## Task 4: Busca, filtro e paxinación en Membros

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.ui.filtros.filtrar_filas` (Task 1); `_ROLES_HORTA` (constante xa engadida na Task 2).

- [ ] **Step 1: Engadir busca, filtro de Rol e paxinación á táboa de Membros**

Dentro de `_seccion_membros`, substituír:

```python
    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Membros").classes("text-lg font-bold")
        ui.button("Engadir membro", icon="person_add", on_click=dialog_engadir.open)

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
            ],
            rows=filas,
            row_key="usuario_id",
            selection="single",
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )
```

por:

```python
    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Membros").classes("text-lg font-bold")
        ui.button("Engadir membro", icon="person_add", on_click=dialog_engadir.open)

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        rol_select = ui.select(
            ["Todos", *_ROLES_HORTA], label="Rol", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
            ],
            rows=filas,
            row_key="usuario_id",
            selection="single",
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        rol_filtro = None if rol_select.value == "Todos" else rol_select.value
        taboa.rows = filtrar_filas(
            filas,
            busca_input.value or "",
            ["nome", "email", "rol"],
            {"rol": rol_filtro},
        )
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    rol_select.on_value_change(refrescar_taboa)
```

Nota: `filas` xa é a lista completa cargada ao principio de `_seccion_membros` (non hai que renomeala, a diferenza de Parcelas/Animais onde a variable orixinal se chamaba `rows`).

- [ ] **Step 2: Reutilizar a constante `_ROLES_HORTA` nos dous selectores de Rol xa existentes**

Substituír (dentro de `dialog_engadir`):

```python
        rol_input = ui.select(["admin", "editor", "lector"], value="lector")
```

por:

```python
        rol_input = ui.select(list(_ROLES_HORTA), value="lector")
```

Substituír (dentro de `dialog_cambiar_rol`):

```python
        rol_edit = ui.select(["admin", "editor", "lector"], value="lector")
```

por:

```python
        rol_edit = ui.select(list(_ROLES_HORTA), value="lector")
```

- [ ] **Step 3: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións)

- [ ] **Step 4: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 5: Verificación manual**

Mesmo procedemento que nas Tasks anteriores, na pestana Membros (busca por nome/email, filtro por Rol, combinación). A táboa de Membros non ten a distinción lector/editor (só é visible para admin de horta), así que non fai falta comprobar ese caso aquí.

- [ ] **Step 6: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir busca, filtro de rol e paxinación en Membros"
```

---

## Task 5: Busca, filtro e paxinación en Usuarios (admin)

**Files:**
- Modify: `src/horta/ui/admin/usuarios.py`

**Interfaces:**
- Consumes: `horta.ui.filtros.filtrar_filas` (Task 1). Non depende das Tasks 2-4 (ficheiro distinto).
- Produces: constante de módulo `_ROLES_USUARIO`, só usada neste ficheiro.

- [ ] **Step 1: Engadir o import e a constante de módulo**

En `src/horta/ui/admin/usuarios.py`, engadir o import despois de `from horta.ui.accions import executar_accion`:

```python
from horta.ui.accions import executar_accion
from horta.ui.filtros import filtrar_filas
from horta.ui.nav import cabeceira_paxina
```

Engadir esta constante despois de `_PROPS_TABOA = 'dense no-data-label="Non hai usuarios"'`:

```python
_PROPS_TABOA = 'dense no-data-label="Non hai usuarios"'

_ROLES_USUARIO = ("admin", "usuario")
```

- [ ] **Step 2: Engadir busca, filtros de Rol/Activo e paxinación á táboa de Usuarios**

Substituír:

```python
    ui.label("Selecciona un usuario na táboa para editalo.").classes("text-caption")
    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
                {"name": "activo", "label": "Activo", "field": "activo"},
            ],
            rows=rows,
            row_key="id",
            selection="single",
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )
```

por:

```python
    ui.label("Selecciona un usuario na táboa para editalo.").classes("text-caption")

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        rol_filtro_select = ui.select(
            ["Todos", *_ROLES_USUARIO], label="Rol", value="Todos"
        ).props("dense")
        activo_select = ui.select(
            ["Todos", "si", "non"], label="Activo", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
                {"name": "activo", "label": "Activo", "field": "activo"},
            ],
            rows=rows,
            row_key="id",
            selection="single",
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        rol_filtro = None if rol_filtro_select.value == "Todos" else rol_filtro_select.value
        activo_filtro = None if activo_select.value == "Todos" else activo_select.value
        taboa.rows = filtrar_filas(
            rows,
            busca_input.value or "",
            ["nome", "email", "rol", "activo"],
            {"rol": rol_filtro, "activo": activo_filtro},
        )
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    rol_filtro_select.on_value_change(refrescar_taboa)
    activo_select.on_value_change(refrescar_taboa)
```

Nota: `rows` xa garda `activo` coma texto (`"si"`/`"non"`, ver liña `"activo": "si" if u.activo else "non"`), non coma booleano — o filtro compara directamente contra ese texto, sen necesidade de ningún campo derivado.

**Importante — colisión de nomes evitada a propósito:** este ficheiro xa ten unha variable chamada `rol_select` dentro do diálogo "Crear usuario" (`rol_select = ui.select(["admin", "usuario"], value="usuario")`, máis abaixo na Step 3). Un bloque `with ui.dialog() as ..., ui.card():` NON crea un ámbito novo en Python — segue sendo o mesmo ámbito da función `admin_usuarios_page` — así que se o selector de filtro deste Step tamén se chamase `rol_select`, rebindaría ese nome e o diálogo "Crear usuario" pasaría a ler o valor do filtro en vez do seu propio selector. Por iso o selector de filtro chámase `rol_filtro_select`, non `rol_select`. Non renomear.

- [ ] **Step 3: Reutilizar a constante `_ROLES_USUARIO` nos dous selectores de Rol xa existentes**

Substituír (dentro de `dialog_crear`):

```python
        rol_select = ui.select(["admin", "usuario"], value="usuario")
```

por:

```python
        rol_select = ui.select(list(_ROLES_USUARIO), value="usuario")
```

Substituír (dentro de `dialog_editar`):

```python
        rol_edit = ui.select(["admin", "usuario"], value="usuario")
```

por:

```python
        rol_edit = ui.select(list(_ROLES_USUARIO), value="usuario")
```

- [ ] **Step 4: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións)

- [ ] **Step 5: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

- [ ] **Step 6: Verificación manual**

Run: `uv run python src/horta/main.py` (en segundo plano)

Con sesión de admin global:
1. Ir a `/admin/usuarios`. Buscar por nome/email dun usuario → só ese aparece.
2. Filtrar por Rol "admin" → só os admins. Volver a "Todos".
3. Filtrar por Activo "non" → só os desactivados (se hai algún; se non hai ningún, desactivar temporalmente un usuario de proba non crítico, comprobar o filtro, e reactivalo despois).
4. Combinar busca + Rol + Activo á vez.
5. Se hai 10 ou menos usuarios, crear temporalmente (vía o servizo, non a UI) usuarios de proba abondo para superar as 10, confirmar a paxinación combinada cun filtro activo, e eliminalos despois.

Parar o servidor despois de verificar.

- [ ] **Step 7: Commit**

```bash
git add src/horta/ui/admin/usuarios.py
git commit -m "feat: engadir busca, filtros de rol/activo e paxinación en Usuarios"
```

---

## Task 6: Verificación final de conxunto

**Files:**
- Ningún ficheiro novo — só verificación.

- [ ] **Step 1: Executar toda a suite de tests**

Run: `uv run pytest -v`
Expected: todos os tests pasan (os existentes máis os 7 novos de `tests/ui/test_filtros.py`).

- [ ] **Step 2: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 3: Verificación manual de conxunto**

Run: `uv run python src/horta/main.py` (en segundo plano)

1. Login normal, entrar nunha horta con parcelas e animais, navegar polas tres pestanas (Parcelas, Animais, Membros se es admin da horta) confirmando que cada táboa amosa a súa propia fila de busca/filtro sen interferir coas outras (son seccións independentes na mesma páxina).
2. Ir a `/admin/usuarios` (se es admin global) e confirmar o mesmo alí.
3. Confirmar que crear/editar/eliminar en calquera táboa segue funcionando con normalidade tras engadir busca/filtro/paxinación (o `ui.navigate.reload()` reinicia os filtros, comportamento esperado).

Parar o servidor despois de verificar.

- [ ] **Step 4: Commit final (só se houbo que corrixir algo nos pasos 1-2)**

```bash
git add -A
git commit -m "chore: corrixir avisos tras a verificación final"
```

(Omitir este commit se non houbo cambios que facer.)

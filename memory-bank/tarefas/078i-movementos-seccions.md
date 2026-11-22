# Tarefa 078i — Entradas e saídas de animais (10/11): seccións

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 078h. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

A sección Animais usa a pantalla nova (sae a vella de horta_detalle) e ábrese a das entradas e saídas. Deseño: `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.catalogos_estado import avisos_catalogos
from horta.services.coidados_animais import en_tempo_espera
```

Despois:
```python
from horta.services.animais import listar_animais
from horta.services.catalogos_estado import avisos_catalogos
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.pages.coidados_animais import seccion_coidados
from horta.ui.pages.colleitas import seccion_colleitas
from horta.ui.pages.cultivos import seccion_cultivos
from horta.ui.pages.diario import Formularios, boton_apuntar_traballo, seccion_diario
from horta.ui.pages.equipo import seccion_equipo
from horta.ui.pages.informes import seccion_informes
from horta.ui.pages.labores import seccion_labores
from horta.ui.pages.maquinaria import seccion_maquinaria
```

Despois:
```python
from horta.ui.pages.animais import seccion_animais
from horta.ui.pages.coidados_animais import seccion_coidados
from horta.ui.pages.colleitas import seccion_colleitas
from horta.ui.pages.cultivos import seccion_cultivos
from horta.ui.pages.diario import Formularios, boton_apuntar_traballo, seccion_diario
from horta.ui.pages.equipo import seccion_equipo
from horta.ui.pages.informes import seccion_informes
from horta.ui.pages.labores import seccion_labores
from horta.ui.pages.maquinaria import seccion_maquinaria
from horta.ui.pages.movementos_animais import seccion_movementos
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
_ESTADOS_PARCELA = ("activa", "inactiva")
_ESTADOS_ANIMAL = ("activo", "baixa")
```

Despois:
```python
_ESTADOS_PARCELA = ("activa", "inactiva")
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        _seccion_animais(horta_id, animais, pode_editar)
    elif seccion == "coidados":
        seccion_coidados(horta_id, pode_editar)
    elif seccion == "equipo":
        seccion_equipo(horta_id, pode_editar, e_horta_admin)
    elif seccion == "maquinaria":
        seccion_maquinaria(horta_id, pode_editar)


def _seccion_animais(horta_id: int, animais: list, pode_editar: bool) -> None:
    if pode_editar:
        with ui.dialog() as dialog_novo_animal, ui.card():
            ui.label("Novo animal").classes("text-md font-bold")
            especie_input = ui.input("Especie (p.ex. galiñas, coellos)")
            raza_input = ui.input("Raza (opcional)")
            cantidade_input = ui.number("Cantidade", value=1)

            def crear() -> None:
                if not especie_input.value:
                    ui.notify("A especie é obrigatoria", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creado = executar_accion(
                        session,
                        lambda: crear_animal(
                            session,
                            actor_actual,
                            horta_id,
                            especie_input.value,
                            date.today(),
                            raza=raza_input.value or None,
                            cantidade=int(cantidade_input.value or 1),
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_animal.close).props("flat")

    with get_session() as session:
        actor = usuario_actual(session)
        espera = en_tempo_espera(session, actor, horta_id) if actor else {}

    with ui.row().classes("w-full items-center justify-between"):
        ui.link("Ver os coidados dos animais", url_seccion(horta_id, "coidados"))
        ui.space()
        if pode_editar:
            ui.button("Novo animal", icon="add", on_click=dialog_novo_animal.open)

    todas_as_filas = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
            "espera": f"En tempo de espera ata {espera[a.id]:%d/%m/%Y}" if a.id in espera
            else "",
        }
        for a in animais
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(["Todos", *_ESTADOS_ANIMAL], label="Estado", value="Todos").props(
            "dense"
        )

    taboa = (
        ui.table(
            columns=[
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "raza", "label": "Raza", "field": "raza"},
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
                {"name": "espera", "label": "Medicamentos", "field": "espera"},
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
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f'Eliminar "{taboa.selected[0]["especie"]}"? Esta acción non se pode desfacer.',
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar animal").classes("text-md font-bold")
        especie_edit = ui.input("Especie")
        raza_edit = ui.input("Raza")
        cantidade_edit = ui.number("Cantidade")
        estado_edit = ui.select(list(_ESTADOS_ANIMAL), label="Estado", value="activo")

        def gardar() -> None:
            if not taboa.selected:
                return
            animal_id = taboa.selected[0]["id"]
            if not especie_edit.value:
                ui.notify("A especie é obrigatoria", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        a
                        for a in listar_animais(session, actor_actual, horta_id)
                        if a.id == animal_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese animal xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_animal(
                        session,
                        actor_actual,
                        obxectivo,
                        especie=especie_edit.value,
                        raza=raza_edit.value or None,
                        cantidade=int(cantidade_edit.value or 1),
                        estado=estado_edit.value,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        especie_edit.value = fila["especie"]
        raza_edit.value = fila["raza"]
        cantidade_edit.value = fila["cantidade"]
        estado_edit.value = fila["estado"]
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        animal_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (a for a in listar_animais(session, actor_actual, horta_id) if a.id == animal_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese animal xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_animal(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()
```

Despois:
```python
        seccion_animais(horta_id, pode_editar)
    elif seccion == "movementos":
        seccion_movementos(horta_id, pode_editar)
    elif seccion == "coidados":
        seccion_coidados(horta_id, pode_editar)
    elif seccion == "equipo":
        seccion_equipo(horta_id, pode_editar, e_horta_admin)
    elif seccion == "maquinaria":
        seccion_maquinaria(horta_id, pode_editar)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Entradas e saídas de animais (10/11): seccións: feito.

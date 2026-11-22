# Tarefa 080f — Pastoreo (7/11): botóns en Animais

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 080e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Columna «Pasto» e botóns «Ao pasto» e «Saíron do pasto» nos grupos de animais, e ligazón «Ver o pastoreo». Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/animais.py`

Antes:
```python
os movementos e a produción teñen as súas táboas."""
```

Despois:
```python
os movementos, a produción e o pastoreo teñen as súas táboas."""
```

### Paso 2 — `src/horta/ui/pages/animais.py`

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.movementos_animais import dialogo_movemento
```

Despois:
```python
from horta.services.pastoreos import no_pasto, nomes_leiras
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.filtros import filtrar_filas
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.pages.pastoreos import dialogo_pastoreo, dialogo_saida
```

### Paso 3 — `src/horta/ui/pages/animais.py`

Antes:
```python
        razas = [(v.codigo, v.descricion) for v in valores_vixentes(session, "raza")]

    with ui.row().classes("w-full items-center gap-4"):
        ui.link("Ver as entradas e saídas", url_seccion(horta_id, "movementos"))
        ui.link("Ver os coidados", url_seccion(horta_id, "coidados"))
        ui.link("Ver a produción", url_seccion(horta_id, "producion"))

    todas_as_filas = [{
        "id": a.id,
        "nome": a.especie,
        "especie": ESPECIES.get(a.especie_codigo or "", ""),
        "raza": a.raza or "",
        "cantidade": a.cantidade,
        "estado": a.estado,
        "espera": f"En tempo de espera ata {espera[a.id]:%d/%m/%Y}" if a.id in espera else "",
    } for a in animais]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca = ui.input("Buscar").props("dense clearable")
        estado = ui.select({"": "Todos", "activo": "De alta", "baixa": "De baixa"},
                           label="Estado", value="activo").props("dense")

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Grupo"), ("especie", "Especie"), ("raza", "Raza"),
            ("cantidade", "Cantos"), ("espera", "Medicamentos"))],
```

Despois:
```python
        pastos = {animal_id: (pa.id, f"No pasto: {nomes_leiras(session, pa)} desde o "
                                     f"{pa.data_inicio:%d/%m}")
                  for animal_id, pa in no_pasto(session, actor, horta_id).items()}
        razas = [(v.codigo, v.descricion) for v in valores_vixentes(session, "raza")]

    with ui.row().classes("w-full items-center gap-4"):
        ui.link("Ver as entradas e saídas", url_seccion(horta_id, "movementos"))
        ui.link("Ver os coidados", url_seccion(horta_id, "coidados"))
        ui.link("Ver a produción", url_seccion(horta_id, "producion"))
        ui.link("Ver o pastoreo", url_seccion(horta_id, "pastoreo"))

    todas_as_filas = [{
        "id": a.id,
        "nome": a.especie,
        "especie": ESPECIES.get(a.especie_codigo or "", ""),
        "raza": a.raza or "",
        "cantidade": a.cantidade,
        "estado": a.estado,
        "espera": f"En tempo de espera ata {espera[a.id]:%d/%m/%Y}" if a.id in espera else "",
        "pasto": pastos[a.id][1] if a.id in pastos else "",
    } for a in animais]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca = ui.input("Buscar").props("dense clearable")
        estado = ui.select({"": "Todos", "activo": "De alta", "baixa": "De baixa"},
                           label="Estado", value="activo").props("dense")

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Grupo"), ("especie", "Especie"), ("raza", "Raza"),
            ("cantidade", "Cantos"), ("espera", "Medicamentos"), ("pasto", "Pasto"))],
```

### Paso 4 — `src/horta/ui/pages/animais.py`

Antes:
```python
    abrir_producion = dialogo_producion(horta_id)
```

Despois:
```python
    abrir_producion = dialogo_producion(horta_id)
    abrir_pastoreo = dialogo_pastoreo(horta_id)
    abrir_saida = dialogo_saida()
```

### Paso 5 — `src/horta/ui/pages/animais.py`

Antes:
```python
        abrir_producion(None, None, taboa.selected[0]["id"] if taboa.selected else None)

```

Despois:
```python
        abrir_producion(None, None, taboa.selected[0]["id"] if taboa.selected else None)

    def ao_pasto() -> None:
        abrir_pastoreo(None, None, taboa.selected[0]["id"] if taboa.selected else None)

    def saida_do_pasto() -> None:
        animal = seleccionado()
        if animal is None:
            return
        if animal.id not in pastos:
            ui.notify("Este grupo non está no pasto", type="warning")
            return
        abrir_saida(pastos[animal.id][0])

```

### Paso 6 — `src/horta/ui/pages/animais.py`

Antes:
```python
        ui.button("Produción", icon="egg", on_click=producion).props("outline")
```

Despois:
```python
        ui.button("Produción", icon="egg", on_click=producion).props("outline")
        ui.button("Ao pasto", icon="landscape", on_click=ao_pasto).props("outline")
        ui.button("Saíron do pasto", icon="logout", on_click=saida_do_pasto).props("outline")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (7/11): botóns en Animais: feito.

# Tarefa 077g — Coidado dos animais (8/10): nova tarefa con animais

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 077d. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O diálogo «Nova tarefa» deixa escoller un grupo de animais. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/dialogo_tarefa.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
from horta.services.cultivos import listar_cultivos
from horta.services.diario import TIPOS
```

Despois:
```python
from horta.services.animais import listar_animais
from horta.services.cultivos import listar_cultivos
from horta.services.diario import TIPOS, nome_grupo
```

### Paso 2 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
    return tipos, persoas


```

Despois:
```python
    return tipos, persoas


def opcions_animais(session: Session, actor: Usuario, horta_id: int) -> dict[int | str, str]:
    """Os grupos de animais de alta, para unha tarefa que se refira a eles (opcional)."""
    return {"": "(sen animais)", **{a.id: nome_grupo(a.especie, a.raza)
                                    for a in listar_animais(session, actor, horta_id)
                                    if a.estado == "activo"}}


```

### Paso 3 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python

    with ui.dialog() as dialogo, ui.card():
        ui.label("Nova tarefa").classes("text-md font-bold")
        descricion = ui.input("Que hai que facer").classes("w-full")
        tipo = ui.select(opcions_tipo, label="Que traballo é", value="").classes("w-full")
        parcela = ui.select(opcions_parcela, label="Parcela", value="").classes("w-full")
        cultivo = ui.select(opcions_cultivo, label="Cultivo", value="").classes("w-full")
```

Despois:
```python
        opcions_animal = opcions_animais(session, actor, horta_id)

    with ui.dialog() as dialogo, ui.card():
        ui.label("Nova tarefa").classes("text-md font-bold")
        descricion = ui.input("Que hai que facer").classes("w-full")
        tipo = ui.select(opcions_tipo, label="Que traballo é", value="").classes("w-full")
        parcela = ui.select(opcions_parcela, label="Parcela", value="").classes("w-full")
        cultivo = ui.select(opcions_cultivo, label="Cultivo", value="").classes("w-full")
        animal = ui.select(opcions_animal, label="Animais", value="").classes("w-full")
```

### Paso 4 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
                    parcela_id=parcela.value or None, cultivo_id=cultivo.value or None,
```

Despois:
```python
                    parcela_id=parcela.value or None, cultivo_id=cultivo.value or None,
                    animal_id=animal.value or None,
```

### Paso 5 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
        parcela.value = cultivo.value = tipo.value = persoa.value = ""
```

Despois:
```python
        parcela.value = cultivo.value = animal.value = tipo.value = persoa.value = ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (8/10): nova tarefa con animais: feito.

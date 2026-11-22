# Tarefa 077c — Coidado dos animais (4/10): tarefa de coidado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 077. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Unha tarefa pode ser de coidado de animais e referirse a un grupo de animais desta explotación. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/tarefas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.analise import Analise
```

Despois:
```python
from horta.models.analise import Analise
from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
```

### Paso 2 — `src/horta/services/tarefas.py`

Antes:
```python
        "cultivo_id",
```

Despois:
```python
        "cultivo_id",
        "animal_id",
```

### Paso 3 — `src/horta/services/tarefas.py`

Antes:
```python
    "tratamento_instalacion": (TratamentoInstalacion, "data"),
```

Despois:
```python
    "tratamento_instalacion": (TratamentoInstalacion, "data"),
    "coidado_animal": (CoidadoAnimal, "data_inicio"),
```

### Paso 4 — `src/horta/services/tarefas.py`

Antes:
```python
def crear_tarefa(
    session: Session,
    actor: Usuario,
    horta_id: int,
    descricion: str,
    **campos: Any,
) -> Tarefa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_datas(campos.get("data"), campos.get("data_limite"))
    _validar_tipo_e_quen(session, horta_id, campos.get("tipo"), campos.get("persoa_id"))
```

Despois:
```python
def _validar_animal(session: Session, horta_id: int, animal_id: int | None) -> None:
    if animal_id is not None:
        animal = session.get(Animal, animal_id)
        if animal is None or animal.horta_id != horta_id:
            raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")


def crear_tarefa(
    session: Session,
    actor: Usuario,
    horta_id: int,
    descricion: str,
    **campos: Any,
) -> Tarefa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_datas(campos.get("data"), campos.get("data_limite"))
    _validar_tipo_e_quen(session, horta_id, campos.get("tipo"), campos.get("persoa_id"))
    _validar_animal(session, horta_id, campos.get("animal_id"))
```

### Paso 5 — `src/horta/services/tarefas.py`

Antes:
```python
                         cambios.get("persoa_id", tarefa.persoa_id))
```

Despois:
```python
                         cambios.get("persoa_id", tarefa.persoa_id))
    _validar_animal(session, tarefa.horta_id, cambios.get("animal_id", tarefa.animal_id))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (4/10): tarefa de coidado: feito.

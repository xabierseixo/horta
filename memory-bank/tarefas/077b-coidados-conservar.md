# Tarefa 077b — Coidado dos animais (3/10): non borrar grupos con coidados

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 077a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Un grupo de animais con coidados apuntados non se pode borrar (dáselle de baixa); tampouco a explotación. Ao borrar un grupo sen coidados, as tarefas que o nomean quedan sen animais. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/animais.py`
- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/animais.py`

Antes:
```python
from horta.models.usuario import Usuario
```

Despois:
```python
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.coidados_animais import ten_coidados
```

### Paso 2 — `src/horta/services/animais.py`

Antes:
```python
def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
```

Despois:
```python
def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if ten_coidados(session, animal.id):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados apuntados e debe conservarse (obriga legal): dálle de baixa")
    session.query(Tarefa).filter_by(animal_id=animal.id).update({"animal_id": None})
```

### Paso 3 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.animal import Animal
```

Despois:
```python
from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
```

### Paso 4 — `src/horta/services/hortas.py`

Antes:
```python
            "Esta explotación ten labores rexistrados e debe conservarse (obriga legal)."
        )
```

Despois:
```python
            "Esta explotación ten labores rexistrados e debe conservarse (obriga legal)."
        )
    if session.query(CoidadoAnimal).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten coidados de animais rexistrados e debe conservarse "
            "(obriga legal)."
        )
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (3/10): non borrar grupos con coidados: feito.

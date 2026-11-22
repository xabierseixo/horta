# Tarefa 076k — Tarefas por facer (12/16): nova tarefa con tipo e quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O diálogo «Nova tarefa» pregunta que traballo é e quen o vai facer. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/dialogo_tarefa.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python

from horta.db import get_session
from horta.services.cultivos import listar_cultivos
from horta.services.parcelas import listar_parcelas
from horta.services.tarefas import crear_tarefa
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual

PRIORIDADES_TAREFA = ("baixa", "media", "alta")
```

Despois:
```python
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.usuario import Usuario
from horta.services.cultivos import listar_cultivos
from horta.services.diario import TIPOS
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_persoas
from horta.services.tarefas import TIPOS_TAREFA, crear_tarefa
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual

PRIORIDADES_TAREFA = ("baixa", "media", "alta")


def opcions_tarefa(
    session: Session, actor: Usuario, horta_id: int
) -> tuple[dict[str, str], dict[int | str, str]]:
    """Que traballo é (baleiro = outro) e quen o vai facer (opcional)."""
    tipos = {"": "Outro traballo", **{tipo: TIPOS[tipo] for tipo in TIPOS_TAREFA}}
    persoas: dict[int | str, str] = {"": "(sen decidir)", **{
        p.id: p.nome for p in listar_persoas(session, actor, horta_id)}}
    return tipos, persoas
```

### Paso 2 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python

    with ui.dialog() as dialogo, ui.card():
        ui.label("Nova tarefa").classes("text-md font-bold")
        descricion = ui.input("Que hai que facer").classes("w-full")
        parcela = ui.select(opcions_parcela, label="Parcela", value="").classes("w-full")
        cultivo = ui.select(opcions_cultivo, label="Cultivo", value="").classes("w-full")
```

Despois:
```python
        opcions_tipo, opcions_persoa = opcions_tarefa(session, actor, horta_id)

    with ui.dialog() as dialogo, ui.card():
        ui.label("Nova tarefa").classes("text-md font-bold")
        descricion = ui.input("Que hai que facer").classes("w-full")
        tipo = ui.select(opcions_tipo, label="Que traballo é", value="").classes("w-full")
        parcela = ui.select(opcions_parcela, label="Parcela", value="").classes("w-full")
        cultivo = ui.select(opcions_cultivo, label="Cultivo", value="").classes("w-full")
        persoa = ui.select(opcions_persoa, label="Quen o vai facer", value="").classes("w-full")
```

### Paso 3 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
                    parcela_id=parcela.value or None, cultivo_id=cultivo.value or None,
```

Despois:
```python
                    parcela_id=parcela.value or None, cultivo_id=cultivo.value or None,
                    tipo=tipo.value or None, persoa_id=persoa.value or None,
```

### Paso 4 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
        parcela.value = cultivo.value = ""
```

Despois:
```python
        parcela.value = cultivo.value = tipo.value = persoa.value = ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (12/16): nova tarefa con tipo e quen: feito.

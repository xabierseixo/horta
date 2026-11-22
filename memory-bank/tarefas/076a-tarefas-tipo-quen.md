# Tarefa 076a — Tarefas por facer (2/16): o servizo admite tipo e quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Crear ou editar unha tarefa admite o tipo de traballo (dos que se poden planificar) e quen o vai facer (da explotación). Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/services/tarefas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.horta import RolHorta
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.db import Base
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/tarefas.py`

Antes:
```python
    }
)


def _validar_datas(data: date | None, data_limite: date | None) -> None:
    if data is not None and data_limite is not None and data_limite < data:
        raise OperacionNonPermitidaError("A data límite non pode ser anterior á data prevista")
```

Despois:
```python
        "tipo",
        "persoa_id",
    }
)

# Tipos de traballo que se poden planificar como tarefa, coa táboa e a data de cada un. A
# sementeira non: un cultivo con data de sementeira futura xa é a sementeira por facer.
_TABOA_E_DATA: dict[str, tuple[type[Base], str]] = {
    "tratamento": (TratamentoFito, "data_inicio"),
    "abonado": (Abonado, "data_inicio"),
    "rega": (Rega, "data_inicio"),
    "labor": (Labor, "data_inicio"),
    "colleita": (Colleita, "data"),
    "analise": (Analise, "data_mostraxe"),
    "tratamento_instalacion": (TratamentoInstalacion, "data"),
}
TIPOS_TAREFA = tuple(_TABOA_E_DATA)


def _validar_datas(data: date | None, data_limite: date | None) -> None:
    if data is not None and data_limite is not None and data_limite < data:
        raise OperacionNonPermitidaError("A data límite non pode ser anterior á data prevista")


def _validar_tipo_e_quen(
    session: Session, horta_id: int, tipo: str | None, persoa_id: int | None
) -> None:
    if tipo is not None and tipo not in _TABOA_E_DATA:
        raise OperacionNonPermitidaError("Ese tipo de traballo non se pode planificar")
    comprobar_quen(session, horta_id, persoa_id, None, obrigatoria=False)
```

### Paso 3 — `src/horta/services/tarefas.py`

Antes:
```python
    _validar_datas(campos.get("data"), campos.get("data_limite"))
```

Despois:
```python
    _validar_datas(campos.get("data"), campos.get("data_limite"))
    _validar_tipo_e_quen(session, horta_id, campos.get("tipo"), campos.get("persoa_id"))
```

### Paso 4 — `src/horta/services/tarefas.py`

Antes:
```python
        cambios.get("data_limite", tarefa.data_limite),
    )
```

Despois:
```python
        cambios.get("data_limite", tarefa.data_limite),
    )
    if tarefa.traballo_id is not None and cambios.get("tipo", tarefa.tipo) != tarefa.tipo:
        raise OperacionNonPermitidaError(
            "Esta tarefa xa ten o traballo apuntado: non se pode cambiar o tipo")
    _validar_tipo_e_quen(session, tarefa.horta_id, cambios.get("tipo", tarefa.tipo),
                         cambios.get("persoa_id", tarefa.persoa_id))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (2/16): o servizo admite tipo e quen: feito.

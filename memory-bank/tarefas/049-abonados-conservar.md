# Tarefa 049 — Conservar cultivos e parcelas con abonados

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 047c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os abonados son rexistros do caderno (CUE) e consérvanse, como os tratamentos: non se pode borrar un cultivo, parcela ou explotación que os teña (antes daría un erro da base de datos).

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `src/horta/services/parcelas.py`
- `tests/services/test_abonados_conservar.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: importar

Antes:
```python
from horta.models.colleita import Colleita
```

Despois:
```python
from horta.models.abonado import Abonado
from horta.models.colleita import Colleita
```

### Paso 2 — `src/horta/services/cultivos.py`: non borrar cultivos con abonados

Antes:
```python
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
```

Despois:
```python
    if session.query(Abonado).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten abonados rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
```

### Paso 3 — `src/horta/services/parcelas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.abonado import Abonado
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 4 — `src/horta/services/parcelas.py`: non borrar parcelas con abonados

Antes:
```python
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
```

Despois:
```python
    if ids_cultivos and session.query(Abonado).filter(
        Abonado.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten abonados rexistrados e debe conservarse (obriga legal)."
        )
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
```

### Paso 5 — crear o ficheiro `tests/services/test_abonados_conservar.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.abonado import Abonado
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=0.1, tipo_fertilizacion="1",
                        metodo="1"))
    session.commit()
    return ana, horta, parcela, cultivo


def test_non_se_borra_un_cultivo_con_abonados(session):
    ana, _, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="abonados"):
        eliminar_cultivo(session, ana, cultivo)


def test_non_se_borra_unha_parcela_con_abonados(session):
    ana, _, parcela, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="abonados"):
        eliminar_parcela(session, ana, parcela)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os cultivos e parcelas con abonados non se poden borrar.

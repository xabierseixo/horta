# Tarefa 049b — Conservar explotacións con abonados

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 049. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os abonados son rexistros do caderno (CUE) e consérvanse, como os tratamentos: non se pode borrar un cultivo, parcela ou explotación que os teña (antes daría un erro da base de datos). Ao borrar unha explotación sen abonados bórranse tamén os seus abonos («Os meus abonos»).

## Ficheiros a tocar

- `src/horta/services/hortas.py`
- `tests/services/test_abonados_conservar_horta.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/hortas.py`: importar

Antes:
```python
from horta.models.animal import Animal
```

Despois:
```python
from horta.models.abonado import Abonado, Fertilizante
from horta.models.animal import Animal
```

### Paso 2 — `src/horta/services/hortas.py`: non borrar explotacións con abonados

Antes:
```python
    for tarefa in session.query(Tarefa).filter_by(horta_id=horta.id).all():
```

Despois:
```python
    if session.query(Abonado).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten abonados rexistrados e debe conservarse (obriga legal)."
        )
    session.query(Fertilizante).filter_by(horta_id=horta.id).delete()
    for tarefa in session.query(Tarefa).filter_by(horta_id=horta.id).all():
```

### Paso 3 — crear o ficheiro `tests/services/test_abonados_conservar_horta.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.abonado import Abonado, Fertilizante
from horta.models.horta import Horta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    session.add(Fertilizante(horta_id=horta.id, nome="Esterco", material="5"))
    session.commit()
    return ana, horta


def test_non_se_borra_unha_explotacion_con_abonados(session):
    ana, horta = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=0.1, tipo_fertilizacion="1",
                        metodo="1"))
    session.commit()
    with pytest.raises(OperacionNonPermitidaError, match="abonados"):
        eliminar_horta(session, ana, horta)


def test_borrar_explotacion_sen_abonados_borra_os_seus_abonos(session):
    ana, horta = _escenario(session)
    eliminar_horta(session, ana, horta)
    assert session.get(Horta, horta.id) is None
    assert session.query(Fertilizante).count() == 0
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As explotacións con abonados non se poden borrar; ao borrar unha sen eles vanse os seus abonos.

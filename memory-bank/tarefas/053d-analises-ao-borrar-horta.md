# Tarefa 053d — Análises ao borrar a explotación

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 053c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As análises son voluntarias (CUE: «en caso de haberse realizado»): borrar un cultivo ou unha parcela non se bloquea, pero a análise consérvase na explotación sen esa ligazón. Ao borrar a explotación bórranse as súas análises. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §5. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/services/hortas.py`
- `tests/services/test_analises_borrar.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/hortas.py`: importar

Antes:
```python
from horta.models.abonado import Abonado, Fertilizante
```

Despois:
```python
from horta.models.abonado import Abonado, Fertilizante
from horta.models.analise import Analise
```

### Paso 2 — `src/horta/services/hortas.py`: borrar as análises da explotación

Antes:
```python
    session.query(Fertilizante).filter_by(horta_id=horta.id).delete()
```

Despois:
```python
    session.query(Fertilizante).filter_by(horta_id=horta.id).delete()
    for analise in session.query(Analise).filter_by(horta_id=horta.id).all():
        session.delete(analise)
    session.flush()
```

### Paso 3 — crear o ficheiro `tests/services/test_analises_borrar.py`

Contido completo:
```python
from datetime import date

from horta.models.analise import Analise, AnaliseTipo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    analise = Analise(horta_id=horta.id, material_analizado="3",
                      data_mostraxe=date(2026, 3, 1), parcela_id=parcela.id,
                      cultivo_id=cultivo.id, tipos=[AnaliseTipo(codigo="5")])
    session.add(analise)
    session.commit()
    return ana, horta, parcela, cultivo, analise


def test_borrar_cultivo_conserva_a_analise(session):
    ana, _, _, cultivo, analise = _escenario(session)
    eliminar_cultivo(session, ana, cultivo)
    session.refresh(analise)
    assert analise.cultivo_id is None and analise.parcela_id is not None


def test_borrar_parcela_conserva_a_analise(session):
    ana, _, parcela, _, analise = _escenario(session)
    eliminar_parcela(session, ana, parcela)
    session.refresh(analise)
    assert analise.parcela_id is None and analise.cultivo_id is None


def test_borrar_explotacion_borra_as_analises(session):
    ana, horta, _, _, _ = _escenario(session)
    eliminar_horta(session, ana, horta)
    assert session.query(Analise).count() == 0
    assert session.query(AnaliseTipo).count() == 0
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Borrar cultivos, parcelas e explotacións con análises funciona (con probas).

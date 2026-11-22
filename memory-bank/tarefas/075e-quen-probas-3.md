# Tarefa 075e — Quen e horas: as probas indican quen (3/5)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075d. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As probas do caderno (labores, solos, instalacións) indican quen fixo o traballo. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `tests/services/test_caderno_labores.py`
- `tests/services/test_caderno_solos.py`
- `tests/services/test_caderno_instalacions.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_caderno_labores.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 2 — `tests/services/test_caderno_labores.py`

Antes:
```python
    crear_labor(session, ana, DatosLabor(cultivo_id=cultivo.id, data_inicio=date(2026, 2, 10),
```

Despois:
```python
    crear_labor(session, ana, DatosLabor(cultivo_id=cultivo.id, data_inicio=date(2026, 2, 10),
                                         persoa_id=QUEN,
```

### Paso 3 — `tests/services/test_caderno_solos.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 4 — `tests/services/test_caderno_solos.py`

Antes:
```python
    ana, horta, parcela = _escenario(session)
    crear_analise(session, ana, horta.id, DatosAnalise(
```

Despois:
```python
    ana, horta, parcela = _escenario(session)
    crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
```

### Paso 5 — `tests/services/test_caderno_solos.py`

Antes:
```python
        crear_analise(session, ana, horta.id, DatosAnalise(
```

Despois:
```python
        crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
```

### Paso 6 — `tests/services/test_caderno_instalacions.py`

Antes:
```python

def test_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
```

Despois:
```python
# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1



def test_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(persoa_id=QUEN,
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: as probas indican quen (3/5): feito.

# Tarefa 075h — Quen e horas: a rega esixe quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar unha rega esixe quen o fixo (da explotación) e garda as horas. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/regas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/regas.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/regas.py`

Antes:
```python
def _validar(session: Session, datos: DatosRega, cultivo: Cultivo, hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data da rega non pode ser futura")
```

Despois:
```python
def _validar(session: Session, datos: DatosRega, cultivo: Cultivo, horta_id: int,
             hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data da rega non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

### Paso 3 — `src/horta/services/regas.py`

Antes:
```python
    rega.notas = datos.notas or None
    rega.boas_practicas = [RegaBoaPractica(codigo=c) for c in datos.boas_practicas]


def crear_rega(
    session: Session, actor: Usuario, datos: DatosRega, hoxe: date | None = None
) -> Rega:
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, hoxe or date.today())
```

Despois:
```python
    rega.persoa_id = datos.persoa_id
    rega.horas = datos.horas
    rega.notas = datos.notas or None
    rega.boas_practicas = [RegaBoaPractica(codigo=c) for c in datos.boas_practicas]


def crear_rega(
    session: Session, actor: Usuario, datos: DatosRega, hoxe: date | None = None
) -> Rega:
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, parcela.horta_id, hoxe or date.today())
```

### Paso 4 — `src/horta/services/regas.py`

Antes:
```python
    _validar(session, datos, cultivo, hoxe or date.today())
```

Despois:
```python
    _validar(session, datos, cultivo, rega.horta_id, hoxe or date.today())
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: a rega esixe quen: feito.

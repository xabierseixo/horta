# Tarefa 075j2 — Quen e horas: o tratamento en instalacións esixe quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075j. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar un tratamento en instalacións esixe quen o fixo e garda as horas. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python
def _validar(session: Session, datos: DatosTratamentoInstalacion, hoxe: date) -> None:
    if datos.tipo not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle se é postcolleita, local ou transporte")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data do tratamento non pode ser futura")
```

Despois:
```python
def _validar(session: Session, datos: DatosTratamentoInstalacion, horta_id: int,
             hoxe: date) -> None:
    if datos.tipo not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle se é postcolleita, local ou transporte")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data do tratamento non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

### Paso 3 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
```

Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, horta_id, hoxe or date.today())
```

### Paso 4 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python
    _validar(session, datos, hoxe or date.today())
```

Despois:
```python
    _validar(session, datos, tratamento.horta_id, hoxe or date.today())
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: o tratamento en instalacións esixe quen: feito.

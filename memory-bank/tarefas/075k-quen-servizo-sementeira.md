# Tarefa 075k — Quen e horas: sementeira

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075j2. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O cultivo garda quen fixo a sementeira ou plantación e as horas, e comproba que a persoa sexa da explotación. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/cultivos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/cultivos.py`

Antes:
```python
        "data_adquisicion_material",
```

Despois:
```python
        "data_adquisicion_material",
        "sementeira_persoa_id",
        "sementeira_horas",
```

### Paso 3 — `src/horta/services/cultivos.py`

Antes:
```python
    _validar_rea(session, _valores_rea(None, campos), session.get(Parcela, parcela_id))
```

Despois:
```python
    _validar_rea(session, _valores_rea(None, campos), session.get(Parcela, parcela_id))
    comprobar_quen(session, horta_id, campos.get("sementeira_persoa_id"),
                   campos.get("sementeira_horas"), obrigatoria=False)
```

### Paso 4 — `src/horta/services/cultivos.py`

Antes:
```python
    _validar_rea(session, _valores_rea(cultivo, cambios), parcela)
```

Despois:
```python
    _validar_rea(session, _valores_rea(cultivo, cambios), parcela)
    comprobar_quen(session, horta_id, cambios.get("sementeira_persoa_id"),
                   cambios.get("sementeira_horas"), obrigatoria=False)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: sementeira: feito.

# Tarefa 060b — Servizo de cultivos sen os campos vellos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 060. **Axente**: qwen-66 (mantemento).

## Obxectivo

Paso 2 de 3: o servizo de cultivos deixa de aceptar e validar data_sementeira, data_plantacion, data_colleita_real, cantidade e unidade.

## Ficheiros a tocar

- `src/horta/services/cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`

Antes:
```python
        "variedade",
        "data_sementeira",
        "data_plantacion",
```

Despois:
```python
        "variedade",
```

### Paso 2 — `src/horta/services/cultivos.py`

Antes:
```python
        "data_colleita_prevista",
        "data_colleita_real",
        "cantidade",
        "unidade",
```

Despois:
```python
        "data_colleita_prevista",
```

### Paso 3 — `src/horta/services/cultivos.py`

Antes:
```python
    return session.query(Parcela.horta_id).filter_by(id=parcela_id).scalar()


def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 0:
            raise OperacionNonPermitidaError("A cantidade non pode ser negativa")


def _validar_datas(sementeira: Any, colleita: Any) -> None:
    if sementeira is not None and colleita is not None and colleita < sementeira:
        raise OperacionNonPermitidaError(
            "A data de colleita non pode ser anterior á de sementeira"
        )
```

Despois:
```python
    return session.query(Parcela.horta_id).filter_by(id=parcela_id).scalar()
```

### Paso 4 — `src/horta/services/cultivos.py`

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    _validar_datas(campos.get("data_sementeira"), campos.get("data_colleita_real"))
```

Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
```

### Paso 5 — `src/horta/services/cultivos.py`

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(cambios)
    _validar_datas(
        cambios.get("data_sementeira", cultivo.data_sementeira),
        cambios.get("data_colleita_real", cultivo.data_colleita_real),
    )
```

Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O servizo de cultivos xa non usa os campos vellos.

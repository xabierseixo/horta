# Tarefa 076o — Tarefas por facer (16/16): quen é obrigatorio ao facela

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076n. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Dar por feita unha tarefa sen tipo esixe quen a fixo; as probas indícano. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/services/tarefas.py`
- `tests/services/test_tarefas.py`
- `tests/services/test_diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`

Antes:
```python
    session: Session, actor: Usuario, tarefa: Tarefa, persoa_id: int | None = None,
    data: date | None = None, horas: float | None = None,
) -> Tarefa:
    """Unha tarefa sen tipo (outro traballo) feita: quen a fixo, cando e cantas horas."""
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    if tarefa.tipo is not None:
        raise OperacionNonPermitidaError("Esta tarefa apúntase no formulario do seu tipo")
    comprobar_quen(session, tarefa.horta_id, persoa_id, horas, obrigatoria=False)
```

Despois:
```python
    session: Session, actor: Usuario, tarefa: Tarefa, persoa_id: int | None,
    data: date | None = None, horas: float | None = None,
) -> Tarefa:
    """Unha tarefa sen tipo (outro traballo) feita: quen a fixo, cando e cantas horas."""
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    if tarefa.tipo is not None:
        raise OperacionNonPermitidaError("Esta tarefa apúntase no formulario do seu tipo")
    comprobar_quen(session, tarefa.horta_id, persoa_id, horas)
```

### Paso 2 — `tests/services/test_tarefas.py`

Antes:
```python
    marcar_pendente,
)
```

Despois:
```python
    marcar_pendente,
)

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1
```

### Paso 3 — `tests/services/test_tarefas.py`

Antes:
```python
    feita = marcar_feita(session, ana, tarefa)
```

Despois:
```python
    feita = marcar_feita(session, ana, tarefa, QUEN)
```

### Paso 4 — `tests/services/test_tarefas.py`

Antes:
```python
    marcar_feita(session, ana, feita_hoxe)
```

Despois:
```python
    marcar_feita(session, ana, feita_hoxe, QUEN)
```

### Paso 5 — `tests/services/test_tarefas.py`

Antes:
```python
    marcar_feita(session, ana, feita)
```

Despois:
```python
    marcar_feita(session, ana, feita, QUEN)
```

### Paso 6 — `tests/services/test_diario.py`

Antes:
```python
    marcar_feita(session, ana, tarefa)
```

Despois:
```python
    marcar_feita(session, ana, tarefa, QUEN)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (16/16): quen é obrigatorio ao facela: feito.

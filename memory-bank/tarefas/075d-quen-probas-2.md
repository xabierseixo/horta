# Tarefa 075d — Quen e horas: as probas indican quen (2/5)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As probas de colleita e de tratamentos en instalacións indican quen fixo o traballo. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `tests/services/test_colleitas.py`
- `tests/services/test_caderno_cliente.py`
- `tests/services/test_tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_colleitas.py`

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

### Paso 2 — `tests/services/test_colleitas.py`

Antes:
```python
    return DatosColleita(**{**base, **cambios})
```

Despois:
```python
    return DatosColleita(**{"persoa_id": QUEN, **base, **cambios})
```

### Paso 3 — `tests/services/test_colleitas.py`

Antes:
```python
    ],
)
```

Despois:
```python
    ],
)

```

### Paso 4 — `tests/services/test_caderno_cliente.py`

Antes:
```python

def test_cliente_da_colleita_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Pataca")
    crear_colleita(session, ana, DatosColleita(
```

Despois:
```python
# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1



def test_cliente_da_colleita_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Pataca")
    crear_colleita(session, ana, DatosColleita(persoa_id=QUEN,
```

### Paso 5 — `tests/services/test_tratamentos_instalacion.py`

Antes:
```python
    listar_tratamentos_instalacion,
)
```

Despois:
```python
    listar_tratamentos_instalacion,
)

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 6 — `tests/services/test_tratamentos_instalacion.py`

Antes:
```python
    return DatosTratamentoInstalacion(**base)
```

Despois:
```python
    return DatosTratamentoInstalacion(**{"persoa_id": QUEN, **base})
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: as probas indican quen (2/5): feito.

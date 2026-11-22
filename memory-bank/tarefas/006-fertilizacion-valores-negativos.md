# Tarefa 006 — Non permitir valores negativos nunha fertilización

**Estado**: feita

## Obxectivo

Que `crear_fertilizacion` e `actualizar_fertilizacion` rexeiten valores negativos en `superficie`, `n`, `p`, `k` e `carbono_organico`, cunha mensaxe clara.

## Ficheiros a tocar

- `src/horta/services/fertilizacions.py`
- `tests/services/test_fertilizacions.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/fertilizacions.py`: importar o erro de dominio

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```
Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

### Paso 2 — mesmo ficheiro: nova función de validación

Antes:
```python
def crear_fertilizacion(
```
Despois:
```python
_CAMPOS_NON_NEGATIVOS = ("superficie", "n", "p", "k", "carbono_organico")


def _validar_non_negativos(campos: dict[str, Any]) -> None:
    for campo in _CAMPOS_NON_NEGATIVOS:
        if campo in campos and campos[campo] is not None and campos[campo] < 0:
            raise OperacionNonPermitidaError(f"O campo {campo} non pode ser negativo")


def crear_fertilizacion(
```

### Paso 3 — mesmo ficheiro: chamala ao crear

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    fertilizacion = Fertilizacion(
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_non_negativos(campos)
    fertilizacion = Fertilizacion(
```

### Paso 4 — mesmo ficheiro: chamala ao actualizar

Antes:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(fertilizacion, campo, valor)
```
Despois:
```python
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_non_negativos(cambios)
    for campo, valor in cambios.items():
        setattr(fertilizacion, campo, valor)
```

### Paso 5 — `tests/services/test_fertilizacions.py`: engadir dous tests ao FINAL do ficheiro

Engade este texto ao final do ficheiro (despois da última liña, `    assert fertilizacion.baixa is False`), deixando dúas liñas en branco antes:

```python
@pytest.mark.parametrize("campo", ["superficie", "n", "p", "k", "carbono_organico"])
def test_valor_negativo_ao_crear_fertilizacion(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    with pytest.raises(ValueError, match=f"O campo {campo} non pode ser negativo"):
        crear_fertilizacion(
            session,
            ana,
            cultivo.id,
            date(2026, 4, 1),
            "abonado_fondo",
            "Compost",
            **{campo: -1.0},
        )


def test_valor_negativo_ao_actualizar_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost", n=10.0
    )

    with pytest.raises(ValueError, match="O campo n non pode ser negativo"):
        actualizar_fertilizacion(session, ana, fertilizacion, n=-3.0)

    session.refresh(fertilizacion)
    assert fertilizacion.n == 10.0
```

## Criterios de aceptación

- Crear ou actualizar unha fertilización cun valor negativo en `superficie`, `n`, `p`, `k` ou `carbono_organico` lanza `OperacionNonPermitidaError` coa mensaxe "O campo <nome> non pode ser negativo".
- Valores 0 ou `None` séguense aceptando.
- Os tests novos pasan (6 casos) e os anteriores tamén.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

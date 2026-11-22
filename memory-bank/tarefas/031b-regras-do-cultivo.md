# Tarefa 031b — Regras do cultivo completo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: a parte anterior desta tarefa.

## Obxectivo

Regras do deseño `2026-10-23-cultivo-e-colleitas-design.md` §1: superficie > 0 e non maior ca da parcela, datas coherentes, árbores ou marco (non os dous), data de conversión só en conversión, códigos de catálogo vixentes; e o estado calcúlase coas datas (planificado / en_curso / rematado).

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `tests/services/test_cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: validar e recalcular o estado ao actualizar

Antes:
```python
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
    session.commit()
```

Despois:
```python
    parcela = session.get(Parcela, cultivo.parcela_id)
    _validar_rea(session, _valores_rea(cultivo, cambios), parcela)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
    if "estado" not in cambios and {"data_inicio", "data_fin"} & set(cambios):
        cultivo.estado = calcular_estado(cultivo)
    session.commit()
```

### Paso 2 — `tests/services/test_cultivos.py`: importar

Antes:
```python
from horta.services.cultivos import (
    actualizar_cultivo,
```

Despois:
```python
from horta.services.cultivos import (
    actualizar_cultivo,
    calcular_estado,
```

### Paso 3 — mesmo ficheiro

Antes:
```python
from horta.services.errors import PermisoDenegadoError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
```

### Paso 4 — mesmo ficheiro: engadir ao final do ficheiro

```python
def _parcela_de_proba(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    return ana, parcela


@pytest.mark.parametrize(
    ("campos", "mensaxe"),
    [
        ({"superficie_ha": 0.8}, "maior ca da parcela"),
        ({"superficie_ha": 0}, "maior que 0"),
        ({"tipo_inicio": "enxerto"}, "Tipo de inicio"),
        ({"data_inicio": date(2026, 5, 1), "data_fin": date(2026, 4, 1)}, "anterior á de inicio"),
        ({"num_arbores": 10, "marco_plantacion": "4x4"}, "non os dous"),
        ({"data_inicio_conversion": date(2026, 1, 1)}, "en conversión"),
        ({"sistema_cultivo": "999"}, "non existe"),
        ({"dose_sementeira_kg_ha": 200, "densidade_plantas_ha": 40000}, "Indica só un"),
        ({"material_adquirido": True}, "data en que se adquiriu"),
    ],
)
def test_validacions_rea_do_cultivo(session, campos, mensaxe):
    ana, parcela = _parcela_de_proba(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_cultivo(session, ana, parcela.id, "Pataca", **campos)


def test_estado_calculase_coas_datas(session):
    ana, parcela = _parcela_de_proba(session)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca", data_inicio=date(2026, 3, 1))
    assert cultivo.estado == "en_curso"
    actualizar_cultivo(session, ana, cultivo, data_fin=date(2026, 7, 1))
    assert cultivo.estado == "rematado"
    assert calcular_estado(cultivo, hoxe=date(2026, 6, 1)) == "en_curso"
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

# Tarefa 023 — REGA tamén para explotacións non profesionais con animais

**Estado**: feita

**Rama**: `smoth/023-rega-para-todos-con-animais`.

**Rama**: `deseno-visual`. **Depende de**: tarefas 019 e 020.

## Obxectivo

O RD 637/2021 obriga a inscribir no REGA tamén os galiñeiros de autoconsumo. Por iso:
- a lista "para estar en regra" pide o REGA a **calquera** explotación con animais (profesional ou non);
- os animais dados de baixa (con `data_baixa`) non contan;
- no diálogo de configuración o campo REGA vese sempre, non só nas profesionais.

## Ficheiros a tocar

- `src/horta/services/en_regra.py`
- `src/horta/ui/pages/horta_detalle.py`
- `tests/services/test_en_regra.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/en_regra.py`: REGA para todos

Antes:
```python
    comprobar_rol_horta(session, horta.id, actor, _ROLES_LECTURA)
    if not horta.uso_profesional:
        return []
    hoxe = hoxe or date.today()
```

Despois:
```python
    comprobar_rol_horta(session, horta.id, actor, _ROLES_LECTURA)
    ten_animais = (
        session.query(Animal).filter_by(horta_id=horta.id, data_baixa=None).first() is not None
    )
    requisito_rega = Requisito(
        "Código REGA do gando",
        bool(horta.codigo_rega),
        "Solicítase na Oficina Agraria Comarcal, tamén para galiñas de autoconsumo.",
    )
    if not horta.uso_profesional:
        return [requisito_rega] if ten_animais else []
    hoxe = hoxe or date.today()
```

### Paso 2 — mesmo ficheiro: quitar o cálculo antigo de animais

Antes:
```python
    ten_animais = session.query(Animal).filter_by(horta_id=horta.id).first() is not None
    requisitos = [
```

Despois:
```python
    requisitos = [
```

### Paso 3 — mesmo ficheiro: usar o requisito común

Antes:
```python
    if ten_animais:
        requisitos.append(
            Requisito(
                "Código REGA do gando",
                bool(horta.codigo_rega),
                "Solicítase na Oficina Agraria Comarcal.",
            )
        )
    return requisitos
```

Despois:
```python
    if ten_animais:
        requisitos.append(requisito_rega)
    return requisitos
```

### Paso 4 — mesmo ficheiro: comentario inicial

Antes:
```python
"""Que lle falta a unha explotación profesional para estar en regra."""
```

Despois:
```python
"""Que lle falta a unha explotación para estar en regra (REGA tamén se non é profesional)."""
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`: o campo REGA vese sempre

Antes:
```python
reaga_input = ui.input("Nº REAGA (ES + 12 díxitos)", value=horta_codigo_reaga).classes("w-full")
rega_input = ui.input("Nº REGA, se ten gando (ES + 12 díxitos)", value=horta_codigo_rega).classes(
    "w-full"
)
```

Despois:
```python
                reaga_input = ui.input(
                    "Nº REAGA (ES + 12 díxitos)", value=horta_codigo_reaga
                ).classes("w-full")
            rega_input = ui.input(
                "Nº REGA, se ten animais (ES + 12 díxitos)", value=horta_codigo_rega
            ).classes("w-full")
```

### Paso 6 — `tests/services/test_en_regra.py`: engadir ao final do ficheiro

```python
def test_non_profesional_con_galinas_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=5)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == ["Código REGA do gando"]
    assert not requisitos[0].cumprido


def test_animais_de_baixa_non_contan(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    animal = crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=5)
    actualizar_animal(session, ana, animal, data_baixa=date(2026, 6, 1))
    assert requisitos_en_regra(session, ana, horta) == []
```

### Paso 7 — mesmo ficheiro de tests: importar `actualizar_animal`

Antes:
```python
from horta.services.animais import crear_animal
```

Despois:
```python
from horta.services.animais import actualizar_animal, crear_animal
```

## Criterios de aceptación

- Non profesional sen animais → lista baleira; non profesional con animais activos → só "Código REGA do gando".
- Os animais con data de baixa non contan.
- No diálogo "Configurar explotación" o campo REGA vese aínda que se escolla "Non profesional".
- Os 2 tests novos pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

Executáronse literalmente os 7 pasos co editor:

1. **`en_regra.py`**: substituído o bloque `if not horta.uso_profesional: return []` polo cálculo de `ten_animais` (con `data_baixa=None`), o requisito `requisito_rega` con texto actualizado e a lóxica condicional para non profesionais.
2. **`en_regra.py`**: eliminado o cálculo antigo de animais (`session.query(Animal).filter_by(horta_id=horta.id).first() is not None`).
3. **`en_regra.py`**: substituída a definición inline de `Requisito("Código REGA do gando", ...)` por `requisito_rega` reutilizado.
4. **`en_regra.py`**: actualizado o docstring a "REGA tamén se non é profesional".
5. **`horta_detalle.py`**: texto do campo REGA cambiado a "se ten animais" e indentación corrigida.
6. **`test_en_regra.py`**: engadidos 2 tests (`test_non_profesional_con_galinas_pide_rega`, `test_animais_de_baixa_non_contan`).
7. **`test_en_regra.py`**: importado `actualizar_animal`.

Comprobacións: `ruff` — All checks passed; `mypy` — no issues; `pytest tests/services/test_en_regra.py` — 6 passed.
Commit `smoth/023-rega-para-todos-con-animais`.

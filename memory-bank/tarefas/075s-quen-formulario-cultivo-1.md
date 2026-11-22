# Tarefa 075s — Formularios con quen (7/8): sementeira, quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No formulario do cultivo, «Quen sementou ou plantou» (obrigatorio se a data xa pasou) e as horas. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
from collections.abc import Callable
```

Despois:
```python
from collections.abc import Callable
from datetime import date
```

### Paso 2 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
from horta.services.parcelas import listar_parcelas
```

Despois:
```python
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_persoas
```

### Paso 3 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            for campo, catalogo in _CATALOGOS.items()
        }
```

Despois:
```python
            for campo, catalogo in _CATALOGOS.items()
        }
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        data_inicio = campo_data("Data de sementeira ou plantación")
```

Despois:
```python
        data_inicio = campo_data("Data de sementeira ou plantación")
        quen = ui.select(persoas, label="Quen sementou ou plantou", clearable=True).classes(
            "w-full")
```

### Paso 5 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            data_fin_sementeira = campo_data("Data de fin da sementeira/plantación")
```

Despois:
```python
            data_fin_sementeira = campo_data("Data de fin da sementeira/plantación")
            horas_sementeira = ui.input("Horas de traballo").classes("w-full")
```

### Paso 6 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            datos: dict[str, Any] = dict(
                especie=opcions_cultivo.get(cultivo_oficial.value, ""),
                cultivo_siex_codigo=cultivo_oficial.value,
                variedade_siex_id=variedade_oficial.value,
                variedade=(variedade_texto.value or None) if variedade_oficial.value is None
                else variedade_oficial.options[variedade_oficial.value],
                superficie_ha=superficie.ha,
                tipo_inicio=tipo_inicio.value,
                data_inicio=parsear_data(data_inicio.value),
```

Despois:
```python
            inicio = parsear_data(data_inicio.value)
            if inicio is not None and inicio <= date.today() and quen.value is None:
                ui.notify("Indica quen sementou ou plantou", type="negative")
                return
            datos: dict[str, Any] = dict(
                especie=opcions_cultivo.get(cultivo_oficial.value, ""),
                cultivo_siex_codigo=cultivo_oficial.value,
                variedade_siex_id=variedade_oficial.value,
                variedade=(variedade_texto.value or None) if variedade_oficial.value is None
                else variedade_oficial.options[variedade_oficial.value],
                superficie_ha=superficie.ha,
                tipo_inicio=tipo_inicio.value,
                data_inicio=inicio,
                sementeira_persoa_id=quen.value,
                sementeira_horas=parsear_decimal(horas_sementeira.value),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (7/8): sementeira, quen: feito.

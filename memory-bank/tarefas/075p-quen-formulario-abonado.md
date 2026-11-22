# Tarefa 075p — Formularios con quen (4/8): abonado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o botou» pasa á vista e horas no formulario do abonado. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/abonados.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 2 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        data_inicio = campo_data("Data", date.today().isoformat())
```

Despois:
```python
        data_inicio = campo_data("Data", date.today().isoformat())
        aplicador = ui.select(persoas, label="Quen o botou", clearable=True).classes("w-full")
```

### Paso 3 — `src/horta/ui/pages/abonados.py`

Antes:
```python
            xestion = ui.checkbox("Xestión sostible dos insumos")
            lodos = ui.checkbox("Leva documento de aplicación de lodos de depuradora")
            albaran = ui.input("Albará ou factura").classes("w-full")
            aplicador = ui.select(persoas, label="Quen o botou", clearable=True).classes(
                "w-full")
```

Despois:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
            xestion = ui.checkbox("Xestión sostible dos insumos")
            lodos = ui.checkbox("Leva documento de aplicación de lodos de depuradora")
            albaran = ui.input("Albará ou factura").classes("w-full")
```

### Paso 4 — `src/horta/ui/pages/abonados.py`

Antes:
```python
                        notas=notas.value or None)
```

Despois:
```python
                        horas=parsear_decimal(horas.value), notas=notas.value or None)
```

### Paso 5 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        aplicador.value = a.aplicador_persoa_id if a else None
```

Despois:
```python
        aplicador.value = (a.aplicador_persoa_id if a.aplicador_persoa_id in persoas
                           else None) if a else proposta_quen(horta_id)
        horas.value = f"{a.horas:g}" if a and a.horas else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (4/8): abonado: feito.

# Tarefa 002 — Latitude e lonxitude no formulario de editar parcela

**Estado**: feita

## Obxectivo

Que no diálogo "Editar parcela" se poidan ver e cambiar a latitude e a lonxitude, e que un valor fóra de rango mostre a mensaxe clara ao usuario (agora mostraría "erro inesperado").

## Ficheiros a tocar

- `src/horta/services/parcelas.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`).

## Pasos

Fai cada substitución **literalmente**: busca o texto de "Antes" e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/parcelas.py`: usar o erro de dominio

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```
Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

Antes:
```python
            raise ValueError("A latitude debe estar entre -90 e 90")
```
Despois:
```python
            raise OperacionNonPermitidaError("A latitude debe estar entre -90 e 90")
```

Antes:
```python
            raise ValueError("A lonxitude debe estar entre -180 e 180")
```
Despois:
```python
            raise OperacionNonPermitidaError("A lonxitude debe estar entre -180 e 180")
```

(`OperacionNonPermitidaError` é subclase de `ValueError`, así que os tests existentes seguen valendo. Non toques os tests.)

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`: filas da táboa

Antes:
```python
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
```
Despois:
```python
        {
            "id": p.id,
            "nome": p.nome,
            "superficie": p.superficie,
            "estado": p.estado,
            "lat": p.lat,
            "lon": p.lon,
        }
```

### Paso 3 — mesmo ficheiro: campos no diálogo de editar

Antes:
```python
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")
```
Despois:
```python
        estado_edit = ui.select(list(_ESTADOS_PARCELA), label="Estado", value="activa")
        lat_edit = ui.number("Latitude", format="%.6f")
        lon_edit = ui.number("Lonxitude", format="%.6f")
```

### Paso 4 — mesmo ficheiro: gardar os valores

Antes:
```python
                        nome=nome_edit.value,
                        superficie=superficie_edit.value,
                        estado=estado_edit.value,
                    ),
```
Despois:
```python
                        nome=nome_edit.value,
                        superficie=superficie_edit.value,
                        estado=estado_edit.value,
                        lat=lat_edit.value,
                        lon=lon_edit.value,
                    ),
```

### Paso 5 — mesmo ficheiro: cargar os valores ao abrir o diálogo

Antes:
```python
        superficie_edit.value = fila["superficie"]
        estado_edit.value = fila["estado"]
        dialog_editar.open()
```
Despois:
```python
        superficie_edit.value = fila["superficie"]
        estado_edit.value = fila["estado"]
        lat_edit.value = fila["lat"]
        lon_edit.value = fila["lon"]
        dialog_editar.open()
```

**Atención**: `estado_edit.value = fila["estado"]` aparece dúas veces no ficheiro (parcelas e animais). O bloque de tres liñas de "Antes" só existe unha vez, na función `abrir_editar` da sección de **parcelas** (arredor da liña 390). Usa sempre o bloque completo.

## Criterios de aceptación

- O diálogo "Editar parcela" ten os campos Latitude e Lonxitude, cargados cos valores actuais.
- Ao gardar, envíanse `lat` e `lon` a `actualizar_parcela`.
- Unha latitude ou lonxitude fóra de rango mostra a mensaxe "A latitude debe estar entre -90 e 90" (ou a da lonxitude) en vez de "erro inesperado".
- Non se cambiou ningún outro ficheiro nin ningunha outra sección.

## Comprobacións

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest -q
```

Se `ruff format --check` falla, executa `uv run ruff format` sobre os ficheiros tocados e volve comprobar.

## Resultado

- Feito polo modelo local (commit `386f051`, integrado en master). As 9 substitucións fixéronse á primeira.
- Comprobado por Claude: ruff, mypy e pytest (148 tests) en verde.
- Nota: `ruff format` reformateou tamén código antigo do mesmo ficheiro (cultivos, fertilización, animais, membros). Só é formato, sen cambios de comportamento.
- Non se probou no navegador.

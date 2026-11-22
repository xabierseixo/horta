# Tarefa 003 — Latitude e lonxitude no formulario de crear parcela

**Estado**: feita

## Obxectivo

Que no diálogo "Nova parcela" se poidan introducir a latitude e a lonxitude (igual que xa se fai no de editar, tarefa 002).

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`).

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — campos no diálogo de crear

Antes:
```python
            superficie_input = ui.number("Superficie (m²)")

            def crear() -> None:
```
Despois:
```python
            superficie_input = ui.number("Superficie (m²)")
            lat_input = ui.number("Latitude", format="%.6f")
            lon_input = ui.number("Lonxitude", format="%.6f")

            def crear() -> None:
```

### Paso 2 — enviar os valores ao crear

Antes:
```python
                            nome_input.value,
                            superficie=superficie_input.value,
                        ),
```
Despois:
```python
                            nome_input.value,
                            superficie=superficie_input.value,
                            lat=lat_input.value,
                            lon=lon_input.value,
                        ),
```

## Regras importantes

- **Non executes `ruff format`** (reformatearía outras partes do ficheiro). Só `ruff check`.
- Non cambies nada máis do ficheiro.

## Resultado

- Engadíuse `lat_input = ui.number("Latitude", format="%.6f")` e `lon_input = ui.number("Lonxitude", format="%.6f")` no diálogo de crear parcela (liñas 242-243).
- Engadíuse `lat=lat_input.value,` e `lon=lon_input.value,` ao enviar os datos a `crear_parcela` (liñas 262-263).
- `git diff --stat`: 1 ficheiro, 4 insercións.
- `ruff check`, `mypy`, `pytest`: todos pasan (148 tests).
- Commit: `b7620ab` con rodapé `Axente: smoth`.

## Criterios de aceptación

- O diálogo "Nova parcela" ten os campos Latitude e Lonxitude.
- Ao crear, envíanse `lat` e `lon` a `crear_parcela`.
- `git diff` mostra só as 4 liñas engadidas.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
git diff --stat
```

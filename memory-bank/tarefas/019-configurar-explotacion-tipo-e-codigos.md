# Tarefa 019 — Configurar explotación: tipo (profesional / non profesional) e códigos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 018.

## Obxectivo

No diálogo de configuración, substituír a casiña "Uso profesional" por unha pregunta "Tipo de explotación" e, se é profesional, pedir o titular e os códigos REAGA e REGA.

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — cargar os datos novos

Antes:
```python
        horta_uso_profesional = horta.uso_profesional
```
Despois:
```python
        horta_uso_profesional = horta.uso_profesional
        horta_titular_nome = horta.titular_nome or ""
        horta_titular_nif = horta.titular_nif or ""
        horta_codigo_reaga = horta.codigo_reaga or ""
        horta_codigo_rega = horta.codigo_rega or ""
```

### Paso 2 — campos do diálogo

Antes:
```python
            ui.label("Configurar horta").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome)
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "")
            uso_profesional_checkbox = ui.checkbox("Uso profesional", value=horta_uso_profesional)
```
Despois:
```python
            ui.label("Configurar explotación").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome).classes("w-full")
            descricion_horta_input = ui.input(
                "Descrición", value=horta_descricion or ""
            ).classes("w-full")
            ui.label("Tipo de explotación").classes("text-caption texto-suave")
            tipo_radio = ui.radio(
                {True: "Profesional", False: "Non profesional"}, value=horta_uso_profesional
            ).props("inline")
            with ui.column().classes("w-full gap-1").bind_visibility_from(tipo_radio, "value"):
                titular_nome_input = ui.input(
                    "Titular (nome ou razón social)", value=horta_titular_nome
                ).classes("w-full")
                titular_nif_input = ui.input(
                    "NIF do titular", value=horta_titular_nif
                ).classes("w-full")
                reaga_input = ui.input(
                    "Nº REAGA (ES + 12 díxitos)", value=horta_codigo_reaga
                ).classes("w-full")
                rega_input = ui.input(
                    "Nº REGA, se ten gando (ES + 12 díxitos)", value=horta_codigo_rega
                ).classes("w-full")
```

### Paso 3 — gardar os datos novos

Antes:
```python
                            uso_profesional=uso_profesional_checkbox.value,
```
Despois:
```python
                            uso_profesional=tipo_radio.value,
                            titular_nome=titular_nome_input.value or None,
                            titular_nif=titular_nif_input.value or None,
                            codigo_reaga=reaga_input.value or None,
                            codigo_rega=rega_input.value or None,
```

## Criterios de aceptación

- O diálogo amosa "Tipo de explotación" con Profesional / Non profesional.
- Os campos do titular e os códigos só se ven se é Profesional.
- Ao gardar, os valores chegan a `actualizar_horta` (que xa os valida, tarefa 018).
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado
## Resultado

- **Paso 1** — Engadidas 4 variables de carga (`horta_titular_nome`, `horta_titular_nif`, `horta_codigo_reaga`, `horta_codigo_rega`) ao bloque de carga de datos (liña 128).
- **Paso 2** — Substituído o checkbox "Uso profesional" polo radio "Tipo de explotación" con campos condicionais de titular e códigos (liñas 147-168).
- **Paso 3** — Substituído `uso_profesional_checkbox.value` por `tipo_radio.value` e engadidas as 4 variables de titular e códigos no gardado (liñas 191-195).
- **Comprobacións**: ruff, mypy e pytest (240 passed) todos pasados.
- **Commit**: `smoth/019-configurar-explotacion-tipo-e-codigos` con rodapé `Axente: smoth`.

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

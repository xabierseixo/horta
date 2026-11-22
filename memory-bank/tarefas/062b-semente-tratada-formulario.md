# Tarefa 062b — Semente tratada no formulario do cultivo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 062. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Se se marca «A semente ou planta vén tratada», aparecen o produto e o nº de rexistro. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            material_tratado = ui.checkbox("A semente ou planta vén tratada")
```

Despois:
```python
            material_tratado = ui.checkbox("A semente ou planta vén tratada")
            with ui.column().classes("w-full gap-1").bind_visibility_from(
                    material_tratado, "value"):
                semente_produto = ui.input("Produto do tratamento (nome comercial ou materia "
                                           "activa)").classes("w-full")
                semente_rexistro = ui.input("Nº de rexistro do produto").classes("w-full")
```

### Paso 2 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                material_tratado=material_tratado.value,
```

Despois:
```python
                material_tratado=material_tratado.value,
                semente_tratamento_produto=(semente_produto.value or None)
                if material_tratado.value else None,
                semente_tratamento_num_rexistro=(semente_rexistro.value or None)
                if material_tratado.value else None,
```

### Paso 3 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                    necesidade_n, necesidade_p, necesidade_k, plan_data, auga_n, auga_p,
```

Despois:
```python
                    necesidade_n, necesidade_p, necesidade_k, plan_data, auga_n, auga_p,
                    semente_produto, semente_rexistro,
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        material_tratado.value = bool(c.material_tratado)
```

Despois:
```python
        material_tratado.value = bool(c.material_tratado)
        semente_produto.value = _texto(c.semente_tratamento_produto)
        semente_rexistro.value = _texto(c.semente_tratamento_num_rexistro)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódese apuntar o produto da semente tratada.

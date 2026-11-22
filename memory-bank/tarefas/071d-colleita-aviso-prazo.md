# Tarefa 071d — Colleitas: aviso do prazo de seguridade

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 071. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Ao apuntar unha colleita, se aínda non rematou o prazo de seguridade dalgún tratamento dese cultivo, aparece un aviso no formulario. Probado no navegador o 2026-10-25. Deseño: `docs/superpowers/specs/2026-10-25-tratamentos-completos-design.md` §3.

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from horta.services.cultivos import listar_cultivos
```

Despois:
```python
from horta.services.cultivos import listar_cultivos
from horta.services.fito_consulta import aviso_prazo_colleita
```

### Paso 2 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        cultivo.on_value_change(propor)
```

Despois:
```python
        cultivo.on_value_change(propor)
        aviso_prazo = ui.label().classes("text-negative text-sm")

        def comprobar_prazo() -> None:
            dia = parsear_data(data.value) if data.value else None
            if cultivo.value is None or dia is None:
                aviso_prazo.text = ""
                return
            with get_session() as session:
                aviso_prazo.text = aviso_prazo_colleita(session, cultivo.value, dia) or ""

        cultivo.on_value_change(comprobar_prazo)
        data.on_value_change(comprobar_prazo)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O formulario de colleita avisa do prazo de seguridade.

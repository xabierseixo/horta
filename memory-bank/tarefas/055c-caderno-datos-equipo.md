# Tarefa 055c — Caderno: enderezo das persoas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 055b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No diálogo das persoas do equipo, un apartado «Enderezo (para o caderno, se é o titular)». Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`, bloque 1.

## Ficheiros a tocar

- `src/horta/ui/pages/equipo.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/equipo.py`

Antes:
```python
        email = ui.input("Email de contacto").classes("w-full")
```

Despois:
```python
        email = ui.input("Email de contacto").classes("w-full")
        with ui.expansion("Enderezo (para o caderno, se é o titular)").classes("w-full"):
            enderezo = ui.input("Enderezo").classes("w-full")
            localidade = ui.input("Localidade").classes("w-full")
            codigo_postal = ui.input("Código postal").classes("w-full")
            provincia = ui.input("Provincia").classes("w-full")
```

### Paso 2 — `src/horta/ui/pages/equipo.py`

Antes:
```python
                telefono=telefono.value or None, email=email.value or None,
```

Despois:
```python
                telefono=telefono.value or None, email=email.value or None,
                enderezo=enderezo.value or None, localidade=localidade.value or None,
                codigo_postal=codigo_postal.value or None, provincia=provincia.value or None,
```

### Paso 3 — `src/horta/ui/pages/equipo.py`

Antes:
```python
    textos = (nome, apelidos, nif, telefono, email, ropo, caducidade, regfer, horas_ano,
```

Despois:
```python
    textos = (nome, apelidos, nif, telefono, email, enderezo, localidade, codigo_postal,
              provincia, ropo, caducidade, regfer, horas_ano,
```

### Paso 4 — `src/horta/ui/pages/equipo.py`

Antes:
```python
        email.value = p.email or ""
```

Despois:
```python
        email.value = p.email or ""
        enderezo.value = p.enderezo or ""
        localidade.value = p.localidade or ""
        codigo_postal.value = p.codigo_postal or ""
        provincia.value = p.provincia or ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O enderezo das persoas gárdase e mostrase ao editar.

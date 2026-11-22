# Tarefa 074a — Apuntar o mínimo (2/6): labor e abonado con datos opcionais

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No labor, a superficie; no abonado, a superficie, o tipo e o método pasan a ser opcionais. O caderno e o balance de nutrientes aceptan que falten. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/models/labor.py`
- `src/horta/models/abonado.py`
- `src/horta/services/plan_abonado.py`
- `src/horta/services/caderno.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/labor.py`

Antes:
```python
    superficie_ha: Mapped[float] = mapped_column(Float)
```

Despois:
```python
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 2 — `src/horta/models/abonado.py`

Antes:
```python
    superficie_ha: Mapped[float] = mapped_column(Float)
```

Despois:
```python
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 3 — `src/horta/models/abonado.py`

Antes:
```python
    tipo_fertilizacion: Mapped[str] = mapped_column(String(20))
    metodo: Mapped[str] = mapped_column(String(20))
```

Despois:
```python
    tipo_fertilizacion: Mapped[str | None] = mapped_column(String(20), default=None)
    metodo: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 4 — `src/horta/services/plan_abonado.py`

Antes:
```python
                 if cultivo.superficie_ha else 1.0)
```

Despois:
```python
                 if cultivo.superficie_ha and abonado.superficie_ha else 1.0)
```

### Paso 5 — `src/horta/services/caderno.py`

Antes:
```python
            describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion),
```

Despois:
```python
            describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion)
            if ab.tipo_fertilizacion else "",
```

### Paso 6 — `src/horta/services/caderno.py`

Antes:
```python
            describir(session, "metodo_fertilizacion", ab.metodo),
```

Despois:
```python
            describir(session, "metodo_fertilizacion", ab.metodo) if ab.metodo else "",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Apuntar o mínimo (2/6): labor e abonado con datos opcionais: feito.

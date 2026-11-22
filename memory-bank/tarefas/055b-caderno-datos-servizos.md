# Tarefa 055b — Caderno: gardar os campos novos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 055. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os servizos aceptan os campos novos (explotación, persoas, máquinas) e validan o tipo de explotación en XIP (AE, PI, CP, ATRIA, AS, NO). Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`, bloque 1.

## Ficheiros a tocar

- `src/horta/services/hortas.py`
- `src/horta/services/persoas.py`
- `src/horta/services/maquinaria.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/hortas.py`

Antes:
```python
        "codigo_rega",
```

Despois:
```python
        "codigo_rega",
        "enderezo",
        "localidade",
        "codigo_postal",
        "provincia",
        "email",
        "tipo_representacion",
        "asesoramento_nome",
        "asesoramento_nif",
        "asesoramento_num",
        "tipo_xip",
        "asesoramento_fertilizacion",
```

### Paso 2 — `src/horta/services/hortas.py`

Antes:
```python
    }
)
```

Despois:
```python
    }
)
# Tipo de explotación en xestión integrada de pragas (modelo do caderno, 1.4)
TIPOS_XIP = {"AE": "Agricultura ecolóxica", "PI": "Produción integrada",
             "CP": "Certificación privada", "ATRIA": "Agrupación de tratamento integrado (ATRIA)",
             "AS": "Asistida por un asesor", "NO": "Sen obriga de asesor en XIP"}
```

### Paso 3 — `src/horta/services/hortas.py`

Antes:
```python
            cambios[campo] = None
```

Despois:
```python
            cambios[campo] = None
    if cambios.get("tipo_xip") and cambios["tipo_xip"] not in TIPOS_XIP:
        raise OperacionNonPermitidaError("Tipo de explotación en XIP descoñecido")
```

### Paso 4 — `src/horta/services/persoas.py`

Antes:
```python
     "discapacidade"}
```

Despois:
```python
     "discapacidade", "enderezo", "localidade", "codigo_postal", "provincia"}
```

### Paso 5 — `src/horta/services/maquinaria.py`

Antes:
```python
     "activa"}
```

Despois:
```python
     "activa", "data_adquisicion"}
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense gardar os campos novos.

# Tarefa 055e — Caderno: os campos novos no Excel

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 055b e 054. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Excel do caderno leva os campos novos da primeira folla: enderezos e tipo de representación (1.1), data de adquisición dos equipos (1.3) e entidade e tipo de asesoramento (1.4). Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`, bloque 1.

## Ficheiros a tocar

- `src/horta/services/caderno.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
        ["Código REGA", horta.codigo_rega or ""],
```

Despois:
```python
        ["Código REGA", horta.codigo_rega or ""],
        ["Dirección", horta.enderezo or ""],
        ["Localidade", horta.localidade or ""],
        ["C. Postal", horta.codigo_postal or ""],
        ["Provincia", horta.provincia or ""],
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
        ["Teléfono", horta.telefono or ""],
```

Despois:
```python
        ["Teléfono", horta.telefono or ""],
        ["e-mail", horta.email or ""],
```

### Paso 3 — `src/horta/services/caderno.py`

Antes:
```python
        ["NIF", (titular.nif or "") if titular else ""],
```

Despois:
```python
        ["NIF", (titular.nif or "") if titular else ""],
        ["Dirección", (titular.enderezo or "") if titular else ""],
        ["Localidade", (titular.localidade or "") if titular else ""],
        ["C. Postal", (titular.codigo_postal or "") if titular else ""],
        ["Provincia", (titular.provincia or "") if titular else ""],
        ["Tipo de representación", horta.tipo_representacion or ""],
```

### Paso 4 — `src/horta/services/caderno.py`

Antes:
```python
           m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "", "",
           _data(m.data_ultima_inspeccion)] for m in maquinas if m.propia],
```

Despois:
```python
           m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "",
           _data(m.data_adquisicion), _data(m.data_ultima_inspeccion)]
          for m in maquinas if m.propia],
```

### Paso 5 — `src/horta/services/caderno.py`

Antes:
```python
        ["Nome ou razón social", "NIF", "Nº de identificación", "Tipo de explotación"],
```

Despois:
```python
        ["Nome ou razón social", "NIF", "Nº de identificación", "Tipo de explotación"],
        [horta.asesoramento_nome or "", horta.asesoramento_nif or "",
         horta.asesoramento_num or "", horta.tipo_xip or ""],
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A primeira folla do caderno leva os datos novos.

# Tarefa 066c — Abonos: valor agronómico no formulario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 066b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O servizo valida as riquezas (0–100 %) e os metais (non negativos) e copia as formas do N do catálogo; o diálogo «Novo abono» ten os apartados «Valor agronómico» e «Metais pesados do residuo» (este só nos residuos). Probado no navegador o 2026-10-25. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/ui/dialogo_abono.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
_IDENTIFICADORES = {"provedor_nif": "NIF", "provedor_rega": "REGA", "provedor_nima": "NIMA"}
```

Despois:
```python
_IDENTIFICADORES = {"provedor_nif": "NIF", "provedor_rega": "REGA", "provedor_nima": "NIMA"}
_FORMAS = (("n_organico_pct", "N orgánico %"), ("n_ureico_pct", "N ureico %"),
           ("n_nitrico_pct", "N nítrico %"), ("n_amoniacal_pct", "N amoniacal %"),
           ("p2o5_soluble_pct", "P₂O₅ soluble %"), ("materia_organica_pct",
                                                    "Materia orgánica % (estercos)"))
_METAIS = (("cadmio", "Cadmio"), ("cobre", "Cobre"), ("niquel", "Níquel"),
           ("chumbo", "Chumbo"), ("zinc", "Cinc"), ("mercurio", "Mercurio"),
           ("cromo_vi", "Cromo VI"), ("arsenico", "Arsénico"), ("cromo", "Cromo total"))
```

### Paso 2 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
                                      backward=lambda v: v in ESTERCOS | RESIDUOS)
```

Despois:
```python
                                      backward=lambda v: v in ESTERCOS | RESIDUOS)
        with ui.expansion("Valor agronómico (se o sabes)").classes("w-full"):
            formas = {c: ui.input(e).classes("w-full") for c, e in _FORMAS}
        with ui.expansion("Metais pesados do residuo (mg/kg)").classes("w-full") as metais_bloque:
            metais = {c: ui.input(e).classes("w-full") for c, e in _METAIS}
        metais_bloque.bind_visibility_from(material, "value", backward=lambda v: v in RESIDUOS)
```

### Paso 3 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
                                                                 d.k2o_pct or 0))
```

Despois:
```python
                                                                 d.k2o_pct or 0))
                for chave, entrada in formas.items():
                    valor = getattr(d, chave)
                    entrada.value = f"{valor:g}" if valor else ""
```

### Paso 4 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
                        k2o_pct=parsear_decimal(k.value))
```

Despois:
```python
                        k2o_pct=parsear_decimal(k.value))
                for campo, entrada in formas.items():
                    if entrada.value:
                        setattr(datos, campo, parsear_decimal(entrada.value))
                if datos.material in RESIDUOS:
                    for campo, entrada in metais.items():
                        setattr(datos, campo, parsear_decimal(entrada.value))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódese apuntar o valor agronómico e os metais dun abono.

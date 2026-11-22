# Tarefa 077d — Coidado dos animais (5/10): no Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 077a e 077c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Diario mostra os coidados dos animais co grupo e quen o fixo; as tarefas co grupo de animais. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/diario.py`

Antes:
```python
from horta.services.catalogos import describir
```

Despois:
```python
from horta.services.animais import listar_animais
from horta.services.catalogos import describir
from horta.services.coidados_animais import TIPOS_COIDADO, listar_coidados
```

### Paso 2 — `src/horta/services/diario.py`

Antes:
```python
    "tratamento_instalacion": "Tratamento en almacén ou instalación",
```

Despois:
```python
    "tratamento_instalacion": "Tratamento en almacén ou instalación",
    "coidado_animal": "Coidado de animais",
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
    sen_quen: bool = False  # feito e sen saber quen o fixo (rexistros de antes)


```

Despois:
```python
    sen_quen: bool = False  # feito e sen saber quen o fixo (rexistros de antes)


def nome_grupo(especie: str, raza: str | None) -> str:
    """Como se nomea un grupo de animais nas listas."""
    return f"{especie} ({raza})" if raza else especie


```

### Paso 4 — `src/horta/services/diario.py`

Antes:
```python
    parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
```

Despois:
```python
    parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
    grupos = {a.id: nome_grupo(a.especie, a.raza) for a in listar_animais(session, actor, horta_id)}
```

### Paso 5 — `src/horta/services/diario.py`

Antes:
```python
    for ta in listar_tarefas(session, actor, horta_id):
        if ta.traballo_id is not None:
            continue  # xa feita: sae o traballo apuntado no seu tipo
        feita = ta.estado == "feito"
        sitio = onde(ta.cultivo_id) or parcelas.get(ta.parcela_id or 0, "")
```

Despois:
```python
    for co in listar_coidados(session, actor, horta_id):
        que = TIPOS_COIDADO[co.tipo].split(" (")[0]
        detalle = co.medicamento if co.tipo == "medicamento" else (
            co.visitante if co.tipo == "visita" else co.descricion)
        traballos.append(Traballo("coidado_animal", co.id, co.data_inicio, True,
                                  f"{que} — {detalle}" if detalle else que,
                                  grupos.get(co.animal_id, ""), frozenset(),
                                  persoas=_quen(co.persoa_id), sen_quen=co.persoa_id is None))
    for ta in listar_tarefas(session, actor, horta_id):
        if ta.traballo_id is not None:
            continue  # xa feita: sae o traballo apuntado no seu tipo
        feita = ta.estado == "feito"
        sitio = (onde(ta.cultivo_id) or parcelas.get(ta.parcela_id or 0, "")
                 or grupos.get(ta.animal_id or 0, ""))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (5/10): no Diario: feito.

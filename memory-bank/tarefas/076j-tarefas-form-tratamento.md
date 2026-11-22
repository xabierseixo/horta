# Tarefa 076j — Tarefas por facer (11/16): formulario do tratamento

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do tratamento fitosanitario ábrese desde unha tarefa co cultivo e o aplicador e, ao gardar, déixaa feita. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/dialogo_tratamento.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
from horta.models.horta import Horta
```

Despois:
```python
from horta.models.horta import Horta
from horta.models.tarefa import Tarefa
```

### Paso 2 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
from horta.ui.campos import campo_data
```

Despois:
```python
from horta.ui.campos import campo_data
from horta.ui.facer_tarefa import rematar_tarefa
```

### Paso 3 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
                              "medidas": [], "orixinais": ""}
```

Despois:
```python
                              "medidas": [], "orixinais": "", "tarefa": None}
```

### Paso 4 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
                                crear_tratamento_fito(session, actor, horta_id, d)
```

Despois:
```python
                                novo = crear_tratamento_fito(session, actor, horta_id, d)
                                rematar_tarefa(session, actor, estado["tarefa"], novo)
```

### Paso 5 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
    def abrir(t: TratamentoFito | None) -> None:
        hoxe = date.today().isoformat()
```

Despois:
```python
    def abrir(t: TratamentoFito | None, tarefa: Tarefa | None = None) -> None:
        hoxe = date.today().isoformat()
        estado["tarefa"] = tarefa.id if tarefa else None
```

### Paso 6 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
        estado["cultivos"] = estado["cultivos"] or [fila_cultivo()]
        estado["problemas"] = estado["problemas"] or [fila_problema()]
        estado["produtos"] = estado["produtos"] or [fila_produto()]
        orixinais_t = [(etiqueta, valor) for etiqueta, valor in (
            ("produto", t.orixinal_produto), ("dose", t.orixinal_dose),
            ("aplicador", t.orixinal_aplicador), ("equipo", t.orixinal_equipo),
            ("asesoramento", t.orixinal_asesoramento)) if valor] if t else []
        estado["orixinais"] = " · ".join(f"{e}: {v}" for e, v in orixinais_t)
        xustificacions.value = [x.codigo for x in t.xustificacions
                                if x.codigo in op.xustificacions] if t else []
        a = t.aplicadores[0] if t and t.aplicadores else None
        aplicador.value = _ou_nada(op.aplicadores, a.persoa_id if a else None)
```

Despois:
```python
        estado["cultivos"] = estado["cultivos"] or [
            fila_cultivo(tarefa.cultivo_id if tarefa else None)]
        estado["problemas"] = estado["problemas"] or [fila_problema()]
        estado["produtos"] = estado["produtos"] or [fila_produto()]
        orixinais_t = [(etiqueta, valor) for etiqueta, valor in (
            ("produto", t.orixinal_produto), ("dose", t.orixinal_dose),
            ("aplicador", t.orixinal_aplicador), ("equipo", t.orixinal_equipo),
            ("asesoramento", t.orixinal_asesoramento)) if valor] if t else []
        estado["orixinais"] = " · ".join(f"{e}: {v}" for e, v in orixinais_t)
        xustificacions.value = [x.codigo for x in t.xustificacions
                                if x.codigo in op.xustificacions] if t else []
        a = t.aplicadores[0] if t and t.aplicadores else None
        aplicador.value = _ou_nada(op.aplicadores, a.persoa_id if a else (
            tarefa.persoa_id if tarefa else None))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (11/16): formulario do tratamento: feito.

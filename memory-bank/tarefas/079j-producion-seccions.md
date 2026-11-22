# Tarefa 079j — Produción dos animais (8/11): Apuntar traballo e sección

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079f. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Tipo novo en «Apuntar traballo» e no Diario, e sección propia «Produción dos animais». Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/diario.py`
- `src/horta/ui/pages/horta_detalle.py`
- `src/horta/ui/layout.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.producion_animal import ProducionAnimal
```

### Paso 2 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets",
    "movemento_animal": "swap_horiz", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
```

Despois:
```python
from horta.ui.pages.producions_animais import dialogo_producion
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets",
    "movemento_animal": "swap_horiz", "producion_animal": "egg", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "producion_animal": "producion", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
    "producion_animal": dialogo_producion,
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.pages.parcelas import seccion_parcelas
```

Despois:
```python
from horta.ui.pages.parcelas import seccion_parcelas
from horta.ui.pages.producions_animais import seccion_producion
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        seccion_movementos(horta_id, pode_editar)
```

Despois:
```python
        seccion_movementos(horta_id, pode_editar)
    elif seccion == "producion":
        seccion_producion(horta_id, pode_editar)
```

### Paso 5 — `src/horta/ui/layout.py`

Antes:
```python
    Seccion("movementos", "Entradas e saídas de animais", "swap_horiz", None, no_menu=True),
```

Despois:
```python
    Seccion("movementos", "Entradas e saídas de animais", "swap_horiz", None, no_menu=True),
    Seccion("producion", "Produción dos animais", "egg", None, no_menu=True),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (8/11): Apuntar traballo e sección: feito.

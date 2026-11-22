# Tarefa 077f — Coidado dos animais (7/10): en Apuntar traballo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 077e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Apuntar traballo» e o Diario ofrecen o coidado de animais; a súa táboa ten sección propia. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/layout.py`
- `src/horta/ui/pages/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/layout.py`

Antes:
```python
    Seccion("colleitas", "Colleitas", "inventory_2", None, no_menu=True),
```

Despois:
```python
    Seccion("colleitas", "Colleitas", "inventory_2", None, no_menu=True),
    Seccion("coidados", "Coidados dos animais", "pets", None, no_menu=True),
```

### Paso 2 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.models.analise import Analise
```

Despois:
```python
from horta.models.analise import Analise
from horta.models.coidado_animal import CoidadoAnimal
```

### Paso 3 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.ui.pages.analises import dialogo_analise
```

Despois:
```python
from horta.ui.pages.analises import dialogo_analise
from horta.ui.pages.coidados_animais import dialogo_coidado
```

### Paso 4 — `src/horta/ui/pages/diario.py`

Antes:
```python
    "tratamento_instalacion": "warehouse", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
```

Despois:
```python
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado,
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (7/10): en Apuntar traballo: feito.

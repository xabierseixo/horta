# Tarefa 046c — Ámbitos das boas prácticas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O catálogo BUENAS_PRACTICAS_AMBITOS ten 60 prácticas e tres columnas que din a que serven (fitosanitario, fertilización, rega). Agora gárdanse en `categoria` como `fito,fertilizacion,rega`, para que cada formulario mostre só as súas. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md`.

## Ficheiros a tocar

- `src/horta/services/catalogos_importar.py`
- `tests/services/test_boas_practicas_ambitos.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/catalogos_importar.py`: función dos ámbitos

Antes:
```python
def _codigo(valor: Any) -> str:
```

Despois:
```python
def _ambitos(fila: dict[str, Any]) -> str:
    """Boas prácticas: 'fito,fertilizacion,rega' segundo as columnas de ámbito do FEGA."""
    columnas = {"fito": "Ámbito Fitosanitario", "fertilizacion": "Ámbito Fertilización",
                "rega": "Ámbito Riego"}
    return ",".join(k for k, c in columnas.items() if _texto(fila.get(c)) == "SI")


def _codigo(valor: Any) -> str:
```

### Paso 2 — `src/horta/services/catalogos_importar.py`: usala nas boas prácticas

Antes:
```python
            "categoria": _texto(fila.get("Categoría")),
```

Despois:
```python
            "categoria": (_ambitos(fila) if catalogo == "boas_practicas"
                          else _texto(fila.get("Categoría"))),
```

### Paso 3 — crear o ficheiro `tests/services/test_boas_practicas_ambitos.py`

Contido completo:
```python
from openpyxl import Workbook

from horta.models.catalogo import CatalogoValor
from horta.services.catalogos_importar import importar_catalogo


def test_boas_practicas_gardan_os_ambitos(session, tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Código SIEX", "Buenas prácticas", "Ámbito Fitosanitario",
               "Ámbito Fertilización", "Ámbito Riego", "Fecha de alta"])
    ws.append(["12", "Fertirrigación", "NO", "SI", "SI", "25/11/2025"])
    ws.append(["50", "Variedades resistentes", "SI", "NO", "NO", "25/11/2025"])
    ruta = tmp_path / "BUENAS_PRACTICAS_AMBITOS.xlsx"
    wb.save(ruta)
    importar_catalogo(session, "boas_practicas", ruta)
    valores = {v.codigo: v.categoria for v in session.query(CatalogoValor)}
    assert valores == {"12": "fertilizacion,rega", "50": "fito"}
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As boas prácticas importadas levan os seus ámbitos en `categoria`.

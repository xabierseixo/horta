# Tarefa 043 — Lote lexible (2026-PATACA-001)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

O lote proposto usaba o código SIEX do cultivo (`2026-99-001`), que só entende o SIEX. Quen le o lote (etiqueta, albará, inspección) é unha persoa: agora proponse co nome do cultivo, `2026-PATACA-001`. O nome vai en maiúsculas, sen acentos, só a primeira palabra e como moito 10 letras. O código SIEX segue gardado no cultivo. Decisión do usuario 2026-10-24.

## Ficheiros a tocar

- `src/horta/services/colleitas.py`
- `tests/services/test_colleitas_lote.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/colleitas.py`: importar

Antes:
```python
from dataclasses import dataclass
```

Despois:
```python
import unicodedata
from dataclasses import dataclass
```

### Paso 2 — mesmo ficheiro: o nome para o lote

Antes:
```python
def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
```

Despois:
```python
def nome_para_lote(especie: str) -> str:
    """'Pemento de Padrón' -> 'PEMENTO': primeira palabra, sen acentos, ata 10 letras."""
    sen_acentos = unicodedata.normalize("NFKD", especie).encode("ascii", "ignore").decode()
    palabras = "".join(c if c.isalnum() else " " for c in sen_acentos).split()
    return palabras[0].upper()[:10] if palabras else "CULTIVO"


def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
```

### Paso 3 — mesmo ficheiro: usar o nome en vez do código SIEX

Antes:
```python
    nome = str(cultivo.cultivo_siex_codigo or cultivo.especie).upper().replace(" ", "-")
```

Despois:
```python
    nome = nome_para_lote(cultivo.especie)
```

### Paso 4 — crear o ficheiro `tests/services/test_colleitas_lote.py`

Contido completo:
```python
import pytest

from horta.services.colleitas import nome_para_lote


@pytest.mark.parametrize(
    ("especie", "esperado"),
    [
        ("Pataca", "PATACA"),
        ("leituga", "LEITUGA"),
        ("Pemento de Padrón", "PEMENTO"),
        ("Chícharo", "CHICHARO"),
        ("Coliflor-romanesco", "COLIFLOR"),
        ("Remolacha azucreira", "REMOLACHA"),
        ("Cabaciña", "CABACINA"),
        ("Alcachofa_branca", "ALCACHOFA"),
        ("Superlonganome", "SUPERLONGA"),
        ("  ", "CULTIVO"),
    ],
)
def test_nome_para_lote(especie, esperado):
    assert nome_para_lote(especie) == esperado
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O lote proposto é do tipo `2026-PATACA-001`, co nome do cultivo en vez do código SIEX.

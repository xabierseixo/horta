# Tarefa 065b — Análises de solo: metais no formulario e no caderno

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 065. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O caderno (6, caracterización de solos) pide os metais pesados (Cd, Cu, Ni, Pb, Zn, Hg, Cr en mg/kg) cando se aplican lodos. Campos na análise, validación, formulario e Excel. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/analises.py`
- `src/horta/services/caderno.py`
- `tests/services/test_caderno_solos.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/analises.py`

Antes:
```python
                    ("conductividade", "Condutividade (dS/m)"))
```

Despois:
```python
                    ("conductividade", "Condutividade (dS/m)"),
                    ("cadmio", "Cadmio (mg/kg)"), ("cobre", "Cobre (mg/kg)"),
                    ("niquel", "Níquel (mg/kg)"), ("chumbo", "Chumbo (mg/kg)"),
                    ("zinc", "Cinc (mg/kg)"), ("mercurio", "Mercurio (mg/kg)"),
                    ("cromo", "Cromo total (mg/kg)"))
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
             _num(a.potasio_ppm), "", "", "", "", "", "", ""]
```

Despois:
```python
             _num(a.potasio_ppm), _num(a.cadmio), _num(a.cobre), _num(a.niquel),
             _num(a.chumbo), _num(a.zinc), _num(a.mercurio), _num(a.cromo)]
```

### Paso 3 — crear o ficheiro `tests/services/test_caderno_solos.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.analises import DatosAnalise, crear_analise
from horta.services.caderno import xerar_caderno
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 25)


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="material_analizado", codigo="3", descricion="Suelo",
                              version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    return ana, horta, crear_parcela(session, ana, horta.id, "Leira")


def test_metais_pesados_no_caderno(session):
    ana, horta, parcela = _escenario(session)
    crear_analise(session, ana, horta.id, DatosAnalise(
        material_analizado="3", data_mostraxe=date(2026, 2, 1), parcela_id=parcela.id,
        solo={"ph": 5.6, "cadmio": 0.4, "chumbo": 12}), hoxe=HOXE)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["6 Solos"].iter_rows(min_row=5, values_only=True)))
    assert fila[0] == "Leira" and fila[2] == 5.6 and fila[7] == 0.4 and fila[10] == 12


def test_metal_negativo(session):
    ana, horta, parcela = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="metais"):
        crear_analise(session, ana, horta.id, DatosAnalise(
            material_analizado="3", data_mostraxe=date(2026, 2, 1), solo={"zinc": -1}),
            hoxe=HOXE)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os metais pesados apúntanse e saen no caderno.

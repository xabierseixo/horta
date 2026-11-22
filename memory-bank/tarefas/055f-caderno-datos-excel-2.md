# Tarefa 055f — Caderno: asesoramento en parcelas e fertilización no Excel

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 055e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Excel do caderno leva o sistema de asesoramento en XIP en cada parcela (2.1) e se hai asesoramento en fertilización (7), con probas de todos os datos novos. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`, bloque 1.

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `tests/services/test_caderno_datos.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import TIPOS_XIP, comprobar_rol_horta
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
    ws.column_dimensions["B"].width = 36
```

Despois:
```python
    ws.column_dimensions["B"].width = 36

    xip = (f"{horta.tipo_xip} ({TIPOS_XIP[horta.tipo_xip]})"
           if horta.tipo_xip in TIPOS_XIP else "")
```

### Paso 3 — `src/horta/services/caderno.py`

Antes:
```python
                if c.sistema_cultivo else "", p.nome]
```

Despois:
```python
                if c.sistema_cultivo else "", xip, p.nome]
```

### Paso 4 — `src/horta/services/caderno.py`

Antes:
```python
            "Aire libre ou protexido", "Nome da parcela (horta)"],
```

Despois:
```python
            "Aire libre ou protexido", "Sistema de asesoramento en XIP",
            "Nome da parcela (horta)"],
```

### Paso 5 — `src/horta/services/caderno.py`

Antes:
```python
    ws7.append(["Asesoramento", ""])
```

Despois:
```python
    ws7.append(["Asesoramento", "SI" if horta.asesoramento_fertilizacion else "NON"])
```

### Paso 6 — crear o ficheiro `tests/services/test_caderno_datos.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.maquinaria import crear_maquina
from horta.services.persoas import crear_persoa


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta da Ana")
    actualizar_horta(session, ana, horta, enderezo="Lugar de Abaixo 3", localidade="Melide",
                     codigo_postal="15800", provincia="A Coruña", tipo_xip="AS",
                     asesoramento_nome="ATRIA Ulloa", asesoramento_fertilizacion=True)
    crear_persoa(session, ana, horta.id, "Ana", e_titular=True, enderezo="Rúa Nova 1",
                 localidade="Melide")
    crear_maquina(session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1",
                  data_adquisicion=date(2020, 5, 1))
    return ana, horta


def test_primeira_folla_leva_enderezos_equipos_e_asesoramento(session):
    ana, horta = _escenario(session)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [[c for c in f if c not in (None, "")] for f in
             libro["1 Información xeral"].iter_rows(values_only=True)]
    assert ["Dirección", "Lugar de Abaixo 3"] in filas
    assert ["Dirección", "Rúa Nova 1"] in filas
    assert [1, "Mochila", "M1", "01/05/2020"] in filas
    assert ["ATRIA Ulloa", "AS"] in filas
    fert = [list(f) for f in libro["7 Fertilización"].iter_rows(values_only=True)]
    assert any(f[:2] == ["Asesoramento", "SI"] for f in fert)


def test_tipo_xip_descoñecido(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="XIP"):
        actualizar_horta(session, ana, horta, tipo_xip="XX")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O caderno leva os datos da explotación completos.

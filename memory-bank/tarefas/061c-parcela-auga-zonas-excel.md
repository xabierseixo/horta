# Tarefa 061c — Parcelas: táboa 2.2 no caderno

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 061. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Excel do caderno leva a táboa 2.2 (datos medioambientais das parcelas). Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `tests/services/test_caderno_parcelas.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
           [fila_parcela(c) for c in cultivos])
```

Despois:
```python
           [fila_parcela(c) for c in cultivos])
    ws2 = wb["2 Parcelas"]
    ws2.append([])
    ws2.append(["2.2 DATOS IDENTIFICATIVOS MEDIOAMBIENTAIS DAS PARCELAS"])
    ws2.append(["Id. parcelas", "Especie", "Variedade",
                "Captación de auga para consumo humano: incluído na parcela (SI/NON)",
                "Distancia (m)", "Coordenadas UTM", "Denominación",
                "Zona específica: totalmente (SI/NON)", "Parcialmente (SI/NON)",
                "Superficie afectada (ha)"])
    for cu in cultivos:
        pa = parcelas[cu.parcela_id]
        if not (pa.auga_consumo or pa.zona_especifica):
            continue
        ws2.append([orde_cultivo[cu.id], cu.especie, cu.variedade or "",
                    ("SI" if pa.auga_consumo_na_parcela else "NON") if pa.auga_consumo else "",
                    _num(pa.auga_consumo_distancia_m) if pa.auga_consumo else "",
                    pa.auga_consumo_utm or "", pa.auga_consumo_denominacion or "",
                    "SI" if pa.zona_especifica == "total" else "NON",
                    "SI" if pa.zona_especifica == "parcial" else "NON",
                    _num(pa.zona_especifica_ha)])
```

### Paso 2 — crear o ficheiro `tests/services/test_caderno_parcelas.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import actualizar_parcela, crear_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    crear_cultivo(session, ana, parcela.id, "Pataca")
    return ana, horta, parcela


def test_auga_e_zona_no_caderno(session):
    ana, horta, parcela = _escenario(session)
    actualizar_parcela(session, ana, parcela, auga_consumo=True, auga_consumo_distancia_m=40,
                       auga_consumo_denominacion="Pozo da casa", zona_especifica="parcial",
                       zona_especifica_ha=0.05)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [list(f) for f in libro["2 Parcelas"].iter_rows(values_only=True)]
    i = next(n for n, f in enumerate(filas) if f[0] == "2.2 DATOS IDENTIFICATIVOS "
             "MEDIOAMBIENTAIS DAS PARCELAS")
    assert [x or "" for x in filas[i + 2][:10]] == [1, "Pataca", "", "NON", 40, "",
                                                    "Pozo da casa", "NON", "SI", 0.05]


@pytest.mark.parametrize(("campos", "mensaxe"), [
    ({"zona_especifica": "media"}, "total"),
    ({"auga_consumo_distancia_m": -1}, "negativas"),
])
def test_validacions(session, campos, mensaxe):
    ana, _, parcela = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        actualizar_parcela(session, ana, parcela, **campos)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A folla de parcelas leva a táboa 2.2.

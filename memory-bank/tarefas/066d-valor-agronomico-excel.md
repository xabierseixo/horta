# Tarefa 066d — Caderno: valor agronómico e metais na fertilización

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 066b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

A folla 7 do caderno leva as columnas do valor agronómico e a táboa de metais pesados dos residuos valorizables. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `tests/services/test_caderno.py`
- `tests/services/test_caderno_abonos_metais.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.fertilizantes import dose_kg_ha
```

Despois:
```python
from horta.services.fertilizantes import FORMAS_N_P, METAIS_RESIDUO, RESIDUOS, dose_kg_ha
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
            _num(fe.k2o_pct) if fe else "",
```

Despois:
```python
            _num(fe.k2o_pct) if fe else "",
            *((_num(getattr(fe, c)) for c in FORMAS_N_P) if fe else ("",) * 5),
            _num(fe.materia_organica_pct) if fe else "",
```

### Paso 3 — `src/horta/services/caderno.py`

Antes:
```python
                  "K₂O total (%)", "Dose (t/ha)", "Aportadas N (kg/ha)",
```

Despois:
```python
                  "K₂O total (%)", "N orgánico (%)", "N ureico (%)", "N nítrico (%)",
                  "N amoniacal (%)", "P₂O₅ soluble (%)", "Mat. orgánica (%) (estercos)",
                  "Dose (t/ha)", "Aportadas N (kg/ha)",
```

### Paso 4 — `src/horta/services/caderno.py`

Antes:
```python
                 filas_fert)
```

Despois:
```python
                 filas_fert)
    ws7.append([])
    ws7.append(["FERTILIZACIÓN (Metais pesados) - só obrigatorio se se empregan residuos "
                "valorizables do Anexo VIII do RD 1051/2022"])
    ws7.append(["Data aplicación", "Identificación parcelas", "Tipo residuo valorizable",
                "Dose (kg/ha de produto)", "Cadmio", "Cobre", "Níquel", "Chumbo", "Cinc",
                "Mercurio", "Cromo VI", "Arsénico", "Cromo"])
    for ab in listar_abonados(session, actor, horta_id):
        fr = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
        if fr is None or fr.material not in RESIDUOS or not no_periodo(ab.data_inicio,
                                                                       ab.data_fin):
            continue
        dose = dose_kg_ha(ab.dose, ab.unidade, fr.densidade) \
            if ab.dose is not None and ab.unidade else None
        ws7.append([_intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(ab.cultivo_id, ""),
                    describir(session, "material_fertilizante", fr.material), _num(dose),
                    *(_num(getattr(fr, m)) for m in METAIS_RESIDUO)])
```

### Paso 5 — `tests/services/test_caderno.py`

Antes:
```python
    assert fert[16] == 0.2 and fert[17:20] == [30.0, 30.0, 30.0]  # 200 kg/ha ao 15 %
```

Despois:
```python
    assert fert[22] == 0.2 and fert[23:26] == [30.0, 30.0, 30.0]  # 200 kg/ha ao 15 %
```

### Paso 6 — crear o ficheiro `tests/services/test_caderno_abonos_metais.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.abonado import Abonado
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.fertilizante import FertilizanteSiex
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante, datos_desde_siex
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for codigo in ("14", "20"):
        session.add(CatalogoValor(catalogo="material_fertilizante", codigo=codigo,
                                  descricion=f"m{codigo}", version_id=v.id))
    session.add(FertilizanteSiex(codigo=5, material="14", nome="UREA (46-00-00)", n_pct=46,
                                 n_ureico_pct=46, version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_formas_do_n_dende_o_catalogo(session):
    ana, horta = _escenario(session)
    assert datos_desde_siex(session, 5).n_ureico_pct == 46


def test_metais_do_residuo_no_caderno(session):
    ana, horta = _escenario(session)
    compost = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost de alperujo", material="20", provedor_nome="Planta X", n_pct=1.5,
        materia_organica_pct=40, cadmio=0.7, chumbo=45))
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id, "Col")
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 3, 1),
                        data_fin=date(2026, 3, 1), superficie_ha=0.1, fertilizante_id=compost.id,
                        dose=10, unidade="29", tipo_fertilizacion="1", metodo="1"))
    session.commit()
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [list(f) for f in libro["7 Fertilización"].iter_rows(values_only=True)]
    assert filas[4][21] == 40  # materia orgánica
    i = next(n for n, f in enumerate(filas) if f[0] and str(f[0]).startswith(
        "FERTILIZACIÓN (Metais pesados)"))
    metais = filas[i + 2]
    assert metais[2] == "m20" and metais[3] == 10000 and metais[4] == 0.7 and metais[7] == 45


def test_metal_negativo(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="metais"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(
            nome="X", material="20", provedor_nome="Y", zinc=-1))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A fertilización do caderno está completa.

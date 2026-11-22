# Tarefa 084d — Varias leiras (5/5): fin da transición e probas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 084c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Quítanse os campos de transición dos modelos; probas das varias leiras. Probado no navegador o 2026-10-28. Deseño: `docs/superpowers/specs/2026-10-28-varias-leiras-design.md` (paso 5 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `tests/services/test_varias_leiras.py` (**ficheiro novo**)
- `tests/test_migracion_varias_leiras.py` (**ficheiro novo**)
- `src/horta/models/labor.py`
- `src/horta/models/rega.py`
- `src/horta/models/abonado.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `tests/services/test_varias_leiras.py`

Contido completo:
```python
"""Varias leiras nun mesmo traballo (docs/superpowers/specs/2026-10-28-varias-leiras-design.md)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleitas, listar_colleitas
from horta.services.cultivos import actualizar_cultivo, crear_cultivo, eliminar_cultivo
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor, listar_labores
from horta.services.leiras import LeiraTraballo
from horta.services.parcelas import crear_parcela
from horta.services.plan_abonado import balance_do_cultivo
from horta.services.regas import DatosRega, crear_rega

HOXE = date(2026, 10, 28)


def _escenario(session):
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="d" * 64, filas=0)
    session.add(version)
    session.flush()
    for catalogo, codigo in [("tipo_labor", "5"), ("material_fertilizante", "14")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=version.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    leiras = []
    for nome, superficie in (("Leira de arriba", 0.1), ("Leira de abaixo", 0.3)):
        cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, nome).id,
                                "Pataca")
        actualizar_cultivo(session, ana, cultivo, superficie_ha=superficie,
                           data_inicio=date(2026, 3, 1), plan_necesidade_n=100)
        leiras.append(cultivo)
    return ana, horta, quen, leiras


def test_un_labor_en_duas_leiras(session):
    ana, horta, quen, (arriba, abaixo) = _escenario(session)
    labor = crear_labor(session, ana, DatosLabor(
        leiras=[LeiraTraballo(arriba.id), LeiraTraballo(abaixo.id, 0.2)], data_inicio=HOXE,
        tipo_labor="5", persoa_id=quen.id, horas=3), hoxe=HOXE)
    assert [(le.cultivo_id, le.superficie_ha) for le in labor.leiras] == [
        (arriba.id, 0.1), (abaixo.id, 0.2)]
    assert listar_labores(session, ana, horta.id, cultivo_id=abaixo.id) == [labor]
    [traballo] = [t for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)
                  if t.tipo == "labor"]
    assert traballo.onde == "2 leiras" and len(traballo.parcelas) == 2
    # Un cultivo cun labor non se borra
    with pytest.raises(OperacionNonPermitidaError, match="labores"):
        eliminar_cultivo(session, ana, abaixo)


@pytest.mark.parametrize("leiras, erro", [
    ([], "polo menos unha leira"),
    ("repetida", "repetida"),
    ("grande", "maior ca do cultivo"),
    ("allea", "non pertence"),
])
def test_validacions_das_leiras(session, leiras, erro):
    ana, _, quen, (arriba, abaixo) = _escenario(session)
    if leiras == "repetida":
        leiras = [LeiraTraballo(arriba.id), LeiraTraballo(arriba.id)]
    elif leiras == "grande":
        leiras = [LeiraTraballo(arriba.id, 0.5)]
    elif leiras == "allea":
        outra = crear_horta(session, ana, "Outra")
        allea = crear_cultivo(session, ana, crear_parcela(session, ana, outra.id, "X").id, "Col")
        leiras = [LeiraTraballo(arriba.id), LeiraTraballo(allea.id)]
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        crear_rega(session, ana, DatosRega(leiras=leiras, data_inicio=HOXE,
                                           persoa_id=quen.id), hoxe=HOXE)


def test_caderno_unha_fila_por_leira_e_a_auga_repartida(session):
    ana, horta, quen, (arriba, abaixo) = _escenario(session)
    # 40 m³ en 0,4 ha: 100 m³/ha nas dúas leiras
    crear_rega(session, ana, DatosRega(
        leiras=[LeiraTraballo(arriba.id), LeiraTraballo(abaixo.id)], data_inicio=HOXE,
        cantidade=40, unidade="3", persoa_id=quen.id), hoxe=HOXE)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [f for f in libro["8 Rega"].iter_rows(min_row=5, values_only=True) if f[0]]
    assert [(f[1], f[4]) for f in filas] == [(0.1, 100), (0.3, 100)]


def test_abonado_en_duas_leiras_conta_en_cada_cultivo(session):
    ana, horta, quen, (arriba, abaixo) = _escenario(session)
    nitrato = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Nitrato", material="14", n_pct=27))
    crear_abonado(session, ana, DatosAbonado(
        leiras=[LeiraTraballo(arriba.id), LeiraTraballo(abaixo.id, 0.15)], data_inicio=HOXE,
        fertilizante_id=nitrato.id, dose=100, unidade="17", persoa_id=quen.id), hoxe=HOXE)
    # 100 kg/ha de produto ao 27 %: 27 kg N/ha; en abaixo só se abonou a metade
    assert balance_do_cultivo(session, ana, horta.id, arriba).aplicado[0] == 27
    assert balance_do_cultivo(session, ana, horta.id, abaixo).aplicado[0] == 13.5


def test_colleita_en_varias_leiras(session):
    ana, horta, quen, (arriba, abaixo) = _escenario(session)
    datos = DatosColleita(cultivo_id=arriba.id, data=date(2026, 9, 1), cantidade=0,
                          unidade="kg", lote="", persoa_id=quen.id, horas=4)
    colleitas = crear_colleitas(session, ana, datos, {arriba.id: 100, abaixo.id: 300},
                                hoxe=HOXE)
    assert [(c.cultivo_id, c.cantidade, c.horas) for c in colleitas] == [
        (arriba.id, 100, 1), (abaixo.id, 300, 3)]
    assert colleitas[0].lote_id == colleitas[1].lote_id
    # Se unha leira falla, non se garda ningunha
    with pytest.raises(OperacionNonPermitidaError, match="cantidade"):
        crear_colleitas(session, ana, datos, {arriba.id: 50, abaixo.id: 0}, hoxe=HOXE)
    assert len(listar_colleitas(session, ana, horta.id)) == 2


def test_colleita_en_varias_leiras_do_mesmo_cultivo(session):
    ana, horta, quen, (arriba, _) = _escenario(session)
    cebola = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Horta").id,
                           "Cebola")
    datos = DatosColleita(cultivo_id=arriba.id, data=date(2026, 9, 1), cantidade=0,
                          unidade="kg", lote="", persoa_id=quen.id)
    with pytest.raises(OperacionNonPermitidaError, match="mesmo cultivo"):
        crear_colleitas(session, ana, datos, {arriba.id: 10, cebola.id: 5}, hoxe=HOXE)
```

### Paso 2 — crear o ficheiro `tests/test_migracion_varias_leiras.py`

Contido completo:
```python
"""Cada labor, rega e abonado de antes pasa a ter a súa leira nunha táboa filla
(docs/superpowers/specs/2026-10-28-varias-leiras-design.md)."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]


def _alembic(url: str, *args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=RAIZ,
                   env={**os.environ, "HORTA_DATABASE_URL": url}, check=True,
                   capture_output=True)


def test_o_cultivo_pasa_a_leira(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "f2c4e6a8b0d5")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, producion_integrada, "
            "sementeira_directa, material_tratado, material_adquirido, "
            "plan_ferramenta_sostibilidade, created_at) "
            "VALUES (1, 1, 'Millo', 0, 0, 0, 0, 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO labor (id, horta_id, cultivo_id, data_inicio, data_fin, superficie_ha, "
            "tipo_labor, restos_desbroce_no_solo, restos_poda_no_solo, baixa, created_at) "
            "VALUES (1, 1, 1, '2026-04-01', '2026-04-01', 0.5, '5', 0, 0, 0, '2026-04-01')"))
        conn.execute(text(
            "INSERT INTO rega (id, horta_id, cultivo_id, data_inicio, data_fin, superficie_ha, "
            "unidade, baixa, created_at) "
            "VALUES (1, 1, 1, '2026-06-01', '2026-06-01', 0.4, '3', 0, '2026-06-01')"))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        labores = conn.execute(text(
            "SELECT labor_id, cultivo_id, superficie_ha FROM labor_cultivo")).all()
        regas = conn.execute(text(
            "SELECT rega_id, cultivo_id, superficie_ha FROM rega_cultivo")).all()
    assert [tuple(f) for f in labores] == [(1, 1, 0.5)]
    assert [tuple(f) for f in regas] == [(1, 1, 0.4)]
    _alembic(url, "downgrade", "f2c4e6a8b0d5")
    with engine.connect() as conn:
        labor = conn.execute(text("SELECT cultivo_id, superficie_ha FROM labor")).one()
    assert tuple(labor) == (1, 0.5)
```

### Paso 3 — `src/horta/models/labor.py`

Antes:
```python
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha

```

Despois:
```python
    )

```

### Paso 4 — `src/horta/models/rega.py`

Antes:
```python
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha

```

Despois:
```python
    )

```

### Paso 5 — `src/horta/models/abonado.py`

Antes:
```python
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha

```

Despois:
```python
    )

```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Varias leiras (5/5): fin da transición e probas: feito.

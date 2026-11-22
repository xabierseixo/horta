# Tarefa 073d — Caderno: folla de labores

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 073c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O caderno descargable leva a folla 9 «Labores (CUE)» co período escollido (non está no modelo da Xunta, pero si no CUE electrónico). Deseño: `docs/superpowers/specs/2026-10-25-labores-culturais-design.md`

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `tests/services/test_caderno.py`
- `tests/services/test_caderno_labores.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.hortas import TIPOS_XIP, comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import TIPOS_XIP, comprobar_rol_horta
from horta.services.labores import DESBROCE, PODAS, listar_labores
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
            "Auga: nitróxeno nítrico (mg/L)", "Auga: fósforo soluble (mg/L)"], filas_rega)

```

Despois:
```python
            "Auga: nitróxeno nítrico (mg/L)", "Auga: fósforo soluble (mg/L)"], filas_rega)

    # Non está no modelo da Xunta, pero si no CUE electrónico (bloque 5)
    filas_labor = []
    for lab in sorted(listar_labores(session, actor, horta_id), key=lambda x: x.data_inicio):
        if not no_periodo(lab.data_inicio, lab.data_fin):
            continue
        m = session.get(Maquina, lab.maquina_id) if lab.maquina_id else None
        filas_labor.append([
            orde_cultivo.get(lab.cultivo_id, ""), _num(lab.superficie_ha),
            describir(session, "tipo_labor", lab.tipo_labor),
            _intervalo(lab.data_inicio, lab.data_fin),
            ("SI" if lab.restos_desbroce_no_solo else "NON") if lab.tipo_labor == DESBROCE
            else "",
            ("SI" if lab.restos_poda_no_solo else "NON") if lab.tipo_labor in PODAS else "",
            describir(session, "tipo_cobertura_solo", lab.tipo_cobertura)
            if lab.tipo_cobertura else "",
            (m.tipo_une or "") if m else "", _num(m.potencia) if m else "",
            describir(session, "tipo_enerxia", m.tipo_enerxia) if m and m.tipo_enerxia else "",
            lab.num_repeticions or "", _num(lab.duracion_h)])
    _folla(wb, "9 Labores (CUE)", "9. LABORES CULTURAIS (CUE, bloque 5)", cab,
           ["Id. parcelas (nº de orde)", "Superficie (ha)", "Tipo de labor", "Data / intervalo",
            "Restos de desbroce no solo", "Restos de poda no solo", "Cobertura do solo",
            "Maquinaria (tipo UNE)", "Potencia", "Tipo de enerxía", "Nº de repeticións",
            "Duración de cada repetición (h)"], filas_labor)

```

### Paso 3 — `tests/services/test_caderno.py`

Antes:
```python
                                "8 Rega"]
```

Despois:
```python
                                "8 Rega", "9 Labores (CUE)"]
```

### Paso 4 — crear o ficheiro `tests/services/test_caderno_labores.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela


def test_labores_no_caderno(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="tipo_labor", codigo="7", descricion="Poda",
                              version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Maceira")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2)
    maquina = crear_maquina(session, ana, horta.id, "Tesoira", id_equipo_non_inscribible="T1",
                            potencia=0.5)
    crear_labor(session, ana, DatosLabor(cultivo_id=cultivo.id, data_inicio=date(2026, 2, 10),
                                         tipo_labor="7", restos_poda_no_solo=True,
                                         maquina_id=maquina.id, num_repeticions=1,
                                         duracion_h=3), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = list(libro["9 Labores (CUE)"].iter_rows(values_only=True))
    assert filas[0][0] == "9. LABORES CULTURAIS (CUE, bloque 5)"
    assert list(filas[4][:6]) == [1, 0.2, "Poda", "10/02/2026", None, "SI"]
    assert filas[4][8] == 0.5 and filas[4][10] == 1 and filas[4][11] == 3
    # Fóra do período non sae
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 3, 1),
                                                date(2026, 12, 31))))
    assert len(list(libro["9 Labores (CUE)"].iter_rows(values_only=True))) == 4
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os labores saen no caderno.

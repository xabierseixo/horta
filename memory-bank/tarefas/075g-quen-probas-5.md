# Tarefa 075g — Quen e horas: as probas indican quen (5/5)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075f. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As probas de apuntar o mínimo indican quen: o mínimo é que, onde, cando e quen. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `tests/services/test_apuntar_minimo.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
"""Apuntar un traballo só obriga ao mínimo (que, onde e cando); o resto é opcional e o
```

Despois:
```python
"""Apuntar un traballo só obriga ao mínimo (que, onde, cando e quen); o resto é opcional e o
```

### Paso 2 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
from horta.services.regas import DatosRega, crear_rega
```

Despois:
```python
from horta.services.regas import DatosRega, crear_rega

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 3 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
    rega = crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE),
                      hoxe=HOXE)
    assert rega.sistema_rega is None and rega.cantidade is None and rega.superficie_ha is None


def test_abonado_so_co_abono(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost da casa", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id), hoxe=HOXE)
    assert abonado.tipo_fertilizacion is None and abonado.metodo is None
    assert abonado.dose is None and abonado.unidade is None and abonado.boas_practicas == []


def test_colleita_pon_o_lote_soa(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=HOXE, cantidade=5, unidade="kg", lote=""), hoxe=HOXE)
    assert colleita.lote == "2026-TOMATE-001"


def test_labor_sen_superficie(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    labor = crear_labor(session, ana, DatosLabor(
```

Despois:
```python
    rega = crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE,
                                              persoa_id=QUEN), hoxe=HOXE)
    assert rega.sistema_rega is None and rega.cantidade is None and rega.superficie_ha is None


def test_abonado_so_co_abono(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost da casa", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(aplicador_persoa_id=QUEN,
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id), hoxe=HOXE)
    assert abonado.tipo_fertilizacion is None and abonado.metodo is None
    assert abonado.dose is None and abonado.unidade is None and abonado.boas_practicas == []


def test_colleita_pon_o_lote_soa(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    colleita = crear_colleita(session, ana, DatosColleita(persoa_id=QUEN,
        cultivo_id=cultivo.id, data=HOXE, cantidade=5, unidade="kg", lote=""), hoxe=HOXE)
    assert colleita.lote == "2026-TOMATE-001"


def test_labor_sen_superficie(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    labor = crear_labor(session, ana, DatosLabor(persoa_id=QUEN,
```

### Paso 4 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
        crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE), hoxe=HOXE)
    assert faltas_caderno(session, ana, horta.id) == [
        Falta("Regas", "superficie", 2), Falta("Regas", "sistema de rega", 2),
        Falta("Regas", "cantidade de auga", 2)]


def test_so_mira_o_periodo(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE), hoxe=HOXE)
```

Despois:
```python
        crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE,
                                           persoa_id=QUEN), hoxe=HOXE)
    assert faltas_caderno(session, ana, horta.id) == [
        Falta("Regas", "superficie", 2), Falta("Regas", "sistema de rega", 2),
        Falta("Regas", "cantidade de auga", 2)]


def test_so_mira_o_periodo(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE, persoa_id=QUEN),
               hoxe=HOXE)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: as probas indican quen (5/5): feito.

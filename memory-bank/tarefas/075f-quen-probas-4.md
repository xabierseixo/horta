# Tarefa 075f — Quen e horas: as probas indican quen (4/5)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As probas de mostras e do Diario indican quen fixo o traballo. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `tests/services/test_analises.py`
- `tests/services/test_diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_analises.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 2 — `tests/services/test_analises.py`

Antes:
```python
    analise = crear_analise(session, ana, horta.id, DatosAnalise(
        material_analizado="3", data_mostraxe=date(2026, 3, 1), tipos=["5"],
        parcela_id=parcela.id, laboratorio="Lab", solo={"ph": 5.8, "materia_organica": 4.2}),
        hoxe=HOXE)
    assert analise.ph == 5.8 and analise.materia_organica == 4.2
    assert [t.codigo for t in analise.tipos] == ["5"]
    assert listar_analises(session, ana, horta.id) == [analise]


def test_residuos_no_produto(session):
    ana, horta, _, cultivo = _escenario(session)
    analise = crear_analise(session, ana, horta.id, DatosAnalise(
```

Despois:
```python
    analise = crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
        material_analizado="3", data_mostraxe=date(2026, 3, 1), tipos=["5"],
        parcela_id=parcela.id, laboratorio="Lab", solo={"ph": 5.8, "materia_organica": 4.2}),
        hoxe=HOXE)
    assert analise.ph == 5.8 and analise.materia_organica == 4.2
    assert [t.codigo for t in analise.tipos] == ["5"]
    assert listar_analises(session, ana, horta.id) == [analise]


def test_residuos_no_produto(session):
    ana, horta, _, cultivo = _escenario(session)
    analise = crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
```

### Paso 3 — `tests/services/test_analises.py`

Antes:
```python
    datos = {"material_analizado": "3", "data_mostraxe": date(2026, 3, 1), **cambios}
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_analise(session, ana, horta.id, DatosAnalise(**datos), hoxe=HOXE)


def test_cultivo_doutra_explotacion(session):
    ana, horta, _, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    outro = crear_cultivo(session, ana, crear_parcela(session, ana, outra.id, "P").id, "X")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_analise(session, ana, horta.id, DatosAnalise(
            material_analizado="3", data_mostraxe=date(2026, 3, 1), cultivo_id=outro.id),
            hoxe=HOXE)


def test_lector_non_pode_e_baixa(session):
    ana, horta, _, _ = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    datos = DatosAnalise(material_analizado="3", data_mostraxe=date(2026, 3, 1))
    with pytest.raises(PermisoDenegadoError):
        crear_analise(session, bea, horta.id, datos, hoxe=HOXE)
    analise = crear_analise(session, ana, horta.id, datos, hoxe=HOXE)
    actualizar_analise(session, ana, analise, DatosAnalise(
```

Despois:
```python
    datos = {"material_analizado": "3", "data_mostraxe": date(2026, 3, 1), "persoa_id": QUEN,
             **cambios}
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_analise(session, ana, horta.id, DatosAnalise(**datos), hoxe=HOXE)


def test_cultivo_doutra_explotacion(session):
    ana, horta, _, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    outro = crear_cultivo(session, ana, crear_parcela(session, ana, outra.id, "P").id, "X")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
            material_analizado="3", data_mostraxe=date(2026, 3, 1), cultivo_id=outro.id),
            hoxe=HOXE)


def test_lector_non_pode_e_baixa(session):
    ana, horta, _, _ = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    datos = DatosAnalise(persoa_id=QUEN, material_analizado="3", data_mostraxe=date(2026, 3, 1))
    with pytest.raises(PermisoDenegadoError):
        crear_analise(session, bea, horta.id, datos, hoxe=HOXE)
    analise = crear_analise(session, ana, horta.id, datos, hoxe=HOXE)
    actualizar_analise(session, ana, analise, DatosAnalise(persoa_id=QUEN,
```

### Paso 4 — `tests/services/test_diario.py`

Antes:
```python
from horta.services.tarefas import crear_tarefa, marcar_feita
```

Despois:
```python
from horta.services.tarefas import crear_tarefa, marcar_feita

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 5 — `tests/services/test_diario.py`

Antes:
```python
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1)),
               hoxe=HOXE)
    traballos = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert [(t.tipo, t.data, t.feito) for t in traballos] == [
        ("rega", date(2026, 7, 1), True), ("sementeira", date(2026, 5, 1), True)]
    assert traballos[1].que == "Plantación"
    assert traballos[0].onde == "Tomate — Horta de abaixo"
    assert traballos[0].parcelas == {parcela.id}


def test_o_por_facer_vai_primeiro_e_sae_sempre(session):
    ana, horta, _, cultivo = _escenario(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 1, 10)),
               hoxe=HOXE)
```

Despois:
```python
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1),
                                       persoa_id=QUEN), hoxe=HOXE)
    traballos = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert [(t.tipo, t.data, t.feito) for t in traballos] == [
        ("rega", date(2026, 7, 1), True), ("sementeira", date(2026, 5, 1), True)]
    assert traballos[1].que == "Plantación"
    assert traballos[0].onde == "Tomate — Horta de abaixo"
    assert traballos[0].parcelas == {parcela.id}


def test_o_por_facer_vai_primeiro_e_sae_sempre(session):
    ana, horta, _, cultivo = _escenario(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 1, 10),
                                       persoa_id=QUEN), hoxe=HOXE)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: as probas indican quen (4/5): feito.

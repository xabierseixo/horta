# Tarefa 063d — Caderno: táboas 3.3, 3.4 e 3.5

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 063b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Excel do caderno leva as táboas de postcolleita, locais e transporte, con «Aplica tratamento SI/NON». Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `tests/services/test_caderno_instalacions.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.tratamentos_fito import listar_tratamentos_fito
```

Despois:
```python
from horta.services.tratamentos_fito import listar_tratamentos_fito
from horta.services.tratamentos_instalacion import listar_tratamentos_instalacion
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
                    cu.semente_tratamento_produto or "", cu.semente_tratamento_num_rexistro or ""])
```

Despois:
```python
                    cu.semente_tratamento_produto or "", cu.semente_tratamento_num_rexistro or ""])
    instalacions = [ti for ti in listar_tratamentos_instalacion(session, actor, horta_id)
                    if no_periodo(ti.data)]
    for tipo, titulo, que, cantidade in (
        ("postcolleita", "3.3 REXISTRO DE TRATAMENTOS POSTCOLLEITA (en produto vexetal)",
         "Produto vexetal tratado", "Cantidade de prod. vex. tratado (ti)"),
        ("local", "3.4 REXISTRO DE TRATAMENTOS DOS LOCAIS DE ALMACENAMENTO",
         "Local tratado (tipo e dirección)", "Volume tratado (m³)"),
        ("transporte", "3.5 REXISTRO DE TRATAMENTOS DOS MEDIOS DE TRANSPORTE",
         "Vehículo tratado (tipo, modelo e matrícula)", "Volume tratado (m³)"),
    ):
        destes = sorted((ti for ti in instalacions if ti.tipo == tipo), key=lambda ti: ti.data)
        ws3.append([])
        ws3.append([titulo])
        ws3.append(["Aplica tratamento", "SI" if destes else "NON"])
        ws3.append(["Data", que, "Referencia catastral", "Problemática fitosanitaria",
                    cantidade, "Nome comercial", "Nº Rexistro", "Materia activa",
                    "Cantidade utilizada (kg ou l)"])
        for ti in destes:
            ws3.append([
                _data(ti.data), ti.obxecto, ti.referencia_catastral or "",
                describir(session, ti.problema_tipo, ti.problema_codigo)
                if ti.problema_tipo and ti.problema_codigo else "",
                _num(ti.cantidade_tratada), ti.nome_comercial or "", ti.num_rexistro or "",
                ti.materia_activa or "",
                f"{_num(ti.cantidade_utilizada)} {describir(session, 'unidade_medida', ti.unidade)}"
                if ti.cantidade_utilizada is not None and ti.unidade else
                _num(ti.cantidade_utilizada)])
```

### Paso 3 — crear o ficheiro `tests/services/test_caderno_instalacions.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.hortas import crear_horta
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    crear_tratamento_instalacion,
)


def test_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
        tipo="local", data=date(2026, 6, 1), obxecto="Alpendre das patacas",
        nome_comercial="Produto X"), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [[x for x in f if x not in (None, "")]
             for f in libro["3 Tratamentos"].iter_rows(values_only=True)]
    i = filas.index(["3.4 REXISTRO DE TRATAMENTOS DOS LOCAIS DE ALMACENAMENTO"])
    assert filas[i + 1] == ["Aplica tratamento", "SI"]
    assert filas[i + 3][:2] == ["01/06/2026", "Alpendre das patacas"]
    j = filas.index(["3.3 REXISTRO DE TRATAMENTOS POSTCOLLEITA (en produto vexetal)"])
    assert filas[j + 1] == ["Aplica tratamento", "NON"]
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O caderno leva todas as táboas de tratamentos.

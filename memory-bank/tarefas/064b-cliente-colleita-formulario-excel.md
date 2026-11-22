# Tarefa 064b — Colleitas: cliente no formulario e no caderno

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 064. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No diálogo da colleita, o apartado «Cliente (se se vende a unha empresa)»; no Excel, as columnas do cliente da folla 5. Probado no navegador o 2026-10-25. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`
- `src/horta/services/caderno.py`
- `tests/services/test_caderno_cliente.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        restos_solo = ui.checkbox("Os restos quedan no chan")
```

Despois:
```python
        restos_solo = ui.checkbox("Os restos quedan no chan")
        with ui.expansion("Cliente (se se vende a unha empresa)").classes("w-full"):
            cliente_nome = ui.input("Nome ou razón social").classes("w-full")
            cliente_nif = ui.input("NIF").classes("w-full")
            cliente_enderezo = ui.input("Enderezo").classes("w-full")
            cliente_reaga = ui.input("Nº REAGA (se é unha explotación)").classes("w-full")
```

### Paso 2 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
                        albaran_factura=albaran.value or None,
```

Despois:
```python
                        albaran_factura=albaran.value or None,
                        cliente_nome=cliente_nome.value or None,
                        cliente_nif=cliente_nif.value or None,
                        cliente_enderezo=cliente_enderezo.value or None,
                        cliente_reaga=cliente_reaga.value or None,
```

### Paso 3 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        for campo in (cantidade, lote, notas, data_fin, albaran):
```

Despois:
```python
        for campo in (cantidade, lote, notas, data_fin, albaran, cliente_nome, cliente_nif,
                      cliente_enderezo, cliente_reaga):
```

### Paso 4 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        albaran.value = c.albaran_factura or ""
```

Despois:
```python
        albaran.value = c.albaran_factura or ""
        cliente_nome.value = c.cliente_nome or ""
        cliente_nif.value = c.cliente_nif or ""
        cliente_enderezo.value = c.cliente_enderezo or ""
        cliente_reaga.value = c.cliente_reaga or ""
```

### Paso 5 — `src/horta/services/caderno.py`

Antes:
```python
            "", "", "", ""])
```

Despois:
```python
            col.cliente_nome or "", col.cliente_nif or "", col.cliente_enderezo or "",
            col.cliente_reaga or ""])
```

### Paso 6 — crear o ficheiro `tests/services/test_caderno_cliente.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela


def test_cliente_da_colleita_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Pataca")
    crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=200, unidade="kg",
        lote="2026-PATACA-001", albaran_factura="A-7", cliente_nome="Froitas Melide SL",
        cliente_nif="B15000000", cliente_enderezo="Rúa do Mercado 2"), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["5 Colleita"].iter_rows(min_row=5, values_only=True)))
    assert fila[4:9] == ["A-7", "2026-PATACA-001", "Froitas Melide SL", "B15000000",
                         "Rúa do Mercado 2"]
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódese apuntar o cliente e sae no caderno.

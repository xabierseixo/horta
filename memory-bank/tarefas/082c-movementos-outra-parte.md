# Tarefa 082c — Persoas (4/11): a outra explotación nas entradas e saídas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Nas entradas e saídas de animais escóllese a outra explotación (titular e REGA) da lista de persoas. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/e5b7d9f1a3c8_movementos_outra_parte.py` (**ficheiro novo**)
- `src/horta/models/movemento_animal.py`
- `src/horta/services/movementos_animais.py`
- `src/horta/ui/pages/movementos_animais.py`
- `tests/services/test_movementos_animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/e5b7d9f1a3c8_movementos_outra_parte.py`

Contido completo:
```python
"""entradas e saídas de animais: a outra explotación é unha persoa (titular e REGA)

Revision ID: e5b7d9f1a3c8
Revises: d4a6c8e0f2b7
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, primeiro


# revision identifiers, used by Alembic.
revision: str = 'e5b7d9f1a3c8'
down_revision: Union[str, Sequence[str], None] = 'd4a6c8e0f2b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("movemento_animal") as batch:
        batch.add_column(sa.Column("outra_parte_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_movemento_animal_outra_parte_id", "persoa",
                                 ["outra_parte_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "movemento_animal", "outra_parte_id", "explotacion",
        "SELECT id, horta_id, titular, rega FROM movemento_animal",
        nome=lambda f: primeiro(f["titular"], f["rega"] and f"Explotación {f['rega']}"),
        datos=lambda f: {"rega": f["rega"]})
    with op.batch_alter_table("movemento_animal") as batch:
        batch.drop_column("titular")
        batch.drop_column("rega")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("movemento_animal") as batch:
        batch.add_column(sa.Column("titular", sa.String(300), nullable=True))
        batch.add_column(sa.Column("rega", sa.String(20), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE movemento_animal SET (titular, rega) = (SELECT nome, rega FROM persoa "
        "WHERE persoa.id = movemento_animal.outra_parte_id)"))
    with op.batch_alter_table("movemento_animal") as batch:
        batch.drop_constraint("fk_movemento_animal_outra_parte_id", type_="foreignkey")
        batch.drop_column("outra_parte_id")
```

### Paso 2 — `src/horta/models/movemento_animal.py`

Antes:
```python
    # Entrada: o titular anterior e a explotación de orixe; saída: o novo e a de destino
    titular: Mapped[str | None] = mapped_column(String(300), default=None)
    rega: Mapped[str | None] = mapped_column(String(20), default=None)
```

Despois:
```python
    # Entrada: a explotación de orixe (titular anterior); saída: a de destino (novo titular)
    outra_parte_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

### Paso 3 — `src/horta/services/movementos_animais.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

### Paso 4 — `src/horta/services/movementos_animais.py`

Antes:
```python
    titular: str | None = None
    rega: str | None = None
```

Despois:
```python
    # A outra explotación (titular e REGA): persoa co papel «explotacion»
    outra_parte_id: int | None = None
```

### Paso 5 — `src/horta/services/movementos_animais.py`

Antes:
```python
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
```

Despois:
```python
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
    if datos.tipo in CON_OUTRA_EXPLOTACION:
        persoa_co_papel(session, animal.horta_id, datos.outra_parte_id, "explotacion")
```

### Paso 6 — `src/horta/services/movementos_animais.py`

Antes:
```python
    mov.titular = (datos.titular or None) if outra else None
    mov.rega = (datos.rega or None) if outra else None
```

Despois:
```python
    mov.outra_parte_id = datos.outra_parte_id if outra else None
```

### Paso 7 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
```

Despois:
```python
from horta.services.persoas import listar_persoas, listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
```

### Paso 8 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
        "outra": " · ".join(x for x in (mo.titular, mo.rega) if x) or mo.causa or "",
```

Despois:
```python
        "outra": persoas.get(mo.outra_parte_id or 0) or mo.causa or "",
```

### Paso 9 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 10 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
            titular = ui.input("Titular (nome e enderezo)").classes("w-full")
            with ui.row().classes("w-full no-wrap"):
                rega = ui.input("Código REGA da explotación").classes("col")
                codigo = ui.input("Nº de guía ou do movemento").classes("col")
        causa = ui.input("Causa").classes("w-full")
        identificacion = ui.input("Identificación dos animais (crotais, anelas…)").classes(
            "w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def mostrar_campos() -> None:
            outra_explotacion.set_visibility(tipo.value in CON_OUTRA_EXPLOTACION)
            titular.label = ("Titular anterior (nome e enderezo)" if tipo.value == "entrada"
                             else "Novo titular (nome e enderezo)")
            rega.label = ("Código REGA de orixe" if tipo.value == "entrada"
                          else "Código REGA de destino")
```

Despois:
```python
            # Titular e REGA da outra explotación: ficha en Persoas
            outra_parte = CampoPersoa(horta_id, "explotacion", "Explotación de destino")
            codigo = ui.input("Nº de guía ou do movemento").classes("w-full")
        causa = ui.input("Causa").classes("w-full")
        identificacion = ui.input("Identificación dos animais (crotais, anelas…)").classes(
            "w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def mostrar_campos() -> None:
            outra_explotacion.set_visibility(tipo.value in CON_OUTRA_EXPLOTACION)
            outra_parte.set_label("Explotación de orixe (titular anterior)"
                                  if tipo.value == "entrada"
                                  else "Explotación de destino (novo titular)")
```

### Paso 11 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
                        titular=titular.value or None, rega=rega.value or None,
```

Despois:
```python
                        outra_parte_id=outra_parte.value,
```

### Paso 12 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
        titular.value = (mo.titular or "") if mo else ""
        rega.value = (mo.rega or "") if mo else ""
```

Despois:
```python
        outra_parte.value = mo.outra_parte_id if mo else None
```

### Paso 13 — `tests/services/test_movementos_animais.py`

Antes:
```python
    listar_movementos,
)
```

Despois:
```python
    listar_movementos,
)
from horta.services.persoas import crear_contacto
```

### Paso 14 — `tests/services/test_movementos_animais.py`

Antes:
```python
    crear_movemento(session, ana, _mov(galinas, persoa, "entrada", 6, titular="Xan, Lalín",
                                       rega="ES360000000001"), hoxe=HOXE)
```

Despois:
```python
    xan = crear_contacto(session, ana, horta.id, "Xan, Lalín", "explotacion",
                         rega="ES360000000001")
    entrada = crear_movemento(session, ana, _mov(galinas, persoa, "entrada", 6,
                                                 outra_parte_id=xan.id), hoxe=HOXE)
    assert entrada.outra_parte_id == xan.id
```

### Paso 15 — `tests/services/test_movementos_animais.py`

Antes:
```python
    ana, _, persoa, galinas = _escenario(session)
    mov = crear_movemento(session, ana, _mov(
        galinas, persoa, "nacemento", 2, titular="Non vai", rega="ES1", causa="Non vai",
        identificacion="Anelas 1 e 2"), hoxe=HOXE)
    assert (mov.titular, mov.rega, mov.causa, mov.identificacion) == (
        None, None, None, "Anelas 1 e 2")
```

Despois:
```python
    ana, horta, persoa, galinas = _escenario(session)
    xan = crear_contacto(session, ana, horta.id, "Xan", "explotacion")
    mov = crear_movemento(session, ana, _mov(
        galinas, persoa, "nacemento", 2, outra_parte_id=xan.id, causa="Non vai",
        identificacion="Anelas 1 e 2"), hoxe=HOXE)
    assert (mov.outra_parte_id, mov.causa, mov.identificacion) == (
        None, None, "Anelas 1 e 2")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (4/11): a outra explotación nas entradas e saídas: feito.

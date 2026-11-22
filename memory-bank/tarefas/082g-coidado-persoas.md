# Tarefa 082g — Persoas (8/11): veterinario, provedor e visitas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082f. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Nos coidados, o veterinario, onde se mercou o medicamento e quen veu son persoas da lista. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/c9f1b3d5e7a2_coidado_persoas.py` (**ficheiro novo**)
- `src/horta/models/coidado_animal.py`
- `src/horta/services/coidados_animais.py`
- `src/horta/ui/pages/coidados_animais.py`
- `tests/services/test_coidados_animais.py`
- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/c9f1b3d5e7a2_coidado_persoas.py`

Contido completo:
```python
"""coidados: o provedor do medicamento, o veterinario e quen visita son persoas

Revision ID: c9f1b3d5e7a2
Revises: b8e0a2c4d6f1
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas


# revision identifiers, used by Alembic.
revision: str = 'c9f1b3d5e7a2'
down_revision: Union[str, Sequence[str], None] = 'b8e0a2c4d6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CAMPOS = (("provedor", "provedor_id", "provedor"), ("veterinario", "veterinario_id",
                                                       "veterinario"),
           ("visitante", "visitante_id", None))


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("coidado_animal") as batch:
        for _, columna, _ in _CAMPOS:
            batch.add_column(sa.Column(columna, sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_coidado_animal_{columna}", "persoa", [columna],
                                     ["id"])
    for texto, columna, papel in _CAMPOS:
        # Quen visita non ten un papel fixo: queda como contacto sen papel
        pasar_a_persoas(op.get_bind(), "coidado_animal", columna, papel,
                        f"SELECT id, horta_id, {texto} FROM coidado_animal",
                        nome=lambda f, t=texto: f[t])
    with op.batch_alter_table("coidado_animal") as batch:
        for texto, _, _ in _CAMPOS:
            batch.drop_column(texto)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("coidado_animal") as batch:
        batch.add_column(sa.Column("provedor", sa.String(300), nullable=True))
        batch.add_column(sa.Column("veterinario", sa.String(200), nullable=True))
        batch.add_column(sa.Column("visitante", sa.String(200), nullable=True))
    for texto, columna, _ in _CAMPOS:
        op.get_bind().execute(sa.text(
            f"UPDATE coidado_animal SET {texto} = (SELECT nome FROM persoa "
            f"WHERE persoa.id = coidado_animal.{columna})"))
    with op.batch_alter_table("coidado_animal") as batch:
        for _, columna, _ in _CAMPOS:
            batch.drop_constraint(f"fk_coidado_animal_{columna}", type_="foreignkey")
            batch.drop_column(columna)
```

### Paso 2 — `src/horta/models/coidado_animal.py`

Antes:
```python
    provedor: Mapped[str | None] = mapped_column(String(300), default=None)
    proba_compra: Mapped[str | None] = mapped_column(String(100), default=None)
    veterinario: Mapped[str | None] = mapped_column(String(200), default=None)
    receita: Mapped[str | None] = mapped_column(String(50), default=None)
    tempo_espera_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    # Visita ou vehículo
    visitante: Mapped[str | None] = mapped_column(String(200), default=None)
```

Despois:
```python
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    proba_compra: Mapped[str | None] = mapped_column(String(100), default=None)
    veterinario_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    receita: Mapped[str | None] = mapped_column(String(50), default=None)
    tempo_espera_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    # Visita ou vehículo
    visitante_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

### Paso 3 — `src/horta/services/coidados_animais.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

### Paso 4 — `src/horta/services/coidados_animais.py`

Antes:
```python
    provedor: str | None = None
    proba_compra: str | None = None
    veterinario: str | None = None
    receita: str | None = None
    tempo_espera_dias: int | None = None
    duracion_dias: int | None = None
    visitante: str | None = None
```

Despois:
```python
    provedor_id: int | None = None
    proba_compra: str | None = None
    veterinario_id: int | None = None
    receita: str | None = None
    tempo_espera_dias: int | None = None
    duracion_dias: int | None = None
    visitante_id: int | None = None
```

### Paso 5 — `src/horta/services/coidados_animais.py`

Antes:
```python
    elif datos.tipo == "visita":
        if not datos.visitante:
            raise OperacionNonPermitidaError("Indica quen veu")
```

Despois:
```python
        persoa_co_papel(session, animal.horta_id, datos.provedor_id, "provedor")
        persoa_co_papel(session, animal.horta_id, datos.veterinario_id, "veterinario")
    elif datos.tipo == "visita":
        if datos.visitante_id is None:
            raise OperacionNonPermitidaError("Indica quen veu")
        persoa_co_papel(session, animal.horta_id, datos.visitante_id, None)
```

### Paso 6 — `src/horta/services/coidados_animais.py`

Antes:
```python
    coidado.provedor = (datos.provedor or None) if medicamento else None
    coidado.proba_compra = (datos.proba_compra or None) if medicamento else None
    coidado.veterinario = (datos.veterinario or None) if medicamento else None
    coidado.receita = (datos.receita or None) if medicamento else None
    coidado.tempo_espera_dias = datos.tempo_espera_dias if medicamento else None
    coidado.duracion_dias = datos.duracion_dias if medicamento else None
    coidado.visitante = datos.visitante if visita else None
```

Despois:
```python
    coidado.provedor_id = datos.provedor_id if medicamento else None
    coidado.proba_compra = (datos.proba_compra or None) if medicamento else None
    coidado.veterinario_id = datos.veterinario_id if medicamento else None
    coidado.receita = (datos.receita or None) if medicamento else None
    coidado.tempo_espera_dias = datos.tempo_espera_dias if medicamento else None
    coidado.duracion_dias = datos.duracion_dias if medicamento else None
    coidado.visitante_id = datos.visitante_id if visita else None
```

### Paso 7 — `src/horta/ui/pages/coidados_animais.py`

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

### Paso 8 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
            "detalle": co.medicamento or co.visitante or co.descricion or "",
```

Despois:
```python
            "detalle": co.medicamento or persoas.get(co.visitante_id or 0) or co.descricion
            or "",
```

### Paso 9 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 10 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
        visitante = ui.input("Quen veu (nome ou empresa)").classes("w-full")
```

Despois:
```python
        visitante = CampoPersoa(horta_id, None, "Quen veu (persoa ou empresa)")
```

### Paso 11 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
            veterinario = ui.input("Veterinario que o receitou").classes("w-full")
            receita = ui.input("Nº de receita").classes("w-full")
            provedor = ui.input("Onde se mercou (nome e enderezo)").classes("w-full")
```

Despois:
```python
            veterinario = CampoPersoa(horta_id, "veterinario", "Veterinario que o receitou")
            receita = ui.input("Nº de receita").classes("w-full")
            provedor = CampoPersoa(horta_id, "provedor", "Onde se mercou")
```

### Paso 12 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
                        provedor=provedor.value or None,
                        proba_compra=proba_compra.value or None,
                        veterinario=veterinario.value or None, receita=receita.value or None,
                        tempo_espera_dias=_enteiro(tempo_espera.value),
                        duracion_dias=_enteiro(duracion.value),
                        visitante=visitante.value or None, matricula=matricula.value or None,
```

Despois:
```python
                        provedor_id=provedor.value,
                        proba_compra=proba_compra.value or None,
                        veterinario_id=veterinario.value, receita=receita.value or None,
                        tempo_espera_dias=_enteiro(tempo_espera.value),
                        duracion_dias=_enteiro(duracion.value),
                        visitante_id=visitante.value, matricula=matricula.value or None,
```

### Paso 13 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
        visitante.value = (co.visitante or "") if co else ""
        medicamento.value = (co.medicamento or "") if co else ""
        cantidade.value = f"{co.cantidade:g}" if co and co.cantidade else ""
        unidade.value = co.unidade if co and co.unidade in unidades else None
        tempo_espera.value = (str(co.tempo_espera_dias)
                              if co and co.tempo_espera_dias is not None else "")
        duracion.value = str(co.duracion_dias) if co and co.duracion_dias else ""
        num_animais.value = str(co.num_animais) if co and co.num_animais else ""
        identificacion.value = (co.identificacion or "") if co else ""
        veterinario.value = (co.veterinario or "") if co else ""
        receita.value = (co.receita or "") if co else ""
        provedor.value = (co.provedor or "") if co else ""
```

Despois:
```python
        visitante.value = co.visitante_id if co else None
        medicamento.value = (co.medicamento or "") if co else ""
        cantidade.value = f"{co.cantidade:g}" if co and co.cantidade else ""
        unidade.value = co.unidade if co and co.unidade in unidades else None
        tempo_espera.value = (str(co.tempo_espera_dias)
                              if co and co.tempo_espera_dias is not None else "")
        duracion.value = str(co.duracion_dias) if co and co.duracion_dias else ""
        num_animais.value = str(co.num_animais) if co and co.num_animais else ""
        identificacion.value = (co.identificacion or "") if co else ""
        veterinario.value = co.veterinario_id if co else None
        receita.value = (co.receita or "") if co else ""
        provedor.value = co.provedor_id if co else None
```

### Paso 14 — `tests/services/test_coidados_animais.py`

Antes:
```python
from horta.services.movementos_animais import DatosMovemento, crear_movemento
```

Despois:
```python
from horta.services.movementos_animais import DatosMovemento, crear_movemento
from horta.services.persoas import crear_contacto
```

### Paso 15 — `tests/services/test_coidados_animais.py`

Antes:
```python
             "duracion_dias": 5, "num_animais": 3, "veterinario": "Marta Vázquez",
             "receita": "R-123"}
```

Despois:
```python
             "duracion_dias": 5, "num_animais": 3, "receita": "R-123"}
```

### Paso 16 — `tests/services/test_coidados_animais.py`

Antes:
```python
    ana, _, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id,
        visitante="Veterinaria da ADS", descricion="Revisión", matricula="1234ABC",
        medicamento="Non vai", num_animais=2), hoxe=HOXE)
    assert (co.visitante, co.matricula, co.medicamento, co.num_animais) == (
        "Veterinaria da ADS", "1234ABC", None, None)
```

Despois:
```python
    ana, horta, persoa, galinas = _escenario(session)
    ads = crear_contacto(session, ana, horta.id, "Veterinaria da ADS", None)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id,
        visitante_id=ads.id, descricion="Revisión", matricula="1234ABC",
        medicamento="Non vai", num_animais=2), hoxe=HOXE)
    assert (co.visitante_id, co.matricula, co.medicamento, co.num_animais) == (
        ads.id, "1234ABC", None, None)
```

### Paso 17 — `src/horta/services/diario.py`

Antes:
```python
            co.visitante if co.tipo == "visita" else co.descricion)
```

Despois:
```python
            nomes.get(co.visitante_id or 0) if co.tipo == "visita" else co.descricion)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (8/11): veterinario, provedor e visitas: feito.

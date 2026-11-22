# Tarefa 082d — Persoas (5/11): de quen é o gando no pastoreo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O gando doutra persoa leva a súa explotación (persoa co REGA na súa ficha). Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/f6c8e0a2b4d9_pastoreo_propietario.py` (**ficheiro novo**)
- `src/horta/models/pastoreo.py`
- `src/horta/services/pastoreos.py`
- `src/horta/ui/pages/pastoreos.py`
- `tests/services/test_pastoreos.py`
- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/f6c8e0a2b4d9_pastoreo_propietario.py`

Contido completo:
```python
"""pastoreo: o gando doutra persoa leva a súa explotación (persoa co REGA)

Revision ID: f6c8e0a2b4d9
Revises: e5b7d9f1a3c8
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas


# revision identifiers, used by Alembic.
revision: str = 'f6c8e0a2b4d9'
down_revision: Union[str, Sequence[str], None] = 'e5b7d9f1a3c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.add_column(sa.Column("propietario_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_pastoreo_animal_propietario_id", "persoa",
                                 ["propietario_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "pastoreo_animal", "propietario_id", "explotacion",
        "SELECT pa.id, p.horta_id, pa.rega FROM pastoreo_animal pa "
        "JOIN pastoreo p ON p.id = pa.pastoreo_id",
        nome=lambda f: f["rega"] and f"Explotación {f['rega']}",
        datos=lambda f: {"rega": f["rega"]})
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.drop_column("rega")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.add_column(sa.Column("rega", sa.String(14), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE pastoreo_animal SET rega = (SELECT rega FROM persoa "
        "WHERE persoa.id = pastoreo_animal.propietario_id)"))
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.drop_constraint("fk_pastoreo_animal_propietario_id", type_="foreignkey")
        batch.drop_column("propietario_id")
```

### Paso 2 — `src/horta/models/pastoreo.py`

Antes:
```python
    rega: Mapped[str | None] = mapped_column(String(14), default=None)
```

Despois:
```python
    # Animais doutra persoa: a súa explotación (co REGA na súa ficha)
    propietario_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

### Paso 3 — `src/horta/services/pastoreos.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

### Paso 4 — `src/horta/services/pastoreos.py`

Antes:
```python
    # Propios: o grupo. De terceiros: o REGA e a especie
    animal_id: int | None = None
    rega: str | None = None
```

Despois:
```python
    # Propios: o grupo. Doutra persoa: a súa explotación (persoa co REGA) e a especie
    animal_id: int | None = None
    propietario_id: int | None = None
```

### Paso 5 — `src/horta/services/pastoreos.py`

Antes:
```python
        if not (linha.rega or "").strip():
            raise OperacionNonPermitidaError("Os animais doutra persoa levan o seu REGA")
        if not linha.especie_codigo or linha.especie_codigo in NON_PASTAN:
            raise OperacionNonPermitidaError("Escolle a especie dos animais")
        validar_codigo(session, "especie_animal", linha.especie_codigo, datos.data_inicio)
```

Despois:
```python
        if not linha.especie_codigo or linha.especie_codigo in NON_PASTAN:
            raise OperacionNonPermitidaError("Escolle a especie dos animais")
        validar_codigo(session, "especie_animal", linha.especie_codigo, datos.data_inicio)
        propietario = persoa_co_papel(session, datos.horta_id, linha.propietario_id,
                                      "explotacion")
        if propietario is None:
            raise OperacionNonPermitidaError("Indica de quen son os animais")
        if not propietario.rega:
            raise OperacionNonPermitidaError(
                f"Os animais doutra persoa levan o seu REGA: complétao na ficha de "
                f"{propietario.nome}")
```

### Paso 6 — `src/horta/services/pastoreos.py`

Antes:
```python
                       rega=None if linha.animal_id else (linha.rega or "").strip(),
```

Despois:
```python
                       propietario_id=None if linha.animal_id else linha.propietario_id,
```

### Paso 7 — `src/horta/ui/pages/pastoreos.py`

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

### Paso 8 — `src/horta/ui/pages/pastoreos.py`

Antes:
```python
                else f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} ({li.rega})"
```

Despois:
```python
                else f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} "
                     f"({persoas.get(li.propietario_id or 0, '')})"
```

### Paso 9 — `src/horta/ui/pages/pastoreos.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 10 — `src/horta/ui/pages/pastoreos.py`

Antes:
```python
            rega = ui.input("REGA da súa explotación").classes("w-full")
```

Despois:
```python
            # De quen son: a súa explotación, co REGA na ficha (Persoas)
            propietario = CampoPersoa(horta_id, "explotacion", "De quen son (a súa explotación)")
```

### Paso 11 — `src/horta/ui/pages/pastoreos.py`

Antes:
```python
                            rega=rega.value or None, especie_codigo=especie.value))
```

Despois:
```python
                            propietario_id=propietario.value,
                            especie_codigo=especie.value))
```

### Paso 12 — `src/horta/ui/pages/pastoreos.py`

Antes:
```python
        rega.value = (alleo.rega or "") if alleo else ""
```

Despois:
```python
        propietario.value = alleo.propietario_id if alleo else None
```

### Paso 13 — `tests/services/test_pastoreos.py`

Antes:
```python
    sairon_do_pasto,
)
```

Despois:
```python
    sairon_do_pasto,
)
from horta.services.persoas import crear_contacto
```

### Paso 14 — `tests/services/test_pastoreos.py`

Antes:
```python
    datos.animais.append(AnimaisPastoreo(numero=20, rega="ES150000000001",
                                         especie_codigo="01"))
    pa = crear_pastoreo(session, ana, datos, hoxe=HOXE)
    assert [(le.superficie_ha, le.tipo_cobertura) for le in pa.leiras] == [(0.8, "6"),
                                                                           (0.3, "3")]
    assert [(a.animal_id, a.rega, a.numero) for a in pa.animais] == [
        (vacas.id, None, 5), (None, "ES150000000001", 20)]
```

Despois:
```python
    veciña = crear_contacto(session, ana, horta.id, "Rosa da Veiga", "explotacion",
                            rega="ES150000000001")
    datos.animais.append(AnimaisPastoreo(numero=20, propietario_id=veciña.id,
                                         especie_codigo="01"))
    pa = crear_pastoreo(session, ana, datos, hoxe=HOXE)
    assert [(le.superficie_ha, le.tipo_cobertura) for le in pa.leiras] == [(0.8, "6"),
                                                                           (0.3, "3")]
    assert [(a.animal_id, a.propietario_id, a.numero) for a in pa.animais] == [
        (vacas.id, None, 5), (None, veciña.id, 20)]
```

### Paso 15 — `tests/services/test_pastoreos.py`

Antes:
```python
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="01")]}, "REGA"),
    ({"animais": [AnimaisPastoreo(numero=3, rega="ES1", especie_codigo="18")]}, "especie"),
    ({"animais": [AnimaisPastoreo(numero=3, rega="ES1", especie_codigo="99")]}, None),
```

Despois:
```python
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="01")]}, "de quen son"),
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="18")]}, "especie"),
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="99")]}, None),
```

### Paso 16 — `tests/services/test_pastoreos.py`

Antes:
```python
        eliminar_horta(session, ana, horta)
```

Despois:
```python
        eliminar_horta(session, ana, horta)


def test_animais_doutra_persoa_levan_o_seu_rega(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    sen_rega = crear_contacto(session, ana, horta.id, "Xan do Outeiro", "explotacion")
    datos = _datos(horta, persoa, pasto, vacas, numero=5)
    datos.animais.append(AnimaisPastoreo(numero=4, propietario_id=sen_rega.id,
                                         especie_codigo="01"))
    with pytest.raises(OperacionNonPermitidaError, match="REGA"):
        crear_pastoreo(session, ana, datos, hoxe=HOXE)
```

### Paso 17 — `src/horta/services/diario.py`

Antes:
```python
from horta.services.pastoreos import listar_pastoreos
```

Despois:
```python
from horta.services.pastoreos import listar_pastoreos
from horta.services.persoas import listar_persoas
```

### Paso 18 — `src/horta/services/diario.py`

Antes:
```python
    grupos = {a.id: nome_grupo(a.especie, a.raza) for a in listar_animais(session, actor, horta_id)}
```

Despois:
```python
    grupos = {a.id: nome_grupo(a.especie, a.raza) for a in listar_animais(session, actor, horta_id)}
    nomes = {p.id: p.nome for p in listar_persoas(session, actor, horta_id, so_activas=False)}
```

### Paso 19 — `src/horta/services/diario.py`

Antes:
```python
            f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} ({li.rega})"
```

Despois:
```python
            f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} "
            f"({nomes.get(li.propietario_id or 0, '')})"
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (5/11): de quen é o gando no pastoreo: feito.

# Tarefa 082i — Persoas (10/11): quen arrenda a parcela

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082h. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Quen arrenda ou cede a parcela é unha persoa da lista, co seu NIF. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/e1b3d5f7a9c4_parcela_arrendador.py` (**ficheiro novo**)
- `src/horta/models/parcela.py`
- `src/horta/services/parcelas.py`
- `src/horta/ui/pages/parcelas.py`
- `tests/services/test_parcelas.py`
- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/e1b3d5f7a9c4_parcela_arrendador.py`

Contido completo:
```python
"""parcelas: quen arrenda ou cede a parcela é unha persoa (co seu NIF)

Revision ID: e1b3d5f7a9c4
Revises: d0a2c4e6f8b3
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas


# revision identifiers, used by Alembic.
revision: str = 'e1b3d5f7a9c4'
down_revision: Union[str, Sequence[str], None] = 'd0a2c4e6f8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("parcela") as batch:
        batch.add_column(sa.Column("arrendador_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_parcela_arrendador_id", "persoa", ["arrendador_id"], ["id"])
    # O REA só pide o NIF de quen arrenda ou cede (sen papel fixo): o NIF fai de nome
    pasar_a_persoas(
        op.get_bind(), "parcela", "arrendador_id", None,
        "SELECT id, horta_id, nif_arrendador FROM parcela",
        nome=lambda f: f["nif_arrendador"] and f"Arrendador {f['nif_arrendador']}",
        datos=lambda f: {"nif": f["nif_arrendador"]})
    with op.batch_alter_table("parcela") as batch:
        batch.drop_column("nif_arrendador")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("parcela") as batch:
        batch.add_column(sa.Column("nif_arrendador", sa.String(9), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE parcela SET nif_arrendador = (SELECT nif FROM persoa "
        "WHERE persoa.id = parcela.arrendador_id)"))
    with op.batch_alter_table("parcela") as batch:
        batch.drop_constraint("fk_parcela_arrendador_id", type_="foreignkey")
        batch.drop_column("arrendador_id")
```

### Paso 2 — `src/horta/models/parcela.py`

Antes:
```python
    nif_arrendador: Mapped[str | None] = mapped_column(String(9), default=None)
```

Despois:
```python
    arrendador_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

### Paso 3 — `src/horta/services/parcelas.py`

Antes:
```python
from horta.services.hortas import _PATRON_NIF, comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import persoa_co_papel
```

### Paso 4 — `src/horta/services/parcelas.py`

Antes:
```python
        "nif_arrendador",
```

Despois:
```python
        "arrendador_id",
```

### Paso 5 — `src/horta/services/parcelas.py`

Antes:
```python
def _validar_rea(session: Session, valores: dict[str, Any]) -> None:
    nif = valores.get("nif_arrendador")
    if nif and not _PATRON_NIF.match(nif):
        raise OperacionNonPermitidaError("O NIF do arrendador non é válido")
```

Despois:
```python
def _validar_rea(session: Session, horta_id: int, valores: dict[str, Any]) -> None:
    # Quen arrenda ou cede a parcela (REA): unha persoa da explotación, co seu NIF
    persoa_co_papel(session, horta_id, valores.get("arrendador_id"), None)
```

### Paso 6 — `src/horta/services/parcelas.py`

Antes:
```python
    _validar_rea(session, campos)
```

Despois:
```python
    _validar_rea(session, horta_id, campos)
```

### Paso 7 — `src/horta/services/parcelas.py`

Antes:
```python
    _validar_rea(session, {c: cambios.get(c, getattr(parcela, c)) for c in
                           ("nif_arrendador", "data_alta", "data_baixa", "zona_especifica",
```

Despois:
```python
    _validar_rea(session, parcela.horta_id, {c: cambios.get(c, getattr(parcela, c)) for c in
                           ("arrendador_id", "data_alta", "data_baixa", "zona_especifica",
```

### Paso 8 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
from horta.ui.accions import executar_accion
```

Despois:
```python
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
```

### Paso 9 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
            nif_arrendador = ui.input("NIF do arrendador ou cedente").classes("w-full")
```

Despois:
```python
            arrendador = CampoPersoa(horta_id, None, "Quen a arrenda ou cede")
```

### Paso 10 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
                rexime_tenencia=tenencia.value, nif_arrendador=nif_arrendador.value or None,
```

Despois:
```python
                rexime_tenencia=tenencia.value, arrendador_id=arrendador.value,
```

### Paso 11 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
    textos = (nome, uso, catastro, nif_arrendador, data_alta, data_baixa, lat, lon, notas,
              auga_distancia, auga_utm, auga_nome, zona_ha, *sigpac.values())
    selectores = (secano, orixe_auga, tenencia, causa_baixa, zona)

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova parcela"
        for campo in textos:
            campo.value = ""
        for selector in selectores:
            selector.value = None
```

Despois:
```python
    textos = (nome, uso, catastro, data_alta, data_baixa, lat, lon, notas,
              auga_distancia, auga_utm, auga_nome, zona_ha, *sigpac.values())
    selectores = (secano, orixe_auga, tenencia, causa_baixa, zona)

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova parcela"
        for campo in textos:
            campo.value = ""
        for selector in selectores:
            selector.value = None
        arrendador.value = None
```

### Paso 12 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
        nif_arrendador.value = _texto(p.nif_arrendador)
```

Despois:
```python
        arrendador.value = p.arrendador_id
```

### Paso 13 — `tests/services/test_parcelas.py`

Antes:
```python
    listar_parcelas,
)
```

Despois:
```python
    listar_parcelas,
)
from horta.services.persoas import crear_contacto
```

### Paso 14 — `tests/services/test_parcelas.py`

Antes:
```python
        ({"nif_arrendador": "123"}, "NIF do arrendador"),
```

Despois:
```python
        ({"arrendador_id": 999}, "non é desta explotación"),
```

### Paso 15 — `tests/services/test_parcelas.py`

Antes:
```python
    actualizar_parcela(session, ana, parcela, nif_arrendador="12345678Z")
    assert (parcela.sigpac_zona, parcela.nif_arrendador) == ("0", "12345678Z")
```

Despois:
```python
    arrendador = crear_contacto(session, ana, horta.id, "Arrendador", None, nif="12345678Z")
    actualizar_parcela(session, ana, parcela, arrendador_id=arrendador.id)
    assert (parcela.sigpac_zona, parcela.arrendador_id) == ("0", arrendador.id)
```

### Paso 16 — `src/horta/services/hortas.py`

Antes:
```python
# Patróns do descritor SIEX (Anexo VI): NIF/NIE de persoa física e CIF (aínda o usa o NIF do
# arrendador das parcelas); código de explotación ES + 12 díxitos (codigoREA).
_PATRON_NIF = re.compile(
    r"^([KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]|[A-HJ-NP-SUVW]\d{7}[0-9A-J])$"
)
```

Despois:
```python
# Patrón do descritor SIEX (Anexo VI): código de explotación ES + 12 díxitos (codigoREA).
# O REGA segue o mesmo formato.
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (10/11): quen arrenda a parcela: feito.

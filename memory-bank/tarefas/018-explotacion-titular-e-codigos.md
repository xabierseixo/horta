# Tarefa 018 — Explotación: datos do titular, códigos oficiais e estado de rexistro

**Estado**: feita

**Rama**: `deseno-visual`. Deseño: `docs/superpowers/specs/2026-10-22-tipo-explotacion-design.md`.

## Obxectivo

Engadir á explotación (modelo `Horta`) o nome e NIF do titular e os códigos REAGA e REGA, validar o seu formato, e unha función `estado_rexistro(horta)` que devolve `"non_profesional"`, `"en_preparacion"` ou `"rexistrada"`.

## Ficheiros a tocar

- `src/horta/models/horta.py`
- `src/horta/services/hortas.py`
- `alembic/versions/c3a9e1f0b7d2_explotacion_titular_e_codigos.py` (**ficheiro novo**)
- `tests/services/test_hortas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/horta.py`: campos novos

Antes:
```python
    uso_profesional: Mapped[bool] = mapped_column(Boolean, default=False)
```
Despois:
```python
    uso_profesional: Mapped[bool] = mapped_column(Boolean, default=False)
    titular_nome: Mapped[str | None] = mapped_column(String(200), default=None)
    titular_nif: Mapped[str | None] = mapped_column(String(9), default=None)
    codigo_reaga: Mapped[str | None] = mapped_column(String(14), default=None)
    codigo_rega: Mapped[str | None] = mapped_column(String(14), default=None)
```

### Paso 2 — `src/horta/services/hortas.py`: campos editables

Antes:
```python
CAMPOS_EDITABLES_HORTA = frozenset({"nome", "descricion", "uso_profesional"})
```
Despois:
```python
CAMPOS_EDITABLES_HORTA = frozenset(
    {
        "nome",
        "descricion",
        "uso_profesional",
        "titular_nome",
        "titular_nif",
        "codigo_reaga",
        "codigo_rega",
    }
)

# Patróns do descritor SIEX (Anexo VI): NIF/NIE de persoa física e CIF; código de
# explotación ES + 12 díxitos (codigoREA). O REGA segue o mesmo formato.
_PATRON_NIF = re.compile(
    r"^([KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]|[A-HJ-NP-SUVW]\d{7}[0-9A-J])$"
)
_PATRON_CODIGO = re.compile(r"^ES\d{12}$")


def _normalizar_e_validar_codigos(cambios: dict[str, Any]) -> None:
    for campo in ("titular_nif", "codigo_reaga", "codigo_rega"):
        if cambios.get(campo):
            cambios[campo] = cambios[campo].strip().upper().replace(" ", "")
        elif campo in cambios:
            cambios[campo] = None
    if cambios.get("titular_nif") and not _PATRON_NIF.match(cambios["titular_nif"]):
        raise OperacionNonPermitidaError("O NIF do titular non é válido")
    for campo, nome in (("codigo_reaga", "REAGA"), ("codigo_rega", "REGA")):
        if cambios.get(campo) and not _PATRON_CODIGO.match(cambios[campo]):
            raise OperacionNonPermitidaError(
                f"O código {nome} debe ter o formato ES seguido de 12 díxitos"
            )


def estado_rexistro(horta: Horta) -> str:
    """non_profesional | en_preparacion | rexistrada (calculado, non gardado)."""
    if not horta.uso_profesional:
        return "non_profesional"
    if horta.titular_nif and horta.codigo_reaga:
        return "rexistrada"
    return "en_preparacion"
```

### Paso 3 — mesmo ficheiro: importar `re`

Antes:
```python
from typing import Any
```
Despois:
```python
import re
from typing import Any
```

### Paso 4 — mesmo ficheiro: validar ao actualizar

Antes:
```python
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    for campo, valor in cambios.items():
        setattr(horta, campo, valor)
```
Despois:
```python
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    _normalizar_e_validar_codigos(cambios)
    for campo, valor in cambios.items():
        setattr(horta, campo, valor)
```

### Paso 5 — crear o ficheiro `alembic/versions/c3a9e1f0b7d2_explotacion_titular_e_codigos.py`

Contido completo:

```python
"""explotacion titular e codigos

Revision ID: c3a9e1f0b7d2
Revises: f752d1bd2c5d
Create Date: 2026-10-22 23:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3a9e1f0b7d2"
down_revision: Union[str, Sequence[str], None] = "f752d1bd2c5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("horta") as batch:
        batch.add_column(sa.Column("titular_nome", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("titular_nif", sa.String(length=9), nullable=True))
        batch.add_column(sa.Column("codigo_reaga", sa.String(length=14), nullable=True))
        batch.add_column(sa.Column("codigo_rega", sa.String(length=14), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("horta") as batch:
        batch.drop_column("codigo_rega")
        batch.drop_column("codigo_reaga")
        batch.drop_column("titular_nif")
        batch.drop_column("titular_nome")
```

### Paso 6 — `tests/services/test_hortas.py`: engadir tres tests ao FINAL do ficheiro

Engade este texto ao **final do ficheiro** (despois da última liña que haxa), deixando dúas liñas en branco antes:

```python
def test_estado_rexistro_segundo_os_datos(session):
    from horta.services.hortas import estado_rexistro

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña explotación")
    assert estado_rexistro(horta) == "non_profesional"
    actualizar_horta(session, ana, horta, uso_profesional=True)
    assert estado_rexistro(horta) == "en_preparacion"
    actualizar_horta(
        session, ana, horta, titular_nif="12345678z", codigo_reaga="es 150010000001"
    )
    assert horta.titular_nif == "12345678Z"
    assert horta.codigo_reaga == "ES150010000001"
    assert estado_rexistro(horta) == "rexistrada"


def test_codigo_reaga_mal_formado(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña explotación")
    with pytest.raises(OperacionNonPermitidaError, match="formato ES"):
        actualizar_horta(session, ana, horta, codigo_reaga="123")


def test_nif_titular_mal_formado(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña explotación")
    with pytest.raises(OperacionNonPermitidaError, match="NIF do titular"):
        actualizar_horta(session, ana, horta, titular_nif="ABC")
```

## Criterios de aceptación

- A explotación ten os catro campos novos e a migración aplícase sen erros (`uv run alembic upgrade head` nunha BD de proba).
- `estado_rexistro` devolve os tres estados segundo os datos.
- NIF e códigos mal formados dan erro claro; os válidos gárdanse en maiúsculas e sen espazos.
- Os tests novos pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

Feitos os pasos (modelo, servizo, migración, 3 tests). smoth esgotou o tempo antes do commit; Claude engadiu a chamada a `_normalizar_e_validar_codigos` que faltaba e quitou unha liña duplicada no test. ruff, mypy, pytest (240) en verde; migración probada arriba e abaixo.

# Tarefa 082 — Persoas (1/11): papeis de cada persoa

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Unha soa lista de persoas e entidades con papeis (titular, traballador, aplicador, asesor, cliente, provedor...). Pantalla Persoas coas pestanas Equipo e Contactos. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/c3f5a7b9d1e6_persoas_e_papeis.py` (**ficheiro novo**)
- `src/horta/models/persoa.py`
- `src/horta/models/__init__.py`
- `src/horta/migracion_persoas.py` (**ficheiro novo**)
- `src/horta/services/persoas.py`
- `src/horta/services/tratamentos_fito.py`
- `src/horta/ui/pages/tratamentos.py`
- `src/horta/ui/pages/equipo.py`
- `src/horta/ui/layout.py`
- `tests/services/test_persoas.py`
- `tests/services/test_tratamentos_fito.py`
- `tests/services/test_caderno_tratamentos.py`
- `src/horta/services/en_regra.py`
- `src/horta/services/caderno.py`
- `src/horta/services/hortas.py`
- `tests/services/test_en_regra.py`
- `tests/services/test_caderno_datos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/c3f5a7b9d1e6_persoas_e_papeis.py`

Contido completo:
```python
"""persoas e entidades: papeis (persoa_papel) e rexistros de cada persoa

Revision ID: c3f5a7b9d1e6
Revises: b2e4a6c8d0f5
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f5a7b9d1e6'
down_revision: Union[str, Sequence[str], None] = 'b2e4a6c8d0f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BOOLEANOS = {"e_titular": "titular", "e_traballador": "traballador",
              "e_aplicador": "aplicador", "e_asesor": "asesor"}
_NOVOS = (("tipo", sa.String(10)), ("concello_codigo", sa.String(5)), ("pais", sa.String(50)),
          ("rega", sa.String(14)), ("reaga", sa.String(14)), ("nima", sa.String(50)),
          ("ropveg", sa.String(50)), ("rexistro_dixital", sa.String(50)),
          ("num_asesoramento", sa.String(50)))


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "persoa_papel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=False),
        sa.Column("papel", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("persoa_id", "papel"),
    )
    op.create_index(op.f("ix_persoa_papel_persoa_id"), "persoa_papel", ["persoa_id"])
    with op.batch_alter_table("persoa") as batch:
        for nome, tipo in _NOVOS:
            batch.add_column(sa.Column(nome, tipo, nullable=True))
        batch.alter_column("nome", type_=sa.String(200))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE persoa SET tipo = 'persoa'"))
    for columna, papel in _BOOLEANOS.items():
        conn.execute(sa.text(
            f"INSERT INTO persoa_papel (persoa_id, papel) SELECT id, '{papel}' FROM persoa "
            f"WHERE {columna}"))
    # Ata agora todas as persoas eran do equipo: as que non tiñan función traballan nela
    conn.execute(sa.text(
        "INSERT INTO persoa_papel (persoa_id, papel) SELECT id, 'traballador' FROM persoa "
        "WHERE id NOT IN (SELECT persoa_id FROM persoa_papel)"))
    with op.batch_alter_table("persoa") as batch:
        for columna in _BOOLEANOS:
            batch.drop_column(columna)
        batch.alter_column("tipo", existing_type=sa.String(10), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("persoa") as batch:
        for columna in _BOOLEANOS:
            batch.add_column(sa.Column(columna, sa.Boolean(), nullable=False,
                                       server_default=sa.false()))
    conn = op.get_bind()
    for columna, papel in _BOOLEANOS.items():
        conn.execute(sa.text(
            f"UPDATE persoa SET {columna} = 1 WHERE id IN "
            f"(SELECT persoa_id FROM persoa_papel WHERE papel = '{papel}')"))
    with op.batch_alter_table("persoa") as batch:
        for nome, _ in _NOVOS:
            batch.drop_column(nome)
    op.drop_index(op.f("ix_persoa_papel_persoa_id"), table_name="persoa_papel")
    op.drop_table("persoa_papel")

```

### Paso 2 — `src/horta/models/persoa.py`

Antes:
```python
from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
```

Despois:
```python
from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
```

### Paso 3 — `src/horta/models/persoa.py`

Antes:
```python
    __tablename__ = "persoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    apelidos: Mapped[str | None] = mapped_column(String(200), default=None)
    nif: Mapped[str | None] = mapped_column(String(9), default=None)
    e_aplicador: Mapped[bool] = mapped_column(Boolean, default=False)
    e_asesor: Mapped[bool] = mapped_column(Boolean, default=False)
    ropo_numero: Mapped[str | None] = mapped_column(String(14), default=None)
    ropo_tipo_carne: Mapped[TipoCarne | None] = mapped_column(Enum(TipoCarne), default=None)
    ropo_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    regfer_numero: Mapped[str | None] = mapped_column(String(20), default=None)
    # Enderezo (caderno de explotación 1.1, para o titular)
    enderezo: Mapped[str | None] = mapped_column(String(200), default=None)
    localidade: Mapped[str | None] = mapped_column(String(100), default=None)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), default=None)
    provincia: Mapped[str | None] = mapped_column(String(50), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    # Equipo (deseño 2026-10-23-equipo): conta, funcións e datos de emprego (UTA, AGADER)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    e_titular: Mapped[bool] = mapped_column(Boolean, default=False)
    e_traballador: Mapped[bool] = mapped_column(Boolean, default=False)
    telefono: Mapped[str | None] = mapped_column(String(30), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    vinculo: Mapped[str | None] = mapped_column(String(20), default=None)
    horas_ano: Mapped[float | None] = mapped_column(Float, default=None)
    formacion_agraria: Mapped[str | None] = mapped_column(String(200), default=None)
    xenero: Mapped[str | None] = mapped_column(String(10), default=None)
    data_nacemento: Mapped[date | None] = mapped_column(Date, default=None)
    discapacidade: Mapped[bool] = mapped_column(Boolean, default=False)
```

Despois:
```python
    """Toda a xente e as empresas coas que trata a explotación, de dentro e de fóra, cos seus
    papeis (docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md)."""

    __tablename__ = "persoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # persoa (física) ou entidade (empresa, cooperativa, laboratorio...)
    tipo: Mapped[str] = mapped_column(String(10), default="persoa")
    # Nome, ou razón social se é unha entidade
    nome: Mapped[str] = mapped_column(String(200))
    apelidos: Mapped[str | None] = mapped_column(String(200), default=None)
    nif: Mapped[str | None] = mapped_column(String(9), default=None)
    ropo_numero: Mapped[str | None] = mapped_column(String(14), default=None)
    ropo_tipo_carne: Mapped[TipoCarne | None] = mapped_column(Enum(TipoCarne), default=None)
    ropo_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    regfer_numero: Mapped[str | None] = mapped_column(String(20), default=None)
    # Enderezo (caderno de explotación 1.1, para o titular)
    enderezo: Mapped[str | None] = mapped_column(String(200), default=None)
    localidade: Mapped[str | None] = mapped_column(String(100), default=None)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), default=None)
    provincia: Mapped[str | None] = mapped_column(String(50), default=None)
    # CUE 3 (quen merca): concello (código INE) e país se non é España
    concello_codigo: Mapped[str | None] = mapped_column(String(5), default=None)
    pais: Mapped[str | None] = mapped_column(String(50), default=None)
    # Rexistros, segundo o papel: REGA (outra explotación), REAGA, NIMA (residuos),
    # ROPVEG (provedor de plantas), rexistro dixital de alimentos (CUE 3), nº de asesoramento
    rega: Mapped[str | None] = mapped_column(String(14), default=None)
    reaga: Mapped[str | None] = mapped_column(String(14), default=None)
    nima: Mapped[str | None] = mapped_column(String(50), default=None)
    ropveg: Mapped[str | None] = mapped_column(String(50), default=None)
    rexistro_dixital: Mapped[str | None] = mapped_column(String(50), default=None)
    num_asesoramento: Mapped[str | None] = mapped_column(String(50), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    # Equipo (deseño 2026-10-23-equipo): conta, funcións e datos de emprego (UTA, AGADER)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    telefono: Mapped[str | None] = mapped_column(String(30), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    vinculo: Mapped[str | None] = mapped_column(String(20), default=None)
    horas_ano: Mapped[float | None] = mapped_column(Float, default=None)
    formacion_agraria: Mapped[str | None] = mapped_column(String(200), default=None)
    xenero: Mapped[str | None] = mapped_column(String(10), default=None)
    data_nacemento: Mapped[date | None] = mapped_column(Date, default=None)
    discapacidade: Mapped[bool] = mapped_column(Boolean, default=False)

    papeis_rexistro: Mapped[list[PersoaPapel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def papeis(self) -> set[str]:
        """Os papeis da persoa (services.persoas.PAPEIS)."""
        return {p.papel for p in self.papeis_rexistro}

    def ten_papel(self, *papeis: str) -> bool:
        return bool(self.papeis & set(papeis))


class PersoaPapel(Base):
    """Cada papel dunha persoa: titular, traballador, aplicador, cliente, provedor..."""

    __tablename__ = "persoa_papel"
    __table_args__ = (UniqueConstraint("persoa_id", "papel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"), index=True)
    papel: Mapped[str] = mapped_column(String(20))
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.persoa import Persoa, TipoCarne
```

Despois:
```python
from horta.models.persoa import Persoa, PersoaPapel, TipoCarne
```

### Paso 5 — `src/horta/models/__init__.py`

Antes:
```python
    "Persoa",
```

Despois:
```python
    "Persoa",
    "PersoaPapel",
```

### Paso 6 — crear o ficheiro `src/horta/migracion_persoas.py`

Contido completo:
```python
"""Axuda para as migracións que pasan textos con persoas ou empresas de fóra a fichas de
persoa (docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md). Só a usan as
migracións de alembic/versions: traballa con SQL directo, sen os modelos, para que non
dependa de como sexan os modelos no futuro."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection

_LETRAS_CIF = "ABCDEFGHJNPQRSUVW"


def e_cif(nif: str | None) -> bool:
    """O NIF é dunha entidade (CIF)?"""
    return bool(nif) and nif.strip().upper()[:1] in _LETRAS_CIF  # type: ignore[union-attr]


def persoa_para(conn: Connection, horta_id: int, papel: str | None, nome: str | None,
                **datos: Any) -> int:
    """A persoa ou entidade co mesmo NIF (ou co mesmo nome, se non hai NIF) nesa explotación,
    ou unha nova; queda co papel (se o ten). Os datos que lle faltaban complétanse."""
    datos = {k: (v.strip() if isinstance(v, str) else v) or None for k, v in datos.items()}
    nome = (nome or "").strip()[:200] or "Sen nome"
    if datos.get("nif"):
        fila = conn.execute(sa.text("SELECT id FROM persoa WHERE horta_id = :h AND nif = :n"),
                            {"h": horta_id, "n": datos["nif"]}).first()
    else:
        fila = conn.execute(sa.text(
            "SELECT id FROM persoa WHERE horta_id = :h AND lower(trim(nome)) = :n"),
            {"h": horta_id, "n": nome.lower()}).first()
    if fila is not None:
        persoa_id = int(fila.id)
        for campo, valor in datos.items():
            if valor is not None and campo != "tipo":
                conn.execute(sa.text(
                    f"UPDATE persoa SET {campo} = coalesce({campo}, :v) WHERE id = :i"),
                    {"v": valor, "i": persoa_id})
    else:
        datos["tipo"] = datos.get("tipo") or ("entidade" if e_cif(datos.get("nif")) else "persoa")
        campos = ", ".join(datos)
        valores = ", ".join(f":{c}" for c in datos)
        persoa_id = int(conn.execute(sa.text(
            f"INSERT INTO persoa (horta_id, nome, activa, discapacidade, {campos}) "
            f"VALUES (:horta_id, :nome, 1, 0, {valores})"),
            {"horta_id": horta_id, "nome": nome, **datos}).lastrowid)
    if papel is not None and not conn.execute(sa.text(
            "SELECT 1 FROM persoa_papel WHERE persoa_id = :i AND papel = :p"),
            {"i": persoa_id, "p": papel}).first():
        conn.execute(sa.text("INSERT INTO persoa_papel (persoa_id, papel) VALUES (:i, :p)"),
                     {"i": persoa_id, "p": papel})
    return persoa_id


def nome_de(conn: Connection, persoa_id: int | None) -> str | None:
    """Para as baixadas (downgrade): o nome da persoa, para volver ao texto."""
    if persoa_id is None:
        return None
    fila = conn.execute(sa.text("SELECT nome, nif, rega FROM persoa WHERE id = :i"),
                        {"i": persoa_id}).first()
    return fila.nome if fila else None


def pasar_a_persoas(conn: Connection, taboa: str, columna_id: str, papel: str | None,
                    consulta: str, nome: Any, datos: Any = lambda fila: {}) -> None:
    """Para cada fila de `consulta` (con `id`, `horta_id` e os textos), crea ou reutiliza a
    persoa (nome(fila), datos(fila)) co papel e gárdaa en `taboa.columna_id`. As filas sen
    ningún texto (nome(fila) None) quedan sen persoa."""
    for fila in conn.execute(sa.text(consulta)).mappings().all():
        texto = nome(fila)
        if not texto:
            continue
        persoa_id = persoa_para(conn, fila["horta_id"], papel, texto, **datos(fila))
        conn.execute(sa.text(f"UPDATE {taboa} SET {columna_id} = :p WHERE id = :i"),
                     {"p": persoa_id, "i": fila["id"]})


def primeiro(*textos: str | None) -> str | None:
    return next((t.strip() for t in textos if t and t.strip()), None)
```

### Paso 7 — `src/horta/services/persoas.py`

Antes:
```python
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Patrón oficial do descritor SIEX (Anexo VI, folla "Patrones texto") para NIF de persoa física.
_PATRON_NIF = re.compile(r"^[KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$")

CAMPOS_EDITABLES_PERSOA = frozenset(
    {"nome", "apelidos", "nif", "e_aplicador", "e_asesor", "ropo_numero", "ropo_tipo_carne",
     "ropo_caducidade", "regfer_numero", "activa", "e_titular", "e_traballador", "telefono",
     "email", "vinculo", "horas_ano", "formacion_agraria", "xenero", "data_nacemento",
     "discapacidade", "enderezo", "localidade", "codigo_postal", "provincia"}
)


VINCULOS = ("titular", "familiar", "asalariado", "socio", "externo")
XENEROS = ("muller", "home", "outro")


def _normalizar_e_validar(datos: dict[str, Any]) -> None:
    if datos.get("nif"):
        datos["nif"] = datos["nif"].strip().upper()
        if not _PATRON_NIF.match(datos["nif"]):
            raise OperacionNonPermitidaError("O NIF non é válido")
    if datos.get("e_aplicador") and not (datos.get("ropo_numero") and datos.get("ropo_caducidade")):
        raise OperacionNonPermitidaError(
            "Un aplicador precisa o nº ROPO e a data de caducidade do carné"
        )
    if datos.get("e_asesor") and not datos.get("ropo_numero"):
```

Despois:
```python
from horta.models.persoa import Persoa, PersoaPapel
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Patrón oficial do descritor SIEX (Anexo VI, folla "Patrones texto") para NIF de persoa física.
_PATRON_NIF = re.compile(r"^[KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$")
# NIF dunha entidade (CIF): letra da forma xurídica, 7 díxitos e control (díxito ou letra)
_PATRON_CIF = re.compile(r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$")
_PATRON_REXISTRO = re.compile(r"^ES\d{12}$")

TIPOS_PERSOA = {"persoa": "Persoa", "entidade": "Empresa ou entidade"}
# Papeis (docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md). Os do equipo saen
# na pestana Equipo; o resto, en Contactos. Unha persoa pode ter varios.
PAPEIS_EQUIPO: dict[str, str] = {
    "titular": "Titular",
    "representante": "Representante",
    "traballador": "Traballa na explotación",
    "aplicador": "Aplica fitosanitarios",
    "asesor": "Asesor",
}
PAPEIS_CONTACTO: dict[str, str] = {
    "cliente": "Cliente",
    "provedor": "Provedor",
    "veterinario": "Veterinario",
    "laboratorio": "Laboratorio",
    "servizos": "Empresa de servizos",
    "explotacion": "Outra explotación",
}
PAPEIS: dict[str, str] = PAPEIS_EQUIPO | PAPEIS_CONTACTO
# Quen pode facer un traballo: o equipo ou unha empresa de servizos
PAPEIS_QUEN = (*PAPEIS_EQUIPO, "servizos")

CAMPOS_EDITABLES_PERSOA = frozenset(
    {"tipo", "nome", "apelidos", "nif", "ropo_numero", "ropo_tipo_carne", "ropo_caducidade",
     "regfer_numero", "activa", "telefono", "email", "vinculo", "horas_ano",
     "formacion_agraria", "xenero", "data_nacemento", "discapacidade", "enderezo",
     "localidade", "codigo_postal", "provincia", "concello_codigo", "pais", "rega", "reaga",
     "nima", "ropveg", "rexistro_dixital", "num_asesoramento"}
)


VINCULOS = ("titular", "familiar", "asalariado", "socio", "externo")
XENEROS = ("muller", "home", "outro")


def _normalizar_e_validar(datos: dict[str, Any], papeis: set[str]) -> None:
    if datos.get("tipo", "persoa") not in TIPOS_PERSOA:
        raise OperacionNonPermitidaError("Indica se é unha persoa ou unha entidade")
    if not papeis <= set(PAPEIS):
        raise OperacionNonPermitidaError(f"Papel descoñecido: {', '.join(papeis - set(PAPEIS))}")
    entidade = datos.get("tipo") == "entidade"
    if datos.get("nif"):
        datos["nif"] = datos["nif"].strip().upper().replace("-", "").replace(" ", "")
        if not (_PATRON_CIF if entidade else _PATRON_NIF).match(datos["nif"]):
            raise OperacionNonPermitidaError("O NIF non é válido")
    for campo, nome in (("rega", "REGA"), ("reaga", "REAGA")):
        if datos.get(campo):
            datos[campo] = datos[campo].strip().upper().replace(" ", "")
            if not _PATRON_REXISTRO.match(datos[campo]):
                raise OperacionNonPermitidaError(
                    f"O código {nome} debe ter o formato ES seguido de 12 díxitos")
    if "aplicador" in papeis and not (datos.get("ropo_numero") and datos.get("ropo_caducidade")):
        raise OperacionNonPermitidaError(
            "Un aplicador precisa o nº ROPO e a data de caducidade do carné"
        )
    # A entidade de asesoramento (caderno 1.4) non ten ROPO: leva o seu nº de asesoramento
    if "asesor" in papeis and not entidade and not datos.get("ropo_numero"):
```

### Paso 8 — `src/horta/services/persoas.py`

Antes:
```python
def crear_persoa(
    session: Session, actor: Usuario, horta_id: int, nome: str, **campos: Any
) -> Persoa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _normalizar_e_validar(campos)
    persoa = Persoa(horta_id=horta_id, nome=nome, **campos)
    session.add(persoa)
    session.commit()
    return persoa


def actualizar_persoa(session: Session, actor: Usuario, persoa: Persoa, **cambios: Any) -> Persoa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_PERSOA
    if non_editables:
        raise ValueError(f"Campos non editables nunha persoa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, persoa.horta_id, actor, _ROLES_ESCRITURA)
    resultado = {c: getattr(persoa, c) for c in CAMPOS_EDITABLES_PERSOA} | cambios
    _normalizar_e_validar(resultado)
    for campo in cambios:
        setattr(persoa, campo, resultado[campo])
    session.commit()
    return persoa


def listar_persoas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True
) -> list[Persoa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return list(consulta.order_by(Persoa.nome).all())
```

Despois:
```python
def _un_so_titular(session: Session, horta_id: int, papeis: set[str], activa: bool,
                   excepto_id: int | None) -> None:
    if "titular" not in papeis or not activa:
        return
    outra = (session.query(Persoa).join(PersoaPapel)
             .filter(Persoa.horta_id == horta_id, Persoa.activa.is_(True),
                     PersoaPapel.papel == "titular", Persoa.id != (excepto_id or 0))
             .first())
    if outra is not None:
        raise OperacionNonPermitidaError(
            f"A explotación xa ten titular ({outra.nome}): quítalle antes ese papel")


def _gardar_papeis(persoa: Persoa, papeis: set[str]) -> None:
    persoa.papeis_rexistro = [p for p in persoa.papeis_rexistro if p.papel in papeis] + [
        PersoaPapel(papel=papel) for papel in sorted(papeis - persoa.papeis)]


def crear_persoa(
    session: Session, actor: Usuario, horta_id: int, nome: str,
    papeis: set[str] | frozenset[str] | tuple[str, ...] = (), **campos: Any
) -> Persoa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not nome.strip():
        raise OperacionNonPermitidaError("Indica o nome")
    _normalizar_e_validar(campos, set(papeis))
    _un_so_titular(session, horta_id, set(papeis), campos.get("activa", True), None)
    persoa = Persoa(horta_id=horta_id, nome=nome.strip(), **campos)
    _gardar_papeis(persoa, set(papeis))
    session.add(persoa)
    session.commit()
    return persoa


def actualizar_persoa(
    session: Session, actor: Usuario, persoa: Persoa,
    papeis: set[str] | frozenset[str] | tuple[str, ...] | None = None, **cambios: Any
) -> Persoa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_PERSOA
    if non_editables:
        raise ValueError(f"Campos non editables nunha persoa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, persoa.horta_id, actor, _ROLES_ESCRITURA)
    novos_papeis = persoa.papeis if papeis is None else set(papeis)
    resultado = {c: getattr(persoa, c) for c in CAMPOS_EDITABLES_PERSOA} | cambios
    _normalizar_e_validar(resultado, novos_papeis)
    _un_so_titular(session, persoa.horta_id, novos_papeis, resultado["activa"], persoa.id)
    for campo in cambios:
        setattr(persoa, campo, resultado[campo])
    _gardar_papeis(persoa, novos_papeis)
    session.commit()
    return persoa


def crear_contacto(
    session: Session, actor: Usuario, horta_id: int, nome: str, papel: str | None,
    **campos: Any
) -> Persoa:
    """Crear unha persoa dende un formulario de traballo (botón «Nova»), xa co papel que fai
    alí. Se xa hai unha co mesmo NIF, ou co mesmo nome se non se dá NIF, úsase esa."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    nif = (campos.get("nif") or "").strip().upper()
    existente = (consulta.filter_by(nif=nif).first() if nif else
                 next((p for p in consulta if p.nome.strip().lower() == nome.strip().lower()),
                      None))
    if existente is not None:
        return persoa_co_papel(session, horta_id, existente.id, papel, gardar=True) or existente
    return crear_persoa(session, actor, horta_id, nome, papeis={papel} if papel else set(),
                        **campos)


def persoa_co_papel(session: Session, horta_id: int, persoa_id: int | None,
                    papel: str | None, gardar: bool = False) -> Persoa | None:
    """A persoa escollida nun traballo ten que ser desta explotación; queda co papel que fai
    (p.ex. quen merca pasa a ser cliente). None se non se escolleu ningunha."""
    if persoa_id is None:
        return None
    persoa = session.get(Persoa, persoa_id)
    if persoa is None or persoa.horta_id != horta_id:
        raise OperacionNonPermitidaError("A persoa ou entidade indicada non é desta explotación")
    if papel is not None and papel not in persoa.papeis:
        persoa.papeis_rexistro.append(PersoaPapel(papel=papel))
        if gardar:
            session.commit()
    return persoa


def con_papel(session: Session, horta_id: int, papel: str) -> list[Persoa]:
    """As persoas activas da explotación con ese papel."""
    return list(session.query(Persoa).join(PersoaPapel)
                .filter(Persoa.horta_id == horta_id, Persoa.activa.is_(True),
                        PersoaPapel.papel == papel)
                .order_by(Persoa.nome))


def titular_da_horta(session: Session, horta_id: int) -> Persoa | None:
    return next(iter(con_papel(session, horta_id, "titular")), None)


def nome_completo(persoa: Persoa | None) -> str:
    if persoa is None:
        return ""
    return " ".join(x for x in (persoa.nome, persoa.apelidos or "") if x)


def listar_persoas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True,
    papel: str | None = None,
) -> list[Persoa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    if papel is not None:
        consulta = consulta.join(PersoaPapel).filter(PersoaPapel.papel == papel)
    return list(consulta.order_by(Persoa.nome).all())


def listar_quen(session: Session, actor: Usuario, horta_id: int) -> list[Persoa]:
    """As persoas activas que poden facer un traballo («Quen o fixo»): o equipo e as
    empresas de servizos. Os clientes, provedores, laboratorios... non."""
    return [p for p in listar_persoas(session, actor, horta_id) if p.ten_papel(*PAPEIS_QUEN)]
```

### Paso 9 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
        if persoa is None or persoa.horta_id != horta.id or not persoa.e_aplicador:
```

Despois:
```python
        if persoa is None or persoa.horta_id != horta.id or not persoa.ten_papel("aplicador"):
```

### Paso 10 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
        if asesor is None or asesor.horta_id != horta.id or not asesor.e_asesor:
```

Despois:
```python
        if asesor is None or asesor.horta_id != horta.id or not asesor.ten_papel("asesor"):
```

### Paso 11 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
            aplicadores={p.id: p.nome for p in persoas if p.e_aplicador},
            asesores={p.id: p.nome for p in persoas if p.e_asesor},
```

Despois:
```python
            aplicadores={p.id: p.nome for p in persoas if p.ten_papel("aplicador")},
            asesores={p.id: p.nome for p in persoas if p.ten_papel("asesor")},
```

### Paso 12 — `src/horta/ui/pages/equipo.py`

Antes:
```python
"""Sección Equipo: a xente da explotación, as súas funcións e o seu acceso á app."""
```

Despois:
```python
"""Sección Persoas: toda a xente e as empresas coas que trata a explotación, cos seus papeis.
Pestana Equipo (quen traballa nela, coas horas e o acceso á app) e pestana Contactos (o resto:
clientes, provedores, laboratorios...). É unha soa lista: quen ten papeis dos dous lados sae
nas dúas (docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md)."""
```

### Paso 13 — `src/horta/ui/pages/equipo.py`

Antes:
```python
from horta.services.persoas import (
```

Despois:
```python
from horta.services.persoas import (
    PAPEIS,
    PAPEIS_CONTACTO,
    PAPEIS_EQUIPO,
    TIPOS_PERSOA,
```

### Paso 14 — `src/horta/ui/pages/equipo.py`

Antes:
```python
def _funcions(p: Persoa) -> str:
    return ", ".join(nome for nome, si in (
        ("titular", p.e_titular), ("traballador", p.e_traballador),
        ("aplicador", p.e_aplicador), ("asesor", p.e_asesor)) if si)
```

Despois:
```python
# Os rexistros que pode ter unha persoa ou entidade, segundo o seu papel
_REXISTROS = (("rega", "REGA (ES + 12 díxitos)"), ("reaga", "REAGA"), ("nima", "NIMA"),
              ("ropveg", "Nº ROPVEG"), ("rexistro_dixital", "Nº de rexistro dixital de alimentos"),
              ("num_asesoramento", "Nº de identificación da entidade de asesoramento"))
_CONTACTO = (("telefono", "Teléfono"), ("email", "Email de contacto"),
             ("enderezo", "Enderezo"), ("localidade", "Localidade"),
             ("codigo_postal", "Código postal"), ("provincia", "Provincia"),
             ("concello_codigo", "Concello (código INE)"), ("pais", "País, se non é España"))
_CON_ROPO = ("aplicador", "asesor", "servizos")


def _papeis(p: Persoa, cales: dict[str, str]) -> str:
    return ", ".join(nome for clave, nome in cales.items() if p.ten_papel(clave))


def _e_equipo(p: Persoa) -> bool:
    return p.ten_papel(*PAPEIS_EQUIPO)


def _e_contacto(p: Persoa) -> bool:
    return p.ten_papel(*PAPEIS_CONTACTO) or not p.papeis
```

### Paso 15 — `src/horta/ui/pages/equipo.py`

Antes:
```python
        if p.activa and p.e_aplicador and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(f"⚠ O carné ROPO de {p.nome} caducou o {p.ropo_caducidade:%d/%m/%Y}") \
                    .classes("aviso w-full")
            elif dias <= _AVISO_DIAS:
                ui.label(f"⚠ O carné ROPO de {p.nome} caduca en {dias} días").classes(
                    "aviso w-full"
                )

    horas = sum(p.horas_ano or 0 for p in persoas if p.activa)
    ui.label(f"Traballo ao ano: {horas:g} horas = {horas / HORAS_UTA:.2f} UTA").classes(
        "texto-suave")

    filas = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(), "funcions": _funcions(p),
         "ropo": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "acceso": _ACCESOS[_clave_acceso(accesos[p.id])],
         "activa": "si" if p.activa else "non"}
        for p in persoas
    ]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Nome"), ("funcions", "Funcións"), ("ropo", "Carné ROPO ata"),
            ("acceso", "Acceso á app"), ("activa", "Activa"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai ninguén no equipo" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Nova persoa").classes("text-h6")
        nome = ui.input("Nome").classes("w-full")
        apelidos = ui.input("Apelidos").classes("w-full")
        nif = ui.input("NIF").classes("w-full")
        telefono = ui.input("Teléfono").classes("w-full")
        email = ui.input("Email de contacto").classes("w-full")
        with ui.expansion("Enderezo (para o caderno, se é o titular)").classes("w-full"):
            enderezo = ui.input("Enderezo").classes("w-full")
            localidade = ui.input("Localidade").classes("w-full")
            codigo_postal = ui.input("Código postal").classes("w-full")
            provincia = ui.input("Provincia").classes("w-full")
        ui.label("Funcións").classes("text-subtitle2 q-mt-sm")
        with ui.row():
            titular = ui.checkbox("Titular")
            traballador = ui.checkbox("Traballador")
            aplicador = ui.checkbox("Aplica fitosanitarios")
            asesor = ui.checkbox("Asesor")
        ropo = ui.input("Nº ROPO").classes("w-full")
        tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                         label="Tipo de carné", clearable=True).classes("w-full")
        caducidade = campo_data("Caducidade do carné")
        regfer = ui.input("Nº REGFER").classes("w-full")
        with ui.expansion("Traballo (para o plan de empresa)").classes("w-full"):
            vinculo = ui.select(list(VINCULOS), label="Vínculo coa explotación",
                                clearable=True).classes("w-full")
            horas_ano = ui.input("Horas ao ano").classes("w-full")
            formacion = ui.input("Formación agraria").classes("w-full")
        with ui.expansion("Colectivo (opcional, para axudas ao emprego)").classes("w-full"):
            xenero = ui.select(list(XENEROS), label="Xénero", clearable=True).classes("w-full")
            nacemento = campo_data("Data de nacemento")
            discapacidade = ui.checkbox("Persoa con discapacidade")
        activa = ui.checkbox("Activa", value=True)
        with ui.column().classes("w-full gap-1") as bloque_acceso:
            ui.label("Acceso á app").classes("text-subtitle2 q-mt-sm")
            acceso = ui.select(_ACCESOS, value="", label="Permiso").classes("w-full")
            email_conta = ui.input("Email da súa conta na app").classes("w-full")
        bloque_acceso.set_visibility(e_admin)

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            datos: dict[str, Any] = dict(
                apelidos=apelidos.value or None, nif=nif.value or None,
                telefono=telefono.value or None, email=email.value or None,
                enderezo=enderezo.value or None, localidade=localidade.value or None,
                codigo_postal=codigo_postal.value or None, provincia=provincia.value or None,
                e_titular=titular.value, e_traballador=traballador.value,
                e_aplicador=aplicador.value, e_asesor=asesor.value,
```

Despois:
```python
        if p.activa and p.ten_papel("aplicador") and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(f"⚠ O carné ROPO de {p.nome} caducou o {p.ropo_caducidade:%d/%m/%Y}") \
                    .classes("aviso w-full")
            elif dias <= _AVISO_DIAS:
                ui.label(f"⚠ O carné ROPO de {p.nome} caduca en {dias} días").classes(
                    "aviso w-full"
                )

    horas = sum(p.horas_ano or 0 for p in persoas if p.activa and _e_equipo(p))

    filas_equipo = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(),
         "funcions": _papeis(p, PAPEIS_EQUIPO),
         "ropo": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "acceso": _ACCESOS[_clave_acceso(accesos[p.id])],
         "activa": "si" if p.activa else "non"}
        for p in persoas if _e_equipo(p)
    ]
    filas_contactos = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(),
         "papeis": _papeis(p, PAPEIS_CONTACTO), "nif": p.nif or "",
         "telefono": p.telefono or "", "activa": "si" if p.activa else "non"}
        for p in persoas if _e_contacto(p)
    ]
    with ui.tabs().classes("w-full") as pestanas:
        pestana_equipo = ui.tab("Equipo", icon="groups")
        pestana_contactos = ui.tab("Contactos", icon="contacts")
    with ui.tab_panels(pestanas, value=pestana_equipo).classes("w-full"):
        with ui.tab_panel(pestana_equipo):
            ui.label(f"Traballo ao ano: {horas:g} horas = {horas / HORAS_UTA:.2f} UTA").classes(
                "texto-suave")
            taboa_equipo = ui.table(
                columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
                    ("nome", "Nome"), ("funcions", "Funcións"), ("ropo", "Carné ROPO ata"),
                    ("acceso", "Acceso á app"), ("activa", "Activa"))],
                rows=filas_equipo, row_key="id",
                selection="single" if pode_editar else None,
            ).classes("w-full taboa").props(
                f'flat bordered no-data-label="Aínda non hai ninguén no equipo" {TEXTOS_TABOA}')
        with ui.tab_panel(pestana_contactos):
            taboa_contactos = ui.table(
                columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
                    ("nome", "Nome"), ("papeis", "Que é"), ("nif", "NIF"),
                    ("telefono", "Teléfono"), ("activa", "Activa"))],
                rows=filas_contactos, row_key="id",
                selection="single" if pode_editar else None,
            ).classes("w-full taboa").props(
                'flat bordered no-data-label="Aínda non hai clientes, provedores nin outros '
                f'contactos" {TEXTOS_TABOA}')

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Nova persoa").classes("text-h6")
        tipo_persoa = ui.radio(TIPOS_PERSOA, value="persoa").props("inline")
        nome = ui.input("Nome ou razón social").classes("w-full")
        apelidos = ui.input("Apelidos").classes("w-full")
        apelidos.bind_visibility_from(tipo_persoa, "value", value="persoa")
        nif = ui.input("NIF").classes("w-full")
        papeis = ui.select(PAPEIS, label="Que é (pode ser varias cousas)", multiple=True,
                           value=[]).classes("w-full").props("use-chips")
        with ui.expansion("Contacto e enderezo").classes("w-full"):
            contacto = {campo: ui.input(etiqueta).classes("w-full")
                        for campo, etiqueta in _CONTACTO}
        with ui.expansion("Rexistros (REGA, NIMA, ROPVEG...)").classes("w-full"):
            rexistros = {campo: ui.input(etiqueta).classes("w-full")
                         for campo, etiqueta in _REXISTROS}
        with ui.column().classes("w-full gap-0") as bloque_ropo:
            ropo = ui.input("Nº ROPO").classes("w-full")
            tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                             label="Tipo de carné", clearable=True).classes("w-full")
            caducidade = campo_data("Caducidade do carné")
            regfer = ui.input("Nº REGFER").classes("w-full")
        with ui.expansion("Traballo (para o plan de empresa)").classes("w-full") as bloque_traballo:
            vinculo = ui.select(list(VINCULOS), label="Vínculo coa explotación",
                                clearable=True).classes("w-full")
            horas_ano = ui.input("Horas ao ano").classes("w-full")
            formacion = ui.input("Formación agraria").classes("w-full")
        with ui.expansion("Colectivo (opcional, para axudas ao emprego)").classes(
                "w-full") as bloque_colectivo:
            xenero = ui.select(list(XENEROS), label="Xénero", clearable=True).classes("w-full")
            nacemento = campo_data("Data de nacemento")
            discapacidade = ui.checkbox("Persoa con discapacidade")
        activa = ui.checkbox("Activa", value=True)
        with ui.column().classes("w-full gap-1") as bloque_acceso:
            ui.label("Acceso á app").classes("text-subtitle2 q-mt-sm")
            acceso = ui.select(_ACCESOS, value="", label="Permiso").classes("w-full")
            email_conta = ui.input("Email da súa conta na app").classes("w-full")

        def mostrar_bloques() -> None:
            escollidos = set(papeis.value or [])
            bloque_ropo.set_visibility(bool(escollidos & set(_CON_ROPO)))
            equipo = bool(escollidos & set(PAPEIS_EQUIPO))
            bloque_traballo.set_visibility(equipo)
            bloque_colectivo.set_visibility(equipo and tipo_persoa.value == "persoa")
            # O acceso á app só para quen traballa na explotación (e só o dá quen administra)
            bloque_acceso.set_visibility(e_admin and equipo)

        papeis.on_value_change(mostrar_bloques)
        tipo_persoa.on_value_change(mostrar_bloques)

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            datos: dict[str, Any] = dict(
                tipo=tipo_persoa.value,
                apelidos=(apelidos.value or None) if tipo_persoa.value == "persoa" else None,
                nif=nif.value or None,
                **{c: (e.value or None) for c, e in {**contacto, **rexistros}.items()},
```

### Paso 16 — `src/horta/ui/pages/equipo.py`

Antes:
```python
                        persoa = crear_persoa(session, actor, horta_id, nome.value, **datos)
                    else:
                        existente = session.get(Persoa, editando["id"])
                        if existente is None:
                            return
                        persoa = existente
                        actualizar_persoa(session, actor, persoa, nome=nome.value,
                                          activa=activa.value, **datos)
```

Despois:
```python
                        persoa = crear_persoa(session, actor, horta_id, nome.value,
                                              papeis=set(papeis.value or []), **datos)
                    else:
                        existente = session.get(Persoa, editando["id"])
                        if existente is None:
                            return
                        persoa = existente
                        actualizar_persoa(session, actor, persoa, nome=nome.value,
                                          papeis=set(papeis.value or []), activa=activa.value,
                                          **datos)
```

### Paso 17 — `src/horta/ui/pages/equipo.py`

Antes:
```python
    textos = (nome, apelidos, nif, telefono, email, enderezo, localidade, codigo_postal,
              provincia, ropo, caducidade, regfer, horas_ano,
              formacion, nacemento, email_conta)
    casillas = (titular, traballador, aplicador, asesor, discapacidade)

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova persoa"
        for campo in textos:
            campo.value = ""
        for casilla in casillas:
            casilla.value = False
        tipo.value = vinculo.value = xenero.value = None
        activa.value = True
        acceso.value = ""
        dialogo.open()

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha persoa na táboa", type="warning")
            return
        p = next(x for x in persoas if x.id == taboa.selected[0]["id"])
        editando["id"] = p.id
        titulo.text = "Editar persoa"
        nome.value = p.nome
        apelidos.value = p.apelidos or ""
        nif.value = p.nif or ""
        telefono.value = p.telefono or ""
        email.value = p.email or ""
        enderezo.value = p.enderezo or ""
        localidade.value = p.localidade or ""
        codigo_postal.value = p.codigo_postal or ""
        provincia.value = p.provincia or ""
        titular.value, traballador.value = p.e_titular, p.e_traballador
        aplicador.value, asesor.value = p.e_aplicador, p.e_asesor
```

Despois:
```python
    textos = (nome, apelidos, nif, *contacto.values(), *rexistros.values(), ropo, caducidade,
              regfer, horas_ano, formacion, nacemento, email_conta)

    def en_equipo() -> bool:
        return pestanas.value in (None, pestana_equipo, pestana_equipo.props["name"])

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova persoa ou entidade"
        for campo in textos:
            campo.value = ""
        tipo_persoa.value = "persoa"
        papeis.value = ["traballador"] if en_equipo() else []
        discapacidade.value = False
        tipo.value = vinculo.value = xenero.value = None
        activa.value = True
        acceso.value = ""
        mostrar_bloques()
        dialogo.open()

    def abrir_edicion() -> None:
        taboa = taboa_equipo if en_equipo() else taboa_contactos
        if not taboa.selected:
            ui.notify("Selecciona unha persoa na táboa", type="warning")
            return
        p = next(x for x in persoas if x.id == taboa.selected[0]["id"])
        editando["id"] = p.id
        titulo.text = "Editar persoa ou entidade"
        tipo_persoa.value = p.tipo
        nome.value = p.nome
        apelidos.value = p.apelidos or ""
        nif.value = p.nif or ""
        for campo, entrada in {**contacto, **rexistros}.items():
            entrada.value = getattr(p, campo) or ""
        papeis.value = [clave for clave in PAPEIS if p.ten_papel(clave)]
```

### Paso 18 — `src/horta/ui/pages/equipo.py`

Antes:
```python
        dialogo.open()

    with ui.row():
        ui.button("Nova persoa", icon="person_add", on_click=abrir_nova)
```

Despois:
```python
        mostrar_bloques()
        dialogo.open()

    with ui.row():
        ui.button("Nova persoa ou entidade", icon="person_add", on_click=abrir_nova)
```

### Paso 19 — `src/horta/ui/layout.py`

Antes:
```python
    Seccion("equipo", "Equipo", "groups", "Explotación"),
```

Despois:
```python
    Seccion("equipo", "Persoas", "groups", "Explotación"),
```

### Paso 20 — `tests/services/test_persoas.py`

Antes:
```python
                          e_aplicador=True, ropo_numero="1234567890",
                          ropo_caducidade=date(2027, 5, 1))
    assert persoa.nif == "12345678Z"
    assert "Xan" in [p.nome for p in listar_persoas(session, ana, horta.id)]


def test_aplicador_sen_ropo_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="nº ROPO e a data de caducidade"):
        crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True)
```

Despois:
```python
                          papeis={"aplicador"}, ropo_numero="1234567890",
                          ropo_caducidade=date(2027, 5, 1))
    assert persoa.nif == "12345678Z"
    assert "Xan" in [p.nome for p in listar_persoas(session, ana, horta.id)]


def test_aplicador_sen_ropo_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="nº ROPO e a data de caducidade"):
        crear_persoa(session, ana, horta.id, "Xan", papeis={"aplicador"})
```

### Paso 21 — `tests/services/test_persoas.py`

Antes:
```python
    persoa = crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
```

Despois:
```python
    persoa = crear_persoa(session, ana, horta.id, "Xan", papeis={"aplicador"}, ropo_numero="1",
```

### Paso 22 — `tests/services/test_tratamentos_fito.py`

Antes:
```python
    xan = crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
```

Despois:
```python
    xan = crear_persoa(session, ana, horta.id, "Xan", papeis={"aplicador"}, ropo_numero="1",
```

### Paso 23 — `tests/services/test_caderno_tratamentos.py`

Antes:
```python
    asesora = crear_persoa(session, ana, horta.id, "Lúa", e_asesor=True, ropo_numero="R-9")
```

Despois:
```python
    asesora = crear_persoa(session, ana, horta.id, "Lúa", papeis={"asesor"}, ropo_numero="R-9")
```

### Paso 24 — `src/horta/services/en_regra.py`

Antes:
```python
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import ropo_vixente
```

Despois:
```python
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import con_papel, ropo_vixente
```

### Paso 25 — `src/horta/services/en_regra.py`

Antes:
```python
    aplicadores = [
        p
        for p in session.query(Persoa).filter_by(horta_id=horta.id, activa=True, e_aplicador=True)
        if ropo_vixente(p, hoxe)
    ]
```

Despois:
```python
    aplicadores = [p for p in con_papel(session, horta.id, "aplicador") if ropo_vixente(p, hoxe)]
```

### Paso 26 — `src/horta/services/caderno.py`

Antes:
```python
    aplicadores = [p for p in persoas if p.e_aplicador or p.e_asesor]
    orde_persoa = {p.id: i for i, p in enumerate(aplicadores, 1)}
    maquinas = session.query(Maquina).filter_by(horta_id=horta_id).order_by(Maquina.id).all()
    orde_maquina = {m.id: i for i, m in enumerate(maquinas, 1)}
    titular = next((p for p in persoas if p.e_titular), None)
```

Despois:
```python
    # 1.2: persoas ou empresas que interveñen nos tratamentos (aplican, asesoran ou dan servizo)
    aplicadores = [p for p in persoas if p.ten_papel("aplicador", "asesor", "servizos")
                   and (p.ropo_numero or p.regfer_numero or p.ten_papel("aplicador"))]
    orde_persoa = {p.id: i for i, p in enumerate(aplicadores, 1)}
    maquinas = session.query(Maquina).filter_by(horta_id=horta_id).order_by(Maquina.id).all()
    orde_maquina = {m.id: i for i, m in enumerate(maquinas, 1)}
    titular = next((p for p in persoas if p.activa and p.ten_papel("titular")), None)
```

### Paso 27 — `src/horta/services/caderno.py`

Antes:
```python
           "X" if p.e_asesor else "", p.regfer_numero or ""] for p in aplicadores],
```

Despois:
```python
           "X" if p.ten_papel("asesor") else "", p.regfer_numero or ""] for p in aplicadores],
```

### Paso 28 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.persoa import Persoa
```

Despois:
```python
from horta.models.persoa import Persoa, PersoaPapel
```

### Paso 29 — `src/horta/services/hortas.py`

Antes:
```python
                       email=actor.email))
```

Despois:
```python
                       email=actor.email, papeis_rexistro=[PersoaPapel(papel="traballador")]))
```

### Paso 30 — `tests/services/test_en_regra.py`

Antes:
```python
        e_aplicador=True,
```

Despois:
```python
        papeis={"aplicador"},
```

### Paso 31 — `tests/services/test_caderno_datos.py`

Antes:
```python
    crear_persoa(session, ana, horta.id, "Ana", e_titular=True, enderezo="Rúa Nova 1",
```

Despois:
```python
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, enderezo="Rúa Nova 1",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (1/11): papeis de cada persoa: feito.

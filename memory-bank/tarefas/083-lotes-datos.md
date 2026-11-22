# Tarefa 083 — Lotes (1/5): o lote como ficha

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As colleitas e a produción entran nun lote (ficha), que suma as do mesmo produto; as saídas do lote (venda, casa, transformación, perda, animais) e o que queda; o cliente da colleita pasa a unha venda; caderno 5 dende as vendas. Deseño: `docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md` (paso 4 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/f2c4e6a8b0d5_lotes_e_saidas.py` (**ficheiro novo**)
- `src/horta/models/lote.py` (**ficheiro novo**)
- `src/horta/models/colleita.py`
- `src/horta/models/producion_animal.py`
- `src/horta/models/__init__.py`
- `src/horta/services/lotes.py` (**ficheiro novo**)
- `src/horta/services/colleitas.py`
- `src/horta/services/producions_animais.py`
- `src/horta/services/caderno.py`
- `tests/services/test_colleitas_lote.py`
- `tests/services/test_caderno.py`
- `tests/services/test_caderno_cliente.py`
- `tests/services/test_colleitas.py`
- `tests/services/test_producions_animais.py`
- `tests/test_migracion_tratamento_fito.py`
- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/f2c4e6a8b0d5_lotes_e_saidas.py`

Contido completo:
```python
"""lotes e saídas: os lotes das colleitas e da produción pasan a fichas; o cliente da colleita
pasa a unha saída de venda

Revision ID: f2c4e6a8b0d5
Revises: e1b3d5f7a9c4
Create Date: 2026-10-28 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import persoa_para, primeiro


# revision identifiers, used by Alembic.
revision: str = 'f2c4e6a8b0d5'
down_revision: Union[str, Sequence[str], None] = 'e1b3d5f7a9c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PROTEXIDOS = ("4", "19", "26", "27", "28")
_PRODUTOS = {"ovos": "Ovos", "leite": "Leite", "mel": "Mel", "cera": "Cera", "la": "La",
             "outro": "Outro"}
_CATEGORIA_ANIMAL = {"ovos": "ovos", "mel": "mel"}
_CLIENTE = ("cliente_nome", "cliente_nif", "cliente_enderezo", "cliente_reaga")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "lote",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("produto", sa.String(length=120), nullable=False),
        sa.Column("cultivo_siex_codigo", sa.Integer(), nullable=True),
        sa.Column("produto_animal", sa.String(length=20), nullable=True),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("categoria_venda_directa", sa.String(length=20), nullable=True),
        sa.Column("protexido", sa.Boolean(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("horta_id", "codigo"),
    )
    op.create_index(op.f("ix_lote_horta_id"), "lote", ["horta_id"])
    op.create_table(
        "lote_saida",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("lote_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("canle", sa.String(length=20), nullable=True),
        sa.Column("lugar", sa.String(length=200), nullable=True),
        sa.Column("comprador_id", sa.Integer(), nullable=True),
        sa.Column("albaran_factura", sa.String(length=60), nullable=True),
        sa.Column("importe", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("maquina_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["comprador_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["lote_id"], ["lote.id"]),
        sa.ForeignKeyConstraint(["maquina_id"], ["maquina.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_lote_saida_horta_id"), "lote_saida", ["horta_id"])
    op.create_index(op.f("ix_lote_saida_lote_id"), "lote_saida", ["lote_id"])
    for taboa in ("colleita", "producion_animal"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("lote_id", sa.Integer(), nullable=True))
    conn = op.get_bind()
    lotes: dict[tuple[int, str], int] = {}

    def lote(horta_id: int, codigo: str, data, **datos) -> int:
        chave = (horta_id, codigo)
        if chave not in lotes:
            lotes[chave] = conn.execute(sa.text(
                "INSERT INTO lote (horta_id, codigo, produto, cultivo_siex_codigo, "
                "produto_animal, unidade, categoria_venda_directa, protexido, data, baixa) "
                "VALUES (:h, :c, :produto, :siex, :animal, :unidade, :categoria, :protexido, "
                ":data, 0)"), {"h": horta_id, "c": codigo, "data": data, **datos}).lastrowid
        else:
            conn.execute(sa.text("UPDATE lote SET data = min(data, :d) WHERE id = :i"),
                         {"d": data, "i": lotes[chave]})
        return lotes[chave]

    for f in conn.execute(sa.text(
            "SELECT c.id, p.horta_id, c.lote, c.data, c.data_fin, c.cantidade, c.unidade, "
            "c.persoa_id, c.albaran_factura, c.cliente_nome, c.cliente_nif, "
            "c.cliente_enderezo, c.cliente_reaga, cu.especie, cu.cultivo_siex_codigo, "
            "cu.sistema_cultivo FROM colleita c JOIN cultivo cu ON cu.id = c.cultivo_id "
            "JOIN parcela p ON p.id = cu.parcela_id ORDER BY c.data, c.id")).mappings().all():
        lote_id = lote(f["horta_id"], f["lote"], f["data"], produto=f["especie"],
                       siex=f["cultivo_siex_codigo"], animal=None, unidade=f["unidade"],
                       categoria=None, protexido=(f["sistema_cultivo"] or "") in _PROTEXIDOS)
        conn.execute(sa.text("UPDATE colleita SET lote_id = :l WHERE id = :i"),
                     {"l": lote_id, "i": f["id"]})
        # O cliente e o albará da colleita: unha venda de toda a colleita a ese cliente
        if any(f[c] for c in _CLIENTE) or f["albaran_factura"]:
            cliente = None
            if any(f[c] for c in _CLIENTE):
                cliente = persoa_para(
                    conn, f["horta_id"], "cliente",
                    primeiro(f["cliente_nome"], f["cliente_nif"], f["cliente_reaga"]),
                    nif=f["cliente_nif"], enderezo=f["cliente_enderezo"],
                    reaga=f["cliente_reaga"])
            conn.execute(sa.text(
                "INSERT INTO lote_saida (horta_id, lote_id, data, data_fin, tipo, cantidade, "
                "unidade, canle, comprador_id, albaran_factura, persoa_id, baixa, created_at) "
                "VALUES (:h, :l, :d, :df, 'venda', :c, :u, 'almacen', :cl, :a, :p, 0, "
                "CURRENT_TIMESTAMP)"),
                {"h": f["horta_id"], "l": lote_id, "d": f["data"],
                 "df": f["data_fin"] or f["data"], "c": f["cantidade"], "u": f["unidade"],
                 "cl": cliente, "a": f["albaran_factura"], "p": f["persoa_id"]})
    for f in conn.execute(sa.text(
            "SELECT id, horta_id, lote, data, produto, unidade FROM producion_animal "
            "ORDER BY data, id")).mappings().all():
        lote_id = lote(f["horta_id"], f["lote"], f["data"],
                       produto=_PRODUTOS.get(f["produto"], "Outro"), siex=None,
                       animal=f["produto"], unidade=f["unidade"],
                       categoria=_CATEGORIA_ANIMAL.get(f["produto"]), protexido=False)
        conn.execute(sa.text("UPDATE producion_animal SET lote_id = :l WHERE id = :i"),
                     {"l": lote_id, "i": f["id"]})
    for taboa in ("colleita", "producion_animal"):
        with op.batch_alter_table(taboa) as batch:
            batch.alter_column("lote_id", existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key(f"fk_{taboa}_lote_id", "lote", ["lote_id"], ["id"])
            batch.create_index(f"ix_{taboa}_lote_id", ["lote_id"])
            batch.drop_column("lote")
    with op.batch_alter_table("colleita") as batch:
        batch.drop_column("albaran_factura")
        for columna in _CLIENTE:
            batch.drop_column(columna)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("colleita") as batch:
        batch.add_column(sa.Column("albaran_factura", sa.String(60), nullable=True))
        batch.add_column(sa.Column("cliente_nome", sa.String(200), nullable=True))
        batch.add_column(sa.Column("cliente_nif", sa.String(14), nullable=True))
        batch.add_column(sa.Column("cliente_enderezo", sa.String(250), nullable=True))
        batch.add_column(sa.Column("cliente_reaga", sa.String(20), nullable=True))
    for taboa in ("colleita", "producion_animal"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("lote", sa.String(40), nullable=True))
    conn = op.get_bind()
    for taboa in ("colleita", "producion_animal"):
        conn.execute(sa.text(
            f"UPDATE {taboa} SET lote = (SELECT codigo FROM lote WHERE lote.id = {taboa}.lote_id)"))
    # A primeira venda de cada lote de colleitas volve ao cliente da colleita
    conn.execute(sa.text(
        "UPDATE colleita SET (albaran_factura, cliente_nome, cliente_nif, cliente_enderezo, "
        "cliente_reaga) = (SELECT s.albaran_factura, p.nome, p.nif, p.enderezo, p.reaga "
        "FROM lote_saida s LEFT JOIN persoa p ON p.id = s.comprador_id "
        "WHERE s.lote_id = colleita.lote_id AND s.tipo = 'venda' ORDER BY s.id LIMIT 1)"))
    for taboa in ("colleita", "producion_animal"):
        with op.batch_alter_table(taboa) as batch:
            batch.alter_column("lote", existing_type=sa.String(40), nullable=False)
            batch.drop_index(f"ix_{taboa}_lote_id")
            batch.drop_constraint(f"fk_{taboa}_lote_id", type_="foreignkey")
            batch.drop_column("lote_id")
    op.drop_index(op.f("ix_lote_saida_lote_id"), table_name="lote_saida")
    op.drop_index(op.f("ix_lote_saida_horta_id"), table_name="lote_saida")
    op.drop_table("lote_saida")
    op.drop_index(op.f("ix_lote_horta_id"), table_name="lote")
    op.drop_table("lote")
```

### Paso 2 — crear o ficheiro `src/horta/models/lote.py`

Contido completo:
```python
"""Lotes do produto que sae da explotación e as súas saídas (venda, casa, transformación,
perda, animais): docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md. Nun lote entran
colleitas ou producións dos animais do mesmo produto; o que queda calcúlase."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Lote(Base):
    __tablename__ = "lote"
    __table_args__ = (UniqueConstraint("horta_id", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # Trazabilidade (Reg. CE 178/2002 art. 18): AAAA-PRODUTO-NNN, único na explotación
    codigo: Mapped[str] = mapped_column(String(40))
    produto: Mapped[str] = mapped_column(String(120))
    # Que produto é: o cultivo oficial (colleitas) ou o produto animal (services.producions_animais)
    cultivo_siex_codigo: Mapped[int | None] = mapped_column(Integer, default=None)
    produto_animal: Mapped[str | None] = mapped_column(String(20), default=None)
    unidade: Mapped[str] = mapped_column(String(20))
    # Decreto 125/2014 anexo II (services.lotes.CATEGORIAS_VENDA_DIRECTA) e se é de invernadoiro
    categoria_venda_directa: Mapped[str | None] = mapped_column(String(20), default=None)
    protexido: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[date] = mapped_column(Date)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)


class LoteSaida(ParteComun, FeitoPor, ConMaquina, Base):
    """Cada saída dun lote: un traballo coa parte común."""

    __tablename__ = "lote_saida"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    # services.lotes.TIPOS_SAIDA: venda, casa, transformacion, perda, animais
    tipo: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    # Só nas vendas (Decreto 125/2014 art. 6; CUE 3)
    canle: Mapped[str | None] = mapped_column(String(20), default=None)
    lugar: Mapped[str | None] = mapped_column(String(200), default=None)
    comprador_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    importe: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 3 — `src/horta/models/colleita.py`

Antes:
```python
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
```

Despois:
```python
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.lote import Lote
```

### Paso 4 — `src/horta/models/colleita.py`

Antes:
```python
    lote: Mapped[str] = mapped_column(String(40))
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    # Caderno 5 (colleita comercializada): cliente; trazabilidade (Reg. CE 178/2002 art. 18)
    cliente_nome: Mapped[str | None] = mapped_column(String(200), default=None)
    cliente_nif: Mapped[str | None] = mapped_column(String(14), default=None)
    cliente_enderezo: Mapped[str | None] = mapped_column(String(250), default=None)
    cliente_reaga: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_colleita: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_restos: Mapped[str | None] = mapped_column(String(20), default=None)
    # Anexo V CUE 11 (colleita): respostas S/N obrigatorias e maquinaria (voluntaria)
    obten_sementes: Mapped[bool] = mapped_column(Boolean, default=False)
    obten_plantas: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_colleita_ambiental: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    # O lote onde entra (models.lote); o cliente e o albará van na súa saída de venda
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    lote_ficha: Mapped[Lote] = relationship(lazy="joined")
    destino_colleita: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_restos: Mapped[str | None] = mapped_column(String(20), default=None)
    # Anexo V CUE 11 (colleita): respostas S/N obrigatorias e maquinaria (voluntaria)
    obten_sementes: Mapped[bool] = mapped_column(Boolean, default=False)
    obten_plantas: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_colleita_ambiental: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)

    @property
    def lote(self) -> str:
        """O código do lote."""
        return self.lote_ficha.codigo
```

### Paso 5 — `src/horta/models/producion_animal.py`

Antes:
```python
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
```

Despois:
```python
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.lote import Lote
```

### Paso 6 — `src/horta/models/producion_animal.py`

Antes:
```python
    # Trazabilidade (Reg. CE 178/2002 art. 18): único na explotación, xunto cos das colleitas
    lote: Mapped[str] = mapped_column(String(40))
```

Despois:
```python
    # O lote onde entra o producido menos o retirado (models.lote)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    lote_ficha: Mapped[Lote] = relationship(lazy="joined")

    @property
    def lote(self) -> str:
        """O código do lote."""
        return self.lote_ficha.codigo
```

### Paso 7 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.labor import Labor
```

Despois:
```python
from horta.models.labor import Labor
from horta.models.lote import Lote, LoteSaida
```

### Paso 8 — `src/horta/models/__init__.py`

Antes:
```python
    "TipoCarne",
```

Despois:
```python
    "TipoCarne",
    "Lote",
    "LoteSaida",
```

### Paso 9 — crear o ficheiro `src/horta/services/lotes.py`

Contido completo:
```python
"""Lotes e saídas do produto (docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md).

Nun lote entran colleitas e producións dos animais do mesmo produto; del sae o produto por
venda, para casa, para transformar, como perda ou para os animais. O que queda calcúlase:
entradas − saídas, na unidade do lote. Avisa (sen bloquear) dos máximos anuais da venda
directa (Decreto 125/2014, anexo II), do tempo de espera e do prazo de seguridade."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.lote import Lote, LoteSaida
from horta.models.producion_animal import ProducionAnimal
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen, persoa_co_papel

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_SAIDA: dict[str, str] = {
    "venda": "Venda",
    "casa": "Para casa",
    "transformacion": "Para transformar",
    "perda": "Perda (podre, roto...)",
    "animais": "Para os animais",
}
# Decreto 125/2014 art. 4 (venda directa) e venda a almacén ou cooperativa (CUE 3: colleita
# comercializada)
CANLES: dict[str, str] = {
    "explotacion": "Na explotación",
    "mercado": "Nun mercado",
    "domicilio": "A domicilio",
    "tenda": "A unha tenda",
    "almacen": "A un almacén ou cooperativa",
}
CANLES_DIRECTAS = ("explotacion", "mercado", "domicilio", "tenda")
# Decreto 125/2014 anexo II: nome, máximo ao ano ao aire libre e en invernadoiro, unidade
CATEGORIAS_VENDA_DIRECTA: dict[str, tuple[str, float, float | None, str]] = {
    "hortalizas": ("Hortalizas", 20000, 40000, "kg"),
    "froitas": ("Froitas", 20000, None, "kg"),
    "amoras": ("Amoras", 5000, 10000, "kg"),
    "kiwi": ("Kiwi", 13000, None, "kg"),
    "legumes": ("Legumes", 10000, 24000, "kg"),
    "patacas": ("Patacas", 20000, None, "kg"),
    "cogomelos": ("Cogomelos", 500, 2500, "kg"),
    "cereais": ("Cereais", 5000, None, "kg"),
    "ovos": ("Ovos", 1000, None, "ducias"),
    "mel": ("Mel", 3000, None, "kg"),
    "pole": ("Pole", 450, None, "kg"),
    "propoleo": ("Propóleo", 30, None, "kg"),
    "xelea": ("Xelea real", 10, None, "kg"),
}
# Produtos dos animais que teñen categoría propia
_CATEGORIA_ANIMAL = {"ovos": "ovos", "mel": "mel"}
# Sistemas de cultivo (catálogo sistema_cultivo) en invernadoiro ou túnel
SISTEMAS_PROTEXIDOS = ("4", "19", "26", "27", "28")
# Unidades que se poden converter: a cal e por canto
_BASE = {"kg": ("kg", 1.0), "t": ("kg", 1000.0), "unidades": ("unidades", 1.0),
         "ducias": ("unidades", 12.0), "litros": ("litros", 1.0), "mazos": ("mazos", 1.0)}
_CON_COMPRADOR = ("tenda", "almacen")


def converter(cantidade: float, de: str, a: str) -> float | None:
    """A cantidade noutra unidade, ou None se non se pode converter (p.ex. kg a unidades)."""
    if de == a:
        return cantidade
    orixe, destino = _BASE.get(de), _BASE.get(a)
    if orixe is None or destino is None or orixe[0] != destino[0]:
        return None
    return cantidade * orixe[1] / destino[1]


def nome_para_codigo(nome: str) -> str:
    """'Pemento de Padrón' -> 'PEMENTO': primeira palabra, sen acentos, ata 10 letras."""
    sen_acentos = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    palabras = "".join(c if c.isalnum() else " " for c in sen_acentos).split()
    return palabras[0].upper()[:10] if palabras else "LOTE"


def propor_codigo(session: Session, horta_id: int, nome: str, data: date) -> str:
    """Primeiro código libre do tipo AAAA-PRODUTO-NNN (p.ex. 2026-PATACA-001)."""
    prefixo = f"{data.year}-{nome_para_codigo(nome)}-"
    existentes = {c for (c,) in session.query(Lote.codigo).filter(
        Lote.horta_id == horta_id, Lote.codigo.like(f"{prefixo}%"))}
    numero = 1
    while f"{prefixo}{numero:03d}" in existentes:
        numero += 1
    return f"{prefixo}{numero:03d}"


def lote_para_entrada(
    session: Session, horta_id: int, codigo: str, produto: str, unidade: str, data: date,
    cultivo_siex_codigo: int | None = None, produto_animal: str | None = None,
    protexido: bool = False,
) -> Lote:
    """O lote onde entra unha colleita ou produción: o que ten ese código, se é o mesmo
    produto, ou un novo. Non garda (commit): faino quen apunta a entrada."""
    codigo = codigo.strip()
    if not codigo:
        raise OperacionNonPermitidaError("O lote non pode quedar baleiro")
    lote = session.query(Lote).filter_by(horta_id=horta_id, codigo=codigo).one_or_none()
    if lote is None:
        lote = Lote(horta_id=horta_id, codigo=codigo, produto=produto, unidade=unidade,
                    data=data, cultivo_siex_codigo=cultivo_siex_codigo,
                    produto_animal=produto_animal, protexido=protexido,
                    categoria_venda_directa=_CATEGORIA_ANIMAL.get(produto_animal or ""))
        session.add(lote)
        session.flush()
        return lote
    mesmo = (lote.produto_animal == produto_animal if produto_animal is not None
             else lote.produto_animal is None and (
                 lote.cultivo_siex_codigo == cultivo_siex_codigo if cultivo_siex_codigo
                 else lote.produto.strip().lower() == produto.strip().lower()))
    if not mesmo:
        raise OperacionNonPermitidaError(
            f"O lote {codigo} xa existe e é doutro produto ({lote.produto})")
    if converter(1, unidade, lote.unidade) is None:
        raise OperacionNonPermitidaError(
            f"O lote {codigo} vai en {lote.unidade}: apunta a cantidade nesa unidade")
    lote.data = min(lote.data, data)
    return lote


def _entradas(session: Session, lote_id: int) -> list[tuple[float, str]]:
    colleitas = session.query(Colleita.cantidade, Colleita.unidade).filter_by(
        lote_id=lote_id, baixa=False)
    producions = session.query(ProducionAnimal.cantidade - func.coalesce(
        ProducionAnimal.retirada, 0), ProducionAnimal.unidade).filter_by(
        lote_id=lote_id, baixa=False)
    return [(float(c), u) for c, u in [*colleitas, *producions]]


def _na_unidade(lote: Lote, cantidades: list[tuple[float, str]]) -> float:
    return sum(converter(c, u, lote.unidade) or 0 for c, u in cantidades)


def entrado(session: Session, lote: Lote) -> float:
    return _na_unidade(lote, _entradas(session, lote.id))


def saido(session: Session, lote: Lote, excepto_saida: int | None = None) -> float:
    consulta = session.query(LoteSaida.cantidade, LoteSaida.unidade).filter_by(
        lote_id=lote.id, baixa=False)
    if excepto_saida is not None:
        consulta = consulta.filter(LoteSaida.id != excepto_saida)
    return _na_unidade(lote, [(float(c), u) for c, u in consulta])


def queda(session: Session, lote: Lote) -> float:
    return entrado(session, lote) - saido(session, lote)


def comprobar_entrada(session: Session, lote_id: int, cantidade_antes: float,
                      cantidade_despois: float, unidade: str) -> None:
    """Unha entrada (colleita ou produción) non pode baixar por debaixo do que xa saíu do
    lote. cantidade_despois = 0 ao dala de baixa."""
    lote = session.get(Lote, lote_id)
    if lote is None:
        return
    baixa = (converter(cantidade_antes, unidade, lote.unidade) or 0) - (
        converter(cantidade_despois, unidade, lote.unidade) or 0)
    if baixa > 0 and entrado(session, lote) - baixa < saido(session, lote) - 1e-9:
        raise OperacionNonPermitidaError(
            f"Do lote {lote.codigo} xa saíron {saido(session, lote):g} {lote.unidade}: "
            "non pode entrar menos ca iso")


def listar_lotes(session: Session, actor: Usuario, horta_id: int) -> list[Lote]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Lote).filter_by(horta_id=horta_id, baixa=False)
                .order_by(Lote.data.desc(), Lote.id.desc()))


def resumo_lotes(session: Session, actor: Usuario, horta_id: int
                 ) -> dict[int, tuple[float, float, float]]:
    """Para cada lote: entrou, saíu e queda, na unidade do lote."""
    resumo = {}
    for lote in listar_lotes(session, actor, horta_id):
        dentro, fora = entrado(session, lote), saido(session, lote)
        resumo[lote.id] = (dentro, fora, dentro - fora)
    return resumo


def actualizar_lote(session: Session, actor: Usuario, lote: Lote,
                    categoria_venda_directa: str | None, protexido: bool) -> Lote:
    """A categoría da venda directa e se é de invernadoiro (para os máximos do anexo II)."""
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_ESCRITURA)
    if categoria_venda_directa not in (None, *CATEGORIAS_VENDA_DIRECTA):
        raise OperacionNonPermitidaError("Categoría da venda directa descoñecida")
    lote.categoria_venda_directa = categoria_venda_directa
    lote.protexido = protexido
    session.commit()
    return lote


@dataclass
class DatosSaida:
    lote_id: int
    data: date
    tipo: str
    cantidade: float
    unidade: str
    persoa_id: int | None
    data_fin: date | None = None
    canle: str | None = None
    lugar: str | None = None
    comprador_id: int | None = None
    albaran_factura: str | None = None
    importe: float | None = None
    horas: float | None = None
    maquina_id: int | None = None
    notas: str | None = None


def _lote(session: Session, lote_id: int) -> Lote:
    lote = session.get(Lote, lote_id)
    if lote is None or lote.baixa:
        raise OperacionNonPermitidaError("Ese lote non existe")
    return lote


def _validar(session: Session, datos: DatosSaida, lote: Lote, hoxe: date,
             excepto_id: int | None) -> None:
    if datos.tipo not in TIPOS_SAIDA:
        raise OperacionNonPermitidaError("Escolle a onde vai: venda, casa...")
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    cantidade = converter(datos.cantidade, datos.unidade, lote.unidade)
    if cantidade is None:
        raise OperacionNonPermitidaError(f"O lote vai en {lote.unidade}")
    fin = datos.data_fin or datos.data
    if fin < datos.data:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if fin > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data < lote.data:
        raise OperacionNonPermitidaError(
            f"O lote empezou o {lote.data:%d/%m/%Y}: a saída non pode ser anterior")
    disponible = entrado(session, lote) - saido(session, lote, excepto_id)
    if cantidade > disponible + 1e-9:
        raise OperacionNonPermitidaError(
            f"Do lote {lote.codigo} só quedan {disponible:g} {lote.unidade}")
    comprobar_quen(session, lote.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, lote.horta_id, datos.maquina_id)
    if datos.tipo != "venda":
        return
    if datos.canle not in CANLES:
        raise OperacionNonPermitidaError("Indica a quen ou onde se vendeu")
    if datos.canle in _CON_COMPRADOR and datos.comprador_id is None:
        raise OperacionNonPermitidaError("Indica a que tenda, almacén ou cooperativa")
    # Decreto 125/2014 art. 7.3
    if datos.canle == "tenda" and lote.categoria_venda_directa == "ovos":
        raise OperacionNonPermitidaError("Os ovos non se poden vender a tendas")
    if datos.importe is not None and datos.importe < 0:
        raise OperacionNonPermitidaError("O prezo non pode ser negativo")
    persoa_co_papel(session, lote.horta_id, datos.comprador_id, "cliente")


def _copiar(saida: LoteSaida, datos: DatosSaida, lote: Lote) -> None:
    venda = datos.tipo == "venda"
    saida.horta_id = lote.horta_id
    saida.lote_id = lote.id
    saida.data = datos.data
    saida.data_fin = datos.data_fin or datos.data
    saida.tipo = datos.tipo
    saida.cantidade = datos.cantidade
    saida.unidade = datos.unidade
    # Cada tipo garda só os seus datos
    saida.canle = datos.canle if venda else None
    saida.lugar = (datos.lugar or None) if venda else None
    saida.comprador_id = datos.comprador_id if venda else None
    saida.albaran_factura = (datos.albaran_factura or None) if venda else None
    saida.importe = datos.importe if venda else None
    saida.persoa_id = datos.persoa_id
    saida.horas = datos.horas
    saida.maquina_id = datos.maquina_id
    saida.notas = datos.notas or None


def crear_saida(session: Session, actor: Usuario, datos: DatosSaida,
                hoxe: date | None = None) -> LoteSaida:
    lote = _lote(session, datos.lote_id)
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, lote, hoxe or date.today(), None)
    saida = LoteSaida(creado_por=actor.id)
    _copiar(saida, datos, lote)
    session.add(saida)
    session.commit()
    return saida


def actualizar_saida(session: Session, actor: Usuario, saida: LoteSaida, datos: DatosSaida,
                     hoxe: date | None = None) -> LoteSaida:
    if saida.baixa:
        raise OperacionNonPermitidaError("Unha saída dada de baixa non se pode modificar")
    comprobar_rol_horta(session, saida.horta_id, actor, _ROLES_ESCRITURA)
    lote = _lote(session, datos.lote_id)
    if lote.horta_id != saida.horta_id:
        raise OperacionNonPermitidaError("Ese lote non é desta explotación")
    _validar(session, datos, lote, hoxe or date.today(), saida.id)
    _copiar(saida, datos, lote)
    session.commit()
    return saida


def dar_de_baixa_saida(session: Session, actor: Usuario, saida: LoteSaida) -> None:
    comprobar_rol_horta(session, saida.horta_id, actor, _ROLES_ESCRITURA)
    saida.baixa = True
    session.commit()


def listar_saidas(session: Session, actor: Usuario, horta_id: int,
                  lote_id: int | None = None) -> list[LoteSaida]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(LoteSaida).filter_by(horta_id=horta_id, baixa=False)
    if lote_id is not None:
        consulta = consulta.filter_by(lote_id=lote_id)
    return list(consulta.order_by(LoteSaida.data.desc(), LoteSaida.id.desc()))


def vendido_no_ano(session: Session, horta_id: int, categoria: str, ano: int,
                   excepto_id: int | None = None) -> float:
    """Venda directa do ano nesa categoría (Decreto 125/2014), na unidade do anexo II."""
    unidade = CATEGORIAS_VENDA_DIRECTA[categoria][3]
    consulta = (session.query(LoteSaida.cantidade, LoteSaida.unidade)
                .join(Lote, Lote.id == LoteSaida.lote_id)
                .filter(LoteSaida.horta_id == horta_id, LoteSaida.baixa.is_(False),
                        LoteSaida.tipo == "venda", LoteSaida.canle.in_(CANLES_DIRECTAS),
                        Lote.categoria_venda_directa == categoria,
                        LoteSaida.data >= date(ano, 1, 1), LoteSaida.data <= date(ano, 12, 31)))
    if excepto_id is not None:
        consulta = consulta.filter(LoteSaida.id != excepto_id)
    return sum(converter(float(c), u, unidade) or 0 for c, u in consulta)


def avisos_saida(session: Session, actor: Usuario, datos: DatosSaida,
                 excepto_id: int | None = None) -> list[str]:
    """Avisos que non bloquean: máximo anual da venda directa, tempo de espera dos animais e
    prazo de seguridade dos tratamentos."""
    from horta.services.fito_consulta import aviso_prazo_colleita
    from horta.services.producions_animais import aviso_tempo_espera

    lote = session.get(Lote, datos.lote_id)
    if lote is None:
        return []
    avisos = []
    categoria = lote.categoria_venda_directa
    if (datos.tipo == "venda" and datos.canle in CANLES_DIRECTAS and categoria
            and datos.cantidade):
        nome, maximo, maximo_protexido, unidade = CATEGORIAS_VENDA_DIRECTA[categoria]
        limite = maximo_protexido if lote.protexido and maximo_protexido else maximo
        total = vendido_no_ano(session, lote.horta_id, categoria, datos.data.year,
                               excepto_id) + (converter(datos.cantidade, datos.unidade,
                                                        unidade) or 0)
        if total > limite:
            avisos.append(
                f"Con esta venda levas {total:g} {unidade} de {nome.lower()} en venda directa "
                f"este ano: o máximo son {limite:g} {unidade} (Decreto 125/2014). Pasado iso "
                "precisas outro rexistro sanitario.")
    for pr in session.query(ProducionAnimal).filter_by(lote_id=lote.id, baixa=False):
        aviso = aviso_tempo_espera(session, actor, lote.horta_id, pr.animal_id, pr.data,
                                   pr.data_fin)
        if aviso:
            avisos.append(aviso)
            break
    for col in session.query(Colleita).filter_by(lote_id=lote.id, baixa=False):
        aviso = aviso_prazo_colleita(session, col.cultivo_id, col.data)
        if aviso:
            avisos.append(aviso)
            break
    return avisos


def ten_saidas(session: Session, lote_id: int) -> bool:
    return session.query(LoteSaida).filter_by(lote_id=lote_id, baixa=False).first() is not None


def cultivo_protexido(cultivo: Cultivo) -> bool:
    return (cultivo.sistema_cultivo or "") in SISTEMAS_PROTEXIDOS
```

### Paso 10 — `src/horta/services/colleitas.py`

Antes:
```python
"""Colleitas dos cultivos (CUE bloque Cosecha), cada unha co seu lote. Baixa lóxica."""

from __future__ import annotations

import unicodedata
```

Despois:
```python
"""Colleitas dos cultivos (CUE bloque Cosecha). Cada colleita entra nun lote (services.lotes),
de onde sae despois a venda. Baixa lóxica."""

from __future__ import annotations

```

### Paso 11 — `src/horta/services/colleitas.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
from horta.services.producions_animais import lotes_da_horta
```

Despois:
```python
from horta.services.lotes import (
    comprobar_entrada,
    cultivo_protexido,
    lote_para_entrada,
    propor_codigo,
)
from horta.services.persoas import comprobar_quen
```

### Paso 12 — `src/horta/services/colleitas.py`

Antes:
```python
    data_fin: date | None = None
    albaran_factura: str | None = None
    cliente_nome: str | None = None
    cliente_nif: str | None = None
    cliente_enderezo: str | None = None
    cliente_reaga: str | None = None
```

Despois:
```python
    data_fin: date | None = None
```

### Paso 13 — `src/horta/services/colleitas.py`

Antes:
```python
def _lotes_da_horta(session: Session, horta_id: int, excepto_id: int | None = None) -> set[str]:
    """Os lotes da explotación, tamén os da produción dos animais."""
    return lotes_da_horta(session, horta_id, excepto_colleita=excepto_id)


def _validar(
    session: Session,
    datos: DatosColleita,
    cultivo: Cultivo,
    horta_id: int,
    hoxe: date,
    excepto_id: int | None = None,
```

Despois:
```python
def _validar(
    session: Session,
    datos: DatosColleita,
    cultivo: Cultivo,
    horta_id: int,
    hoxe: date,
```

### Paso 14 — `src/horta/services/colleitas.py`

Antes:
```python
            raise OperacionNonPermitidaError("A superficie colleitada é maior ca do cultivo")
    lote = datos.lote.strip()
    if not lote:
        raise OperacionNonPermitidaError("O lote non pode quedar baleiro")
    if lote in _lotes_da_horta(session, horta_id, excepto_id):
        raise OperacionNonPermitidaError(f"O lote {lote} xa existe nesta explotación")
```

Despois:
```python
            raise OperacionNonPermitidaError("A superficie colleitada é maior ca do cultivo")
```

### Paso 15 — `src/horta/services/colleitas.py`

Antes:
```python
def _copiar(colleita: Colleita, datos: DatosColleita) -> None:
    colleita.cultivo_id = datos.cultivo_id
    colleita.data = datos.data
    colleita.cantidade = datos.cantidade
    colleita.unidade = datos.unidade
    colleita.lote = datos.lote.strip()
    colleita.superficie_ha = datos.superficie_ha
    colleita.data_fin = datos.data_fin or datos.data
    colleita.albaran_factura = datos.albaran_factura or None
```

Despois:
```python
def _lote(session: Session, datos: DatosColleita, cultivo: Cultivo, horta_id: int) -> int:
    """O lote onde entra: o do código, se é o mesmo cultivo, ou un novo."""
    return lote_para_entrada(
        session, horta_id, datos.lote, cultivo.especie, datos.unidade, datos.data,
        cultivo_siex_codigo=cultivo.cultivo_siex_codigo,
        protexido=cultivo_protexido(cultivo)).id


def _copiar(colleita: Colleita, datos: DatosColleita) -> None:
    colleita.cultivo_id = datos.cultivo_id
    colleita.data = datos.data
    colleita.cantidade = datos.cantidade
    colleita.unidade = datos.unidade
    colleita.superficie_ha = datos.superficie_ha
    colleita.data_fin = datos.data_fin or datos.data
```

### Paso 16 — `src/horta/services/colleitas.py`

Antes:
```python
    colleita.notas = datos.notas or None
    colleita.cliente_nome = datos.cliente_nome or None
    colleita.cliente_nif = datos.cliente_nif or None
    colleita.cliente_enderezo = datos.cliente_enderezo or None
    colleita.cliente_reaga = datos.cliente_reaga or None
```

Despois:
```python
    colleita.notas = datos.notas or None
```

### Paso 17 — `src/horta/services/colleitas.py`

Antes:
```python
    colleita = Colleita(creado_por=actor.id)
```

Despois:
```python
    colleita = Colleita(creado_por=actor.id, lote_id=_lote(session, datos, cultivo, horta_id))
```

### Paso 18 — `src/horta/services/colleitas.py`

Antes:
```python
    _validar(session, datos, cultivo, horta_id, hoxe or date.today(), excepto_id=colleita.id)
    _copiar(colleita, datos)
    session.commit()
    return colleita


def dar_de_baixa_colleita(session: Session, actor: Usuario, colleita: Colleita) -> None:
    _, horta_id = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
```

Despois:
```python
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    lote_id = _lote(session, datos, cultivo, horta_id)
    # O lote de antes non pode quedar con menos do que xa saíu del
    comprobar_entrada(session, colleita.lote_id, colleita.cantidade,
                      datos.cantidade if lote_id == colleita.lote_id else 0, colleita.unidade)
    colleita.lote_id = lote_id
    _copiar(colleita, datos)
    session.commit()
    return colleita


def dar_de_baixa_colleita(session: Session, actor: Usuario, colleita: Colleita) -> None:
    _, horta_id = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    comprobar_entrada(session, colleita.lote_id, colleita.cantidade, 0, colleita.unidade)
```

### Paso 19 — `src/horta/services/colleitas.py`

Antes:
```python
def nome_para_lote(especie: str) -> str:
    """'Pemento de Padrón' -> 'PEMENTO': primeira palabra, sen acentos, ata 10 letras."""
    sen_acentos = unicodedata.normalize("NFKD", especie).encode("ascii", "ignore").decode()
    palabras = "".join(c if c.isalnum() else " " for c in sen_acentos).split()
    return palabras[0].upper()[:10] if palabras else "CULTIVO"


def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
    """Primeiro lote libre do tipo AAAA-CULTIVO-NNN (p.ex. 2026-PATACA-001)."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    nome = nome_para_lote(cultivo.especie)
    existentes = _lotes_da_horta(session, horta_id)
    numero = 1
    while f"{data.year}-{nome}-{numero:03d}" in existentes:
        numero += 1
    return f"{data.year}-{nome}-{numero:03d}"
```

Despois:
```python
def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
    """Primeiro lote libre do tipo AAAA-CULTIVO-NNN (p.ex. 2026-PATACA-001)."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return propor_codigo(session, horta_id, cultivo.especie, data)
```

### Paso 20 — `src/horta/services/producions_animais.py`

Antes:
```python
import unicodedata
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.producion_animal import ProducionAnimal
from horta.models.usuario import Usuario
from horta.services.coidados_animais import fin_tempo_espera, listar_coidados
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.producion_animal import ProducionAnimal
from horta.models.usuario import Usuario
from horta.services.coidados_animais import fin_tempo_espera, listar_coidados
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import comprobar_entrada, lote_para_entrada, propor_codigo
```

### Paso 21 — `src/horta/services/producions_animais.py`

Antes:
```python
def lotes_da_horta(session: Session, horta_id: int, excepto_producion: int | None = None,
                   excepto_colleita: int | None = None) -> set[str]:
    """Os lotes da explotación: os da produción dos animais e os das colleitas."""
    producions = session.query(ProducionAnimal.lote).filter_by(horta_id=horta_id)
    if excepto_producion is not None:
        producions = producions.filter(ProducionAnimal.id != excepto_producion)
    colleitas = (
        session.query(Colleita.lote)
        .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
    )
    if excepto_colleita is not None:
        colleitas = colleitas.filter(Colleita.id != excepto_colleita)
    return {lote for (lote,) in producions} | {lote for (lote,) in colleitas}


def propor_lote(session: Session, actor: Usuario, horta_id: int, produto: str,
                data: date) -> str:
    """Primeiro lote libre do tipo AAAA-PRODUTO-NNN (p.ex. 2026-OVOS-001)."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    nome = unicodedata.normalize("NFKD", PRODUTOS.get(produto, "Outro")).encode(
        "ascii", "ignore").decode().upper()
    existentes = lotes_da_horta(session, horta_id)
    numero = 1
    while f"{data.year}-{nome}-{numero:03d}" in existentes:
        numero += 1
    return f"{data.year}-{nome}-{numero:03d}"
```

Despois:
```python
def propor_lote(session: Session, actor: Usuario, horta_id: int, produto: str,
                data: date) -> str:
    """Primeiro lote libre do tipo AAAA-PRODUTO-NNN (p.ex. 2026-OVOS-001)."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return propor_codigo(session, horta_id, PRODUTOS.get(produto, "Outro"), data)
```

### Paso 22 — `src/horta/services/producions_animais.py`

Antes:
```python
            f"O grupo quedou sen animais o {animal.data_baixa:%d/%m/%Y}")
    lote = datos.lote.strip()
    if not lote:
        raise OperacionNonPermitidaError("O lote non pode quedar baleiro")
    if lote in lotes_da_horta(session, animal.horta_id, excepto_producion=excepto_id):
        raise OperacionNonPermitidaError(f"O lote {lote} xa existe nesta explotación")
```

Despois:
```python
            f"O grupo quedou sen animais o {animal.data_baixa:%d/%m/%Y}")
```

### Paso 23 — `src/horta/services/producions_animais.py`

Antes:
```python
    pr.lote = datos.lote.strip()
    pr.persoa_id = datos.persoa_id
    pr.horas = datos.horas
    pr.maquina_id = datos.maquina_id
    pr.notas = datos.notas or None


def crear_producion(
    session: Session, actor: Usuario, datos: DatosProducion, hoxe: date | None = None
) -> ProducionAnimal:
    animal = _animal(session, datos.animal_id)
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, animal.horta_id, datos.produto, datos.data)
    _validar(session, datos, animal, hoxe or date.today(), None)
    pr = ProducionAnimal(creado_por=actor.id)
```

Despois:
```python
    pr.persoa_id = datos.persoa_id
    pr.horas = datos.horas
    pr.maquina_id = datos.maquina_id
    pr.notas = datos.notas or None


def _lote(session: Session, datos: DatosProducion, animal: Animal) -> int:
    """O lote onde entra (o producido menos o retirado): o do código, se é o mesmo produto,
    ou un novo."""
    return lote_para_entrada(session, animal.horta_id, datos.lote, PRODUTOS[datos.produto],
                             datos.unidade, datos.data, produto_animal=datos.produto).id


def _neto(cantidade: float, retirada: float | None) -> float:
    return cantidade - (retirada or 0)


def crear_producion(
    session: Session, actor: Usuario, datos: DatosProducion, hoxe: date | None = None
) -> ProducionAnimal:
    animal = _animal(session, datos.animal_id)
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, animal.horta_id, datos.produto, datos.data)
    _validar(session, datos, animal, hoxe or date.today(), None)
    pr = ProducionAnimal(creado_por=actor.id, lote_id=_lote(session, datos, animal))
```

### Paso 24 — `src/horta/services/producions_animais.py`

Antes:
```python
    _copiar(pr, datos, animal)
    session.commit()
    return pr


def dar_de_baixa_producion(session: Session, actor: Usuario, pr: ProducionAnimal) -> None:
    comprobar_rol_horta(session, pr.horta_id, actor, _ROLES_ESCRITURA)
```

Despois:
```python
    lote_id = _lote(session, datos, animal)
    # O lote de antes non pode quedar con menos do que xa saíu del
    comprobar_entrada(session, pr.lote_id, _neto(pr.cantidade, pr.retirada),
                      _neto(datos.cantidade, datos.retirada) if lote_id == pr.lote_id else 0,
                      pr.unidade)
    pr.lote_id = lote_id
    _copiar(pr, datos, animal)
    session.commit()
    return pr


def dar_de_baixa_producion(session: Session, actor: Usuario, pr: ProducionAnimal) -> None:
    comprobar_rol_horta(session, pr.horta_id, actor, _ROLES_ESCRITURA)
    comprobar_entrada(session, pr.lote_id, _neto(pr.cantidade, pr.retirada), 0, pr.unidade)
```

### Paso 25 — `src/horta/services/caderno.py`

Antes:
```python
from horta.models.horta import Horta, RolHorta
```

Despois:
```python
from horta.models.horta import Horta, RolHorta
from horta.models.lote import Lote
```

### Paso 26 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.persoas import nome_completo
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import listar_tratamentos_fito
from horta.services.tratamentos_instalacion import listar_tratamentos_instalacion

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_A_KG = {"kg": 1.0, "t": 1000.0}
```

Despois:
```python
from horta.services.lotes import converter, listar_saidas
from horta.services.persoas import nome_completo
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import listar_tratamentos_fito
from horta.services.tratamentos_instalacion import listar_tratamentos_instalacion

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
```

### Paso 27 — `src/horta/services/caderno.py`

Antes:
```python
    filas_colleita = []
    for col in listar_colleitas(session, actor, horta_id):
        if not no_periodo(col.data, col.data_fin):
            continue
        c = cultivo_de(col.cultivo_id)
        kg = col.cantidade * _A_KG[col.unidade] if col.unidade in _A_KG else None
        filas_colleita.append([
            _intervalo(col.data, col.data_fin), c.especie if c else "",
            _num(kg) if kg is not None else f"{col.cantidade:g} {col.unidade}",
            orde_cultivo.get(col.cultivo_id, ""), col.albaran_factura or "", col.lote,
            col.cliente_nome or "", col.cliente_nif or "", col.cliente_enderezo or "",
            col.cliente_reaga or ""])
```

Despois:
```python
    # 5: as vendas dos lotes de colleitas (a colleita comercializada)
    filas_colleita = []
    colleitas = listar_colleitas(session, actor, horta_id)
    for venda in listar_saidas(session, actor, horta_id):
        lote = session.get(Lote, venda.lote_id)
        if (venda.tipo != "venda" or lote is None or lote.produto_animal is not None
                or not no_periodo(venda.data, venda.data_fin)):
            continue
        kg = converter(venda.cantidade, venda.unidade, "kg")
        cliente = persoas_por_id.get(venda.comprador_id or 0)
        filas_colleita.append([
            _intervalo(venda.data, venda.data_fin), lote.produto,
            _num(kg) if kg is not None else f"{venda.cantidade:g} {venda.unidade}",
            ", ".join(str(n) for n in sorted({orde_cultivo[col.cultivo_id] for col in colleitas
                                              if col.lote_id == lote.id
                                              and col.cultivo_id in orde_cultivo})),
            venda.albaran_factura or "", lote.codigo, nome_completo(cliente),
            (cliente.nif or "") if cliente else "", (cliente.enderezo or "") if cliente else "",
            (cliente.reaga or "") if cliente else ""])
```

### Paso 28 — `tests/services/test_colleitas_lote.py`

Antes:
```python
from horta.services.colleitas import nome_para_lote
```

Despois:
```python
from horta.services.lotes import nome_para_codigo
```

### Paso 29 — `tests/services/test_colleitas_lote.py`

Antes:
```python
        ("  ", "CULTIVO"),
    ],
)
def test_nome_para_lote(especie, esperado):
    assert nome_para_lote(especie) == esperado
```

Despois:
```python
        ("  ", "LOTE"),
    ],
)
def test_nome_para_codigo(especie, esperado):
    assert nome_para_codigo(especie) == esperado
```

### Paso 30 — `tests/services/test_caderno.py`

Antes:
```python
from horta.models.colleita import Colleita
from horta.models.rega import Rega
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.models.persoa import Persoa
from horta.models.rega import Rega
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
```

### Paso 31 — `tests/services/test_caderno.py`

Antes:
```python
        Colleita(cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=1.5, unidade="t",
                 lote="2026-PATACA-001"),
        Analise(horta_id=horta.id, material_analizado="3", data_mostraxe=date(2026, 2, 1),
                parcela_id=parcela.id, ph=5.6),
        # fóra do período: non debe saír
        Rega(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2025, 7, 1),
             data_fin=date(2025, 7, 1), superficie_ha=0.2, sistema_rega="6", cantidade=9,
             unidade="3"),
    ])
    session.commit()
```

Despois:
```python
        Analise(horta_id=horta.id, material_analizado="3", data_mostraxe=date(2026, 2, 1),
                parcela_id=parcela.id, ph=5.6),
        # fóra do período: non debe saír
        Rega(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2025, 7, 1),
             data_fin=date(2025, 7, 1), superficie_ha=0.2, sistema_rega="6", cantidade=9,
             unidade="3"),
    ])
    session.commit()
    # A folla 5 (colleita comercializada) sae das vendas dos lotes de colleitas
    quen = session.query(Persoa).filter_by(horta_id=horta.id).first().id
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=1.5, unidade="t",
        lote="2026-PATACA-001", persoa_id=quen), hoxe=date(2026, 10, 28))
    crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2026, 9, 2), tipo="venda", cantidade=1.5,
        unidade="t", canle="almacen", persoa_id=quen,
        comprador_id=crear_contacto(session, ana, horta.id, "Coop", "cliente").id),
        hoxe=date(2026, 10, 28))
```

### Paso 32 — `tests/services/test_caderno_cliente.py`

Antes:
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

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1



def test_cliente_da_colleita_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Pataca")
    crear_colleita(session, ana, DatosColleita(persoa_id=QUEN,
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=200, unidade="kg",
        lote="2026-PATACA-001", albaran_factura="A-7", cliente_nome="Froitas Melide SL",
        cliente_nif="B15000000", cliente_enderezo="Rúa do Mercado 2"), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["5 Colleita"].iter_rows(min_row=5, values_only=True)))
```

Despois:
```python
"""Caderno, folla 5 (colleita comercializada): sae das vendas dos lotes de colleitas, co
cliente da súa ficha (docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md)."""

from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1


def test_cliente_da_venda_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Pataca")
    colleita = crear_colleita(session, ana, DatosColleita(
        persoa_id=QUEN, cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=200,
        unidade="kg", lote="2026-PATACA-001"), hoxe=date(2026, 10, 25))
    cliente = crear_contacto(session, ana, horta.id, "Froitas Melide SL", "cliente",
                             tipo="entidade", nif="B15000000", enderezo="Rúa do Mercado 2")
    crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2026, 9, 3), tipo="venda", cantidade=150,
        unidade="kg", canle="almacen", comprador_id=cliente.id, albaran_factura="A-7",
        persoa_id=QUEN), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["5 Colleita"].iter_rows(min_row=5, values_only=True)))
    assert fila[2] == 150
```

### Paso 33 — `tests/services/test_colleitas.py`

Antes:
```python
def test_lote_repetido_rexeitase(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
```

Despois:
```python
def test_o_mesmo_lote_recolle_varias_colleitas_do_mesmo_cultivo(session):
    ana, horta, cultivo = _escenario(session)
    primeira = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    segunda = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert primeira.lote_id == segunda.lote_id
    outro = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Outra").id,
                          "Cebola")
    with pytest.raises(OperacionNonPermitidaError, match="doutro produto"):
        crear_colleita(session, ana, _datos(outro), hoxe=HOXE)
```

### Paso 34 — `tests/services/test_producions_animais.py`

Antes:
```python
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_producion(session, ana, _ovos(galinas, persoa, lote="2026-OVOS-001"), hoxe=HOXE)
```

Despois:
```python
    # Co mesmo código, os ovos doutro día súmanse ao mesmo lote
    outra = crear_producion(session, ana, _ovos(galinas, persoa, lote="2026-OVOS-001"),
                            hoxe=HOXE)
    assert outra.lote == "2026-OVOS-001"
```

### Paso 35 — `tests/test_migracion_tratamento_fito.py`

Antes:
```python
            "SELECT cultivo_id, data, cantidade, unidade, lote FROM colleita"
```

Despois:
```python
            "SELECT c.cultivo_id, c.data, c.cantidade, c.unidade, l.codigo FROM colleita c "
            "JOIN lote l ON l.id = c.lote_id"
```

### Paso 36 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        lote = ui.input("Lote").classes("w-full")
        albaran = ui.input("Nº de albarán ou factura (opcional)").classes("w-full")
```

Despois:
```python
        lote = ui.input("Lote (un que xa exista do mesmo cultivo súmase a el)").classes("w-full")
```

### Paso 37 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        restos_solo = ui.checkbox("Os restos quedan no chan")
        with ui.expansion("Cliente (se se vende a unha empresa)").classes("w-full"):
            cliente_nome = ui.input("Nome ou razón social").classes("w-full")
            cliente_nif = ui.input("NIF").classes("w-full")
            cliente_enderezo = ui.input("Enderezo").classes("w-full")
            cliente_reaga = ui.input("Nº REAGA (se é unha explotación)").classes("w-full")
```

Despois:
```python
        restos_solo = ui.checkbox("Os restos quedan no chan")
```

### Paso 38 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
                        data_fin=parsear_data(data_fin.value),
                        albaran_factura=albaran.value or None,
                        cliente_nome=cliente_nome.value or None,
                        cliente_nif=cliente_nif.value or None,
                        cliente_enderezo=cliente_enderezo.value or None,
                        cliente_reaga=cliente_reaga.value or None,
```

Despois:
```python
                        data_fin=parsear_data(data_fin.value),
```

### Paso 39 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        data_fin.value = c.data_fin.isoformat() if c and c.data_fin else ""
        albaran.value = (c.albaran_factura or "") if c else ""
        cliente_nome.value = (c.cliente_nome or "") if c else ""
        cliente_nif.value = (c.cliente_nif or "") if c else ""
        cliente_enderezo.value = (c.cliente_enderezo or "") if c else ""
        cliente_reaga.value = (c.cliente_reaga or "") if c else ""
```

Despois:
```python
        data_fin.value = c.data_fin.isoformat() if c and c.data_fin else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Lotes (1/5): o lote como ficha: feito.

"""lotes: ficha do produto que sae, clases, clasificación e mestura de lotes

Revision ID: d3b5f7a9c1e2
Revises: c2a4e6b8d0f1
Create Date: 2026-10-29 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3b5f7a9c1e2'
down_revision: Union[str, Sequence[str], None] = 'c2a4e6b8d0f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _parte_comun() -> list[sa.Column]:
    return [
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True, unique=True),
        sa.Column("creado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("tempo_id", sa.Integer(), sa.ForeignKey("tempo_dia.id"), nullable=True),
        sa.Column("persoa_id", sa.Integer(), sa.ForeignKey("persoa.id"), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("maquina_id", sa.Integer(), sa.ForeignKey("maquina.id"), nullable=True),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "produto_venda",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("horta_id", sa.Integer(), sa.ForeignKey("horta.id"), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("cultivo_siex_codigo", sa.Integer(), nullable=True),
        sa.Column("produto_animal", sa.String(length=20), nullable=True),
        sa.Column("categoria_venda_directa", sa.String(length=20), nullable=True),
        sa.Column("clases", sa.String(length=500), nullable=True),
        sa.Column("agrupacion", sa.String(length=10), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
    )
    op.create_index(op.f("ix_produto_venda_horta_id"), "produto_venda", ["horta_id"])
    with op.batch_alter_table("lote") as batch:
        batch.add_column(sa.Column("produto_venda_id", sa.Integer(), nullable=True))

    # Unha ficha por produto: o mesmo cultivo oficial, o mesmo produto animal ou o mesmo nome
    conexion = op.get_bind()
    fichas: dict[tuple[object, ...], int] = {}
    lotes = conexion.execute(sa.text(
        "SELECT id, horta_id, produto, unidade, cultivo_siex_codigo, produto_animal, "
        "categoria_venda_directa FROM lote ORDER BY id")).fetchall()
    for id_, horta, produto, unidade, cultivo, animal, categoria in lotes:
        clave = (horta, "c", cultivo) if cultivo else (horta, "a", animal) if animal \
            else (horta, "n", produto.strip().lower())
        if clave not in fichas:
            fichas[clave] = conexion.execute(sa.text(
                "INSERT INTO produto_venda (horta_id, nome, unidade, cultivo_siex_codigo, "
                "produto_animal, categoria_venda_directa, agrupacion, activo) VALUES "
                "(:h, :n, :u, :c, :a, :cat, 'colleita', 1)"),
                {"h": horta, "n": produto, "u": unidade, "c": cultivo, "a": animal,
                 "cat": categoria}).lastrowid
        elif categoria:
            conexion.execute(sa.text(
                "UPDATE produto_venda SET categoria_venda_directa = :cat WHERE id = :id "
                "AND categoria_venda_directa IS NULL"), {"cat": categoria, "id": fichas[clave]})
        conexion.execute(sa.text("UPDATE lote SET produto_venda_id = :p WHERE id = :id"),
                         {"p": fichas[clave], "id": id_})

    with op.batch_alter_table("lote") as batch:
        batch.alter_column("produto_venda_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key("fk_lote_produto_venda", "produto_venda",
                                 ["produto_venda_id"], ["id"])
        batch.create_index(batch.f("ix_lote_produto_venda_id"), ["produto_venda_id"])
        batch.drop_column("categoria_venda_directa")
    with op.batch_alter_table("lote_saida") as batch:
        batch.add_column(sa.Column("clase", sa.String(length=60), nullable=True))

    op.create_table(
        "clasificacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("horta_id", sa.Integer(), sa.ForeignKey("horta.id"), nullable=False),
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("lote.id"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("refugo", sa.Float(), nullable=False),
        *_parte_comun(),
    )
    op.create_index(op.f("ix_clasificacion_horta_id"), "clasificacion", ["horta_id"])
    op.create_index(op.f("ix_clasificacion_lote_id"), "clasificacion", ["lote_id"])
    op.create_table(
        "clasificacion_clase",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clasificacion_id", sa.Integer(), sa.ForeignKey("clasificacion.id"),
                  nullable=False),
        sa.Column("clase", sa.String(length=60), nullable=False),
        sa.Column("cantidade", sa.Float(), nullable=False),
    )
    op.create_index(op.f("ix_clasificacion_clase_clasificacion_id"), "clasificacion_clase",
                    ["clasificacion_id"])
    op.create_table(
        "mestura",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("horta_id", sa.Integer(), sa.ForeignKey("horta.id"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("lote.id"), nullable=False),
        *_parte_comun(),
    )
    op.create_index(op.f("ix_mestura_horta_id"), "mestura", ["horta_id"])
    op.create_index(op.f("ix_mestura_lote_id"), "mestura", ["lote_id"])
    op.create_table(
        "mestura_orixe",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mestura_id", sa.Integer(), sa.ForeignKey("mestura.id"), nullable=False),
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("lote.id"), nullable=False),
        sa.Column("clase", sa.String(length=60), nullable=True),
        sa.Column("cantidade", sa.Float(), nullable=False),
    )
    op.create_index(op.f("ix_mestura_orixe_mestura_id"), "mestura_orixe", ["mestura_id"])
    op.create_index(op.f("ix_mestura_orixe_lote_id"), "mestura_orixe", ["lote_id"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in ("mestura_orixe", "mestura", "clasificacion_clase", "clasificacion"):
        op.drop_table(taboa)
    with op.batch_alter_table("lote_saida") as batch:
        batch.drop_column("clase")
    with op.batch_alter_table("lote") as batch:
        batch.add_column(sa.Column("categoria_venda_directa", sa.String(length=20),
                                   nullable=True))
    op.execute("UPDATE lote SET categoria_venda_directa = (SELECT categoria_venda_directa "
               "FROM produto_venda WHERE produto_venda.id = lote.produto_venda_id)")
    with op.batch_alter_table("lote") as batch:
        batch.drop_index(batch.f("ix_lote_produto_venda_id"))
        batch.drop_constraint("fk_lote_produto_venda", type_="foreignkey")
        batch.drop_column("produto_venda_id")
    op.drop_index(op.f("ix_produto_venda_horta_id"), table_name="produto_venda")
    op.drop_table("produto_venda")

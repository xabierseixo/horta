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

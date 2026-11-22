"""produtos e entradas: os insumos da explotación e as súas compras; os usos apuntan a eles

Revision ID: b4e6a8c0d2f9
Revises: a3d5f7b9c1e8
Create Date: 2026-10-29 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e6a8c0d2f9'
down_revision: Union[str, Sequence[str], None] = 'a3d5f7b9c1e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Unidades do catálogo oficial → unidade das existencias do produto
_UNIDADE = {"4": "litros", "18": "litros", "5": "kg", "6": "kg", "17": "kg", "29": "kg",
            "11": "unidades"}


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "produto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=250), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("num_rexistro", sa.String(length=20), nullable=True),
        sa.Column("fertilizante_id", sa.Integer(), nullable=True),
        sa.Column("tipo_enerxia", sa.String(length=20), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["fertilizante_id"], ["fertilizante.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fertilizante_id"),
    )
    op.create_index(op.f("ix_produto_horta_id"), "produto", ["horta_id"])
    op.create_table(
        "entrada_produto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("provedor_id", sa.Integer(), nullable=True),
        sa.Column("cantidade", sa.Float(), nullable=True),
        sa.Column("unidade", sa.String(length=20), nullable=True),
        sa.Column("lote_provedor", sa.String(length=50), nullable=True),
        sa.Column("albaran_factura", sa.String(length=60), nullable=True),
        sa.Column("importe", sa.Float(), nullable=True),
        sa.Column("data_caducidade", sa.Date(), nullable=True),
        sa.Column("pasaporte_fitosanitario", sa.String(length=40), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produto.id"]),
        sa.ForeignKeyConstraint(["provedor_id"], ["persoa.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_entrada_produto_horta_id"), "entrada_produto", ["horta_id"])
    op.create_index(op.f("ix_entrada_produto_produto_id"), "entrada_produto", ["produto_id"])
    for taboa, columnas in (("abonado", ("entrada_id",)),
                            ("tratamento_produto", ("produto_id", "entrada_id")),
                            ("coidado_animal", ("produto_id", "entrada_id")),
                            ("cultivo", ("entrada_semente_id",))):
        with op.batch_alter_table(taboa) as batch:
            for columna in columnas:
                destino = "produto" if columna == "produto_id" else "entrada_produto"
                batch.add_column(sa.Column(columna, sa.Integer(), nullable=True))
                batch.create_foreign_key(f"fk_{taboa}_{columna}", destino, [columna], ["id"])
    conn = op.get_bind()

    def produto(horta_id, tipo, nome, unidade, **datos) -> int:
        return conn.execute(sa.text(
            "INSERT INTO produto (horta_id, tipo, nome, unidade, num_rexistro, fertilizante_id, "
            "activo, created_at) VALUES (:h, :t, :n, :u, :r, :f, 1, CURRENT_TIMESTAMP)"),
            {"h": horta_id, "t": tipo, "n": (nome or "Sen nome")[:250], "u": unidade,
             "r": datos.get("num_rexistro"), "f": datos.get("fertilizante_id")}).lastrowid

    def entrada(horta_id, produto_id, data, **datos) -> int:
        return conn.execute(sa.text(
            "INSERT INTO entrada_produto (horta_id, produto_id, data, provedor_id, "
            "lote_provedor, albaran_factura, pasaporte_fitosanitario, baixa, created_at) "
            "VALUES (:h, :p, :d, :prov, :lote, :alb, :pas, 0, CURRENT_TIMESTAMP)"),
            {"h": horta_id, "p": produto_id, "d": data, "prov": datos.get("provedor_id"),
             "lote": datos.get("lote"), "alb": datos.get("albaran"),
             "pas": datos.get("pasaporte")}).lastrowid

    # Abonos: cada fertilizante é un produto; o seu provedor e os albarás, entradas
    for fe in conn.execute(sa.text(
            "SELECT id, horta_id, nome, liquido, provedor_id, created_at FROM fertilizante")
            ).mappings().all():
        produto_id = produto(fe["horta_id"], "abono", fe["nome"],
                             "litros" if fe["liquido"] else "kg",
                             fertilizante_id=fe["id"])
        entradas: dict[str | None, int] = {}
        for ab in conn.execute(sa.text(
                "SELECT id, data_inicio, albaran_factura FROM abonado WHERE fertilizante_id = :f "
                "ORDER BY data_inicio"), {"f": fe["id"]}).mappings().all():
            albaran = ab["albaran_factura"]
            if albaran is None and fe["provedor_id"] is None:
                continue
            if albaran not in entradas:
                entradas[albaran] = entrada(fe["horta_id"], produto_id, ab["data_inicio"],
                                            provedor_id=fe["provedor_id"], albaran=albaran)
            conn.execute(sa.text("UPDATE abonado SET entrada_id = :e WHERE id = :i"),
                         {"e": entradas[albaran], "i": ab["id"]})
        if fe["provedor_id"] is not None and not entradas:
            entrada(fe["horta_id"], produto_id, str(fe["created_at"])[:10],
                    provedor_id=fe["provedor_id"])
    # Fitosanitarios dos tratamentos: un produto por nº de rexistro (ou nome)
    fitos: dict[tuple[int, str], int] = {}
    for tp in conn.execute(sa.text(
            "SELECT tp.id, t.horta_id, tp.num_rexistro, tp.nome_comercial, tp.unidade "
            "FROM tratamento_produto tp JOIN tratamento_fito t ON t.id = tp.tratamento_id")
            ).mappings().all():
        chave = (tp["horta_id"], (tp["num_rexistro"] or tp["nome_comercial"] or "").strip())
        if not chave[1]:
            continue
        if chave not in fitos:
            fitos[chave] = produto(tp["horta_id"], "fitosanitario",
                                   tp["nome_comercial"] or tp["num_rexistro"],
                                   _UNIDADE.get(tp["unidade"] or "", "litros"),
                                   num_rexistro=tp["num_rexistro"])
        conn.execute(sa.text("UPDATE tratamento_produto SET produto_id = :p WHERE id = :i"),
                     {"p": fitos[chave], "i": tp["id"]})
    # Medicamentos dos coidados: un produto por nome; o provedor e a proba de compra, entrada
    medicamentos: dict[tuple[int, str], int] = {}
    for co in conn.execute(sa.text(
            "SELECT id, horta_id, data_inicio, medicamento, unidade, provedor_id, proba_compra "
            "FROM coidado_animal WHERE medicamento IS NOT NULL AND medicamento != ''")
            ).mappings().all():
        chave = (co["horta_id"], co["medicamento"].strip().lower())
        if chave not in medicamentos:
            medicamentos[chave] = produto(co["horta_id"], "medicamento", co["medicamento"].strip(),
                                          _UNIDADE.get(co["unidade"] or "", "unidades"))
        entrada_id = None
        if co["provedor_id"] is not None or co["proba_compra"]:
            entrada_id = entrada(co["horta_id"], medicamentos[chave], co["data_inicio"],
                                 provedor_id=co["provedor_id"], albaran=co["proba_compra"])
        conn.execute(sa.text(
            "UPDATE coidado_animal SET produto_id = :p, entrada_id = :e WHERE id = :i"),
            {"p": medicamentos[chave], "e": entrada_id, "i": co["id"]})
    # Sementes e plantas dos cultivos: a compra pasa a unha entrada
    for cu in conn.execute(sa.text(
            "SELECT c.id, p.horta_id, c.especie, c.data_inicio, c.provedor_material_id, "
            "c.lote_material, c.pasaporte_fitosanitario, c.material_adquirido, "
            "c.data_adquisicion_material, c.tipo_inicio, c.created_at FROM cultivo c "
            "JOIN parcela p ON p.id = c.parcela_id")).mappings().all():
        if not (cu["provedor_material_id"] or cu["lote_material"] or cu["pasaporte_fitosanitario"]
                or cu["material_adquirido"]):
            continue
        que = "Planta" if cu["tipo_inicio"] == "plantacion" else "Semente"
        produto_id = produto(cu["horta_id"], "semente", f"{que} de {cu['especie']}",
                             "unidades" if que == "Planta" else "kg")
        data = (cu["data_adquisicion_material"] or cu["data_inicio"]
                or str(cu["created_at"])[:10])
        entrada_id = entrada(cu["horta_id"], produto_id, data,
                             provedor_id=cu["provedor_material_id"], lote=cu["lote_material"],
                             pasaporte=cu["pasaporte_fitosanitario"])
        conn.execute(sa.text("UPDATE cultivo SET entrada_semente_id = :e WHERE id = :i"),
                     {"e": entrada_id, "i": cu["id"]})
    with op.batch_alter_table("fertilizante") as batch:
        batch.drop_constraint("fk_fertilizante_provedor_id", type_="foreignkey")
        batch.drop_column("provedor_id")
    with op.batch_alter_table("abonado") as batch:
        batch.drop_column("albaran_factura")
    with op.batch_alter_table("coidado_animal") as batch:
        batch.drop_constraint("fk_coidado_animal_provedor_id", type_="foreignkey")
        batch.drop_column("provedor_id")
        batch.drop_column("medicamento")
        batch.drop_column("proba_compra")
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_constraint("fk_cultivo_provedor_material_id", type_="foreignkey")
        for columna in ("provedor_material_id", "lote_material", "pasaporte_fitosanitario",
                        "material_adquirido", "data_adquisicion_material"):
            batch.drop_column(columna)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("provedor_material_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_cultivo_provedor_material_id", "persoa",
                                 ["provedor_material_id"], ["id"])
        batch.add_column(sa.Column("lote_material", sa.String(40), nullable=True))
        batch.add_column(sa.Column("pasaporte_fitosanitario", sa.String(40), nullable=True))
        batch.add_column(sa.Column("material_adquirido", sa.Boolean(), nullable=False,
                                   server_default=sa.false()))
        batch.add_column(sa.Column("data_adquisicion_material", sa.Date(), nullable=True))
    with op.batch_alter_table("coidado_animal") as batch:
        batch.add_column(sa.Column("medicamento", sa.String(250), nullable=True))
        batch.add_column(sa.Column("provedor_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_coidado_animal_provedor_id", "persoa", ["provedor_id"],
                                 ["id"])
        batch.add_column(sa.Column("proba_compra", sa.String(100), nullable=True))
    with op.batch_alter_table("abonado") as batch:
        batch.add_column(sa.Column("albaran_factura", sa.String(50), nullable=True))
    with op.batch_alter_table("fertilizante") as batch:
        batch.add_column(sa.Column("provedor_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_fertilizante_provedor_id", "persoa", ["provedor_id"],
                                 ["id"])
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE cultivo SET (provedor_material_id, lote_material, pasaporte_fitosanitario, "
        "data_adquisicion_material, material_adquirido) = (SELECT provedor_id, lote_provedor, "
        "pasaporte_fitosanitario, data, 1 FROM entrada_produto e "
        "WHERE e.id = cultivo.entrada_semente_id) WHERE entrada_semente_id IS NOT NULL"))
    conn.execute(sa.text(
        "UPDATE coidado_animal SET medicamento = (SELECT nome FROM produto "
        "WHERE produto.id = coidado_animal.produto_id)"))
    conn.execute(sa.text(
        "UPDATE coidado_animal SET (provedor_id, proba_compra) = (SELECT provedor_id, "
        "albaran_factura FROM entrada_produto e WHERE e.id = coidado_animal.entrada_id) "
        "WHERE entrada_id IS NOT NULL"))
    conn.execute(sa.text(
        "UPDATE abonado SET albaran_factura = (SELECT albaran_factura FROM entrada_produto e "
        "WHERE e.id = abonado.entrada_id) WHERE entrada_id IS NOT NULL"))
    conn.execute(sa.text(
        "UPDATE fertilizante SET provedor_id = (SELECT e.provedor_id FROM entrada_produto e "
        "JOIN produto p ON p.id = e.produto_id WHERE p.fertilizante_id = fertilizante.id "
        "AND e.provedor_id IS NOT NULL ORDER BY e.data LIMIT 1)"))
    for taboa, columnas in (("abonado", ("entrada_id",)),
                            ("tratamento_produto", ("produto_id", "entrada_id")),
                            ("coidado_animal", ("produto_id", "entrada_id")),
                            ("cultivo", ("entrada_semente_id",))):
        with op.batch_alter_table(taboa) as batch:
            for columna in columnas:
                batch.drop_constraint(f"fk_{taboa}_{columna}", type_="foreignkey")
                batch.drop_column(columna)
    op.drop_index(op.f("ix_entrada_produto_produto_id"), table_name="entrada_produto")
    op.drop_index(op.f("ix_entrada_produto_horta_id"), table_name="entrada_produto")
    op.drop_table("entrada_produto")
    op.drop_index(op.f("ix_produto_horta_id"), table_name="produto")
    op.drop_table("produto")

"""abonos: o provedor é unha persoa; a empresa de servizos do abonado é quen o fixo

Revision ID: a7d9f1b3c5e0
Revises: f6c8e0a2b4d9
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, persoa_para, primeiro


# revision identifiers, used by Alembic.
revision: str = 'a7d9f1b3c5e0'
down_revision: Union[str, Sequence[str], None] = 'f6c8e0a2b4d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("fertilizante") as batch:
        batch.add_column(sa.Column("provedor_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_fertilizante_provedor_id", "persoa", ["provedor_id"], ["id"])
    conn = op.get_bind()
    pasar_a_persoas(
        conn, "fertilizante", "provedor_id", "provedor",
        "SELECT id, horta_id, provedor_nome, provedor_nif, provedor_rega, provedor_nima "
        "FROM fertilizante",
        nome=lambda f: primeiro(f["provedor_nome"], f["provedor_nif"], f["provedor_rega"],
                                f["provedor_nima"]),
        datos=lambda f: {"nif": f["provedor_nif"], "rega": f["provedor_rega"],
                         "nima": f["provedor_nima"]})
    # A empresa de servizos que fixo o abonado é quen o fixo; se xa había unha persoa,
    # a empresa vai ás notas para non perder o dato
    for f in conn.execute(sa.text(
            "SELECT id, horta_id, persoa_id, notas, empresa_servizos_regfer FROM abonado "
            "WHERE empresa_servizos_regfer IS NOT NULL AND empresa_servizos_regfer != ''")
            ).mappings().all():
        regfer = f["empresa_servizos_regfer"].strip()
        if f["persoa_id"] is None:
            empresa = persoa_para(conn, f["horta_id"], "servizos",
                                  f"Empresa de servizos (REGFER {regfer})", tipo="entidade",
                                  regfer_numero=regfer)
            conn.execute(sa.text("UPDATE abonado SET persoa_id = :p WHERE id = :i"),
                         {"p": empresa, "i": f["id"]})
        else:
            notas = " · ".join(x for x in (f["notas"], f"Empresa de servizos: REGFER {regfer}")
                               if x)
            conn.execute(sa.text("UPDATE abonado SET notas = :n WHERE id = :i"),
                         {"n": notas[:1000], "i": f["id"]})
    with op.batch_alter_table("fertilizante") as batch:
        for columna in ("provedor_nome", "provedor_nif", "provedor_rega", "provedor_nima"):
            batch.drop_column(columna)
    with op.batch_alter_table("abonado") as batch:
        batch.drop_column("empresa_servizos_regfer")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("abonado") as batch:
        batch.add_column(sa.Column("empresa_servizos_regfer", sa.String(50), nullable=True))
    with op.batch_alter_table("fertilizante") as batch:
        batch.add_column(sa.Column("provedor_nome", sa.String(150), nullable=True))
        batch.add_column(sa.Column("provedor_nif", sa.String(14), nullable=True))
        batch.add_column(sa.Column("provedor_rega", sa.String(14), nullable=True))
        batch.add_column(sa.Column("provedor_nima", sa.String(50), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE fertilizante SET (provedor_nome, provedor_nif, provedor_rega, provedor_nima) = "
        "(SELECT nome, nif, rega, nima FROM persoa WHERE persoa.id = fertilizante.provedor_id)"))
    conn.execute(sa.text(
        "UPDATE abonado SET empresa_servizos_regfer = (SELECT regfer_numero FROM persoa p "
        "JOIN persoa_papel pp ON pp.persoa_id = p.id WHERE p.id = abonado.persoa_id "
        "AND pp.papel = 'servizos')"))
    with op.batch_alter_table("fertilizante") as batch:
        batch.drop_constraint("fk_fertilizante_provedor_id", type_="foreignkey")
        batch.drop_column("provedor_id")

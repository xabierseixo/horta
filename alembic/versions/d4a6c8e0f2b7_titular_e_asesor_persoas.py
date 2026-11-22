"""o titular e a entidade de asesoramento da explotación pasan a ser persoas con ese papel

Revision ID: d4a6c8e0f2b7
Revises: c3f5a7b9d1e6
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import persoa_para


# revision identifiers, used by Alembic.
revision: str = 'd4a6c8e0f2b7'
down_revision: Union[str, Sequence[str], None] = 'c3f5a7b9d1e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNAS = (("titular_nome", sa.String(200)), ("titular_nif", sa.String(9)),
             ("asesoramento_nome", sa.String(200)), ("asesoramento_nif", sa.String(14)),
             ("asesoramento_num", sa.String(50)))


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for h in conn.execute(sa.text(
            "SELECT id, titular_nome, titular_nif, asesoramento_nome, asesoramento_nif, "
            "asesoramento_num FROM horta")).mappings().all():
        if h["titular_nome"] or h["titular_nif"]:
            titular = conn.execute(sa.text(
                "SELECT p.id, p.nif FROM persoa p JOIN persoa_papel pp ON pp.persoa_id = p.id "
                "WHERE p.horta_id = :h AND pp.papel = 'titular' AND p.activa"),
                {"h": h["id"]}).first()
            if titular is None:
                persoa_para(conn, h["id"], "titular", h["titular_nome"] or "Titular",
                            nif=h["titular_nif"])
            elif not titular.nif and h["titular_nif"]:
                conn.execute(sa.text("UPDATE persoa SET nif = :n WHERE id = :i"),
                             {"n": h["titular_nif"], "i": titular.id})
        if h["asesoramento_nome"] or h["asesoramento_nif"] or h["asesoramento_num"]:
            persoa_para(conn, h["id"], "asesor", h["asesoramento_nome"] or "Asesoramento",
                        nif=h["asesoramento_nif"], tipo="entidade",
                        num_asesoramento=h["asesoramento_num"])
    with op.batch_alter_table("horta") as batch:
        for columna, _ in _COLUMNAS:
            batch.drop_column(columna)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("horta") as batch:
        for columna, tipo in _COLUMNAS:
            batch.add_column(sa.Column(columna, tipo, nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE horta SET (titular_nome, titular_nif) = (SELECT p.nome, p.nif FROM persoa p "
        "JOIN persoa_papel pp ON pp.persoa_id = p.id WHERE p.horta_id = horta.id "
        "AND pp.papel = 'titular' LIMIT 1)"))
    conn.execute(sa.text(
        "UPDATE horta SET (asesoramento_nome, asesoramento_nif, asesoramento_num) = "
        "(SELECT p.nome, p.nif, p.num_asesoramento FROM persoa p JOIN persoa_papel pp "
        "ON pp.persoa_id = p.id WHERE p.horta_id = horta.id AND pp.papel = 'asesor' "
        "AND p.tipo = 'entidade' LIMIT 1)"))

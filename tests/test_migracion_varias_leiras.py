"""Cada labor, rega e abonado de antes pasa a ter a súa leira nunha táboa filla
."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]


def _alembic(url: str, *args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=RAIZ,
                   env={**os.environ, "HORTA_DATABASE_URL": url}, check=True,
                   capture_output=True)


def test_o_cultivo_pasa_a_leira(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "f2c4e6a8b0d5")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, producion_integrada, "
            "sementeira_directa, material_tratado, material_adquirido, "
            "plan_ferramenta_sostibilidade, created_at) "
            "VALUES (1, 1, 'Millo', 0, 0, 0, 0, 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO labor (id, horta_id, cultivo_id, data_inicio, data_fin, superficie_ha, "
            "tipo_labor, restos_desbroce_no_solo, restos_poda_no_solo, baixa, created_at) "
            "VALUES (1, 1, 1, '2026-04-01', '2026-04-01', 0.5, '5', 0, 0, 0, '2026-04-01')"))
        conn.execute(text(
            "INSERT INTO rega (id, horta_id, cultivo_id, data_inicio, data_fin, superficie_ha, "
            "unidade, baixa, created_at) "
            "VALUES (1, 1, 1, '2026-06-01', '2026-06-01', 0.4, '3', 0, '2026-06-01')"))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        labores = conn.execute(text(
            "SELECT labor_id, cultivo_id, superficie_ha FROM labor_cultivo")).all()
        regas = conn.execute(text(
            "SELECT rega_id, cultivo_id, superficie_ha FROM rega_cultivo")).all()
    assert [tuple(f) for f in labores] == [(1, 1, 0.5)]
    assert [tuple(f) for f in regas] == [(1, 1, 0.4)]
    _alembic(url, "downgrade", "f2c4e6a8b0d5")
    with engine.connect() as conn:
        labor = conn.execute(text("SELECT cultivo_id, superficie_ha FROM labor")).one()
    assert tuple(labor) == (1, 0.5)

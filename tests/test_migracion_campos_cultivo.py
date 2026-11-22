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


def test_as_datas_vellas_pasan_aos_campos_novos(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "d6f8b0c2e4a7")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        for fila in ("(1, 'Pataca', '2026-03-01', NULL, '2026-08-01', NULL, NULL)",
                     "(2, 'Leituga', NULL, '2026-04-01', NULL, NULL, NULL)",
                     "(3, 'Tomate', '2026-03-01', NULL, NULL, '2026-05-01', 'plantacion')"):
            conn.execute(text(
                "INSERT INTO cultivo (id, especie, data_sementeira, data_plantacion, "
                "data_colleita_real, data_inicio, tipo_inicio, parcela_id, estado, "
                "material_tratado, material_adquirido, sementeira_directa, "
                "producion_integrada, created_at) VALUES " + fila[:-1]
                + ", 1, 'planificado', 0, 0, 0, 0, '2026-01-01')"))
    _alembic(url, "upgrade", "b1d3f5a7c9e2")
    with engine.connect() as conn:
        filas = conn.execute(text("SELECT id, tipo_inicio, data_inicio, data_fin FROM cultivo "
                                  "ORDER BY id")).all()
    assert filas == [(1, "sementeira", "2026-03-01", "2026-08-01"),
                     (2, "plantacion", "2026-04-01", None),
                     (3, "plantacion", "2026-05-01", None)]  # os datos novos mandan

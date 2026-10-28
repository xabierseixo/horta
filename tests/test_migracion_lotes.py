"""Os lotes de texto pasan a fichas de lote, e o cliente da colleita a unha venda
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


def test_lotes_e_cliente_da_colleita(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "e1b3d5f7a9c4")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, cultivo_siex_codigo, "
            "sistema_cultivo, producion_integrada, certificacion_ecoloxica, sementeira_directa, "
            "material_tratado, material_adquirido, plan_ferramenta_sostibilidade, created_at) "
            "VALUES (1, 1, 'Tomate', 37, '4', 0, NULL, 0, 0, 0, 0, '2026-01-01')"))
        for fila in ("(1, 1, '2026-08-01', 20, 'kg', 'L-1', NULL, NULL)",
                     "(2, 1, '2026-08-08', 30, 'kg', 'L-2', 'Froitas Melide SL', 'A-7')"):
            conn.execute(text(
                "INSERT INTO colleita (id, cultivo_id, data, cantidade, unidade, lote, "
                "cliente_nome, albaran_factura, obten_sementes, obten_plantas, "
                "sen_colleita_ambiental, restos_no_solo, baixa, created_at) VALUES "
                f"{fila[:-1]}, 0, 0, 0, 0, 0, '2026-01-01')"))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        lotes = conn.execute(text(
            "SELECT codigo, produto, cultivo_siex_codigo, unidade, protexido FROM lote "
            "ORDER BY codigo")).all()
        venda = conn.execute(text(
            "SELECT s.tipo, s.cantidade, s.canle, s.albaran_factura, p.nome FROM lote_saida s "
            "JOIN persoa p ON p.id = s.comprador_id")).one()
    assert [tuple(f) for f in lotes] == [("L-1", "Tomate", 37, "kg", 1),
                                         ("L-2", "Tomate", 37, "kg", 1)]
    assert tuple(venda) == ("venda", 30.0, "almacen", "A-7", "Froitas Melide SL")
    _alembic(url, "downgrade", "e1b3d5f7a9c4")
    with engine.connect() as conn:
        colleitas = conn.execute(text(
            "SELECT lote, cliente_nome, albaran_factura FROM colleita ORDER BY id")).all()
    assert [tuple(f) for f in colleitas] == [("L-1", None, None),
                                             ("L-2", "Froitas Melide SL", "A-7")]

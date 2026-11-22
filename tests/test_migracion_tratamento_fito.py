import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]


def _alembic(url: str, *args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=RAIZ,
        env={**os.environ, "HORTA_DATABASE_URL": url},
        check=True,
        capture_output=True,
    )


def test_migracion_copia_os_tratamentos_antigos(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "516b82f37f2e")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO usuario (id, nome, email, password_hash, rol, activo, created_at) "
            "VALUES (1, 'ana', 'ana@example.com', 'x', 'USUARIO', 1, '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO horta (id, nome, uso_profesional, created_at) "
            "VALUES (1, 'Horta', 1, '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO parcela (id, horta_id, nome, superficie, estado, created_at) "
            "VALUES (1, 1, 'P1', 2000, 'activa', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, estado, created_at) "
            "VALUES (1, 1, 'Pataca', 'planificado', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO tratamento (id, cultivo_id, data, praga, superficie_tratada, produto, "
            "numero_rexistro_produto, dose, eficacia, aplicador, equipo_aplicador, "
            "persoas_asesoramento, notas, baixa, created_at) VALUES (7, 1, '2026-05-01', "
            "'Mildeu', 1500, 'Cobre', 'ES-1', '2 kg/ha', 'boa', 'Xan', 'Mochila', 'Ana', "
            "'nota', 0, '2026-05-01')"
        ))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        fito = conn.execute(text(
            "SELECT id, horta_id, data_inicio, orixinal_produto, orixinal_dose, "
            "orixinal_aplicador, notas, tratamento_antigo_id, baixa FROM tratamento_fito"
        )).mappings().one()
        cultivo = conn.execute(text(
            "SELECT cultivo_id, superficie_ha FROM tratamento_cultivo WHERE tratamento_id = :t"
        ), {"t": fito["id"]}).mappings().one()
    assert fito["horta_id"] == 1
    assert str(fito["data_inicio"]) == "2026-05-01"
    assert (fito["orixinal_produto"], fito["orixinal_dose"], fito["orixinal_aplicador"]) == (
        "Cobre", "2 kg/ha", "Xan"
    )
    assert "Mildeu" in fito["notas"] and "ES-1" in fito["notas"]
    assert fito["tratamento_antigo_id"] == 7
    assert cultivo["cultivo_id"] == 1
    assert cultivo["superficie_ha"] == 0.15


def test_migracion_cultivo_pasa_datas_e_crea_colleita(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "e5c9f3b7d2a4")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO horta (id, nome, uso_profesional, created_at) "
            "VALUES (1, 'Horta', 0, '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO parcela (id, horta_id, nome, estado, created_at) "
            "VALUES (1, 1, 'P1', 'activa', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, estado, data_sementeira, "
            "data_colleita_real, cantidade, unidade, created_at) VALUES (1, 1, 'Pataca', "
            "'colleitado', '2026-03-01', '2026-07-15', 120, 'kg', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, estado, data_plantacion, "
            "created_at) VALUES (2, 1, 'Leituga', 'plantado', '2026-04-01', '2026-01-01')"
        ))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        cultivos = conn.execute(text(
            "SELECT id, tipo_inicio, data_inicio, data_fin FROM cultivo ORDER BY id"
        )).all()
        colleitas = conn.execute(text(
            "SELECT c.cultivo_id, c.data, c.cantidade, c.unidade, l.codigo FROM colleita c "
            "JOIN lote l ON l.id = c.lote_id"
        )).all()
    assert [tuple(map(str, c)) for c in cultivos] == [
        ("1", "sementeira", "2026-03-01", "2026-07-15"),
        ("2", "plantacion", "2026-04-01", "None"),
    ]
    assert [tuple(map(str, c)) for c in colleitas] == [
        ("1", "2026-07-15", "120.0", "kg", "MIGRADO-1"),
    ]

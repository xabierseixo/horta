"""O abono, o medicamento e a semente de antes pasan a produtos, e o provedor, o albará e o
lote a entradas."""

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


def test_insumos_pasan_a_produtos_e_compras(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "a3d5f7b9c1e8")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO persoa (id, horta_id, tipo, nome, activa, discapacidade) "
                          "VALUES (1, 1, 'entidade', 'Coop', 1, 0)"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, producion_integrada, "
            "sementeira_directa, material_tratado, material_adquirido, "
            "plan_ferramenta_sostibilidade, provedor_material_id, lote_material, "
            "data_adquisicion_material, created_at) "
            "VALUES (1, 1, 'Millo', 0, 0, 0, 1, 0, 1, 'L-9', '2026-03-01', '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO fertilizante (id, horta_id, nome, material, liquido, activo, "
            "provedor_id, created_at) VALUES (1, 1, 'NPK', '14', 0, 1, 1, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO abonado (id, horta_id, data_inicio, data_fin, fertilizante_id, "
            "xestion_sostible, aplicacion_lodos, albaran_factura, num_repeticions, baixa, "
            "created_at) VALUES (1, 1, '2026-03-10', '2026-03-10', 1, 0, 0, 'A-1', NULL, 0, "
            "'2026-03-10')"))
        conn.execute(text("INSERT INTO animal (id, horta_id, especie, cantidade, data_alta, "
                          "estado, created_at) VALUES (1, 1, 'Galiñas', 5, '2026-01-01', "
                          "'activo', '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO coidado_animal (id, horta_id, animal_id, data_inicio, data_fin, tipo, "
            "medicamento, provedor_id, proba_compra, tempo_espera_dias, baixa, created_at) "
            "VALUES (1, 1, 1, '2026-10-20', '2026-10-20', 'medicamento', 'Oxitetraciclina', 1, "
            "'F-7', 7, 0, '2026-10-20')"))
    _alembic(url, "upgrade", "b4e6a8c0d2f9")
    with engine.connect() as conn:
        produtos = {f.tipo: f for f in conn.execute(text(
            "SELECT id, tipo, nome, unidade, fertilizante_id FROM produto"))}
        entradas = {f.produto_id: f for f in conn.execute(text(
            "SELECT id, produto_id, data, provedor_id, albaran_factura, lote_provedor "
            "FROM entrada_produto"))}
        abonado = conn.execute(text("SELECT entrada_id FROM abonado")).scalar()
        coidado = conn.execute(text("SELECT produto_id, entrada_id FROM coidado_animal")).one()
        semente = conn.execute(text("SELECT entrada_semente_id FROM cultivo")).scalar()
    assert produtos["abono"].fertilizante_id == 1
    assert {p.unidade for p in produtos.values()} <= {"kg", "litros", "unidades"}
    compra_abono = entradas[produtos["abono"].id]
    assert (compra_abono.provedor_id, compra_abono.albaran_factura, abonado) == (
        1, "A-1", compra_abono.id)
    compra_medicamento = entradas[produtos["medicamento"].id]
    assert (produtos["medicamento"].nome, coidado.produto_id, coidado.entrada_id) == (
        "Oxitetraciclina", produtos["medicamento"].id, compra_medicamento.id)
    assert compra_medicamento.albaran_factura == "F-7"
    compra_semente = entradas[produtos["semente"].id]
    assert (compra_semente.lote_provedor, str(compra_semente.data), semente) == (
        "L-9", "2026-03-01", compra_semente.id)
    _alembic(url, "downgrade", "a3d5f7b9c1e8")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT albaran_factura FROM abonado")).scalar() == "A-1"
        assert tuple(conn.execute(text(
            "SELECT medicamento, provedor_id, proba_compra FROM coidado_animal")).one()) == (
            "Oxitetraciclina", 1, "F-7")
        assert tuple(conn.execute(text(
            "SELECT provedor_material_id, lote_material FROM cultivo")).one()) == (1, "L-9")

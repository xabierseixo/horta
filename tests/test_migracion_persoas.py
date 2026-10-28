"""Os textos con persoas e empresas de fóra pasan a fichas de persoa, sen perder nada e sen
duplicar."""

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


def test_os_textos_pasan_a_persoas(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "b2e4a6c8d0f5")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO horta (id, nome, uso_profesional, asesoramento_fertilizacion, "
            "titular_nome, titular_nif, asesoramento_nome, asesoramento_num, created_at) "
            "VALUES (1, 'Horta', 1, 0, 'Agro Ulla SL', 'B15000000', 'ATRIA Ulla', 'AT-7', "
            "'2026-01-01')"))
        conn.execute(text(
            "INSERT INTO persoa (id, horta_id, nome, e_aplicador, e_asesor, e_titular, "
            "e_traballador, activa, discapacidade) VALUES (1, 1, 'Xan', 1, 0, 0, 0, 1, 0), "
            "(2, 1, 'Ana', 0, 0, 0, 0, 1, 0)"))
        conn.execute(text(
            "INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
            "nif_arrendador, created_at) VALUES (1, 1, 'P1', 'activa', 0, '12345678Z', "
            "'2026-01-01')"))
        conn.execute(text(
            "INSERT INTO fertilizante (id, horta_id, nome, material, liquido, activo, "
            "provedor_nome, provedor_nif, created_at) VALUES "
            "(1, 1, 'Esterco', '5', 0, 1, 'Granxa do Monte', '33333333P', '2026-01-01'), "
            "(2, 1, 'Compost', '13', 0, 1, NULL, '33333333P', '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO analise (id, horta_id, material_analizado, data_mostraxe, "
            "laboratorio, laboratorio_nif, baixa, created_at) VALUES "
            "(1, 1, '3', '2026-03-01', 'Laboratorio Agrario', 'Q1500000A', 0, '2026-01-01')"))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        persoas = {fila.nome: fila for fila in conn.execute(text(
            "SELECT p.id, p.nome, p.tipo, p.nif, p.num_asesoramento, "
            "group_concat(pp.papel) AS papeis FROM persoa p "
            "LEFT JOIN persoa_papel pp ON pp.persoa_id = p.id GROUP BY p.id"))}
        provedores = conn.execute(text(
            "SELECT DISTINCT provedor_id FROM fertilizante")).scalars().all()
        laboratorio = conn.execute(text("SELECT laboratorio_id FROM analise")).scalar()
        arrendador = conn.execute(text("SELECT arrendador_id FROM parcela")).scalar()
    # Os papeis de antes; quen non tiña función traballa na explotación
    assert persoas["Xan"].papeis == "aplicador"
    assert persoas["Ana"].papeis == "traballador"
    # O titular e a entidade de asesoramento da explotación
    assert (persoas["Agro Ulla SL"].tipo, persoas["Agro Ulla SL"].papeis) == ("entidade",
                                                                              "titular")
    assert (persoas["ATRIA Ulla"].num_asesoramento, persoas["ATRIA Ulla"].papeis) == (
        "AT-7", "asesor")
    # O mesmo NIF é a mesma persoa: os dous abonos van ao mesmo provedor
    assert provedores == [persoas["Granxa do Monte"].id]
    assert laboratorio == persoas["Laboratorio Agrario"].id
    assert persoas["Laboratorio Agrario"].tipo == "entidade"
    assert arrendador == persoas["Arrendador 12345678Z"].id
    # E pódese volver atrás sen perder os textos
    _alembic(url, "downgrade", "b2e4a6c8d0f5")
    with engine.connect() as conn:
        horta = conn.execute(text("SELECT titular_nome, titular_nif FROM horta")).one()
        nif = conn.execute(text("SELECT nif_arrendador FROM parcela")).scalar()
    assert tuple(horta) == ("Agro Ulla SL", "B15000000") and nif == "12345678Z"

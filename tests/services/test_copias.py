"""Copias de seguridade da base de datos e das fotos (S1)."""

import sqlite3
import zipfile
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, make_url, text

from horta.models.usuario import RolGlobal, Usuario
from horta.services.copias import copia_diaria, facer_copia, ficheiro_da_copia, listar_copias
from horta.services.errors import PermisoDenegadoError

DIA = datetime(2026, 11, 4, 3, 0)


@pytest.fixture()
def motor(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path / 'horta.db'}")
    with motor.begin() as conexion:
        conexion.execute(text("CREATE TABLE parcela (id INTEGER PRIMARY KEY, nome TEXT)"))
        conexion.execute(text("INSERT INTO parcela (nome) VALUES ('Leira do medio')"))
    return motor


@pytest.fixture()
def cartafois(tmp_path, monkeypatch):
    fotos = tmp_path / "fotos"
    (fotos / "parcela").mkdir(parents=True)
    (fotos / "parcela" / "1.png").write_bytes(b"png")
    copias = tmp_path / "copias"
    monkeypatch.setenv("HORTA_FOTOS_DIR", str(fotos))
    monkeypatch.setenv("HORTA_COPIAS_DIR", str(copias))
    return copias


def test_copia_leva_a_base_de_datos_e_as_fotos(motor, cartafois, tmp_path):
    ruta = facer_copia(motor, DIA)

    assert ruta.name == "horta-2026-11-04-0300.zip"
    with zipfile.ZipFile(ruta) as zip_copia:
        assert "fotos/parcela/1.png" in zip_copia.namelist()
        zip_copia.extract("horta.db", tmp_path / "restaurada")
    with sqlite3.connect(tmp_path / "restaurada" / "horta.db") as restaurada:
        assert restaurada.execute("SELECT nome FROM parcela").fetchone() == ("Leira do medio",)


def test_copia_diaria_so_unha_vez_ao_dia(motor, cartafois):
    assert copia_diaria(motor, DIA) is not None
    assert copia_diaria(motor, DIA.replace(hour=9)) is None
    assert copia_diaria(motor, datetime(2026, 11, 5, 3, 0)) is not None
    assert len(list(cartafois.glob("*.zip"))) == 2


def test_garda_so_as_ultimas_copias(motor, cartafois):
    for dia in range(1, 32):
        copia_diaria(motor, datetime(2026, 10, dia, 3, 0))
    copia_diaria(motor, DIA)

    nomes = sorted(r.name for r in cartafois.glob("*.zip"))
    assert len(nomes) == 30
    assert nomes[-1] == "horta-2026-11-04-0300.zip"
    assert "horta-2026-10-02-0300.zip" not in nomes


def test_sen_sqlite_non_fai_copia(cartafois):
    """Con PostgreSQL a copia faise coas ferramentas do servidor, non dende a app."""
    motor = SimpleNamespace(url=make_url("postgresql://u@localhost/horta"))
    assert copia_diaria(motor, DIA) is None  # type: ignore[arg-type]
    assert not cartafois.exists()


def _usuario(session, rol):
    usuario = Usuario(nome=rol.value, email=f"{rol.value}@example.com", password_hash="x",
                      rol=rol)
    session.add(usuario)
    session.flush()
    return usuario


def test_so_o_admin_ve_e_descarga_as_copias(session, motor, cartafois):
    ruta = facer_copia(motor, DIA)
    admin = _usuario(session, RolGlobal.ADMIN)
    usuario = _usuario(session, RolGlobal.USUARIO)

    assert [c.nome for c in listar_copias(admin)] == [ruta.name]
    assert ficheiro_da_copia(admin, ruta.name) == ruta
    with pytest.raises(PermisoDenegadoError):
        listar_copias(usuario)
    with pytest.raises(PermisoDenegadoError):
        ficheiro_da_copia(usuario, ruta.name)


def test_non_se_descarga_nada_fora_do_cartafol(session, motor, cartafois):
    facer_copia(motor, DIA)
    admin = _usuario(session, RolGlobal.ADMIN)

    assert ficheiro_da_copia(admin, "../horta.db") is None
    assert ficheiro_da_copia(admin, "non-existe.zip") is None

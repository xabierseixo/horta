"""Fotos (paso 11a)."""

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fotos import (
    contar_fotos,
    dar_de_baixa_foto,
    ficheiro_da_foto,
    gardar_foto,
    listar_fotos,
)
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


@pytest.fixture(autouse=True)
def cartafol(tmp_path, monkeypatch):
    monkeypatch.setenv("HORTA_FOTOS_DIR", str(tmp_path))
    return tmp_path


def _usuario(session, nome):
    usuario = Usuario(nome=nome, email=f"{nome}@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _usuario(session, "ana")
    horta = crear_horta(session, ana, "Horta")
    return ana, horta, crear_parcela(session, ana, horta.id, "Leira")


def test_gardar_listar_e_baixa(session, cartafol):
    ana, horta, parcela = _escenario(session)
    foto = gardar_foto(session, ana, horta.id, "parcela", parcela.id, PNG, "leira.png",
                       hoxe=date(2026, 10, 29))
    assert foto.ficheiro.endswith(".png")
    assert (cartafol / str(horta.id) / foto.ficheiro).read_bytes() == PNG
    assert ficheiro_da_foto(session, ana, foto.id) == cartafol / str(horta.id) / foto.ficheiro
    assert contar_fotos(session, ana, horta.id) == {("parcela", parcela.id): 1}
    dar_de_baixa_foto(session, ana, foto)
    assert listar_fotos(session, ana, horta.id, "parcela", parcela.id) == []
    # O ficheiro consérvase (baixa lóxica)
    assert (cartafol / str(horta.id) / foto.ficheiro).exists()
    with pytest.raises(OperacionNonPermitidaError):
        ficheiro_da_foto(session, ana, foto.id)


@pytest.mark.parametrize("que, contido, erro", [
    ("parcela", b"GIF89a....", "JPEG, PNG ou WEBP"),
    ("parcela", PNG + b"0" * (10 * 1024 * 1024), "10 MB"),
    ("xoias", PNG, "non é desta"),
])
def test_validacions(session, que, contido, erro):
    ana, horta, parcela = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        gardar_foto(session, ana, horta.id, que, parcela.id, contido)


def test_doutra_explotacion(session):
    ana, horta, parcela = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta"):
        gardar_foto(session, ana, outra.id, "parcela", parcela.id, PNG)


def test_permisos(session):
    ana, horta, parcela = _escenario(session)
    foto = gardar_foto(session, ana, horta.id, "parcela", parcela.id, PNG)
    luis, xan = _usuario(session, "luis"), _usuario(session, "xan")
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)
    # Quen só mira ve as fotos pero non sube
    assert ficheiro_da_foto(session, luis, foto.id).name == foto.ficheiro
    with pytest.raises(PermisoDenegadoError):
        gardar_foto(session, luis, horta.id, "parcela", parcela.id, PNG)
    # Quen non é da explotación non a ve
    with pytest.raises(PermisoDenegadoError):
        ficheiro_da_foto(session, xan, foto.id)

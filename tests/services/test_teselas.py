"""Teselas do mapa con caché (sen rede: descarga simulada)."""

import pytest

from horta.services.teselas import (
    bbox_tesela,
    gardar_zona,
    tesela,
    tesela_do_punto,
    url_orixe,
)


@pytest.fixture(autouse=True)
def cartafol(tmp_path, monkeypatch):
    monkeypatch.setenv("HORTA_TESELAS_DIR", str(tmp_path))
    return tmp_path


def test_contas_das_teselas():
    assert bbox_tesela(0, 0, 0) == pytest.approx((-20037508.34, -20037508.34, 20037508.34,
                                                  20037508.34))
    assert tesela_do_punto(42.8, -8.0, 16) == (31311, 24130)
    assert "tilematrix=16&tilerow=24130&tilecol=31311" in url_orixe("pnoa", 16, 31311, 24130)
    assert "layers=AU.Sigpac:recinto" in url_orixe("sigpac", 16, 1, 1)


def test_cache_e_sen_conexion(cartafol):
    pedidas = []

    def descargar(url):
        pedidas.append(url)
        return b"png"

    assert tesela("sigpac", 16, 1, 2, descargar) == (b"png", "image/png")
    # A segunda vez sae do disco, sen descargar
    assert tesela("sigpac", 16, 1, 2, lambda url: None) == (b"png", "image/png")
    assert len(pedidas) == 1 and (cartafol / "sigpac" / "16" / "1" / "2.png").exists()
    assert tesela("sigpac", 16, 9, 9, lambda url: None) is None
    assert tesela("inventada", 16, 1, 2, descargar) is None


def test_gardar_zona():
    gardadas, fallidas = gardar_zona([(42.8, -8.0)], ("pnoa",), marxe_m=50,
                                     descargar=lambda url: b"x")
    assert gardadas > 0 and fallidas == 0

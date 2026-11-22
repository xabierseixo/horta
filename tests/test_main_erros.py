import anyio

from horta import main


class _RequestFalso:
    class _URLFalsa:
        path = "/isto-non-existe"

    url = _URLFalsa()


def test_manexador_404_devolve_pagina_propia():
    resposta = anyio.run(main.manexador_404, _RequestFalso(), Exception("non atopado"))

    corpo = resposta.body.decode("utf-8")
    assert resposta.status_code == 404
    assert "Páxina non atopada" in corpo


def test_manexador_500_devolve_pagina_propia_e_rexistra(caplog):
    resposta = anyio.run(main.manexador_500, _RequestFalso(), ValueError("boom"))

    corpo = resposta.body.decode("utf-8")
    assert resposta.status_code == 500
    assert "Ocorreu un erro" in corpo

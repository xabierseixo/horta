from horta.ui.erros import pagina_erro_html


def test_pagina_erro_html_inclue_titulo_e_mensaxe():
    resposta = pagina_erro_html("Páxina non atopada", "A ruta non existe.", 404)

    corpo = resposta.body.decode("utf-8")
    assert "Páxina non atopada" in corpo
    assert "A ruta non existe." in corpo
    assert resposta.status_code == 404


def test_pagina_erro_html_devolve_o_codigo_indicado():
    resposta = pagina_erro_html("Ocorreu un erro", "Algo saíu mal.", 500)

    assert resposta.status_code == 500


def test_pagina_erro_html_inclue_enlace_a_inicio():
    resposta = pagina_erro_html("Ocorreu un erro", "Algo saíu mal.", 500)

    corpo = resposta.body.decode("utf-8")
    assert 'href="/"' in corpo

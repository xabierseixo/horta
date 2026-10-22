from horta.ui.layout import normalizar_seccion, seccions_visibles, url_seccion


def test_url_seccion():
    assert url_seccion(2, "tratamentos") == "/hortas/2/tratamentos"


def test_seccion_descoñecida_vai_ao_resumo():
    assert normalizar_seccion("non-existe") == "resumo"
    assert normalizar_seccion("parcelas") == "parcelas"


def test_membros_so_para_admin_da_horta():
    claves_admin = [s.clave for s in seccions_visibles(e_horta_admin=True)]
    claves_editor = [s.clave for s in seccions_visibles(e_horta_admin=False)]
    assert "membros" in claves_admin
    assert "membros" not in claves_editor
    assert claves_editor[0] == "resumo"


def test_grupos_en_orde():
    grupos = []
    for s in seccions_visibles(e_horta_admin=True):
        if s.grupo and s.grupo not in grupos:
            grupos.append(s.grupo)
    assert grupos == ["Terra", "Caderno", "Gandaría", "Equipo"]

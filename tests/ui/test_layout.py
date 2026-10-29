from horta.ui.layout import normalizar_seccion, seccions_visibles, url_seccion


def test_url_seccion():
    assert url_seccion(2, "tratamentos") == "/hortas/2/tratamentos"


def test_seccion_descoñecida_vai_ao_resumo():
    assert normalizar_seccion("non-existe") == "resumo"
    assert normalizar_seccion("parcelas") == "parcelas"


def test_equipo_substitue_persoas_e_membros():
    claves_editor = [s.clave for s in seccions_visibles(e_horta_admin=False)]
    assert "equipo" in claves_editor
    assert "persoas" not in claves_editor and "membros" not in claves_editor
    assert claves_editor[0] == "resumo"


def test_grupos_en_orde():
    grupos = []
    for s in seccions_visibles(e_horta_admin=True):
        if s.grupo and s.grupo not in grupos:
            grupos.append(s.grupo)
    assert grupos == ["Produción", "Xestión", "Explotación"]


def test_menu_de_traballos_e_informes():
    claves = [s.clave for s in seccions_visibles(e_horta_admin=False)]
    assert claves[:4] == ["resumo", "diario", "calendario", "informes"]
    assert "tratamentos" not in claves and "explotacion" not in claves
    assert normalizar_seccion("tratamentos") == "tratamentos"
    assert "explotacion" in [s.clave for s in seccions_visibles(e_horta_admin=True)]

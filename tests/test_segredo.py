from horta.segredo import segredo_sesion


def test_usa_a_variable_se_existe(monkeypatch, tmp_path):
    monkeypatch.setenv("HORTA_STORAGE_SECRET", "o-meu-segredo")
    assert segredo_sesion(tmp_path / "segredo") == "o-meu-segredo"
    assert not (tmp_path / "segredo").exists()


def test_sen_variable_crea_un_segredo_e_reutilizao(monkeypatch, tmp_path):
    monkeypatch.delenv("HORTA_STORAGE_SECRET", raising=False)
    ficheiro = tmp_path / "horta" / "segredo"
    primeiro = segredo_sesion(ficheiro)
    assert len(primeiro) >= 32
    assert primeiro != "dev-secret-cambiar-en-produccion"
    assert segredo_sesion(ficheiro) == primeiro
    assert ficheiro.stat().st_mode & 0o077 == 0

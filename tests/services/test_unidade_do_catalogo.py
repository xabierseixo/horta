from horta.services.produtos import unidade_do_catalogo


def test_a_unidade_do_produto_sae_da_do_catalogo():
    assert unidade_do_catalogo("17") == "kg"
    assert unidade_do_catalogo("18") == "litros"
    assert unidade_do_catalogo("5") == "kg"
    assert unidade_do_catalogo("6") == "kg"
    assert unidade_do_catalogo("11") == "unidades"
    assert unidade_do_catalogo(None) == "litros"

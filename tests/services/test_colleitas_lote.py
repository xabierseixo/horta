import pytest

from horta.services.colleitas import nome_para_lote


@pytest.mark.parametrize(
    ("especie", "esperado"),
    [
        ("Pataca", "PATACA"),
        ("leituga", "LEITUGA"),
        ("Pemento de Padrón", "PEMENTO"),
        ("Chícharo", "CHICHARO"),
        ("Coliflor-romanesco", "COLIFLOR"),
        ("Remolacha azucreira", "REMOLACHA"),
        ("Cabaciña", "CABACINA"),
        ("Alcachofa_branca", "ALCACHOFA"),
        ("Superlonganome", "SUPERLONGA"),
        ("  ", "CULTIVO"),
    ],
)
def test_nome_para_lote(especie, esperado):
    assert nome_para_lote(especie) == esperado

import pytest

from horta.services.lotes import nome_para_codigo


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
        ("  ", "LOTE"),
    ],
)
def test_nome_para_codigo(especie, esperado):
    assert nome_para_codigo(especie) == esperado

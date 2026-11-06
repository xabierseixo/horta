"""Orde dos tipos en «Apuntar traballo»: primeiro os usados (X5)."""

from horta.services.diario import TIPOS, orde_tipos


def test_sen_historial_saen_os_habituais_e_o_resto_en_outros():
    principais, outros = orde_tipos({}, ten_animais=False, ten_lotes=False)
    assert principais == ["colleita", "rega", "tratamento", "abonado", "labor", "sementeira"]
    assert set(principais) | set(outros) == set(TIPOS)
    assert not set(principais) & set(outros)


def test_os_mais_usados_van_primeiro():
    principais, _ = orde_tipos({"rega": 9, "pastoreo": 3, "analise": 5},
                               ten_animais=True, ten_lotes=True)
    assert principais[:3] == ["rega", "analise", "pastoreo"]
    assert len(principais) == 6


def test_sen_animais_os_de_animais_van_a_outros_aínda_que_se_usasen():
    principais, outros = orde_tipos({"pastoreo": 4}, ten_animais=False, ten_lotes=True)
    assert "pastoreo" not in principais and "pastoreo" in outros

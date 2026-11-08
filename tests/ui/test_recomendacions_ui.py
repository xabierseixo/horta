"""Probas das funcións de texto da UI de recomendacións."""

from horta.ui.pages.recomendacions import (
    texto_aviso_recomendacions,
    texto_estado_recomendacion,
    texto_ligazon_recomendacions,
)


def test_texto_aviso_recomendacions():
    assert texto_aviso_recomendacions(1) == "O asesor deixou 1 recomendación por aplicar"
    assert texto_aviso_recomendacions(2) == "O asesor deixou 2 recomendacións por aplicar"
    assert texto_aviso_recomendacions(5) == "O asesor deixou 5 recomendacións por aplicar"


def test_texto_ligazon_recomendacions():
    assert texto_ligazon_recomendacions(0) == "Recomendacións do asesor (0 pendentes)"
    assert texto_ligazon_recomendacions(1) == "Recomendacións do asesor (1 pendentes)"
    assert texto_ligazon_recomendacions(3) == "Recomendacións do asesor (3 pendentes)"


def test_texto_estado_recomendacion():
    assert texto_estado_recomendacion("pendente") == "Pendente"
    assert texto_estado_recomendacion("aplicada") == "Aplicada"
    assert texto_estado_recomendacion("descartada") == "Descartada"
    assert texto_estado_recomendacion("outro") == "outro"

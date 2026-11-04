"""Límite de intentos de acceso (S2)."""

from datetime import datetime, timedelta

import pytest

from horta.services import intentos_login
from horta.services.intentos_login import apuntar_fallo, borrar_fallos, minutos_de_espera

AGORA = datetime(2026, 11, 5, 10, 0)


@pytest.fixture(autouse=True)
def sen_fallos():
    intentos_login._fallos.clear()


def test_catro_fallos_non_fan_esperar():
    for _ in range(4):
        apuntar_fallo("ana@example.com", AGORA)
    assert minutos_de_espera("ana@example.com", AGORA) == 0


def test_cinco_fallos_fan_esperar_quince_minutos():
    for _ in range(5):
        apuntar_fallo("ana@example.com", AGORA)
    assert minutos_de_espera("ana@example.com", AGORA) == 15
    assert minutos_de_espera("ana@example.com", AGORA + timedelta(minutes=14)) == 1
    assert minutos_de_espera("ana@example.com", AGORA + timedelta(minutes=15)) == 0


def test_conta_o_mesmo_email_con_maiusculas_e_espazos():
    for _ in range(5):
        apuntar_fallo(" Ana@Example.com", AGORA)
    assert minutos_de_espera("ana@example.com", AGORA) == 15


def test_outro_email_non_espera():
    for _ in range(5):
        apuntar_fallo("ana@example.com", AGORA)
    assert minutos_de_espera("brais@example.com", AGORA) == 0


def test_entrar_ben_borra_os_fallos():
    for _ in range(5):
        apuntar_fallo("ana@example.com", AGORA)
    borrar_fallos("ana@example.com")
    assert minutos_de_espera("ana@example.com", AGORA) == 0


def test_os_fallos_vellos_bórranse():
    apuntar_fallo("ana@example.com", AGORA)
    apuntar_fallo("brais@example.com", AGORA + timedelta(minutes=20))
    assert "ana@example.com" not in intentos_login._fallos

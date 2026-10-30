"""A conexión coa Xunta: a petición é de quen a pide, caduca e o token non se garda no disco."""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest

from horta.services import conexion_xeaga as conexion
from horta.services.errors import OperacionNonPermitidaError

AGORA = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)


def _jwt(nif="12345678Z"):
    carga = base64.urlsafe_b64encode(json.dumps({"cif": nif, "exp": 4_000_000_000})
                                     .encode()).decode().rstrip("=")
    return f"c.{carga}.s"


def test_o_token_volve_a_quen_pediu_a_conexion():
    peticion = conexion.nova_peticion(1, 7, AGORA)
    horta_id, token = conexion.recibir_token(peticion, _jwt(), 1, AGORA)
    assert (horta_id, token.nif) == (7, "12345678Z")
    assert conexion.token_vixente(1, 7) is token
    conexion.desconectar(1, 7)
    assert conexion.token_vixente(1, 7) is None


def test_peticion_allea_repetida_ou_caducada():
    peticion = conexion.nova_peticion(1, 7, AGORA)
    with pytest.raises(OperacionNonPermitidaError):
        conexion.recibir_token(peticion, _jwt(), 2, AGORA)
    with pytest.raises(OperacionNonPermitidaError):
        conexion.recibir_token(peticion, _jwt(), 1, AGORA)
    vella = conexion.nova_peticion(1, 7, AGORA)
    with pytest.raises(OperacionNonPermitidaError):
        conexion.recibir_token(vella, _jwt(), 1, AGORA + timedelta(minutes=16))


def test_sen_configuracion_non_hai_xunta(monkeypatch):
    monkeypatch.delenv("HORTA_XEAGA_URL", raising=False)
    assert conexion.xeaga_configurada() is None
    monkeypatch.setenv("HORTA_XEAGA_URL", "https://api-lab.xeaga.xunta.gal/IUWS/api")
    monkeypatch.setenv("HORTA_XEAGA_APP", "horta")
    assert conexion.xeaga_configurada().app == "horta"

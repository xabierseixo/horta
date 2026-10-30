"""Cliente do IUWS da Xunta (Anexo VI v4.10), con respostas gardadas: as probas nunca usan a
rede."""

import base64
import io
import json
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import pytest

from horta.services.xeaga import (
    IUWS_CONSUMER,
    Xeaga,
    XeagaErro,
    actividades_procesadas,
    ler_resultado,
    ler_token,
)

DATOS = Path(__file__).parent.parent / "datos" / "xeaga"


def _token(nif="12345678Z", exp=2_000_000_000):
    carga = base64.urlsafe_b64encode(json.dumps({"sub": "horta", "cif": nif, "exp": exp})
                                     .encode()).decode().rstrip("=")
    return f"cabeceira.{carga}.sinatura"


class _Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *erro):
        return False


def _xeaga(ficheiro, peticions):
    def abrir(peticion):
        peticions.append(peticion)
        return _Resposta((DATOS / ficheiro).read_bytes())
    return Xeaga("https://api-lab.xeaga.xunta.gal/IUWS/api/", "horta", abrir)


def test_o_token_trae_o_nif_e_a_caducidade():
    token = ler_token(_token())
    assert token.nif == "12345678Z"
    assert token.valido(datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert not token.valido(datetime(2034, 1, 1, tzinfo=timezone.utc))
    with pytest.raises(XeagaErro):
        ler_token("isto-non-e-un-jwt")


def test_url_de_acceso_do_produtor():
    xeaga = Xeaga("https://api-lab.xeaga.xunta.gal/IUWS/api/", "horta")
    assert xeaga.url_acceso("a1b2") == (
        "https://api-lab.xeaga.xunta.gal/IUWS/api/comunicacionProductor/horta/a1b2")


def test_crear_devolve_o_numero_de_peticion_e_manda_as_cabeceiras():
    peticions = []
    numero = _xeaga("crear_ok.json", peticions).crear(ler_token(_token()), {"CodigoRea": "X"})
    assert numero == 64672
    [p] = peticions
    assert p.get_method() == "POST" and p.full_url.endswith("/crear/")
    assert p.get_header("Iuws-consumer") == IUWS_CONSUMER
    assert p.get_header("Authorization").startswith("Bearer ")
    assert json.loads(p.data) == {"CUADERNO": [{"CodigoRea": "X"}]}


def test_un_envio_de_mais_de_2_mb_non_sae():
    peticions = []
    with pytest.raises(XeagaErro, match="2 MB"):
        _xeaga("crear_ok.json", peticions).crear(ler_token(_token()), {"x": "a" * 2_100_000})
    assert peticions == []


def test_estado_pendente():
    estado = _xeaga("estado_pendente.json", []).comprobar_estado(ler_token(_token()), 64672)
    assert estado.pendente and estado.cuaderno is None


def test_estado_parcial_trae_cada_actividade():
    estado = ler_resultado(json.loads((DATOS / "estado_parcial.json").read_text()))
    assert estado.codigo == "PARCIAL" and not estado.pendente
    assert estado.mensaxes[0].codigo == 12
    procesadas = {(a.bloque, a.id_ajena): (a.valida, a.id_cuaderno)
                  for a in actividades_procesadas(estado)}
    assert procesadas == {("SiembraPlantacion", 64256): (True, 36),
                          ("Fertilizacion", 700): (False, 36)}


def test_rea_sen_cif_de_xestora():
    peticions = []
    rea = _xeaga("rea.json", peticions).exportar_rea(ler_token(_token()), "12345678Z")
    assert peticions[0].full_url.endswith("/exportarREA/12345678Z")
    assert rea.codigo == "OK" and rea.rea[0]["Codigo_Rea"] == "ES130000008846"


def test_sen_acceso_dise_claro():
    def abrir(peticion):
        raise urllib.error.HTTPError(peticion.full_url, 401, "", {}, None)
    with pytest.raises(XeagaErro, match="volve conectar"):
        Xeaga("https://x", "horta", abrir).comprobar_estado(ler_token(_token()), 1)

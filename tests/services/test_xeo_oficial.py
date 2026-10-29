"""SIGPAC e Catastro: lectura das respostas (exemplos gardados, sen rede)."""

from horta.models.usuario import RolGlobal, Usuario
from horta.services.hortas import crear_horta
from horta.services.xeo_oficial import (
    crear_parcela_do_recinto,
    ler_recintos,
    ler_referencia_catastral,
    puntos_wkt,
)

_RECINTO = [{
    "provincia": 15, "municipio": 78, "agregado": 0, "zona": 0, "poligono": 12,
    "parcela": 345, "recinto": 2, "uso_sigpac": "TA", "superficie": 1.0,
    "wkt": "POLYGON((-8.0 42.8,-8.0 42.8009,-7.99878 42.8009,-7.99878 42.8,-8.0 42.8))",
}]
_CATASTRO = b"""<?xml version="1.0" encoding="utf-8"?>
<consulta_coordenadas xmlns="http://www.catastro.meh.es/"><coordenadas><coord>
<pc><pc1>15078A0</pc1><pc2>1200345</pc2></pc></coord></coordenadas></consulta_coordenadas>"""


def test_ler_recinto_e_wkt():
    [recinto] = ler_recintos(_RECINTO)
    assert recinto.referencia == "15:78:0:0:12:345:2"
    assert recinto.uso == "TA" and len(recinto.puntos) == 4
    assert puntos_wkt("MULTIPOLYGON(((1 2,3 4,5 6,1 2)))") == [(2, 1), (4, 3), (6, 5)]
    assert ler_recintos([]) == []


def test_referencia_catastral():
    assert ler_referencia_catastral(_CATASTRO) == "15078A01200345"
    assert ler_referencia_catastral(b"non e xml") is None


def test_crear_parcela_do_recinto(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    [recinto] = ler_recintos(_RECINTO)
    parcela = crear_parcela_do_recinto(session, ana, horta.id, "", recinto)
    assert parcela.nome == "Recinto 12-345-2"
    assert (parcela.sigpac_poligono, parcela.sigpac_parcela, parcela.sigpac_subparcela) == (
        "12", "345", "2")
    assert 0.95 < parcela.superficie < 1.05 and parcela.geometria

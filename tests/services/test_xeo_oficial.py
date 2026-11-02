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


_DNPRC = """<consulta_dnp xmlns="http://www.catastro.meh.es/"><bico><bi>
<ldt>Polígono 12 Parcela 345 AS VEIGAS. SANTIAGO (A CORUÑA)</ldt>
<debi><luso>Agrario</luso></debi><cn>RU</cn></bi><lspr>
<spr><cspr>a</cspr><dspr><ccc>LR</ccc><dcc>LABOR O LABRADIO REGADIO</dcc><ip>02</ip>
<ssp>6000</ssp></dspr></spr>
<spr><cspr>b</cspr><dspr><ccc>PD</ccc><dcc>PRADOS O PRADERAS</dcc><ip>01</ip>
<ssp>4000</ssp></dspr></spr></lspr></bico></consulta_dnp>""".encode()
_GML = """<FeatureCollection xmlns:gml="http://www.opengis.net/gml/3.2"
xmlns:cp="urn:x-inspire:specification:gmlas:CadastralParcels:3.0"><member><cp:CadastralParcel>
<cp:areaValue uom="m2">10000</cp:areaValue><gml:posList>42.8 -8.0 42.8009 -8.0 42.8009 -7.99878
42.8 -7.99878 42.8 -8.0</gml:posList></cp:CadastralParcel></member></FeatureCollection>""".encode()


def test_catastro_datos_e_contorno(session):
    from horta.services.xeo_oficial import (
        ParcelaCatastral,
        crear_parcela_do_catastro,
        ler_dnprc,
        ler_gml_parcela,
    )

    datos = ler_dnprc(_DNPRC, "15078A01200345")
    assert datos.clase == "Rústico" and datos.uso == "Agrario"
    assert datos.cultivos == (("LABOR O LABRADIO REGADIO", "02", 6000.0),
                              ("PRADOS O PRADERAS", "01", 4000.0))
    puntos, area = ler_gml_parcela(_GML)
    assert len(puntos) == 4 and area == 10000
    assert ler_dnprc(b"mal", "X").referencia == "X"
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela_do_catastro(session, ana, horta.id, "", ParcelaCatastral(
        datos.referencia, datos.localizacion, puntos=tuple(puntos)))
    assert parcela.referencia_catastral == "15078A01200345"
    assert parcela.nome.startswith("Polígono 12") and parcela.geometria


def test_o_catastro_non_pisa_o_sigpac(session):
    from horta.services.xeo_oficial import ParcelaCatastral, completar_parcela_co_catastro

    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    [recinto] = ler_recintos(_RECINTO)
    parcela = crear_parcela_do_recinto(session, ana, horta.id, "", recinto,
                                       referencia_catastral="15078A01200345")
    assert parcela.referencia_catastral == "15078A01200345"
    contorno, superficie = parcela.geometria, parcela.superficie
    pequena = ((42.8, -8.0), (42.8001, -8.0), (42.8001, -7.9999))
    completar_parcela_co_catastro(session, ana, parcela, ParcelaCatastral(
        "15078A01200346", None, superficie_m2=50.0, puntos=pequena))
    assert parcela.referencia_catastral == "15078A01200346"
    assert (parcela.geometria, parcela.superficie) == (contorno, superficie)

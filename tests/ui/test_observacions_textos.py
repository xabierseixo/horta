"""Probas unitarias das funcións puras de textos de observacións de pragas."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from horta.models.observacion import ObservacionPraga
from horta.ui.layout import SECCIONS
from horta.ui.pages.diario import _CONSTRUTORES, _MODELOS, ICONAS, SECCION_DO_TIPO
from horta.ui.pages.observacions import (
    HINT_FONTE_LIMIAR,
    LIGAZON_GUIAS_MAPA,
    dialogo_limiares,
    dialogo_observacion,
    opcions_grafica_evolucion,
    texto_conto_ou_nivel,
    texto_cultivo_limiar,
    texto_limiar,
    texto_supera,
)


def test_texto_conto_ou_nivel_con_conto_e_unidade() -> None:
    assert texto_conto_ou_nivel(5.0, "capturas por trampa") == "5 capturas por trampa"
    assert texto_conto_ou_nivel(12.5, "% de follas") == "12.5 % de follas"


def test_texto_conto_ou_nivel_so_conto() -> None:
    assert texto_conto_ou_nivel(3.0) == "3"


def test_texto_conto_ou_nivel_so_nivel() -> None:
    assert texto_conto_ou_nivel(None, nivel="baixo") == "Baixo"
    assert texto_conto_ou_nivel(None, nivel="medio") == "Medio"
    assert texto_conto_ou_nivel(None, nivel="alto") == "Alto"


def test_texto_conto_ou_nivel_conto_e_nivel() -> None:
    assert (
        texto_conto_ou_nivel(10.0, "capturas por trampa", "medio")
        == "10 capturas por trampa (Medio)"
    )


def test_texto_conto_ou_nivel_baleiro() -> None:
    assert texto_conto_ou_nivel(None, None, None) == ""


def test_texto_limiar_con_valor() -> None:
    assert texto_limiar(10.0) == "10"
    assert texto_limiar(3.5) == "3.5"


def test_texto_limiar_con_obxecto() -> None:
    limiar = SimpleNamespace(valor=8.0, unidade_conto="capturas por trampa")
    assert texto_limiar(limiar) == "8"


def test_texto_limiar_sen_limiar() -> None:
    assert texto_limiar(None) == "—"


def test_texto_supera() -> None:
    assert texto_supera(True) == "Si"
    assert texto_supera(False) == ""


def test_rexistro_seccion_e_diario() -> None:
    seccions_claves = {s.clave: s for s in SECCIONS}
    assert "pragas" in seccions_claves
    seccion = seccions_claves["pragas"]
    assert seccion.etiqueta == "Seguimento de pragas"
    assert seccion.icona == "bug_report"
    assert seccion.no_menu is True

    assert ICONAS["observacion"] == "bug_report"
    assert SECCION_DO_TIPO["observacion"] == "pragas"
    assert _MODELOS["observacion"] is ObservacionPraga
    assert _CONSTRUTORES["observacion"] is dialogo_observacion


def test_texto_cultivo_limiar() -> None:
    assert texto_cultivo_limiar(None) == "Xeral (todos os cultivos)"
    cultivo1 = SimpleNamespace(especie="Pataca", variedade=None, cultivo_siex_codigo=101)
    cultivo2 = SimpleNamespace(especie="Millo", variedade="Doce", cultivo_siex_codigo=202)
    assert texto_cultivo_limiar(101, [cultivo1, cultivo2]) == "Pataca"
    assert texto_cultivo_limiar(202, [cultivo1, cultivo2]) == "Millo (Doce)"
    assert texto_cultivo_limiar(999, [cultivo1, cultivo2]) == "Cultivo SIEX 999"


def test_opcions_grafica_evolucion_baleiro() -> None:
    assert opcions_grafica_evolucion([]) is None
    obs_sen_conto = [
        SimpleNamespace(
            data=date(2026, 5, 1),
            problema_tipo="praga",
            problema_codigo="10",
            conto=None,
            nivel="alto",
        )
    ]
    assert opcions_grafica_evolucion(obs_sen_conto) is None


def test_opcions_grafica_evolucion_un_problema() -> None:
    obs1 = SimpleNamespace(
        data=date(2026, 5, 10),
        problema_tipo="praga",
        problema_codigo="10",
        conto=2.0,
    )
    obs2 = SimpleNamespace(
        data=date(2026, 5, 5),
        problema_tipo="praga",
        problema_codigo="10",
        conto=1.0,
    )
    opcions = opcions_grafica_evolucion(
        [obs1, obs2],
        problemas_nomes={("praga", "10"): "Escaravello da pataca"},
    )
    assert opcions is not None
    assert opcions["xAxis"]["data"] == ["05/05/2026", "10/05/2026"]
    assert len(opcions["series"]) == 1
    serie = opcions["series"][0]
    assert serie["name"] == "Escaravello da pataca"
    assert serie["type"] == "line"
    assert serie["data"] == [1.0, 2.0]
    assert serie["connectNulls"] is True
    assert "markLine" not in serie


def test_opcions_grafica_evolucion_con_limiar() -> None:
    obs = SimpleNamespace(
        data=date(2026, 5, 8),
        problema_tipo="praga",
        problema_codigo="10",
        conto=12.0,
    )
    limiar = SimpleNamespace(valor=10.0, unidade_conto="capturas por trampa")
    opcions = opcions_grafica_evolucion(
        [obs],
        problemas_nomes={("praga", "10"): "Praga 10"},
        limiares={("praga", "10"): limiar},
    )
    assert opcions is not None
    serie = opcions["series"][0]
    assert "markLine" in serie
    assert serie["markLine"]["lineStyle"]["type"] == "dashed"
    assert serie["markLine"]["data"] == [{"yAxis": 10.0, "name": "Limiar"}]


def test_opcions_grafica_evolucion_varios_problemas() -> None:
    obs1 = SimpleNamespace(
        data=date(2026, 5, 1),
        problema_tipo="praga",
        problema_codigo="10",
        conto=3.0,
    )
    obs2 = SimpleNamespace(
        data=date(2026, 5, 5),
        problema_tipo="enfermidade",
        problema_codigo="20",
        conto=7.0,
    )
    opcions = opcions_grafica_evolucion(
        [obs1, obs2],
        problemas_nomes={
            ("praga", "10"): "Escaravello",
            ("enfermidade", "20"): "Mildiou",
        },
    )
    assert opcions is not None
    assert opcions["xAxis"]["data"] == ["01/05/2026", "05/05/2026"]
    assert len(opcions["series"]) == 2
    assert opcions["series"][0]["name"] == "Escaravello"
    assert opcions["series"][0]["data"] == [3.0, None]
    assert opcions["series"][1]["name"] == "Mildiou"
    assert opcions["series"][1]["data"] == [None, 7.0]


def test_constantes_e_dialogo_limiares() -> None:
    assert "mapa.gob.es" in LIGAZON_GUIAS_MAPA
    assert "guía" in HINT_FONTE_LIMIAR.lower()
    assert callable(dialogo_limiares)

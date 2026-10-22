from datetime import date
from pathlib import Path

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, NomeGalego
from horta.services.catalogos import (
    buscar_cultivos,
    cargar_nomes_galegos,
    describir,
    normalizar,
    validar_codigo,
    valores_vixentes,
)
from horta.services.errors import OperacionNonPermitidaError


def _preparar(session):
    v = CatalogoVersion(catalogo="x", nome_ficheiro="x", sha256="b" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add_all([
        CatalogoValor(catalogo="praga", codigo="1", descricion="Arthropoda", version_id=v.id),
        CatalogoValor(catalogo="praga", codigo="2", descricion="Vella", version_id=v.id,
                      data_baixa=date(2026, 1, 1)),
        CultivoSiex(codigo=99, nome_oficial="PATATA", version_id=v.id),
        CultivoSiex(codigo=484, nome_oficial="GRELOS", version_id=v.id),
        CultivoSiex(codigo=1, nome_oficial="TRIGO BLANDO", version_id=v.id),
    ])
    session.add(NomeGalego(catalogo="cultivo", codigo="99", nome_gl="Pataca", prioridade=10))
    session.commit()


def test_valores_vixentes_exclúe_os_de_baixa(session):
    _preparar(session)
    codigos = [v.codigo for v in valores_vixentes(session, "praga", date(2026, 6, 1))]
    assert codigos == ["1"]
    codigos_antes = [v.codigo for v in valores_vixentes(session, "praga", date(2025, 6, 1))]
    assert codigos_antes == ["1", "2"]


def test_validar_codigo_de_baixa_falla(session):
    _preparar(session)
    with pytest.raises(OperacionNonPermitidaError, match="non existe ou está de baixa"):
        validar_codigo(session, "praga", "2", date(2026, 6, 1))
    assert validar_codigo(session, "praga", "2", date(2025, 6, 1)).descricion == "Vella"


def test_describir_inclúe_baixas_e_descoñecidos(session):
    _preparar(session)
    assert describir(session, "praga", "2") == "Vella"
    assert describir(session, "praga", "999") == "999"


def test_normalizar():
    assert normalizar("  Ácaros ÑÁÉ ") == "acaros nae"


def test_buscar_cultivos_galego_primeiro(session):
    _preparar(session)
    resultado = buscar_cultivos(session, "pat")
    assert [(c.codigo, nome) for c, nome in resultado] == [(99, "Pataca")]
    resultado = buscar_cultivos(session, "")
    assert resultado[0][0].codigo == 99  # o de maior prioridade galega, primeiro


def test_cargar_nomes_galegos(session, tmp_path: Path):
    _preparar(session)
    ruta = tmp_path / "nomes.csv"
    ruta.write_text("codigo;nome_gl;prioridade\n484;Grelos;9\n", encoding="utf-8")
    assert cargar_nomes_galegos(session, ruta) == 1
    assert session.query(NomeGalego).filter_by(codigo="484").one().prioridade == 9


def test_buscar_cultivos_por_comezo_de_palabra(session):
    _preparar(session)
    v = session.query(CatalogoVersion).first()
    session.add_all([
        CultivoSiex(codigo=519, nome_oficial="FESTUCA OVINA", version_id=v.id),
        CultivoSiex(codigo=102, nome_oficial="VIÑA", version_id=v.id),
        CultivoSiex(codigo=884, nome_oficial="IMPATIENS", version_id=v.id),
    ])
    session.commit()
    assert [c.codigo for c, _ in buscar_cultivos(session, "viña")] == [102]
    assert 884 not in [c.codigo for c, _ in buscar_cultivos(session, "pat")]


def test_codigo_non_vale_antes_da_data_de_alta(session):
    _preparar(session)
    v = session.query(CatalogoVersion).first()
    session.add(CatalogoValor(catalogo="praga", codigo="3", descricion="Nova",
                              version_id=v.id, data_alta=date(2026, 6, 1)))
    session.commit()
    with pytest.raises(OperacionNonPermitidaError, match="non existe ou está de baixa"):
        validar_codigo(session, "praga", "3", date(2026, 5, 1))
    assert validar_codigo(session, "praga", "3", date(2026, 6, 1)).descricion == "Nova"

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from horta.models.catalogo import (
    CatalogoValor,
    CatalogoVersion,
    CultivoSiex,
    NomeGalego,
    VariedadeLocal,
    VariedadeSiex,
)


def _version(session, catalogo="praga"):
    v = CatalogoVersion(catalogo=catalogo, nome_ficheiro="PLAGAS.xlsx", sha256="a" * 64, filas=1)
    session.add(v)
    session.commit()
    return v


def test_catalogo_valor_e_unico_por_catalogo_e_codigo(session):
    v = _version(session)
    session.add(
        CatalogoValor(catalogo="praga", codigo="1", descricion="Arthropoda", version_id=v.id)
    )
    session.commit()
    session.add(CatalogoValor(catalogo="praga", codigo="1", descricion="Outra", version_id=v.id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_cultivo_variedade_e_capa_galega(session):
    v = _version(session, "cultivo")
    pataca = CultivoSiex(
        codigo=99, nome_oficial="PATATA", nome_latin="Solanum tuberosum",
        codigo_eppo="SOLTU", horticola=True, integrado=True, version_id=v.id,
    )
    session.add(pataca)
    session.add(VariedadeSiex(cultivo_codigo=99, codigo=0, nome_oficial="SIN VARIEDAD",
                              version_id=v.id))
    session.add(NomeGalego(catalogo="cultivo", codigo="99", nome_gl="Pataca", prioridade=10))
    session.add(VariedadeLocal(cultivo_codigo=99, nome="Fina de Carballo",
                               fonte="IXP Pataca de Galicia"))
    session.commit()
    assert pataca.data_baixa is None
    assert session.query(VariedadeLocal).one().cultivo_codigo == 99
    assert session.query(NomeGalego).one().nome_gl == "Pataca"


def test_data_baixa_opcional(session):
    v = _version(session)
    valor = CatalogoValor(catalogo="praga", codigo="2", descricion="X", version_id=v.id,
                          data_baixa=date(2026, 1, 1))
    session.add(valor)
    session.commit()
    assert valor.data_baixa == date(2026, 1, 1)

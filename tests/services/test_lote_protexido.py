"""G6: un lote non mestura colleitas de invernadoiro e de aire libre (máximos distintos
na venda directa)."""

import pytest
from test_lotes import _colleita, _escenario

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.lotes import SISTEMAS_PROTEXIDOS


def test_non_mestura_invernadoiro_e_aire_libre(session):
    ana, horta, quen, cultivo = _escenario(session)
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="e" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="sistema_cultivo", codigo=SISTEMAS_PROTEXIDOS[0],
                              descricion="Invernadoiro", version_id=v.id))
    invernadoiro = crear_cultivo(session, ana, cultivo.parcela_id, "Pataca")
    actualizar_cultivo(session, ana, invernadoiro, sistema_cultivo=SISTEMAS_PROTEXIDOS[0])
    _colleita(session, ana, cultivo, quen)
    with pytest.raises(OperacionNonPermitidaError, match="invernadoiro"):
        _colleita(session, ana, invernadoiro, quen)


def test_dous_cultivos_ao_aire_libre_van_no_mesmo_lote(session):
    ana, horta, quen, cultivo = _escenario(session)
    outro = crear_cultivo(session, ana, cultivo.parcela_id, "Pataca")
    a = _colleita(session, ana, cultivo, quen)
    b = _colleita(session, ana, outro, quen)
    assert a.lote_id == b.lote_id

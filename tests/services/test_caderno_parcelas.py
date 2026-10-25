from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import actualizar_parcela, crear_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    crear_cultivo(session, ana, parcela.id, "Pataca")
    return ana, horta, parcela


def test_auga_e_zona_no_caderno(session):
    ana, horta, parcela = _escenario(session)
    actualizar_parcela(session, ana, parcela, auga_consumo=True, auga_consumo_distancia_m=40,
                       auga_consumo_denominacion="Pozo da casa", zona_especifica="parcial",
                       zona_especifica_ha=0.05)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [list(f) for f in libro["2 Parcelas"].iter_rows(values_only=True)]
    i = next(n for n, f in enumerate(filas) if f[0] == "2.2 DATOS IDENTIFICATIVOS "
             "MEDIOAMBIENTAIS DAS PARCELAS")
    assert [x or "" for x in filas[i + 2][:10]] == [1, "Pataca", "", "NON", 40, "",
                                                    "Pozo da casa", "NON", "SI", 0.05]


@pytest.mark.parametrize(("campos", "mensaxe"), [
    ({"zona_especifica": "media"}, "total"),
    ({"auga_consumo_distancia_m": -1}, "negativas"),
])
def test_validacions(session, campos, mensaxe):
    ana, _, parcela = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        actualizar_parcela(session, ana, parcela, **campos)

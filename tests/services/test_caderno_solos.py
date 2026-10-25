from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.analises import DatosAnalise, crear_analise
from horta.services.caderno import xerar_caderno
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 25)


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="material_analizado", codigo="3", descricion="Suelo",
                              version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    return ana, horta, crear_parcela(session, ana, horta.id, "Leira")


def test_metais_pesados_no_caderno(session):
    ana, horta, parcela = _escenario(session)
    crear_analise(session, ana, horta.id, DatosAnalise(
        material_analizado="3", data_mostraxe=date(2026, 2, 1), parcela_id=parcela.id,
        solo={"ph": 5.6, "cadmio": 0.4, "chumbo": 12}), hoxe=HOXE)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    fila = list(next(libro["6 Solos"].iter_rows(min_row=5, values_only=True)))
    assert fila[0] == "Leira" and fila[2] == 5.6 and fila[7] == 0.4 and fila[10] == 12


def test_metal_negativo(session):
    ana, horta, parcela = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="metais"):
        crear_analise(session, ana, horta.id, DatosAnalise(
            material_analizado="3", data_mostraxe=date(2026, 2, 1), solo={"zinc": -1}),
            hoxe=HOXE)

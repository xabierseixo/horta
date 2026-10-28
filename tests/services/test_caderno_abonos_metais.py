from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.abonado import Abonado
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.fertilizante import FertilizanteSiex
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante, datos_desde_siex
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for codigo in ("14", "20"):
        session.add(CatalogoValor(catalogo="material_fertilizante", codigo=codigo,
                                  descricion=f"m{codigo}", version_id=v.id))
    session.add(FertilizanteSiex(codigo=5, material="14", nome="UREA (46-00-00)", n_pct=46,
                                 n_ureico_pct=46, version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_formas_do_n_dende_o_catalogo(session):
    ana, horta = _escenario(session)
    assert datos_desde_siex(session, 5).n_ureico_pct == 46


def test_metais_do_residuo_no_caderno(session):
    ana, horta = _escenario(session)
    compost = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost de alperujo", material="20",
        provedor_id=crear_contacto(session, ana, horta.id, "Planta X", "provedor").id, n_pct=1.5,
        materia_organica_pct=40, cadmio=0.7, chumbo=45))
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id, "Col")
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 3, 1),
                        data_fin=date(2026, 3, 1), superficie_ha=0.1, fertilizante_id=compost.id,
                        dose=10, unidade="29", tipo_fertilizacion="1", metodo="1"))
    session.commit()
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [list(f) for f in libro["7 Fertilización"].iter_rows(values_only=True)]
    assert filas[4][21] == 40  # materia orgánica
    i = next(n for n, f in enumerate(filas) if f[0] and str(f[0]).startswith(
        "FERTILIZACIÓN (Metais pesados)"))
    metais = filas[i + 2]
    assert metais[2] == "m20" and metais[3] == 10000 and metais[4] == 0.7 and metais[7] == 45


def test_metal_negativo(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="metais"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(
            nome="X", material="20",
            provedor_id=crear_contacto(session, ana, horta.id, "Y", "provedor").id, zinc=-1))

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.abonado import Abonado, AbonadoCultivo, Fertilizante
from horta.models.analise import Analise
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.rega import Rega, RegaCultivo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto


def _usuario(session, email):
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo, texto in [("sistema_rega", "6", "Goteo"),
                                    ("tipo_fertilizacion", "1", "Abonado de fondo"),
                                    ("metodo_fertilizacion", "1", "Esparcido general"),
                                    ("material_fertilizante", "14", "Abonos inorgánicos"),
                                    ("material_analizado", "3", "Suelo")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=texto,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta da Ana")
    parcela = crear_parcela(session, ana, horta.id, "Leira", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2, data_inicio=date(2026, 3, 1),
                       plan_necesidade_n=120, plan_data=date(2026, 2, 1))
    abono = Fertilizante(horta_id=horta.id, nome="NPK 15-15-15", material="14", n_pct=15,
                         p2o5_pct=15, k2o_pct=15)
    session.add(abono)
    session.flush()
    session.add_all([
        Abonado(horta_id=horta.id, data_inicio=date(2026, 3, 10),
                data_fin=date(2026, 3, 10), fertilizante_id=abono.id,
                dose=200, unidade="17", tipo_fertilizacion="1", metodo="1",
                leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]),
        Rega(horta_id=horta.id, data_inicio=date(2026, 7, 1),
             data_fin=date(2026, 7, 1), sistema_rega="6", cantidade=4,
             unidade="3",
             leiras=[RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]),
        Analise(horta_id=horta.id, material_analizado="3", data_mostraxe=date(2026, 2, 1),
                parcela_id=parcela.id, ph=5.6),
        # fóra do período: non debe saír
        Rega(horta_id=horta.id, data_inicio=date(2025, 7, 1),
             data_fin=date(2025, 7, 1), sistema_rega="6", cantidade=9,
             unidade="3",
             leiras=[RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]),
    ])
    session.commit()
    # A folla 5 (colleita comercializada) sae das vendas dos lotes de colleitas
    quen = session.query(Persoa).filter_by(horta_id=horta.id).first().id
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=1.5, unidade="t",
        lote="2026-PATACA-001", persoa_id=quen), hoxe=date(2026, 10, 28))
    crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2026, 9, 2), tipo="venda", cantidade=1.5,
        unidade="t", canle="almacen", persoa_id=quen,
        comprador_id=crear_contacto(session, ana, horta.id, "Coop", "cliente").id),
        hoxe=date(2026, 10, 28))
    return ana, horta


def _libro(session, ana, horta):
    datos = xerar_caderno(session, ana, horta.id, date(2026, 1, 1), date(2026, 12, 31))
    return load_workbook(BytesIO(datos))


def _filas(ws):
    return [list(f) for f in ws.iter_rows(min_row=5, values_only=True)]


def test_ten_as_seccions_do_modelo_da_xunta(session):
    ana, horta = _escenario(session)
    libro = _libro(session, ana, horta)
    assert libro.sheetnames == ["1 Información xeral", "2 Parcelas", "3 Tratamentos",
                                "4 Análises", "5 Colleita", "6 Solos", "7 Fertilización",
                                "8 Rega", "9 Labores (CUE)"]


def test_contido_de_cada_seccion(session):
    ana, horta = _escenario(session)
    libro = _libro(session, ana, horta)
    parcela = _filas(libro["2 Parcelas"])[0]
    assert parcela[0] == 1 and parcela[10] == 0.2 and parcela[11] == "Pataca"
    fert = _filas(libro["7 Fertilización"])[0]
    assert fert[5] == "Abonado de fondo" and fert[7] == "NPK 15-15-15"
    assert fert[22] == 0.2 and fert[23:26] == [30.0, 30.0, 30.0]  # 200 kg/ha ao 15 %
    assert any(f[:2] == ["Plan de abonado de cultivos", "SI"] for f in _filas(
        libro["7 Fertilización"]))
    rega = _filas(libro["8 Rega"])
    assert len(rega) == 1 and rega[0][4] == 20.0  # 4 m³ en 0,2 ha
    colleita = _filas(libro["5 Colleita"])[0]
    assert colleita[2] == 1500.0 and colleita[5] == "2026-PATACA-001"
    solo = _filas(libro["6 Solos"])[0]
    assert solo[0] == "Leira" and solo[2] == 5.6


def test_permisos_e_datas(session):
    ana, horta = _escenario(session)
    allea = _usuario(session, "outra@example.com")
    with pytest.raises(PermisoDenegadoError):
        xerar_caderno(session, allea, horta.id, date(2026, 1, 1), date(2026, 12, 31))
    with pytest.raises(OperacionNonPermitidaError, match="anterior"):
        xerar_caderno(session, ana, horta.id, date(2026, 12, 31), date(2026, 1, 1))

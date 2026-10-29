"""Os datos do CUE co formato oficial e o que lles falta, por traballo
."""

import json
from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex
from horta.models.cultivo import Cultivo
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cue import excel_xeaga, json_cue, xerar_cue
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.leiras import LeiraTraballo
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.persoas import crear_contacto, crear_persoa
from horta.services.regas import DatosRega, crear_rega

HOXE = date(2026, 10, 29)
DESDE, ATA = date(2026, 1, 1), date(2026, 12, 31)


def _escenario(session, sigpac=True):
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="e" * 64, filas=0)
    session.add(version)
    session.flush()
    session.add(CultivoSiex(codigo=37, nome_oficial="TOMATE", version_id=version.id))
    session.add(CatalogoValor(catalogo="sistema_rega", codigo="6", descricion="Goteo",
                              version_id=version.id))
    session.flush()
    variedade = VariedadeSiex(cultivo_codigo=37, codigo=1, nome_oficial="SIN VARIEDAD",
                              version_id=version.id)
    session.add(variedade)
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta", uso_profesional=True)
    actualizar_horta(session, ana, horta, codigo_reaga="ES150010000001")
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="12345678Z")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).first()
    leiras = []
    for n in (1, 2):
        parcela = Parcela(horta_id=horta.id, nome=f"Leira {n}", estado="activa",
                          secano_regadio=SecanoRegadio.REGADIO)
        if sigpac:
            parcela.sigpac_provincia, parcela.sigpac_concello = "15", "078"
            parcela.sigpac_agregado, parcela.sigpac_zona = "0", "0"
            parcela.sigpac_poligono, parcela.sigpac_parcela = "12", str(100 + n)
            parcela.sigpac_subparcela = "1"
        session.add(parcela)
        session.flush()
        cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate", cultivo_siex_codigo=37,
                          variedade_siex_id=variedade.id, superficie_ha=0.1,
                          data_inicio=date(2026, 4, 1), sistema_cultivo="1")
        session.add(cultivo)
        leiras.append(cultivo)
    session.commit()
    return ana, horta, quen, leiras


def test_rega_colleita_e_venda_completas_non_faltan(session):
    ana, horta, quen, (uno, dous) = _escenario(session)
    crear_rega(session, ana, DatosRega(
        leiras=[LeiraTraballo(uno.id), LeiraTraballo(dous.id)], data_inicio=date(2026, 6, 1),
        sistema_rega="6", cantidade=20, unidade="3", persoa_id=quen.id), hoxe=HOXE)
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=uno.id, data=date(2026, 8, 1), cantidade=1.5, unidade="t", lote="T-1",
        persoa_id=quen.id), hoxe=HOXE)
    bar = crear_contacto(session, ana, horta.id, "Bar Central", "cliente", nif="87654321X")
    crear_saida(session, ana, DatosSaida(
        lote_id=colleita.lote_id, data=date(2026, 8, 2), tipo="venda", cantidade=500,
        unidade="kg", canle="tenda", comprador_id=bar.id, persoa_id=quen.id), hoxe=HOXE)
    cue = xerar_cue(session, ana, horta.id, DESDE, ATA)
    actividades = cue.datos["ActividadesExplotacion"]
    # As dúas leiras son do mesmo produto e variedade: unha soa rega con dúas DGC
    [rega] = actividades["Riego"]
    assert rega["Cantidad"] == 20 and len(rega["DGCs"]) == 2
    [colleita_cue] = actividades["Cosecha"]
    assert (colleita_cue["Cantidad"], colleita_cue["Unidad"]) == (1.5, 6)
    [venda] = actividades["ComercializacionVD"]
    assert (venda["TipoVenta"], venda["NumLote"], venda["IdComprador"]) == (0, "T-1",
                                                                          "87654321X")
    assert cue.faltas() == []
    assert json.loads(json_cue(cue))["CodigoRea"] == "ES150010000001"
    libro = load_workbook(BytesIO(excel_xeaga(cue)))
    assert libro.sheetnames == ["Leiras (DGC)", "Sementeira e plantación", "Rega", "Colleita",
                                "Venda directa e comercializada"]


def test_o_que_falta_dise_por_traballo(session):
    ana, horta, quen, (uno, _) = _escenario(session, sigpac=False)
    rega = crear_rega(session, ana, DatosRega(cultivo_id=uno.id, data_inicio=date(2026, 6, 1),
                                              persoa_id=quen.id), hoxe=HOXE)
    faltas = {(f.orixe.tipo, f.orixe.id, f.falta) for f in
              xerar_cue(session, ana, horta.id, DESDE, ATA).faltas()}
    assert ("rega", rega.id, "o sistema de rega") in faltas
    assert ("rega", rega.id, "a cantidade") in faltas
    assert ("cultivo", uno.id, "o polígono SIGPAC") in faltas

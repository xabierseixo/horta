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
from horta.services.instalacions import crear_instalacion
from horta.services.leiras import LeiraTraballo
from horta.services.lotes import DatosSaida, crear_saida
from horta.services.persoas import crear_contacto, crear_persoa
from horta.services.regas import DatosRega, crear_rega
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    crear_tratamento_instalacion,
)

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


def test_tratamentos_de_postcolleita_e_de_local_van_ao_cue(session):
    ana, horta, quen, _ = _escenario(session)
    alpendre = crear_instalacion(session, ana, horta.id, "almacen", "Alpendre")
    comun = {"data": date(2026, 9, 1), "nome_comercial": "Produto X", "num_rexistro": "ES-1",
             "cantidade_utilizada": 0.5, "persoa_id": quen.id}
    postcolleita = crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
        tipo="postcolleita", obxecto="Patacas", produto_vexetal=37, cantidade_tratada=2,
        **comun), hoxe=HOXE)
    local = crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
        tipo="local", obxecto="Alpendre", instalacion_id=alpendre.id, cantidade_tratada=30,
        **comun), hoxe=HOXE)
    crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
        tipo="transporte", obxecto="Remolque", **comun), hoxe=HOXE)
    actividades = xerar_cue(session, ana, horta.id, DESDE, ATA).datos["ActividadesExplotacion"]
    [pc] = actividades["TratamientosPostCosecha"]
    assert (pc["IdAjenaTratamPostco"], pc["ProductoVegetal"], pc["Cantidad"]) == (
        postcolleita.id, 37, 2)
    assert pc["ProductosFito"] == [{"NumRegistro": "ES-1", "Cantidad": 0.5}]
    # O transporte non ten bloque no CUE (só no caderno da Xunta)
    [edif] = actividades["TratamientosEdifInstalaciones"]
    assert edif["IdAjenaTratamEdif"] == local.id
    assert edif["Edificaciones"] == [{"IdEdificacion": alpendre.id, "Volumen": 30, "Unidad": 3}]


def test_datas_da_leira_segundo_o_fega(session):
    """DT 3.11 §3.4: empeza coa preparación do terreo e remata co último traballo."""
    from horta.models.labor import Labor, LaborCultivo
    from horta.services.cue import datas_dgc

    ana, horta, quen, (uno, _) = _escenario(session)
    for inicio, fin in ((date(2026, 3, 10), date(2026, 3, 12)),
                        (date(2026, 9, 20), date(2026, 9, 25))):
        session.add(Labor(horta_id=horta.id, data_inicio=inicio, data_fin=fin, tipo_labor="1",
                          leiras=[LaborCultivo(cultivo_id=uno.id)]))
    session.commit()
    # Sen data de fin, o cultivo segue aberto
    assert datas_dgc(session, uno.id) == (date(2026, 3, 10), None)
    crear_colleita(session, ana, DatosColleita(
        cultivo_id=uno.id, data=date(2026, 8, 1), cantidade=1.5, unidade="t", lote="T-1",
        persoa_id=quen.id), hoxe=HOXE)
    uno.data_fin = date(2026, 8, 31)
    session.commit()
    assert datas_dgc(session, uno.id) == (date(2026, 3, 10), date(2026, 9, 25))
    cue = xerar_cue(session, ana, horta.id, DESDE, ATA)
    alta = next(a for a in cue.datos["DatosExplotacion"]["AltaDGC"]
                if a["CodigoDGCAjena"] == uno.id)
    assert (alta["FechaInicio"], alta["FechaFin"]) == ("10/03/2026", "25/09/2026")


def test_traballo_con_maquina_sen_datos_cue_avisa_en_faltas(session):
    from horta.models.labor import Labor, LaborCultivo
    from horta.services.faltas_caderno import faltas_caderno
    from horta.services.maquinaria import actualizar_maquina, crear_maquina

    ana, horta, quen, (uno, _) = _escenario(session)
    version = session.query(CatalogoVersion).first()
    for catalogo, codigo, desc in (
        ("tipo_maquinaria_une", "1.1", "Tractores de rodas"),
        ("unidade_medida", "40", "Cabalo de vapor (CV)"),
        ("tipo_enerxia", "1", "Diésel"),
    ):
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=desc,
                                  version_id=version.id))
    session.commit()

    tractor = crear_maquina(session, ana, horta.id, "Tractor")
    labor = Labor(horta_id=horta.id, data_inicio=date(2026, 5, 10), tipo_labor="1",
                  maquina_id=tractor.id, num_repeticions=1, duracion_h=2.0, persoa_id=quen.id,
                  leiras=[LaborCultivo(cultivo_id=uno.id, superficie_ha=0.1)])
    session.add(labor)
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=uno.id, data=date(2026, 8, 1), cantidade=1.5, unidade="t", lote="T-1",
        persoa_id=quen.id, maquina_id=tractor.id, num_repeticions=1, duracion_h_ha=1.5), hoxe=HOXE)

    faltas = {(f.orixe.tipo, f.orixe.id, f.falta) for f in
              xerar_cue(session, ana, horta.id, DESDE, ATA).faltas()}
    for tipo, rex_id in (("labor", labor.id), ("colleita", colleita.id)):
        assert (tipo, rex_id, "o tipo de máquina (UNE)") in faltas
        assert (tipo, rex_id, "a potencia da máquina") in faltas
        assert (tipo, rex_id, "a unidade da potencia") in faltas
        assert (tipo, rex_id, "o tipo de enerxía") in faltas
    assert any(f.traballo == "Labores" and "máquina" in f.dato
               for f in faltas_caderno(session, ana, horta.id, DESDE, ATA))

    actualizar_maquina(session, ana, tractor, tipo_une="1.1", potencia=75.0,
                       unidade_potencia="40", tipo_enerxia="1")
    assert xerar_cue(session, ana, horta.id, DESDE, ATA).faltas() == []
    assert not any(f.traballo == "Labores" and "máquina" in f.dato
                   for f in faltas_caderno(session, ana, horta.id, DESDE, ATA))

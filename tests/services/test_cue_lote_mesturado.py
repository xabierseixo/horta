"""Probas das vendas no CUE con lotes procedentes de mesturas ou transformacións
(tarefa 136, DT 3.11)."""

from datetime import date

from horta.models.catalogo import (
    CatalogoValor,
    CatalogoVersion,
    CultivoSiex,
    VariedadeSiex,
)
from horta.models.cultivo import Cultivo
from horta.models.lote import (
    Lote,
    Mestura,
    MesturaOrixe,
    Transformacion,
    TransformacionEntrada,
)
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cue import cultivos_do_lote, xerar_cue
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.lotes import DatosSaida, crear_saida, ficha_para
from horta.services.persoas import crear_contacto, crear_persoa

HOXE = date(2026, 10, 29)
DESDE, ATA = date(2026, 1, 1), date(2026, 12, 31)


def _escenario(session):
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="e" * 64, filas=0)
    session.add(version)
    session.flush()
    session.add(CultivoSiex(codigo=37, nome_oficial="TOMATE", version_id=version.id))
    session.add(CultivoSiex(codigo=38, nome_oficial="PEMENTO", version_id=version.id))
    session.add(CatalogoValor(catalogo="sistema_rega", codigo="6", descricion="Goteo",
                              version_id=version.id))
    session.flush()
    var_tomate = VariedadeSiex(cultivo_codigo=37, codigo=1, nome_oficial="SIN VARIEDAD",
                               version_id=version.id)
    var_pemento = VariedadeSiex(cultivo_codigo=38, codigo=1, nome_oficial="SIN VARIEDAD",
                                version_id=version.id)
    session.add_all([var_tomate, var_pemento])

    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()

    horta = crear_horta(session, ana, "Horta", uso_profesional=True)
    actualizar_horta(session, ana, horta, codigo_reaga="ES150010000001")
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="12345678Z")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).first()

    p1 = Parcela(horta_id=horta.id, nome="Leira 1", estado="activa",
                 secano_regadio=SecanoRegadio.REGADIO,
                 sigpac_provincia="15", sigpac_concello="078",
                 sigpac_agregado="0", sigpac_zona="0",
                 sigpac_poligono="12", sigpac_parcela="101", sigpac_subparcela="1")
    p2 = Parcela(horta_id=horta.id, nome="Leira 2", estado="activa",
                 secano_regadio=SecanoRegadio.REGADIO,
                 sigpac_provincia="15", sigpac_concello="078",
                 sigpac_agregado="0", sigpac_zona="0",
                 sigpac_poligono="12", sigpac_parcela="102", sigpac_subparcela="1")
    session.add_all([p1, p2])
    session.flush()

    c1 = Cultivo(parcela_id=p1.id, especie="Tomate", cultivo_siex_codigo=37,
                 variedade_siex_id=var_tomate.id, superficie_ha=0.1,
                 data_inicio=date(2026, 4, 1), sistema_cultivo="1")
    c2 = Cultivo(parcela_id=p2.id, especie="Pemento", cultivo_siex_codigo=38,
                 variedade_siex_id=var_pemento.id, superficie_ha=0.1,
                 data_inicio=date(2026, 4, 1), sistema_cultivo="1")
    session.add_all([c1, c2])
    session.commit()

    return ana, horta, quen, c1, c2


def test_venda_lote_mesturado_ten_dgcs_dos_dous_cultivos(session):
    """Dous lotes con colleitas distintas mestúranse nun terceiro: a venda ten
    os dous cultivos."""
    ana, horta, quen, c1, c2 = _escenario(session)

    col1 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c1.id, data=date(2026, 8, 1), cantidade=50.0, unidade="kg",
        lote="LOTE-TOM", persoa_id=quen.id), hoxe=HOXE)
    col2 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c2.id, data=date(2026, 8, 2), cantidade=50.0, unidade="kg",
        lote="LOTE-PEM", persoa_id=quen.id), hoxe=HOXE)

    ficha3 = ficha_para(session, horta.id, "Mestura Tomate e Pemento", "kg")
    lote3 = Lote(horta_id=horta.id, codigo="LOTE-MESTURA", produto="Mestura Tomate e Pemento",
                 unidade="kg", produto_venda_id=ficha3.id, data=date(2026, 8, 3))
    session.add(lote3)
    session.flush()

    mestura = Mestura(
        horta_id=horta.id, data=date(2026, 8, 3), lote_id=lote3.id,
        orixes=[
            MesturaOrixe(lote_id=col1.lote_id, cantidade=10.0),
            MesturaOrixe(lote_id=col2.lote_id, cantidade=10.0),
        ],
    )
    session.add(mestura)
    session.commit()

    bar = crear_contacto(session, ana, horta.id, "Bar Central", "cliente", nif="87654321X")
    crear_saida(session, ana, DatosSaida(
        lote_id=lote3.id, data=date(2026, 8, 4), tipo="venda", cantidade=15.0,
        unidade="kg", canle="tenda", comprador_id=bar.id, persoa_id=quen.id), hoxe=HOXE)

    cue = xerar_cue(session, ana, horta.id, DESDE, ATA)
    actividades = cue.datos["ActividadesExplotacion"]

    [venda] = actividades["ComercializacionVD"]
    assert venda["NumLote"] == "LOTE-MESTURA"
    assert len(venda["DGCs"]) == 2
    dgcs = {d["CodigoDGCAjena"] for d in venda["DGCs"]}
    assert dgcs == {c1.id, c2.id}

    altas = {a["CodigoDGCAjena"] for a in cue.datos["DatosExplotacion"]["AltaDGC"]}
    assert {c1.id, c2.id}.issubset(altas)


def test_venda_lote_transformado_recursivo(session):
    """Unha transformación sobre un lote mesturado colle os cultivos orixinais cara atrás."""
    ana, horta, quen, c1, c2 = _escenario(session)

    col1 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c1.id, data=date(2026, 8, 1), cantidade=50.0, unidade="kg",
        lote="L-TOM", persoa_id=quen.id), hoxe=HOXE)
    col2 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c2.id, data=date(2026, 8, 2), cantidade=50.0, unidade="kg",
        lote="L-PEM", persoa_id=quen.id), hoxe=HOXE)

    ficha_m = ficha_para(session, horta.id, "Mestura", "kg")
    lote_m = Lote(horta_id=horta.id, codigo="L-MEST", produto="Mestura",
                  unidade="kg", produto_venda_id=ficha_m.id, data=date(2026, 8, 3))
    session.add(lote_m)
    session.flush()

    mestura = Mestura(
        horta_id=horta.id, data=date(2026, 8, 3), lote_id=lote_m.id,
        orixes=[
            MesturaOrixe(lote_id=col1.lote_id, cantidade=10.0),
            MesturaOrixe(lote_id=col2.lote_id, cantidade=10.0),
        ],
    )
    session.add(mestura)
    session.flush()

    ficha_t = ficha_para(session, horta.id, "Salsa", "kg")
    lote_t = Lote(horta_id=horta.id, codigo="L-SALSA", produto="Salsa",
                  unidade="kg", produto_venda_id=ficha_t.id, data=date(2026, 8, 4))
    session.add(lote_t)
    session.flush()

    transformacion = Transformacion(
        horta_id=horta.id, data=date(2026, 8, 4), lote_id=lote_t.id, cantidade=15.0,
        entradas=[TransformacionEntrada(lote_id=lote_m.id, cantidade=15.0)],
    )
    session.add(transformacion)
    session.commit()

    bar = crear_contacto(session, ana, horta.id, "Restaurante", "cliente", nif="11223344Y")
    crear_saida(session, ana, DatosSaida(
        lote_id=lote_t.id, data=date(2026, 8, 5), tipo="venda", cantidade=10.0,
        unidade="kg", canle="tenda", comprador_id=bar.id, persoa_id=quen.id), hoxe=HOXE)

    cue = xerar_cue(session, ana, horta.id, DESDE, ATA)
    [venda] = cue.datos["ActividadesExplotacion"]["ComercializacionVD"]
    assert venda["NumLote"] == "L-SALSA"
    assert {d["CodigoDGCAjena"] for d in venda["DGCs"]} == {c1.id, c2.id}


def test_mestura_ou_lote_de_baixa_ignorado(session):
    """Mesturas ou lotes de orixe dados de baixa non deben achegar cultivos."""
    ana, horta, quen, c1, c2 = _escenario(session)

    col1 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c1.id, data=date(2026, 8, 1), cantidade=30.0, unidade="kg",
        lote="L-ACTIVO", persoa_id=quen.id), hoxe=HOXE)
    col2 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c2.id, data=date(2026, 8, 2), cantidade=30.0, unidade="kg",
        lote="L-BAIXA", persoa_id=quen.id), hoxe=HOXE)

    # Marcamos o segundo lote como de baixa
    lote2 = session.get(Lote, col2.lote_id)
    assert lote2 is not None
    lote2.baixa = True

    ficha3 = ficha_para(session, horta.id, "Mestura 3", "kg")
    lote3 = Lote(horta_id=horta.id, codigo="L-MEST-3", produto="Mestura 3",
                 unidade="kg", produto_venda_id=ficha3.id, data=date(2026, 8, 3))
    session.add(lote3)
    session.flush()

    mestura = Mestura(
        horta_id=horta.id, data=date(2026, 8, 3), lote_id=lote3.id,
        orixes=[
            MesturaOrixe(lote_id=col1.lote_id, cantidade=5.0),
            MesturaOrixe(lote_id=col2.lote_id, cantidade=5.0),
        ],
    )
    session.add(mestura)
    session.commit()

    cultivos = cultivos_do_lote(session, lote3.id)
    assert cultivos == {c1.id}

    # Agora damos de baixa a mestura enteira
    mestura.baixa = True
    session.commit()
    assert cultivos_do_lote(session, lote3.id) == set()


def test_ciclo_de_mesturas_non_provoca_bucle_infinito(session):
    """Un ciclo artificial entre lotes non debe colgar a recursión."""
    ana, horta, quen, c1, _ = _escenario(session)

    col1 = crear_colleita(session, ana, DatosColleita(
        cultivo_id=c1.id, data=date(2026, 8, 1), cantidade=30.0, unidade="kg",
        lote="L-CICLO-1", persoa_id=quen.id), hoxe=HOXE)

    ficha_b = ficha_para(session, horta.id, "Lote B", "kg")
    lote_b = Lote(horta_id=horta.id, codigo="L-CICLO-2", produto="Lote B",
                  unidade="kg", produto_venda_id=ficha_b.id, data=date(2026, 8, 2))
    session.add(lote_b)
    session.flush()

    # Lote 1 mesturado en Lote B, e Lote B mesturado en Lote 1
    m1 = Mestura(horta_id=horta.id, data=date(2026, 8, 2), lote_id=lote_b.id,
                 orixes=[MesturaOrixe(lote_id=col1.lote_id, cantidade=5.0)])
    m2 = Mestura(horta_id=horta.id, data=date(2026, 8, 2), lote_id=col1.lote_id,
                 orixes=[MesturaOrixe(lote_id=lote_b.id, cantidade=5.0)])
    session.add_all([m1, m2])
    session.commit()

    cultivos = cultivos_do_lote(session, lote_b.id)
    assert cultivos == {c1.id}

"""Probas do servizo de visitas de campo do persoal asesor técnico (mellora N7)."""

from datetime import date, time, timedelta
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.observacion import ObservacionPraga
from horta.models.recomendacion import Recomendacion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fotos import gardar_foto, listar_fotos
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.observacions import crear_observacion
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
from horta.services.recomendacions import crear_recomendacion
from horta.services.tratamentos_fito import LinhaCultivo, LinhaProduto, Problema
from horta.services.visitas import (
    actualizar_visita,
    contido_visita,
    crear_visita,
    dar_de_baixa_visita,
    informe_visita,
    ligar_observacion,
    ligar_recomendacion,
    listar_visitas,
    obter_visita,
    proximas_visitas,
)

D = date(2026, 5, 10)


@pytest.fixture(autouse=True)
def _cultivos_siex(cultivos_siex):
    cultivos_siex(101)


def _usuario(session, email: str) -> Usuario:
    u = Usuario(
        nome=email,
        email=email,
        password_hash="x",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca", cultivo_siex_codigo=101)
    bieito = crear_persoa(
        session,
        ana,
        horta.id,
        "Bieito",
        papeis={"asesor"},
        ropo_numero="2",
        ropo_caducidade=D,
    )
    xan = crear_persoa(
        session,
        ana,
        horta.id,
        "Xan",
        papeis={"traballador"},
    )
    return ana, horta, parcela, cultivo, bieito, xan


def test_crear_visita_correcta(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    proxima = D + timedelta(days=10)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        hora_inicio=time(9, 30),
        estado_xeral="Bo desenvolvemento vexetativo",
        conclusions="Manter a rega e vixiar posible mildio",
        proxima_visita=proxima,
    )

    assert visita.id is not None
    assert visita.horta_id == horta.id
    assert visita.asesor_persoa_id == bieito.id
    assert visita.data == D
    assert visita.hora_inicio == time(9, 30)
    assert visita.cultivos == [cultivo.id]
    assert visita.estado_xeral == "Bo desenvolvemento vexetativo"
    assert visita.conclusions == "Manter a rega e vixiar posible mildio"
    assert visita.proxima_visita == proxima
    assert visita.creado_por == ana.id
    assert visita.baixa is False


def test_crear_asesor_sen_papel_rexeitase(session):
    ana, horta, _, cultivo, _, xan = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="asesor"):
        crear_visita(
            session,
            ana,
            horta.id,
            asesor_persoa_id=xan.id,
            data=D,
            cultivos=[cultivo.id],
        )


def test_crear_asesor_doutra_horta_rexeitase(session):
    ana, horta, _, cultivo, _, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra Horta")
    asesor_outra = crear_persoa(
        session,
        ana,
        outra.id,
        "Asesor Outra",
        papeis={"asesor"},
        ropo_numero="9",
    )
    with pytest.raises(OperacionNonPermitidaError, match="asesor"):
        crear_visita(
            session,
            ana,
            horta.id,
            asesor_persoa_id=asesor_outra.id,
            data=D,
            cultivos=[cultivo.id],
        )


def test_crear_cultivo_doutra_horta_rexeitase(session):
    ana, horta, _, _, bieito, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra Horta")
    p_outra = crear_parcela(session, ana, outra.id, "P2")
    c_outra = crear_cultivo(session, ana, p_outra.id, "Cenoria")
    with pytest.raises(
        OperacionNonPermitidaError, match="non pertence a esta explotación"
    ):
        crear_visita(
            session,
            ana,
            horta.id,
            asesor_persoa_id=bieito.id,
            data=D,
            cultivos=[c_outra.id],
        )


def test_crear_proxima_visita_anterior_rexeitase(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="anterior"):
        crear_visita(
            session,
            ana,
            horta.id,
            asesor_persoa_id=bieito.id,
            data=D,
            cultivos=[cultivo.id],
            proxima_visita=D - timedelta(days=1),
        )


def test_lector_non_pode_crear(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_visita(
            session,
            carlos,
            horta.id,
            asesor_persoa_id=bieito.id,
            data=D,
            cultivos=[cultivo.id],
        )


def test_actualizar_visita(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        estado_xeral="Inicial",
    )

    actualizar_visita(
        session,
        ana,
        visita,
        estado_xeral="Actualizado",
        conclusions="Novas conclusións",
        proxima_visita=D + timedelta(days=7),
    )
    assert visita.estado_xeral == "Actualizado"
    assert visita.conclusions == "Novas conclusións"
    assert visita.proxima_visita == D + timedelta(days=7)

    # Actualizar pasando o id da visita
    actualizar_visita(
        session,
        ana,
        visita.id,
        estado_xeral="Por ID",
    )
    assert visita.estado_xeral == "Por ID"

    # Lector non pode actualizar
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        actualizar_visita(session, carlos, visita, estado_xeral="Outro")

    # Visita dada de baixa non se pode modificar
    dar_de_baixa_visita(session, ana, visita)
    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_visita(session, ana, visita, estado_xeral="Outro")


def test_dar_de_baixa_visita(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )

    # Lector non pode dar de baixa
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        dar_de_baixa_visita(session, carlos, visita)

    dar_de_baixa_visita(session, ana, visita)
    assert visita.baixa is True
    assert listar_visitas(session, ana, horta.id) == []
    assert obter_visita(session, ana, visita.id) is None


def test_listar_visitas(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    v1 = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D - timedelta(days=5),
        cultivos=[cultivo.id],
    )
    v2 = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )
    v3 = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D + timedelta(days=5),
        cultivos=[cultivo.id],
    )

    # Orde: das máis recentes ás máis antigas
    visitas = listar_visitas(session, ana, horta.id)
    assert [v.id for v in visitas] == [v3.id, v2.id, v1.id]

    # Filtro desde
    visitas_desde = listar_visitas(session, ana, horta.id, desde=D)
    assert [v.id for v in visitas_desde] == [v3.id, v2.id]

    # Filtro ata
    visitas_ata = listar_visitas(session, ana, horta.id, ata=D)
    assert [v.id for v in visitas_ata] == [v2.id, v1.id]

    # Lector pode listar
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    visitas_lector = listar_visitas(session, carlos, horta.id)
    assert len(visitas_lector) == 3


def test_proximas_visitas(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)

    # 1. Próxima visita dentro dos 14 días (en 5 días)
    v1 = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        proxima_visita=D + timedelta(days=5),
    )
    # 2. Próxima visita fóra dos 14 días (en 20 días)
    v2 = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        proxima_visita=D + timedelta(days=20),
    )
    # 3. Próxima visita no pasado
    crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D - timedelta(days=10),
        cultivos=[cultivo.id],
        proxima_visita=D - timedelta(days=2),
    )
    # 4. Sen próxima visita
    crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        proxima_visita=None,
    )
    # 5. Dada de baixa
    v5 = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        proxima_visita=D + timedelta(days=3),
    )
    dar_de_baixa_visita(session, ana, v5)

    proximas = proximas_visitas(session, ana, horta.id, hoxe=D, dias=14)
    assert len(proximas) == 1
    assert proximas[0].id == v1.id

    # Con dias=30 inclúe tamén v2
    proximas_mes = proximas_visitas(session, ana, horta.id, hoxe=D, dias=30)
    assert len(proximas_mes) == 2
    assert [v.id for v in proximas_mes] == [v1.id, v2.id]

    # Lector pode consultar
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    assert len(proximas_visitas(session, carlos, horta.id, hoxe=D, dias=14)) == 1


def test_gardar_foto_en_visita(session):
    ana, horta, _, cultivo, bieito, _ = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )

    imaxe_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00"
        b"\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    foto = gardar_foto(
        session,
        ana,
        horta.id,
        "visita",
        visita.id,
        imaxe_png,
        nome_orixinal="visita_campo.png",
        nota="Foto da visita",
        hoxe=D,
    )
    assert foto.id is not None
    assert foto.que == "visita"
    assert foto.ref_id == visita.id

    fotos = listar_fotos(session, ana, horta.id, "visita", visita.id)
    assert len(fotos) == 1
    assert fotos[0].id == foto.id


def test_visita_id_en_observacion_e_recomendacion(session):
    ana, horta, _, cultivo, bieito, xan = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )

    obs = ObservacionPraga(
        horta_id=horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="visual",
        persoa_id=xan.id,
        visita_id=visita.id,
    )
    session.add(obs)

    rec = Recomendacion(
        horta_id=horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[{"cultivo_id": cultivo.id}],
        problemas=[{"tipo": "praga", "codigo": "10"}],
        produtos=[{"tipo_produto": "1", "unidade": "5"}],
        visita_id=visita.id,
    )
    session.add(rec)
    session.commit()

    assert obs.visita_id == visita.id
    assert rec.visita_id == visita.id


def _catalogos(session) -> None:
    v = CatalogoVersion(
        catalogo="praga",
        nome_ficheiro="pragas.xlsx",
        sha256="0" * 64,
        filas=1,
    )
    session.add(v)
    session.flush()
    session.add(
        CatalogoValor(
            catalogo="praga",
            codigo="10",
            descricion="Escaravello da pataca",
            version_id=v.id,
        )
    )
    session.commit()


def test_ligar_observacion_e_recomendacion(session):
    _catalogos(session)
    ana, horta, _, cultivo, bieito, xan = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )
    obs = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=2.0,
        unidade_conto="individuos por planta",
        persoa_id=xan.id,
    )
    rec = crear_recomendacion(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=None)],
        problemas=[Problema(tipo="praga", codigo="10")],
        xustificacions=["Presenza"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5")],
    )

    assert obs.visita_id is None
    assert rec.visita_id is None

    ligar_observacion(session, ana, visita, obs)
    ligar_recomendacion(session, ana, visita, rec)

    assert obs.visita_id == visita.id
    assert rec.visita_id == visita.id

    # Ligar pasando os identificadores
    obs2 = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=1.0,
        unidade_conto="individuos por planta",
        persoa_id=xan.id,
    )
    ligar_observacion(session, ana, visita.id, obs2.id)
    assert obs2.visita_id == visita.id

    # Non se pode ligar cunha observación ou recomendación doutra horta
    outra = crear_horta(session, ana, "Outra Horta 2")
    p_outra = crear_parcela(session, ana, outra.id, "P2")
    c_outra = crear_cultivo(session, ana, p_outra.id, "Cenoria")
    bieito_outra = crear_persoa(
        session,
        ana,
        outra.id,
        "Asesor 2",
        papeis={"asesor"},
        ropo_numero="8",
    )
    obs_outra = crear_observacion(
        session,
        ana,
        outra.id,
        cultivo_id=c_outra.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=1.0,
        unidade_conto="individuos por planta",
        persoa_id=bieito_outra.id,
    )
    rec_outra = crear_recomendacion(
        session,
        ana,
        outra.id,
        asesor_persoa_id=bieito_outra.id,
        data=D,
        cultivos=[LinhaCultivo(cultivo_id=c_outra.id, superficie_ha=None)],
        problemas=[Problema(tipo="praga", codigo="10")],
        xustificacions=["Presenza"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5")],
    )

    with pytest.raises(
        OperacionNonPermitidaError, match="non pertence á mesma explotación"
    ):
        ligar_observacion(session, ana, visita, obs_outra)

    with pytest.raises(
        OperacionNonPermitidaError, match="non pertence á mesma explotación"
    ):
        ligar_recomendacion(session, ana, visita, rec_outra)

    # Lector non pode ligar
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        ligar_observacion(session, carlos, visita, obs)
    with pytest.raises(PermisoDenegadoError):
        ligar_recomendacion(session, carlos, visita, rec)


def test_crear_observacion_e_recomendacion_con_visita_id(session):
    _catalogos(session)
    ana, horta, _, cultivo, bieito, xan = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )
    obs = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=2.0,
        unidade_conto="individuos por planta",
        persoa_id=xan.id,
        visita_id=visita.id,
    )
    rec = crear_recomendacion(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=None)],
        problemas=[Problema(tipo="praga", codigo="10")],
        xustificacions=["Presenza"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5")],
        visita_id=visita.id,
    )
    assert obs.visita_id == visita.id
    assert rec.visita_id == visita.id

    # Visita doutra horta rexeitada
    outra = crear_horta(session, ana, "Outra Horta 3")
    asesor_outra = crear_persoa(
        session,
        ana,
        outra.id,
        "Asesor 3",
        papeis={"asesor"},
        ropo_numero="7",
    )
    p_outra = crear_parcela(session, ana, outra.id, "P3")
    c_outra = crear_cultivo(session, ana, p_outra.id, "Cenoria")
    v_outra = crear_visita(
        session,
        ana,
        outra.id,
        asesor_persoa_id=asesor_outra.id,
        data=D,
        cultivos=[c_outra.id],
    )

    with pytest.raises(
        OperacionNonPermitidaError, match="non pertence a esta explotación"
    ):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=D,
            problema_tipo="praga",
            problema_codigo="10",
            metodo="mostraxe",
            conto=2.0,
            unidade_conto="individuos por planta",
            visita_id=v_outra.id,
        persoa_id=xan.id,
    )

    with pytest.raises(
        OperacionNonPermitidaError, match="non pertence a esta explotación"
    ):
        crear_recomendacion(
            session,
            ana,
            horta.id,
            asesor_persoa_id=bieito.id,
            data=D,
            cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=None)],
            problemas=[Problema(tipo="praga", codigo="10")],
            xustificacions=["Presenza"],
            produtos=[LinhaProduto(tipo_produto="1", unidade="5")],
            visita_id=v_outra.id,
        )

    # Visita dada de baixa rexeitada
    dar_de_baixa_visita(session, ana, visita)
    with pytest.raises(
        OperacionNonPermitidaError, match="dada de baixa"
    ):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=D,
            problema_tipo="praga",
            problema_codigo="10",
            metodo="mostraxe",
            conto=2.0,
            unidade_conto="individuos por planta",
            visita_id=visita.id,
        persoa_id=xan.id,
    )


def test_contido_visita(session):
    _catalogos(session)
    ana, horta, _, cultivo, bieito, xan = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
    )
    obs = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=2.0,
        unidade_conto="individuos por planta",
        persoa_id=xan.id,
        visita_id=visita.id,
    )
    rec = crear_recomendacion(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=None)],
        problemas=[Problema(tipo="praga", codigo="10")],
        xustificacions=["Presenza"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5", nome_comercial="BioFito")],
        visita_id=visita.id,
    )

    # Observación e recomendación dadas de baixa non deben aparecer
    obs_baixa = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=1.0,
        unidade_conto="individuos por planta",
        persoa_id=xan.id,
        visita_id=visita.id,
    )
    obs_baixa.baixa = True
    rec_baixa = crear_recomendacion(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=None)],
        problemas=[Problema(tipo="praga", codigo="10")],
        xustificacions=["Presenza"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5")],
        visita_id=visita.id,
    )
    rec_baixa.baixa = True
    session.commit()

    cv = contido_visita(session, ana, visita.id)
    assert cv.visita.id == visita.id
    assert [o.id for o in cv.observacions] == [obs.id]
    assert [r.id for r in cv.recomendacions] == [rec.id]
    assert "Pataca" in cv.nomes_cultivos
    assert [c.id for c in cv.cultivos] == [cultivo.id]

    # Lector pode consultar contido
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    cv_lector = contido_visita(session, carlos, visita.id)
    assert cv_lector.visita.id == visita.id

    # Visita inexistente dá erro
    with pytest.raises(OperacionNonPermitidaError):
        contido_visita(session, ana, 99999)


def test_informe_visita(session):
    _catalogos(session)
    ana, horta, _, cultivo, bieito, xan = _escenario(session)
    visita = crear_visita(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[cultivo.id],
        hora_inicio=time(10, 0),
        estado_xeral="Vigor axeitado e bo desenvolvemento",
        conclusions="Revisar praga en dúas semanas",
        proxima_visita=D + timedelta(days=14),
    )
    crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=D,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="mostraxe",
        conto=3.0,
        unidade_conto="individuos por planta",
        persoa_id=xan.id,
        visita_id=visita.id,
    )
    crear_recomendacion(
        session,
        ana,
        horta.id,
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=None)],
        problemas=[Problema(tipo="praga", codigo="10")],
        xustificacions=["Presenza confirmada"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5", nome_comercial="BioFito")],
        valida_ata=D + timedelta(days=7),
        visita_id=visita.id,
    )

    xlsx_bytes = informe_visita(session, ana, visita.id)
    assert isinstance(xlsx_bytes, bytes)
    assert len(xlsx_bytes) > 0

    wb = load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    assert ws is not None

    valores = [
        str(cell.value)
        for row in ws.iter_rows()
        for cell in row
        if cell.value is not None
    ]
    texto_total = " ".join(valores)

    # Comprobar que leva o título, data, asesor, observación e recomendación
    assert "Informe da visita de campo" in texto_total
    assert "10/05/2026" in texto_total
    assert "Bieito" in texto_total
    assert "Escaravello da pataca" in texto_total or "10" in texto_total
    assert "BioFito" in texto_total or "pendente" in texto_total

    # Lector pode xerar o informe
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    lector_bytes = informe_visita(session, carlos, visita.id)
    assert len(lector_bytes) > 0

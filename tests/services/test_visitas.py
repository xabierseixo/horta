"""Probas do servizo de visitas de campo do persoal asesor técnico (mellora N7)."""

from datetime import date, time, timedelta

import pytest

from horta.models.horta import RolHorta
from horta.models.observacion import ObservacionPraga
from horta.models.recomendacion import Recomendacion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fotos import gardar_foto, listar_fotos
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
from horta.services.visitas import (
    actualizar_visita,
    crear_visita,
    dar_de_baixa_visita,
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

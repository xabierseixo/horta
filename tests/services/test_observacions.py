"""Probas do servizo de observacións e limiares de pragas (GIP)."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.observacions import (
    actualizar_observacion,
    crear_observacion,
    dar_de_baixa_limiar,
    dar_de_baixa_observacion,
    gardar_limiar,
    limiar_para,
    listar_limiares,
    listar_observacions,
    supera_limiar,
)
from horta.services.parcelas import crear_parcela


def _usuario(session, email):
    u = Usuario(
        nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True
    )
    session.add(u)
    session.commit()
    return u


def _catalogos(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [
        ("praga", "10"),
        ("praga", "11"),
        ("enfermidade", "20"),
        ("mala_herba", "30"),
        ("estado_fenoloxico", "6"),
    ]:
        session.add(
            CatalogoValor(
                catalogo=catalogo,
                codigo=codigo,
                descricion=codigo,
                version_id=v.id,
            )
        )
    session.commit()


def _escenario(session):
    _catalogos(session)
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=1.0)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca", cultivo_siex_codigo=101)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).first()
    return ana, horta, parcela, cultivo, persoa


def test_crear_observacion_correcto(session):
    ana, horta, _, cultivo, persoa = _escenario(session)
    d = date(2026, 5, 10)
    obs = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=d,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=5.0,
        unidade_conto="capturas por trampa",
        nivel="medio",
        estado_fenoloxico="6",
        notas="Trampa delta norte",
        persoa_id=persoa.id,
    )
    assert obs.id is not None
    assert obs.horta_id == horta.id
    assert obs.cultivo_id == cultivo.id
    assert obs.data == d
    assert obs.problema_tipo == "praga"
    assert obs.problema_codigo == "10"
    assert obs.metodo == "trampa"
    assert obs.conto == 5.0
    assert obs.unidade_conto == "capturas por trampa"
    assert obs.nivel == "medio"
    assert obs.estado_fenoloxico == "6"
    assert obs.notas == "Trampa delta norte"
    assert obs.persoa_id == persoa.id
    assert obs.creado_por == ana.id
    assert not obs.baixa


def test_crear_observacion_con_nivel_sen_conto(session):
    ana, horta, _, cultivo, persoa = _escenario(session)
    d = date(2026, 5, 10)
    obs = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=d,
        problema_tipo="enfermidade",
        problema_codigo="20",
        metodo="sintomas",
        nivel="baixo",
        persoa_id=persoa.id,
    )
    assert obs.conto is None
    assert obs.unidade_conto is None
    assert obs.nivel == "baixo"


def test_crear_observacion_validacions(session):
    ana, horta, _, cultivo, persoa = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    parcela_outra = crear_parcela(session, ana, outra.id, "P2")
    cultivo_outro = crear_cultivo(session, ana, parcela_outra.id, "Maceira")
    persoa_outra = session.query(Persoa).filter_by(horta_id=outra.id).first()

    # Cultivo doutra horta
    with pytest.raises(OperacionNonPermitidaError, match="cultivo"):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo_outro.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            conto=1.0,
            unidade_conto="capturas por trampa",
            persoa_id=persoa.id,
        )

    # Problema que non existe no catálogo
    with pytest.raises(OperacionNonPermitidaError):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="999",
            metodo="trampa",
            conto=1.0,
            unidade_conto="capturas por trampa",
            persoa_id=persoa.id,
        )

    # Sen conto nin nivel
    with pytest.raises(OperacionNonPermitidaError, match="conto ou o nivel"):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            persoa_id=persoa.id,
        )

    # Conto sen unidade
    with pytest.raises(OperacionNonPermitidaError, match="unidade de conto"):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            conto=5.0,
            persoa_id=persoa.id,
        )

    # Método non válido
    with pytest.raises(OperacionNonPermitidaError, match="Método"):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="inventado",
            conto=5.0,
            unidade_conto="capturas por trampa",
            persoa_id=persoa.id,
        )

    # Persoa doutra horta
    with pytest.raises(OperacionNonPermitidaError, match="persoa"):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            conto=5.0,
            unidade_conto="capturas por trampa",
            persoa_id=persoa_outra.id,
        )

    # Sen persoa
    with pytest.raises(OperacionNonPermitidaError, match="quen o fixo"):
        crear_observacion(
            session,
            ana,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            conto=5.0,
            unidade_conto="capturas por trampa",
            persoa_id=None,
        )


def test_lector_non_pode_crear(session):
    ana, horta, _, cultivo, persoa = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_observacion(
            session,
            bea,
            horta.id,
            cultivo_id=cultivo.id,
            data=date(2026, 5, 10),
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            conto=1.0,
            unidade_conto="capturas por trampa",
            persoa_id=persoa.id,
        )
    with pytest.raises(PermisoDenegadoError):
        gardar_limiar(
            session,
            bea,
            horta.id,
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            unidade_conto="capturas por trampa",
            valor=5.0,
            fonte="Guía GIP",
        )


def test_limiar_sen_fonte(session):
    ana, horta, _, _, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="fonte"):
        gardar_limiar(
            session,
            ana,
            horta.id,
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            unidade_conto="capturas por trampa",
            valor=5.0,
            fonte="",
        )
    with pytest.raises(OperacionNonPermitidaError, match="fonte"):
        gardar_limiar(
            session,
            ana,
            horta.id,
            problema_tipo="praga",
            problema_codigo="10",
            metodo="trampa",
            unidade_conto="capturas por trampa",
            valor=5.0,
            fonte="   ",
        )


def test_limiar_para_especifico_gana_ao_xeral(session):
    ana, horta, parcela, cultivo, _ = _escenario(session)
    outro_cultivo = crear_cultivo(session, ana, parcela.id, "Millo", cultivo_siex_codigo=202)
    cultivo_sen_siex = crear_cultivo(session, ana, parcela.id, "Tomate")

    # Limiar xeral (cultivo_siex_codigo=None)
    limiar_xeral = gardar_limiar(
        session,
        ana,
        horta.id,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        unidade_conto="capturas por trampa",
        valor=10.0,
        fonte="Guía xeral GIP MAPA 2020",
        cultivo_siex_codigo=None,
    )
    # Limiar específico para o cultivo de pataca (101)
    limiar_especifico = gardar_limiar(
        session,
        ana,
        horta.id,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        unidade_conto="capturas por trampa",
        valor=4.0,
        fonte="Guía GIP pataca 2021",
        cultivo_siex_codigo=101,
    )

    # Para a pataca gaña o específico (valor 4.0)
    resultado_pataca = limiar_para(
        session,
        horta.id,
        cultivo,
        "praga",
        "10",
        "trampa",
        "capturas por trampa",
    )
    assert resultado_pataca is not None
    assert resultado_pataca.id == limiar_especifico.id
    assert resultado_pataca.valor == 4.0

    # Para o millo, que non ten específico, devolve o xeral (valor 10.0)
    resultado_millo = limiar_para(
        session,
        horta.id,
        outro_cultivo,
        "praga",
        "10",
        "trampa",
        "capturas por trampa",
    )
    assert resultado_millo is not None
    assert resultado_millo.id == limiar_xeral.id
    assert resultado_millo.valor == 10.0

    # Para o cultivo sen siex devolve o xeral
    resultado_sen_siex = limiar_para(
        session,
        horta.id,
        cultivo_sen_siex,
        "praga",
        "10",
        "trampa",
        "capturas por trampa",
    )
    assert resultado_sen_siex is not None
    assert resultado_sen_siex.id == limiar_xeral.id

    # Se non hai limiar para ese problema, devolve None
    resultado_outro = limiar_para(
        session,
        horta.id,
        cultivo,
        "praga",
        "11",
        "trampa",
        "capturas por trampa",
    )
    assert resultado_outro is None


def test_supera_limiar(session):
    ana, horta, _, cultivo, persoa = _escenario(session)
    limiar = gardar_limiar(
        session,
        ana,
        horta.id,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        unidade_conto="capturas por trampa",
        valor=5.0,
        fonte="Guía GIP",
    )
    obs_supera = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=date(2026, 5, 10),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=5.0,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )
    assert supera_limiar(obs_supera, limiar) is True

    obs_maior = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=date(2026, 5, 11),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=8.0,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )
    assert supera_limiar(obs_maior, limiar) is True

    obs_menor = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=date(2026, 5, 12),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=4.9,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )
    assert supera_limiar(obs_menor, limiar) is False

    obs_sen_conto = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=date(2026, 5, 13),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="sintomas",
        nivel="alto",
        persoa_id=persoa.id,
    )
    assert supera_limiar(obs_sen_conto, limiar) is False
    assert supera_limiar(None, limiar) is False
    assert supera_limiar(obs_supera, None) is False


def test_actualizar_e_dar_de_baixa_observacion(session):
    ana, horta, _, cultivo, persoa = _escenario(session)
    obs = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo.id,
        data=date(2026, 5, 10),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=2.0,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )
    actualizar_observacion(
        session,
        ana,
        obs,
        conto=12.0,
        nivel="alto",
        notas="Aumento notable",
    )
    assert obs.conto == 12.0
    assert obs.nivel == "alto"
    assert obs.notas == "Aumento notable"

    dar_de_baixa_observacion(session, ana, obs)
    assert obs.baixa is True
    assert listar_observacions(session, ana, horta.id) == []

    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_observacion(session, ana, obs, conto=1.0)


def test_listar_observacions_orde_e_filtros(session):
    ana, horta, parcela, cultivo1, persoa = _escenario(session)
    cultivo2 = crear_cultivo(session, ana, parcela.id, "Millo")

    obs1 = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo1.id,
        data=date(2026, 5, 1),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=1.0,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )
    obs2 = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo2.id,
        data=date(2026, 5, 5),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=2.0,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )
    obs3 = crear_observacion(
        session,
        ana,
        horta.id,
        cultivo_id=cultivo1.id,
        data=date(2026, 5, 10),
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        conto=3.0,
        unidade_conto="capturas por trampa",
        persoa_id=persoa.id,
    )

    # Orde: das máis novas ás máis vellas
    todas = listar_observacions(session, ana, horta.id)
    assert [o.id for o in todas] == [obs3.id, obs2.id, obs1.id]

    # Filtro por cultivo
    do_cultivo1 = listar_observacions(session, ana, horta.id, cultivo_id=cultivo1.id)
    assert [o.id for o in do_cultivo1] == [obs3.id, obs1.id]

    # Filtro por datas
    desde = listar_observacions(session, ana, horta.id, desde=date(2026, 5, 5))
    assert [o.id for o in desde] == [obs3.id, obs2.id]

    ata = listar_observacions(session, ana, horta.id, ata=date(2026, 5, 5))
    assert [o.id for o in ata] == [obs2.id, obs1.id]


def test_gardar_listar_e_dar_de_baixa_limiar(session):
    ana, horta, _, _, _ = _escenario(session)
    limiar = gardar_limiar(
        session,
        ana,
        horta.id,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        unidade_conto="capturas por trampa",
        valor=5.0,
        fonte="Guía inicial",
    )
    assert limiar.valor == 5.0
    assert listar_limiares(session, ana, horta.id) == [limiar]

    # Actualizar o mesmo limiar
    gardar_limiar(
        session,
        ana,
        horta.id,
        problema_tipo="praga",
        problema_codigo="10",
        metodo="trampa",
        unidade_conto="capturas por trampa",
        valor=7.0,
        fonte="Guía actualizada",
    )
    limiares = listar_limiares(session, ana, horta.id)
    assert len(limiares) == 1
    assert limiares[0].valor == 7.0
    assert limiares[0].fonte == "Guía actualizada"

    # Dar de baixa
    dar_de_baixa_limiar(session, ana, limiar)
    assert listar_limiares(session, ana, horta.id) == []

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import Horta, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
from horta.services.tratamentos_fito import (
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaProduto,
    Problema,
    crear_tratamento_fito,
    dar_de_baixa_tratamento_fito,
    faltas_para_cue,
    listar_tratamentos_fito,
)

D = date(2026, 5, 10)


def _usuario(session, email):
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _catalogos(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("enfermidade", "10"), ("xustificacion", "1"),
                             ("tipo_produto", "1"), ("unidade_medida", "5"),
                             ("estado_fenoloxico", "6"), ("eficacia", "1")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=catalogo,
                                  version_id=v.id))
    session.add(CatalogoValor(catalogo="enfermidade", codigo="99", descricion="vella",
                              version_id=v.id, data_baixa=date(2026, 1, 1)))
    session.commit()


def _escenario(session, profesional=True):
    _catalogos(session)
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    session.get(Horta, horta.id).uso_profesional = profesional
    session.commit()
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=2000.0)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    xan = crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
                       ropo_caducidade=D)
    maquina = crear_maquina(session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1")
    return ana, horta, parcela, cultivo, xan, maquina


def _datos(cultivo, xan, maquina, **cambios):
    base = dict(
        data_inicio=D, data_fin=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=0.1, estado_fenoloxico="6")],
        problemas=[Problema(tipo="enfermidade", codigo="10")],
        xustificacions=["1"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5", num_rexistro="ES-1",
                               nome_comercial="Cobre", dose=2.0)],
        medidas=[],
        aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
        eficacia="1",
    )
    base.update(cambios)
    return DatosTratamento(**base)


def test_crear_tratamento_completo(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    t = crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    assert [c.cultivo_id for c in t.cultivos] == [cultivo.id]
    assert faltas_para_cue(t) == []
    assert listar_tratamentos_fito(session, ana, horta.id) == [t]


def test_ropo_que_caduca_o_mesmo_dia_e_valido(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))


def test_ropo_caducado_bloquea(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    datos = _datos(cultivo, xan, maquina, data_inicio=date(2026, 5, 11),
                   data_fin=date(2026, 5, 11))
    with pytest.raises(OperacionNonPermitidaError, match="carné ROPO de Xan caducou"):
        crear_tratamento_fito(session, ana, horta.id, datos)


def test_data_fin_anterior_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="data de fin"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, data_fin=date(2026, 5, 9)))


def test_dose_e_cantidade_a_vez_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    produto = LinhaProduto(tipo_produto="1", unidade="5", num_rexistro="ES-1", dose=1.0,
                           cantidade=3.0)
    with pytest.raises(OperacionNonPermitidaError, match="dose ou a cantidade"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, produtos=[produto]))


def test_sen_produto_nin_medida_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="produto ou unha medida"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, produtos=[]))


def test_codigo_de_baixa_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="de baixa"):
        crear_tratamento_fito(
            session, ana, horta.id,
            _datos(cultivo, xan, maquina, problemas=[Problema(tipo="enfermidade",
                                                              codigo="99")]))


def test_cultivos_distintos_rexeitanse(session):
    ana, horta, parcela, cultivo, xan, maquina = _escenario(session)
    outro = crear_cultivo(session, ana, parcela.id, "Tomate")
    linhas = [LinhaCultivo(cultivo.id, 0.1), LinhaCultivo(outro.id, 0.1)]
    with pytest.raises(OperacionNonPermitidaError, match="mesmo cultivo"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, cultivos=linhas))


def test_superficie_maior_ca_parcela_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)  # parcela de 2000 m² = 0,2 ha
    linhas = [LinhaCultivo(cultivo.id, 0.5)]
    with pytest.raises(OperacionNonPermitidaError, match="maior ca da parcela"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, cultivos=linhas))


def test_cultivo_doutra_horta_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    p2 = crear_parcela(session, ana, outra.id, "P2")
    c2 = crear_cultivo(session, ana, p2.id, "Pataca")
    with pytest.raises(OperacionNonPermitidaError, match="non pertence a esta horta"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina,
                                     cultivos=[LinhaCultivo(c2.id, 0.1)]))


def test_lector_non_pode_crear(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_tratamento_fito(session, carlos, horta.id, _datos(cultivo, xan, maquina))


def test_autoconsumo_con_datos_minimos(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session, profesional=False)
    datos = _datos(cultivo, xan, maquina, xustificacions=[], aplicadores=[], eficacia=None)
    t = crear_tratamento_fito(session, ana, horta.id, datos)
    assert "aplicador" in " ".join(faltas_para_cue(t))


def test_profesional_sen_aplicador_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="aplicador"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, aplicadores=[]))


def test_baixa_loxica(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    t = crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    dar_de_baixa_tratamento_fito(session, ana, t)
    assert listar_tratamentos_fito(session, ana, horta.id) == []
    assert t.baixa is True


def test_non_se_pode_eliminar_cultivo_con_tratamentos(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    with pytest.raises(OperacionNonPermitidaError, match="tratamentos fitosanitarios"):
        eliminar_cultivo(session, ana, cultivo)

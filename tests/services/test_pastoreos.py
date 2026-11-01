"""Pastoreo (CUE bloque 12): gando propio ou de terceiros nunha ou máis leiras, e o aviso do
prazo de seguridade dos tratamentos."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.fito_rexistro import FitoProduto, FitoUso
from horta.models.persoa import Persoa
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal, eliminar_animal
from horta.services.cultivos import actualizar_cultivo, crear_cultivo, eliminar_cultivo
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela
from horta.services.pastoreos import (
    AnimaisPastoreo,
    DatosPastoreo,
    LeiraPastoreo,
    actualizar_pastoreo,
    aviso_prazo_pastoreo,
    crear_pastoreo,
    dar_de_baixa_pastoreo,
    listar_pastoreos,
    no_pasto,
    nomes_leiras,
    sairon_do_pasto,
)
from horta.services.persoas import crear_contacto
from horta.services.tarefas import crear_tarefa, facer_tarefa, marcar_pendente

HOXE = date(2026, 10, 28)
ALTA = date(2026, 3, 1)
DIA = date(2026, 9, 1)


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo, texto in [("tipo_cobertura_solo", "3", "Espontánea"),
                                    ("tipo_cobertura_solo", "6", "Pastos"),
                                    ("especie_animal", "01", "Bovinos"),
                                    ("especie_animal", "18", "Abejas")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=texto,
                                  version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    parcela = crear_parcela(session, ana, horta.id, "Leira de abaixo", superficie=1.0)
    pasto = crear_cultivo(session, ana, parcela.id, "Pasto")
    actualizar_cultivo(session, ana, pasto, superficie_ha=0.8, tipo_cobertura_solo="6")
    vacas = crear_animal(session, ana, horta.id, "Vacas do monte", ALTA, cantidade=12)
    vacas.especie_codigo = "01"
    session.commit()
    return ana, horta, persoa, pasto, vacas


def _datos(horta, persoa, pasto, vacas, numero=12, inicio=DIA, **campos):
    return DatosPastoreo(horta_id=horta.id, data_inicio=inicio, persoa_id=persoa.id,
                         leiras=[LeiraPastoreo(cultivo_id=pasto.id)],
                         animais=[AnimaisPastoreo(numero=numero, animal_id=vacas.id)], **campos)


def test_levar_ao_pasto_e_sair(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    pa = crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas), hoxe=HOXE)
    # A superficie e a cobertura son as do cultivo
    assert (pa.leiras[0].superficie_ha, pa.leiras[0].tipo_cobertura) == (0.8, "6")
    assert no_pasto(session, ana, horta.id) == {vacas.id: pa}
    assert nomes_leiras(session, pa) == "Leira de abaixo"
    sairon_do_pasto(session, ana, pa, date(2026, 10, 15), hoxe=HOXE)
    assert pa.data_fin == date(2026, 10, 15)
    assert no_pasto(session, ana, horta.id) == {}
    with pytest.raises(OperacionNonPermitidaError, match="anterior"):
        sairon_do_pasto(session, ana, pa, date(2026, 8, 1), hoxe=HOXE)


def test_varias_leiras_e_animais_de_terceiros(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    outra = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Agra").id, "Pasto")
    datos = _datos(horta, persoa, pasto, vacas, numero=5)
    datos.leiras.append(LeiraPastoreo(cultivo_id=outra.id, superficie_ha=0.3,
                                      tipo_cobertura="3"))
    veciña = crear_contacto(session, ana, horta.id, "Rosa da Veiga", "explotacion",
                            rega="ES150000000001")
    datos.animais.append(AnimaisPastoreo(numero=20, propietario_id=veciña.id,
                                         especie_codigo="01"))
    pa = crear_pastoreo(session, ana, datos, hoxe=HOXE)
    assert [(le.superficie_ha, le.tipo_cobertura) for le in pa.leiras] == [(0.8, "6"),
                                                                           (0.3, "3")]
    assert [(a.animal_id, a.propietario_id, a.numero) for a in pa.animais] == [
        (vacas.id, None, 5), (None, veciña.id, 20)]
    datos.animais = datos.animais[1:]
    actualizar_pastoreo(session, ana, pa, datos, hoxe=HOXE)
    assert len(pa.animais) == 1
    assert listar_pastoreos(session, ana, horta.id, vacas.id) == []
    dar_de_baixa_pastoreo(session, ana, pa)
    assert listar_pastoreos(session, ana, horta.id) == []


@pytest.mark.parametrize("cambio, erro", [
    ({"leiras": []}, "leira"),
    ({"animais": []}, "animais"),
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="01")]}, "de quen son"),
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="18")]}, "especie"),
    ({"animais": [AnimaisPastoreo(numero=3, especie_codigo="99")]}, None),
    ({"data_inicio": date(2026, 10, 29)}, "futura"),
    ({"data_inicio": date(2026, 2, 1)}, "alta"),
    ({"data_fin": date(2026, 8, 1)}, "anterior"),
    ({"data_fin": date(2026, 10, 29)}, "futura"),
    ({"persoa_id": None}, None),
])
def test_datos_que_non_valen(session, cambio, erro):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    datos = _datos(horta, persoa, pasto, vacas)
    for campo, valor in cambio.items():
        setattr(datos, campo, valor)
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        crear_pastoreo(session, ana, datos, hoxe=HOXE)


def test_superficie_maior_ca_do_cultivo(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    datos = _datos(horta, persoa, pasto, vacas)
    datos.leiras = [LeiraPastoreo(cultivo_id=pasto.id, superficie_ha=2.0)]
    with pytest.raises(OperacionNonPermitidaError, match="superficie"):
        crear_pastoreo(session, ana, datos, hoxe=HOXE)


def test_non_van_mais_animais_dos_que_ten_o_grupo(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tiña 12"):
        crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas, numero=13), hoxe=HOXE)
    crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas, numero=8), hoxe=HOXE)
    # As outras 4 poden ir a outro pasto á vez, pero non 5
    crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas, numero=4,
                                        inicio=date(2026, 9, 10)), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="noutro pasto"):
        crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas, numero=1,
                                            inicio=date(2026, 9, 20)), hoxe=HOXE)


def test_aviso_de_prazo_de_seguridade(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    v = session.query(CatalogoVersion).first()
    session.add(FitoProduto(num_rexistro="ES-1", nome="HERBICIDA", estado="Vigente",
                            version_id=v.id))
    session.flush()
    session.add(FitoUso(num_rexistro="ES-1", codigo_cultivo="x", cultivo="c", codigo_agente="a",
                        agente="a", ps_tipo="dias", ps_dias=14))
    t = TratamentoFito(horta_id=horta.id, data_inicio=DIA, data_fin=DIA)
    t.cultivos = [TratamentoCultivo(cultivo_id=pasto.id)]
    t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1",
                                    nome_comercial="HERBICIDA")]
    session.add(t)
    session.commit()
    aviso = aviso_prazo_pastoreo(session, [pasto.id], date(2026, 9, 5))
    assert aviso and "HERBICIDA" in aviso and "15/09/2026" in aviso and "gando" in aviso
    assert aviso_prazo_pastoreo(session, [pasto.id], date(2026, 9, 15)) is None


def test_no_diario_e_como_tarefa(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Levar as vacas", tipo="pastoreo",
                          animal_id=vacas.id)
    pa = crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas), hoxe=HOXE)
    facer_tarefa(session, ana, tarefa, pa)
    traballos = [t for t in listar_traballos(session, ana, horta.id) if t.tipo == "pastoreo"]
    assert len(traballos) == 1
    assert traballos[0].que == "12 Vacas do monte · aínda no pasto"
    assert traballos[0].onde == "Pasto — Leira de abaixo"
    sairon_do_pasto(session, ana, pa, date(2026, 11, 15), hoxe=date(2026, 11, 20))
    traballos = [t for t in listar_traballos(session, ana, horta.id) if t.tipo == "pastoreo"]
    assert traballos[0].que == "12 Vacas do monte · ata o 15/11/2026"


def test_traballo_de_baixa_solta_a_tarefa(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Levar as vacas", tipo="pastoreo",
                          animal_id=vacas.id)
    pa = crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas), hoxe=HOXE)
    facer_tarefa(session, ana, tarefa, pa)
    with pytest.raises(OperacionNonPermitidaError, match="edita ese traballo"):
        marcar_pendente(session, ana, tarefa)
    dar_de_baixa_pastoreo(session, ana, pa)
    marcar_pendente(session, ana, tarefa)
    assert (tarefa.estado, tarefa.traballo_id) == ("pendente", None)


def test_non_se_borra_nada_con_pastoreo(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    crear_pastoreo(session, ana, _datos(horta, persoa, pasto, vacas), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="pastoreos"):
        eliminar_animal(session, ana, vacas)
    with pytest.raises(OperacionNonPermitidaError, match="pastoreos"):
        eliminar_cultivo(session, ana, pasto)
    from horta.models.parcela import Parcela
    with pytest.raises(OperacionNonPermitidaError, match="pastoreos"):
        eliminar_parcela(session, ana, session.get(Parcela, pasto.parcela_id))
    with pytest.raises(OperacionNonPermitidaError, match="pastoreos"):
        eliminar_horta(session, ana, horta)


def test_animais_doutra_persoa_levan_o_seu_rega(session):
    ana, horta, persoa, pasto, vacas = _escenario(session)
    sen_rega = crear_contacto(session, ana, horta.id, "Xan do Outeiro", "explotacion")
    datos = _datos(horta, persoa, pasto, vacas, numero=5)
    datos.animais.append(AnimaisPastoreo(numero=4, propietario_id=sen_rega.id,
                                         especie_codigo="01"))
    with pytest.raises(OperacionNonPermitidaError, match="REGA"):
        crear_pastoreo(session, ana, datos, hoxe=HOXE)

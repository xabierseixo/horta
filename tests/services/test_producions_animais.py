"""Produción dos animais: ovos, leite, mel... de cada grupo, co seu lote, e o aviso do tempo de
espera dos medicamentos."""

from datetime import date

import pytest

from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal, eliminar_animal
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.movementos_animais import DatosMovemento, crear_movemento
from horta.services.producions_animais import (
    DatosProducion,
    actualizar_producion,
    aviso_tempo_espera,
    crear_producion,
    dar_de_baixa_producion,
    listar_producions,
    produtos_da_especie,
    propor_lote,
)
from horta.services.tarefas import crear_tarefa, facer_tarefa

HOXE = date(2026, 10, 28)
ALTA = date(2026, 3, 1)


def _escenario(session, especie_codigo=None):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    galinas = crear_animal(session, ana, horta.id, "Galiñas", ALTA, cantidade=10)
    galinas.especie_codigo = especie_codigo
    session.commit()
    return ana, horta, persoa, galinas


def _ovos(galinas, persoa, cantidade=24.0, dia=date(2026, 9, 1), **campos):
    return DatosProducion(animal_id=galinas.id, data=dia, produto="ovos", cantidade=cantidade,
                          unidade="unidades", persoa_id=persoa.id, **campos)


def test_apuntar_editar_e_dar_de_baixa(session):
    ana, horta, persoa, galinas = _escenario(session)
    pr = crear_producion(session, ana, _ovos(galinas, persoa, retirada=2,
                                             data_fin=date(2026, 9, 7)), hoxe=HOXE)
    assert (pr.lote, pr.data_fin, pr.retirada) == ("2026-OVOS-001", date(2026, 9, 7), 2)
    actualizar_producion(session, ana, pr, _ovos(galinas, persoa, 30, lote=pr.lote),
                         hoxe=HOXE)
    assert (pr.cantidade, pr.data_fin, pr.retirada) == (30, date(2026, 9, 1), None)
    dar_de_baixa_producion(session, ana, pr)
    assert listar_producions(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError):
        actualizar_producion(session, ana, pr, _ovos(galinas, persoa, lote=pr.lote),
                             hoxe=HOXE)


def test_o_lote_proposto_non_repite_os_das_colleitas_nin_os_propios(session):
    ana, horta, persoa, galinas = _escenario(session)
    crear_producion(session, ana, _ovos(galinas, persoa), hoxe=HOXE)
    assert propor_lote(session, ana, horta.id, "ovos", date(2026, 9, 2)) == "2026-OVOS-002"
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_producion(session, ana, _ovos(galinas, persoa, lote="2026-OVOS-001"), hoxe=HOXE)


def test_un_lote_de_colleita_non_se_pode_repetir_na_producion(session):
    from horta.services.colleitas import DatosColleita, crear_colleita
    from horta.services.cultivos import crear_cultivo
    from horta.services.parcelas import crear_parcela

    ana, horta, persoa, galinas = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=100, unidade="kg",
        lote="L-1", persoa_id=persoa.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_producion(session, ana, _ovos(galinas, persoa, lote="L-1"), hoxe=HOXE)
    crear_producion(session, ana, _ovos(galinas, persoa, lote="L-2"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_colleita(session, ana, DatosColleita(
            cultivo_id=cultivo.id, data=date(2026, 9, 2), cantidade=50, unidade="kg",
            lote="L-2", persoa_id=persoa.id), hoxe=HOXE)


def test_so_os_produtos_da_especie(session):
    assert list(produtos_da_especie("18")) == ["mel", "cera", "outro"]
    assert "leite" not in produtos_da_especie("06")
    assert len(produtos_da_especie(None)) == 6
    ana, horta, persoa, galinas = _escenario(session, especie_codigo="06")
    with pytest.raises(OperacionNonPermitidaError, match="non o dá"):
        crear_producion(session, ana, DatosProducion(
            animal_id=galinas.id, data=date(2026, 9, 1), produto="leite", cantidade=5,
            unidade="litros", persoa_id=persoa.id), hoxe=HOXE)


@pytest.mark.parametrize("campos, erro", [
    ({"retirada": 30}, "retirado"),
    ({"cantidade": 0}, "maior que 0"),
    ({"dia": date(2026, 2, 1)}, "alta"),
    ({"dia": date(2026, 10, 29)}, "futura"),
    ({"data_fin": date(2026, 8, 1)}, "fin"),
    ({"unidade": "sacos"}, "Unidade"),
])
def test_datos_que_non_valen(session, campos, erro):
    ana, horta, persoa, galinas = _escenario(session)
    datos = _ovos(galinas, persoa, **{k: v for k, v in campos.items()
                                      if k in ("cantidade", "dia", "retirada", "data_fin")})
    if "unidade" in campos:
        datos.unidade = campos["unidade"]
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        crear_producion(session, ana, datos, hoxe=HOXE)


def test_despois_de_quedar_sen_animais_non_hai_produción(session):
    ana, horta, persoa, galinas = _escenario(session)
    crear_movemento(session, ana, DatosMovemento(
        animal_id=galinas.id, data=date(2026, 9, 1), tipo="saida", cantidade=10,
        persoa_id=persoa.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="sen animais"):
        crear_producion(session, ana, _ovos(galinas, persoa, dia=date(2026, 9, 2)), hoxe=HOXE)


def test_quen_o_fixo_e_obrigatorio(session):
    ana, horta, persoa, galinas = _escenario(session)
    datos = _ovos(galinas, persoa)
    datos.persoa_id = None
    with pytest.raises(OperacionNonPermitidaError):
        crear_producion(session, ana, datos, hoxe=HOXE)


def test_aviso_de_tempo_de_espera(session):
    ana, horta, persoa, galinas = _escenario(session)
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 9, 10), data_fin=date(2026, 9, 12),
        tipo="medicamento", medicamento="Antibiótico", tempo_espera_dias=7,
        persoa_id=persoa.id), hoxe=HOXE)
    aviso = aviso_tempo_espera(session, ana, horta.id, galinas.id, date(2026, 9, 15))
    assert aviso is not None and "19/09/2026" in aviso
    assert aviso_tempo_espera(session, ana, horta.id, galinas.id, date(2026, 9, 1)) is None
    assert aviso_tempo_espera(session, ana, horta.id, galinas.id, date(2026, 9, 20)) is None
    # Un período que colle o medicamento tamén avisa
    assert aviso_tempo_espera(session, ana, horta.id, galinas.id, date(2026, 9, 5),
                              date(2026, 9, 11)) is not None


def test_no_diario_e_como_tarefa(session):
    ana, horta, persoa, galinas = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Recoller os ovos", tipo="producion_animal",
                          animal_id=galinas.id)
    pr = crear_producion(session, ana, _ovos(galinas, persoa, retirada=2), hoxe=HOXE)
    facer_tarefa(session, ana, tarefa, pr)
    traballos = [t for t in listar_traballos(session, ana, horta.id)
                 if t.tipo == "producion_animal"]
    assert len(traballos) == 1
    assert traballos[0].que == "Ovos: 24 unidades (2 retirados) · lote 2026-OVOS-001"
    assert traballos[0].persoas == (persoa.id,)


def test_non_se_borra_un_grupo_nin_a_explotacion_con_producion(session):
    ana, horta, persoa, galinas = _escenario(session)
    crear_producion(session, ana, _ovos(galinas, persoa), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="produción"):
        eliminar_animal(session, ana, galinas)
    with pytest.raises(OperacionNonPermitidaError, match="produción"):
        eliminar_horta(session, ana, horta)

from datetime import date

from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.diario import listar_traballos
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega
from horta.services.tarefas import crear_tarefa, marcar_feita

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1


HOXE = date(2026, 10, 26)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x", rol=RolGlobal.USUARIO,
                  activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Horta de abaixo")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    return ana, horta, parcela, cultivo


def test_xunta_os_traballos_de_cada_tipo(session):
    ana, horta, parcela, cultivo = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, data_inicio=date(2026, 5, 1),
                       tipo_inicio="plantacion")
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1),
                                       persoa_id=QUEN), hoxe=HOXE)
    traballos = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert [(t.tipo, t.data, t.feito) for t in traballos] == [
        ("rega", date(2026, 7, 1), True), ("sementeira", date(2026, 5, 1), True)]
    assert traballos[1].que == "Plantación"
    assert traballos[0].onde == "Tomate — Horta de abaixo"
    assert traballos[0].parcelas == {parcela.id}


def test_o_por_facer_vai_primeiro_e_sae_sempre(session):
    ana, horta, _, cultivo = _escenario(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 1, 10),
                                       persoa_id=QUEN), hoxe=HOXE)
    crear_tarefa(session, ana, horta.id, "Podar a viña", data=date(2026, 11, 2))
    crear_tarefa(session, ana, horta.id, "Mercar sementes")
    crear_tarefa(session, ana, horta.id, "Sulfatar", data_limite=date(2026, 10, 1))
    traballos = listar_traballos(session, ana, horta.id, desde=date(2026, 10, 1), hoxe=HOXE)
    assert [(t.que, t.feito, t.atrasado) for t in traballos] == [
        ("Mercar sementes", False, False), ("Sulfatar", False, True),
        ("Podar a viña", False, False)]


def test_a_tarefa_feita_vai_coa_data_en_que_se_fixo(session):
    ana, horta, _, _ = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Limpar o galiñeiro", data=date(2026, 10, 1))
    marcar_feita(session, ana, tarefa, QUEN)
    (traballo,) = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert traballo.feito and traballo.data == tarefa.data_feita

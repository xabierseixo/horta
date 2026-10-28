"""Unha soa lista de persoas e entidades, con papeis
."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.caderno import xerar_caderno
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.persoas import (
    actualizar_persoa,
    crear_contacto,
    crear_persoa,
    listar_persoas,
    listar_quen,
    persoa_co_papel,
    titular_da_horta,
)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_quen_crea_a_explotacion_traballa_nela(session):
    ana, horta = _escenario(session)
    [persoa] = listar_persoas(session, ana, horta.id)
    assert persoa.papeis == {"traballador"}


def test_unha_persoa_pode_ter_varios_papeis(session):
    ana, horta = _escenario(session)
    xan = crear_persoa(session, ana, horta.id, "Xan", papeis={"traballador", "cliente"})
    assert xan.papeis == {"traballador", "cliente"}
    actualizar_persoa(session, ana, xan, papeis={"cliente"})
    assert xan.papeis == {"cliente"}
    assert listar_persoas(session, ana, horta.id, papel="cliente") == [xan]


def test_so_un_titular(session):
    ana, horta = _escenario(session)
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"})
    with pytest.raises(OperacionNonPermitidaError, match="xa ten titular"):
        crear_persoa(session, ana, horta.id, "Xan", papeis={"titular"})
    assert titular_da_horta(session, horta.id).nome == "Ana"


def test_nif_de_persoa_e_de_entidade(session):
    ana, horta = _escenario(session)
    crear_persoa(session, ana, horta.id, "Ana", nif="12345678z")
    crear_persoa(session, ana, horta.id, "Coop", tipo="entidade", nif="F15000000")
    with pytest.raises(OperacionNonPermitidaError, match="NIF"):
        crear_persoa(session, ana, horta.id, "Coop 2", tipo="entidade", nif="12345678Z")


def test_asesor_persoa_precisa_ropo_e_a_entidade_non(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="ROPO"):
        crear_persoa(session, ana, horta.id, "Lúa", papeis={"asesor"})
    crear_persoa(session, ana, horta.id, "ATRIA", tipo="entidade", papeis={"asesor"},
                 num_asesoramento="AT-1")


def test_quen_o_fixo_e_o_equipo_ou_unha_empresa_de_servizos(session):
    ana, horta = _escenario(session)
    cliente = crear_contacto(session, ana, horta.id, "Bar Central", "cliente")
    servizos = crear_contacto(session, ana, horta.id, "Abonos SL", "servizos")
    quen = listar_quen(session, ana, horta.id)
    assert servizos in quen and cliente not in quen


def test_crear_dende_un_formulario_reutiliza_a_persoa(session):
    ana, horta = _escenario(session)
    xan = crear_contacto(session, ana, horta.id, "Xan da Ponte", "cliente", nif="12345678Z")
    # O mesmo NIF (ou o mesmo nome) é a mesma persoa, e gaña o papel novo
    assert crear_contacto(session, ana, horta.id, "Xan", "provedor", nif="12345678Z") is xan
    assert crear_contacto(session, ana, horta.id, "xan da ponte ", "explotacion") is xan
    assert xan.papeis == {"cliente", "provedor", "explotacion"}


def test_a_persoa_dun_traballo_ten_que_ser_da_explotacion(session):
    ana, horta = _escenario(session)
    allea = crear_contacto(session, ana, crear_horta(session, ana, "Outra").id, "X", None)
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        persoa_co_papel(session, horta.id, allea.id, "cliente")


def test_caderno_titular_entidade_e_o_seu_representante(session):
    ana, horta = _escenario(session)
    crear_persoa(session, ana, horta.id, "Agro Ulla SL", tipo="entidade", nif="B15000000",
                 papeis={"titular"})
    crear_persoa(session, ana, horta.id, "Rosa", apelidos="Vilar", nif="12345678Z",
                 papeis={"representante"})
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [[c for c in f if c not in (None, "")] for f in
             libro["1 Información xeral"].iter_rows(values_only=True)]
    assert ["Nome e apelidos ou razón social", "Agro Ulla SL"] in filas
    assert ["Nome e apelidos", "Rosa Vilar"] in filas


def test_o_medicamento_garda_veterinario_e_provedor(session):
    ana, horta = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    marta = crear_contacto(session, ana, horta.id, "Marta Vázquez", None)
    agrovet = crear_contacto(session, ana, horta.id, "Agrovet Lalín", None)
    [quen] = listar_persoas(session, ana, horta.id, papel="traballador")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=quen.id, medicamento="Oxitetraciclina", tempo_espera_dias=7,
        veterinario_id=marta.id, provedor_id=agrovet.id), hoxe=date(2026, 10, 28))
    assert (co.veterinario_id, co.provedor_id) == (marta.id, agrovet.id)
    # Quedan co papel que fixeron, para atopalos despois en Contactos
    assert marta.papeis == {"veterinario"} and agrovet.papeis == {"provedor"}

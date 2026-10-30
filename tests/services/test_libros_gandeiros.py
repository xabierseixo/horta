"""Libro de rexistro gandeiro e rexistro de medicamentos (paso 14)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.coidado_animal import CoidadoAnimal
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal, crear_identificado
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.libros_gandeiros import xerar_libros
from horta.services.persoas import crear_contacto, crear_persoa


def test_libros_dos_animais(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    galinas = crear_animal(session, ana, horta.id, "Galiña", cantidade=10,
                           data_alta=date(2026, 1, 1))
    session.add(CoidadoAnimal(horta_id=horta.id, animal_id=galinas.id, tipo="medicamento",
                              data_inicio=date(2026, 3, 1), data_fin=date(2026, 3, 5),
                              receita="R-1", tempo_espera_dias=7))
    session.commit()
    libro = load_workbook(BytesIO(xerar_libros(session, ana, horta.id, date(2026, 1, 1),
                                               date(2026, 12, 31))))
    assert libro.sheetnames == ["Explotación", "Censo", "Identificación", "Entradas e saídas",
                                "Enfermidades e produción",
                                "Visitas", "Medicamentos"]
    # Fila 5: a primeira de datos (título, explotación, baleira, cabeceiras)
    assert libro["Entradas e saídas"]["D5"].value == 10
    assert libro["Medicamentos"]["I5"].value == "R-1"
    with pytest.raises(OperacionNonPermitidaError):
        xerar_libros(session, ana, horta.id, date(2026, 2, 1), date(2026, 1, 1))


def test_o_libro_leva_o_anexo_v(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    actualizar_horta(session, ana, horta, codigo_rega="ES150010000002",
                     rega_clasificacion="Produción de leite", rega_capacidade="20 vacas")
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="12345678Z")
    dono = crear_contacto(session, ana, horta.id, "Xan", None, nif="87654321X")
    vacas = crear_animal(session, ana, horta.id, "Vacas", cantidade=2,
                         data_alta=date(2026, 1, 1), titular_animais_id=dono.id)
    crear_identificado(session, ana, vacas, identificador="ES0123", dispositivo="bolo",
                       data_alta=date(2026, 1, 1))
    libro = load_workbook(BytesIO(xerar_libros(session, ana, horta.id, date(2026, 1, 1),
                                               date(2026, 12, 31))))
    datos = {f[0].value: f[1].value for f in libro["Explotación"].iter_rows(min_row=5)}
    assert datos["Código da explotación (REGA)"] == "ES150010000002"
    assert datos["NIF do titular"] == "12345678Z"
    assert (datos["Clasificación"], datos["Capacidade máxima"]) == ("Produción de leite",
                                                                     "20 vacas")
    assert libro["Censo"]["H5"].value == "87654321X"
    assert libro["Identificación"]["C5"].value == "Bolo ruminal"

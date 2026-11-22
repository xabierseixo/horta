"""Libro de rexistro gandeiro e rexistro de medicamentos (paso 14)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.coidado_animal import CoidadoAnimal
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.libros_gandeiros import xerar_libros


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
    assert libro.sheetnames == ["Censo", "Identificación", "Entradas e saídas",
                                "Enfermidades e produción",
                                "Visitas", "Medicamentos"]
    # Fila 5: a primeira de datos (título, explotación, baleira, cabeceiras)
    assert libro["Entradas e saídas"]["D5"].value == 10
    assert libro["Medicamentos"]["I5"].value == "R-1"
    with pytest.raises(OperacionNonPermitidaError):
        xerar_libros(session, ana, horta.id, date(2026, 2, 1), date(2026, 1, 1))

from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.hortas import crear_horta
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    crear_tratamento_instalacion,
)

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1



def test_no_caderno(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(persoa_id=QUEN,
        tipo="local", data=date(2026, 6, 1), obxecto="Alpendre das patacas",
        nome_comercial="Produto X"), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [[x for x in f if x not in (None, "")]
             for f in libro["3 Tratamentos"].iter_rows(values_only=True)]
    i = filas.index(["3.4 REXISTRO DE TRATAMENTOS DOS LOCAIS DE ALMACENAMENTO"])
    assert filas[i + 1] == ["Aplica tratamento", "SI"]
    assert filas[i + 3][:2] == ["01/06/2026", "Alpendre das patacas"]
    j = filas.index(["3.3 REXISTRO DE TRATAMENTOS POSTCOLLEITA (en produto vexetal)"])
    assert filas[j + 1] == ["Aplica tratamento", "NON"]

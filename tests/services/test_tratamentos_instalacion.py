from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    actualizar_tratamento_instalacion,
    crear_tratamento_instalacion,
    dar_de_baixa_tratamento_instalacion,
    listar_tratamentos_instalacion,
)

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1


HOXE = date(2026, 10, 25)


def _usuario(session, email):
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("praga", "7"), ("unidade_medida", "4")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    return ana, crear_horta(session, ana, "Horta")


def _datos(**cambios):
    base = {"tipo": "local", "data": date(2026, 6, 1), "obxecto": "Alpendre das patacas",
            "problema_tipo": "praga", "problema_codigo": "7", "cantidade_tratada": 30,
            "nome_comercial": "Produto X", "cantidade_utilizada": 0.5, "unidade": "4"}
    base.update(cambios)
    return DatosTratamentoInstalacion(**{"persoa_id": QUEN, **base})


def test_crear_editar_e_dar_de_baixa(session):
    ana, horta = _escenario(session)
    t = crear_tratamento_instalacion(session, ana, horta.id, _datos(), hoxe=HOXE)
    assert t.creado_por == ana.id and t.referencia_catastral is None
    actualizar_tratamento_instalacion(session, ana, t, _datos(cantidade_tratada=40), hoxe=HOXE)
    assert t.cantidade_tratada == 40
    assert listar_tratamentos_instalacion(session, ana, horta.id) == [t]
    dar_de_baixa_tratamento_instalacion(session, ana, t)
    assert listar_tratamentos_instalacion(session, ana, horta.id) == []


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"tipo": "almacen"}, "postcolleita"),
    ({"data": date(2026, 11, 1)}, "futura"),
    ({"obxecto": " "}, "que se tratou"),
    ({"nome_comercial": None}, "produto"),
    ({"cantidade_utilizada": 0}, "maiores que 0"),
    ({"problema_codigo": "99"}, "non existe"),
])
def test_validacions(session, cambios, mensaxe):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_tratamento_instalacion(session, ana, horta.id, _datos(**cambios), hoxe=HOXE)


def test_lector_non_pode(session):
    ana, horta = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_tratamento_instalacion(session, bea, horta.id, _datos(), hoxe=HOXE)


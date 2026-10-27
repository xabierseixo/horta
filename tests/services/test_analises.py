from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.analises import (
    DatosAnalise,
    actualizar_analise,
    crear_analise,
    dar_de_baixa_analise,
    listar_analises,
)
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

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
    for catalogo, codigo in [("material_analizado", "2"), ("material_analizado", "3"),
                             ("tipo_analise", "1"), ("tipo_analise", "5"),
                             ("substancia_activa", "2")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    return ana, horta, parcela, cultivo


def test_analise_de_solo_dunha_parcela(session):
    ana, horta, parcela, _ = _escenario(session)
    analise = crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
        material_analizado="3", data_mostraxe=date(2026, 3, 1), tipos=["5"],
        parcela_id=parcela.id, laboratorio="Lab", solo={"ph": 5.8, "materia_organica": 4.2}),
        hoxe=HOXE)
    assert analise.ph == 5.8 and analise.materia_organica == 4.2
    assert [t.codigo for t in analise.tipos] == ["5"]
    assert listar_analises(session, ana, horta.id) == [analise]


def test_residuos_no_produto(session):
    ana, horta, _, cultivo = _escenario(session)
    analise = crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
        material_analizado="2", data_mostraxe=date(2026, 8, 1), tipos=["1"],
        substancias=["2"], cultivo_id=cultivo.id), hoxe=HOXE)
    assert [s.codigo for s in analise.substancias] == ["2"]


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_mostraxe": date(2026, 11, 1)}, "futura"),
    ({"material_analizado": "2", "solo": {"ph": 6}}, "só van nas análises de solo"),
    ({"solo": {"ph": 15}}, "pH"),
    ({"solo": {"arxila": 120}}, "porcentaxes"),
    ({"tipos": ["9"]}, "non existe"),
])
def test_validacions(session, cambios, mensaxe):
    ana, horta, _, _ = _escenario(session)
    datos = {"material_analizado": "3", "data_mostraxe": date(2026, 3, 1), "persoa_id": QUEN,
             **cambios}
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_analise(session, ana, horta.id, DatosAnalise(**datos), hoxe=HOXE)


def test_cultivo_doutra_explotacion(session):
    ana, horta, _, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    outro = crear_cultivo(session, ana, crear_parcela(session, ana, outra.id, "P").id, "X")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_analise(session, ana, horta.id, DatosAnalise(persoa_id=QUEN,
            material_analizado="3", data_mostraxe=date(2026, 3, 1), cultivo_id=outro.id),
            hoxe=HOXE)


def test_lector_non_pode_e_baixa(session):
    ana, horta, _, _ = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    datos = DatosAnalise(persoa_id=QUEN, material_analizado="3", data_mostraxe=date(2026, 3, 1))
    with pytest.raises(PermisoDenegadoError):
        crear_analise(session, bea, horta.id, datos, hoxe=HOXE)
    analise = crear_analise(session, ana, horta.id, datos, hoxe=HOXE)
    actualizar_analise(session, ana, analise, DatosAnalise(persoa_id=QUEN,
        material_analizado="3", data_mostraxe=date(2026, 3, 2)), hoxe=HOXE)
    dar_de_baixa_analise(session, ana, analise)
    assert listar_analises(session, ana, horta.id) == []

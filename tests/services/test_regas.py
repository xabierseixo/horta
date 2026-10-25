from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import actualizar_parcela, crear_parcela
from horta.services.regas import (
    DatosRega,
    actualizar_rega,
    crear_rega,
    dar_de_baixa_rega,
    listar_regas,
    litros_estimados,
    ultimo_sistema_rega,
)

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
    for catalogo, codigo, categoria in [
        ("sistema_rega", "6", None), ("orixe_auga", "2", None), ("orixe_auga", "3", None),
        ("boas_practicas", "23", "rega"), ("boas_practicas", "50", "fito"),
    ]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  categoria=categoria, version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    actualizar_parcela(session, ana, parcela, orixe_auga="2")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.01)
    return ana, horta, cultivo


def _datos(cultivo, **cambios):
    base = {"cultivo_id": cultivo.id, "data_inicio": date(2026, 7, 1), "sistema_rega": "6",
            "cantidade": 300}
    base.update(cambios)
    return DatosRega(**base)


def test_crear_rega_cos_valores_por_defecto(session):
    ana, horta, cultivo = _escenario(session)
    rega = crear_rega(session, ana, _datos(cultivo), hoxe=HOXE)
    assert rega.superficie_ha == 0.01 and rega.data_fin == date(2026, 7, 1)
    assert rega.unidade == "4" and rega.orixe_auga == "2"  # a orixe da parcela
    assert rega.creado_por == ana.id
    assert listar_regas(session, ana, horta.id) == [rega]
    assert ultimo_sistema_rega(session, cultivo.id) == "6"


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_inicio": date(2026, 11, 1)}, "futura"),
    ({"data_fin": date(2026, 6, 1)}, "anterior"),
    ({"superficie_ha": 0.02}, "maior ca do cultivo"),
    ({"cantidade": 0}, "maior que 0"),
    ({"unidade": "5"}, "litros ou m³"),
    ({"boas_practicas": ["50"]}, "non é de rega"),
])
def test_validacions(session, cambios, mensaxe):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_rega(session, ana, _datos(cultivo, **cambios), hoxe=HOXE)


def test_lector_non_pode_regar(session):
    ana, horta, cultivo = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_rega(session, bea, _datos(cultivo), hoxe=HOXE)


def test_actualizar_e_dar_de_baixa(session):
    ana, horta, cultivo = _escenario(session)
    rega = crear_rega(session, ana, _datos(cultivo), hoxe=HOXE)
    actualizar_rega(session, ana, rega, _datos(cultivo, cantidade=2, unidade="3",
                                               orixe_auga="3", boas_practicas=["23"]),
                    hoxe=HOXE)
    assert rega.cantidade == 2 and rega.orixe_auga == "3"
    assert [b.codigo for b in rega.boas_practicas] == ["23"]
    dar_de_baixa_rega(session, ana, rega)
    assert listar_regas(session, ana, horta.id) == []


@pytest.mark.parametrize(("args", "esperado"), [
    ({"minutos": 20, "litros_minuto": 12}, 240),
    ({"regadeiras": 6, "litros_regadeira": 10}, 60),
    ({"minutos": 20}, None),
    ({}, None),
])
def test_litros_estimados(args, esperado):
    assert litros_estimados(**args) == esperado

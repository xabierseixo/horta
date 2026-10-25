from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.labores import (
    DatosLabor,
    actualizar_labor,
    crear_labor,
    dar_de_baixa_labor,
    listar_labores,
    ultimo_labor,
)
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela, eliminar_parcela

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
    for catalogo, codigo in [("tipo_labor", "1"), ("tipo_labor", "5"), ("tipo_labor", "7"),
                             ("tipo_cobertura_solo", "1"), ("tipo_cobertura_solo", "3")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Maceira")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2, tipo_cobertura_solo="3")
    return ana, horta, parcela, cultivo


def _datos(cultivo, **cambios):
    base = {"cultivo_id": cultivo.id, "data_inicio": date(2026, 3, 1), "tipo_labor": "7"}
    base.update(cambios)
    return DatosLabor(**base)


def test_crear_labor_cos_valores_por_defecto(session):
    ana, horta, _, cultivo = _escenario(session)
    labor = crear_labor(session, ana, _datos(cultivo, restos_poda_no_solo=True), hoxe=HOXE)
    assert labor.data_fin == labor.data_inicio
    assert labor.superficie_ha == 0.2
    assert labor.tipo_cobertura == "3"  # a do cultivo
    assert labor.restos_poda_no_solo and not labor.restos_desbroce_no_solo
    assert labor.creado_por == ana.id
    assert listar_labores(session, ana, horta.id) == [labor]


def test_restos_so_nos_labores_que_os_preguntan(session):
    ana, _, _, cultivo = _escenario(session)
    labor = crear_labor(session, ana, _datos(cultivo, tipo_labor="1", restos_poda_no_solo=True,
                                             restos_desbroce_no_solo=True), hoxe=HOXE)
    assert not labor.restos_poda_no_solo and not labor.restos_desbroce_no_solo
    desbroce = crear_labor(session, ana, _datos(cultivo, tipo_labor="5",
                                                restos_desbroce_no_solo=True), hoxe=HOXE)
    assert desbroce.restos_desbroce_no_solo


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_inicio": date(2026, 11, 1)}, "futura"),
    ({"data_fin": date(2026, 2, 1)}, "anterior"),
    ({"superficie_ha": 0.3}, "maior ca do cultivo"),
    ({"superficie_ha": 0}, "maior que 0"),
    ({"num_repeticions": 0}, "repeticións"),
    ({"tipo_labor": "99"}, None),
    ({"tipo_cobertura": "99"}, None),
])
def test_validacions(session, cambios, mensaxe):
    ana, _, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_labor(session, ana, _datos(cultivo, **cambios), hoxe=HOXE)


def test_maquina_doutra_explotacion(session):
    ana, _, _, cultivo = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    maquina = crear_maquina(session, ana, outra.id, "Tractor", id_equipo_non_inscribible="T1")
    with pytest.raises(OperacionNonPermitidaError, match="máquina"):
        crear_labor(session, ana, _datos(cultivo, maquina_id=maquina.id), hoxe=HOXE)


def test_editar_baixa_e_ultimo_labor(session):
    ana, horta, _, cultivo = _escenario(session)
    labor = crear_labor(session, ana, _datos(cultivo), hoxe=HOXE)
    actualizar_labor(session, ana, labor, _datos(cultivo, tipo_labor="1", num_repeticions=2,
                                                 duracion_h=1.5), hoxe=HOXE)
    assert (labor.tipo_labor, labor.num_repeticions, labor.duracion_h) == ("1", 2, 1.5)
    assert ultimo_labor(session, cultivo.id) == "1"
    dar_de_baixa_labor(session, ana, labor)
    assert listar_labores(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_labor(session, ana, labor, _datos(cultivo), hoxe=HOXE)


def test_lector_non_pode(session):
    ana, horta, _, cultivo = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_labor(session, bea, _datos(cultivo), hoxe=HOXE)


def test_cultivo_e_parcela_con_labores_conservanse(session):
    ana, _, parcela, cultivo = _escenario(session)
    crear_labor(session, ana, _datos(cultivo), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="labores"):
        eliminar_cultivo(session, ana, cultivo)
    with pytest.raises(OperacionNonPermitidaError, match="labores"):
        eliminar_parcela(session, ana, parcela)

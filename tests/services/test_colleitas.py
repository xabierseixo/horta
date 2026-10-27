from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import (
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    dar_de_baixa_colleita,
    listar_colleitas,
    propor_lote,
    rendemento_kg_ha,
)
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

HOXE = date(2026, 10, 23)


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.5, data_inicio=date(2026, 3, 1))
    return ana, horta, cultivo


def _datos(cultivo, **cambios) -> DatosColleita:
    base = {"cultivo_id": cultivo.id, "data": date(2026, 7, 15), "cantidade": 1000.0,
            "unidade": "kg", "lote": "2026-PATACA-001"}
    return DatosColleita(**{"persoa_id": QUEN, **base, **cambios})


def test_crear_e_listar(session):
    ana, horta, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert colleita.creado_por == ana.id
    assert [c.lote for c in listar_colleitas(session, ana, horta.id)] == ["2026-PATACA-001"]


@pytest.mark.parametrize(
    ("cambios", "mensaxe"),
    [
        ({"cantidade": 0}, "maior que 0"),
        ({"unidade": "sacos"}, "Unidade non válida"),
        ({"data": date(2026, 12, 1)}, "futura"),
        ({"data": date(2026, 2, 1)}, "anterior ao inicio"),
        ({"superficie_ha": 0.9}, "maior ca do cultivo"),
    ],
)

def test_validacions(session, cambios, mensaxe):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_colleita(session, ana, _datos(cultivo, **cambios), hoxe=HOXE)


def test_lote_repetido_rexeitase(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)


def test_lector_non_pode_crear(session):
    ana, horta, cultivo = _escenario(session)
    bea = _crear_usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_colleita(session, bea, _datos(cultivo), hoxe=HOXE)


def test_propor_lote_salta_os_usados(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert propor_lote(session, ana, cultivo.id, date(2026, 8, 1)) == "2026-PATACA-002"


def test_baixa_non_se_lista_nin_se_modifica(session):
    ana, horta, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    dar_de_baixa_colleita(session, ana, colleita)
    assert listar_colleitas(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError, match="dada de baixa"):
        actualizar_colleita(session, ana, colleita, _datos(cultivo, cantidade=5.0), hoxe=HOXE)


def test_actualizar_mantendo_o_mesmo_lote(session):
    ana, _, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    actualizar_colleita(session, ana, colleita, _datos(cultivo, cantidade=900.0), hoxe=HOXE)
    assert colleita.cantidade == 900.0


def test_rendemento_en_kg_por_hectarea(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    crear_colleita(session, ana, _datos(cultivo, cantidade=1.0, unidade="t",
                                        lote="2026-PATACA-002"), hoxe=HOXE)
    assert rendemento_kg_ha(session, ana, cultivo.id) == 4000.0


def test_superficie_por_defecto_e_data_fin(session):
    ana, _, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert colleita.superficie_ha == 0.5
    assert colleita.data_fin == colleita.data


def test_finalidade_so_para_procesado_ou_vino(session):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="viño ou a procesado"):
        crear_colleita(session, ana, _datos(cultivo, destino_colleita="6"), hoxe=HOXE)


def test_rendemento_sen_superficie_ou_con_unidades_non_kg(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo, unidade="mazos"), hoxe=HOXE)
    assert rendemento_kg_ha(session, ana, cultivo.id) is None

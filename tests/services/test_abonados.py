from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import (
    DatosAbonado,
    actualizar_abonado,
    crear_abonado,
    dar_de_baixa_abonado,
    listar_abonados,
    nutrientes_do_abonado,
)
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
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
    for catalogo, codigo, categoria in [
        ("material_fertilizante", "14", None), ("tipo_fertilizacion", "1", None),
        ("metodo_fertilizacion", "1", None), ("boas_practicas", "0", "fito,fertilizacion,rega"),
        ("boas_practicas", "20", "fito,fertilizacion"), ("boas_practicas", "50", "fito"),
    ]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  categoria=categoria, version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK 15-15-15", material="14", n_pct=15, p2o5_pct=15, k2o_pct=15))
    return ana, horta, cultivo, abono


def _datos(cultivo, abono, **cambios):
    base = {"cultivo_id": cultivo.id, "data_inicio": date(2026, 4, 1), "tipo_fertilizacion": "1",
            "metodo": "1", "boas_practicas": ["0"], "fertilizante_id": abono.id, "dose": 200,
            "unidade": "17"}
    base.update(cambios)
    return DatosAbonado(**{"aplicador_persoa_id": QUEN, **base})


def test_crear_abonado_coa_superficie_do_cultivo(session):
    ana, horta, cultivo, abono = _escenario(session)
    abonado = crear_abonado(session, ana, _datos(cultivo, abono), hoxe=HOXE)
    assert abonado.superficie_ha == 0.2 and abonado.data_fin == date(2026, 4, 1)
    assert abonado.creado_por == ana.id
    assert [b.codigo for b in abonado.boas_practicas] == ["0"]
    assert nutrientes_do_abonado(session, abonado) == (30.0, 30.0, 30.0)
    assert listar_abonados(session, ana, horta.id) == [abonado]


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_inicio": date(2026, 11, 1)}, "futura"),
    ({"data_fin": date(2026, 3, 1)}, "anterior"),
    ({"superficie_ha": 0.3}, "maior ca do cultivo"),
    ({"boas_practicas": ["50"]}, "non é de fertilización"),
    ({"fertilizante_id": None}, "Escolle o abono"),
    ({"dose": 0}, "dose"),
    ({"unidade": "2"}, "unidade"),
])
def test_validacions(session, cambios, mensaxe):
    ana, _, cultivo, abono = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_abonado(session, ana, _datos(cultivo, abono, **cambios), hoxe=HOXE)


def test_abonado_en_verde_sen_abono(session):
    ana, _, cultivo, abono = _escenario(session)
    abonado = crear_abonado(session, ana, _datos(
        cultivo, abono, fertilizante_id=None, boas_practicas=["20"]), hoxe=HOXE)
    assert abonado.fertilizante_id is None and abonado.dose is None
    assert nutrientes_do_abonado(session, abonado) is None


def test_lector_non_pode_abonar(session):
    ana, horta, cultivo, abono = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_abonado(session, bea, _datos(cultivo, abono), hoxe=HOXE)


def test_actualizar_e_dar_de_baixa(session):
    ana, horta, cultivo, abono = _escenario(session)
    abonado = crear_abonado(session, ana, _datos(cultivo, abono), hoxe=HOXE)
    actualizar_abonado(session, ana, abonado, _datos(cultivo, abono, dose=100), hoxe=HOXE)
    assert abonado.dose == 100
    dar_de_baixa_abonado(session, ana, abonado)
    assert listar_abonados(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_abonado(session, ana, abonado, _datos(cultivo, abono), hoxe=HOXE)

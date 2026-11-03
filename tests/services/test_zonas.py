"""Zonas da parcela e ferramentas para facelas (bancais iguais)."""

from datetime import date

import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    puntos_da_xeometria,
    xeometria_debuxada,
)
from horta.services.zonas import (
    aviso_superficie,
    borrar_zona,
    cambiar_zona,
    crear_zona,
    dividir_en_bancais,
    dividir_zona,
    franxas,
    listar_zonas,
    xuntar_zonas,
)

# Cadrado de ~100 × 100 m
CADRADO = [(42.8, -8.0), (42.8009, -8.0), (42.8009, -7.99878), (42.8, -7.99878)]


def _parcela(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    geojson, hectareas, _ = xeometria_debuxada(CADRADO)
    actualizar_parcela(session, ana, parcela, geometria=geojson, superficie=hectareas)
    return ana, parcela


def test_franxas_iguais():
    bancais = franxas(CADRADO, 4, 0, paso_m=0)
    areas = [xeometria_debuxada(b)[1] for b in bancais]
    assert len(bancais) == 4 and max(areas) - min(areas) < 0.001
    assert 0.95 < sum(areas) < 1.05
    # Con paso de 2 m entre bancais queda menos superficie cultivada
    con_paso = sum(xeometria_debuxada(b)[1] for b in franxas(CADRADO, 4, 0, paso_m=2))
    assert con_paso < sum(areas)
    with pytest.raises(OperacionNonPermitidaError, match="non caben"):
        franxas(CADRADO, 10, 0, paso_m=20)


def test_dividir_zonas_e_cultivo(session):
    ana, parcela = _parcela(session)
    zonas = dividir_en_bancais(session, ana, parcela, 3, 90, paso_m=1, nome="Bancal")
    assert [z.nome for z in zonas] == ["Bancal 1", "Bancal 2", "Bancal 3"]
    assert aviso_superficie(session, parcela) is None
    cultivo = crear_cultivo(session, ana, parcela.id, "Leituga", zona_id=zonas[0].id,
                            data_inicio=date(2026, 4, 1))
    assert cultivo.zona_id == zonas[0].id
    with pytest.raises(OperacionNonPermitidaError, match="cultivos"):
        borrar_zona(session, ana, zonas[0])
    crear_zona(session, ana, parcela, "Invernadoiro", "invernadoiro", CADRADO)
    assert "suman" in (aviso_superficie(session, parcela) or "")


# --- Zonas de cultivo debuxadas no mapa (pantalla Terras)

def _area(zona):
    return xeometria_debuxada(puntos_da_xeometria(zona.geometria))[1]


def test_a_zona_recortase_polo_contorno(session):
    ana, parcela = _parcela(session)
    saida = [(42.80045, -8.0006), (42.8015, -8.0006), (42.8015, -7.99939), (42.80045, -7.99939)]
    zona = crear_zona(session, ana, parcela, "Patacas", "cultivo", saida, so_dentro=True)
    assert _area(zona) == pytest.approx(parcela.superficie / 4, rel=0.02)


def test_dividir_e_xuntar_zonas(session):
    ana, parcela = _parcela(session)
    zona = crear_zona(session, ana, parcela, "Patacas", "cultivo", CADRADO)
    nova = dividir_zona(session, ana, zona, [(42.7995, -7.99939), (42.8015, -7.99939)])
    assert nova[0].nome == "Patacas (2)" and nova[0].tipo == "cultivo"
    assert _area(zona) == pytest.approx(_area(nova[0]), rel=0.02)
    cultivo = crear_cultivo(session, ana, parcela.id, "Patacas", zona_id=nova[0].id,
                            data_inicio=date(2026, 3, 1))
    xuntar_zonas(session, ana, zona, nova[0])
    assert _area(zona) == pytest.approx(parcela.superficie, rel=0.02)
    assert listar_zonas(session, ana, parcela) == [zona]
    assert cultivo.zona_id == zona.id


def test_mover_os_lindes_e_renomear(session):
    ana, parcela = _parcela(session)
    zona = crear_zona(session, ana, parcela, "Patacas", "cultivo", CADRADO)
    cambiar_zona(session, ana, zona, nome="Cebolas",
                 puntos=[(42.8, -8.0), (42.8009, -8.0), (42.8009, -7.99939), (42.8, -7.99939)])
    assert zona.nome == "Cebolas"
    assert zona.superficie == pytest.approx(parcela.superficie / 2, rel=0.02)
    with pytest.raises(OperacionNonPermitidaError, match="dentro"):
        cambiar_zona(session, ana, zona, puntos=[(la + 0.01, lo) for la, lo in CADRADO])


def test_quitar_a_parcela_quita_as_zonas(session):
    from horta.models.zona import ParcelaZona
    from horta.services.parcelas import eliminar_parcela
    ana, parcela = _parcela(session)
    crear_zona(session, ana, parcela, "Patacas", "cultivo", CADRADO)
    eliminar_parcela(session, ana, parcela)
    assert session.query(ParcelaZona).count() == 0

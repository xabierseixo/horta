"""Probas das estatísticas de enerxía (tarefa 170)."""

from __future__ import annotations

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.estatisticas import enerxia_por_mes
from horta.services.hortas import crear_horta
from horta.services.produtos import (
    DatosEntrada,
    crear_entrada,
    crear_produto,
    dar_de_baixa_entrada,
)

HOXE = date(2026, 11, 1)


def _escenario(session):
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="f" * 64, filas=0)
    session.add(version)
    session.flush()
    session.add(CatalogoValor(catalogo="tipo_enerxia", codigo="1", descricion="Gasóleo B",
                              version_id=version.id))
    session.add(CatalogoValor(catalogo="tipo_enerxia", codigo="2", descricion="Electricidade",
                              version_id=version.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    return ana, horta, quen


def test_duas_entradas_gasoleo_e_unha_luz(session):
    """Dúas entradas de gasóleo en meses distintos e unha de luz en kWh: totais e importes."""
    ana, horta, quen = _escenario(session)
    gasoleo = crear_produto(
        session, ana, horta.id, tipo="enerxia", nome="Gasóleo calefacción",
        unidade="litros", tipo_enerxia="1"
    )
    luz = crear_produto(
        session, ana, horta.id, tipo="enerxia", nome="Luz almacén",
        unidade="kWh", tipo_enerxia="2"
    )
    # Entrada 1 de gasóleo: febreiro (mes 2)
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=gasoleo.id, data=date(2026, 2, 10), persoa_id=quen.id,
            cantidade=100.0, unidade="litros", importe=120.50
        ), hoxe=HOXE
    )
    # Entrada 2 de gasóleo: maio (mes 5)
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=gasoleo.id, data=date(2026, 5, 20), persoa_id=quen.id,
            cantidade=200.0, unidade="litros", importe=250.00
        ), hoxe=HOXE
    )
    # Entrada de luz: maio (mes 5)
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=luz.id, data=date(2026, 5, 5), persoa_id=quen.id,
            cantidade=350.0, unidade="kWh", importe=85.20
        ), hoxe=HOXE
    )

    res = enerxia_por_mes(session, ana, horta.id, 2026)

    # Cantidades agrupadas por (descrición do catálogo, unidade)
    assert ("Gasóleo B", "litros") in res.cantidades
    assert ("Electricidade", "kWh") in res.cantidades
    # Gasóleo: febreiro (índice 1) e maio (índice 4)
    assert res.cantidades[("Gasóleo B", "litros")][1] == 100.0
    assert res.cantidades[("Gasóleo B", "litros")][4] == 200.0
    assert sum(res.cantidades[("Gasóleo B", "litros")]) == 300.0
    # Luz: maio (índice 4)
    assert res.cantidades[("Electricidade", "kWh")][4] == 350.0
    assert sum(res.cantidades[("Electricidade", "kWh")]) == 350.0
    # Importe: febreiro 120.50, maio 250.00 + 85.20 = 335.20
    assert res.importe[1] == 120.50
    assert res.importe[4] == 335.20
    assert round(sum(res.importe), 2) == 455.70


def test_entradas_baixa_e_doutro_ano_non_contan(session):
    """As entradas de baixa e as doutro ano non contan."""
    ana, horta, quen = _escenario(session)
    gasoleo = crear_produto(
        session, ana, horta.id, tipo="enerxia", nome="Gasóleo B",
        unidade="litros", tipo_enerxia="1"
    )
    # Entrada en 2026
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=gasoleo.id, data=date(2026, 3, 15), persoa_id=quen.id,
            cantidade=50.0, unidade="litros", importe=60.00
        ), hoxe=HOXE
    )
    # Entrada noutro ano (2025)
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=gasoleo.id, data=date(2025, 3, 15), persoa_id=quen.id,
            cantidade=100.0, unidade="litros", importe=120.00
        ), hoxe=HOXE
    )
    # Entrada de 2026 que se dá de baixa
    baixa = crear_entrada(
        session, ana, DatosEntrada(
            produto_id=gasoleo.id, data=date(2026, 4, 10), persoa_id=quen.id,
            cantidade=70.0, unidade="litros", importe=80.00
        ), hoxe=HOXE
    )
    dar_de_baixa_entrada(session, ana, baixa)

    res = enerxia_por_mes(session, ana, horta.id, 2026)

    # Só conta a de marzo de 2026
    assert res.cantidades[("Gasóleo B", "litros")][2] == 50.0
    assert sum(res.cantidades[("Gasóleo B", "litros")]) == 50.0
    assert res.importe[2] == 60.00
    assert round(sum(res.importe), 2) == 60.00


def test_entrada_sen_cantidade_suma_ao_importe(session):
    """Unha entrada sen cantidade suma só ao importe e sen tipo usa o nome do produto."""
    ana, horta, quen = _escenario(session)
    # Produto sen tipo_enerxia
    luz = crear_produto(
        session, ana, horta.id, tipo="enerxia", nome="Factura luz eléctrica",
        unidade="kWh"
    )
    # Entrada sen cantidade, con importe
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=luz.id, data=date(2026, 6, 1), persoa_id=quen.id,
            cantidade=None, importe=95.40
        ), hoxe=HOXE
    )

    res = enerxia_por_mes(session, ana, horta.id, 2026)

    # Non hai cantidade, polo que non se engade ningunha clave a cantidades
    assert res.cantidades == {}
    assert res.importe[5] == 95.40
    assert round(sum(res.importe), 2) == 95.40

    # Entrada sen importe, con cantidade (só suma á cantidade)
    crear_entrada(
        session, ana, DatosEntrada(
            produto_id=luz.id, data=date(2026, 7, 1), persoa_id=quen.id,
            cantidade=120.0, unidade="kWh", importe=None
        ), hoxe=HOXE
    )
    res2 = enerxia_por_mes(session, ana, horta.id, 2026)
    # Como non ten tipo_enerxia, a clave usa o nome do produto
    assert res2.cantidades[("Factura luz eléctrica", "kWh")][6] == 120.0
    assert res2.importe[6] == 0.0
    assert round(sum(res2.importe), 2) == 95.40


def test_persoa_sen_permiso_erro(session):
    """Unha persoa sen permiso lanza PermisoDenegadoError; con rol lector funciona."""
    ana, horta, _ = _escenario(session)
    pepe = Usuario(nome="pepe", email="pepe@example.com", password_hash="x",
                   rol=RolGlobal.USUARIO, activo=True)
    session.add(pepe)
    session.commit()

    with pytest.raises(PermisoDenegadoError):
        enerxia_por_mes(session, pepe, horta.id, 2026)

    # Con rol de lectura ten acceso
    membro = HortaMembro(horta_id=horta.id, usuario_id=pepe.id, rol=RolHorta.LECTOR)
    session.add(membro)
    session.commit()

    res = enerxia_por_mes(session, pepe, horta.id, 2026)
    assert res.importe == [0.0] * 12
    assert res.cantidades == {}

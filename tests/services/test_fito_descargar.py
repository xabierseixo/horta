import json
from datetime import datetime, timedelta

import pytest

from horta.models.fito_rexistro import FitoProduto
from horta.services import fito_descargar
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_descargar import (
    actualizar_fitosanitarios,
    toca_actualizar,
    ultima_comprobacion,
)

AGORA = datetime(2026, 10, 25, 12, 0)
_PRODUTOS = {"Productos": [{"DATOSPRODUCTO": {"Num_Registro": "ES-1", "Nombre": "A",
                                              "Estado": "Vigente"},
                            "COMPOSICION": [], "USOS": []}]}
_CULTIVOS = [{"CodigoEppo": "SOLTU", "CodigoCultivo": "0102090000000000"}]


@pytest.fixture
def mapa(monkeypatch):
    chamadas = []

    def pedir(endpoint, extra):
        chamadas.append(endpoint)
        return json.dumps(_PRODUTOS if "Productos" in endpoint else _CULTIVOS)

    monkeypatch.setattr(fito_descargar, "_pedir", pedir)
    return chamadas


def test_descarga_e_importa(session, mapa):
    informe = actualizar_fitosanitarios(session, agora=AGORA)
    assert informe.altas == 1 and session.get(FitoProduto, "ES-1")
    assert ultima_comprobacion(session).data == AGORA
    assert ultima_comprobacion(session).erro is None


def test_non_volve_descargar_ata_os_7_dias(session, mapa):
    actualizar_fitosanitarios(session, agora=AGORA)
    assert actualizar_fitosanitarios(session, agora=AGORA + timedelta(days=6)) is None
    assert len(mapa) == 2
    assert not toca_actualizar(session, AGORA + timedelta(days=6))
    # Sen cambios no MAPA: impórtase nada pero anótase a comprobación
    informe = actualizar_fitosanitarios(session, agora=AGORA + timedelta(days=7))
    assert informe.xa_importado and len(mapa) == 4
    assert ultima_comprobacion(session).data == AGORA + timedelta(days=7)


def test_erro_anotase_e_reinténtase(session, monkeypatch):
    def falla(endpoint, extra):
        raise OSError("sen rede")

    monkeypatch.setattr(fito_descargar, "_pedir", falla)
    with pytest.raises(OperacionNonPermitidaError, match="sen rede"):
        actualizar_fitosanitarios(session, agora=AGORA)
    assert "sen rede" in ultima_comprobacion(session).erro
    assert toca_actualizar(session, AGORA + timedelta(hours=6))

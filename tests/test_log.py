from pathlib import Path
from typing import Iterator

import pytest
from loguru import logger

from horta.log import configurar_rexistro
from horta import log as log_module


@pytest.fixture()
def reset_log_state() -> Iterator[None]:
    """Reinicia o estado global de configuración de loguru entre tests.

    Remove todos os handlers engadidos por configurar_rexistro() para evitar
    deixar sinks orfos apuntando a directorios tmp que xa foron borrados.
    """
    log_module._xa_configurado = False
    yield
    # Eliminar todos os handlers (menos o de stderr que vén por defecto)
    logger.remove()
    log_module._xa_configurado = False


def test_configurar_rexistro_crea_directorio_logs(tmp_path, monkeypatch, reset_log_state):
    monkeypatch.chdir(tmp_path)

    configurar_rexistro()

    assert (tmp_path / "logs").is_dir()


def test_configurar_rexistro_e_idempotente(tmp_path, monkeypatch, reset_log_state):
    monkeypatch.chdir(tmp_path)

    configurar_rexistro()
    configurar_rexistro()  # non debe fallar nin duplicar

    # Non hai xeito directo de contar handlers de loguru dende fóra sen
    # tocar API interna, así que a proba real é que a segunda chamada
    # non levanta excepción e o directorio segue existindo.
    assert (tmp_path / "logs").is_dir()

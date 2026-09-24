from __future__ import annotations

from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import horta.models  # noqa: F401  (rexistra todos os modelos en Base.metadata)
from horta.db import Base, activar_fk_sqlite
from horta import log as log_module


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    activar_fk_sqlite(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


@pytest.fixture(autouse=True)
def reset_log_state() -> Iterator[None]:
    """Reinicia o estado global de configuración de loguru entre tests."""
    log_module._xa_configurado = False
    yield
    log_module._xa_configurado = False

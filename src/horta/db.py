from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("HORTA_DATABASE_URL", "sqlite:///horta.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, hide_parameters=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def configurar_sqlite(engine: Engine) -> None:
    """Axustes de SQLite que PostgreSQL xa trae de seu.

    - Claves foráneas: SQLite non as comproba por defecto. Sen isto, un erro de
      orde de borrado (coma eliminar_horta) só fallaría en PostgreSQL.
    - WAL e busy_timeout: mentres a actualización do MAPA escribe miles de filas,
      ler non queda bloqueado e gardar un traballo agarda ata 5 s en vez de dar
      «database is locked».
    """

    @event.listens_for(engine, "connect")
    def _configurar(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


if DATABASE_URL.startswith("sqlite"):
    configurar_sqlite(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("HORTA_DATABASE_URL", "sqlite:///horta.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def activar_fk_sqlite(engine: Engine) -> None:
    """SQLite non comproba as claves foráneas por defecto.

    Sen isto, un erro de orde de borrado entre táboas relacionadas (coma
    eliminar_horta) pode pasar desapercibido en desenvolvemento e só
    fallar en produción (PostgreSQL, que si comproba as FKs).
    """

    @event.listens_for(engine, "connect")
    def _configurar_fk(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


if DATABASE_URL.startswith("sqlite"):
    activar_fk_sqlite(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

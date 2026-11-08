from __future__ import annotations

from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import horta.models  # noqa: F401  (rexistra todos os modelos en Base.metadata)
from horta.db import Base, configurar_sqlite


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    configurar_sqlite(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


@pytest.fixture()
def cultivos_siex(session: Session):
    """Función que crea no catálogo de proba os códigos de cultivo do SIEX que use unha
    proba (o cultivo ten clave allea a esa táboa): `cultivos_siex(197, 99)`."""
    return lambda *codigos: _engadir_cultivos_siex(session, *codigos)


def _engadir_cultivos_siex(session: Session, *codigos: int) -> None:
    from horta.models.catalogo import CatalogoVersion, CultivoSiex

    v = CatalogoVersion(catalogo="cultivo", nome_ficheiro="proba", sha256="c" * 64,
                        filas=len(codigos))
    session.add(v)
    session.flush()
    for codigo in codigos:
        if session.get(CultivoSiex, codigo) is None:
            session.add(CultivoSiex(codigo=codigo, nome_oficial=f"CULTIVO {codigo}",
                                    version_id=v.id))
    session.commit()

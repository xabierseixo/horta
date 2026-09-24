from __future__ import annotations

from typing import Callable

from nicegui import ui
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError


def executar_accion(session: Session, accion: Callable[[], object]) -> bool:
    """Executa unha acción que modifica datos e informa ao usuario se falla.

    Devolve True se a acción rematou ben. Os erros esperables (permiso
    denegado, regra de negocio, duplicado na BD) desfán a transacción e
    amósanse cun ui.notify en negativo en lugar de fallar en silencio.
    """
    try:
        accion()
    except PermisoDenegadoError as erro:
        session.rollback()
        ui.notify(str(erro), type="negative")
        return False
    except OperacionNonPermitidaError as erro:
        session.rollback()
        ui.notify(str(erro), type="negative")
        return False
    except IntegrityError:
        session.rollback()
        ui.notify("Xa existe un rexistro con eses datos", type="negative")
        return False
    return True

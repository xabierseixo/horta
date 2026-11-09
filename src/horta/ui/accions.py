from __future__ import annotations

from typing import Callable

from loguru import logger
from nicegui import app, ui
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from horta.idiomas import _
from horta.services.diario import TIPOS
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.ui.mensaxes_bd import mensaxe_integridade
from horta.ui.numeros import parsear_data


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
    except IntegrityError as erro:
        session.rollback()
        ui.notify(mensaxe_integridade(erro), type="negative")
        return False
    except Exception as erro:  # noqa: BLE001 — límite deliberado da capa de UI
        session.rollback()
        logger.exception("Erro non previsto en executar_accion: {}", erro)
        ui.notify(_("Ocorreu un erro inesperado. Téntao de novo."), type="negative")
        return False
    return True


def recargar_apuntado(tipo: str, data: str | None) -> None:
    """Recarga a páxina e, xa recargada, di que o traballo quedou apuntado (Y6)."""
    tipo_traducido = _(TIPOS[tipo]).lower() if tipo in TIPOS else tipo.lower()
    try:
        dia = parsear_data(data)
    except ValueError:
        dia = None
    if dia is not None:
        texto = _("Apuntado: {tipo} do {dia}").format(
            tipo=tipo_traducido, dia=f"{dia:%d/%m}"
        )
    else:
        texto = _("Apuntado: {tipo}").format(tipo=tipo_traducido)
    app.storage.user["aviso"] = texto
    ui.navigate.reload()


def mostrar_aviso_pendente() -> None:
    """O aviso que deixou `recargar_apuntado` antes de recargar."""
    texto = app.storage.user.pop("aviso", None)
    if texto:
        ui.notify(texto, type="positive")

"""A conexión de cada usuario co CUE da Xunta: a petición que se manda e o token que volve.
Gárdanse só na memoria do servidor, ata que caducan: nunca no disco nin na base de datos
."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from horta.services.errors import OperacionNonPermitidaError
from horta.services.xeaga import Token, Xeaga, ler_token

# Tempo para identificarse na Xunta e volver
_VIDA_PETICION = timedelta(minutes=15)


@dataclass
class _Peticion:
    usuario_id: int
    horta_id: int
    creada: datetime


_peticions: dict[str, _Peticion] = {}
_tokens: dict[tuple[int, int], Token] = {}


def xeaga_configurada() -> Xeaga | None:
    """O cliente da Xunta se o ficheiro de contorno ten a dirección e o nome da app."""
    url, app = os.environ.get("HORTA_XEAGA_URL"), os.environ.get("HORTA_XEAGA_APP")
    return Xeaga(url, app) if url and app else None


def nova_peticion(usuario_id: int, horta_id: int, agora: datetime | None = None) -> str:
    agora = agora or datetime.now(timezone.utc)
    for clave in [c for c, p in _peticions.items() if agora - p.creada > _VIDA_PETICION]:
        del _peticions[clave]
    peticion = str(secrets.randbelow(10**15) + 10**14)
    _peticions[peticion] = _Peticion(usuario_id, horta_id, agora)
    return peticion


def recibir_token(peticion: str, valor: str, usuario_id: int,
                  agora: datetime | None = None) -> tuple[int, Token]:
    """O token que volve da Xunta: só para quen pediu a conexión e a tempo."""
    agora = agora or datetime.now(timezone.utc)
    pedida = _peticions.pop(peticion, None)
    if pedida is None or pedida.usuario_id != usuario_id \
            or agora - pedida.creada > _VIDA_PETICION:
        raise OperacionNonPermitidaError("Esta conexión coa Xunta non se pediu desde aquí ou "
                                         "caducou: volve conectar")
    token = ler_token(valor)
    _tokens[(usuario_id, pedida.horta_id)] = token
    return pedida.horta_id, token


def token_vixente(usuario_id: int, horta_id: int) -> Token | None:
    token = _tokens.get((usuario_id, horta_id))
    if token is not None and not token.valido():
        del _tokens[(usuario_id, horta_id)]
        return None
    return token


def desconectar(usuario_id: int, horta_id: int) -> None:
    _tokens.pop((usuario_id, horta_id), None)

"""Xestión de dispositivos móbiles e claves de acceso para a app do campo."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from horta.models.dispositivo import Dispositivo
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError


def hash_token(token: str) -> str:
    """Calcula o hash SHA-256 dunha clave de dispositivo."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def crear_dispositivo(
    session: Session, actor: Usuario, nome: str
) -> tuple[Dispositivo, str]:
    """Crea un novo dispositivo cunha clave aleatoria e garda o seu hash."""
    nome_limpo = nome.strip() if nome else ""
    if not nome_limpo:
        raise OperacionNonPermitidaError("Indica o nome do dispositivo")
    clave = secrets.token_urlsafe(32)
    thash = hash_token(clave)
    dispositivo = Dispositivo(
        usuario_id=actor.id,
        nome=nome_limpo,
        token_hash=thash,
        creado_en=datetime.now(timezone.utc),
        ultimo_uso=None,
        revogado=False,
    )
    session.add(dispositivo)
    session.commit()
    return dispositivo, clave


def listar_dispositivos(session: Session, actor: Usuario) -> list[Dispositivo]:
    """Lista os dispositivos rexistrados polo propio usuario."""
    return list(
        session.query(Dispositivo)
        .filter_by(usuario_id=actor.id)
        .order_by(Dispositivo.creado_en.desc(), Dispositivo.id.desc())
        .all()
    )


def revogar_dispositivo(
    session: Session, actor: Usuario, dispositivo: Dispositivo
) -> Dispositivo:
    """Revoga un dispositivo móbil para que non poida volver conectarse."""
    if dispositivo.usuario_id != actor.id:
        raise PermisoDenegadoError("Non tes permiso para revogar este dispositivo")
    dispositivo.revogado = True
    session.commit()
    return dispositivo


def usuario_do_token(session: Session, token: str) -> Usuario | None:
    """Obtén o usuario asociado a un token vixente e actualiza o seu último uso."""
    if not token or not isinstance(token, str):
        return None
    thash = hash_token(token)
    dispositivo = session.query(Dispositivo).filter_by(token_hash=thash).first()
    if dispositivo is None or dispositivo.revogado:
        return None
    usuario = session.get(Usuario, dispositivo.usuario_id)
    if usuario is None or not usuario.activo:
        return None
    dispositivo.ultimo_uso = datetime.now(timezone.utc)
    session.commit()
    return usuario

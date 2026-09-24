from __future__ import annotations

import bcrypt
from sqlalchemy.orm import Session

from horta.models.usuario import Usuario


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def autenticar(session: Session, email: str, password: str) -> Usuario | None:
    usuario = session.query(Usuario).filter_by(email=email).one_or_none()
    if usuario is None or not usuario.activo:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario


def obter_usuario_activo(session: Session, usuario_id: int) -> Usuario | None:
    """Devolve o usuario da sesión só se aínda existe e segue activo."""
    usuario = session.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        return None
    return usuario

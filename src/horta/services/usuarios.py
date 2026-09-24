from __future__ import annotations

from sqlalchemy.orm import Session

from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import PermisoDenegadoError


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só un administrador pode xestionar usuarios")


def crear_usuario(
    session: Session,
    actor: Usuario,
    nome: str,
    email: str,
    password: str,
    rol: RolGlobal = RolGlobal.USUARIO,
) -> Usuario:
    _esixir_admin(actor)
    usuario = Usuario(
        nome=nome,
        email=email,
        password_hash=hash_password(password),
        rol=rol,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def actualizar_usuario(
    session: Session,
    actor: Usuario,
    usuario: Usuario,
    *,
    nome: str | None = None,
    rol: RolGlobal | None = None,
) -> Usuario:
    _esixir_admin(actor)
    if nome is not None:
        usuario.nome = nome
    if rol is not None:
        usuario.rol = rol
    session.commit()
    return usuario


def desactivar_usuario(session: Session, actor: Usuario, usuario: Usuario) -> Usuario:
    _esixir_admin(actor)
    usuario.activo = False
    session.commit()
    return usuario


def listar_usuarios(session: Session, actor: Usuario) -> list[Usuario]:
    _esixir_admin(actor)
    return list(session.query(Usuario).order_by(Usuario.nome).all())

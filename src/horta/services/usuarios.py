from __future__ import annotations

from sqlalchemy.orm import Session

from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password, normalizar_email
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só un administrador pode xestionar usuarios")


def _e_ultimo_admin_activo(session: Session, usuario: Usuario) -> bool:
    if usuario.rol != RolGlobal.ADMIN or not usuario.activo:
        return False
    admins_activos = session.query(Usuario).filter_by(rol=RolGlobal.ADMIN, activo=True).count()
    return admins_activos <= 1


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
        email=normalizar_email(email),
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
    if rol is not None and rol != RolGlobal.ADMIN and _e_ultimo_admin_activo(session, usuario):
        raise OperacionNonPermitidaError(
            "Non se pode quitar o rol de administrador ao último administrador activo"
        )
    if nome is not None:
        usuario.nome = nome
    if rol is not None:
        usuario.rol = rol
    session.commit()
    return usuario


def desactivar_usuario(session: Session, actor: Usuario, usuario: Usuario) -> Usuario:
    _esixir_admin(actor)
    if usuario.id == actor.id:
        raise OperacionNonPermitidaError("Non podes desactivar a túa propia conta")
    if _e_ultimo_admin_activo(session, usuario):
        raise OperacionNonPermitidaError("Non se pode desactivar o último administrador activo")
    usuario.activo = False
    session.commit()
    return usuario


def activar_usuario(session: Session, actor: Usuario, usuario: Usuario) -> Usuario:
    _esixir_admin(actor)
    usuario.activo = True
    session.commit()
    return usuario


def listar_usuarios(session: Session, actor: Usuario) -> list[Usuario]:
    _esixir_admin(actor)
    return list(session.query(Usuario).order_by(Usuario.nome).all())

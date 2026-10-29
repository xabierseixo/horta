"""Equipo da explotación: persoas, as súas funcións e o seu acceso á app.

O acceso gárdase en HortaMembro (fronteira de seguridade); a persoa liga coa súa conta
por usuario_id. Deseño: o deseño
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from horta.db import Base
from horta.models.categoria import persoa_categoria
from horta.models.convite import Convite
from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa, PersoaPapel
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password, normalizar_email
from horta.services.errors import OperacionNonPermitidaError
from horta.services.historial import Feito, por_referencia
from horta.services.hortas import (
    cambiar_rol_membro,
    comprobar_rol_horta,
    engadir_membro,
    quitar_membro,
)

HORAS_UTA = 1920
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def acceso_da_persoa(session: Session, persoa: Persoa) -> RolHorta | None:
    if persoa.usuario_id is None:
        return None
    membro = session.get(HortaMembro, (persoa.horta_id, persoa.usuario_id))
    return membro.rol if membro else None


def conceder_acceso(
    session: Session, actor: Usuario, persoa: Persoa, email: str, rol: RolHorta
) -> None:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    usuario = session.query(Usuario).filter_by(email=normalizar_email(email)).one_or_none()
    if usuario is None:
        raise OperacionNonPermitidaError(
            "Non hai ningunha conta con ese email. Pídelle ao administrador que a cree."
        )
    outra = (
        session.query(Persoa)
        .filter(Persoa.horta_id == persoa.horta_id, Persoa.usuario_id == usuario.id,
                Persoa.id != persoa.id)
        .first()
    )
    if outra is not None:
        raise OperacionNonPermitidaError(f"Esa conta xa está ligada a {outra.nome}")
    if session.get(HortaMembro, (persoa.horta_id, usuario.id)) is None:
        engadir_membro(session, actor, persoa.horta_id, usuario, rol)
    else:
        cambiar_rol_membro(session, actor, persoa.horta_id, usuario.id, rol)
    persoa.usuario_id = usuario.id
    session.commit()


def retirar_acceso(session: Session, actor: Usuario, persoa: Persoa) -> None:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    if persoa.usuario_id is None:
        return
    quitar_membro(session, actor, persoa.horta_id, persoa.usuario_id)
    persoa.usuario_id = None
    session.commit()


def uta_equipo(session: Session, actor: Usuario, horta_id: int) -> float:
    """Unidades de traballo agrario: horas ao ano das persoas activas / 1.920."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    horas = sum(
        p.horas_ano or 0
        for p in session.query(Persoa).filter_by(horta_id=horta_id, activa=True)
    )
    return round(horas / HORAS_UTA, 2)


# Convites (deseño global §2bis): unha ligazón para entrar, sen escribir correos de contas alleas
DIAS_CONVITE = 7


def crear_convite(session: Session, actor: Usuario, persoa: Persoa, rol: RolHorta,
                  agora: datetime | None = None) -> Convite:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    if persoa.usuario_id is not None:
        raise OperacionNonPermitidaError(f"{persoa.nome} xa ten acceso á app")
    agora = agora or datetime.now(timezone.utc).replace(tzinfo=None)
    # Só vale o último convite de cada persoa
    session.query(Convite).filter_by(persoa_id=persoa.id, usado=None).delete()
    convite = Convite(token=secrets.token_urlsafe(32), horta_id=persoa.horta_id,
                      persoa_id=persoa.id, rol=rol, creado_por=actor.id,
                      caduca=agora + timedelta(days=DIAS_CONVITE))
    session.add(convite)
    session.commit()
    return convite


def convite_valido(session: Session, token: str, agora: datetime | None = None) -> Convite:
    agora = agora or datetime.now(timezone.utc).replace(tzinfo=None)
    convite = session.query(Convite).filter_by(token=token).one_or_none()
    if convite is None or convite.usado is not None or convite.caduca < agora:
        raise OperacionNonPermitidaError(
            "Este convite non vale (xa se usou ou caducou). Pide outro a quen administra "
            "a explotación")
    return convite


def aceptar_convite(session: Session, token: str, usuario: Usuario,
                    agora: datetime | None = None) -> Persoa:
    """A conta entra na explotación co permiso do convite e queda ligada á súa ficha."""
    convite = convite_valido(session, token, agora)
    persoa = session.get(Persoa, convite.persoa_id)
    if persoa is None or persoa.usuario_id is not None:
        raise OperacionNonPermitidaError("Esa persoa xa ten acceso á app")
    outra = session.query(Persoa).filter_by(horta_id=convite.horta_id,
                                            usuario_id=usuario.id).first()
    if outra is not None:
        raise OperacionNonPermitidaError(
            f"A túa conta xa está nesta explotación como {outra.nome}")
    membro = session.get(HortaMembro, (convite.horta_id, usuario.id))
    if membro is None:
        session.add(HortaMembro(horta_id=convite.horta_id, usuario_id=usuario.id,
                                rol=convite.rol))
    else:
        membro.rol = convite.rol
    persoa.usuario_id = usuario.id
    convite.usado = agora or datetime.now(timezone.utc).replace(tzinfo=None)
    session.commit()
    return persoa


def crear_conta_con_convite(session: Session, token: str, email: str, contrasinal: str,
                            agora: datetime | None = None) -> Usuario:
    """Quen non ten conta créaa co seu propio contrasinal ao abrir o convite."""
    convite = convite_valido(session, token, agora)
    email = normalizar_email(email)
    if session.query(Usuario).filter_by(email=email).first() is not None:
        raise OperacionNonPermitidaError(
            "Xa hai unha conta con ese email: entra con ela e volve abrir a ligazón")
    if len(contrasinal) < 8:
        raise OperacionNonPermitidaError("O contrasinal ten que ter polo menos 8 caracteres")
    persoa = session.get(Persoa, convite.persoa_id)
    usuario = Usuario(nome=persoa.nome if persoa else email, email=email,
                      password_hash=hash_password(contrasinal), rol=RolGlobal.USUARIO,
                      activo=True)
    session.add(usuario)
    session.flush()
    aceptar_convite(session, token, usuario, agora)
    return usuario


def cambiar_permiso(session: Session, actor: Usuario, persoa: Persoa, rol: RolHorta) -> None:
    if persoa.usuario_id is None:
        raise OperacionNonPermitidaError(f"{persoa.nome} non ten acceso á app")
    cambiar_rol_membro(session, actor, persoa.horta_id, persoa.usuario_id, rol)


# Duplicados e xuntar (deseño global §2bis): a mesma persoa nunca dúas veces

def duplicados(session: Session, horta_id: int, nome: str, apelidos: str | None,
               nif: str | None, email: str | None, excepto: int | None = None) -> list[Persoa]:
    def igual(a: str | None, b: str | None) -> bool:
        return bool(a and b and a.strip().casefold() == b.strip().casefold())

    return [p for p in session.query(Persoa).filter(Persoa.horta_id == horta_id)
            if p.id != excepto and (
                igual(p.nif, nif) or igual(p.email, email)
                or (igual(p.nome, nome) and igual(p.apelidos or "-", apelidos or "-")))]


def xuntar_persoas(session: Session, actor: Usuario, queda: Persoa, sae: Persoa) -> Persoa:
    """Pasa todo o de «sae» a «queda» (traballos, compras, vendas, papeis, conta) e bórraa.
    Os datos baleiros de «queda» énchense cos de «sae»."""
    comprobar_rol_horta(session, queda.horta_id, actor, {RolHorta.ADMIN})
    if queda.id == sae.id or queda.horta_id != sae.horta_id:
        raise OperacionNonPermitidaError("Escolle dúas persoas distintas da explotación")
    if queda.usuario_id is not None and sae.usuario_id is not None:
        raise OperacionNonPermitidaError("As dúas teñen conta na app: quítalle o acceso a unha")
    for columna in Persoa.__table__.columns:
        if columna.name not in ("id", "horta_id", "created_at") \
                and getattr(queda, columna.key) in (None, "") \
                and getattr(sae, columna.key) not in (None, ""):
            setattr(queda, columna.key, getattr(sae, columna.key))
    usuario_id, sae.usuario_id = sae.usuario_id, None
    session.flush()
    if usuario_id is not None:
        queda.usuario_id = usuario_id
    for papel in sae.papeis - queda.papeis:
        queda.papeis_rexistro.append(PersoaPapel(papel=papel))
    session.flush()
    for taboa in Base.metadata.sorted_tables:
        for fk in taboa.foreign_keys:
            if fk.column.table.name == "persoa" and taboa.name not in ("persoa_papel",
                                                                       "persoa_categoria"):
                session.execute(update(taboa).where(fk.parent == sae.id)
                                .values({fk.parent.name: queda.id}))
    # As categorías libres: as da outra que aínda non ten
    tenta = set(session.scalars(select(persoa_categoria.c.categoria_id).where(
        persoa_categoria.c.persoa_id == queda.id)))
    for categoria_id in set(session.scalars(select(persoa_categoria.c.categoria_id).where(
            persoa_categoria.c.persoa_id == sae.id))) - tenta:
        session.execute(insert(persoa_categoria).values(persoa_id=queda.id,
                                                       categoria_id=categoria_id))
    session.execute(delete(persoa_categoria).where(persoa_categoria.c.persoa_id == sae.id))
    session.delete(sae)
    session.commit()
    return queda


def historial(session: Session, actor: Usuario, persoa: Persoa) -> list[Feito]:
    """Historial de cada contacto (CRM): sae do que xa se apunta, sen escribir nada a maiores."""
    comprobar_rol_horta(session, persoa.horta_id, actor, _ROLES_LECTURA)
    return por_referencia(session, "persoa", persoa.id,
                          excluir=("persoa_papel", "convite", "persoa_categoria"))

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, Fertilizante
from horta.models.analise import Analise
from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.labor import Labor
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError

# Campos que se poden modificar dende actualizar_horta. Queda fóra id e
# created_at, que non teñen sentido editar.
CAMPOS_EDITABLES_HORTA = frozenset(
    {
        "nome",
        "descricion",
        "uso_profesional",
        "titular_nome",
        "titular_nif",
        "codigo_reaga",
        "codigo_rega",
        "enderezo",
        "localidade",
        "codigo_postal",
        "provincia",
        "email",
        "tipo_representacion",
        "asesoramento_nome",
        "asesoramento_nif",
        "asesoramento_num",
        "tipo_xip",
        "asesoramento_fertilizacion",
    }
)
# Tipo de explotación en xestión integrada de pragas (modelo do caderno, 1.4)
TIPOS_XIP = {"AE": "Agricultura ecolóxica", "PI": "Produción integrada",
             "CP": "Certificación privada", "ATRIA": "Agrupación de tratamento integrado (ATRIA)",
             "AS": "Asistida por un asesor", "NO": "Sen obriga de asesor en XIP"}

# Patróns do descritor SIEX (Anexo VI): NIF/NIE de persoa física e CIF; código de
# explotación ES + 12 díxitos (codigoREA). O REGA segue o mesmo formato.
_PATRON_NIF = re.compile(
    r"^([KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]|[A-HJ-NP-SUVW]\d{7}[0-9A-J])$"
)
_PATRON_CODIGO = re.compile(r"^ES\d{12}$")


def _normalizar_e_validar_codigos(cambios: dict[str, Any]) -> None:
    for campo in ("titular_nif", "codigo_reaga", "codigo_rega"):
        if cambios.get(campo):
            cambios[campo] = cambios[campo].strip().upper().replace(" ", "")
        elif campo in cambios:
            cambios[campo] = None
    if cambios.get("tipo_xip") and cambios["tipo_xip"] not in TIPOS_XIP:
        raise OperacionNonPermitidaError("Tipo de explotación en XIP descoñecido")
    if cambios.get("titular_nif") and not _PATRON_NIF.match(cambios["titular_nif"]):
        raise OperacionNonPermitidaError("O NIF do titular non é válido")
    for campo, nome in (("codigo_reaga", "REAGA"), ("codigo_rega", "REGA")):
        if cambios.get(campo) and not _PATRON_CODIGO.match(cambios[campo]):
            raise OperacionNonPermitidaError(
                f"O código {nome} debe ter o formato ES seguido de 12 díxitos"
            )


def estado_rexistro(horta: Horta) -> str:
    """non_profesional | en_preparacion | rexistrada (calculado, non gardado)."""
    if not horta.uso_profesional:
        return "non_profesional"
    if horta.titular_nif and horta.codigo_reaga:
        return "rexistrada"
    return "en_preparacion"


def _obter_membro(session: Session, horta_id: int, usuario_id: int) -> HortaMembro | None:
    return session.get(HortaMembro, (horta_id, usuario_id))


def _e_ultimo_admin_da_horta(session: Session, membro: HortaMembro) -> bool:
    if membro.rol != RolHorta.ADMIN:
        return False
    admins = (
        session.query(HortaMembro).filter_by(horta_id=membro.horta_id, rol=RolHorta.ADMIN).count()
    )
    return admins <= 1


def comprobar_rol_horta(
    session: Session,
    horta_id: int,
    usuario: Usuario,
    roles_permitidos: set[RolHorta],
) -> HortaMembro:
    membro = _obter_membro(session, horta_id, usuario.id)
    if membro is None or membro.rol not in roles_permitidos:
        raise PermisoDenegadoError("Non tes permiso suficiente nesta explotación")
    return membro


def crear_horta(
    session: Session,
    actor: Usuario,
    nome: str,
    descricion: str | None = None,
    uso_profesional: bool = False,
) -> Horta:
    horta = Horta(nome=nome, descricion=descricion, uso_profesional=uso_profesional)
    session.add(horta)
    session.flush()
    membro = HortaMembro(horta_id=horta.id, usuario_id=actor.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.add(Persoa(horta_id=horta.id, nome=actor.nome, usuario_id=actor.id,
                       email=actor.email))
    session.commit()
    return horta


def actualizar_horta(
    session: Session,
    actor: Usuario,
    horta: Horta,
    **cambios: Any,
) -> Horta:
    non_editables = set(cambios) - CAMPOS_EDITABLES_HORTA
    if non_editables:
        raise ValueError(f"Campos non editables nunha horta: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    _normalizar_e_validar_codigos(cambios)
    for campo, valor in cambios.items():
        setattr(horta, campo, valor)
    session.commit()
    return horta


def eliminar_horta(session: Session, actor: Usuario, horta: Horta) -> None:
    """Elimina a horta e todo o que dependa dela (parcelas, animais, membros).

    Non hai borrado en cascada a nivel de base de datos (sen relacións
    SQLAlchemy nin FKs ON DELETE CASCADE), así que hai que borrar
    explicitamente os rexistros dependentes antes da propia horta.
    """
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    if session.query(TratamentoFito).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten tratamentos fitosanitarios rexistrados e debe conservarse "
            "(obriga legal)."
        )
    if session.query(Abonado).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten abonados rexistrados e debe conservarse (obriga legal)."
        )
    if session.query(Rega).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten regas rexistradas e debe conservarse (obriga legal)."
        )
    if session.query(Labor).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten labores rexistrados e debe conservarse (obriga legal)."
        )
    if session.query(CoidadoAnimal).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten coidados de animais rexistrados e debe conservarse "
            "(obriga legal)."
        )
    if session.query(MovementoAnimal).filter(
        MovementoAnimal.horta_id == horta.id, MovementoAnimal.tipo != "inicial"
    ).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten entradas e saídas de animais rexistradas e debe conservarse "
            "(obriga legal)."
        )
    session.query(Fertilizante).filter_by(horta_id=horta.id).delete()
    for analise in session.query(Analise).filter_by(horta_id=horta.id).all():
        session.delete(analise)
    session.flush()
    for tarefa in session.query(Tarefa).filter_by(horta_id=horta.id).all():
        session.delete(tarefa)
    # As Tarefas poden referenciar Parcela/Cultivo (FK opcionais) — hai que
    # borralas e facer flush ANTES de tocar Parcela/Cultivo, senón o borrado
    # dunha Tarefa violaría a FK se o seu Cultivo/Parcela xa se borrou antes.
    session.flush()
    parcelas = session.query(Parcela).filter_by(horta_id=horta.id).all()
    parcela_ids = [p.id for p in parcelas]
    cultivos = (
        session.query(Cultivo).filter(Cultivo.parcela_id.in_(parcela_ids)).all()
        if parcela_ids
        else []
    )
    for cultivo in cultivos:
        session.delete(cultivo)
    session.flush()
    for parcela in parcelas:
        session.delete(parcela)
    session.query(MovementoAnimal).filter_by(horta_id=horta.id).delete()
    session.flush()
    for animal in session.query(Animal).filter_by(horta_id=horta.id).all():
        session.delete(animal)
    for membro in session.query(HortaMembro).filter_by(horta_id=horta.id).all():
        session.delete(membro)
    for persoa in session.query(Persoa).filter_by(horta_id=horta.id).all():
        session.delete(persoa)
    for maquina in session.query(Maquina).filter_by(horta_id=horta.id).all():
        session.delete(maquina)
    # SQLAlchemy non ten relationship() entre estes modelos, así que non hai
    # información de dependencia para ordenar o DELETE automaticamente. Sen
    # este flush, os borrados poden enviarse na orde inversa (horta antes dos
    # seus fillos), o que falla en calquera BD que comprobe as FKs.
    session.flush()
    session.delete(horta)
    session.commit()


def engadir_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo: Usuario,
    rol: RolHorta,
) -> HortaMembro:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = HortaMembro(horta_id=horta_id, usuario_id=usuario_obxectivo.id, rol=rol)
    session.add(membro)
    session.commit()
    return membro


def cambiar_rol_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo_id: int,
    novo_rol: RolHorta,
) -> HortaMembro:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = _obter_membro(session, horta_id, usuario_obxectivo_id)
    if membro is None:
        raise OperacionNonPermitidaError("Ese usuario non é membro desta explotación")
    if novo_rol != RolHorta.ADMIN and _e_ultimo_admin_da_horta(session, membro):
        raise OperacionNonPermitidaError("A explotación debe ter polo menos un administrador")
    membro.rol = novo_rol
    session.commit()
    return membro


def quitar_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo_id: int,
) -> None:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = _obter_membro(session, horta_id, usuario_obxectivo_id)
    if membro is not None:
        if _e_ultimo_admin_da_horta(session, membro):
            raise OperacionNonPermitidaError("A explotación debe ter polo menos un administrador")
        session.delete(membro)
        session.commit()


def listar_hortas_usuario(session: Session, usuario: Usuario) -> list[tuple[Horta, RolHorta]]:
    membros = session.query(HortaMembro).filter_by(usuario_id=usuario.id).all()
    resultado: list[tuple[Horta, RolHorta]] = []
    for membro in membros:
        horta = session.get(Horta, membro.horta_id)
        assert horta is not None
        resultado.append((horta, membro.rol))
    return resultado

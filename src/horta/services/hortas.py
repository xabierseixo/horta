from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.acceso import RexistroAcceso
from horta.models.analise import Analise
from horta.models.animal import Animal, AnimalIdentificado
from horta.models.cartos import ApunteCartos
from horta.models.categoria import Categoria, persoa_categoria
from horta.models.colleita import Colleita
from horta.models.convite import Convite
from horta.models.cultivo import Cultivo
from horta.models.envio_cue import EnvioCue, RexistroCue
from horta.models.foto import Foto
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.instalacion import Instalacion
from horta.models.lote import (
    Clasificacion,
    ClasificacionClase,
    Lote,
    LoteSaida,
    Mestura,
    MesturaOrixe,
    ProdutoVenda,
    Transformacion,
    TransformacionEntrada,
    TransformacionInsumo,
)
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa, PersoaPapel
from horta.models.plan_empresa import (
    PlanAno,
    PlanEmpresa,
    PlanFinanciamento,
    PlanInvestimento,
    PlanOferta,
)
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto, Produto
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.models.zona import ParcelaZona
from horta.services.conservar import comprobar_conservar
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError

# Campos que se poden modificar dende actualizar_horta. Queda fóra id e
# created_at, que non teñen sentido editar.
CAMPOS_EDITABLES_HORTA = frozenset(
    {
        "nome",
        "descricion",
        "uso_profesional",
        "codigo_reaga",
        "codigo_rega",
        "rega_clasificacion",
        "rega_capacidade",
        "enderezo",
        "localidade",
        "codigo_postal",
        "provincia",
        "email",
        "tipo_representacion",
        "tipo_xip",
        "asesoramento_fertilizacion",
    }
)
# Tipo de explotación en xestión integrada de pragas (modelo do caderno, 1.4)
TIPOS_XIP = {"AE": "Agricultura ecolóxica", "PI": "Produción integrada",
             "CP": "Certificación privada", "ATRIA": "Agrupación de tratamento integrado (ATRIA)",
             "AS": "Asistida por un asesor", "NO": "Sen obriga de asesor en XIP"}

# Patrón do descritor SIEX (Anexo VI): código de explotación ES + 12 díxitos (codigoREA).
# O REGA segue o mesmo formato.
_PATRON_CODIGO = re.compile(r"^ES\d{12}$")


def _normalizar_e_validar_codigos(cambios: dict[str, Any]) -> None:
    for campo in ("codigo_reaga", "codigo_rega"):
        if cambios.get(campo):
            cambios[campo] = cambios[campo].strip().upper().replace(" ", "")
        elif campo in cambios:
            cambios[campo] = None
    if cambios.get("tipo_xip") and cambios["tipo_xip"] not in TIPOS_XIP:
        raise OperacionNonPermitidaError("Tipo de explotación en XIP descoñecido")
    for campo, nome in (("codigo_reaga", "REAGA"), ("codigo_rega", "REGA")):
        if cambios.get(campo) and not _PATRON_CODIGO.match(cambios[campo]):
            raise OperacionNonPermitidaError(
                f"O código {nome} debe ter o formato ES seguido de 12 díxitos"
            )


def estado_rexistro(session: Session, horta: Horta) -> str:
    """non_profesional | en_preparacion | rexistrada (calculado, non gardado): rexistrada se
    ten REAGA e o titular (a persoa co papel titular) ten NIF."""
    if not horta.uso_profesional:
        return "non_profesional"
    nif_titular = (session.query(Persoa.nif).join(PersoaPapel)
                   .filter(Persoa.horta_id == horta.id, Persoa.activa.is_(True),
                           PersoaPapel.papel == "titular").scalar())
    if nif_titular and horta.codigo_reaga:
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
    if membro is None:
        raise PermisoDenegadoError("Non tes permiso suficiente nesta explotación")
    if membro.acceso_ata is not None and membro.acceso_ata < date.today():
        data_fmt = membro.acceso_ata.strftime("%d/%m/%Y")
        raise PermisoDenegadoError(f"O teu acceso a esta explotación rematou o {data_fmt}")
    if membro.rol not in roles_permitidos:
        raise PermisoDenegadoError("Non tes permiso suficiente nesta explotación")
    return membro


def crear_horta(
    session: Session,
    actor: Usuario,
    nome: str,
    descricion: str | None = None,
    uso_profesional: bool = False,
    son_titular: bool = False,
) -> Horta:
    horta = Horta(nome=nome, descricion=descricion, uso_profesional=uso_profesional)
    session.add(horta)
    session.flush()
    membro = HortaMembro(horta_id=horta.id, usuario_id=actor.id, rol=RolHorta.ADMIN)
    session.add(membro)
    # Quen crea a explotación di se é o titular (Z1); se non, queda como traballador
    papeis = ["titular", "traballador"] if son_titular else ["traballador"]
    session.add(Persoa(horta_id=horta.id, nome=actor.nome, usuario_id=actor.id,
                       email=actor.email,
                       papeis_rexistro=[PersoaPapel(papel=p) for p in papeis]))
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
    """Elimina a horta e todo o que dependa dela.

    Non hai borrado en cascada a nivel de base de datos (sen relacións
    SQLAlchemy nin FKs ON DELETE CASCADE), así que hai que borrar
    explicitamente os rexistros dependentes antes da propia horta.
    """
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    comprobar_conservar(session, horta)

    # 1. Envíos e rexistros CUE
    session.query(RexistroCue).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.query(EnvioCue).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 2. Plan de empresa e subtáboas (Anexos III, V, VI)
    plan_ids = [p.id for p in session.query(PlanEmpresa).filter_by(horta_id=horta.id).all()]
    if plan_ids:
        inv_ids = [
            row[0]
            for row in session.query(PlanInvestimento.id)
            .filter(PlanInvestimento.plan_id.in_(plan_ids))
            .all()
        ]
        if inv_ids:
            session.query(PlanOferta).filter(PlanOferta.investimento_id.in_(inv_ids)).delete(
                synchronize_session=False
            )
            session.flush()
        session.query(PlanInvestimento).filter(PlanInvestimento.plan_id.in_(plan_ids)).delete(
            synchronize_session=False
        )
        session.query(PlanFinanciamento).filter(PlanFinanciamento.plan_id.in_(plan_ids)).delete(
            synchronize_session=False
        )
        session.query(PlanAno).filter(PlanAno.plan_id.in_(plan_ids)).delete(
            synchronize_session=False
        )
        session.flush()
        session.query(PlanEmpresa).filter_by(horta_id=horta.id).delete(synchronize_session=False)
        session.flush()

    # 3. Fotos
    session.query(Foto).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 4. Apuntes de cartos
    session.query(ApunteCartos).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 5. Lotes e todas as súas dependencias
    t_ids = [
        row[0]
        for row in session.query(Transformacion.id).filter_by(horta_id=horta.id).all()
    ]
    if t_ids:
        session.query(TransformacionEntrada).filter(
            TransformacionEntrada.transformacion_id.in_(t_ids)
        ).delete(synchronize_session=False)
        session.query(TransformacionInsumo).filter(
            TransformacionInsumo.transformacion_id.in_(t_ids)
        ).delete(synchronize_session=False)
        session.flush()
        session.query(Transformacion).filter_by(horta_id=horta.id).delete(
            synchronize_session=False
        )
        session.flush()

    m_ids = [
        row[0]
        for row in session.query(Mestura.id).filter_by(horta_id=horta.id).all()
    ]
    if m_ids:
        session.query(MesturaOrixe).filter(MesturaOrixe.mestura_id.in_(m_ids)).delete(
            synchronize_session=False
        )
        session.flush()
        session.query(Mestura).filter_by(horta_id=horta.id).delete(synchronize_session=False)
        session.flush()

    cl_ids = [
        row[0]
        for row in session.query(Clasificacion.id).filter_by(horta_id=horta.id).all()
    ]
    if cl_ids:
        session.query(ClasificacionClase).filter(
            ClasificacionClase.clasificacion_id.in_(cl_ids)
        ).delete(synchronize_session=False)
        session.flush()
        session.query(Clasificacion).filter_by(horta_id=horta.id).delete(
            synchronize_session=False
        )
        session.flush()

    session.query(LoteSaida).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    parcelas = session.query(Parcela).filter_by(horta_id=horta.id).all()
    parcela_ids = [p.id for p in parcelas]
    cultivos = (
        session.query(Cultivo).filter(Cultivo.parcela_id.in_(parcela_ids)).all()
        if parcela_ids
        else []
    )
    cultivo_ids = [c.id for c in cultivos]
    lote_ids = [row[0] for row in session.query(Lote.id).filter_by(horta_id=horta.id).all()]

    conds = []
    if cultivo_ids:
        conds.append(Colleita.cultivo_id.in_(cultivo_ids))
    if lote_ids:
        conds.append(Colleita.lote_id.in_(lote_ids))
    if conds:
        session.query(Colleita).filter(or_(*conds)).delete(synchronize_session=False)
        session.flush()

    session.query(ProducionAnimal).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    session.query(Lote).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    session.query(ProdutoVenda).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 6. Outros traballos, produtos e fertilizantes
    session.query(OutroTraballo).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    session.query(EntradaProduto).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    session.query(Produto).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    session.query(Fertilizante).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 7. Análises e tarefas
    for analise in session.query(Analise).filter_by(horta_id=horta.id).all():
        session.delete(analise)
    session.flush()

    for tarefa in session.query(Tarefa).filter_by(horta_id=horta.id).all():
        session.delete(tarefa)
    session.flush()

    # 8. Cultivos, zonas debuxadas e parcelas
    for cultivo in cultivos:
        session.delete(cultivo)
    session.flush()

    if parcela_ids:
        session.query(ParcelaZona).filter(ParcelaZona.parcela_id.in_(parcela_ids)).delete(
            synchronize_session=False
        )
        session.flush()

    for parcela in parcelas:
        session.delete(parcela)
    session.flush()

    # 9. Animais e instalacións
    animais = session.query(Animal).filter_by(horta_id=horta.id).all()
    animal_ids = [a.id for a in animais]
    if animal_ids:
        session.query(AnimalIdentificado).filter(AnimalIdentificado.animal_id.in_(animal_ids)).delete(
            synchronize_session=False
        )
        session.flush()

    session.query(MovementoAnimal).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    for animal in animais:
        session.delete(animal)
    session.flush()

    session.query(Instalacion).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 10. Máquinas
    for maquina in session.query(Maquina).filter_by(horta_id=horta.id).all():
        session.delete(maquina)
    session.flush()

    # 11. Membros, convites, categorías e persoas
    session.query(RexistroAcceso).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    for membro in session.query(HortaMembro).filter_by(horta_id=horta.id).all():
        session.delete(membro)
    session.flush()

    session.query(Convite).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    persoas = session.query(Persoa).filter_by(horta_id=horta.id).all()
    ids_persoas = [p.id for p in persoas]
    if ids_persoas:
        session.execute(delete(persoa_categoria).where(
            persoa_categoria.c.persoa_id.in_(ids_persoas)))
        session.flush()

    for persoa in persoas:
        session.delete(persoa)
    session.flush()

    session.query(Categoria).filter_by(horta_id=horta.id).delete(synchronize_session=False)
    session.flush()

    # 12. A explotación
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
    hoxe = date.today()
    for membro in membros:
        if membro.acceso_ata is not None and membro.acceso_ata < hoxe:
            continue
        horta = session.get(Horta, membro.horta_id)
        assert horta is not None
        resultado.append((horta, membro.rol))
    return resultado

"""Tratamentos de postcolleita, locais de almacenamento e transporte (caderno 3.3–3.5)."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.models.tratamento_instalacion import TIPOS_INSTALACION, TratamentoInstalacion
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass
class DatosTratamentoInstalacion:
    tipo: str
    data: date
    obxecto: str
    referencia_catastral: str | None = None
    problema_tipo: str | None = None
    problema_codigo: str | None = None
    xustificacion: str | None = None
    cantidade_tratada: float | None = None
    tipo_produto: str | None = None
    nome_comercial: str | None = None
    num_rexistro: str | None = None
    materia_activa: str | None = None
    cantidade_utilizada: float | None = None
    unidade: str | None = None
    notas: str | None = None
    persoa_id: int | None = None
    horas: float | None = None


def _validar(session: Session, datos: DatosTratamentoInstalacion, hoxe: date) -> None:
    if datos.tipo not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle se é postcolleita, local ou transporte")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data do tratamento non pode ser futura")
    if not datos.obxecto.strip():
        raise OperacionNonPermitidaError("Indica que se tratou")
    if not (datos.nome_comercial or datos.materia_activa):
        raise OperacionNonPermitidaError("Indica o produto (nome comercial ou materia activa)")
    for cantidade in (datos.cantidade_tratada, datos.cantidade_utilizada):
        if cantidade is not None and cantidade <= 0:
            raise OperacionNonPermitidaError("As cantidades teñen que ser maiores que 0")
    if datos.problema_codigo:
        if datos.problema_tipo not in TIPOS_PROBLEMA:
            raise OperacionNonPermitidaError("Tipo de problema descoñecido")
        validar_codigo(session, datos.problema_tipo, datos.problema_codigo, datos.data)
    for catalogo, codigo in (("xustificacion", datos.xustificacion),
                             ("tipo_produto", datos.tipo_produto),
                             ("unidade_medida", datos.unidade)):
        if codigo:
            validar_codigo(session, catalogo, codigo, datos.data)


def _copiar(tratamento: TratamentoInstalacion, datos: DatosTratamentoInstalacion) -> None:
    for campo in fields(datos):
        valor = getattr(datos, campo.name)
        setattr(tratamento, campo.name, valor.strip() or None if isinstance(valor, str)
                and campo.name not in ("tipo", "obxecto") else valor)
    tratamento.obxecto = datos.obxecto.strip()


def crear_tratamento_instalacion(
    session: Session, actor: Usuario, horta_id: int, datos: DatosTratamentoInstalacion,
    hoxe: date | None = None,
) -> TratamentoInstalacion:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
    tratamento = TratamentoInstalacion(horta_id=horta_id, creado_por=actor.id)
    _copiar(tratamento, datos)
    session.add(tratamento)
    session.commit()
    return tratamento


def actualizar_tratamento_instalacion(
    session: Session, actor: Usuario, tratamento: TratamentoInstalacion,
    datos: DatosTratamentoInstalacion, hoxe: date | None = None,
) -> TratamentoInstalacion:
    if tratamento.baixa:
        raise OperacionNonPermitidaError("Un tratamento dado de baixa non se pode modificar")
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
    _copiar(tratamento, datos)
    session.commit()
    return tratamento


def dar_de_baixa_tratamento_instalacion(
    session: Session, actor: Usuario, tratamento: TratamentoInstalacion
) -> None:
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    tratamento.baixa = True
    session.commit()


def listar_tratamentos_instalacion(
    session: Session, actor: Usuario, horta_id: int
) -> list[TratamentoInstalacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(TratamentoInstalacion).filter_by(horta_id=horta_id, baixa=False)
                .order_by(TratamentoInstalacion.data.desc(), TratamentoInstalacion.id.desc()))

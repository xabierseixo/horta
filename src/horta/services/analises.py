"""Análises de cultivo, produto colleitado, solo ou auga (CUE bloque 13). Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.analise import Analise, AnaliseSubstancia, AnaliseTipo
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
SOLO = "3"  # catálogo MATERIAL_ANALIZADO
_PORCENTAXES = ("materia_organica", "area", "limo", "arxila", "n_total")
CAMPOS_SOLO = (*_PORCENTAXES, "ph", "fosforo_ppm", "potasio_ppm", "conductividade")


@dataclass
class DatosAnalise:
    material_analizado: str
    data_mostraxe: date
    tipos: list[str] = field(default_factory=list)
    substancias: list[str] = field(default_factory=list)
    laboratorio: str | None = None
    laboratorio_nif: str | None = None
    num_boletin: str | None = None
    parcela_id: int | None = None
    cultivo_id: int | None = None
    colleita_id: int | None = None
    solo: dict[str, float | None] = field(default_factory=dict)
    notas: str | None = None


def _horta_de(session: Session, modelo: type, ident: int | None) -> int | None:
    if ident is None:
        return None
    obxecto = session.get(modelo, ident)
    if obxecto is None:
        return -1
    if isinstance(obxecto, Parcela):
        return obxecto.horta_id
    cultivo = obxecto if isinstance(obxecto, Cultivo) else session.get(Cultivo, obxecto.cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    return parcela.horta_id if parcela else -1


def _validar(session: Session, horta_id: int, datos: DatosAnalise, hoxe: date) -> None:
    if datos.data_mostraxe > hoxe:
        raise OperacionNonPermitidaError("A data da mostra non pode ser futura")
    validar_codigo(session, "material_analizado", datos.material_analizado, datos.data_mostraxe)
    for codigo in datos.tipos:
        validar_codigo(session, "tipo_analise", codigo, datos.data_mostraxe)
    for codigo in datos.substancias:
        validar_codigo(session, "substancia_activa", codigo, datos.data_mostraxe)
    for modelo, ident in ((Parcela, datos.parcela_id), (Cultivo, datos.cultivo_id),
                          (Colleita, datos.colleita_id)):
        if _horta_de(session, modelo, ident) not in (None, horta_id):
            raise OperacionNonPermitidaError("A parcela, cultivo ou lote non é desta explotación")
    valores = {k: v for k, v in datos.solo.items() if v is not None}
    if valores and datos.material_analizado != SOLO:
        raise OperacionNonPermitidaError("Os parámetros do solo só van nas análises de solo")
    if set(valores) - set(CAMPOS_SOLO):
        raise OperacionNonPermitidaError("Parámetro do solo descoñecido")
    for campo in _PORCENTAXES:
        if campo in valores and not 0 <= valores[campo] <= 100:
            raise OperacionNonPermitidaError("As porcentaxes van de 0 a 100")
    if "ph" in valores and not 0 <= valores["ph"] <= 14:
        raise OperacionNonPermitidaError("O pH vai de 0 a 14")


def _copiar(analise: Analise, horta_id: int, datos: DatosAnalise) -> None:
    analise.horta_id = horta_id
    analise.material_analizado = datos.material_analizado
    analise.data_mostraxe = datos.data_mostraxe
    analise.laboratorio = datos.laboratorio or None
    analise.laboratorio_nif = datos.laboratorio_nif or None
    analise.num_boletin = datos.num_boletin or None
    analise.parcela_id = datos.parcela_id
    analise.cultivo_id = datos.cultivo_id
    analise.colleita_id = datos.colleita_id
    for campo in CAMPOS_SOLO:
        setattr(analise, campo, datos.solo.get(campo))
    analise.notas = datos.notas or None
    analise.tipos = [AnaliseTipo(codigo=c) for c in datos.tipos]
    analise.substancias = [AnaliseSubstancia(codigo=c) for c in datos.substancias]


def crear_analise(
    session: Session, actor: Usuario, horta_id: int, datos: DatosAnalise,
    hoxe: date | None = None,
) -> Analise:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, horta_id, datos, hoxe or date.today())
    analise = Analise(creado_por=actor.id)
    _copiar(analise, horta_id, datos)
    session.add(analise)
    session.commit()
    return analise


def actualizar_analise(
    session: Session, actor: Usuario, analise: Analise, datos: DatosAnalise,
    hoxe: date | None = None,
) -> Analise:
    if analise.baixa:
        raise OperacionNonPermitidaError("Unha análise dada de baixa non se pode modificar")
    comprobar_rol_horta(session, analise.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, analise.horta_id, datos, hoxe or date.today())
    _copiar(analise, analise.horta_id, datos)
    session.commit()
    return analise


def dar_de_baixa_analise(session: Session, actor: Usuario, analise: Analise) -> None:
    comprobar_rol_horta(session, analise.horta_id, actor, _ROLES_ESCRITURA)
    analise.baixa = True
    session.commit()


def listar_analises(session: Session, actor: Usuario, horta_id: int) -> list[Analise]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Analise).filter_by(horta_id=horta_id, baixa=False)
                .order_by(Analise.data_mostraxe.desc(), Analise.id.desc()))

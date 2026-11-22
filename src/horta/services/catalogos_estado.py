"""Estado dos catálogos oficiais, aviso para a administración e actualización con permisos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex
from horta.models.comprobacion_catalogo import ComprobacionCatalogo
from horta.models.fertilizante import FertilizanteSiex
from horta.models.usuario import RolGlobal, Usuario
from horta.services.catalogos_ficheiros import CATALOGOS_APP, Revision, revisar
from horta.services.catalogos_importar import InformeImportacion
from horta.services.errors import PermisoDenegadoError
from horta.services.fito_descargar import actualizar_fitosanitarios, ultima_comprobacion

DIAS_AVISO = 60
FEGA = "fega"  # comprobación manual dos catálogos do FEGA (aínda que non trouxesen cambios)


@dataclass
class EstadoCatalogo:
    clave: str
    nome: str
    ficheiro: str
    codigos: int
    importado: datetime | None


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só a administración pode actualizar os catálogos oficiais")


def estado_catalogos(session: Session) -> list[EstadoCatalogo]:
    ultimas: dict[str, datetime] = {
        catalogo: data for catalogo, data in session.query(
            CatalogoVersion.catalogo, func.max(CatalogoVersion.data_importacion)
        ).group_by(CatalogoVersion.catalogo)}
    codigos: dict[str, int] = {
        catalogo: n for catalogo, n in session.query(
            CatalogoValor.catalogo, func.count()).filter(CatalogoValor.data_baixa.is_(None)
                                                        ).group_by(CatalogoValor.catalogo)}
    codigos["cultivo"] = session.query(CultivoSiex).filter(CultivoSiex.data_baixa.is_(None)).count()
    codigos["variedade"] = session.query(VariedadeSiex).filter(
        VariedadeSiex.data_baixa.is_(None)).count()
    codigos["fertilizante"] = session.query(FertilizanteSiex).filter(
        FertilizanteSiex.data_baixa.is_(None)).count()
    return [EstadoCatalogo(clave, nome, f"{codigo}.xlsx", codigos.get(clave, 0),
                           ultimas.get(clave))
            for clave, (codigo, _, nome) in CATALOGOS_APP.items()]


def ultima_revision_fega(session: Session) -> datetime | None:
    """Última vez que alguén revisou os catálogos do FEGA: importación con cambios ou subida
    revisada aínda que non trouxese cambios."""
    datas = [e.importado for e in estado_catalogos(session) if e.importado]
    comprobacion = session.get(ComprobacionCatalogo, FEGA)
    if comprobacion is not None:
        datas.append(comprobacion.data)
    return max(datas) if datas else None


def avisos_catalogos(session: Session, agora: datetime | None = None) -> list[str]:
    agora = agora or datetime.now()
    avisos = []
    faltan = [e.nome for e in estado_catalogos(session) if e.importado is None]
    if faltan:
        avisos.append(f"Faltan catálogos oficiais: {', '.join(faltan)}.")
    revision = ultima_revision_fega(session)
    if revision is not None and (agora - revision).days > DIAS_AVISO:
        avisos.append(f"Os catálogos oficiais do FEGA levan {(agora - revision).days} días sen "
                      "revisar: descárgaos de novo e súbeos.")
    fito = ultima_comprobacion(session)
    if fito is not None and fito.erro:
        avisos.append(f"Fallou a descarga do rexistro de fitosanitarios do MAPA o "
                      f"{fito.data:%d/%m/%Y}. A app segue coa copia anterior.")
    return avisos


def revisar_ficheiros(session: Session, actor: Usuario, rutas: list[Path],
                      aplicar: bool = False, agora: datetime | None = None) -> list[Revision]:
    _esixir_admin(actor)
    revisions = revisar(session, rutas, aplicar=aplicar)
    if aplicar and any(r.informe is not None for r in revisions):
        comprobacion = session.get(ComprobacionCatalogo, FEGA) or ComprobacionCatalogo(
            catalogo=FEGA, data=agora or datetime.now())
        comprobacion.data, comprobacion.erro = agora or datetime.now(), None
        session.add(comprobacion)
        session.commit()
    return revisions


def actualizar_rexistro_mapa(session: Session, actor: Usuario) -> InformeImportacion:
    _esixir_admin(actor)
    informe = actualizar_fitosanitarios(session, forzar=True)
    assert informe is not None
    return informe

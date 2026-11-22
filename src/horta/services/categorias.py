"""Categorías dos contactos (deseño global §2bis): todas libres, coas da app xa creadas."""

from __future__ import annotations

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from horta.models.categoria import Categoria, persoa_categoria
from horta.models.horta import RolHorta
from horta.models.persoa import Persoa, PersoaPapel
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import PAPEIS_CONTACTO

_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# As que trae a app (cada unha cun papel que usan o caderno e os formularios)
INICIAIS = {**PAPEIS_CONTACTO, "servizos": "Fai traballos (persoa ou empresa)"}


def listar_categorias(session: Session, actor: Usuario, horta_id: int) -> list[Categoria]:
    comprobar_rol_horta(session, horta_id, actor, _LECTURA)
    existentes = {c.papel for c in session.query(Categoria).filter_by(horta_id=horta_id)}
    for papel, nome in INICIAIS.items():
        if papel not in existentes:
            session.add(Categoria(horta_id=horta_id, nome=nome, papel=papel))
    session.commit()
    return list(session.query(Categoria).filter_by(horta_id=horta_id).order_by(Categoria.nome))


def _nome(nome: str) -> str:
    nome = nome.strip()
    if not nome:
        raise OperacionNonPermitidaError("Indica o nome da categoría")
    return nome


def crear_categoria(session: Session, actor: Usuario, horta_id: int, nome: str) -> Categoria:
    comprobar_rol_horta(session, horta_id, actor, _ESCRITURA)
    categoria = Categoria(horta_id=horta_id, nome=_nome(nome))
    session.add(categoria)
    session.commit()
    return categoria


def renomear_categoria(session: Session, actor: Usuario, categoria: Categoria, nome: str) -> None:
    comprobar_rol_horta(session, categoria.horta_id, actor, _ESCRITURA)
    categoria.nome = _nome(nome)
    session.commit()


def borrar_categoria(session: Session, actor: Usuario, categoria: Categoria) -> None:
    comprobar_rol_horta(session, categoria.horta_id, actor, _ESCRITURA)
    if categoria.papel is not None:
        raise OperacionNonPermitidaError(
            "A app usa esta categoría (caderno, formularios): podes cambiarlle o nome, pero "
            "non borrala")
    session.execute(delete(persoa_categoria).where(
        persoa_categoria.c.categoria_id == categoria.id))
    session.delete(categoria)
    session.commit()


def categorias_da_persoa(session: Session, persoa: Persoa) -> set[int]:
    libres = set(session.scalars(select(persoa_categoria.c.categoria_id).where(
        persoa_categoria.c.persoa_id == persoa.id)))
    con_papel = {c.id for c in session.query(Categoria).filter(
        Categoria.horta_id == persoa.horta_id, Categoria.papel.in_(persoa.papeis))}
    return libres | con_papel


def asignar_categorias(session: Session, actor: Usuario, persoa: Persoa,
                     ids: set[int]) -> None:
    """As categorías dun contacto. Os papeis do equipo (titular, traballador...) non se tocan."""
    comprobar_rol_horta(session, persoa.horta_id, actor, _ESCRITURA)
    categorias = {c.id: c for c in session.query(Categoria).filter_by(horta_id=persoa.horta_id)}
    if not ids <= set(categorias):
        raise OperacionNonPermitidaError("Esa categoría non é desta explotación")
    papeis = {categorias[i].papel for i in ids if categorias[i].papel}
    for rexistro in list(persoa.papeis_rexistro):
        if rexistro.papel in INICIAIS and rexistro.papel not in papeis:
            persoa.papeis_rexistro.remove(rexistro)
    for papel in papeis - persoa.papeis:
        persoa.papeis_rexistro.append(PersoaPapel(papel=papel))
    session.execute(delete(persoa_categoria).where(persoa_categoria.c.persoa_id == persoa.id))
    libres = [i for i in ids if categorias[i].papel is None]
    if libres:
        session.execute(insert(persoa_categoria), [
            {"persoa_id": persoa.id, "categoria_id": i} for i in libres])
    session.commit()

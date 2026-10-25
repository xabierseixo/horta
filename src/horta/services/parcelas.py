from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.parcela import Parcela
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import _PATRON_NIF, comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_parcela. Quedan fóra id,
# horta_id e created_at: mover unha parcela a outra horta saltaría o control
# de permisos, que se fai coa horta_id actual.
CAMPOS_EDITABLES_PARCELA = frozenset(
    {
        "nome",
        "descricion",
        "superficie",
        "posicion",
        "uso_aproveitamento",
        "secano_regadio",
        "sigpac_provincia",
        "sigpac_concello",
        "sigpac_poligono",
        "sigpac_parcela",
        "sigpac_subparcela",
        "sigpac_agregado",
        "sigpac_zona",
        "referencia_catastral",
        "rexime_tenencia",
        "nif_arrendador",
        "pequena_superficie",
        "data_alta",
        "data_baixa",
        "causa_baixa",
        "orixe_auga",
        "auga_consumo",
        "auga_consumo_na_parcela",
        "auga_consumo_distancia_m",
        "auga_consumo_utm",
        "auga_consumo_denominacion",
        "zona_especifica",
        "zona_especifica_ha",
        "notas",
        "estado",
        "lat",
        "lon",
        "geometria",
        "imaxe",
    }
)


def _validar_coordenadas(campos: dict[str, Any]) -> None:
    if "lat" in campos and campos["lat"] is not None:
        if not (-90 <= campos["lat"] <= 90):
            raise OperacionNonPermitidaError("A latitude debe estar entre -90 e 90")
    if "lon" in campos and campos["lon"] is not None:
        if not (-180 <= campos["lon"] <= 180):
            raise OperacionNonPermitidaError("A lonxitude debe estar entre -180 e 180")


def _validar_superficie(campos: dict[str, Any]) -> None:
    if "superficie" in campos and campos["superficie"] is not None:
        if campos["superficie"] < 0:
            raise OperacionNonPermitidaError("A superficie non pode ser negativa")


_CATALOGOS_PARCELA = {
    "rexime_tenencia": "rexime_tenencia",
    "causa_baixa": "causa_baixa",
    "orixe_auga": "orixe_auga",
}


def _validar_rea(session: Session, valores: dict[str, Any]) -> None:
    nif = valores.get("nif_arrendador")
    if nif and not _PATRON_NIF.match(nif):
        raise OperacionNonPermitidaError("O NIF do arrendador non é válido")
    alta, baixa = valores.get("data_alta"), valores.get("data_baixa")
    if alta is not None and baixa is not None and baixa < alta:
        raise OperacionNonPermitidaError("A data de baixa non pode ser anterior á de alta")
    if valores.get("zona_especifica") not in (None, "total", "parcial"):
        raise OperacionNonPermitidaError("A zona específica é «total» ou «parcial»")
    for campo in ("auga_consumo_distancia_m", "zona_especifica_ha"):
        if valores.get(campo) is not None and valores[campo] < 0:
            raise OperacionNonPermitidaError("As distancias e superficies non poden ser negativas")
    for campo, catalogo in _CATALOGOS_PARCELA.items():
        if valores.get(campo):
            validar_codigo(session, catalogo, str(valores[campo]), alta or date.today())


def crear_parcela(
    session: Session,
    actor: Usuario,
    horta_id: int,
    nome: str,
    **campos: Any,
) -> Parcela:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_coordenadas(campos)
    _validar_superficie(campos)
    _validar_rea(session, campos)
    estado = campos.pop("estado", "activa")
    parcela = Parcela(horta_id=horta_id, nome=nome, estado=estado, **campos)
    session.add(parcela)
    session.commit()
    return parcela


def actualizar_parcela(
    session: Session,
    actor: Usuario,
    parcela: Parcela,
    **cambios: Any,
) -> Parcela:
    non_editables = set(cambios) - CAMPOS_EDITABLES_PARCELA
    if non_editables:
        raise ValueError(f"Campos non editables nunha parcela: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar_coordenadas(cambios)
    _validar_superficie(cambios)
    _validar_rea(session, {c: cambios.get(c, getattr(parcela, c)) for c in
                           ("nif_arrendador", "data_alta", "data_baixa", "zona_especifica",
                            "auga_consumo_distancia_m", "zona_especifica_ha",
                            *_CATALOGOS_PARCELA)})
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
    session.commit()
    return parcela


def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    ids_cultivos = [c.id for c in session.query(Cultivo).filter_by(parcela_id=parcela.id)]
    if ids_cultivos and session.query(TratamentoCultivo).filter(
        TratamentoCultivo.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten tratamentos fitosanitarios rexistrados e debe conservarse "
            "(obriga legal)."
        )
    if ids_cultivos and session.query(Abonado).filter(
        Abonado.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten abonados rexistrados e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(Rega).filter(Rega.cultivo_id.in_(ids_cultivos)).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten regas rexistradas e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(Labor).filter(Labor.cultivo_id.in_(ids_cultivos)).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten labores rexistrados e debe conservarse (obriga legal)."
        )
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    session.query(Analise).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    if ids_cultivos:
        session.query(Analise).filter(Analise.cultivo_id.in_(ids_cultivos)).update(
            {"cultivo_id": None})
    cultivos = session.query(Cultivo).filter_by(parcela_id=parcela.id).all()
    for cultivo in cultivos:
        session.delete(cultivo)
    session.flush()
    session.delete(parcela)
    session.commit()


def listar_parcelas(session: Session, actor: Usuario, horta_id: int) -> list[Parcela]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Parcela).filter_by(horta_id=horta_id).order_by(Parcela.nome).all())

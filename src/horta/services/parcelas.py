from __future__ import annotations

import json
import math
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.analise import Analise
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.models.zona import ParcelaZona
from horta.services.catalogos import validar_codigo
from horta.services.conservar import comprobar_conservar
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import persoa_co_papel

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
        "arrendador_id",
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


def _validar_rea(session: Session, horta_id: int, valores: dict[str, Any]) -> None:
    # Quen arrenda ou cede a parcela (REA): unha persoa da explotación, co seu NIF
    persoa_co_papel(session, horta_id, valores.get("arrendador_id"), None)
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
    _validar_rea(session, horta_id, campos)
    estado = campos.pop("estado", "activa")
    parcela = Parcela(horta_id=horta_id, nome=nome, estado=estado, **campos)
    session.add(parcela)
    session.commit()
    return parcela


def _comprobar_cultivos(session: Session, parcela: Parcela, superficie: float | None) -> None:
    """A parcela non pode quedar menor ca un cultivo en curso nela."""
    if superficie is None:
        return
    maior = max((c.superficie_ha for c in session.query(Cultivo).filter_by(
        parcela_id=parcela.id, data_fin=None) if c.superficie_ha), default=None)
    if maior is not None and superficie < maior:
        texto = f"{maior:g}".replace(".", ",")
        raise OperacionNonPermitidaError(
            f"Un cultivo desta parcela ocupa {texto} ha: a parcela non pode ser menor")


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
    _comprobar_cultivos(session, parcela, cambios.get("superficie"))
    _validar_rea(session, parcela.horta_id, {c: cambios.get(c, getattr(parcela, c)) for c in
                           ("arrendador_id", "data_alta", "data_baixa", "zona_especifica",
                            "auga_consumo_distancia_m", "zona_especifica_ha",
                            *_CATALOGOS_PARCELA)})
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
    session.commit()
    return parcela


def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    comprobar_conservar(session, parcela)
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    session.query(OutroTraballo).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    session.query(Analise).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    ids_cultivos = [c.id for c in session.query(Cultivo).filter_by(parcela_id=parcela.id)]
    if ids_cultivos:
        session.query(Analise).filter(Analise.cultivo_id.in_(ids_cultivos)).update(
            {"cultivo_id": None})
        session.query(Tarefa).filter(Tarefa.cultivo_id.in_(ids_cultivos)).update(
            {"cultivo_id": None})
    cultivos = session.query(Cultivo).filter_by(parcela_id=parcela.id).all()
    for cultivo in cultivos:
        session.delete(cultivo)
    session.flush()
    session.query(ParcelaZona).filter_by(parcela_id=parcela.id).delete()
    session.delete(parcela)
    session.commit()


def ten_historial(session: Session, parcela: Parcela) -> bool:
    """Ten traballos que hai que conservar: non se borra, dáse de baixa (D4)."""
    try:
        comprobar_conservar(session, parcela)
    except OperacionNonPermitidaError:
        return True
    return False


def dar_de_baixa_parcela(session: Session, actor: Usuario, parcela: Parcela, data: date,
                         causa: str | None, hoxe: date | None = None) -> Parcela:
    """A parcela deixa de ser da explotación; o seu historial consérvase para os informes."""
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    if data > (hoxe or date.today()):
        raise OperacionNonPermitidaError("A data de baixa non pode ser futura")
    if not causa:
        raise OperacionNonPermitidaError("Indica a causa da baixa")
    _validar_rea(session, parcela.horta_id, {"data_alta": parcela.data_alta,
                                             "data_baixa": data, "causa_baixa": causa})
    seguen = [c.especie for c in session.query(Cultivo).filter_by(parcela_id=parcela.id)
              if c.data_fin is None or c.data_fin > data]
    if seguen:
        raise OperacionNonPermitidaError(
            f"Remata antes os cultivos que seguen na parcela: {', '.join(seguen)}")
    parcela.data_baixa, parcela.causa_baixa, parcela.estado = data, causa, "baixa"
    session.commit()
    return parcela


def listar_parcelas(session: Session, actor: Usuario, horta_id: int) -> list[Parcela]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Parcela).filter_by(horta_id=horta_id).order_by(Parcela.nome).all())


# --- Debuxo da parcela no mapa (paso 13)

def xeometria_debuxada(puntos: list[tuple[float, float]]) -> tuple[str, float, tuple[float, float]]:
    """De (lat, lon) dun polígono debuxado: GeoJSON, superficie en ha e centro.
    Superficie aproximada (proxección local), abonda para unha leira."""
    if len(puntos) < 3:
        raise OperacionNonPermitidaError("Un polígono precisa polo menos tres puntos")
    lat0 = sum(p[0] for p in puntos) / len(puntos)
    lon0 = sum(p[1] for p in puntos) / len(puntos)
    raio = 6371008.8
    xy = [(math.radians(lon - lon0) * raio * math.cos(math.radians(lat0)),
           math.radians(lat - lat0) * raio) for lat, lon in puntos]
    area_m2 = abs(sum(x1 * y2 - x2 * y1
                      for (x1, y1), (x2, y2) in zip(xy, xy[1:] + xy[:1], strict=True))) / 2
    aneis = [[lon, lat] for lat, lon in puntos] + [[puntos[0][1], puntos[0][0]]]
    geojson = json.dumps({"type": "Polygon", "coordinates": [aneis]})
    return geojson, round(area_m2 / 10000, 4), (round(lat0, 6), round(lon0, 6))


def _dentro(lat: float, lon: float, aneis: list[tuple[float, float]]) -> bool:
    dentro = False
    for (la1, lo1), (la2, lo2) in zip(aneis, aneis[1:] + aneis[:1]):
        if (lo1 > lon) != (lo2 > lon) and lat < la1 + (lon - lo1) * (la2 - la1) / (lo2 - lo1):
            dentro = not dentro
    return dentro


def parcela_no_punto(parcelas: list[Parcela], lat: float, lon: float) -> Parcela | None:
    """A parcela que ten ese punto dentro do contorno; ou, se non ten contorno, a que está
    situada a menos de 25 m."""
    for p in parcelas:
        forma = puntos_da_xeometria(p.geometria)
        if forma and _dentro(lat, lon, forma):
            return p
    for p in parcelas:
        if not puntos_da_xeometria(p.geometria) and p.lat is not None and p.lon is not None:
            metros = math.hypot((lat - p.lat) * 111_320,
                                (lon - p.lon) * 111_320 * math.cos(math.radians(lat)))
            if metros < 25:
                return p
    return None


def puntos_da_xeometria(geometria: str | None) -> list[tuple[float, float]]:
    """(lat, lon) do primeiro anel dun Polygon GeoJSON; [] se non o é."""
    try:
        datos = json.loads(geometria or "")
        return [(lat, lon) for lon, lat in datos["coordinates"][0][:-1]]
    except (ValueError, KeyError, IndexError, TypeError):
        return []

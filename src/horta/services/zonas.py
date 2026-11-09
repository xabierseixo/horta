"""Zonas dunha parcela (bancais, sectores, invernadoiros…) e as ferramentas para facelas:
debuxalas a man ou dividir a parcela en bancais iguais. Xeometría en metros nunha proxección
local (abonda para unha parcela), sen librerías de fóra."""

from __future__ import annotations

import math

from sqlalchemy.orm import Session

from horta.idiomas import N_
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.models.zona import ParcelaZona
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.parcelas import puntos_da_xeometria, xeometria_debuxada
from horta.services.xeometria import dividir, recortar, xuntar

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_RAIO = 6371008.8
TIPOS_ZONA: dict[str, str] = {
    # A superficie dun cultivo dentro do recinto (DGC, RD 1054/2022 art. 2.1.d)
    "cultivo": N_("Zona de cultivo"),
    "bancal": N_("Bancal"),
    "sector": N_("Sector"),
    "invernadoiro": N_("Invernadoiro ou túnel"),
    "camino": N_("Camiño ou paso"),
    "outra": N_("Outra"),
}
Punto = tuple[float, float]


def _a_metros(puntos: list[Punto], orixe: Punto) -> list[Punto]:
    lat0, lon0 = orixe
    return [(math.radians(lon - lon0) * _RAIO * math.cos(math.radians(lat0)),
             math.radians(lat - lat0) * _RAIO) for lat, lon in puntos]


def _a_graos(xy: list[Punto], orixe: Punto) -> list[Punto]:
    lat0, lon0 = orixe
    return [(lat0 + math.degrees(y / _RAIO),
             lon0 + math.degrees(x / (_RAIO * math.cos(math.radians(lat0))))) for x, y in xy]


def _recortar(poligono: list[Punto], normal: Punto, limite: float) -> list[Punto]:
    """Sutherland–Hodgman: a parte do polígono onde normal·p >= limite."""
    def dentro(p: Punto) -> bool:
        return normal[0] * p[0] + normal[1] * p[1] >= limite - 1e-9

    def corte(a: Punto, b: Punto) -> Punto:
        da = normal[0] * a[0] + normal[1] * a[1] - limite
        db = normal[0] * b[0] + normal[1] * b[1] - limite
        t = da / (da - db)
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))

    saida: list[Punto] = []
    for i, actual in enumerate(poligono):
        anterior = poligono[i - 1]
        if dentro(actual):
            if not dentro(anterior):
                saida.append(corte(anterior, actual))
            saida.append(actual)
        elif dentro(anterior):
            saida.append(corte(anterior, actual))
    return saida


def franxas(puntos: list[Punto], cantas: int, orientacion_graos: float,
            paso_m: float = 0) -> list[list[Punto]]:
    """Divide o polígono (lat, lon) en «cantas» franxas iguais. A orientación é a dirección
    dos bancais medida desde o norte (0 = norte–sur, 90 = leste–oeste); entre bancais queda
    un paso do ancho indicado."""
    if cantas < 1:
        raise OperacionNonPermitidaError("Polo menos un bancal")
    if paso_m < 0:
        raise OperacionNonPermitidaError("O paso non pode ser negativo")
    orixe = (sum(p[0] for p in puntos) / len(puntos), sum(p[1] for p in puntos) / len(puntos))
    xy = _a_metros(puntos, orixe)
    angulo = math.radians(orientacion_graos)
    # Eixo perpendicular aos bancais: por el córtanse as franxas
    normal = (math.cos(angulo), -math.sin(angulo))
    valores = [normal[0] * x + normal[1] * y for x, y in xy]
    inicio, fin = min(valores), max(valores)
    ancho = (fin - inicio - paso_m * (cantas - 1)) / cantas
    if ancho <= 0:
        raise OperacionNonPermitidaError("Con ese paso non caben tantos bancais")
    resultado = []
    for i in range(cantas):
        a = inicio + i * (ancho + paso_m)
        anaco = _recortar(xy, normal, a)
        anaco = _recortar(anaco, (-normal[0], -normal[1]), -(a + ancho))
        if len(anaco) >= 3:
            resultado.append(_a_graos(anaco, orixe))
    return resultado


def _parcela(session: Session, actor: Usuario, parcela: Parcela, roles: set[RolHorta]
             ) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, roles)


def _dentro_da_parcela(session: Session, parcela_id: int, puntos: list[Punto]
                       ) -> list[Punto]:
    parcela = session.get(Parcela, parcela_id)
    contorno = puntos_da_xeometria(parcela.geometria) if parcela else []
    return recortar(puntos, contorno) if len(contorno) >= 3 else puntos


def crear_zona(session: Session, actor: Usuario, parcela: Parcela, nome: str, tipo: str,
               puntos: list[Punto], so_dentro: bool = False) -> ParcelaZona:
    """Con so_dentro, o que saia fóra do contorno da parcela quítase."""
    _parcela(session, actor, parcela, _ROLES_ESCRITURA)
    if not nome.strip():
        raise OperacionNonPermitidaError("Ponlle un nome á zona")
    if tipo not in TIPOS_ZONA:
        raise OperacionNonPermitidaError("Escolle o tipo de zona")
    if so_dentro:
        puntos = _dentro_da_parcela(session, parcela.id, puntos)
    geojson, hectareas, _ = xeometria_debuxada(puntos)
    zona = ParcelaZona(parcela_id=parcela.id, nome=nome.strip(), tipo=tipo, geometria=geojson,
                       superficie=hectareas)
    session.add(zona)
    session.commit()
    return zona


def dividir_en_bancais(session: Session, actor: Usuario, parcela: Parcela, cantos: int,
                       orientacion_graos: float, paso_m: float = 0,
                       nome: str = "Bancal") -> list[ParcelaZona]:
    """Bancais iguais que cobren a parcela (precisa o seu contorno)."""
    _parcela(session, actor, parcela, _ROLES_ESCRITURA)
    contorno = puntos_da_xeometria(parcela.geometria)
    if len(contorno) < 3:
        raise OperacionNonPermitidaError("Primeiro debuxa ou trae o contorno da parcela")
    zonas = []
    for n, anaco in enumerate(franxas(contorno, cantos, orientacion_graos, paso_m), start=1):
        geojson, hectareas, _ = xeometria_debuxada(anaco)
        zona = ParcelaZona(parcela_id=parcela.id, nome=f"{nome.strip() or 'Bancal'} {n}",
                           tipo="bancal", geometria=geojson, superficie=hectareas)
        session.add(zona)
        zonas.append(zona)
    session.commit()
    return zonas


def _zona_escribible(session: Session, actor: Usuario, zona: ParcelaZona) -> None:
    parcela = session.get(Parcela, zona.parcela_id)
    assert parcela is not None
    _parcela(session, actor, parcela, _ROLES_ESCRITURA)


def _pon_lindes(zona: ParcelaZona, puntos: list[Punto]) -> None:
    zona.geometria, zona.superficie, _ = xeometria_debuxada(puntos)


def cambiar_zona(session: Session, actor: Usuario, zona: ParcelaZona, nome: str | None = None,
                 puntos: list[Punto] | None = None) -> ParcelaZona:
    """Outro nome ou outros lindes (sempre dentro da parcela)."""
    _zona_escribible(session, actor, zona)
    if nome is not None:
        if not nome.strip():
            raise OperacionNonPermitidaError("Ponlle un nome á zona")
        zona.nome = nome.strip()
    if puntos is not None:
        _pon_lindes(zona, _dentro_da_parcela(session, zona.parcela_id, puntos))
    session.commit()
    return zona


def dividir_zona(session: Session, actor: Usuario, zona: ParcelaZona, linea: list[Punto]
                 ) -> list[ParcelaZona]:
    """Parte a zona cunha liña: ela queda co primeiro anaco (e cos seus cultivos) e
    devólvense as zonas novas cos outros."""
    _zona_escribible(session, actor, zona)
    primeiro, *resto = dividir(puntos_da_xeometria(zona.geometria), linea)
    _pon_lindes(zona, primeiro)
    novas = []
    for n, anaco in enumerate(resto, start=2):
        nova = ParcelaZona(parcela_id=zona.parcela_id, nome=f"{zona.nome} ({n})", tipo=zona.tipo)
        _pon_lindes(nova, anaco)
        session.add(nova)
        novas.append(nova)
    session.commit()
    return novas


def xuntar_zonas(session: Session, actor: Usuario, zona: ParcelaZona, outra: ParcelaZona
                 ) -> ParcelaZona:
    """A zona colle a outra (que se toca con ela), e os cultivos da outra pasan a ela."""
    _zona_escribible(session, actor, zona)
    if outra.id == zona.id or outra.parcela_id != zona.parcela_id:
        raise OperacionNonPermitidaError("Escolle outra zona da mesma parcela")
    _pon_lindes(zona, xuntar(puntos_da_xeometria(zona.geometria),
                             puntos_da_xeometria(outra.geometria)))
    for cultivo in session.query(Cultivo).filter_by(zona_id=outra.id):
        cultivo.zona_id = zona.id
    session.delete(outra)
    session.commit()
    return zona


def listar_zonas(session: Session, actor: Usuario, parcela: Parcela) -> list[ParcelaZona]:
    _parcela(session, actor, parcela, _ROLES_LECTURA)
    return list(session.query(ParcelaZona).filter_by(parcela_id=parcela.id)
                .order_by(ParcelaZona.id))


def borrar_zona(session: Session, actor: Usuario, zona: ParcelaZona) -> None:
    parcela = session.get(Parcela, zona.parcela_id)
    assert parcela is not None
    _parcela(session, actor, parcela, _ROLES_ESCRITURA)
    if session.query(Cultivo).filter_by(zona_id=zona.id).first() is not None:
        raise OperacionNonPermitidaError("Hai cultivos nesta zona: cámbiaos antes de borrala")
    session.delete(zona)
    session.commit()


def aviso_superficie(session: Session, parcela: Parcela) -> str | None:
    """Se as zonas suman máis ca a parcela (debuxos que se solapan ou saen fóra)."""
    suma = sum(z.superficie or 0 for z in session.query(ParcelaZona).filter_by(
        parcela_id=parcela.id))
    if parcela.superficie and suma > parcela.superficie * 1.02:
        return (f"As zonas suman {suma:.4f} ha e a parcela ten {parcela.superficie:.4f} ha: "
                "algunha sae fóra ou se solapa")
    return None


def comprobar_zona(session: Session, parcela_id: int, zona_id: int | None) -> None:
    """A zona dun cultivo (opcional) ten que ser da súa parcela."""
    if zona_id is None:
        return
    zona = session.get(ParcelaZona, zona_id)
    if zona is None or zona.parcela_id != parcela_id:
        raise OperacionNonPermitidaError("Esa zona non é desta parcela")

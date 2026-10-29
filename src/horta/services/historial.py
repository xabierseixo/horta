"""Historial de cada recurso (paso 12 do deseño global): todo o que se apuntou cunha persoa,
un grupo de animais, unha máquina ou nunha parcela, sacado do que xa hai (nada se apunta a
maiores). E a rotación de cultivos de cada parcela."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from horta.db import Base
from horta.models.animal import Animal
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Rotación: non repetir o mesmo cultivo na mesma leira antes de 3 anos (orientativo: as boas
# prácticas falan de 3–4 anos e da mesma familia; aquí só se mira o mesmo cultivo)
ANOS_ROTACION = 3

_QUE_E = {"entrada_produto": "Compra", "lote_saida": "Venda", "analise": "Análise",
          "coidado_animal": "Coidado de animais", "movemento_animal": "Entrada ou saída de animais",
          "pastoreo": "Pastoreo", "pastoreo_animal": "Pastoreo",
          "parcela": "Parcela arrendada ou cedida",
          "tarefa": "Tarefa", "cultivo": "Sementeira", "labor": "Labor", "rega": "Rega",
          "abonado": "Abonado", "colleita": "Colleita", "outro_traballo": "Outro traballo",
          "tratamento_aplicador": "Tratamento (aplicou)",
          "tratamento_asesor": "Tratamento (asesorou)",
          "tratamento_instalacion": "Tratamento en instalación",
          "producion_animal": "Produción dos animais", "apunte_cartos": "Outro gasto ou ingreso",
          "clasificacion": "Clasificación dun lote", "mestura": "Mestura de lotes"}
_DATAS = ("data_inicio", "data", "data_mostraxe")


@dataclass(frozen=True)
class Feito:
    data: date | None
    que: str
    importe: float | None
    # Con prezo e sen cobrar nin pagar (paso 10, cartos)
    pendente: bool = False


def _data(fila: Any) -> date | None:
    return next((fila[c] for c in _DATAS if fila.get(c) is not None), None)


def _pai(session: Session, taboa: Table, fila: Any, excepto: str) -> Any | None:
    """Nas táboas fillas (p.ex. os aplicadores dun tratamento), a fila do traballo pai."""
    for fk in taboa.foreign_keys:
        pai = fk.column.table
        if pai.name != excepto and any(c in pai.c for c in _DATAS):
            return session.execute(select(pai).where(
                fk.column == fila[fk.parent.name])).mappings().first()
    return None


def por_referencia(session: Session, taboa_obxectivo: str, ref_id: int,
                   excluir: tuple[str, ...] = ()) -> list[Feito]:
    """Todo o que apunta a ese rexistro (persoa, animal, máquina…), do máis recente ao máis
    antigo, sen o dado de baixa. Quen chama comproba os permisos."""
    feitos: list[Feito] = []
    for taboa in Base.metadata.sorted_tables:
        if taboa.name in excluir:
            continue
        for fk in taboa.foreign_keys:
            if fk.column.table.name != taboa_obxectivo:
                continue
            for fila in session.execute(select(taboa).where(fk.parent == ref_id)).mappings():
                data = _data(fila)
                fonte = fila
                if data is None and not any(c in taboa.c for c in _DATAS):
                    fonte = _pai(session, taboa, fila, taboa_obxectivo) or fila
                    data = _data(fonte)
                if fila.get("baixa") or fonte.get("baixa"):
                    continue
                importe = fila.get("importe")
                pendente = ("data_pago" in fila and importe is not None
                            and fila["data_pago"] is None)
                que = _QUE_E.get(taboa.name, taboa.name.replace("_", " ").capitalize())
                feitos.append(Feito(data, que, importe, pendente))
    return sorted(feitos, key=lambda f: f.data or date.min, reverse=True)


def historial_animal(session: Session, actor: Usuario, animal: Animal) -> list[Feito]:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_LECTURA)
    return por_referencia(session, "animal", animal.id)


def historial_maquina(session: Session, actor: Usuario, maquina: Maquina) -> list[Feito]:
    comprobar_rol_horta(session, maquina.horta_id, actor, _ROLES_LECTURA)
    return por_referencia(session, "maquina", maquina.id)


def historial_parcela(session: Session, actor: Usuario, parcela: Parcela) -> list[Any]:
    """Os traballos feitos na parcela (os do Diario, que chegan a ela polos seus cultivos)."""
    from horta.services.diario import listar_traballos

    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_LECTURA)
    return [t for t in listar_traballos(session, actor, parcela.horta_id)
            if t.feito and parcela.id in t.parcelas]


@dataclass(frozen=True)
class CultivoNaLeira:
    cultivo: Cultivo
    # Aviso se o mesmo cultivo xa estivo na leira hai menos de ANOS_ROTACION
    aviso: str | None


def _mesmo(a: Cultivo, b: Cultivo) -> bool:
    if a.cultivo_siex_codigo and b.cultivo_siex_codigo:
        return a.cultivo_siex_codigo == b.cultivo_siex_codigo
    return a.especie.strip().lower() == b.especie.strip().lower()


def aviso_rotacion(anteriores: list[Cultivo], cultivo: Cultivo) -> str | None:
    """O mesmo cultivo na mesma leira hai menos de 3 anos. Nunca bloquea."""
    if cultivo.data_inicio is None:
        return None
    for antes in anteriores:
        if (antes.id != cultivo.id and antes.data_inicio is not None and _mesmo(antes, cultivo)
                and 0 <= (cultivo.data_inicio - antes.data_inicio).days
                < ANOS_ROTACION * 365):
            return (f"{cultivo.especie} xa estivo nesta leira en {antes.data_inicio.year}: "
                    f"convén rotar polo menos {ANOS_ROTACION} anos")
    return None


def rotacion(session: Session, actor: Usuario, parcela: Parcela) -> list[CultivoNaLeira]:
    """Os cultivos da parcela do máis recente ao máis antigo, co aviso de rotación."""
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_LECTURA)
    cultivos = sorted(session.query(Cultivo).filter_by(parcela_id=parcela.id),
                      key=lambda c: c.data_inicio or date.min, reverse=True)
    return [CultivoNaLeira(c, aviso_rotacion(cultivos, c)) for c in cultivos]

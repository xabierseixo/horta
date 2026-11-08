"""Servizo de recomendacións do asesor fitosanitario (mellora N7)."""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from datetime import date, time
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.recomendacion import Recomendacion
from horta.models.tratamento_fito import TratamentoFito
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_consulta import comprobar_tratamento
from horta.services.hortas import comprobar_rol_horta
from horta.services.tratamentos_fito import (
    DatosAsesor,
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaMedida,
    LinhaProduto,
    Problema,
    crear_tratamento_fito,
)

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_MAPA_UNIDADES_TOTAL = {"17": "5", "18": "4"}
_OMITIDO = object()


def _a_dict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, dict):
        return dict(obj)
    return obj


def _cultivos_de_dict(
    cultivos: Sequence[LinhaCultivo | dict[str, Any]]
) -> list[LinhaCultivo]:
    res: list[LinhaCultivo] = []
    for c in cultivos:
        if isinstance(c, LinhaCultivo):
            res.append(c)
        else:
            res.append(
                LinhaCultivo(
                    cultivo_id=c["cultivo_id"],
                    superficie_ha=c.get("superficie_ha"),
                    estado_fenoloxico=c.get("estado_fenoloxico"),
                )
            )
    return res


def _problemas_de_dict(
    problemas: Sequence[Problema | dict[str, Any]]
) -> list[Problema]:
    res: list[Problema] = []
    for p in problemas:
        if isinstance(p, Problema):
            res.append(p)
        else:
            res.append(Problema(tipo=p["tipo"], codigo=p["codigo"]))
    return res


def _produtos_de_dict(
    produtos: Sequence[LinhaProduto | dict[str, Any]]
) -> list[LinhaProduto]:
    res: list[LinhaProduto] = []
    for p in produtos:
        if isinstance(p, LinhaProduto):
            res.append(p)
        else:
            res.append(
                LinhaProduto(
                    tipo_produto=p["tipo_produto"],
                    unidade=p["unidade"],
                    num_rexistro=p.get("num_rexistro"),
                    nome_comercial=p.get("nome_comercial"),
                    materia_activa=p.get("materia_activa"),
                    dose=p.get("dose"),
                    cantidade=p.get("cantidade"),
                    entrada_id=p.get("entrada_id"),
                )
            )
    return res


def _medidas_de_dict(
    medidas: Sequence[LinhaMedida | dict[str, Any]]
) -> list[LinhaMedida]:
    res: list[LinhaMedida] = []
    for m in medidas:
        if isinstance(m, LinhaMedida):
            res.append(m)
        else:
            res.append(
                LinhaMedida(
                    tipo_medida=m["tipo_medida"],
                    cantidade=m.get("cantidade"),
                    unidade=m.get("unidade"),
                    num_rexistro_mdf=m.get("num_rexistro_mdf"),
                    boas_practicas=m.get("boas_practicas"),
                )
            )
    return res


def recomendacion_a_datos(rec: Recomendacion) -> DatosTratamento:
    return DatosTratamento(
        data_inicio=rec.data,
        data_fin=rec.data,
        cultivos=_cultivos_de_dict(rec.cultivos),
        problemas=_problemas_de_dict(rec.problemas),
        xustificacions=list(rec.xustificacions or []),
        produtos=_produtos_de_dict(rec.produtos or []),
        medidas=_medidas_de_dict(rec.medidas or []),
        aplicadores=[],
        asesor=DatosAsesor(
            persoa_id=rec.asesor_persoa_id,
            data=rec.data,
            validacion=True,
        ),
        notas=rec.observacions,
    )


_a_datos = recomendacion_a_datos


def _validar_datos(
    session: Session,
    horta_id: int,
    asesor_persoa_id: int,
    data: date,
    cultivos: list[Any],
    problemas: list[Any],
    produtos: list[Any],
    medidas: list[Any],
    valida_ata: date | None,
) -> None:
    asesor = session.get(Persoa, asesor_persoa_id)
    if asesor is None or asesor.horta_id != horta_id or not asesor.ten_papel("asesor"):
        raise OperacionNonPermitidaError("Escolle un asesor da explotación")

    if not cultivos:
        raise OperacionNonPermitidaError("Indica polo menos un cultivo tratado")
    for c in cultivos:
        cid = c.cultivo_id if hasattr(c, "cultivo_id") else c["cultivo_id"]
        cultivo = session.get(Cultivo, cid)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None or parcela.horta_id != horta_id:
            raise OperacionNonPermitidaError(
                "O cultivo indicado non pertence a esta explotación"
            )
        if cultivo.data_fin is not None:
            raise OperacionNonPermitidaError(
                f"O cultivo {cultivo.especie} xa está pechado"
            )

    if not problemas:
        raise OperacionNonPermitidaError(
            "Indica polo menos un problema (praga, enfermidade, mala herba ou regulador)"
        )

    if not produtos and not medidas:
        raise OperacionNonPermitidaError(
            "Indica polo menos un produto ou unha medida non química"
        )

    if valida_ata is not None and valida_ata < data:
        raise OperacionNonPermitidaError(
            "A data de validez non pode ser anterior á data da recomendación"
        )


def crear_recomendacion(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    asesor_persoa_id: int,
    data: date,
    cultivos: list[LinhaCultivo],
    problemas: list[Problema],
    xustificacions: list[str],
    produtos: list[LinhaProduto],
    medidas: list[LinhaMedida] | None = None,
    valida_ata: date | None = None,
    observacions: str | None = None,
    visita_id: int | None = None,
) -> Recomendacion:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    medidas_lista = medidas or []
    _validar_datos(
        session,
        horta_id,
        asesor_persoa_id,
        data,
        cultivos,
        problemas,
        produtos,
        medidas_lista,
        valida_ata,
    )
    if visita_id is not None:
        from horta.models.visita import VisitaCampo

        visita = session.get(VisitaCampo, visita_id)
        if visita is None or visita.horta_id != horta_id:
            raise OperacionNonPermitidaError(
                "A visita indicada non pertence a esta explotación"
            )
        if visita.baixa:
            raise OperacionNonPermitidaError("A visita indicada está dada de baixa")
    rec = Recomendacion(
        horta_id=horta_id,
        asesor_persoa_id=asesor_persoa_id,
        data=data,
        valida_ata=valida_ata,
        cultivos=[_a_dict(c) for c in cultivos],
        problemas=[_a_dict(p) for p in problemas],
        xustificacions=list(xustificacions),
        produtos=[_a_dict(p) for p in produtos],
        medidas=[_a_dict(m) for m in medidas_lista],
        observacions=observacions,
        estado="pendente",
        visita_id=visita_id,
        baixa=False,
        creado_por=actor.id if actor else None,
    )
    session.add(rec)
    session.commit()
    return rec


def actualizar_recomendacion(
    session: Session,
    actor: Usuario,
    rec: Recomendacion,
    *,
    asesor_persoa_id: int | None = None,
    data: date | None = None,
    cultivos: list[LinhaCultivo] | None = None,
    problemas: list[Problema] | None = None,
    xustificacions: list[str] | None = None,
    produtos: list[LinhaProduto] | None = None,
    medidas: list[LinhaMedida] | None = None,
    valida_ata: Any = _OMITIDO,
    observacions: Any = _OMITIDO,
    visita_id: Any = _OMITIDO,
) -> Recomendacion:
    if rec.baixa:
        raise OperacionNonPermitidaError(
            "Unha recomendación dada de baixa non se pode modificar"
        )
    if rec.estado != "pendente":
        raise OperacionNonPermitidaError(
            "Só se poden modificar recomendacións pendentes"
        )
    comprobar_rol_horta(session, rec.horta_id, actor, _ROLES_ESCRITURA)

    novo_asesor = (
        asesor_persoa_id if asesor_persoa_id is not None else rec.asesor_persoa_id
    )
    nova_data = data if data is not None else rec.data
    novos_cultivos = (
        cultivos if cultivos is not None else _cultivos_de_dict(rec.cultivos)
    )
    novos_problemas = (
        problemas if problemas is not None else _problemas_de_dict(rec.problemas)
    )
    novas_xustificacions = (
        xustificacions if xustificacions is not None else list(rec.xustificacions or [])
    )
    novos_produtos = (
        produtos if produtos is not None else _produtos_de_dict(rec.produtos or [])
    )
    novas_medidas = (
        medidas if medidas is not None else _medidas_de_dict(rec.medidas or [])
    )
    nova_valida_ata = rec.valida_ata if valida_ata is _OMITIDO else valida_ata
    novas_observacions = (
        rec.observacions if observacions is _OMITIDO else observacions
    )

    _validar_datos(
        session,
        rec.horta_id,
        novo_asesor,
        nova_data,
        novos_cultivos,
        novos_problemas,
        novos_produtos,
        novas_medidas,
        nova_valida_ata,
    )

    if visita_id is not _OMITIDO:
        if visita_id is not None:
            from horta.models.visita import VisitaCampo

            v = session.get(VisitaCampo, visita_id)
            if v is None or v.horta_id != rec.horta_id:
                raise OperacionNonPermitidaError(
                    "A visita indicada non pertence a esta explotación"
                )
            if v.baixa:
                raise OperacionNonPermitidaError("A visita indicada está dada de baixa")
        rec.visita_id = visita_id

    rec.asesor_persoa_id = novo_asesor
    rec.data = nova_data
    rec.cultivos = [_a_dict(c) for c in novos_cultivos]
    rec.problemas = [_a_dict(p) for p in novos_problemas]
    rec.xustificacions = list(novas_xustificacions)
    rec.produtos = [_a_dict(p) for p in novos_produtos]
    rec.medidas = [_a_dict(m) for m in novas_medidas]
    rec.valida_ata = nova_valida_ata
    rec.observacions = novas_observacions

    session.commit()
    return rec


def listar_recomendacions(
    session: Session, actor: Usuario, horta_id: int, estado: str | None = None
) -> list[Recomendacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Recomendacion).filter_by(
        horta_id=horta_id, baixa=False
    )
    if estado is not None:
        consulta = consulta.filter(Recomendacion.estado == estado)
    return list(
        consulta.order_by(Recomendacion.data.desc(), Recomendacion.id.desc()).all()
    )


def recomendacions_pendentes(
    session: Session, actor: Usuario, horta_id: int, hoxe: date | None = None
) -> list[Recomendacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    data_actual = hoxe or date.today()
    consulta = session.query(Recomendacion).filter(
        Recomendacion.horta_id == horta_id,
        Recomendacion.baixa.is_(False),
        Recomendacion.estado == "pendente",
        or_(
            Recomendacion.valida_ata.is_(None),
            Recomendacion.valida_ata >= data_actual,
        ),
    )
    return list(
        consulta.order_by(Recomendacion.data.desc(), Recomendacion.id.desc()).all()
    )


def avisos_recomendacion(session: Session, rec: Recomendacion) -> list[str]:
    horta = session.get(Horta, rec.horta_id)
    if horta is None:
        return []
    datos = _a_datos(rec)
    avisos = comprobar_tratamento(session, horta, datos)
    return [a.texto for a in avisos]


def aplicar_recomendacion(
    session: Session,
    actor: Usuario,
    rec: Recomendacion,
    *,
    data_inicio: date,
    data_fin: date,
    aplicadores: list[LinhaAplicador],
    hora: time | None = None,
    cantidades: dict[int, float] | None = None,
    eficacia: str | None = None,
    notas: str | None = None,
) -> TratamentoFito:
    if rec.baixa:
        raise OperacionNonPermitidaError(
            "Unha recomendación dada de baixa non se pode aplicar"
        )
    if rec.estado != "pendente":
        raise OperacionNonPermitidaError(
            "Só se poden aplicar recomendacións pendentes"
        )
    comprobar_rol_horta(session, rec.horta_id, actor, _ROLES_ESCRITURA)

    produtos_tratamento: list[LinhaProduto] = []
    for i, p_dict in enumerate(rec.produtos or []):
        unidade = p_dict["unidade"]
        dose = p_dict.get("dose")
        cantidade = p_dict.get("cantidade")
        if cantidades is not None and i in cantidades:
            cantidade = cantidades[i]
            dose = None
            unidade = _MAPA_UNIDADES_TOTAL.get(unidade, unidade)
        produtos_tratamento.append(
            LinhaProduto(
                tipo_produto=p_dict["tipo_produto"],
                unidade=unidade,
                num_rexistro=p_dict.get("num_rexistro"),
                nome_comercial=p_dict.get("nome_comercial"),
                materia_activa=p_dict.get("materia_activa"),
                dose=dose,
                cantidade=cantidade,
                entrada_id=p_dict.get("entrada_id"),
            )
        )

    medidas_tratamento = _medidas_de_dict(rec.medidas or [])

    datos = DatosTratamento(
        data_inicio=data_inicio,
        data_fin=data_fin,
        cultivos=_cultivos_de_dict(rec.cultivos),
        problemas=_problemas_de_dict(rec.problemas),
        xustificacions=list(rec.xustificacions or []),
        produtos=produtos_tratamento,
        medidas=medidas_tratamento,
        aplicadores=aplicadores,
        hora=hora,
        asesor=DatosAsesor(
            persoa_id=rec.asesor_persoa_id,
            data=rec.data,
            validacion=True,
        ),
        eficacia=eficacia,
        notas=notas if notas is not None else rec.observacions,
    )

    tratamento = crear_tratamento_fito(session, actor, rec.horta_id, datos)
    rec.estado = "aplicada"
    rec.tratamento_id = tratamento.id
    session.commit()
    return tratamento


def ligar_tratamento(
    session: Session,
    actor: Usuario,
    rec: Recomendacion,
    tratamento: TratamentoFito,
) -> None:
    comprobar_rol_horta(session, rec.horta_id, actor, _ROLES_ESCRITURA)
    if rec.baixa:
        raise OperacionNonPermitidaError(
            "Unha recomendación dada de baixa non se pode aplicar"
        )
    if rec.estado != "pendente":
        raise OperacionNonPermitidaError(
            "Só se poden aplicar recomendacións pendentes"
        )
    if tratamento.horta_id != rec.horta_id:
        raise OperacionNonPermitidaError(
            "O tratamento non pertence á mesma explotación"
        )
    rec.estado = "aplicada"
    rec.tratamento_id = tratamento.id
    session.commit()


def descartar_recomendacion(
    session: Session, actor: Usuario, rec: Recomendacion, motivo: str
) -> Recomendacion:
    if rec.baixa:
        raise OperacionNonPermitidaError(
            "Unha recomendación dada de baixa non se pode descartar"
        )
    if rec.estado != "pendente":
        raise OperacionNonPermitidaError(
            "Só se poden descartar recomendacións pendentes"
        )
    comprobar_rol_horta(session, rec.horta_id, actor, _ROLES_ESCRITURA)
    if not motivo or not motivo.strip():
        raise OperacionNonPermitidaError("O motivo do descarte é obrigatorio")
    rec.estado = "descartada"
    rec.motivo_descarte = motivo.strip()
    session.commit()
    return rec


def dar_de_baixa_recomendacion(
    session: Session, actor: Usuario, rec: Recomendacion
) -> None:
    comprobar_rol_horta(session, rec.horta_id, actor, _ROLES_ESCRITURA)
    rec.baixa = True
    session.commit()


def obter_recomendacion(
    session: Session, actor: Usuario, recomendacion_id: int
) -> Recomendacion | None:
    rec = session.get(Recomendacion, recomendacion_id)
    if rec is None or rec.baixa:
        return None
    comprobar_rol_horta(session, rec.horta_id, actor, _ROLES_LECTURA)
    return rec


__all__ = [
    "actualizar_recomendacion",
    "aplicar_recomendacion",
    "avisos_recomendacion",
    "crear_recomendacion",
    "dar_de_baixa_recomendacion",
    "descartar_recomendacion",
    "ligar_tratamento",
    "listar_recomendacions",
    "obter_recomendacion",
    "recomendacion_a_datos",
    "recomendacions_pendentes",
]

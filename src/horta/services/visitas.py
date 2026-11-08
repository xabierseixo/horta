"""Servizo de visitas de campo do persoal asesor técnico (mellora N7)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.observacion import ObservacionPraga
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.recomendacion import Recomendacion
from horta.models.usuario import Usuario
from horta.models.visita import VisitaCampo
from horta.services.catalogos import describir
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.observacions import METODOS, NIVEIS, limiar_para, supera_limiar
from horta.services.persoas import nome_completo, titular_da_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_OMITIDO = object()


def _validar_datos_visita(
    session: Session,
    horta_id: int,
    asesor_persoa_id: int,
    data: date,
    cultivos: Sequence[int],
    proxima_visita: date | None = None,
) -> None:
    asesor = session.get(Persoa, asesor_persoa_id)
    if asesor is None or asesor.horta_id != horta_id or not asesor.ten_papel("asesor"):
        raise OperacionNonPermitidaError("Escolle unha persoa asesora da explotación")

    for cid in cultivos:
        cultivo = session.get(Cultivo, cid)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None or parcela.horta_id != horta_id:
            raise OperacionNonPermitidaError(
                "O cultivo indicado non pertence a esta explotación"
            )

    if proxima_visita is not None and proxima_visita < data:
        raise OperacionNonPermitidaError(
            "A data da próxima visita non pode ser anterior á data da visita"
        )


def crear_visita(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    asesor_persoa_id: int,
    data: date,
    cultivos: list[int] | None = None,
    hora_inicio: time | None = None,
    estado_xeral: str | None = None,
    conclusions: str | None = None,
    proxima_visita: date | None = None,
) -> VisitaCampo:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    lista_cultivos: list[int] = list(cultivos) if cultivos else []
    _validar_datos_visita(
        session,
        horta_id,
        asesor_persoa_id,
        data,
        lista_cultivos,
        proxima_visita,
    )
    visita = VisitaCampo(
        horta_id=horta_id,
        asesor_persoa_id=asesor_persoa_id,
        data=data,
        hora_inicio=hora_inicio,
        cultivos=lista_cultivos,
        estado_xeral=estado_xeral.strip() if estado_xeral and estado_xeral.strip() else None,
        conclusions=conclusions.strip() if conclusions and conclusions.strip() else None,
        proxima_visita=proxima_visita,
        baixa=False,
        creado_por=actor.id if actor else None,
    )
    session.add(visita)
    session.commit()
    return visita


def actualizar_visita(
    session: Session,
    actor: Usuario,
    visita: VisitaCampo | int,
    *,
    asesor_persoa_id: int | None = None,
    data: date | None = None,
    hora_inicio: Any = _OMITIDO,
    cultivos: list[int] | None = None,
    estado_xeral: Any = _OMITIDO,
    conclusions: Any = _OMITIDO,
    proxima_visita: Any = _OMITIDO,
) -> VisitaCampo:
    if isinstance(visita, int):
        v = session.get(VisitaCampo, visita)
        if v is None:
            raise OperacionNonPermitidaError("Non existe a visita")
        visita = v

    if visita.baixa:
        raise OperacionNonPermitidaError(
            "Unha visita dada de baixa non se pode modificar"
        )
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_ESCRITURA)

    novo_asesor = (
        asesor_persoa_id if asesor_persoa_id is not None else visita.asesor_persoa_id
    )
    nova_data = data if data is not None else visita.data
    novos_cultivos = (
        list(cultivos) if cultivos is not None else list(visita.cultivos or [])
    )
    nova_hora = visita.hora_inicio if hora_inicio is _OMITIDO else hora_inicio
    novo_estado_xeral = (
        visita.estado_xeral if estado_xeral is _OMITIDO else estado_xeral
    )
    novas_conclusions = (
        visita.conclusions if conclusions is _OMITIDO else conclusions
    )
    nova_proxima_visita = (
        visita.proxima_visita if proxima_visita is _OMITIDO else proxima_visita
    )

    _validar_datos_visita(
        session,
        visita.horta_id,
        novo_asesor,
        nova_data,
        novos_cultivos,
        nova_proxima_visita,
    )

    visita.asesor_persoa_id = novo_asesor
    visita.data = nova_data
    visita.cultivos = novos_cultivos
    visita.hora_inicio = nova_hora
    visita.estado_xeral = (
        novo_estado_xeral.strip()
        if novo_estado_xeral and isinstance(novo_estado_xeral, str) and novo_estado_xeral.strip()
        else (novo_estado_xeral if novo_estado_xeral is None else str(novo_estado_xeral))
    )
    visita.conclusions = (
        novas_conclusions.strip()
        if novas_conclusions and isinstance(novas_conclusions, str) and novas_conclusions.strip()
        else (novas_conclusions if novas_conclusions is None else str(novas_conclusions))
    )
    visita.proxima_visita = nova_proxima_visita

    session.commit()
    return visita


def dar_de_baixa_visita(
    session: Session,
    actor: Usuario,
    visita: VisitaCampo | int,
) -> None:
    if isinstance(visita, int):
        v = session.get(VisitaCampo, visita)
        if v is None:
            raise OperacionNonPermitidaError("Non existe a visita")
        visita = v
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_ESCRITURA)
    visita.baixa = True
    session.commit()


def listar_visitas(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    desde: date | None = None,
    ata: date | None = None,
) -> list[VisitaCampo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(VisitaCampo).filter_by(horta_id=horta_id, baixa=False)
    if desde is not None:
        consulta = consulta.filter(VisitaCampo.data >= desde)
    if ata is not None:
        consulta = consulta.filter(VisitaCampo.data <= ata)
    return list(
        consulta.order_by(VisitaCampo.data.desc(), VisitaCampo.id.desc()).all()
    )


def proximas_visitas(
    session: Session,
    actor: Usuario,
    horta_id: int,
    hoxe: date | None = None,
    dias: int = 14,
) -> list[VisitaCampo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    data_actual = hoxe or date.today()
    limite = data_actual + timedelta(days=dias)
    return list(
        session.query(VisitaCampo)
        .filter(
            VisitaCampo.horta_id == horta_id,
            VisitaCampo.baixa.is_(False),
            VisitaCampo.proxima_visita.is_not(None),
            VisitaCampo.proxima_visita >= data_actual,
            VisitaCampo.proxima_visita <= limite,
        )
        .order_by(VisitaCampo.proxima_visita.asc(), VisitaCampo.id.asc())
        .all()
    )


def obter_visita(
    session: Session,
    actor: Usuario,
    visita_id: int,
) -> VisitaCampo | None:
    visita = session.get(VisitaCampo, visita_id)
    if visita is None or visita.baixa:
        return None
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_LECTURA)
    return visita


@dataclass
class ContidoVisita:
    """Contido completo dunha visita de campo con observacións, recomendacións e cultivos."""

    visita: VisitaCampo
    observacions: list[ObservacionPraga]
    recomendacions: list[Recomendacion]
    nomes_cultivos: list[str]
    cultivos: list[Cultivo] = field(default_factory=list)


def ligar_observacion(
    session: Session,
    actor: Usuario,
    visita: VisitaCampo | int,
    observacion: ObservacionPraga | int,
) -> None:
    """Liga unha observación de pragas existente a unha visita de campo."""
    if isinstance(visita, int):
        v = session.get(VisitaCampo, visita)
        if v is None:
            raise OperacionNonPermitidaError("Non existe a visita")
        visita = v

    if visita.baixa:
        raise OperacionNonPermitidaError("Unha visita dada de baixa non se pode modificar")
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_ESCRITURA)

    if isinstance(observacion, int):
        obs = session.get(ObservacionPraga, observacion)
        if obs is None:
            raise OperacionNonPermitidaError("Non existe a observación")
        observacion = obs

    if observacion.baixa:
        raise OperacionNonPermitidaError("Unha observación dada de baixa non se pode ligar")

    if observacion.horta_id != visita.horta_id:
        raise OperacionNonPermitidaError("A observación non pertence á mesma explotación")

    observacion.visita_id = visita.id
    session.commit()


def ligar_recomendacion(
    session: Session,
    actor: Usuario,
    visita: VisitaCampo | int,
    rec: Recomendacion | int,
) -> None:
    """Liga unha recomendación do persoal asesor a unha visita de campo."""
    if isinstance(visita, int):
        v = session.get(VisitaCampo, visita)
        if v is None:
            raise OperacionNonPermitidaError("Non existe a visita")
        visita = v

    if visita.baixa:
        raise OperacionNonPermitidaError("Unha visita dada de baixa non se pode modificar")
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_ESCRITURA)

    if isinstance(rec, int):
        r = session.get(Recomendacion, rec)
        if r is None:
            raise OperacionNonPermitidaError("Non existe a recomendación")
        rec = r

    if rec.baixa:
        raise OperacionNonPermitidaError("Unha recomendación dada de baixa non se pode ligar")

    if rec.horta_id != visita.horta_id:
        raise OperacionNonPermitidaError("A recomendación non pertence á mesma explotación")

    rec.visita_id = visita.id
    session.commit()


def contido_visita(
    session: Session,
    actor: Usuario,
    visita_id: int,
) -> ContidoVisita:
    """Obtén a visita coas súas observacións e recomendacións vixentes e os cultivos."""
    visita = session.get(VisitaCampo, visita_id)
    if visita is None or visita.baixa:
        raise OperacionNonPermitidaError("Non existe a visita")
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_LECTURA)

    observacions = list(
        session.query(ObservacionPraga)
        .filter(
            ObservacionPraga.visita_id == visita.id,
            ObservacionPraga.baixa.is_(False),
        )
        .order_by(ObservacionPraga.data.asc(), ObservacionPraga.id.asc())
        .all()
    )

    recomendacions = list(
        session.query(Recomendacion)
        .filter(
            Recomendacion.visita_id == visita.id,
            Recomendacion.baixa.is_(False),
        )
        .order_by(Recomendacion.data.asc(), Recomendacion.id.asc())
        .all()
    )

    cultivos_lista: list[Cultivo] = []
    nomes_cultivos: list[str] = []
    for cid in visita.cultivos or []:
        c = session.get(Cultivo, cid)
        if c is not None:
            cultivos_lista.append(c)
            nome = f"{c.especie} ({c.variedade})" if c.variedade else c.especie
            nomes_cultivos.append(nome)

    return ContidoVisita(
        visita=visita,
        observacions=observacions,
        recomendacions=recomendacions,
        nomes_cultivos=nomes_cultivos,
        cultivos=cultivos_lista,
    )


def informe_visita(
    session: Session,
    actor: Usuario,
    visita_id: int,
) -> bytes:
    """Xera un informe en Excel (openpyxl) da visita de campo convertible a PDF."""
    contido = contido_visita(session, actor, visita_id)
    visita = contido.visita
    horta = session.get(Horta, visita.horta_id)
    if horta is None:
        raise OperacionNonPermitidaError("Non existe a explotación")

    asesor = session.get(Persoa, visita.asesor_persoa_id)
    asesor_nome = nome_completo(asesor)
    asesor_ropo = (asesor.ropo_numero if asesor else "") or ""

    titular = titular_da_horta(session, visita.horta_id)
    titular_nome = nome_completo(titular)
    rega_reaga = (
        horta.codigo_rega
        or horta.codigo_reaga
        or (titular.rega if titular else None)
        or (titular.reaga if titular else None)
        or ""
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Informe de visita"

    negra = Font(bold=True)
    titulo_font = Font(bold=True, size=13)
    seccion_font = Font(bold=True, size=11)

    ws.append(["Informe da visita de campo"])
    ws["A1"].font = titulo_font
    ws.append([])

    ws.append(["1. Datos xerais da explotación e da visita"])
    ws.cell(row=ws.max_row, column=1).font = seccion_font

    ws.append(["Explotación", horta.nome, "Data", f"{visita.data:%d/%m/%Y}"])
    hora_str = f"{visita.hora_inicio:%H:%M}" if visita.hora_inicio else ""
    ws.append(["Titular", titular_nome, "Hora", hora_str])
    ws.append(["REGA / REAGA", rega_reaga, "Persoa asesora", asesor_nome])
    ws.append(["", "", "Nº ROPO", asesor_ropo])
    ws.append([])

    ws.append(["2. Cultivos visitados"])
    ws.cell(row=ws.max_row, column=1).font = seccion_font
    ws.append(["Parcela", "Cultivo", "Variedade", "Superficie (ha)"])
    for cell in ws[ws.max_row]:
        cell.font = negra

    if contido.cultivos:
        for c in contido.cultivos:
            p = session.get(Parcela, c.parcela_id) if c.parcela_id else None
            sup_str = f"{c.superficie_ha:g}" if c.superficie_ha is not None else ""
            ws.append([p.nome if p else "", c.especie, c.variedade or "", sup_str])
    else:
        ws.append(["Sen cultivos especificados", "", "", ""])
    ws.append([])

    ws.append(["3. Estado xeral"])
    ws.cell(row=ws.max_row, column=1).font = seccion_font
    ws.append([visita.estado_xeral or "Sen observacións xerais"])
    ws.append([])

    ws.append(["4. Observacións de pragas, enfermidades e malas herbas"])
    ws.cell(row=ws.max_row, column=1).font = seccion_font
    ws.append(["Problema", "Método", "Conto / Nivel", "Limiar", "Supera", "Notas"])
    for cell in ws[ws.max_row]:
        cell.font = negra

    if contido.observacions:
        for obs in contido.observacions:
            prob_desc = describir(session, obs.problema_tipo, obs.problema_codigo)
            met_desc = METODOS.get(obs.metodo, obs.metodo)
            if obs.conto is not None:
                conto_str = f"{obs.conto:g} {obs.unidade_conto or ''}".strip()
            elif obs.nivel:
                conto_str = NIVEIS.get(obs.nivel, obs.nivel)
            else:
                conto_str = ""

            limiar = (
                limiar_para(
                    session,
                    visita.horta_id,
                    obs.cultivo_id,
                    obs.problema_tipo,
                    obs.problema_codigo,
                    obs.metodo,
                    obs.unidade_conto or "",
                )
                if obs.unidade_conto
                else None
            )

            if limiar is not None:
                limiar_str = f"{limiar.valor:g} {limiar.unidade_conto}"
                supera_str = "Si" if supera_limiar(obs, limiar) else "Non"
            elif obs.nivel == "alto":
                limiar_str = "-"
                supera_str = "Si"
            else:
                limiar_str = "-"
                supera_str = "Non"

            ws.append([
                prob_desc,
                met_desc,
                conto_str,
                limiar_str,
                supera_str,
                obs.notas or "",
            ])
    else:
        ws.append(["Sen observacións rexistradas", "", "", "", "", ""])
    ws.append([])

    ws.append(["5. Recomendacións fitosanitarias"])
    ws.cell(row=ws.max_row, column=1).font = seccion_font
    ws.append(["Cultivos", "Problema", "Produtos", "Dose", "Válida ata", "Estado"])
    for cell in ws[ws.max_row]:
        cell.font = negra

    if contido.recomendacions:
        for rec in contido.recomendacions:
            cult_nomes: list[str] = []
            for c_info in rec.cultivos or []:
                cid = (
                    c_info.get("cultivo_id")
                    if isinstance(c_info, dict)
                    else getattr(c_info, "cultivo_id", None)
                )
                if cid:
                    c_obj = session.get(Cultivo, cid)
                    if c_obj:
                        cult_nomes.append(c_obj.especie)
            cultivos_rec = ", ".join(cult_nomes) if cult_nomes else "-"

            prob_nomes: list[str] = []
            for p_info in rec.problemas or []:
                p_t = (
                    p_info.get("tipo")
                    if isinstance(p_info, dict)
                    else getattr(p_info, "tipo", "")
                )
                p_c = (
                    p_info.get("codigo")
                    if isinstance(p_info, dict)
                    else getattr(p_info, "codigo", "")
                )
                if p_t and p_c:
                    prob_nomes.append(describir(session, p_t, p_c))
            problemas_rec = ", ".join(prob_nomes) if prob_nomes else "-"

            prod_nomes: list[str] = []
            doses_rec: list[str] = []
            for pr in rec.produtos or []:
                nome_p = (
                    pr.get("nome_comercial")
                    or pr.get("materia_activa")
                    or (f"Reg. {pr.get('num_rexistro')}" if pr.get("num_rexistro") else "")
                    or str(pr.get("tipo_produto", ""))
                )
                if nome_p:
                    prod_nomes.append(nome_p)
                dose_val = pr.get("dose") or pr.get("cantidade")
                if dose_val is not None:
                    doses_rec.append(f"{dose_val} {pr.get('unidade', '')}".strip())

            produtos_rec = ", ".join(prod_nomes) if prod_nomes else "-"
            dose_str = ", ".join(doses_rec) if doses_rec else "-"
            valida_str = f"{rec.valida_ata:%d/%m/%Y}" if rec.valida_ata else "-"

            ws.append([
                cultivos_rec,
                problemas_rec,
                produtos_rec,
                dose_str,
                valida_str,
                rec.estado,
            ])
    else:
        ws.append(["Sen recomendacións rexistradas", "", "", "", "", ""])
    ws.append([])

    ws.append(["6. Conclusións e próxima visita"])
    ws.cell(row=ws.max_row, column=1).font = seccion_font
    ws.append(["Conclusións", visita.conclusions or "Sen conclusións"])
    proxima_str = f"{visita.proxima_visita:%d/%m/%Y}" if visita.proxima_visita else "-"
    ws.append(["Próxima visita", proxima_str])
    ws.append([])
    ws.append([])

    ws.append(["Sinatura da persoa asesora", "", "Sinatura da persoa titular", ""])
    ws.append([])
    ws.append([
        "________________________________________",
        "",
        "________________________________________",
        "",
    ])
    ws.append([f"Asdo.: {asesor_nome}", "", f"Asdo.: {titular_nome}", ""])

    for col in ("A", "B", "C", "D", "E", "F"):
        ws.column_dimensions[col].width = 22

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


__all__ = [
    "ContidoVisita",
    "actualizar_visita",
    "contido_visita",
    "crear_visita",
    "dar_de_baixa_visita",
    "informe_visita",
    "ligar_observacion",
    "ligar_recomendacion",
    "listar_visitas",
    "obter_visita",
    "proximas_visitas",
]

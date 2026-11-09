"""Servizo de xestión de certificacións, autoavaliación e informes de auditoría (tarefa 182c)."""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from sqlalchemy.orm import Session

from horta.idiomas import N_
from horta.models.abonado import Fertilizante
from horta.models.certificacion import Certificacion, PuntoAutoavaliacion
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados
from horta.services.analises import listar_analises
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import nome_cultivo
from horta.services.documentos import estado_documento, listar_documentos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import entrado, listar_lotes, listar_saidas, queda, saido
from horta.services.persoas import nome_completo, titular_da_horta
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import listar_tratamentos_fito

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

ESQUEMAS: dict[str, str] = {
    "ecoloxica": N_("Agricultura e gandaría ecolóxica (CRAEGA)"),
    "dop_igp": N_("Denominación de orixe ou IGP"),
    "producion_integrada": N_("Produción integrada"),
    "globalgap": N_("GlobalG.A.P."),
    "qs": N_("QS"),
    "leaf": N_("LEAF Marque"),
    "demeter": N_("Demeter (biodinámica)"),
    "outro": N_("Outro selo"),
}

RESULTADOS: tuple[str, ...] = ("cumpre", "non_cumpre", "non_aplica")


def _validar_certificacion(
    esquema: str,
    nome: str | None,
    numero: str | None,
    data_inicio: date | None,
    data_fin: date | None,
) -> None:
    if esquema not in ESQUEMAS:
        raise OperacionNonPermitidaError(f"Esquema de certificación non recoñecido: {esquema}")
    if esquema in ("dop_igp", "outro") and not (nome or "").strip():
        raise OperacionNonPermitidaError(
            "O nome é obrigatorio para denominacións de orixe / IGP e outros selos"
        )
    if esquema == "globalgap" and numero and numero.strip():
        num = numero.strip()
        if len(num) != 13 or not num.isdigit():
            raise OperacionNonPermitidaError(
                "O número GlobalG.A.P. (GGN) debe ter exactamente 13 díxitos"
            )
    if data_inicio is not None and data_fin is not None and data_fin < data_inicio:
        raise OperacionNonPermitidaError(
            "A data de fin non pode ser anterior á data de inicio"
        )


def crear_certificacion(
    session: Session,
    actor: Usuario,
    horta_id: int,
    esquema: str,
    nome: str | None = None,
    numero: str | None = None,
    entidade: str | None = None,
    data_inicio: date | None = None,
    data_fin: date | None = None,
    documento_id: int | None = None,
) -> Certificacion:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_certificacion(esquema, nome, numero, data_inicio, data_fin)
    doc_id = documento_id if documento_id and documento_id > 0 else None
    cert = Certificacion(
        horta_id=horta_id,
        esquema=esquema,
        nome=nome.strip() if nome and nome.strip() else None,
        numero=numero.strip() if numero and numero.strip() else None,
        entidade=entidade.strip() if entidade and entidade.strip() else None,
        data_inicio=data_inicio,
        data_fin=data_fin,
        documento_id=doc_id,
        activa=True,
    )
    session.add(cert)
    session.commit()
    return cert


def actualizar_certificacion(
    session: Session,
    actor: Usuario,
    certificacion: Certificacion,
    esquema: str | None = None,
    nome: str | None = None,
    numero: str | None = None,
    entidade: str | None = None,
    data_inicio: date | None = None,
    data_fin: date | None = None,
    documento_id: int | None = None,
) -> Certificacion:
    if not certificacion.activa:
        raise OperacionNonPermitidaError("Unha certificación dada de baixa non se pode modificar")
    comprobar_rol_horta(session, certificacion.horta_id, actor, _ROLES_ESCRITURA)

    esquema_act = esquema if esquema is not None else certificacion.esquema
    nome_act = nome if nome is not None else certificacion.nome
    numero_act = numero if numero is not None else certificacion.numero
    d_inicio = data_inicio if data_inicio is not None else certificacion.data_inicio
    d_fin = data_fin if data_fin is not None else certificacion.data_fin
    _validar_certificacion(esquema_act, nome_act, numero_act, d_inicio, d_fin)

    certificacion.esquema = esquema_act
    certificacion.nome = nome_act.strip() if nome_act and nome_act.strip() else None
    certificacion.numero = numero_act.strip() if numero_act and numero_act.strip() else None
    if entidade is not None:
        certificacion.entidade = entidade.strip() if entidade.strip() else None
    if data_inicio is not None:
        certificacion.data_inicio = data_inicio
    if data_fin is not None:
        certificacion.data_fin = data_fin
    if documento_id is not None:
        certificacion.documento_id = documento_id if documento_id > 0 else None

    session.commit()
    return certificacion


def baixa_certificacion(
    session: Session,
    actor: Usuario,
    certificacion: Certificacion,
) -> None:
    comprobar_rol_horta(session, certificacion.horta_id, actor, _ROLES_ESCRITURA)
    certificacion.activa = False
    session.commit()


def listar_certificacions(
    session: Session,
    actor: Usuario,
    horta_id: int,
    so_activas: bool = True,
) -> list[Certificacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    q = session.query(Certificacion).filter_by(horta_id=horta_id)
    if so_activas:
        q = q.filter(Certificacion.activa.is_(True))
    return list(
        q.order_by(
            Certificacion.data_inicio.desc().nulls_last(),
            Certificacion.id.desc(),
        ).all()
    )


def estado_certificacion(certificacion: Certificacion, hoxe: date | None = None) -> str:
    """Calcula o estado: 'caducado', 'caduca_pronto' (<= 60 días) ou 'vixente'."""
    dia = hoxe or date.today()
    if certificacion.data_fin is None:
        return "vixente"
    if certificacion.data_fin < dia:
        return "caducado"
    if certificacion.data_fin <= dia + timedelta(days=60):
        return "caduca_pronto"
    return "vixente"


def _validar_punto(
    punto: str,
    resultado: str,
    accion_correctora: str | None,
) -> None:
    if not (punto or "").strip():
        raise OperacionNonPermitidaError("O código do punto é obrigatorio")
    if resultado not in RESULTADOS:
        raise OperacionNonPermitidaError(
            f"O resultado debe ser un de: {', '.join(RESULTADOS)}"
        )
    if resultado == "non_cumpre" and not (accion_correctora or "").strip():
        raise OperacionNonPermitidaError(
            "A acción correctora é obrigatoria cando o resultado é «non_cumpre»"
        )


def crear_punto(
    session: Session,
    actor: Usuario,
    certificacion_id: int,
    data: date,
    punto: str,
    resultado: str,
    evidencia: str | None = None,
    documento_id: int | None = None,
    accion_correctora: str | None = None,
    data_correccion: date | None = None,
) -> PuntoAutoavaliacion:
    cert = session.get(Certificacion, certificacion_id)
    if cert is None or not cert.activa:
        raise OperacionNonPermitidaError("A certificación non existe ou está dada de baixa")
    comprobar_rol_horta(session, cert.horta_id, actor, _ROLES_ESCRITURA)
    _validar_punto(punto, resultado, accion_correctora)

    doc_id = documento_id if documento_id and documento_id > 0 else None
    pto = PuntoAutoavaliacion(
        certificacion_id=certificacion_id,
        data=data,
        punto=punto.strip(),
        resultado=resultado,
        evidencia=evidencia.strip() if evidencia and evidencia.strip() else None,
        documento_id=doc_id,
        accion_correctora=(
            accion_correctora.strip() if accion_correctora and accion_correctora.strip() else None
        ),
        data_correccion=data_correccion,
    )
    session.add(pto)
    session.commit()
    return pto


def actualizar_punto(
    session: Session,
    actor: Usuario,
    punto_obj: PuntoAutoavaliacion,
    data: date | None = None,
    punto: str | None = None,
    resultado: str | None = None,
    evidencia: str | None = None,
    documento_id: int | None = None,
    accion_correctora: str | None = None,
    data_correccion: date | None = None,
) -> PuntoAutoavaliacion:
    cert = session.get(Certificacion, punto_obj.certificacion_id)
    if cert is None:
        raise OperacionNonPermitidaError("A certificación non existe")
    comprobar_rol_horta(session, cert.horta_id, actor, _ROLES_ESCRITURA)

    punto_act = punto if punto is not None else punto_obj.punto
    resultado_act = resultado if resultado is not None else punto_obj.resultado
    accion_act = (
        accion_correctora if accion_correctora is not None else punto_obj.accion_correctora
    )
    _validar_punto(punto_act, resultado_act, accion_act)

    if data is not None:
        punto_obj.data = data
    punto_obj.punto = punto_act.strip()
    punto_obj.resultado = resultado_act
    if evidencia is not None:
        punto_obj.evidencia = evidencia.strip() if evidencia.strip() else None
    if documento_id is not None:
        punto_obj.documento_id = documento_id if documento_id > 0 else None
    punto_obj.accion_correctora = (
        accion_act.strip() if accion_act and accion_act.strip() else None
    )
    if data_correccion is not None or "data_correccion" in locals():
        punto_obj.data_correccion = data_correccion

    session.commit()
    return punto_obj


def borrar_punto(
    session: Session,
    actor: Usuario,
    punto: PuntoAutoavaliacion,
) -> None:
    cert = session.get(Certificacion, punto.certificacion_id)
    if cert is None:
        raise OperacionNonPermitidaError("A certificación non existe")
    comprobar_rol_horta(session, cert.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(punto)
    session.commit()


def listar_puntos(
    session: Session,
    actor: Usuario,
    certificacion_id: int,
    ano: int | None = None,
) -> list[PuntoAutoavaliacion]:
    cert = session.get(Certificacion, certificacion_id)
    if cert is None:
        raise OperacionNonPermitidaError("A certificación non existe")
    comprobar_rol_horta(session, cert.horta_id, actor, _ROLES_LECTURA)
    q = session.query(PuntoAutoavaliacion).filter_by(certificacion_id=certificacion_id)
    if ano is not None:
        q = q.filter(
            PuntoAutoavaliacion.data >= date(ano, 1, 1),
            PuntoAutoavaliacion.data <= date(ano, 12, 31),
        )
    return list(
        q.order_by(
            PuntoAutoavaliacion.data.asc(),
            PuntoAutoavaliacion.punto.asc(),
        ).all()
    )


def avisos_certificacions(
    session: Session,
    actor: Usuario,
    horta_id: int,
    hoxe: date | None = None,
) -> list[str]:
    """Avisos de selos que caducan en 60 días ou xa caducaron, e de correccións pendentes."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    dia = hoxe or date.today()
    avisos: list[str] = []
    certificacions = listar_certificacions(session, actor, horta_id, so_activas=True)
    for c in certificacions:
        nome_selo = c.nome or ESQUEMAS.get(c.esquema, c.esquema)
        if c.data_fin is not None:
            if c.data_fin < dia:
                avisos.append(
                    f"O selo «{nome_selo}» caducou o {c.data_fin:%d/%m/%Y}"
                )
            elif c.data_fin <= dia + timedelta(days=60):
                dias = (c.data_fin - dia).days
                if dias <= 0:
                    avisos.append(f"O selo «{nome_selo}» caduca hoxe")
                elif dias == 1:
                    avisos.append(f"O selo «{nome_selo}» caduca en 1 día")
                else:
                    avisos.append(
                        f"O selo «{nome_selo}» caduca en {dias} días ({c.data_fin:%d/%m/%Y})"
                    )

        puntos_pendentes = (
            session.query(PuntoAutoavaliacion)
            .filter_by(certificacion_id=c.id, resultado="non_cumpre")
            .filter(PuntoAutoavaliacion.data_correccion.is_(None))
            .all()
        )
        for p in puntos_pendentes:
            avisos.append(
                f"Selo «{nome_selo}»: corrección pendente no punto {p.punto}"
            )

    return avisos


def informe_auditoria(
    session: Session,
    actor: Usuario,
    certificacion_id: int,
    ano: int,
) -> dict[str, list[list[Any]]]:
    """Xera o informe completo para a auditoría coas nove follas requiridas."""
    cert = session.get(Certificacion, certificacion_id)
    if cert is None:
        raise OperacionNonPermitidaError("A certificación non existe")
    horta_id = cert.horta_id
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)

    horta = session.get(Horta, horta_id)
    assert horta is not None
    titular = titular_da_horta(session, horta_id)
    nome_titular = nome_completo(titular) if titular else ""
    selo = cert.nome if cert.nome else ESQUEMAS.get(cert.esquema, cert.esquema)

    validez: str
    if cert.data_inicio and cert.data_fin:
        validez = f"{cert.data_inicio:%d/%m/%Y} - {cert.data_fin:%d/%m/%Y}"
    elif cert.data_inicio:
        validez = f"Desde {cert.data_inicio:%d/%m/%Y}"
    elif cert.data_fin:
        validez = f"Ata {cert.data_fin:%d/%m/%Y}"
    else:
        validez = "Indefinida"

    # 1. Explotación e selo
    folla_explotacion: list[list[Any]] = [
        ["Dato", "Valor"],
        ["Nome da explotación", horta.nome],
        ["Código REAGA", horta.codigo_reaga or ""],
        ["Persoa titular", nome_titular],
        ["Selo de calidade", selo],
        ["Número / Código de operador", cert.numero or ""],
        ["Entidade certificadora", cert.entidade or ""],
        ["Validez", validez],
    ]

    # 2. Autoavaliación
    folla_autoavaliacion: list[list[Any]] = [
        ["Data", "Punto", "Resultado", "Evidencia", "Acción correctora", "Data corrección"]
    ]
    puntos = listar_puntos(session, actor, certificacion_id, ano)
    for p in puntos:
        folla_autoavaliacion.append([
            f"{p.data:%d/%m/%Y}",
            p.punto,
            p.resultado,
            p.evidencia or "",
            p.accion_correctora or "",
            f"{p.data_correccion:%d/%m/%Y}" if p.data_correccion else "",
        ])

    # 3. Tratamentos
    folla_tratamentos: list[list[Any]] = [
        [
            "Data inicio",
            "Data fin",
            "Cultivos",
            "Problemas",
            "Produtos / Medidas",
            "Materias activas",
            "Dose",
            "Eficacia",
        ]
    ]
    for t in listar_tratamentos_fito(session, actor, horta_id):
        if t.data_inicio.year != ano:
            continue
        cultivos_t = [session.get(Cultivo, tc.cultivo_id) for tc in t.cultivos]
        cultivos_desc = ", ".join(nome_cultivo(c) for c in cultivos_t if c is not None)
        problemas_desc = ", ".join(
            f"{prob.tipo}:{prob.codigo}" for prob in t.problemas
        )
        prods = [p.nome_comercial or "" for p in t.produtos if p.nome_comercial]
        meds = [m.tipo_medida for m in t.medidas if m.tipo_medida]
        produtos_desc = ", ".join([*prods, *meds])
        materias_desc = ", ".join(
            p.materia_activa for p in t.produtos if p.materia_activa
        )
        doses_desc = ", ".join(
            f"{p.dose:g} {p.unidade}" for p in t.produtos if p.dose is not None
        )
        folla_tratamentos.append([
            f"{t.data_inicio:%d/%m/%Y}",
            f"{t.data_fin:%d/%m/%Y}" if t.data_fin else "",
            cultivos_desc,
            problemas_desc,
            produtos_desc,
            materias_desc,
            doses_desc,
            t.eficacia or "",
        ])

    # 4. Abonados
    folla_abonados: list[list[Any]] = [
        ["Data", "Fertilizante", "Tipo", "Dose", "Unidade", "Superficie total (ha)"]
    ]
    for ab in listar_abonados(session, actor, horta_id):
        if ab.data_inicio.year != ano:
            continue
        sup_total = sum(leira.superficie_ha or 0.0 for leira in ab.leiras)
        fert = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
        folla_abonados.append([
            f"{ab.data_inicio:%d/%m/%Y}",
            fert.nome if fert else "",
            ab.tipo_fertilizacion or "",
            ab.dose if ab.dose is not None else "",
            ab.unidade or "",
            round(sup_total, 3) if sup_total > 0 else "",
        ])

    # 5. Regas
    folla_regas: list[list[Any]] = [
        ["Data inicio", "Data fin", "Volume", "Unidade", "Sistema de rega"]
    ]
    for r in listar_regas(session, actor, horta_id):
        if r.data_inicio.year != ano:
            continue
        folla_regas.append([
            f"{r.data_inicio:%d/%m/%Y}",
            f"{r.data_fin:%d/%m/%Y}" if r.data_fin else "",
            r.cantidade if r.cantidade is not None else "",
            r.unidade or "",
            r.sistema_rega or "",
        ])

    # 6. Colleitas e lotes
    folla_colleitas: list[list[Any]] = [
        ["Data", "Cultivo", "Cantidade", "Unidade", "Lote", "Destino"]
    ]
    for c in listar_colleitas(session, actor, horta_id):
        if c.data.year != ano:
            continue
        cult = session.get(Cultivo, c.cultivo_id)
        folla_colleitas.append([
            f"{c.data:%d/%m/%Y}",
            nome_cultivo(cult) if cult else "",
            c.cantidade,
            c.unidade,
            c.lote,
            c.destino_colleita or "",
        ])

    # 7. Saídas de lotes (balance de masas: entrado, saído e quedan por lote)
    folla_saidas: list[list[Any]] = [
        ["Lote", "Entrado", "Saído", "Quedan", "Unidade", "Data", "Tipo de saída", "Cantidade"]
    ]
    lotes = listar_lotes(session, actor, horta_id)
    saidas_todas = listar_saidas(session, actor, horta_id)
    for lt in lotes:
        e = entrado(session, lt)
        s = saido(session, lt)
        q = queda(session, lt)
        saidas_lote = [sd for sd in saidas_todas if sd.lote_id == lt.id and sd.data.year == ano]
        if lt.data.year == ano or saidas_lote:
            if saidas_lote:
                for sd in saidas_lote:
                    folla_saidas.append([
                        lt.codigo,
                        round(e, 3),
                        round(s, 3),
                        round(q, 3),
                        lt.unidade,
                        f"{sd.data:%d/%m/%Y}",
                        sd.tipo,
                        sd.cantidade,
                    ])
            else:
                folla_saidas.append([
                    lt.codigo,
                    round(e, 3),
                    round(s, 3),
                    round(q, 3),
                    lt.unidade,
                    "",
                    "",
                    "",
                ])

    # 8. Análises
    folla_analises: list[list[Any]] = [
        ["Data mostraxe", "Material analizado", "Nº boletín", "Notas"]
    ]
    for an in listar_analises(session, actor, horta_id):
        if an.data_mostraxe.year != ano:
            continue
        folla_analises.append([
            f"{an.data_mostraxe:%d/%m/%Y}",
            an.material_analizado or "",
            an.num_boletin or "",
            an.notas or "",
        ])

    # 9. Documentos (con caducidade e se está vixente)
    folla_documentos: list[list[Any]] = [
        ["Nome", "Tipo", "Emisor", "Número", "Data emisión", "Data caducidade", "Estado"]
    ]
    dia_actual = date.today()
    for doc in listar_documentos(session, actor, horta_id):
        st = estado_documento(doc, dia_actual)
        nomes_estados = {
            "vixente": "Vixente",
            "caduca_pronto": "Caduca pronto",
            "caducado": "Caducado",
        }
        st_gl = nomes_estados.get(st, "Vixente")
        folla_documentos.append([
            doc.nome,
            doc.tipo,
            doc.emisor or "",
            doc.numero or "",
            f"{doc.data_emision:%d/%m/%Y}" if doc.data_emision else "",
            f"{doc.data_caducidade:%d/%m/%Y}" if doc.data_caducidade else "",
            st_gl,
        ])

    return {
        "Explotación e selo": folla_explotacion,
        "Autoavaliación": folla_autoavaliacion,
        "Tratamentos": folla_tratamentos,
        "Abonados": folla_abonados,
        "Regas": folla_regas,
        "Colleitas e lotes": folla_colleitas,
        "Saídas de lotes": folla_saidas,
        "Análises": folla_analises,
        "Documentos": folla_documentos,
    }


def informe_auditoria_xlsx(
    session: Session,
    actor: Usuario,
    certificacion_id: int,
    ano: int,
) -> bytes:
    """Xera o caderno de auditoría en formato Excel .xlsx."""
    dados = informe_auditoria(session, actor, certificacion_id, ano)
    wb = Workbook()
    wb.remove(wb.active)  # Quitar a folla inicial baleira por defecto
    for nome_folla, filas in dados.items():
        ws = wb.create_sheet(title=nome_folla[:31])
        for fila in filas:
            ws.append(list(fila))
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()

"""Caderno de explotación en Excel, co modelo oficial da Xunta (7/8/2026).

Seccións e columnas: a documentación. Expórtase cando se queira e para o
período que se escolla; o que a app aínda non garda queda en branco.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet
from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.persoa import Persoa, TipoCarne
from horta.models.tratamento_fito import TratamentoProduto
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados, nutrientes_do_abonado
from horta.services.analises import SOLO, listar_analises
from horta.services.catalogos import describir
from horta.services.colleitas import listar_colleitas
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import dose_kg_ha
from horta.services.hortas import TIPOS_XIP, comprobar_rol_horta
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import listar_tratamentos_fito
from horta.services.tratamentos_instalacion import listar_tratamentos_instalacion

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_A_KG = {"kg": 1.0, "t": 1000.0}
_A_M3 = {"3": 1.0, "4": 0.001}  # UNIDADES_MEDIDA: m³ e litros
_NEGRA = Font(bold=True)


def _data(valor: date | None) -> str:
    return f"{valor:%d/%m/%Y}" if valor else ""


def _intervalo(inicio: date, fin: date | None) -> str:
    return _data(inicio) if not fin or fin == inicio else f"{_data(inicio)} - {_data(fin)}"


def _num(valor: float | None) -> float | str:
    return "" if valor is None else round(valor, 3)


def _folla(wb: Workbook, nome: str, titulo: str, cabeceira_explotacion: str,
           cabeceiras: Sequence[str], filas: Iterable[Sequence[Any]]) -> Worksheet:
    ws = wb.create_sheet(nome)
    ws.append([titulo])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append([cabeceira_explotacion])
    ws.append([])
    ws.append(list(cabeceiras))
    for cela in ws[4]:
        cela.font = _NEGRA
        cela.alignment = Alignment(wrap_text=True, vertical="top")
    for fila in filas:
        ws.append(list(fila))
    for i in range(1, len(cabeceiras) + 1):
        ws.column_dimensions[ws.cell(row=4, column=i).column_letter].width = 16
    return ws


def _activo(cultivo: Cultivo, desde: date, ata: date) -> bool:
    inicio, fin = cultivo.data_inicio, cultivo.data_fin
    return (inicio is None or inicio <= ata) and (fin is None or fin >= desde)


def xerar_caderno(
    session: Session, actor: Usuario, horta_id: int, desde: date, ata: date
) -> bytes:
    """Excel do caderno da explotación co que se rexistrou entre `desde` e `ata`."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    if ata < desde:
        raise OperacionNonPermitidaError("A data final non pode ser anterior á inicial")
    horta = session.get(Horta, horta_id)
    assert horta is not None
    parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
    cultivos = [c for c in session.query(Cultivo).filter(Cultivo.parcela_id.in_(parcelas))
                .order_by(Cultivo.parcela_id, Cultivo.id) if _activo(c, desde, ata)]
    orde_cultivo = {c.id: i for i, c in enumerate(cultivos, 1)}
    persoas = session.query(Persoa).filter_by(horta_id=horta_id).order_by(Persoa.id).all()
    aplicadores = [p for p in persoas if p.e_aplicador or p.e_asesor]
    orde_persoa = {p.id: i for i, p in enumerate(aplicadores, 1)}
    maquinas = session.query(Maquina).filter_by(horta_id=horta_id).order_by(Maquina.id).all()
    orde_maquina = {m.id: i for i, m in enumerate(maquinas, 1)}
    titular = next((p for p in persoas if p.e_titular), None)
    cab = (f"Explotación/Titular da explotación: {horta.nome} / "
           f"{horta.titular_nome or (titular.nome if titular else '')}   "
           f"Período: {_data(desde)} - {_data(ata)}")

    def no_periodo(inicio: date, fin: date | None = None) -> bool:
        return inicio <= ata and (fin or inicio) >= desde

    def cultivo_de(cultivo_id: int | None) -> Cultivo | None:
        return next((c for c in cultivos if c.id == cultivo_id), None) \
            or (session.get(Cultivo, cultivo_id) if cultivo_id else None)

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "1 Información xeral"
    for fila in (
        ["1. INFORMACIÓN XERAL"], [cab], [],
        ["1.1 DATOS XERAIS DA EXPLOTACIÓN"],
        ["Nome e apelidos ou razón social", horta.titular_nome or horta.nome],
        ["NIF", horta.titular_nif or (titular.nif if titular else "")],
        ["CEA/Nº de Rexistro da Explotación", horta.codigo_reaga or ""],
        ["Código REGA", horta.codigo_rega or ""],
        ["Dirección", horta.enderezo or ""],
        ["Localidade", horta.localidade or ""],
        ["C. Postal", horta.codigo_postal or ""],
        ["Provincia", horta.provincia or ""],
        ["Teléfono", horta.telefono or ""],
        ["e-mail", horta.email or ""],
        [],
        ["TITULAR OU REPRESENTANTE DA EXPLOTACIÓN"],
        ["Nome e apelidos", " ".join(x for x in (titular.nome, titular.apelidos or "")
                                     if x) if titular else ""],
        ["NIF", (titular.nif or "") if titular else ""],
        ["Dirección", (titular.enderezo or "") if titular else ""],
        ["Localidade", (titular.localidade or "") if titular else ""],
        ["C. Postal", (titular.codigo_postal or "") if titular else ""],
        ["Provincia", (titular.provincia or "") if titular else ""],
        ["Tipo de representación", horta.tipo_representacion or ""],
        ["Teléfono", (titular.telefono or "") if titular else ""],
        ["e-mail", (titular.email or "") if titular else ""],
        [],
        ["1.2 PERSOAS OU EMPRESAS QUE INTERVEÑEN NO TRATAMENTO CON PRODUTOS FITOSANITARIOS"],
        ["Nº de orde", "Nome e apelidos / Empresas de servizos", "NIF", "Nº Inscrición ROPO",
         "Básico", "Cualif.", "Fumig", "Piloto", "Asesor", "Nº REGFER"],
        *[[orde_persoa[p.id], " ".join(x for x in (p.nome, p.apelidos or "") if x), p.nif or "",
           p.ropo_numero or "",
           *["X" if p.ropo_tipo_carne == t else "" for t in (
               TipoCarne.basico, TipoCarne.cualificado, TipoCarne.fumigador, TipoCarne.piloto)],
           "X" if p.e_asesor else "", p.regfer_numero or ""] for p in aplicadores],
        [],
        ["1.3 EQUIPOS DE APLICACIÓN DE PRODUTOS FITOSANITARIOS E PRODUTOS FERTILIZANTES "
         "PROPIOS DA EXPLOTACIÓN"],
        ["Nº de orde", "Descrición do equipo", "Nº inscrición ROMA", "Data de adquisición",
         "Data da última inspección"],
        *[[orde_maquina[m.id], " ".join(x for x in (m.alias, m.marca_modelo or "") if x),
           m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "",
           _data(m.data_adquisicion), _data(m.data_ultima_inspeccion)]
          for m in maquinas if m.propia],
        [],
        ["1.4 AGRUPACIÓN OU ENTIDADE DE ASESORAMENTO A QUE PERTENCE A EXPLOTACIÓN"],
        ["Nome ou razón social", "NIF", "Nº de identificación", "Tipo de explotación"],
        [horta.asesoramento_nome or "", horta.asesoramento_nif or "",
         horta.asesoramento_num or "", horta.tipo_xip or ""],
    ):
        ws.append(fila)
    ws["A1"].font = Font(bold=True, size=13)
    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 36

    xip = (f"{horta.tipo_xip} ({TIPOS_XIP[horta.tipo_xip]})"
           if horta.tipo_xip in TIPOS_XIP else "")

    def fila_parcela(c: Cultivo) -> list[Any]:
        p = parcelas[c.parcela_id]
        return [orde_cultivo[c.id], p.sigpac_provincia or "", p.sigpac_concello or "",
                p.sigpac_agregado or "", p.sigpac_zona or "", p.sigpac_poligono or "",
                p.sigpac_parcela or "", p.sigpac_subparcela or "", p.uso_aproveitamento or "",
                _num(p.superficie), _num(c.superficie_ha), c.especie, c.variedade or "",
                {SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
                    p.secano_regadio, "") if p.secano_regadio else "",
                describir(session, "sistema_cultivo", c.sistema_cultivo)
                if c.sistema_cultivo else "", xip, p.nome]

    _folla(wb, "2 Parcelas", "2.1 DATOS IDENTIFICATIVOS E AGRONÓMICOS DAS PARCELAS", cab,
           ["Nº de orde", "Provincia", "Termo municipal", "Agregado", "Zona", "Polígono",
            "Parcela", "Recinto", "Uso SIXPAC", "Superficie SIXPAC (ha)",
            "Superficie cultivada (ha)", "Especie", "Variedade", "Secano/Regadío",
            "Aire libre ou protexido", "Sistema de asesoramento en XIP",
            "Nome da parcela (horta)"],
           [fila_parcela(c) for c in cultivos])
    ws2 = wb["2 Parcelas"]
    ws2.append([])
    ws2.append(["2.2 DATOS IDENTIFICATIVOS MEDIOAMBIENTAIS DAS PARCELAS"])
    ws2.append(["Id. parcelas", "Especie", "Variedade",
                "Captación de auga para consumo humano: incluído na parcela (SI/NON)",
                "Distancia (m)", "Coordenadas UTM", "Denominación",
                "Zona específica: totalmente (SI/NON)", "Parcialmente (SI/NON)",
                "Superficie afectada (ha)"])
    for cu in cultivos:
        pa = parcelas[cu.parcela_id]
        if not (pa.auga_consumo or pa.zona_especifica):
            continue
        ws2.append([orde_cultivo[cu.id], cu.especie, cu.variedade or "",
                    ("SI" if pa.auga_consumo_na_parcela else "NON") if pa.auga_consumo else "",
                    _num(pa.auga_consumo_distancia_m) if pa.auga_consumo else "",
                    pa.auga_consumo_utm or "", pa.auga_consumo_denominacion or "",
                    "SI" if pa.zona_especifica == "total" else "NON",
                    "SI" if pa.zona_especifica == "parcial" else "NON",
                    _num(pa.zona_especifica_ha)])

    filas_trat = []
    for t in listar_tratamentos_fito(session, actor, horta_id):
        if t.baixa or not no_periodo(t.data_inicio, t.data_fin):
            continue
        problema = ", ".join(describir(session, p.tipo, p.codigo) for p in t.problemas)
        aplicador = t.aplicadores[0] if t.aplicadores else None
        for tc in t.cultivos:
            c = cultivo_de(tc.cultivo_id)
            produtos: list[TratamentoProduto | None] = list(t.produtos) or [None]
            for pr in produtos:
                filas_trat.append([
                    orde_cultivo.get(tc.cultivo_id, ""), c.especie if c else "",
                    (c.variedade or "") if c else "", _intervalo(t.data_inicio, t.data_fin),
                    _num(tc.superficie_ha), problema,
                    orde_persoa.get(aplicador.persoa_id, "") if aplicador else "",
                    orde_maquina.get(aplicador.maquina_id or 0, "") if aplicador else "",
                    (pr.nome_comercial or pr.materia_activa or "") if pr else "",
                    (pr.num_rexistro or "") if pr else "",
                    f"{_num(pr.dose)} {describir(session, 'unidade_medida', pr.unidade)}"
                    if pr and pr.dose is not None else "",
                    describir(session, "eficacia", t.eficacia) if t.eficacia else "",
                    t.observacions or ""])
    _folla(wb, "3 Tratamentos", "3.1 REXISTRO DE ACTUACIÓNS FITOSANITARIAS DA PARCELA", cab,
           ["Id. parcelas (nº de orde)", "Especie", "Variedade", "Intervalo de datas",
            "Sup. tratada (ha)", "Problema fitosanitario", "Aplicador (nº de orde)",
            "Equipo (nº de orde)", "Nome comercial", "Nº Rexistro", "Dose", "Eficacia",
            "Observacións"], filas_trat)
    ws3 = wb["3 Tratamentos"]
    ws3.append([])
    ws3.append(["3.1 bis REXISTRO DE TRATAMENTOS FITOSANITARIOS DA PARCELA (soamente para "
                "cultivos e superficies obxecto de asesoramento)"])
    ws3.append(["Especie", "Variedade", "Id. parcelas", "Superficie cultivada (ha)",
                "Superficie tratada (ha)", "Praga", "Xustificación da actuación",
                "Alternativas non químicas: tipo de medida", "Intensidade da medida",
                "Data de actuación", "Alternativas químicas: nome comercial",
                "Número de rexistro", "Dose utilizada", "Data de actuación",
                "Eficacia da intervención", "Observacións", "Asesor", "Nº inscrición ROPO",
                "Data de validación"])
    for t in listar_tratamentos_fito(session, actor, horta_id):
        if t.baixa or not no_periodo(t.data_inicio, t.data_fin) or t.asesor is None:
            continue
        asesor = session.get(Persoa, t.asesor.persoa_id)
        praga = ", ".join(describir(session, p.tipo, p.codigo) for p in t.problemas)
        xust = ", ".join(describir(session, "xustificacion", x.codigo) for x in t.xustificacions)
        medidas = ", ".join(describir(session, "tipo_medida_fito", m.tipo_medida)
                            for m in t.medidas)
        intensidade = ", ".join(f"{m.cantidade:g} {describir(session, 'unidade_medida', m.unidade)}"
                                for m in t.medidas if m.cantidade is not None and m.unidade)
        pr = t.produtos[0] if t.produtos else None
        for tc in t.cultivos:
            cv = cultivo_de(tc.cultivo_id)
            ws3.append([
                cv.especie if cv else "", (cv.variedade or "") if cv else "",
                orde_cultivo.get(tc.cultivo_id, ""), _num(cv.superficie_ha) if cv else "",
                _num(tc.superficie_ha), praga, xust, medidas, intensidade,
                _intervalo(t.data_inicio, t.data_fin) if t.medidas else "",
                (pr.nome_comercial or pr.materia_activa or "") if pr else "",
                (pr.num_rexistro or "") if pr else "",
                f"{_num(pr.dose)} {describir(session, 'unidade_medida', pr.unidade)}"
                if pr and pr.dose is not None else "",
                _intervalo(t.data_inicio, t.data_fin) if pr else "",
                describir(session, "eficacia", t.eficacia) if t.eficacia else "",
                t.observacions or "",
                " ".join(x for x in (asesor.nome, asesor.apelidos or "") if x) if asesor else "",
                (asesor.ropo_numero or "") if asesor else "", _data(t.asesor.data)])
    tratadas = [c for c in cultivos if c.material_tratado
                and c.data_inicio and no_periodo(c.data_inicio)]
    ws3.append([])
    ws3.append(["3.2 REXISTRO DE USO DE SEMENTE TRATADA"])
    ws3.append(["Aplica tratamento", "SI" if tratadas else "NON"])
    ws3.append(["Data de sementeira", "Id. parcelas", "Especie", "Variedade",
                "Superficie sementada (ha)", "Cantidade de semente (kg)",
                "Materia activa / Nome comercial", "Nº rexistro"])
    for cu in tratadas:
        ws3.append([_data(cu.data_inicio), orde_cultivo[cu.id], cu.especie, cu.variedade or "",
                    _num(cu.superficie_ha), _num(cu.cantidade_semente_kg),
                    cu.semente_tratamento_produto or "", cu.semente_tratamento_num_rexistro or ""])
    instalacions = [ti for ti in listar_tratamentos_instalacion(session, actor, horta_id)
                    if no_periodo(ti.data)]
    for tipo, titulo, que, cantidade in (
        ("postcolleita", "3.3 REXISTRO DE TRATAMENTOS POSTCOLLEITA (en produto vexetal)",
         "Produto vexetal tratado", "Cantidade de prod. vex. tratado (ti)"),
        ("local", "3.4 REXISTRO DE TRATAMENTOS DOS LOCAIS DE ALMACENAMENTO",
         "Local tratado (tipo e dirección)", "Volume tratado (m³)"),
        ("transporte", "3.5 REXISTRO DE TRATAMENTOS DOS MEDIOS DE TRANSPORTE",
         "Vehículo tratado (tipo, modelo e matrícula)", "Volume tratado (m³)"),
    ):
        destes = sorted((ti for ti in instalacions if ti.tipo == tipo), key=lambda ti: ti.data)
        ws3.append([])
        ws3.append([titulo])
        ws3.append(["Aplica tratamento", "SI" if destes else "NON"])
        ws3.append(["Data", que, "Referencia catastral", "Problemática fitosanitaria",
                    cantidade, "Nome comercial", "Nº Rexistro", "Materia activa",
                    "Cantidade utilizada (kg ou l)"])
        for ti in destes:
            ws3.append([
                _data(ti.data), ti.obxecto, ti.referencia_catastral or "",
                describir(session, ti.problema_tipo, ti.problema_codigo)
                if ti.problema_tipo and ti.problema_codigo else "",
                _num(ti.cantidade_tratada), ti.nome_comercial or "", ti.num_rexistro or "",
                ti.materia_activa or "",
                f"{_num(ti.cantidade_utilizada)} {describir(session, 'unidade_medida', ti.unidade)}"
                if ti.cantidade_utilizada is not None and ti.unidade else
                _num(ti.cantidade_utilizada)])

    analises = [a for a in listar_analises(session, actor, horta_id)
                if no_periodo(a.data_mostraxe)]
    _folla(wb, "4 Análises", "4. REXISTRO DE ANÁLISE DE PRODUTOS FITOSANITARIOS "
           "(en caso de realizarse)", cab,
           ["Data", "Material analizado", "Cultivo ou colleita mostrado/s", "Nº Boletín",
            "Laboratorio", "Sustancias activas detectadas"],
           [[_data(a.data_mostraxe), describir(session, "material_analizado",
                                               a.material_analizado),
             ", ".join(x for x in (str(orde_cultivo.get(a.cultivo_id or 0, "")),) if x),
             a.num_boletin or "", a.laboratorio or "",
             ", ".join(describir(session, "substancia_activa", s.codigo)
                       for s in a.substancias)]
            for a in analises if a.material_analizado != SOLO])

    filas_colleita = []
    for col in listar_colleitas(session, actor, horta_id):
        if not no_periodo(col.data, col.data_fin):
            continue
        c = cultivo_de(col.cultivo_id)
        kg = col.cantidade * _A_KG[col.unidade] if col.unidade in _A_KG else None
        filas_colleita.append([
            _intervalo(col.data, col.data_fin), c.especie if c else "",
            _num(kg) if kg is not None else f"{col.cantidade:g} {col.unidade}",
            orde_cultivo.get(col.cultivo_id, ""), col.albaran_factura or "", col.lote,
            "", "", "", ""])
    _folla(wb, "5 Colleita", "5. REXISTRO DE COLLEITA COMERCIALIZADA", cab,
           ["Data", "Produto", "Cantidade de produto (kg)", "Nº de orde parcela/s de orixe",
            "Nº de albará ou factura", "Nº de lote", "Cliente: nome ou razón social",
            "NIF", "Dirección", "Nº de REAGA"], filas_colleita)

    _folla(wb, "6 Solos", "6. CARACTERIZACIÓN DE SOLOS", cab,
           ["Id. parcelas", "Data", "pH", "Mat. orgánica (%)", "Nitróxeno (%)",
            "Fósforo (P₂O₅) asimilable (ppm)", "Potasio (K₂O) asimilable (ppm)", "Cadmio",
            "Cobre", "Níquel", "Chumbo", "Zinc", "Mercurio", "Cromo total"],
           [[parcelas[a.parcela_id].nome if a.parcela_id in parcelas else
             orde_cultivo.get(a.cultivo_id or 0, ""), _data(a.data_mostraxe), _num(a.ph),
             _num(a.materia_organica), _num(a.n_total), _num(a.fosforo_ppm),
             _num(a.potasio_ppm), "", "", "", "", "", "", ""]
            for a in analises if a.material_analizado == SOLO])

    filas_fert = []
    for ab in listar_abonados(session, actor, horta_id):
        if not no_periodo(ab.data_inicio, ab.data_fin):
            continue
        c = cultivo_de(ab.cultivo_id)
        p = parcelas.get(c.parcela_id) if c else None
        fe = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
        npk = nutrientes_do_abonado(session, ab)
        kg_ha = dose_kg_ha(ab.dose, ab.unidade, fe.densidade if fe else None) \
            if ab.dose is not None and ab.unidade else None
        persoa = session.get(Persoa, ab.aplicador_persoa_id) if ab.aplicador_persoa_id else None
        maquina = session.get(Maquina, ab.maquina_id) if ab.maquina_id else None
        filas_fert.append([
            _intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(ab.cultivo_id, ""),
            ({SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
                p.secano_regadio, "") if p and p.secano_regadio else ""),
            c.especie if c else "", _num(ab.superficie_ha),
            describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion),
            describir(session, "material_fertilizante", fe.material) if fe else
            "Abonado en verde",
            fe.nome if fe else "", (fe.provedor_nome or "") if fe else "",
            (fe.provedor_rega or fe.provedor_nif or fe.provedor_nima or "") if fe else "",
            describir(session, "metodo_fertilizacion", ab.metodo),
            maquina.alias if maquina else "",
            ab.empresa_servizos_regfer or ((persoa.regfer_numero or "") if persoa else ""),
            _num(fe.n_pct) if fe else "", _num(fe.p2o5_pct) if fe else "",
            _num(fe.k2o_pct) if fe else "",
            _num(kg_ha / 1000) if kg_ha is not None else "",
            *(npk if npk else ("", "", "")),
            ab.albaran_factura or ""])
    ws7 = _folla(wb, "7 Fertilización", "7. FERTILIZACIÓN", cab,
                 ["Data aplicación", "Identificación parcelas (nº de orde)", "Secano/regadío",
                  "Cultivo", "Superficie fertilizada (ha)", "Tipo de tratamento",
                  "Tipo de material", "Material empregado", "Empresa subministradora",
                  "REGA/NIF/NIMA", "Forma de aplicación", "Máquina de tratamento",
                  "Nº REGFER", "Valor agronómico: N total (%)", "P₂O₅ total (%)",
                  "K₂O total (%)", "Dose (t/ha)", "Aportadas N (kg/ha)",
                  "Aportadas P₂O₅ (kg/ha)", "Aportadas K₂O (kg/ha)", "Nº albará/factura"],
                 filas_fert)
    ws7.append([])
    plan = any(c.plan_necesidade_n or c.plan_necesidade_p2o5 or c.plan_necesidade_k2o
               for c in cultivos)
    datas_plan = [c.plan_data for c in cultivos if c.plan_data]
    ws7.append(["Plan de abonado de cultivos", "SI" if plan else "NON",
                "Data de entrada en vigor", _data(min(datas_plan)) if datas_plan else ""])
    ws7.append(["Asesoramento", "SI" if horta.asesoramento_fertilizacion else "NON"])
    ws7.append([])
    ws7.append(["PLAN DE ABONADO (necesidades en kg/ha)"])
    ws7.append(["Nº de orde", "Cultivo", "Data do plan", "N", "P₂O₅", "K₂O",
                "Obxectivo de produción (kg/ha)", "Ferramenta de cálculo"])
    for c in cultivos:
        if c.plan_necesidade_n or c.plan_necesidade_p2o5 or c.plan_necesidade_k2o:
            ws7.append([orde_cultivo[c.id], c.especie, _data(c.plan_data),
                        _num(c.plan_necesidade_n), _num(c.plan_necesidade_p2o5),
                        _num(c.plan_necesidade_k2o), _num(c.obxectivo_colleita_kg_ha),
                        "SI" if c.plan_ferramenta_sostibilidade else "NON"])

    filas_rega = []
    acumulado: dict[int, float] = {}
    for r in sorted(listar_regas(session, actor, horta_id), key=lambda x: x.data_inicio):
        if not no_periodo(r.data_inicio, r.data_fin):
            continue
        c = cultivo_de(r.cultivo_id)
        m3_ha = (r.cantidade * _A_M3.get(r.unidade, 0) / r.superficie_ha
                 if r.superficie_ha else None)
        if m3_ha is not None:
            acumulado[r.cultivo_id] = acumulado.get(r.cultivo_id, 0) + m3_ha
        filas_rega.append([
            orde_cultivo.get(r.cultivo_id, ""), _num(r.superficie_ha),
            describir(session, "sistema_rega", r.sistema_rega),
            _intervalo(r.data_inicio, r.data_fin), _num(m3_ha),
            _num(acumulado.get(r.cultivo_id)),
            _num(c.plan_auga_n_nitrico) if c else "", _num(c.plan_auga_p2o5) if c else ""])
    _folla(wb, "8 Rega", "8. REGA", cab,
           ["Id. parcelas (nº de orde)", "Superficie regada (ha)", "Sistema de rega",
            "Data / intervalo rega", "Volume de rega (m³/ha)", "Volume acumulado (m³/ha)",
            "Auga: nitróxeno nítrico (mg/L)", "Auga: fósforo soluble (mg/L)"], filas_rega)

    saida = BytesIO()
    wb.save(saida)
    return saida.getvalue()

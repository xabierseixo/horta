"""Os datos do caderno dixital (CUE) co formato oficial: un CUADERNO en JSON como o pide o
método `crear` do Anexo VI do FEGA, montado co apuntado na app, e o que lle falta, traducido a
que traballo e que dato.

Sen conexión co REA, cada cultivo vai como DGC allea (AltaDGC) coa referencia SIGPAC da súa
parcela; cada actividade leva o id da app (IdAjena…) para poder corrixila despois."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.catalogo import VariedadeSiex
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.lote import Lote
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.persoa import Persoa
from horta.models.produto import EntradaProduto
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados
from horta.services.analises import listar_analises
from horta.services.colleitas import listar_colleitas
from horta.services.cue_descritor import Erro, validar
from horta.services.cultivos import listar_cultivos
from horta.services.hortas import comprobar_rol_horta
from horta.services.labores import DESBROCE, PODAS, listar_labores
from horta.services.lotes import converter, listar_saidas
from horta.services.pastoreos import listar_pastoreos
from horta.services.persoas import titular_da_horta
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import listar_tratamentos_fito

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Organismo pagador da Comunidade Autónoma de Galicia (lista de valores do SIEX)
CA_GALICIA = "12"
# Unidades da app → catálogo oficial de unidades de medida
UNIDADES_CUE = {"kg": 5, "t": 6, "litros": 4, "l": 4, "m3": 3, "unidades": 11}
# Os tipos de problema da app → bloque e campo do CUE
_PROBLEMAS = {"enfermidade": ("Enfermedades", "TipoEnfermedad"),
              "praga": ("ArtropodosGasteropodos", "TipoPlaga"),
              "mala_herba": ("MalasHierbas", "TipoMalaHierba"),
              "regulador": ("ReguladoresOtros", "TipoRegulador")}
# Nomes en galego dos campos do CUE que máis faltan, para dicir que completar
_CAMPOS = {
    "FechaInicio": "a data", "FechaFin": "a data de fin", "Superficie": "a superficie",
    "SistemaRiego": "o sistema de rega", "Cantidad": "a cantidade", "UnidadMedida": "a unidade",
    "Unidad": "a unidade", "TipoLabor": "o tipo de labor", "Eficacia": "a eficacia",
    "JustAct": "a xustificación", "NumROPO": "o nº ROPO", "AplicacionManual": "a aplicación",
    "TipoFertilizacion": "o tipo de fertilización", "MetodoFertilizacion": "o método",
    "Dosis": "a dose", "TipoBPF": "as boas prácticas", "Material": "o material do abono",
    "Provincia": "a provincia SIGPAC", "Municipio": "o concello SIGPAC",
    "Agregado": "o agregado SIGPAC", "Zona": "a zona SIGPAC", "Poligono": "o polígono SIGPAC",
    "Parcela": "a parcela SIGPAC", "Recinto": "o recinto SIGPAC", "Cultivo": "o cultivo oficial",
    "Variedad": "a variedade oficial", "SistemaExplotacion": "secano ou regadío",
    "SistCultivo": "o sistema de cultivo", "IdTitular": "o NIF do titular",
    "UnidadGestora": "o NIF do titular", "CodigoRea": "o código REAGA",
    "ProductoVegetal": "o produto oficial", "ProductoCosechado": "o produto oficial",
    "MaterialAnalizado": "o material analizado", "REGA": "o REGA", "Especie": "a especie",
    "FechaAdquisicion": "a data de compra da semente",
    "NecesidadUFN": "a necesidade de N", "ObjetivoProduccion": "o obxectivo de produción",
    "CultivoPrecedente": "o cultivo anterior", "FechaGeneracion": "a data do plan",
}


def _data(d: date | None) -> str | None:
    return f"{d:%d/%m/%Y}" if d else None


def _num(valor: Any) -> int | None:
    """Un código de catálogo (texto) como número."""
    try:
        return int(valor) if valor not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _ha(superficie: float | None) -> float | None:
    return round(superficie, 2) if superficie else None


def _limpo(bloque: dict[str, Any]) -> dict[str, Any]:
    """Sen os campos baleiros (None, [] ou {}), que o descritor trata como non enviados."""
    return {k: v for k, v in bloque.items() if v not in (None, [], {})}


@dataclass
class Orixe:
    """De que traballo da app saíu un bloque do CUE."""

    tipo: str  # clave de services.diario.TIPOS, ou «cultivo», «explotacion»
    id: int | None
    texto: str


@dataclass
class FaltaCue:
    orixe: Orixe
    falta: str  # p.ex. «o sistema de rega»
    ruta: str  # ruta no CUE, para o detalle


@dataclass
class Cue:
    datos: dict[str, Any]
    orixes: dict[str, Orixe]  # ruta do bloque → traballo

    def faltas(self) -> list[FaltaCue]:
        """O que lle falta ao CUE para o descritor oficial, por traballo."""
        return [_falta(self.orixes, erro) for erro in validar(self.datos)]


def _falta(orixes: dict[str, Orixe], erro: Erro) -> FaltaCue:
    ruta = erro.ruta
    orixe = next((o for prefixo, o in sorted(orixes.items(), key=lambda x: -len(x[0]))
                  if ruta == prefixo or ruta.startswith(prefixo + "/")),
                 Orixe("explotacion", None, "Datos da explotación"))
    campo = ruta.rsplit("/", 1)[-1].split("[")[0]
    nome = _CAMPOS.get(campo, campo)
    return FaltaCue(orixe, nome if erro.mensaxe == "é obrigatorio" else f"{nome}: {erro.mensaxe}",
                    ruta)


def xerar_cue(session: Session, actor: Usuario, horta_id: int, desde: date, ata: date) -> Cue:
    """O CUADERNO do período coas actividades apuntadas na app."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    horta = session.get(Horta, horta_id)
    assert horta is not None
    titular = titular_da_horta(session, horta_id)
    orixes: dict[str, Orixe] = {}

    def no_periodo(inicio: date | None, fin: date | None = None) -> bool:
        return inicio is not None and inicio <= ata and (fin or inicio) >= desde

    cultivos = {c.id: c for c in listar_cultivos(session, actor, horta_id)}
    parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
    persoas = {p.id: p for p in session.query(Persoa).filter_by(horta_id=horta_id)}
    maquinas = {m.id: m for m in session.query(Maquina).filter_by(horta_id=horta_id)}
    usados: set[int] = set()

    def dgc(cultivo_id: int, **mais: Any) -> dict[str, Any]:
        usados.add(cultivo_id)
        return _limpo({"CodigoDGCAjena": cultivo_id, **mais})

    def grupos(leiras: list[tuple[int, float | None]]) -> list[list[tuple[int, float | None]]]:
        """O CUE quere en cada actividade DGCs do mesmo produto e variedade."""
        por_produto: dict[tuple[Any, Any], list[tuple[int, float | None]]] = defaultdict(list)
        for cultivo_id, superficie in leiras:
            c = cultivos.get(cultivo_id)
            chave = (c.cultivo_siex_codigo, c.variedade_siex_id) if c else (None, None)
            por_produto[chave].append((cultivo_id, superficie))
        return list(por_produto.values())

    actividades: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def engadir(bloque: str, datos: dict[str, Any], orixe: Orixe) -> None:
        actividades[bloque].append(_limpo(datos))
        orixes[f"CUADERNO/ActividadesExplotacion/{bloque}[{len(actividades[bloque])}]"] = orixe

    # --- Sementeira ou plantación (o cultivo)
    for c in cultivos.values():
        if not no_periodo(c.data_inicio, c.data_fin_sementeira or c.data_inicio):
            continue
        plantacion = c.tipo_inicio == "plantacion"
        # A compra da semente ou planta (paso 7): provedor, lote e data
        semente = session.get(EntradaProduto, c.entrada_semente_id) if c.entrada_semente_id \
            else None
        engadir("SiembraPlantacion", {
            "IdAjenaSiembraPlant": c.id, "SiembraPlantacion": 0 if plantacion else 1,
            "FechaInicio": _data(c.data_inicio),
            "FechaFin": _data(c.data_fin_sementeira or c.data_inicio),
            "SiembraDirecta": c.sementeira_directa,
            "DosisSiembra": c.dose_sementeira_kg_ha,
            "UnidadDosisSiembra": 17 if c.dose_sementeira_kg_ha else None,
            "MaterialTratado": c.material_tratado, "MaterialAdquirido": semente is not None,
            "FechaAdquisicion": _data(semente.data if semente else c.data_inicio),
            "NumLote": semente.lote_provedor if semente else None,
            "DGCs": [dgc(c.id, SuperficieCultivada=_ha(c.superficie_ha))],
            "Cantidad": c.cantidade_semente_kg, "MarcoPlantacion": c.marco_plantacion,
            "DensidadPlantacion": c.densidade_plantas_ha,
        }, Orixe("sementeira", c.id, f"Sementeira ou plantación de {c.especie}"))

    # --- Tratamentos fitosanitarios
    for t in listar_tratamentos_fito(session, actor, horta_id):
        if not no_periodo(t.data_inicio, t.data_fin):
            continue
        problemas: dict[str, Any] = {}
        for p in t.problemas:
            bloque, campo = _PROBLEMAS.get(p.tipo, (None, None))
            if bloque and bloque not in problemas:
                problemas[bloque] = {campo: _num(p.codigo)}
        aplicadores = []
        for ap in t.aplicadores:
            persoa = persoas.get(ap.persoa_id)
            m = maquinas.get(ap.maquina_id or 0)
            aplicadores.append({
                "AplicadorEmpresa": {"NumROPO": persoa.ropo_numero if persoa else None},
                "EquipoAplicador": _limpo({
                    "NumROMA": m.num_roma if m else None,
                    "NumREGANIP": m.num_reganip if m and not m.num_roma else None,
                    "EquipoPropio": m.propia if m else None,
                    "IdEquipoAplicador": m.id_equipo_non_inscribible if m else None,
                    "AplicacionManual": ap.aplicacion_manual,
                    "HorasUtilizacion": ap.horas_utilizacion,
                    "TipoMaquinariaUNE": m.tipo_une if m else None,
                    "NumRepeticiones": ap.num_repeticions, "Duracion": ap.duracion})})
        asesor = persoas.get(t.asesor.persoa_id) if t.asesor else None
        orixe = Orixe("tratamento", t.id, f"Tratamento do {t.data_inicio:%d/%m/%Y}")
        for n, grupo in enumerate(grupos([(tc.cultivo_id, tc.superficie_ha)
                                          for tc in t.cultivos])):
            fenoloxico = {tc.cultivo_id: tc.estado_fenoloxico for tc in t.cultivos}
            engadir("TratamFito", {
                "IdAjenaTratamFito": t.id * 100 + n,
                "FechaInicio": _data(t.data_inicio), "FechaFin": _data(t.data_fin),
                "HoraTratamiento": f"{t.hora:%H:%M:%S}" if t.hora else None,
                "Actividad": _num(t.actividade_cuberta),
                "DGCs": [dgc(c, Superficie=_ha(s), EstadoFenologico=_num(fenoloxico.get(c)))
                         for c, s in grupo],
                "ProblematicaFito": problemas,
                "Justificaciones": [{"JustAct": _num(x.codigo)} for x in t.xustificacions],
                "OtrasActuacionesFito": _limpo({
                    "TipoMedida": _num(t.medidas[0].tipo_medida),
                    "Cantidad": t.medidas[0].cantidade, "Unidad": _num(t.medidas[0].unidade),
                    "NumRegistroMDF": t.medidas[0].num_rexistro_mdf,
                    "BuenasPracticas": _num(t.medidas[0].boas_practicas)})
                if t.medidas else None,
                "ProductosFito": [_limpo({
                    "TipoProducto": _num(p.tipo_produto), "NumRegistro": p.num_rexistro,
                    "Dosis": p.dose, "Cantidad": p.cantidade if p.dose is None else None,
                    "Unidad": _num(p.unidade)}) for p in t.produtos],
                "IdentificadorAplicador": aplicadores,
                "AsesorValidacion": _limpo({
                    "NumROPO": asesor.ropo_numero if asesor else None,
                    "Fecha": _data(t.asesor.data), "Validacion": t.asesor.validacion,
                    "Observaciones": t.asesor.observacions,
                    "Confirmacion": t.asesor.confirmacion, "Contrato": t.asesor.contrato})
                if t.asesor else None,
                "Eficacia": _num(t.eficacia),
                "Observaciones": (t.notas or "")[:150] or None,
            }, orixe)

    # --- Abonados
    for ab in listar_abonados(session, actor, horta_id):
        if not no_periodo(ab.data_inicio, ab.data_fin):
            continue
        fe = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
        entrada = session.get(EntradaProduto, ab.entrada_id) if ab.entrada_id else None
        provedor = persoas.get(entrada.provedor_id or 0) if entrada else None
        quen = persoas.get(ab.persoa_id or 0)
        m = maquinas.get(ab.maquina_id or 0)
        orixe = Orixe("abonado", ab.id, f"Abonado do {ab.data_inicio:%d/%m/%Y}")
        for n, grupo in enumerate(grupos([(le.cultivo_id, le.superficie_ha)
                                          for le in ab.leiras])):
            engadir("Fertilizacion", {
                "IdAjenaFerti": ab.id * 100 + n,
                "FechaInicio": _data(ab.data_inicio), "FechaFin": _data(ab.data_fin),
                "DeclaraBuenasPracticas": bool(ab.boas_practicas),
                "GestionSostInsu": ab.xestion_sostible,
                "BuenasPracticas": [{"TipoBPF": _num(b.codigo)} for b in ab.boas_practicas],
                "MaterialFertilizante": _limpo({
                    "Material": _num(fe.material), "DetalleMaterial": fe.fertilizante_siex_codigo,
                    "EmpresaSuministradora": provedor.nome if provedor else None,
                    "NifEmpresa": provedor.nif if provedor else None,
                    "REGA": provedor.rega if provedor else None,
                    "NIMA": provedor.nima if provedor else None,
                    "TratamientoEstiercoles": _num(fe.tratamento_estercos),
                    "Densidad": fe.densidade}) if fe else None,
                "AplicacionMaterialFertilizante": _limpo({
                    "NombreProducto": fe.nome[:250] if fe else None,
                    "AplicacionLodos": ab.aplicacion_lodos,
                    "TipoFertilizacion": _num(ab.tipo_fertilizacion),
                    "MetodoFertilizacion": _num(ab.metodo), "Dosis": ab.dose,
                    "Unidad": _num(ab.unidade),
                    "AlbaranFactura": entrada.albaran_factura if entrada else None,
                    "EmpresaServicios": quen.regfer_numero if quen and quen.ten_papel(
                        "servizos") else None,
                    "NifAplicador": quen.nif if quen else None}),
                "EquipoAplicador": _limpo({
                    "NumROMA": m.num_roma, "EquipoPropio": m.propia,
                    "IdEquipoAplicador": m.id_equipo_non_inscribible,
                    "TipoMaquinariaUNE": m.tipo_une, "NumRepeticiones": ab.num_repeticions,
                    "Duracion": ab.duracion_h_ha}) if m else None,
                "DGCs": [dgc(c, Superficie=_ha(s)) for c, s in grupo],
            }, orixe)

    # --- Regas: a auga repártese pola superficie de cada grupo de leiras
    for r in listar_regas(session, actor, horta_id):
        if not no_periodo(r.data_inicio, r.data_fin):
            continue
        total = sum(le.superficie_ha or 0 for le in r.leiras)
        orixe = Orixe("rega", r.id, f"Rega do {r.data_inicio:%d/%m/%Y}")
        for n, grupo in enumerate(grupos([(le.cultivo_id, le.superficie_ha)
                                          for le in r.leiras])):
            parte = (sum(s or 0 for _, s in grupo) / total) if total else 1.0
            engadir("Riego", {
                "IdAjenaRiego": r.id * 100 + n,
                "FechaInicio": _data(r.data_inicio), "FechaFin": _data(r.data_fin),
                "SistemaRiego": _num(r.sistema_rega),
                "Cantidad": round(r.cantidade * parte, 2) if r.cantidade else None,
                "UnidadMedida": _num(r.unidade),
                "OrigenAgua": [{"IdOrigenAgua": _num(r.orixe_auga)}] if r.orixe_auga else [],
                "TipoEnergia": _num(r.tipo_enerxia), "NumContador": r.num_contador,
                "BuenasPracticasRiego": [{"TipoBPR": _num(b.codigo)} for b in r.boas_practicas],
                "DGCs": [dgc(c, Superficie=_ha(s)) for c, s in grupo],
            }, orixe)

    # --- Labores
    for lab in listar_labores(session, actor, horta_id):
        if not no_periodo(lab.data_inicio, lab.data_fin):
            continue
        m = maquinas.get(lab.maquina_id or 0)
        orixe = Orixe("labor", lab.id, f"Labor do {lab.data_inicio:%d/%m/%Y}")
        for n, grupo in enumerate(grupos([(le.cultivo_id, le.superficie_ha)
                                          for le in lab.leiras])):
            engadir("LaboresCulturales", {
                "IdAjenaLabor": lab.id * 100 + n,
                "FechaInicio": _data(lab.data_inicio), "FechaFin": _data(lab.data_fin),
                "TipoLabor": _num(lab.tipo_labor),
                "DepositadoSueloDesb": lab.restos_desbroce_no_solo
                if lab.tipo_labor == DESBROCE else None,
                "DepositadoSueloPoda": lab.restos_poda_no_solo
                if lab.tipo_labor in PODAS else None,
                "Maquinaria": [_limpo({
                    "TipoMaquinariaUNE": m.tipo_une, "PotenciaMaquinaria": m.potencia,
                    "UnidadesMedida": _num(m.unidade_potencia),
                    "TipoEnergia": _num(m.tipo_enerxia),
                    "NumRepeticiones": lab.num_repeticions or 1,
                    "Duracion": lab.duracion_h})] if m else [],
                "DGCs": [dgc(c, Superficie=_ha(s), Cubiertas=[{"TipoCobertura": _num(
                    lab.tipo_cobertura)}] if lab.tipo_cobertura else [])
                         for c, s in grupo],
            }, orixe)

    # --- Colleitas
    for col in listar_colleitas(session, actor, horta_id):
        if not no_periodo(col.data, col.data_fin):
            continue
        cultivo_col = cultivos.get(col.cultivo_id)
        cantidade, unidade = col.cantidade, col.unidade
        if unidade == "ducias":
            cantidade, unidade = cantidade * 12, "unidades"
        engadir("Cosecha", {
            "IdAjenaCosecha": col.id, "CosechaSiega": 1,
            "FechaInicio": _data(col.data), "FechaFin": _data(col.data_fin or col.data),
            "Cantidad": round(cantidade, 2), "Unidad": UNIDADES_CUE.get(unidade),
            "DGCs": [dgc(col.cultivo_id, ProductoCosechado=cultivo_col.cultivo_siex_codigo
                         if cultivo_col else None,
                         Superficie=_ha(col.superficie_ha))],
            "FinalidadCosecha": [{"IdFinalidad": _num(col.destino_colleita)}]
            if col.destino_colleita else [],
            "GestionInsumos": False,
            "DestinoRestoVeg": [{"IdDestinoRest": _num(col.destino_restos)}]
            if col.destino_restos else [],
            "SemillasSiembra": col.obten_sementes, "Plantas": col.obten_plantas,
            "SinCosechado": col.sen_colleita_ambiental, "DepositadoSuelo": col.restos_no_solo,
        }, Orixe("colleita", col.id, f"Colleita do {col.data:%d/%m/%Y}"))

    # --- Pastoreo
    for pa in listar_pastoreos(session, actor, horta_id):
        if not no_periodo(pa.data_inicio, pa.data_fin or ata):
            continue
        animais = []
        for li in pa.animais:
            propietario = persoas.get(li.propietario_id or 0)
            animais.append({"REGA": horta.codigo_rega if li.animal_id else (
                propietario.rega if propietario else None),
                "Numero": li.numero, "Especie": _num(li.especie_codigo)})
        engadir("Pastoreo", {
            "IdAjenaPastoreo": pa.id,
            "FechaInicio": _data(pa.data_inicio), "FechaFin": _data(pa.data_fin),
            "AnimalesTerceros": any(li.animal_id is None for li in pa.animais),
            "AnimalesPropios": any(li.animal_id is not None for li in pa.animais),
            "Animales": animais,
            "DGCs": [dgc(le.cultivo_id, Superficie=_ha(le.superficie_ha),
                         Cubiertas=[{"TipoCobertura": _num(le.tipo_cobertura)}]
                         if le.tipo_cobertura else []) for le in pa.leiras],
        }, Orixe("pastoreo", pa.id, f"Pastoreo do {pa.data_inicio:%d/%m/%Y}"))

    # --- Vendas dos lotes de colleitas (CUE 3)
    colleitas_lote: dict[int, list[int]] = defaultdict(list)
    for col in listar_colleitas(session, actor, horta_id):
        colleitas_lote[col.lote_id].append(col.cultivo_id)
    for venda in listar_saidas(session, actor, horta_id):
        lote = session.get(Lote, venda.lote_id)
        if (venda.tipo != "venda" or lote is None or lote.produto_animal is not None
                or not no_periodo(venda.data, venda.data_fin)):
            continue
        cliente = persoas.get(venda.comprador_id or 0)
        kg = converter(venda.cantidade, venda.unidade, "kg")
        entidade = cliente is not None and cliente.tipo == "entidade"
        engadir("ComercializacionVD", {
            "IdAjenaVenta": venda.id,
            "FechaInicio": _data(venda.data), "FechaFin": _data(venda.data_fin),
            "ProductoVegetal": lote.cultivo_siex_codigo,
            "TipoVenta": 1 if venda.canle == "almacen" else 0,
            "Cantidad": round(kg if kg is not None else venda.cantidade, 2),
            "Unidad": 5 if kg is not None else UNIDADES_CUE.get(venda.unidade),
            "NumFactura": venda.albaran_factura, "NumLote": lote.codigo,
            "NumRegDigital": cliente.rexistro_dixital if cliente else None,
            "IdComprador": cliente.nif if cliente else None,
            "Nombre": cliente.nome[:150] if cliente and not entidade else None,
            "PrimerApellido": (cliente.apelidos or "").split(" ")[0] or None
            if cliente and not entidade else None,
            "RazonSocial": cliente.nome[:150] if entidade and cliente else None,
            "Direccion": cliente.enderezo if cliente else None,
            "Provincia": cliente.concello_codigo[:2] if cliente and cliente.concello_codigo
            else None,
            "Municipio": cliente.concello_codigo[2:] if cliente and cliente.concello_codigo
            else None,
            "CP": cliente.codigo_postal if cliente else None,
            "DGCs": [dgc(c) for c in sorted(set(colleitas_lote.get(lote.id, [])))],
        }, Orixe("lote_saida", venda.id, f"Venda do {venda.data:%d/%m/%Y}"))

    # --- Análises
    for an in listar_analises(session, actor, horta_id):
        if not no_periodo(an.data_mostraxe):
            continue
        laboratorio = persoas.get(an.laboratorio_id or 0)
        solo = _limpo({"MateriaOrganica": an.materia_organica, "Arena": an.area,
                       "Limo": an.limo, "Arcilla": an.arxila, "Ph": an.ph,
                       "FosforoAsimilable": an.fosforo_ppm, "PotasioAsimilable": an.potasio_ppm,
                       "NitrogenoTotal": an.n_total, "Conductividad": an.conductividade})
        engadir("Analitica", {
            "IdAjenaAna": an.id, "MaterialAnalizado": _num(an.material_analizado),
            "Fecha": _data(an.data_mostraxe),
            "Laboratorio": laboratorio.nome[:150] if laboratorio else None,
            "Nif": laboratorio.nif if laboratorio else None, "NumBoletin": an.num_boletin,
            "TiposAnalisis": [{"TipoAnalisis": _num(t.codigo)} for t in an.tipos],
            "TiposSustancias": [{"TipoSustancia": _num(s.codigo)} for s in an.substancias],
            "ParametrosSuelo": solo or None,
            "DGCs": [dgc(an.cultivo_id)] if an.cultivo_id else [],
        }, Orixe("analise", an.id, f"Análise do {an.data_mostraxe:%d/%m/%Y}"))

    # --- Plan de abonado de cada cultivo
    for c in cultivos.values():
        if not (c.plan_necesidade_n or c.plan_necesidade_p2o5 or c.plan_necesidade_k2o):
            continue
        if c.plan_data and not no_periodo(c.plan_data, ata):
            continue
        engadir("PlanAbonado", {
            "IdAjenaPlan": c.id, "NecesidadUFN": c.plan_necesidade_n,
            "NecesidadUFP2O5": c.plan_necesidade_p2o5, "NecesidadUFK2O": c.plan_necesidade_k2o,
            "ObjetivoProduccion": c.obxectivo_colleita_kg_ha,
            "CultivoPrecedente": c.cultivo_anterior_codigo,
            "Herramienta": c.plan_ferramenta_sostibilidade,
            "FechaGeneracion": _data(c.plan_data), "DGCs": [dgc(c.id)],
        }, Orixe("cultivo", c.id, f"Plan de abonado de {c.especie}"))

    # --- As leiras (DGC alleas) usadas nas actividades
    altas = []
    for cultivo_id in sorted(usados):
        alta = cultivos.get(cultivo_id) or session.get(Cultivo, cultivo_id)
        if alta is None:
            continue
        c = alta
        parcela = parcelas.get(c.parcela_id)
        variedade = session.get(VariedadeSiex, c.variedade_siex_id) if c.variedade_siex_id \
            else None
        altas.append(_limpo({
            "CodigoDGCAjena": c.id,
            "ReferenciaCatastral": parcela.referencia_catastral if parcela else None,
            "Provincia": parcela.sigpac_provincia if parcela else None,
            "Municipio": parcela.sigpac_concello if parcela else None,
            "Agregado": _num(parcela.sigpac_agregado) if parcela else None,
            "Zona": _num(parcela.sigpac_zona) if parcela else None,
            "Poligono": _num(parcela.sigpac_poligono) if parcela else None,
            "Parcela": _num(parcela.sigpac_parcela) if parcela else None,
            "Recinto": _num(parcela.sigpac_subparcela) if parcela else None,
            "Superficie": _ha(c.superficie_ha),
            "FechaInicio": _data(c.data_inicio), "FechaFin": _data(c.data_fin),
            "Cultivo": c.cultivo_siex_codigo,
            "Variedad": variedade.codigo if variedade else None,
            "SistemaExplotacion": (
                {SecanoRegadio.SECANO: "S", SecanoRegadio.REGADIO: "R"}.get(parcela.secano_regadio)
                if parcela and parcela.secano_regadio else None),
            "SistCultivo": _num(c.sistema_cultivo),
        }))
        orixes[f"CUADERNO/DatosExplotacion/AltaDGC[{len(altas)}]"] = Orixe(
            "cultivo", c.id, f"Cultivo {c.especie} en {parcela.nome if parcela else ''}".strip())

    nif = titular.nif if titular else None
    cuaderno = _limpo({
        "CAExplotacion": CA_GALICIA, "IdTitular": nif, "UnidadGestora": nif,
        "CodigoRea": horta.codigo_reaga,
        "DatosExplotacion": {"AltaDGC": altas} if altas else None,
        "ActividadesExplotacion": dict(actividades) or None,
    })
    return Cue(cuaderno, orixes)


# Nomes en galego dos bloques, como os formularios do caderno público (XEAGA)
BLOQUES = {
    "AltaDGC": "Leiras (DGC)", "SiembraPlantacion": "Sementeira e plantación",
    "TratamFito": "Tratamentos fitosanitarios", "Fertilizacion": "Fertilización",
    "Riego": "Rega", "LaboresCulturales": "Labores culturais", "Cosecha": "Colleita",
    "Pastoreo": "Pastoreo", "ComercializacionVD": "Venda directa e comercializada",
    "Analitica": "Análises", "PlanAbonado": "Plan de abonado",
}


def json_cue(cue: Cue) -> bytes:
    """O CUADERNO en JSON, como o recibe o método `crear` do Anexo VI."""
    return json.dumps(cue.datos, ensure_ascii=False, indent=2).encode("utf-8")


def _aplanar(datos: dict[str, Any], prefixo: str = "") -> dict[str, str]:
    """Un bloque nunha fila: os subbloques como «Bloque.Campo», as listas xuntas con «; »."""
    fila: dict[str, str] = {}
    for clave, valor in datos.items():
        nome = f"{prefixo}{clave}"
        if isinstance(valor, dict):
            fila |= _aplanar(valor, f"{nome}.")
        elif isinstance(valor, list):
            partes = [", ".join(f"{k}: {v}" for k, v in _aplanar(e).items())
                      if isinstance(e, dict) else str(e) for e in valor]
            fila[nome] = "; ".join(partes)
        elif isinstance(valor, bool):
            fila[nome] = "Si" if valor else "Non"
        else:
            fila[nome] = str(valor)
    return fila


def excel_xeaga(cue: Cue) -> bytes:
    """Para pasar o CUE a man ao caderno público: unha folla por bloque, unha fila por
    rexistro, cos nomes dos campos do descritor oficial."""
    libro = Workbook()
    primeira = libro.active
    assert primeira is not None
    libro.remove(primeira)
    altas = cue.datos.get("DatosExplotacion", {}).get("AltaDGC", [])
    bloques = {"AltaDGC": altas, **cue.datos.get("ActividadesExplotacion", {})}
    for bloque, rexistros in bloques.items():
        if not rexistros:
            continue
        folla = libro.create_sheet(BLOQUES.get(bloque, bloque)[:31])
        filas = [_aplanar(r) for r in rexistros]
        columnas = list(dict.fromkeys(c for f in filas for c in f))
        folla.append(columnas)
        for cela in folla[1]:
            cela.font = Font(bold=True)
        for fila in filas:
            folla.append([fila.get(c, "") for c in columnas])
    if not libro.sheetnames:
        libro.create_sheet("Sen datos").append(["Non hai nada apuntado nese período"])
    saida = BytesIO()
    libro.save(saida)
    return saida.getvalue()

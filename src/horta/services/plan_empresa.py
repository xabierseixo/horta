"""Plan de empresa (paso 16).

A conta a 5 anos propónse desde o real (Contas) e edítase; as amortizacións saen do
investimento e os xuros dos préstamos. VAN, TIR e pay-back calcúlanse. Seguimento: o
previsto de cada ano ao lado do real. Ofertas (Anexo VI-A), o que lle falta para
presentalo e a documentación do art. 18 da convocatoria MR701L (DOG do 2/2/2026)."""

from __future__ import annotations

import functools
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.idiomas import N_
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.lote import Clasificacion, Lote, LoteSaida
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.plan_empresa import (
    PlanActividade,
    PlanAno,
    PlanEmpresa,
    PlanFinanciamento,
    PlanInvestimento,
    PlanObxectivo,
    PlanOferta,
    PlanVenda,
)
from horta.models.usuario import Usuario
from horta.services.cartos import Resumo, horas_dos_traballos, resumo_ano
from horta.services.equipo import HORAS_UTA
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import CANLES, converter
from horta.services.persoas import con_papel, nome_completo, persoa_co_papel, titular_da_horta

# Os cartos e o plan: quen só mira non os ve
_ROLES = {RolHorta.ADMIN, RolHorta.EDITOR}
ANOS = 5
# Anexo V, tal como está no DOG
PARTIDAS: dict[str, str] = {
    "1": N_("1. Adquisición de terreos ou inmobles"),
    "2": N_("2. Obra civil e instalacións"),
    "3": N_("3. Maquinaria e equipamento"),
    "4": N_("4. Estudos, proxectos e honorarios"),
    "5": N_("5. Gastos de constitución"),
    "6": N_("6. Outros"),
}


@dataclass(frozen=True)
class Tipoloxia:
    texto: str
    axuda: str  # intensidade da axuda
    max_investimento: float | None = None  # investimento subvencionable máximo


# Arts. 11–15 da convocatoria
TIPOLOXIAS: dict[str, Tipoloxia] = {
    "primaria_enerxia": Tipoloxia(
        N_("Art. 11.1 · Explotación agraria: eficiencia enerxética ou renovables"),
        N_("15–50 %"),
    ),
    "primaria_complementaria": Tipoloxia(
        N_("Art. 11.2 · Actividade agraria complementaria dunha principal non agraria"),
        N_("15–50 %"),
        30000,
    ),
    "primaria_terras": Tipoloxia(
        N_("Art. 11.3 · Mobilización ou recuperación de terras"),
        N_("15–50 %"),
    ),
    "transformacion": Tipoloxia(
        N_("Art. 12 · Transformación e comercialización de produtos agrarios"),
        N_("15–50 %"),
        60000,
    ),
    "forestal": Tipoloxia(
        N_("Art. 13 · Transformación de produtos forestais"),
        N_("15–40 %, ata 200.000 € de axuda"),
    ),
    "non_agraria": Tipoloxia(
        N_("Art. 14 · Actividades non agrarias"),
        N_("15–50 %, ata 200.000 € de axuda"),
    ),
    "bono": Tipoloxia(
        N_("Art. 15 · Bono Activa Rural"),
        N_("ata 18.000 € a tanto global"),
    ),
}
FONTES: dict[str, str] = {
    "capital": N_("Capital social"),
    "propios": N_("Recursos propios"),
    "prestamo": N_("Créditos ou préstamos"),
    "subvencion": N_("Subvencións"),
    "outros": N_("Outros"),
}
CAMPOS_PLAN = frozenset({
    "titulo", "ano_inicio", "empresa_nova", "cnae", "descricion", "proceso", "formacion",
    "uta_mantidas", "uta_creadas", "uta_mulleres", "uta_mozas", "uta_maiores",
    "uta_discapacidade", "uta_outros", "taxa_desconto", "tipoloxia", "expediente",
    "anualidade", "submedida", "gdr", "participada", "traballadores", "facturacion",
    "balance", "iva_recuperable", "situacion_partida", "metodoloxia", "mercado",
    "ofertas_autenticas", "sen_vinculo_promotor", "sen_vinculo_entre_provedores",
    "dafo_debilidades", "dafo_ameazas", "dafo_fortalezas", "dafo_oportunidades",
    "clientela", "competencia", "mk_produto", "mk_prezo", "mk_canles", "mk_comunicacion",
    "argumentos", "organizacion", "riscos", "permisos", "escenario_pct", "ote_recan"})

# Apartados e campos da memoria complementaria (art. 18.1.p)
SECCIONS_MEMORIA: dict[str, tuple[str, ...]] = {
    N_("Punto de partida e organización"): ("situacion_partida", "metodoloxia", "organizacion"),
    N_("DAFO"): ("dafo_debilidades", "dafo_ameazas", "dafo_fortalezas", "dafo_oportunidades"),
    N_("Mercado"): ("mercado", "clientela", "competencia"),
    N_("Márketing"): ("mk_produto", "mk_prezo", "mk_canles", "mk_comunicacion", "argumentos"),
    N_("Riscos e permisos"): ("riscos", "permisos"),
}

ETIQUETAS_MEMORIA: dict[str, str] = {
    "situacion_partida": N_("situación de partida"),
    "metodoloxia": N_("metodoloxía de traballo"),
    "organizacion": N_("organización e persoas"),
    "dafo_debilidades": N_("debilidades"),
    "dafo_ameazas": N_("ameazas"),
    "dafo_fortalezas": N_("fortalezas"),
    "dafo_oportunidades": N_("oportunidades"),
    "mercado": N_("mercado: tamaño e tendencia"),
    "clientela": N_("clientela"),
    "competencia": N_("competencia"),
    "mk_produto": N_("produto ou servizo"),
    "mk_prezo": N_("prezo"),
    "mk_canles": N_("canles de venda e distribución"),
    "mk_comunicacion": N_("comunicación e promoción"),
    "argumentos": N_("argumentos de venda"),
    "riscos": N_("riscos e como se reducen"),
    "permisos": N_("permisos e rexistros necesarios"),
}


def puntos(texto: str | None) -> list[str]:
    """As liñas non baleiras, sen espazos nin guións ou viñetas («-», «*», «•») ao principio."""
    if not texto:
        return []
    resultado = []
    for lin in texto.splitlines():
        limpa = lin.lstrip("-*• ").strip()
        if limpa:
            resultado.append(limpa)
    return resultado



def _plan(session: Session, actor: Usuario, plan_id: int) -> PlanEmpresa:
    plan = session.get(PlanEmpresa, plan_id)
    if plan is None or plan.baixa:
        raise OperacionNonPermitidaError("Ese plan non existe")
    comprobar_rol_horta(session, plan.horta_id, actor, _ROLES)
    return plan


def base_do_real(resumo: Resumo) -> tuple[float, float, float]:
    """Vendas, custos variables e fixos dun ano real. A man de obra propia (titular e
    familia) non se paga: non entra."""
    vendas = resumo.ingresos.get("Vendas", 0) + resumo.ingresos.get("Venda de animais", 0)
    variables = (resumo.gastos.get("Compras de produtos", 0)
                 + resumo.gastos.get("Compra de animais", 0)
                 + resumo.custos.man_de_obra - resumo.custos.man_de_obra_propia
                 + resumo.custos.maquinas)
    fixos = resumo.total_gastos - variables - resumo.custos.man_de_obra_propia
    return round(vendas, 2), round(variables, 2), round(max(fixos, 0), 2)


def ano_de_referencia(session: Session, actor: Usuario, horta_id: int,
                      hoxe: date | None = None) -> int:
    """O ano pasado se ten datos en Contas; se non (o primeiro ano), o ano en curso (Y9)."""
    ano = (hoxe or date.today()).year
    pasado = resumo_ano(session, actor, horta_id, ano - 1)
    return ano - 1 if pasado.total_ingresos or pasado.total_gastos else ano


def crear_plan(session: Session, actor: Usuario, horta_id: int, titulo: str,
               ano_inicio: int, hoxe: date | None = None) -> PlanEmpresa:
    """Os 5 anos propóñense iguais ao ano de referencia de Contas."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    if not titulo.strip():
        raise OperacionNonPermitidaError("Pon un título ao plan")
    real = ano_de_referencia(session, actor, horta_id, hoxe)
    vendas, variables, fixos = base_do_real(resumo_ano(session, actor, horta_id, real))
    plan = PlanEmpresa(horta_id=horta_id, titulo=titulo.strip(), ano_inicio=ano_inicio,
                       anos=[PlanAno(ano_n=n, vendas=vendas, custos_variables=variables,
                                     custos_fixos=fixos) for n in range(1, ANOS + 1)])
    session.add(plan)
    session.commit()
    return plan


# --- RECAN (Red Contable Agraria Nacional) do MAPA


@functools.cache
def _datos_recan() -> dict[str, Any]:
    ruta = Path(__file__).parent.parent / "data" / "recan_galicia_2023.json"
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


@functools.cache
def orientacions_recan() -> dict[str, str]:
    datos = _datos_recan()
    return {k: str(v["nome"]) for k, v in datos.get("orientacions", {}).items()}


def fonte_recan() -> str:
    return str(_datos_recan().get("fonte", ""))


def actualizar_plan(session: Session, actor: Usuario, plan: PlanEmpresa,
                    **cambios: Any) -> PlanEmpresa:
    _plan(session, actor, plan.id)
    if set(cambios) - CAMPOS_PLAN:
        raise ValueError("Campos non editables no plan")
    if "titulo" in cambios and not (cambios["titulo"] or "").strip():
        raise OperacionNonPermitidaError("Pon un título ao plan")
    if any((v or 0) < 0 for k, v in cambios.items() if k.startswith("uta_")):
        raise OperacionNonPermitidaError("As UTA non poden ser negativas")
    if any((cambios.get(k) or 0) < 0 for k in ("traballadores", "facturacion", "balance")):
        raise OperacionNonPermitidaError("Os datos da empresa non poden ser negativos")
    if cambios.get("tipoloxia") not in (None, *TIPOLOXIAS):
        raise OperacionNonPermitidaError("Escolle a tipoloxía do proxecto")
    if not 0 <= (cambios.get("taxa_desconto", plan.taxa_desconto) or 0) < 1:
        raise OperacionNonPermitidaError("A taxa de desconto vai en tanto por un (p.ex. 0,03)")
    if "escenario_pct" in cambios:
        pct = cambios["escenario_pct"]
        if pct is None or not (1 <= pct <= 90):
            raise OperacionNonPermitidaError("A variación dos escenarios vai do 1 ao 90 %")
    if "ote_recan" in cambios:
        ote = cambios["ote_recan"]
        if ote is not None and ote not in orientacions_recan():
            raise OperacionNonPermitidaError("Esa orientación da RECAN non existe")
    for campo, valor in cambios.items():
        setattr(plan, campo, valor)
    session.commit()
    return plan


def gardar_anos(session: Session, actor: Usuario, plan: PlanEmpresa,
                valores: dict[int, tuple[float, float, float, float]]) -> None:
    """ano_n → (vendas, custos variables, custos fixos, ingresos financeiros)."""
    _plan(session, actor, plan.id)
    hai_detalle = bool(plan.vendas_detalle)
    hai_custo = hai_detalle and any(v.custo_unitario is not None for v in plan.vendas_detalle)
    for ano in plan.anos:
        if ano.ano_n in valores:
            vendas, variables, fixos, financeiros = valores[ano.ano_n]
            if min(vendas, variables, fixos, financeiros) < 0:
                raise OperacionNonPermitidaError("Os importes non poden ser negativos")
            if not hai_detalle:
                ano.vendas = vendas
            if not hai_custo:
                ano.custos_variables = variables
            ano.custos_fixos = fixos
            ano.ingresos_financeiros = financeiros
    session.commit()


def engadir_investimento(session: Session, actor: Usuario, plan: PlanEmpresa, partida: str,
                         concepto: str, importe_sen_iva: float, iva_pct: float = 21,
                         vida_util_anos: int = 10,
                         motivo_sen_ofertas: str | None = None) -> PlanInvestimento:
    _plan(session, actor, plan.id)
    if partida not in PARTIDAS:
        raise OperacionNonPermitidaError("Escolle a partida")
    if not concepto.strip() or importe_sen_iva <= 0:
        raise OperacionNonPermitidaError("Indica o concepto e un importe maior que 0")
    if iva_pct < 0 or vida_util_anos < 0:
        raise OperacionNonPermitidaError("Valores negativos non")
    investimento = PlanInvestimento(
        partida=partida, concepto=concepto.strip(), importe_sen_iva=importe_sen_iva,
        iva_pct=iva_pct, vida_util_anos=0 if partida == "1" else vida_util_anos,
        motivo_sen_ofertas=(motivo_sen_ofertas or "").strip() or None)
    plan.investimentos.append(investimento)
    session.commit()
    return investimento


def engadir_oferta(session: Session, actor: Usuario, plan: PlanEmpresa,
                   investimento: PlanInvestimento, provedor_id: int, importe_sen_iva: float,
                   elixida: bool = False, criterio: str | None = None,
                   xustificacion: str | None = None) -> PlanOferta:
    """Unha oferta dun provedor dos Contactos (Anexo VI-A); só unha elixida por concepto."""
    _plan(session, actor, plan.id)
    if investimento.plan_id != plan.id:
        raise OperacionNonPermitidaError("Ese concepto non é deste plan")
    if importe_sen_iva <= 0:
        raise OperacionNonPermitidaError("Indica un importe maior que 0")
    persoa_co_papel(session, plan.horta_id, provedor_id, "provedor")
    if any(o.provedor_id == provedor_id for o in investimento.ofertas):
        raise OperacionNonPermitidaError("Ese provedor xa ten unha oferta neste concepto")
    if elixida:
        for outra in investimento.ofertas:
            outra.elixida = False
    oferta = PlanOferta(provedor_id=provedor_id, importe_sen_iva=importe_sen_iva,
                        elixida=elixida, criterio=(criterio or "").strip() or None,
                        xustificacion=(xustificacion or "").strip() or None)
    investimento.ofertas.append(oferta)
    session.commit()
    return oferta


def engadir_financiamento(session: Session, actor: Usuario, plan: PlanEmpresa, tipo: str,
                          importe: float, xuro_pct: float | None = None,
                          anos: int | None = None) -> PlanFinanciamento:
    _plan(session, actor, plan.id)
    if tipo not in FONTES or importe <= 0:
        raise OperacionNonPermitidaError("Escolle a fonte e un importe maior que 0")
    if tipo == "prestamo" and not (xuro_pct is not None and xuro_pct >= 0 and anos
                                   and anos > 0):
        raise OperacionNonPermitidaError("Un préstamo precisa o xuro e os anos")
    fonte = PlanFinanciamento(tipo=tipo, importe=importe,
                              xuro_pct=xuro_pct if tipo == "prestamo" else None,
                              anos=anos if tipo == "prestamo" else None)
    plan.financiamento.append(fonte)
    session.commit()
    return fonte


def engadir_actividade(session: Session, actor: Usuario, plan: PlanEmpresa,
                       mes_inicio: int, mes_fin: int, actividade: str,
                       responsable: str | None = None) -> PlanActividade:
    _plan(session, actor, plan.id)
    if not (1 <= mes_inicio <= mes_fin <= 12):
        raise OperacionNonPermitidaError(
            "Os meses van do 1 ao 12 e o fin non pode ir antes do inicio"
        )
    if not (actividade or "").strip():
        raise OperacionNonPermitidaError("Indica a actividade")
    act = PlanActividade(
        plan_id=plan.id,
        mes_inicio=mes_inicio,
        mes_fin=mes_fin,
        actividade=actividade.strip(),
        responsable=(responsable or "").strip() or None,
    )
    plan.actividades.append(act)
    session.commit()
    return act


def engadir_obxectivo(session: Session, actor: Usuario, plan: PlanEmpresa,
                      obxectivo: str, indicador: str, meta: str | None = None,
                      prazo: str | None = None) -> PlanObxectivo:
    _plan(session, actor, plan.id)
    if not (obxectivo or "").strip() or not (indicador or "").strip():
        raise OperacionNonPermitidaError("Indica o obxectivo e como se mide")
    obx = PlanObxectivo(
        plan_id=plan.id,
        obxectivo=obxectivo.strip(),
        indicador=indicador.strip(),
        meta=(meta or "").strip() or None,
        prazo=(prazo or "").strip() or None,
    )
    plan.obxectivos.append(obx)
    session.commit()
    return obx


def meses_de(texto: str) -> list[int]:
    """Os números 1–12 do texto separado por comas, sen repetir e ordenados; se non queda
    ningún, os 12."""
    numeros: set[int] = set()
    for parte in (texto or "").split(","):
        parte = parte.strip()
        if parte.isdigit():
            n = int(parte)
            if 1 <= n <= 12:
                numeros.add(n)
    return sorted(numeros) if numeros else list(range(1, 13))


def engadir_venda(
    session: Session,
    actor: Usuario,
    plan: PlanEmpresa,
    produto: str,
    unidade: str,
    canle: str,
    cantidade: float,
    prezo: float,
    custo_unitario: float | None = None,
    crece_cantidade_pct: float = 0,
    crece_prezo_pct: float = 0,
    meses: list[int] | str | None = None,
) -> PlanVenda:
    _plan(session, actor, plan.id)
    if not (produto or "").strip() or not (unidade or "").strip():
        raise OperacionNonPermitidaError("Indica o produto e a unidade")
    if canle not in CANLES:
        raise OperacionNonPermitidaError("Escolle a canle")
    if cantidade <= 0 or prezo <= 0:
        raise OperacionNonPermitidaError("A cantidade e o prezo teñen que ser maiores que 0")
    if custo_unitario is not None and custo_unitario < 0:
        raise OperacionNonPermitidaError("O custo unitario non pode ser negativo")
    if crece_cantidade_pct < -100 or crece_prezo_pct < -100:
        raise OperacionNonPermitidaError("O crecemento non pode ser menor que -100 %")
    if meses is None:
        meses_str = ",".join(str(m) for m in meses_de(""))
    elif isinstance(meses, str):
        meses_str = ",".join(str(m) for m in meses_de(meses))
    else:
        meses_str = ",".join(str(m) for m in meses_de(",".join(str(x) for x in meses)))
    venda = PlanVenda(
        plan_id=plan.id,
        produto=produto.strip(),
        unidade=unidade.strip(),
        canle=canle,
        cantidade=cantidade,
        prezo=prezo,
        custo_unitario=custo_unitario,
        crece_cantidade_pct=crece_cantidade_pct,
        crece_prezo_pct=crece_prezo_pct,
        meses=meses_str,
    )
    plan.vendas_detalle.append(venda)
    session.commit()
    return venda


def propor_vendas_do_real(
    session: Session, actor: Usuario, plan: PlanEmpresa, ano: int
) -> int:
    """Crea vendas en detalle baseadas nas saídas de venda do ano real."""
    _plan(session, actor, plan.id)
    if plan.vendas_detalle:
        raise OperacionNonPermitidaError("O plan xa ten vendas en detalle")
    desde, ata = date(ano, 1, 1), date(ano, 12, 31)
    agrupadas: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {"cantidade": 0.0, "importe": 0.0, "meses": set()}
    )
    for sa, lote in (
        session.query(LoteSaida, Lote)
        .join(Lote, Lote.id == LoteSaida.lote_id)
        .filter(
            LoteSaida.horta_id == plan.horta_id,
            LoteSaida.baixa.is_(False),
            LoteSaida.tipo == "venda",
            LoteSaida.importe.is_not(None),
            LoteSaida.data_fin >= desde,
            LoteSaida.data_fin <= ata,
        )
    ):
        canle = sa.canle if sa.canle in CANLES else "explotacion"
        c = converter(sa.cantidade, sa.unidade, lote.unidade)
        cant = c if c is not None else sa.cantidade
        clave = (lote.produto, lote.unidade, canle)
        agrupadas[clave]["cantidade"] += cant
        agrupadas[clave]["importe"] += sa.importe or 0.0
        if sa.data_fin:
            agrupadas[clave]["meses"].add(sa.data_fin.month)

    creadas = 0
    for (produto, unidade, canle), datos in sorted(agrupadas.items(), key=lambda x: x[0]):
        cantidade = round(datos["cantidade"], 2)
        if cantidade <= 0:
            continue
        prezo = round(datos["importe"] / cantidade, 2)
        meses_lista = sorted(datos["meses"]) if datos["meses"] else list(range(1, 13))
        meses_str = ",".join(str(m) for m in meses_lista)
        venda = PlanVenda(
            plan_id=plan.id,
            produto=produto,
            unidade=unidade,
            canle=canle,
            cantidade=cantidade,
            prezo=prezo,
            custo_unitario=None,
            crece_cantidade_pct=0,
            crece_prezo_pct=0,
            meses=meses_str,
        )
        plan.vendas_detalle.append(venda)
        creadas += 1

    if creadas:
        session.commit()
    return creadas


def quitar(session: Session, actor: Usuario, plan: PlanEmpresa,
           elemento: (PlanInvestimento | PlanFinanciamento | PlanOferta
                      | PlanActividade | PlanObxectivo | PlanVenda)) -> None:
    _plan(session, actor, plan.id)
    if isinstance(elemento, PlanOferta):
        inv = session.get(PlanInvestimento, elemento.investimento_id)
        if inv is None or inv.plan_id != plan.id:
            raise OperacionNonPermitidaError("Ese elemento non é deste plan")
    elif getattr(elemento, "plan_id", None) != plan.id:
        raise OperacionNonPermitidaError("Ese elemento non é deste plan")
    session.delete(elemento)
    session.commit()


def dar_de_baixa_plan(session: Session, actor: Usuario, plan: PlanEmpresa) -> None:
    _plan(session, actor, plan.id)
    plan.baixa = True
    session.commit()


def listar_plans(session: Session, actor: Usuario, horta_id: int) -> list[PlanEmpresa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    return list(session.query(PlanEmpresa).filter_by(horta_id=horta_id, baixa=False)
                .order_by(PlanEmpresa.created_at.desc()))


# --- Cálculos

def xuros(fonte: PlanFinanciamento) -> list[float]:
    """Xuros de cada ano dun préstamo con cota constante (sistema francés)."""
    if fonte.tipo != "prestamo" or not fonte.anos:
        return []
    i, n, pendente = (fonte.xuro_pct or 0) / 100, fonte.anos, fonte.importe
    cota = pendente / n if i == 0 else pendente * i / (1 - (1 + i) ** -n)
    lista = []
    for _ in range(n):
        xuro = pendente * i
        lista.append(round(xuro, 2))
        pendente -= cota - xuro
    return lista


@dataclass(frozen=True)
class AnoConta:
    ano_n: int
    ano: int
    vendas: float  # A
    variables: float  # B
    fixos: float  # C
    amortizacions: float  # D
    marxe: float  # E = A − (B + C + D)
    financeiro: float  # F
    beneficio: float  # G = E + F
    fluxo: float  # G + D


@dataclass(frozen=True)
class Indicadores:
    investimento: float
    investimento_con_iva: float
    subvencionable: float  # sen IVE, ou con IVE se non é recuperable (art. 8.b)
    financiamento: float
    van: float
    tir: float | None
    payback: int | None


def custo(plan: PlanEmpresa, investimento: PlanInvestimento) -> float:
    """O que lle custa á empresa: o IVE só conta se non o recupera."""
    if plan.iva_recuperable:
        return investimento.importe_sen_iva
    return investimento.importe_sen_iva * (1 + investimento.iva_pct / 100)


def vendas_do_ano(venda: PlanVenda, ano_n: int) -> tuple[float, float]:
    """(importe, custo) do ano ano_n (1–5) co crecemento acumulado."""
    potencia = ano_n - 1
    cantidade = venda.cantidade * ((1 + (venda.crece_cantidade_pct or 0) / 100) ** potencia)
    prezo = venda.prezo * ((1 + (venda.crece_prezo_pct or 0) / 100) ** potencia)
    importe = round(cantidade * prezo, 2)
    custo = (
        round(cantidade * venda.custo_unitario, 2)
        if venda.custo_unitario is not None
        else 0.0
    )
    return importe, custo


def conta(plan: PlanEmpresa, factor_vendas: float = 1.0) -> list[AnoConta]:
    amortizacion = sum(custo(plan, i) / i.vida_util_anos
                       for i in plan.investimentos if i.vida_util_anos)
    xuros_ano: dict[int, float] = defaultdict(float)
    for fonte in plan.financiamento:
        for n, xuro in enumerate(xuros(fonte), start=1):
            xuros_ano[n] += xuro
    filas = []
    hai_detalle = bool(plan.vendas_detalle)
    hai_custo = hai_detalle and any(v.custo_unitario is not None for v in plan.vendas_detalle)
    for ano in sorted(plan.anos, key=lambda a: a.ano_n):
        if hai_detalle:
            cifras = [vendas_do_ano(v, ano.ano_n) for v in plan.vendas_detalle]
            vendas = round(sum(c[0] for c in cifras) * factor_vendas, 2)
            variables = (round(sum(c[1] for c in cifras), 2)
                         if hai_custo else ano.custos_variables)
        else:
            vendas = round(ano.vendas * factor_vendas, 2)
            variables = ano.custos_variables
        d = round(amortizacion, 2)
        e = round(vendas - (variables + ano.custos_fixos + d), 2)
        f = round(ano.ingresos_financeiros - xuros_ano.get(ano.ano_n, 0), 2)
        g = round(e + f, 2)
        filas.append(AnoConta(ano.ano_n, plan.ano_inicio + ano.ano_n - 1, vendas,
                              variables, ano.custos_fixos, d, e, f, g,
                              round(g + d, 2)))
    return filas


@dataclass(frozen=True)
class MarxeVenda:
    produto: str
    canle: str
    importe: float
    custo: float
    marxe: float
    marxe_pct: float | None


def marxes_por_venda(plan: PlanEmpresa) -> list[MarxeVenda]:
    """Marxes do ano 1 por venda en detalle, ordenadas de maior a menor marxe."""
    resultado = []
    for v in plan.vendas_detalle:
        importe, custo = vendas_do_ano(v, 1)
        marxe = round(importe - custo, 2)
        marxe_pct = round(100 * marxe / importe, 2) if importe else None
        resultado.append(
            MarxeVenda(
                produto=v.produto,
                canle=CANLES.get(v.canle, v.canle),
                importe=importe,
                custo=custo,
                marxe=marxe,
                marxe_pct=marxe_pct,
            )
        )
    return sorted(resultado, key=lambda m: m.marxe, reverse=True)


def _van(taxa: float, fluxos: list[float]) -> float:
    return sum(f / (1 + taxa) ** n for n, f in enumerate(fluxos))


def _tir(fluxos: list[float]) -> float | None:
    """TIR por bisección entre -99 % e ata un máximo de 10 000 %."""
    baixo, alto = -0.99, 1.0
    while alto < 100.0 and _van(baixo, fluxos) * _van(alto, fluxos) > 0:
        alto = min(alto * 2, 100.0)
    if _van(baixo, fluxos) * _van(alto, fluxos) < 0:
        for _ in range(100):
            medio = (baixo + alto) / 2
            if _van(baixo, fluxos) * _van(medio, fluxos) <= 0:
                alto = medio
            else:
                baixo = medio
        return round((baixo + alto) / 2, 4)
    return None


def indicadores(plan: PlanEmpresa, factor_vendas: float = 1.0) -> Indicadores:
    investimento = round(sum(i.importe_sen_iva for i in plan.investimentos), 2)
    con_iva = round(sum(i.importe_sen_iva * (1 + i.iva_pct / 100)
                        for i in plan.investimentos), 2)
    subvencionable = round(sum(custo(plan, i) for i in plan.investimentos), 2)
    fluxos = [-subvencionable, *(a.fluxo for a in conta(plan, factor_vendas=factor_vendas))]
    tir = _tir(fluxos) if subvencionable else None
    acumulado, payback = 0.0, None
    for n, fluxo in enumerate(fluxos):
        acumulado += fluxo
        if n and acumulado >= 0:
            payback = n
            break
    return Indicadores(investimento, con_iva, subvencionable,
                       round(sum(f.importe for f in plan.financiamento), 2),
                       round(_van(plan.taxa_desconto, fluxos), 2), tir, payback)


def _euros(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")


def anos_texto(anos: int | None) -> str:
    """«1 ano», «3 anos» ou «—»."""
    if anos is None:
        return "—"
    return f"{anos} ano" if anos == 1 else f"{anos} anos"


def pct(valor: float, decimais: int = 1) -> str:
    """Tanto por un como porcentaxe con coma decimal: 0,123 → «12,3 %»."""
    return f"{valor * 100:.{decimais}f} %".replace(".", ",")


@dataclass(frozen=True)
class MesTesouraria:
    mes: int
    cobros: float
    pagos: float
    saldo: float


def tesouraria(plan: PlanEmpresa) -> list[MesTesouraria]:
    """Tesouraría mes a mes do primeiro ano do plan."""
    filas_conta = conta(plan)
    if not filas_conta:
        return []
    ano1 = filas_conta[0]

    vendas_mes: dict[int, float] = {m: 0.0 for m in range(1, 13)}
    if plan.vendas_detalle:
        for v in plan.vendas_detalle:
            importe, _ = vendas_do_ano(v, 1)
            meses = meses_de(v.meses)
            if meses:
                parte = importe / len(meses)
                for m in meses:
                    vendas_mes[m] += parte
    else:
        for m in range(1, 13):
            vendas_mes[m] = ano1.vendas / 12

    fin_mes1 = sum(f.importe for f in plan.financiamento if f.tipo != "subvencion")
    subvencions_mes12 = sum(f.importe for f in plan.financiamento if f.tipo == "subvencion")

    investimento_con_iva = sum(
        i.importe_sen_iva * (1 + i.iva_pct / 100) for i in plan.investimentos
    )

    total_vendas_ano1 = sum(vendas_mes.values())
    variables_mes: dict[int, float] = {}
    for m in range(1, 13):
        if total_vendas_ano1 > 0:
            variables_mes[m] = ano1.variables * (vendas_mes[m] / total_vendas_ano1)
        else:
            variables_mes[m] = ano1.variables / 12

    fixos_mes = ano1.fixos / 12

    total_cota_anual = 0.0
    for f in plan.financiamento:
        if f.tipo == "prestamo" and f.anos:
            i, n, pendente = (f.xuro_pct or 0) / 100, f.anos, f.importe
            cota = pendente / n if i == 0 else pendente * i / (1 - (1 + i) ** -n)
            total_cota_anual += cota
    cota_mes = total_cota_anual / 12

    saldo_acumulado = 0.0
    meses_tesouraria: list[MesTesouraria] = []
    for m in range(1, 13):
        cobros_m = vendas_mes[m]
        if m == 1:
            cobros_m += fin_mes1
        if m == 12:
            cobros_m += subvencions_mes12

        pagos_m = variables_mes[m] + fixos_mes + cota_mes
        if m == 1:
            pagos_m += investimento_con_iva

        cobros_redondeado = round(cobros_m, 2)
        pagos_redondeado = round(pagos_m, 2)
        saldo_acumulado = round(saldo_acumulado + cobros_redondeado - pagos_redondeado, 2)

        meses_tesouraria.append(
            MesTesouraria(
                mes=m,
                cobros=cobros_redondeado,
                pagos=pagos_redondeado,
                saldo=saldo_acumulado,
            )
        )
    return meses_tesouraria


def avisos_ofertas(investimento: PlanInvestimento) -> list[str]:
    """Art. 20: tres ofertas de provedores distintos e escoller a máis económica."""
    nome, ofertas = f"«{investimento.concepto}»", investimento.ofertas
    avisos = []
    if len(ofertas) < 3 and not investimento.motivo_sen_ofertas:
        avisos.append(f"{nome}: hai {len(ofertas)} ofertas e piden tres de provedores "
                      "distintos, ou explicar por que non hai (art. 20.1)")
    elixida = next((o for o in ofertas if o.elixida), None)
    if ofertas and elixida is None:
        avisos.append(f"{nome}: marca a oferta elixida")
    if elixida is not None:
        if elixida.importe_sen_iva > min(o.importe_sen_iva for o in ofertas) and not \
                elixida.xustificacion:
            avisos.append(f"{nome}: a oferta elixida non é a máis económica; xustifícao "
                          "(art. 20.4)")
        if abs(elixida.importe_sen_iva - investimento.importe_sen_iva) > 0.01:
            avisos.append(f"{nome}: o importe ({_euros(investimento.importe_sen_iva)}) non é o "
                          f"da oferta elixida ({_euros(elixida.importe_sen_iva)})")
    return avisos


def avisos_plan(plan: PlanEmpresa) -> list[str]:
    avisos = [a for i in plan.investimentos for a in avisos_ofertas(i)]
    ind = indicadores(plan)
    if ind.investimento and abs(ind.financiamento - ind.investimento_con_iva) > 1:
        avisos.append(f"O financiamento ({_euros(ind.financiamento)}) non cadra co "
                      f"investimento con IVE ({_euros(ind.investimento_con_iva)})")
    tipoloxia = TIPOLOXIAS.get(plan.tipoloxia or "")
    if tipoloxia and tipoloxia.max_investimento and \
            ind.subvencionable > tipoloxia.max_investimento:
        avisos.append(f"O investimento subvencionable ({_euros(ind.subvencionable)}) pasa do "
                      f"máximo de {_euros(tipoloxia.max_investimento)} ({tipoloxia.texto})")
    if (plan.traballadores or 0) >= 50:
        avisos.append("Con 50 persoas ou máis non é pequena empresa (art. 4.2.c)")
    if (plan.facturacion or 0) > 10_000_000 and (plan.balance or 0) > 10_000_000:
        avisos.append("Coa facturación e o balance por riba de 10 millóns non é pequena "
                      "empresa (art. 4.2.c)")
    meses_tes = tesouraria(plan)
    negativos = [t for t in meses_tes if t.saldo < 0]
    if negativos:
        mes_min = min(negativos, key=lambda t: t.saldo)
        avisos.append(
            f"No mes {mes_min.mes} a caixa queda en {_euros(mes_min.saldo)}: "
            f"precisas polo menos {_euros(-mes_min.saldo)} máis para empezar"
        )
    return avisos


def faltas_plan(session: Session, actor: Usuario, plan: PlanEmpresa) -> list[str]:
    """O que lle falta ao plan para presentalo. Nunca bloquea."""
    _plan(session, actor, plan.id)
    titular = titular_da_horta(session, plan.horta_id)
    faltas = []
    if titular is None or not titular.nif:
        faltas.append("o NIF do titular (en Persoas)")
    if not plan.tipoloxia:
        faltas.append("a tipoloxía do proxecto")
    if not plan.cnae:
        faltas.append("o CNAE da actividade principal")
    for campo, texto in (("descricion", "1. a descrición, os obxectivos e a finalidade"),
                         ("proceso", "2. o proceso e os medios humanos e materiais"),
                         ("formacion", "4. a formación do promotor"),
                         ("situacion_partida", "a situación de partida (memoria)"),
                         ("metodoloxia", "a metodoloxía de traballo (memoria)")):
        if not (getattr(plan, campo) or "").strip():
            faltas.append(texto)
    if not plan.empresa_nova and None in (plan.traballadores, plan.facturacion, plan.balance):
        faltas.append("os traballadores, a facturación e o balance da empresa")
    if not (plan.uta_mantidas or plan.uta_creadas):
        faltas.append("3. o emprego en UTA (mantido ou creado)")
    if not any(a.vendas for a in plan.anos):
        faltas.append("6. as vendas da conta a 5 anos")
    if plan.tipoloxia != "bono" and not plan.investimentos:
        faltas.append("o investimento (Anexo V)")
    if not plan.financiamento:
        faltas.append("5. o plan de financiamento")
    if plan.investimentos and not (plan.ofertas_autenticas and plan.sen_vinculo_promotor
                                   and plan.sen_vinculo_entre_provedores):
        faltas.append("as declaracións do Anexo VI-B")
    for investimento in plan.investimentos:
        for oferta in investimento.ofertas:
            provedor = session.get(Persoa, oferta.provedor_id)
            if provedor is not None and not provedor.nif:
                faltas.append(f"o NIF de {nome_completo(provedor)} (en Contactos)")
    return list(dict.fromkeys(faltas))


def faltas_memoria(plan: PlanEmpresa) -> list[str]:
    """Os títulos dos apartados da memoria sen encher. Só informa: non bloquea."""
    faltas = []
    for titulo, campos in SECCIONS_MEMORIA.items():
        if all(not (getattr(plan, c, None) or "").strip() for c in campos):
            faltas.append(titulo)
    if not plan.actividades:
        faltas.append("Calendario de 12 meses")
    if not plan.obxectivos:
        faltas.append("Obxectivos e indicadores")
    return faltas


# --- Escenarios, semáforo, revisión e comparación RECAN


@dataclass(frozen=True)
class Escenario:
    nome: str
    factor: float
    vendas_ano1: float
    beneficio_ano1: float
    van: float
    tir: float | None
    payback: int | None


def escenarios(plan: PlanEmpresa) -> list[Escenario]:
    pct = (plan.escenario_pct if plan.escenario_pct is not None else 20.0) / 100.0
    casos = [
        ("Pesimista", round(1.0 - pct, 4)),
        ("Normal", 1.0),
        ("Optimista", round(1.0 + pct, 4)),
    ]
    resultado = []
    for nome, factor in casos:
        filas = conta(plan, factor_vendas=factor)
        ano1 = filas[0]
        ind = indicadores(plan, factor_vendas=factor)
        resultado.append(
            Escenario(
                nome=nome,
                factor=factor,
                vendas_ano1=ano1.vendas,
                beneficio_ano1=ano1.beneficio,
                van=ind.van,
                tir=ind.tir,
                payback=ind.payback,
            )
        )
    return resultado


@dataclass(frozen=True)
class Sinal:
    nome: str
    cor: str  # «verde», «amarelo» ou «vermello»
    texto: str


def semaforo(plan: PlanEmpresa) -> list[Sinal]:
    ind = indicadores(plan)

    # 1. VAN
    if ind.van > 0:
        sinal_van = Sinal("VAN", "verde", "O proxecto recupera o investimento e a taxa pedida")
    else:
        sinal_van = Sinal("VAN", "vermello",
                          "O proxecto non recupera o investimento e a taxa pedida")

    # 2. TIR
    # Os límites de 3 e 5 anos no pay-back e os 2 puntos (+0,02) de TIR sobre a taxa
    # de desconto son orientativos.
    taxa = plan.taxa_desconto or 0.0
    if ind.tir is not None and ind.tir >= taxa + 0.02:
        sinal_tir = Sinal("TIR", "verde",
                          f"A TIR ({pct(ind.tir)}) supera con folgura a taxa pedida ({pct(taxa)})")
    elif ind.tir is not None and ind.tir >= taxa:
        sinal_tir = Sinal("TIR", "amarelo",
                          f"A TIR ({pct(ind.tir)}) cobre a taxa pedida ({pct(taxa)}), "
                          "con pouca marxe")
    else:
        if ind.tir is not None:
            msg_tir = f"A TIR ({pct(ind.tir)}) non acada a taxa pedida ({pct(taxa)})"
        else:
            msg_tir = "A TIR non se pode calcular"
        sinal_tir = Sinal("TIR", "vermello", msg_tir)

    # 3. Pay-back
    if ind.payback is not None and ind.payback <= 3:
        sinal_payback = Sinal("Pay-back", "verde",
                              f"O investimento recupérase no ano {ind.payback}")
    elif ind.payback is not None and ind.payback in (4, 5):
        sinal_payback = Sinal("Pay-back", "amarelo",
                              f"O investimento tarda {ind.payback} anos en recuperarse")
    else:
        sinal_payback = Sinal("Pay-back", "vermello",
                              "O investimento non se recupera nos 5 anos")

    # 4. Caixa do ano 1
    meses_tes = tesouraria(plan)
    negativos = [t for t in meses_tes if t.saldo < 0]
    if not negativos:
        sinal_caixa = Sinal("Caixa do ano 1", "verde",
                            "A tesouraría mantense en positivo durante todo o ano")
    else:
        mes_min = min(negativos, key=lambda t: t.saldo)
        sinal_caixa = Sinal(
            "Caixa do ano 1",
            "vermello",
            f"No mes {mes_min.mes} a caixa queda en {_euros(mes_min.saldo)}: "
            f"precisas polo menos {_euros(-mes_min.saldo)} máis para empezar",
        )

    # 5. Escenario pesimista
    esc_pesimista = next(e for e in escenarios(plan) if e.nome == "Pesimista")
    pct_val = plan.escenario_pct if plan.escenario_pct is not None else 20.0
    pct_str = (
        f"{int(pct_val)}"
        if pct_val == int(pct_val)
        else f"{pct_val:.1f}".replace(".", ",")
    )
    if esc_pesimista.van > 0:
        sinal_pesimista = Sinal(
            "Escenario pesimista",
            "verde",
            f"Aguanta unha baixada das vendas do {pct_str} %",
        )
    else:
        sinal_pesimista = Sinal(
            "Escenario pesimista",
            "amarelo",
            f"Non aguanta unha baixada das vendas do {pct_str} % (VAN negativa)",
        )

    if not ind.subvencionable:
        # Sen investimento, a TIR e o pay-back non din nada
        return [sinal_van, sinal_caixa, sinal_pesimista]
    return [sinal_van, sinal_tir, sinal_payback, sinal_caixa, sinal_pesimista]


@dataclass(frozen=True)
class Comparacion:
    indicador: str
    plan: float | None
    media: float | None
    unidade: str
    nota: str | None = None


def comparar_recan(
    session: Session, actor: Usuario, plan: PlanEmpresa
) -> list[Comparacion]:
    _plan(session, actor, plan.id)
    if not plan.ote_recan:
        return []
    datos_all = _datos_recan().get("orientacions", {})
    if plan.ote_recan not in datos_all:
        return []
    datos_ote = datos_all[plan.ote_recan]
    mostra = int(datos_ote.get("mostra", 0))

    # Ano 1 de conta
    filas_conta = conta(plan)
    ano1 = filas_conta[0]
    a = ano1.vendas
    b = ano1.variables
    c = ano1.fixos
    d = ano1.amortizacions
    g = ano1.beneficio

    xuros_ano: dict[int, float] = defaultdict(float)
    for fonte in plan.financiamento:
        for n, xuro in enumerate(xuros(fonte), start=1):
            xuros_ano[n] += xuro
    xuros_ano1 = xuros_ano.get(1, 0.0)

    # Superficie (ha) e UTA
    parcelas = session.query(Parcela).filter_by(
        horta_id=plan.horta_id, data_baixa=None
    ).all()
    sup_total = sum(p.superficie or 0.0 for p in parcelas)
    superficie: float | None = sup_total if sup_total > 0 else None

    total_uta = (plan.uta_mantidas or 0.0) + (plan.uta_creadas or 0.0)
    uta: float | None = total_uta if total_uta > 0 else None

    # 1. Produción por hectárea (€/ha): A / superficie fronte a SE131 / SE025
    plan_prod_ha = round(a / superficie) if superficie else None
    se025 = datos_ote.get("SE025")
    recan_prod_ha = round(datos_ote["SE131"] / se025) if se025 and se025 > 0 else None
    nota1 = (
        f"Media con poucas explotacións na mostra ({mostra})"
        if mostra < 15
        else None
    )

    # 2. Produción por UTA (€/UTA): A / UTA fronte a SE131 / SE010
    plan_prod_uta = round(a / uta) if uta else None
    se010 = datos_ote.get("SE010")
    recan_prod_uta = round(datos_ote["SE131"] / se010) if se010 and se010 > 0 else None

    # 3. Custos sobre a produción (%): (B + C + D + xuros) / A * 100 fronte a SE270 / SE131 * 100
    plan_custos_pct = (
        round((b + c + d + xuros_ano1) / a * 100, 1) if a > 0 else None
    )
    se131 = datos_ote.get("SE131")
    recan_custos_pct = (
        round(datos_ote["SE270"] / se131 * 100, 1) if se131 and se131 > 0 else None
    )

    # 4. Resultado por UTA (€/UTA): G / UTA fronte a SE420 / SE010
    plan_res_uta = round(g / uta) if uta else None
    recan_res_uta = round(datos_ote["SE420"] / se010) if se010 and se010 > 0 else None
    nota4 = "A RECAN inclúe as subvencións correntes; o plan non"

    return [
        Comparacion("Produción por hectárea", plan_prod_ha, recan_prod_ha, "€/ha", nota1),
        Comparacion("Produción por UTA", plan_prod_uta, recan_prod_uta, "€/UTA", None),
        Comparacion("Custos sobre a produción", plan_custos_pct, recan_custos_pct, "%", None),
        Comparacion("Resultado por UTA", plan_res_uta, recan_res_uta, "€/UTA", nota4),
    ]


@dataclass(frozen=True)
class Revision:
    afirmable: list[str]
    falta_probar: list[str]


def revision(session: Session, actor: Usuario, plan: PlanEmpresa) -> Revision:
    _plan(session, actor, plan.id)
    afirmable: list[str] = []
    falta_probar: list[str] = []

    # Vendas
    ano_ref = ano_de_referencia(session, actor, plan.horta_id)
    real_vendas, _, _ = base_do_real(resumo_ano(session, actor, plan.horta_id, ano_ref))
    filas = conta(plan)
    a_ano1 = filas[0].vendas if filas else 0.0

    if real_vendas > 0 and a_ano1 <= round(real_vendas * 1.10, 2):
        afirmable.append(
            f"As vendas do ano 1 ({_euros(a_ano1)}) están ao nivel das reais de "
            f"{ano_ref} ({_euros(real_vendas)})"
        )
    elif real_vendas > 0:
        x_val = round(((a_ano1 - real_vendas) / real_vendas) * 100, 1)
        x_str = f"{int(x_val)}" if x_val.is_integer() else f"{x_val:.1f}".replace(".", ",")
        falta_probar.append(
            f"As vendas do ano 1 ({_euros(a_ano1)}) son {x_str} % máis cás reais de {ano_ref}: "
            "achega contratos, cartas de interese ou prezos de mercado"
        )
    else:
        falta_probar.append(
            f"As vendas do ano 1 ({_euros(a_ano1)}) non teñen vendas reais detrás: "
            "achega contratos, cartas de interese ou prezos de mercado"
        )

    # Ofertas
    faltan_ofertas = [
        i.concepto
        for i in plan.investimentos
        if len(i.ofertas) < 3 and not (i.motivo_sen_ofertas or "").strip()
    ]
    if not faltan_ofertas:
        afirmable.append("Todos os gastos teñen tres ofertas ou o motivo")
    else:
        falta_probar.append(f"Faltan ofertas en: {', '.join(faltan_ofertas)}")

    # Financiamento
    ind = indicadores(plan)
    if abs(ind.financiamento - ind.investimento_con_iva) <= 1:
        afirmable.append(
            f"O financiamento ({_euros(ind.financiamento)}) cadra co investimento con IVE "
            f"({_euros(ind.investimento_con_iva)})"
        )
    else:
        falta_probar.append(
            f"O financiamento ({_euros(ind.financiamento)}) non cadra co investimento con IVE "
            f"({_euros(ind.investimento_con_iva)})"
        )

    # Memoria
    faltas_mem = faltas_memoria(plan)
    if faltas_mem:
        falta_probar.append(f"Completar a memoria: {', '.join(faltas_mem)}")

    # Media galega
    if plan.ote_recan:
        comps = comparar_recan(session, actor, plan)
        comp_uta = next((c for c in comps if c.indicador == "Produción por UTA"), None)
        if (
            comp_uta
            and comp_uta.plan is not None
            and comp_uta.media is not None
            and comp_uta.media > 0
        ):
            if comp_uta.plan > 2 * comp_uta.media:
                ratio = comp_uta.plan / comp_uta.media
                n_val = round(ratio, 1)
                n_str = (
                    f"{int(n_val)}"
                    if n_val.is_integer()
                    else f"{n_val:.1f}".replace(".", ",")
                )
                falta_probar.append(
                    f"A produción por UTA prevista é {n_str} veces a media galega da RECAN: "
                    "explica por que"
                )

    return Revision(afirmable=afirmable, falta_probar=falta_probar)


@dataclass(frozen=True)
class Documento:
    letra: str  # art. 18.1
    texto: str
    da_app: bool  # sae da app ou hai que achegalo


def documentos_plan(session: Session, actor: Usuario, plan: PlanEmpresa) -> list[Documento]:
    """A documentación complementaria do art. 18.1 que lle toca a este plan."""
    _plan(session, actor, plan.id)
    horta = session.get(Horta, plan.horta_id)
    codigo = (horta.codigo_rega or horta.codigo_reaga) if horta else None
    partidas = {i.partida for i in plan.investimentos}
    docs = [
        Documento("a", "Acreditación da persoa solicitante e, se é o caso, da representación",
                  False),
        Documento("b", "Declaración censual (modelo 036 ou 037) ou compromiso de comunicar o "
                       "inicio da actividade", False),
    ]
    if not plan.empresa_nova:
        docs.append(Documento("c", "Contas depositadas e memoria do último exercicio (pequena "
                                   "empresa), e das empresas vinculadas se as hai", False))
    docs += [
        Documento("d", "Informe do cadro de persoal medio dos últimos 12 meses (Seguridade "
                       "Social)", False),
        Documento("e", "Vida laboral das contas de cotización dos últimos 12 meses", False),
        Documento("f", "Anexo III: resumo do proxecto – plan de empresa", True),
        Documento("g", "Anexo V: orzamento de gastos por partidas", True),
    ]
    if plan.investimentos:
        docs.append(Documento("h", "Anexos VI-A e VI-B, con tres orzamentos ou facturas pro "
                                   "forma de cada gasto", True))
    if not plan.iva_recuperable:
        docs.append(Documento("i", "Acreditación de que o IVE non é recuperable", False))
    if (plan.tipoloxia or "").startswith("primaria"):
        docs.append(Documento("j", f"Código de explotación agraria: {codigo}" if codigo else
                              "Código de explotación agraria (non está na ficha da "
                              "explotación)", bool(codigo)))
    docs.append(Documento("k", "Plano do SIXPAC coas coordenadas (folla «Localización»)",
                          True))
    if not plan.empresa_nova:
        docs.append(Documento("l", "Licenza de actividade ou comunicación previa", False))
    if "2" in partidas:
        docs.append(Documento("m", "Anteproxecto ou memoria valorada asinada por técnico "
                                   "(hai obra civil)", False))
    if "3" in partidas:
        docs.append(Documento("n", "Declaración de que a maquinaria non existía ou mellora a "
                                   "capacidade máis dun 25 %", False))
    docs.append(Documento("o", "Certificado dos prazos de pagamento a provedores (Lei 3/2004), "
                               "se é o caso", False))
    return docs


# --- Seguimento e métricas

@dataclass(frozen=True)
class Seguimento:
    ano: int
    previsto_vendas: float
    real_vendas: float
    previsto_marxe: float
    real_marxe: float


def seguimento(session: Session, actor: Usuario, plan: PlanEmpresa,
               hoxe: date | None = None) -> list[Seguimento]:
    """Os anos do plan xa empezados: o previsto e o real (vendas e marxe sen amortizacións)."""
    _plan(session, actor, plan.id)
    hoxe = hoxe or date.today()
    filas = []
    for a in conta(plan):
        if a.ano > hoxe.year:
            break
        vendas, variables, fixos = base_do_real(resumo_ano(session, actor, plan.horta_id,
                                                           a.ano))
        filas.append(Seguimento(a.ano, a.vendas, vendas, round(a.marxe + a.amortizacions, 2),
                                round(vendas - variables - fixos, 2)))
    return filas


@dataclass
class Metricas:
    rendemento: dict[str, float]  # cultivo → kg/ha
    prezo_medio: dict[str, float]  # «produto · canle» → €/unidade do lote
    refugo_pct: dict[str, float]  # produto → %
    horas: float
    uta: float
    punto_morto: float | None  # vendas necesarias para cubrir custos


def metricas(session: Session, actor: Usuario, horta_id: int, ano: int) -> Metricas:
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    desde, ata = date(ano, 1, 1), date(ano, 12, 31)
    kg: dict[str, float] = defaultdict(float)
    ha: dict[str, float] = defaultdict(float)
    vistos: set[int] = set()
    for co, cu in (session.query(Colleita, Cultivo).join(Cultivo, Cultivo.id ==
                                                          Colleita.cultivo_id)
                   .join(Parcela, Parcela.id == Cultivo.parcela_id)
                   .filter(Parcela.horta_id == horta_id, Colleita.baixa.is_(False),
                           Colleita.data >= desde, Colleita.data <= ata)):
        kg[cu.especie] += converter(co.cantidade, co.unidade, "kg") or 0
        if cu.id not in vistos and cu.superficie_ha:
            vistos.add(cu.id)
            ha[cu.especie] += cu.superficie_ha
    rendemento = {c: round(kg[c] / ha[c], 1) for c in kg if ha.get(c)}
    importe: dict[str, float] = defaultdict(float)
    canto: dict[str, float] = defaultdict(float)
    for sa, lote in (session.query(LoteSaida, Lote).join(Lote, Lote.id == LoteSaida.lote_id)
                     .filter(LoteSaida.horta_id == horta_id, LoteSaida.baixa.is_(False),
                             LoteSaida.tipo == "venda", LoteSaida.importe.is_not(None),
                             LoteSaida.data_fin >= desde, LoteSaida.data_fin <= ata)):
        clave = f"{lote.produto} ({lote.unidade}) · {CANLES.get(sa.canle or '', '')}"
        importe[clave] += sa.importe or 0
        canto[clave] += converter(sa.cantidade, sa.unidade, lote.unidade) or 0
    prezo = {c: round(importe[c] / canto[c], 2) for c in importe if canto[c]}
    clasificado: dict[str, float] = defaultdict(float)
    refugo: dict[str, float] = defaultdict(float)
    for cl, lote in (session.query(Clasificacion, Lote).join(Lote, Lote.id ==
                                                              Clasificacion.lote_id)
                     .filter(Clasificacion.horta_id == horta_id, Clasificacion.baixa.is_(False),
                             Clasificacion.data >= desde, Clasificacion.data <= ata)):
        clasificado[lote.produto] += sum(c.cantidade for c in cl.clases) + (cl.refugo or 0)
        refugo[lote.produto] += cl.refugo or 0
    refugo_pct = {p: round(100 * refugo[p] / clasificado[p], 1)
                  for p in clasificado if clasificado[p]}
    horas = round(sum(h for _, _, h in horas_dos_traballos(session, horta_id, desde, ata)),
                  1)
    vendas, variables, fixos = base_do_real(resumo_ano(session, actor, horta_id, ano))
    marxe_unitaria = 1 - variables / vendas if vendas else 0
    punto_morto = round(fixos / marxe_unitaria, 2) if marxe_unitaria > 0 else None
    return Metricas(rendemento, prezo, refugo_pct, horas, round(horas / HORAS_UTA, 2),
                    punto_morto)


def _identificacion(persoa: Persoa | None) -> list[tuple[str, Any]]:
    nif = ((persoa.nif if persoa else None) or "").upper()
    tipo = "NIE" if nif and nif[0] in "XYZ" else "NIF"
    return [("   Identificación", f"{tipo} {nif}" if nif else ""),
            ("   País emisor", (persoa.pais or "España") if persoa else ""),
            ("   Nome ou razón social", persoa.nome if persoa else ""),
            ("   Apelidos", (persoa.apelidos or "") if persoa else "")]


def _financiamento(plan: PlanEmpresa, ind: Indicadores) -> list[tuple[str, Any]]:
    """5. Importe e porcentaxe de cada fonte sobre o total."""
    total = ind.financiamento
    filas: list[tuple[str, Any]] = []
    for tipo, texto in FONTES.items():
        importe = round(sum(f.importe for f in plan.financiamento if f.tipo == tipo), 2)
        porcentaxe = f" ({pct(importe / total)})" if total else ""
        filas.append((f"5. {texto} (€)", f"{importe:.2f}{porcentaxe}"))
    filas.append(("5. Total investimentos con IVE (€)", ind.investimento_con_iva))
    return filas


def _partidas(plan: PlanEmpresa) -> list[tuple[Any, ...]]:
    """Cada partida cos seus conceptos e o seu total, e o total das partidas."""
    filas: list[tuple[Any, ...]] = []
    for clave, nome in PARTIDAS.items():
        conceptos = [i for i in plan.investimentos if i.partida == clave]
        for i in conceptos:
            filas.append((nome, i.concepto, i.importe_sen_iva, i.iva_pct,
                          round(i.importe_sen_iva * (1 + i.iva_pct / 100), 2)))
        filas.append((f"TOTAL {nome}", "", round(sum(i.importe_sen_iva for i in conceptos), 2),
                      "", round(sum(i.importe_sen_iva * (1 + i.iva_pct / 100)
                                    for i in conceptos), 2)))
    ind = indicadores(plan)
    filas.append(("TOTAL PARTIDAS", "", ind.investimento, "", ind.investimento_con_iva))
    return filas


def _sixpac(parcela: Parcela) -> str:
    """Provincia:concello:agregado:zona:polígono:parcela:recinto."""
    partes = (parcela.sigpac_provincia, parcela.sigpac_concello, parcela.sigpac_agregado,
              parcela.sigpac_zona, parcela.sigpac_poligono, parcela.sigpac_parcela,
              parcela.sigpac_subparcela)
    if not (parcela.sigpac_poligono and parcela.sigpac_parcela):
        return ""
    return ":".join(p or "0" for p in partes)


def xerar_anexos(session: Session, actor: Usuario, plan_id: int) -> bytes:
    """Excel cos Anexos III, V, VI-A e VI-B, a documentación do art. 18 e a localización."""
    from io import BytesIO

    from openpyxl import Workbook

    from horta.services.caderno import folla

    plan = _plan(session, actor, plan_id)
    cab = f"{plan.titulo} · Ano 1: {plan.ano_inicio}"
    ind = indicadores(plan)
    titular = titular_da_horta(session, plan.horta_id)
    representante = next(iter(con_papel(session, plan.horta_id, "representante")), None)
    tipoloxia = TIPOLOXIAS.get(plan.tipoloxia or "")
    wb = Workbook()
    wb.remove(wb.active)
    folla(wb, "Anexo III", "Resumo do proxecto – plan de empresa (AGADER, Anexo III)", cab,
          ("Apartado", "Valor"),
          [("Persoa solicitante", ""), *_identificacion(titular),
           ("E na súa representación", ""), *_identificacion(representante),
           ("Número de expediente", plan.expediente or ""),
           ("Anualidade", plan.anualidade or ""), ("Submedida", plan.submedida or ""),
           ("Grupo de desenvolvemento rural", plan.gdr or ""),
           ("Título do proxecto", plan.titulo),
           ("Tipoloxía", f"{tipoloxia.texto} ({tipoloxia.axuda})" if tipoloxia else ""),
           ("Tipo de empresa", "Nova" if plan.empresa_nova else "Existente"),
           ("Actividade principal (CNAE)", plan.cnae or ""),
           ("Participa ou está participada nun 25 % ou máis", "Si" if plan.participada
            else "Non"),
           ("Nº de traballadores", plan.traballadores if plan.traballadores is not None
            else ""),
           ("Facturación (€)", plan.facturacion if plan.facturacion is not None else ""),
           ("Balance (€)", plan.balance if plan.balance is not None else ""),
           ("1. Descrición, obxectivos e finalidade", plan.descricion or ""),
           ("2. Proceso e medios humanos e materiais", plan.proceso or ""),
           ("3. Emprego (UTA) mantido", plan.uta_mantidas),
           ("3. Emprego (UTA) creado", plan.uta_creadas),
           ("   creado: mulleres", plan.uta_mulleres), ("   creado: persoas mozas",
                                                       plan.uta_mozas),
           ("   creado: persoas maiores", plan.uta_maiores),
           ("   creado: persoas con discapacidade", plan.uta_discapacidade),
           ("   creado: outros", plan.uta_outros),
           ("4. Formación do promotor", plan.formacion or ""),
           *_financiamento(plan, ind),
           ("VAN (€)", ind.van), ("TIR", f"{pct(ind.tir, 2)}" if ind.tir is not None else "—"),
           ("Pay-back (anos)", ind.payback or "—"),
           ("Memoria: situación de partida", plan.situacion_partida or ""),
           ("Memoria: metodoloxía de traballo", plan.metodoloxia or ""),
           ("Memoria: mercado e clientes", plan.mercado or "")])
    filas = conta(plan)
    folla(wb, "Conta 5 anos", "6. Previsión da conta de explotación (Anexo III)", cab,
          ("Concepto", *(f"Ano {a.ano_n} ({a.ano})" for a in filas)),
          [("A) Vendas", *(a.vendas for a in filas)),
           ("B) Custos variables", *(a.variables for a in filas)),
           ("C) Custos fixos", *(a.fixos for a in filas)),
           ("D) Amortizacións", *(a.amortizacions for a in filas)),
           ("E) Marxe de explotación = A−(B+C+D)", *(a.marxe for a in filas)),
           ("F) Ingresos − custos financeiros", *(a.financeiro for a in filas)),
           ("G) Beneficio antes de imposto = E+F", *(a.beneficio for a in filas))])
    folla(wb, "Anexo V", "Orzamento de gastos desagregados por partidas (AGADER, Anexo V)",
          cab, ("Partida", "Concepto", "Importe sen IVE (€)", "IVE (%)",
                "Importe con IVE (€)"), _partidas(plan))
    provedores = {p.id: p for p in session.query(Persoa).filter_by(horta_id=plan.horta_id)}
    folla(wb, "Anexo VI-A", "Relación de ofertas solicitadas e elixidas (AGADER, Anexo VI-A)",
          cab, ("Concepto", "Provedor", "NIF", "Importe sen IVE (€)", "Elixida",
                "Criterio de elección", "Xustificación de non escoller a máis económica"),
          [(i.concepto, nome_completo(provedores.get(o.provedor_id)),
            getattr(provedores.get(o.provedor_id), "nif", "") or "", o.importe_sen_iva,
            "Si" if o.elixida else "", o.criterio or "", o.xustificacion or "")
           for i in sorted(plan.investimentos, key=lambda i: i.partida) for o in i.ofertas])
    tres = all(len(i.ofertas) >= 3 for i in plan.investimentos)
    folla(wb, "Anexo VI-B", "Declaración sobre as ofertas solicitadas e elixidas (Anexo VI-B)",
          cab, ("Declaración", "Si/Non"),
          [(texto, "Si" if valor else "Non") for texto, valor in (
              ("Que se solicitaron polo menos tres ofertas a distintos provedores", tres),
              ("Que todas as ofertas presentadas a través de facturas pro forma son "
               "auténticas", plan.ofertas_autenticas),
              ("Que o promotor do proxecto carece de vinculación cos provedores",
               plan.sen_vinculo_promotor),
              ("Que as ofertas de cada gasto non proceden de empresas vinculadas entre elas",
               plan.sen_vinculo_entre_provedores))])
    folla(wb, "Documentación", "Documentación complementaria (art. 18.1)", cab,
          ("Letra", "Documento", "Quen"),
          [(d.letra, d.texto, "Sae da app" if d.da_app else "Achegas ti")
           for d in documentos_plan(session, actor, plan)])
    folla(wb, "Localización", "Localización da operación: parcelas e recintos SIXPAC", cab,
          ("Parcela", "Referencia SIXPAC", "Superficie (ha)", "Latitude", "Lonxitude"),
          [(p.nome, _sixpac(p), p.superficie or "", p.lat or "", p.lon or "")
           for p in session.query(Parcela).filter_by(horta_id=plan.horta_id,
                                                     data_baixa=None).order_by(Parcela.nome)])
    saida = BytesIO()
    wb.save(saida)
    return saida.getvalue()


def xerar_memoria(session: Session, actor: Usuario, plan_id: int) -> bytes:
    """Excel coa memoria complementaria (art. 18.1.p da convocatoria MR701L)."""
    from io import BytesIO

    from openpyxl import Workbook

    from horta.services.caderno import folla

    plan = _plan(session, actor, plan_id)
    cab = f"{plan.titulo} · Ano 1: {plan.ano_inicio}"
    tipoloxia = TIPOLOXIAS.get(plan.tipoloxia or "")
    texto_tipo = f"{tipoloxia.texto} ({tipoloxia.axuda})" if tipoloxia else "—"

    def _val(t: str | None) -> str:
        return (t or "").strip() or "—"

    wb = Workbook()
    wb.remove(wb.active)

    # 1. Proxecto
    filas_proxecto = [
        ("Título", _val(plan.titulo)),
        ("Tipoloxía", texto_tipo),
        ("1. Descrición", _val(plan.descricion)),
        ("2. Proceso", _val(plan.proceso)),
        ("4. Formación", _val(plan.formacion)),
        (ETIQUETAS_MEMORIA["situacion_partida"].capitalize(), _val(plan.situacion_partida)),
        (ETIQUETAS_MEMORIA["metodoloxia"].capitalize(), _val(plan.metodoloxia)),
        (ETIQUETAS_MEMORIA["organizacion"].capitalize(), _val(plan.organizacion)),
    ]
    folla(wb, "Proxecto", "Proxecto e organización", cab, ("Apartado", "Texto"), filas_proxecto)

    # 2. DAFO
    filas_dafo: list[tuple[str, str]] = []
    for campo in ("dafo_debilidades", "dafo_ameazas", "dafo_fortalezas", "dafo_oportunidades"):
        tipo = ETIQUETAS_MEMORIA[campo].capitalize()
        pts = puntos(getattr(plan, campo, None))
        if pts:
            for p in pts:
                filas_dafo.append((tipo, p))
        else:
            filas_dafo.append((tipo, "—"))
    folla(wb, "DAFO", "Análise DAFO", cab, ("Tipo", "Punto"), filas_dafo)

    # 3. Mercado
    filas_mercado = [
        (ETIQUETAS_MEMORIA[c].capitalize(), _val(getattr(plan, c, None)))
        for c in SECCIONS_MEMORIA["Mercado"]
    ]
    folla(wb, "Mercado", "Mercado, clientela e competencia", cab, ("Apartado", "Texto"),
          filas_mercado)

    # 4. Márketing
    filas_mk: list[tuple[str, str]] = [
        (ETIQUETAS_MEMORIA["mk_produto"].capitalize(), _val(plan.mk_produto)),
        (ETIQUETAS_MEMORIA["mk_prezo"].capitalize(), _val(plan.mk_prezo)),
        (ETIQUETAS_MEMORIA["mk_canles"].capitalize(), _val(plan.mk_canles)),
        (ETIQUETAS_MEMORIA["mk_comunicacion"].capitalize(), _val(plan.mk_comunicacion)),
    ]
    pts_args = puntos(plan.argumentos)
    if pts_args:
        for p in pts_args:
            filas_mk.append((ETIQUETAS_MEMORIA["argumentos"].capitalize(), p))
    else:
        filas_mk.append((ETIQUETAS_MEMORIA["argumentos"].capitalize(), "—"))
    folla(wb, "Márketing", "Plan de márketing", cab, ("Apartado", "Texto"), filas_mk)

    # 5. Calendario
    filas_cal: list[tuple[Any, ...]] = []
    if plan.actividades:
        for act in plan.actividades:
            meses = ["■" if act.mes_inicio <= m <= act.mes_fin else "" for m in range(1, 13)]
            filas_cal.append((act.actividade, act.responsable or "—", *meses))
    else:
        filas_cal.append(("—", "—", *( "" for _ in range(1, 13) )))
    folla(wb, "Calendario", "Calendario de actividades (12 meses)", cab,
          ("Actividade", "Responsable", *(f"Mes {m}" for m in range(1, 13))), filas_cal)

    # 6. Obxectivos
    filas_obx: list[tuple[str, ...]] = []
    if plan.obxectivos:
        for obx in plan.obxectivos:
            filas_obx.append((obx.obxectivo, obx.indicador, obx.meta or "—", obx.prazo or "—"))
    else:
        filas_obx.append(("—", "—", "—", "—"))
    folla(wb, "Obxectivos", "Obxectivos e indicadores", cab,
          ("Obxectivo", "Indicador", "Meta", "Prazo"), filas_obx)

    # 7. Riscos e permisos
    filas_riscos: list[tuple[str, str]] = []
    pts_riscos = puntos(plan.riscos)
    if pts_riscos:
        for p in pts_riscos:
            filas_riscos.append(("Risco", p))
    else:
        filas_riscos.append(("Risco", "—"))
    pts_permisos = puntos(plan.permisos)
    if pts_permisos:
        for p in pts_permisos:
            filas_riscos.append(("Permiso", p))
    else:
        filas_riscos.append(("Permiso", "—"))
    folla(wb, "Riscos e permisos", "Riscos e permisos", cab, ("Tipo", "Punto"), filas_riscos)

    # 8. Cifras
    ind = indicadores(plan)
    filas_cifras: list[tuple[str, Any]] = [
        ("Investimento sen IVE (€)", ind.investimento),
        ("Investimento con IVE (€)", ind.investimento_con_iva),
        ("VAN (€)", ind.van),
        ("TIR", f"{pct(ind.tir, 2)}" if ind.tir is not None else "—"),
        ("Pay-back (anos)", ind.payback if ind.payback is not None else "—"),
    ]
    for a in conta(plan):
        filas_cifras.append((f"Vendas ano {a.ano_n} ({a.ano})", a.vendas))
        filas_cifras.append((f"Beneficio antes de imposto ano {a.ano_n} ({a.ano})", a.beneficio))
    folla(wb, "Cifras", "Principais cifras e indicadores", cab, ("Concepto", "Valor"), filas_cifras)

    # 9. Escenarios
    esc_lista = escenarios(plan)
    filas_esc: list[tuple[Any, ...]] = [
        ("Vendas do ano 1", *(e.vendas_ano1 for e in esc_lista)),
        ("Beneficio do ano 1", *(e.beneficio_ano1 for e in esc_lista)),
        ("VAN", *(e.van for e in esc_lista)),
        ("TIR", *(f"{pct(e.tir)}" if e.tir is not None else "—" for e in esc_lista)),
        ("Pay-back", *(anos_texto(e.payback) for e in esc_lista)),
    ]
    folla(wb, "Escenarios", "Análise de escenarios", cab,
          ("Concepto", "Pesimista", "Normal", "Optimista"), filas_esc)

    # 10. Media galega
    filas_media: list[tuple[Any, ...]] = []
    if plan.ote_recan:
        for c in comparar_recan(session, actor, plan):
            nota = c.nota or ""
            if c.plan is None and c.indicador in (
                "Produción por hectárea",
                "Produción por UTA",
                "Resultado por UTA",
            ):
                nota = "Pon a superficie das parcelas ou as UTA para comparar"
            filas_media.append((
                c.indicador,
                c.plan if c.plan is not None else "—",
                c.media if c.media is not None else "—",
                c.unidade,
                nota,
            ))
        filas_media.append((f"Fonte: {fonte_recan()}", "", "", "", ""))
    else:
        filas_media.append(("Sen tipo de explotación escollido", "", "", "", ""))
    folla(wb, "Media galega", "Comparación coa media galega (RECAN)", cab,
          ("Indicador", "Plan", "Media RECAN", "Unidade", "Nota"), filas_media)

    saida = BytesIO()
    wb.save(saida)
    return saida.getvalue()

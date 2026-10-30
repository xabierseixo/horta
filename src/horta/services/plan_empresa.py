"""Plan de empresa (paso 16).

A conta a 5 anos propónse desde o real (Cartos) e edítase; as amortizacións saen do
investimento e os xuros dos préstamos. VAN, TIR e pay-back calcúlanse. Seguimento: o
previsto de cada ano ao lado do real. Ofertas (Anexo VI-A), o que lle falta para
presentalo e a documentación do art. 18 da convocatoria MR701L (DOG do 2/2/2026)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.lote import Clasificacion, Lote, LoteSaida
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.plan_empresa import (
    PlanAno,
    PlanEmpresa,
    PlanFinanciamento,
    PlanInvestimento,
    PlanOferta,
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
    "1": "1. Adquisición de terreos ou inmobles",
    "2": "2. Obra civil e instalacións",
    "3": "3. Maquinaria e equipamento",
    "4": "4. Estudos, proxectos e honorarios",
    "5": "5. Gastos de constitución",
    "6": "6. Outros",
}


@dataclass(frozen=True)
class Tipoloxia:
    texto: str
    axuda: str  # intensidade da axuda
    max_investimento: float | None = None  # investimento subvencionable máximo


# Arts. 11–15 da convocatoria
TIPOLOXIAS: dict[str, Tipoloxia] = {
    "primaria_enerxia": Tipoloxia(
        "Art. 11.1 · Explotación agraria: eficiencia enerxética ou renovables", "15–50 %"),
    "primaria_complementaria": Tipoloxia(
        "Art. 11.2 · Actividade agraria complementaria dunha principal non agraria",
        "15–50 %", 30000),
    "primaria_terras": Tipoloxia("Art. 11.3 · Mobilización ou recuperación de terras",
                                 "15–50 %"),
    "transformacion": Tipoloxia(
        "Art. 12 · Transformación e comercialización de produtos agrarios", "15–50 %", 60000),
    "forestal": Tipoloxia("Art. 13 · Transformación de produtos forestais",
                          "15–40 %, ata 200.000 € de axuda"),
    "non_agraria": Tipoloxia("Art. 14 · Actividades non agrarias",
                             "15–50 %, ata 200.000 € de axuda"),
    "bono": Tipoloxia("Art. 15 · Bono Activa Rural", "ata 18.000 € a tanto global"),
}
FONTES: dict[str, str] = {
    "capital": "Capital social",
    "propios": "Recursos propios",
    "prestamo": "Créditos ou préstamos",
    "subvencion": "Subvencións",
    "outros": "Outros",
}
CAMPOS_PLAN = frozenset({
    "titulo", "ano_inicio", "empresa_nova", "cnae", "descricion", "proceso", "formacion",
    "uta_mantidas", "uta_creadas", "uta_mulleres", "uta_mozas", "uta_maiores",
    "uta_discapacidade", "uta_outros", "taxa_desconto", "tipoloxia", "expediente",
    "anualidade", "submedida", "gdr", "participada", "traballadores", "facturacion",
    "balance", "iva_recuperable", "situacion_partida", "metodoloxia", "mercado",
    "ofertas_autenticas", "sen_vinculo_promotor", "sen_vinculo_entre_provedores"})


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


def crear_plan(session: Session, actor: Usuario, horta_id: int, titulo: str,
               ano_inicio: int, hoxe: date | None = None) -> PlanEmpresa:
    """Os 5 anos propóñense iguais ao último ano completo de Cartos."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    if not titulo.strip():
        raise OperacionNonPermitidaError("Pon un título ao plan")
    real = (hoxe or date.today()).year - 1
    vendas, variables, fixos = base_do_real(resumo_ano(session, actor, horta_id, real))
    plan = PlanEmpresa(horta_id=horta_id, titulo=titulo.strip(), ano_inicio=ano_inicio,
                       anos=[PlanAno(ano_n=n, vendas=vendas, custos_variables=variables,
                                     custos_fixos=fixos) for n in range(1, ANOS + 1)])
    session.add(plan)
    session.commit()
    return plan


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
    for campo, valor in cambios.items():
        setattr(plan, campo, valor)
    session.commit()
    return plan


def gardar_anos(session: Session, actor: Usuario, plan: PlanEmpresa,
                valores: dict[int, tuple[float, float, float, float]]) -> None:
    """ano_n → (vendas, custos variables, custos fixos, ingresos financeiros)."""
    _plan(session, actor, plan.id)
    for ano in plan.anos:
        if ano.ano_n in valores:
            vendas, variables, fixos, financeiros = valores[ano.ano_n]
            if min(vendas, variables, fixos, financeiros) < 0:
                raise OperacionNonPermitidaError("Os importes non poden ser negativos")
            ano.vendas, ano.custos_variables, ano.custos_fixos = vendas, variables, fixos
            ano.ingresos_financeiros = financeiros
    session.commit()


def engadir_investimento(session: Session, actor: Usuario, plan: PlanEmpresa, partida: str,
                         concepto: str, importe_sen_iva: float, iva_pct: float = 21,
                         vida_util_anos: int = 10, ofertas: int = 0) -> PlanInvestimento:
    _plan(session, actor, plan.id)
    if partida not in PARTIDAS:
        raise OperacionNonPermitidaError("Escolle a partida")
    if not concepto.strip() or importe_sen_iva <= 0:
        raise OperacionNonPermitidaError("Indica o concepto e un importe maior que 0")
    if iva_pct < 0 or vida_util_anos < 0 or ofertas < 0:
        raise OperacionNonPermitidaError("Valores negativos non")
    investimento = PlanInvestimento(
        partida=partida, concepto=concepto.strip(), importe_sen_iva=importe_sen_iva,
        iva_pct=iva_pct, vida_util_anos=0 if partida == "1" else vida_util_anos,
        ofertas=ofertas)
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


def quitar(session: Session, actor: Usuario, plan: PlanEmpresa,
           elemento: PlanInvestimento | PlanFinanciamento) -> None:
    _plan(session, actor, plan.id)
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
    financiamento: float
    van: float
    tir: float | None
    payback: int | None


def conta(plan: PlanEmpresa) -> list[AnoConta]:
    amortizacion = sum(i.importe_sen_iva / i.vida_util_anos
                       for i in plan.investimentos if i.vida_util_anos)
    xuros_ano: dict[int, float] = defaultdict(float)
    for fonte in plan.financiamento:
        for n, xuro in enumerate(xuros(fonte), start=1):
            xuros_ano[n] += xuro
    filas = []
    for ano in sorted(plan.anos, key=lambda a: a.ano_n):
        d = round(amortizacion, 2)
        e = round(ano.vendas - (ano.custos_variables + ano.custos_fixos + d), 2)
        f = -round(xuros_ano.get(ano.ano_n, 0), 2)
        g = round(e + f, 2)
        filas.append(AnoConta(ano.ano_n, plan.ano_inicio + ano.ano_n - 1, ano.vendas,
                              ano.custos_variables, ano.custos_fixos, d, e, f, g,
                              round(g + d, 2)))
    return filas


def _van(taxa: float, fluxos: list[float]) -> float:
    return sum(f / (1 + taxa) ** n for n, f in enumerate(fluxos))


def indicadores(plan: PlanEmpresa) -> Indicadores:
    investimento = round(sum(i.importe_sen_iva for i in plan.investimentos), 2)
    con_iva = round(sum(i.importe_sen_iva * (1 + i.iva_pct / 100)
                        for i in plan.investimentos), 2)
    fluxos = [-investimento, *(a.fluxo for a in conta(plan))]
    tir = None
    # TIR por bisección, se o signo cambia entre -99 % e 100 %
    baixo, alto = -0.99, 1.0
    if investimento and _van(baixo, fluxos) * _van(alto, fluxos) < 0:
        for _ in range(100):
            medio = (baixo + alto) / 2
            if _van(baixo, fluxos) * _van(medio, fluxos) <= 0:
                alto = medio
            else:
                baixo = medio
        tir = round((baixo + alto) / 2, 4)
    acumulado, payback = 0.0, None
    for n, fluxo in enumerate(fluxos):
        acumulado += fluxo
        if n and acumulado >= 0:
            payback = n
            break
    return Indicadores(investimento, con_iva,
                       round(sum(f.importe for f in plan.financiamento), 2),
                       round(_van(plan.taxa_desconto, fluxos), 2), tir, payback)


def avisos_plan(plan: PlanEmpresa) -> list[str]:
    avisos = [f"«{i.concepto}»: hai {i.ofertas} ofertas e piden tres (art. 18.h)"
              for i in plan.investimentos if i.ofertas < 3]
    ind = indicadores(plan)
    if ind.investimento and abs(ind.financiamento - ind.investimento_con_iva) > 1:
        def euros(valor: float) -> str:
            return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")

        avisos.append(f"O financiamento ({euros(ind.financiamento)}) non cadra co "
                      f"investimento con IVE ({euros(ind.investimento_con_iva)})")
    return avisos


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


def xerar_anexos(session: Session, actor: Usuario, plan_id: int) -> bytes:
    """Excel co Anexo III (resumo do plan) e o Anexo V (orzamento por partidas)."""
    from io import BytesIO

    from openpyxl import Workbook

    from horta.services.caderno import folla

    plan = _plan(session, actor, plan_id)
    cab = f"{plan.titulo} · Ano 1: {plan.ano_inicio}"
    ind = indicadores(plan)
    wb = Workbook()
    wb.remove(wb.active)
    folla(wb, "Anexo III", "Resumo do proxecto – plan de empresa (095c, Anexo III)", cab,
          ("Apartado", "Valor"),
          [("Empresa", "Nova" if plan.empresa_nova else "Existente"),
           ("CNAE", plan.cnae or ""),
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
           *((f"5. {FONTES[t]} (€)", round(sum(f.importe for f in plan.financiamento
                                                if f.tipo == t), 2)) for t in FONTES),
           ("5. Total investimento con IVE (€)", ind.investimento_con_iva),
           ("VAN (€)", ind.van), ("TIR", f"{ind.tir:.2%}" if ind.tir is not None else "—"),
           ("Pay-back (anos)", ind.payback or "—")])
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
    folla(wb, "Anexo V", "Orzamento de gastos desagregados por partidas (095c, Anexo V)",
          cab, ("Partida", "Concepto", "Importe sen IVE (€)", "IVE (%)",
                "Importe con IVE (€)", "Ofertas"),
          [(PARTIDAS[i.partida], i.concepto, i.importe_sen_iva, i.iva_pct,
            round(i.importe_sen_iva * (1 + i.iva_pct / 100), 2), i.ofertas)
           for i in sorted(plan.investimentos, key=lambda i: i.partida)])
    saida = BytesIO()
    wb.save(saida)
    return saida.getvalue()

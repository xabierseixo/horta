"""Os cartos: cobros e pagos, outros
gastos e ingresos, custo de cada traballo e resumo do ano. Non se apunta nada que saia doutro
sitio: ingresos e gastos saen das vendas, compras e horas; á man só os outros."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from horta.db import Base
from horta.idiomas import N_
from horta.models.cartos import ApunteCartos
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.lote import LoteSaida
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.produto import EntradaProduto
from horta.models.tarefa import Tarefa
from horta.models.traballo import FeitoPor
from horta.models.tratamento_fito import TratamentoAplicador, TratamentoFito
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

# Quen só mira non ve os cartos
_ROLES = {RolHorta.ADMIN, RolHorta.EDITOR}

CATEGORIAS: dict[str, str] = {
    "seguro": N_("Seguro"),
    "aluguer": N_("Aluguer"),
    "auga": N_("Auga"),
    "luz": N_("Luz"),
    "combustible": N_("Combustible"),
    "cota": N_("Cota (cooperativa, asociación…)"),
    "axuda": N_("Axuda ou subvención"),
    "impostos": N_("Impostos e taxas"),
    "reparacion": N_("Reparación"),
    "servizos": N_("Servizos (xestoría, veterinario…)"),
    "outro": N_("Outro"),
}
TIPOS = {"gasto": N_("Gasto"), "ingreso": N_("Ingreso")}
# A man de obra destes vínculos non é un pago: custo de oportunidade
VINCULOS_PROPIOS = ("titular", "familiar", "socio")


def comprobar_pago(data: date, data_pago: date | None, hoxe: date) -> None:
    """A data do cobro ou do pago: nin anterior á operación nin futura."""
    if data_pago is None:
        return
    if data_pago < data:
        raise OperacionNonPermitidaError("O cobro ou pago non pode ser anterior á operación")
    if data_pago > hoxe:
        raise OperacionNonPermitidaError("A data do cobro ou pago non pode ser futura")


# --- Outros gastos e ingresos

@dataclass(kw_only=True)
class DatosApunte:
    tipo: str
    categoria: str
    concepto: str
    data: date
    importe: float
    persoa_id: int | None = None
    albaran_factura: str | None = None
    data_pago: date | None = None
    notas: str | None = None


def _validar(session: Session, horta_id: int, datos: DatosApunte, hoxe: date) -> None:
    if datos.tipo not in TIPOS:
        raise OperacionNonPermitidaError("Indica se é un gasto ou un ingreso")
    if datos.categoria not in CATEGORIAS:
        raise OperacionNonPermitidaError("Escolle unha categoría")
    if not (datos.concepto or "").strip():
        raise OperacionNonPermitidaError("Indica o concepto")
    if datos.importe is None or datos.importe <= 0:
        raise OperacionNonPermitidaError("O importe ten que ser maior que 0")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    comprobar_pago(datos.data, datos.data_pago, hoxe)
    if datos.persoa_id is not None:
        persoa = session.get(Persoa, datos.persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("Esa persoa non é desta explotación")


def _copiar(apunte: ApunteCartos, datos: DatosApunte) -> None:
    apunte.tipo = datos.tipo
    apunte.categoria = datos.categoria
    apunte.concepto = datos.concepto.strip()
    apunte.data = datos.data
    apunte.importe = datos.importe
    apunte.persoa_id = datos.persoa_id
    apunte.albaran_factura = datos.albaran_factura or None
    apunte.data_pago = datos.data_pago
    apunte.notas = datos.notas or None


def crear_apunte(session: Session, actor: Usuario, horta_id: int, datos: DatosApunte,
                 hoxe: date | None = None) -> ApunteCartos:
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    _validar(session, horta_id, datos, hoxe or date.today())
    apunte = ApunteCartos(horta_id=horta_id, creado_por=actor.id)
    _copiar(apunte, datos)
    session.add(apunte)
    session.commit()
    return apunte


def actualizar_apunte(session: Session, actor: Usuario, apunte: ApunteCartos,
                      datos: DatosApunte, hoxe: date | None = None) -> ApunteCartos:
    if apunte.baixa:
        raise OperacionNonPermitidaError("Un apunte dado de baixa non se pode modificar")
    comprobar_rol_horta(session, apunte.horta_id, actor, _ROLES)
    _validar(session, apunte.horta_id, datos, hoxe or date.today())
    _copiar(apunte, datos)
    session.commit()
    return apunte


def dar_de_baixa_apunte(session: Session, actor: Usuario, apunte: ApunteCartos) -> None:
    comprobar_rol_horta(session, apunte.horta_id, actor, _ROLES)
    apunte.baixa = True
    session.commit()


def listar_apuntes(session: Session, actor: Usuario, horta_id: int,
                   desde: date | None = None, ata: date | None = None
                   ) -> list[ApunteCartos]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    consulta = session.query(ApunteCartos).filter_by(horta_id=horta_id, baixa=False)
    if desde is not None:
        consulta = consulta.filter(ApunteCartos.data >= desde)
    if ata is not None:
        consulta = consulta.filter(ApunteCartos.data <= ata)
    return list(consulta.order_by(ApunteCartos.data.desc(), ApunteCartos.id.desc()))


# --- Pendente de cobrar e de pagar

@dataclass(frozen=True)
class Pendente:
    """Que é, a quen e canto (positivo: debénche; negativo: debes)."""

    data: date
    que: str
    persoa_id: int | None
    importe: float


def _pendentes(session: Session, horta_id: int) -> list[Pendente]:
    lista: list[Pendente] = []
    for s in session.query(LoteSaida).filter(
            LoteSaida.horta_id == horta_id, LoteSaida.baixa.is_(False),
            LoteSaida.tipo == "venda", LoteSaida.importe.is_not(None),
            LoteSaida.data_pago.is_(None)):
        lista.append(Pendente(s.data_fin, "Venda", s.comprador_id, s.importe or 0))
    for e in session.query(EntradaProduto).filter(
            EntradaProduto.horta_id == horta_id, EntradaProduto.baixa.is_(False),
            EntradaProduto.importe.is_not(None), EntradaProduto.data_pago.is_(None)):
        lista.append(Pendente(e.data, "Compra", e.provedor_id, -(e.importe or 0)))
    for m in session.query(MovementoAnimal).filter(
            MovementoAnimal.horta_id == horta_id, MovementoAnimal.baixa.is_(False),
            MovementoAnimal.importe.is_not(None), MovementoAnimal.data_pago.is_(None)):
        venda = m.tipo == "saida"
        lista.append(Pendente(m.data, "Venda de animais" if venda else "Compra de animais",
                              m.outra_parte_id, (m.importe or 0) * (1 if venda else -1)))
    for a in session.query(ApunteCartos).filter(
            ApunteCartos.horta_id == horta_id, ApunteCartos.baixa.is_(False),
            ApunteCartos.data_pago.is_(None)):
        lista.append(Pendente(a.data, a.concepto, a.persoa_id,
                              a.importe * (1 if a.tipo == "ingreso" else -1)))
    return sorted(lista, key=lambda p: p.data)


def pendentes(session: Session, actor: Usuario, horta_id: int) -> list[Pendente]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    return _pendentes(session, horta_id)


def pendente_por_persoa(session: Session, actor: Usuario, horta_id: int
                        ) -> dict[int | None, tuple[float, float]]:
    """Para cada persoa (None: sen persoa): (cobrar, pagar) pendentes."""
    cobrar: dict[int | None, float] = defaultdict(float)
    pagar: dict[int | None, float] = defaultdict(float)
    for p in pendentes(session, actor, horta_id):
        if p.importe > 0:
            cobrar[p.persoa_id] += p.importe
        else:
            pagar[p.persoa_id] += -p.importe
    saldos = {k: (round(cobrar[k], 2), round(pagar[k], 2)) for k in {*cobrar, *pagar}}
    return {k: v for k, v in saldos.items() if v != (0.0, 0.0)}


def pendente_da_persoa(session: Session, actor: Usuario, persoa: Persoa) -> list[Pendente]:
    """Para o historial do contacto."""
    return [p for p in pendentes(session, actor, persoa.horta_id) if p.persoa_id == persoa.id]


# --- Custo dos traballos

@dataclass
class Custos:
    man_de_obra: float = 0.0
    # Parte da man de obra do titular, familia e socios (non é un pago)
    man_de_obra_propia: float = 0.0
    maquinas: float = 0.0
    # Traballos con horas pero sen custo da hora (de quen ou da máquina)
    sen_custo: int = 0


def horas_dos_traballos(session: Session, horta_id: int, desde: date, ata: date
                         ) -> list[tuple[int | None, int | None, float]]:
    """(persoa, máquina, horas) de cada traballo feito entre dúas datas."""
    horas: list[tuple[int | None, int | None, float]] = []
    for mapper in Base.registry.mappers:
        modelo: Any = mapper.class_
        if not issubclass(modelo, FeitoPor):
            continue
        columna = next(getattr(modelo, c) for c in ("data_inicio", "data", "data_mostraxe")
                       if hasattr(modelo, c))
        consulta = session.query(modelo).filter(
            modelo.baixa.is_(False), modelo.horas.is_not(None), columna >= desde,
            columna <= ata)
        # A colleita é da explotación a través do seu cultivo
        consulta = (consulta.join(Cultivo, Cultivo.id == modelo.cultivo_id)
                    .join(Parcela, Parcela.id == Cultivo.parcela_id)
                    .filter(Parcela.horta_id == horta_id) if not hasattr(modelo, "horta_id")
                    else consulta.filter(modelo.horta_id == horta_id))
        for t in consulta:
            horas.append((t.persoa_id, getattr(t, "maquina_id", None), t.horas))
    for ap in (session.query(TratamentoAplicador)
               .join(TratamentoFito, TratamentoFito.id == TratamentoAplicador.tratamento_id)
               .filter(TratamentoFito.horta_id == horta_id, TratamentoFito.baixa.is_(False),
                       TratamentoAplicador.horas_utilizacion.is_not(None),
                       TratamentoFito.data_inicio >= desde, TratamentoFito.data_inicio <= ata)):
        horas.append((ap.persoa_id, ap.maquina_id, ap.horas_utilizacion or 0))
    for cu in session.query(Cultivo).join(Parcela, Parcela.id == Cultivo.parcela_id).filter(
            Parcela.horta_id == horta_id, Cultivo.sementeira_horas.is_not(None),
            Cultivo.data_inicio >= desde, Cultivo.data_inicio <= ata):
        horas.append((cu.sementeira_persoa_id, None, cu.sementeira_horas or 0))
    # Só as tarefas feitas sen tipo: as que teñen tipo xa están no seu traballo
    for ta in session.query(Tarefa).filter(
            Tarefa.horta_id == horta_id, Tarefa.estado == "feito", Tarefa.tipo.is_(None),
            Tarefa.traballo_id.is_(None), Tarefa.horas.is_not(None),
            Tarefa.data_feita >= desde, Tarefa.data_feita <= ata):
        horas.append((ta.persoa_id, None, ta.horas or 0))
    return horas


def custos(session: Session, horta_id: int, desde: date, ata: date) -> Custos:
    persoas = {p.id: p for p in session.query(Persoa).filter_by(horta_id=horta_id)}
    maquinas = {m.id: m for m in session.query(Maquina).filter_by(horta_id=horta_id)}
    total = Custos()
    for persoa_id, maquina_id, horas in horas_dos_traballos(session, horta_id, desde, ata):
        persoa = persoas.get(persoa_id or 0)
        maquina = maquinas.get(maquina_id or 0)
        if persoa is not None and persoa.custo_hora is not None:
            custo = horas * persoa.custo_hora
            total.man_de_obra += custo
            if persoa.vinculo in VINCULOS_PROPIOS:
                total.man_de_obra_propia += custo
        else:
            total.sen_custo += 1
        if maquina is not None:
            if maquina.custo_hora is not None:
                total.maquinas += horas * maquina.custo_hora
            else:
                total.sen_custo += 1
    return total


# --- Resumo do ano

# --- Períodos do resumo

PERIODOS = {
    "semana": N_("Semana"),
    "mes": N_("Mes"),
    "trimestre": N_("Trimestre"),
    "ano": N_("Ano"),
}
_MESES = ("xaneiro", "febreiro", "marzo", "abril", "maio", "xuño", "xullo", "agosto",
          "setembro", "outubro", "novembro", "decembro")


@dataclass(frozen=True)
class Periodo:
    desde: date
    ata: date
    nome: str


def periodo(tipo: str, dia: date) -> Periodo:
    """A semana (de luns a domingo), o mes, o trimestre ou o ano onde cae ese día."""
    if tipo == "semana":
        luns = dia - timedelta(days=dia.weekday())
        domingo = luns + timedelta(days=6)
        return Periodo(luns, domingo, f"Semana do {luns:%d/%m/%Y} ao {domingo:%d/%m/%Y}")
    if tipo == "mes":
        seguinte = date(dia.year + dia.month // 12, dia.month % 12 + 1, 1)
        return Periodo(date(dia.year, dia.month, 1), seguinte - timedelta(days=1),
                       f"{_MESES[dia.month - 1].capitalize()} de {dia.year}")
    if tipo == "trimestre":
        t = (dia.month - 1) // 3
        inicio = date(dia.year, 3 * t + 1, 1)
        fin = periodo("mes", date(dia.year, 3 * t + 3, 1)).ata
        return Periodo(inicio, fin, f"{t + 1}.º trimestre de {dia.year}")
    if tipo == "ano":
        return Periodo(date(dia.year, 1, 1), date(dia.year, 12, 31), str(dia.year))
    raise OperacionNonPermitidaError("Período descoñecido")


def periodos_recentes(tipo: str, hoxe: date, cantos: int = 12) -> list[Periodo]:
    """O período actual e os anteriores, do máis recente ao máis antigo."""
    lista = [periodo(tipo, hoxe)]
    while len(lista) < cantos:
        lista.append(periodo(tipo, lista[-1].desde - timedelta(days=1)))
    return lista


@dataclass
class Resumo:
    periodo: Periodo
    ingresos: dict[str, float] = field(default_factory=dict)
    gastos: dict[str, float] = field(default_factory=dict)
    custos: Custos = field(default_factory=Custos)
    vendas_sen_prezo: int = 0

    @property
    def total_ingresos(self) -> float:
        return round(sum(self.ingresos.values()), 2)

    @property
    def total_gastos(self) -> float:
        return round(sum(self.gastos.values()), 2)

    @property
    def resultado(self) -> float:
        return round(self.total_ingresos - self.total_gastos, 2)

    @property
    def resultado_sen_man_propia(self) -> float:
        """O resultado sen contar as horas do titular e a familia (que non se pagan)."""
        return round(self.resultado + self.custos.man_de_obra_propia, 2)


def resumo_ano(session: Session, actor: Usuario, horta_id: int, ano: int) -> Resumo:
    return resumo_periodo(session, actor, horta_id, periodo("ano", date(ano, 1, 1)))


def resumo_periodo(session: Session, actor: Usuario, horta_id: int, periodo: Periodo
                   ) -> Resumo:
    comprobar_rol_horta(session, horta_id, actor, _ROLES)
    desde, ata = periodo.desde, periodo.ata
    resumo = Resumo(periodo)

    def suma(valores: Any) -> float:
        return round(sum(v or 0 for (v,) in valores), 2)

    vendas = (LoteSaida.horta_id == horta_id, LoteSaida.baixa.is_(False),
              LoteSaida.tipo == "venda", LoteSaida.data_fin >= desde, LoteSaida.data_fin <= ata)
    resumo.ingresos["Vendas"] = suma(session.query(LoteSaida.importe).filter(*vendas))
    resumo.vendas_sen_prezo = session.query(LoteSaida).filter(
        *vendas, LoteSaida.importe.is_(None)).count()
    for tipo, onde, nome in (("saida", resumo.ingresos, "Venda de animais"),
                             ("entrada", resumo.gastos, "Compra de animais")):
        onde[nome] = suma(session.query(MovementoAnimal.importe).filter(
            MovementoAnimal.horta_id == horta_id, MovementoAnimal.baixa.is_(False),
            MovementoAnimal.tipo == tipo, MovementoAnimal.data >= desde,
            MovementoAnimal.data <= ata))
    resumo.gastos["Compras de produtos"] = suma(session.query(EntradaProduto.importe).filter(
        EntradaProduto.horta_id == horta_id, EntradaProduto.baixa.is_(False),
        EntradaProduto.data >= desde, EntradaProduto.data <= ata))
    for apunte in session.query(ApunteCartos).filter(
            ApunteCartos.horta_id == horta_id, ApunteCartos.baixa.is_(False),
            ApunteCartos.data >= desde, ApunteCartos.data <= ata):
        onde = resumo.ingresos if apunte.tipo == "ingreso" else resumo.gastos
        nome = CATEGORIAS[apunte.categoria]
        onde[nome] = round(onde.get(nome, 0) + apunte.importe, 2)
    resumo.custos = custos(session, horta_id, desde, ata)
    resumo.gastos["Man de obra"] = round(resumo.custos.man_de_obra, 2)
    resumo.gastos["Máquinas"] = round(resumo.custos.maquinas, 2)
    resumo.ingresos = {k: v for k, v in resumo.ingresos.items() if v}
    resumo.gastos = {k: v for k, v in resumo.gastos.items() if v}
    return resumo

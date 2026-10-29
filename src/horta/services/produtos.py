"""Produtos (insumos) e entradas (compras ou recepcións), e as existencias: o que entrou menos o
que se usou nos abonados, tratamentos, coidados e sementeiras
."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, Fertilizante
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.produto import EntradaProduto, Produto
from horta.models.tratamento_fito import TratamentoFito, TratamentoProduto
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import dose_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import converter
from horta.services.persoas import comprobar_quen, persoa_co_papel

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_PRODUTO: dict[str, str] = {
    "fitosanitario": "Fitosanitario",
    "abono": "Abono",
    "semente": "Semente ou planta",
    "medicamento": "Medicamento veterinario",
    "penso": "Penso",
    "enerxia": "Enerxía (gasóleo, luz...)",
    "outro": "Outro",
}
UNIDADES_PRODUTO = ("kg", "litros", "unidades")
UNIDADES_ENTRADA = ("kg", "t", "litros", "unidades", "ducias")
# Unidades do catálogo oficial (tratamentos e coidados): absolutas e por hectárea
_ABSOLUTAS = {"5": "kg", "6": "t", "4": "litros", "11": "unidades"}
_POR_HECTAREA = {"17": "kg", "18": "litros", "29": "t"}


# --- Produtos

def crear_produto(session: Session, actor: Usuario, horta_id: int, tipo: str, nome: str,
                  unidade: str, num_rexistro: str | None = None,
                  fertilizante_id: int | None = None, tipo_enerxia: str | None = None,
                  gardar: bool = True) -> Produto:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if tipo not in TIPOS_PRODUTO:
        raise OperacionNonPermitidaError("Escolle que tipo de produto é")
    if not nome.strip():
        raise OperacionNonPermitidaError("Pon un nome ao produto")
    if unidade not in UNIDADES_PRODUTO:
        raise OperacionNonPermitidaError("A unidade é kg, litros ou unidades")
    produto = Produto(horta_id=horta_id, tipo=tipo, nome=nome.strip(), unidade=unidade,
                      num_rexistro=(num_rexistro or "").strip() or None,
                      fertilizante_id=fertilizante_id, tipo_enerxia=tipo_enerxia or None)
    session.add(produto)
    if gardar:
        session.commit()
    else:
        session.flush()
    return produto


def produto_ou_novo(session: Session, actor: Usuario, horta_id: int, tipo: str, nome: str,
                    unidade: str = "unidades", num_rexistro: str | None = None) -> Produto:
    """O produto dese tipo co mesmo nº de rexistro (ou nome), ou un novo. Para os formularios
    e para ligar os tratamentos cos seus fitosanitarios."""
    consulta = session.query(Produto).filter_by(horta_id=horta_id, tipo=tipo)
    if num_rexistro:
        existente = consulta.filter_by(num_rexistro=num_rexistro.strip()).first()
    else:
        existente = next((p for p in consulta
                          if p.nome.strip().lower() == nome.strip().lower()), None)
    if existente is not None:
        return existente
    return crear_produto(session, actor, horta_id, tipo, nome or num_rexistro or "",
                         unidade, num_rexistro=num_rexistro, gardar=False)


def produto_do_abono(session: Session, fertilizante: Fertilizante) -> Produto:
    """O produto dun abono (creado con el)."""
    produto = session.query(Produto).filter_by(fertilizante_id=fertilizante.id).one_or_none()
    if produto is None:
        produto = Produto(horta_id=fertilizante.horta_id, tipo="abono", nome=fertilizante.nome,
                          unidade="litros" if fertilizante.liquido else "kg",
                          fertilizante_id=fertilizante.id)
        session.add(produto)
        session.flush()
    return produto


def listar_produtos(session: Session, actor: Usuario, horta_id: int, tipo: str | None = None,
                    so_activos: bool = True) -> list[Produto]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Produto).filter_by(horta_id=horta_id)
    if tipo is not None:
        consulta = consulta.filter_by(tipo=tipo)
    if so_activos:
        consulta = consulta.filter_by(activo=True)
    return list(consulta.order_by(Produto.tipo, Produto.nome))


# --- Entradas

@dataclass(kw_only=True)
class DatosEntrada:
    produto_id: int
    data: date
    persoa_id: int | None
    provedor_id: int | None = None
    cantidade: float | None = None
    unidade: str | None = None
    lote_provedor: str | None = None
    albaran_factura: str | None = None
    importe: float | None = None
    data_caducidade: date | None = None
    pasaporte_fitosanitario: str | None = None
    horas: float | None = None
    notas: str | None = None


def _validar_entrada(session: Session, datos: DatosEntrada, produto: Produto,
                     hoxe: date) -> None:
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    comprobar_quen(session, produto.horta_id, datos.persoa_id, datos.horas)
    persoa_co_papel(session, produto.horta_id, datos.provedor_id, "provedor")
    if datos.cantidade is not None:
        if datos.cantidade <= 0:
            raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
        if converter(datos.cantidade, datos.unidade or produto.unidade, produto.unidade) is None:
            raise OperacionNonPermitidaError(f"Este produto cóntase en {produto.unidade}")
    if datos.importe is not None and datos.importe < 0:
        raise OperacionNonPermitidaError("O prezo non pode ser negativo")
    if datos.data_caducidade is not None and datos.data_caducidade < datos.data:
        raise OperacionNonPermitidaError("A caducidade non pode ser anterior á entrada")


def _copiar_entrada(entrada: EntradaProduto, datos: DatosEntrada, produto: Produto) -> None:
    entrada.horta_id = produto.horta_id
    entrada.produto_id = produto.id
    entrada.data = datos.data
    entrada.provedor_id = datos.provedor_id
    entrada.cantidade = datos.cantidade
    entrada.unidade = (datos.unidade or produto.unidade) if datos.cantidade else None
    entrada.lote_provedor = datos.lote_provedor or None
    entrada.albaran_factura = datos.albaran_factura or None
    entrada.importe = datos.importe
    entrada.data_caducidade = datos.data_caducidade
    entrada.pasaporte_fitosanitario = (datos.pasaporte_fitosanitario or None
                                       if produto.tipo == "semente" else None)
    entrada.persoa_id = datos.persoa_id
    entrada.horas = datos.horas
    entrada.notas = datos.notas or None


def _produto(session: Session, produto_id: int) -> Produto:
    produto = session.get(Produto, produto_id)
    if produto is None:
        raise OperacionNonPermitidaError("Ese produto non existe")
    return produto


def crear_entrada(session: Session, actor: Usuario, datos: DatosEntrada,
                  hoxe: date | None = None) -> EntradaProduto:
    produto = _produto(session, datos.produto_id)
    comprobar_rol_horta(session, produto.horta_id, actor, _ROLES_ESCRITURA)
    _validar_entrada(session, datos, produto, hoxe or date.today())
    entrada = EntradaProduto(creado_por=actor.id)
    _copiar_entrada(entrada, datos, produto)
    session.add(entrada)
    session.commit()
    return entrada


def actualizar_entrada(session: Session, actor: Usuario, entrada: EntradaProduto,
                       datos: DatosEntrada, hoxe: date | None = None) -> EntradaProduto:
    if entrada.baixa:
        raise OperacionNonPermitidaError("Unha entrada dada de baixa non se pode modificar")
    comprobar_rol_horta(session, entrada.horta_id, actor, _ROLES_ESCRITURA)
    produto = _produto(session, datos.produto_id)
    if produto.horta_id != entrada.horta_id:
        raise OperacionNonPermitidaError("Ese produto non é desta explotación")
    _validar_entrada(session, datos, produto, hoxe or date.today())
    _copiar_entrada(entrada, datos, produto)
    session.commit()
    return entrada


def dar_de_baixa_entrada(session: Session, actor: Usuario, entrada: EntradaProduto) -> None:
    comprobar_rol_horta(session, entrada.horta_id, actor, _ROLES_ESCRITURA)
    entrada.baixa = True
    session.commit()


def listar_entradas(session: Session, actor: Usuario, horta_id: int,
                    produto_id: int | None = None, tipo: str | None = None
                    ) -> list[EntradaProduto]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(EntradaProduto).filter_by(horta_id=horta_id, baixa=False)
    if produto_id is not None:
        consulta = consulta.filter_by(produto_id=produto_id)
    if tipo is not None:
        consulta = consulta.join(Produto, Produto.id == EntradaProduto.produto_id).filter(
            Produto.tipo == tipo)
    return list(consulta.order_by(EntradaProduto.data.desc(), EntradaProduto.id.desc()))


def comprobar_entrada_do_produto(session: Session, horta_id: int, entrada_id: int | None,
                                 produto_id: int | None) -> EntradaProduto | None:
    """A entrada escollida nun uso ten que ser desta explotación e dese produto."""
    if entrada_id is None:
        return None
    entrada = session.get(EntradaProduto, entrada_id)
    if entrada is None or entrada.horta_id != horta_id or entrada.baixa:
        raise OperacionNonPermitidaError("Esa compra non é desta explotación")
    if produto_id is not None and entrada.produto_id != produto_id:
        raise OperacionNonPermitidaError("Esa compra é doutro produto")
    return entrada


# --- Existencias

@dataclass
class Existencias:
    entrou: float
    usado: float
    sen_contar: int  # usos que non se poden contar (sen cantidade ou noutra unidade)
    entradas_sen_cantidade: int

    @property
    def queda(self) -> float:
        return self.entrou - self.usado


def _usos(session: Session, produto: Produto) -> list[tuple[float | None, str | None]]:
    """Cantidade e unidade de cada uso do produto (None se non se pode saber)."""
    usos: list[tuple[float | None, str | None]] = []
    if produto.fertilizante_id is not None:
        fertilizante = session.get(Fertilizante, produto.fertilizante_id)
        for ab in session.query(Abonado).filter_by(fertilizante_id=produto.fertilizante_id,
                                                   baixa=False):
            superficie = sum(le.superficie_ha or 0 for le in ab.leiras)
            kg_ha = (dose_kg_ha(ab.dose, ab.unidade, fertilizante.densidade if fertilizante
                                else None) if ab.dose is not None and ab.unidade else None)
            usos.append((kg_ha * superficie, "kg") if kg_ha is not None and superficie
                        else (None, None))
    for tp in (session.query(TratamentoProduto)
               .join(TratamentoFito, TratamentoFito.id == TratamentoProduto.tratamento_id)
               .filter(TratamentoProduto.produto_id == produto.id,
                       TratamentoFito.baixa.is_(False))):
        if tp.cantidade is not None and tp.unidade in _ABSOLUTAS:
            usos.append((tp.cantidade, _ABSOLUTAS[tp.unidade]))
        elif tp.dose is not None and tp.unidade in _POR_HECTAREA:
            tratamento = session.get(TratamentoFito, tp.tratamento_id)
            superficie = sum(c.superficie_ha or 0 for c in tratamento.cultivos) \
                if tratamento else 0
            usos.append((tp.dose * superficie, _POR_HECTAREA[tp.unidade]) if superficie
                        else (None, None))
        else:
            usos.append((None, None))
    for co in session.query(CoidadoAnimal).filter_by(produto_id=produto.id, baixa=False):
        usos.append((co.cantidade, _ABSOLUTAS.get(co.unidade or ""))
                    if co.cantidade is not None else (None, None))
    for cu in (session.query(Cultivo)
               .join(EntradaProduto, EntradaProduto.id == Cultivo.entrada_semente_id)
               .filter(EntradaProduto.produto_id == produto.id)):
        if cu.cantidade_semente_kg:
            usos.append((cu.cantidade_semente_kg, "kg"))
        elif cu.dose_sementeira_kg_ha and cu.superficie_ha:
            usos.append((cu.dose_sementeira_kg_ha * cu.superficie_ha, "kg"))
        else:
            usos.append((None, None))
    return usos


def existencias(session: Session, produto: Produto) -> Existencias:
    entrou, sen_cantidade = 0.0, 0
    for entrada in session.query(EntradaProduto).filter_by(produto_id=produto.id, baixa=False):
        cantidade = (converter(entrada.cantidade, entrada.unidade or produto.unidade,
                               produto.unidade) if entrada.cantidade is not None else None)
        if cantidade is None:
            sen_cantidade += 1
        else:
            entrou += cantidade
    usado, sen_contar = 0.0, 0
    for cantidade, unidade in _usos(session, produto):
        convertida = (converter(cantidade, unidade, produto.unidade)
                      if cantidade is not None and unidade else None)
        if convertida is None:
            sen_contar += 1
        else:
            usado += convertida
    return Existencias(round(entrou, 3), round(usado, 3), sen_contar, sen_cantidade)


def ten_movementos(session: Session, produto: Produto) -> bool:
    return (session.query(EntradaProduto).filter_by(produto_id=produto.id).first() is not None
            or bool(_usos(session, produto)))

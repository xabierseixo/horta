"""Lotes e saídas do produto.

Nun lote entran colleitas e producións dos animais do mesmo produto; del sae o produto por
venda, para casa, para transformar, como perda ou para os animais. O que queda calcúlase:
entradas − saídas, na unidade do lote. Avisa (sen bloquear) dos máximos anuais da venda
directa (Decreto 125/2014, anexo II), do tempo de espera e do prazo de seguridade."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.lote import Lote, LoteSaida
from horta.models.producion_animal import ProducionAnimal
from horta.models.usuario import Usuario
from horta.services.cartos import comprobar_pago
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen, persoa_co_papel

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_SAIDA: dict[str, str] = {
    "venda": "Venda",
    "casa": "Para casa",
    "transformacion": "Para transformar",
    "perda": "Perda (podre, roto...)",
    "animais": "Para os animais",
}
# Decreto 125/2014 art. 4 (venda directa) e venda a almacén ou cooperativa (CUE 3: colleita
# comercializada)
CANLES: dict[str, str] = {
    "explotacion": "Na explotación",
    "mercado": "Nun mercado",
    "domicilio": "A domicilio",
    "tenda": "A unha tenda",
    "almacen": "A un almacén ou cooperativa",
}
CANLES_DIRECTAS = ("explotacion", "mercado", "domicilio", "tenda")
# Decreto 125/2014 anexo II: nome, máximo ao ano ao aire libre e en invernadoiro, unidade
CATEGORIAS_VENDA_DIRECTA: dict[str, tuple[str, float, float | None, str]] = {
    "hortalizas": ("Hortalizas", 20000, 40000, "kg"),
    "froitas": ("Froitas", 20000, None, "kg"),
    "amoras": ("Amoras", 5000, 10000, "kg"),
    "kiwi": ("Kiwi", 13000, None, "kg"),
    "legumes": ("Legumes", 10000, 24000, "kg"),
    "patacas": ("Patacas", 20000, None, "kg"),
    "cogomelos": ("Cogomelos", 500, 2500, "kg"),
    "cereais": ("Cereais", 5000, None, "kg"),
    "ovos": ("Ovos", 1000, None, "ducias"),
    "mel": ("Mel", 3000, None, "kg"),
    "pole": ("Pole", 450, None, "kg"),
    "propoleo": ("Propóleo", 30, None, "kg"),
    "xelea": ("Xelea real", 10, None, "kg"),
}
# Produtos dos animais que teñen categoría propia
_CATEGORIA_ANIMAL = {"ovos": "ovos", "mel": "mel"}
# Sistemas de cultivo (catálogo sistema_cultivo) en invernadoiro ou túnel
SISTEMAS_PROTEXIDOS = ("4", "19", "26", "27", "28")
# Unidades que se poden converter: a cal e por canto
_BASE = {"kg": ("kg", 1.0), "t": ("kg", 1000.0), "unidades": ("unidades", 1.0),
         "ducias": ("unidades", 12.0), "litros": ("litros", 1.0), "mazos": ("mazos", 1.0)}
_CON_COMPRADOR = ("tenda", "almacen")


def converter(cantidade: float, de: str, a: str) -> float | None:
    """A cantidade noutra unidade, ou None se non se pode converter (p.ex. kg a unidades)."""
    if de == a:
        return cantidade
    orixe, destino = _BASE.get(de), _BASE.get(a)
    if orixe is None or destino is None or orixe[0] != destino[0]:
        return None
    return cantidade * orixe[1] / destino[1]


def nome_para_codigo(nome: str) -> str:
    """'Pemento de Padrón' -> 'PEMENTO': primeira palabra, sen acentos, ata 10 letras."""
    sen_acentos = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    palabras = "".join(c if c.isalnum() else " " for c in sen_acentos).split()
    return palabras[0].upper()[:10] if palabras else "LOTE"


def propor_codigo(session: Session, horta_id: int, nome: str, data: date) -> str:
    """Primeiro código libre do tipo AAAA-PRODUTO-NNN (p.ex. 2026-PATACA-001)."""
    prefixo = f"{data.year}-{nome_para_codigo(nome)}-"
    existentes = {c for (c,) in session.query(Lote.codigo).filter(
        Lote.horta_id == horta_id, Lote.codigo.like(f"{prefixo}%"))}
    numero = 1
    while f"{prefixo}{numero:03d}" in existentes:
        numero += 1
    return f"{prefixo}{numero:03d}"


def lote_para_entrada(
    session: Session, horta_id: int, codigo: str, produto: str, unidade: str, data: date,
    cultivo_siex_codigo: int | None = None, produto_animal: str | None = None,
    protexido: bool = False,
) -> Lote:
    """O lote onde entra unha colleita ou produción: o que ten ese código, se é o mesmo
    produto, ou un novo. Non garda (commit): faino quen apunta a entrada."""
    codigo = codigo.strip()
    if not codigo:
        raise OperacionNonPermitidaError("O lote non pode quedar baleiro")
    lote = session.query(Lote).filter_by(horta_id=horta_id, codigo=codigo).one_or_none()
    if lote is None:
        lote = Lote(horta_id=horta_id, codigo=codigo, produto=produto, unidade=unidade,
                    data=data, cultivo_siex_codigo=cultivo_siex_codigo,
                    produto_animal=produto_animal, protexido=protexido,
                    categoria_venda_directa=_CATEGORIA_ANIMAL.get(produto_animal or ""))
        session.add(lote)
        session.flush()
        return lote
    mesmo = (lote.produto_animal == produto_animal if produto_animal is not None
             else lote.produto_animal is None and (
                 lote.cultivo_siex_codigo == cultivo_siex_codigo if cultivo_siex_codigo
                 else lote.produto.strip().lower() == produto.strip().lower()))
    if not mesmo:
        raise OperacionNonPermitidaError(
            f"O lote {codigo} xa existe e é doutro produto ({lote.produto})")
    if converter(1, unidade, lote.unidade) is None:
        raise OperacionNonPermitidaError(
            f"O lote {codigo} vai en {lote.unidade}: apunta a cantidade nesa unidade")
    lote.data = min(lote.data, data)
    return lote


def _entradas(session: Session, lote_id: int) -> list[tuple[float, str]]:
    colleitas = session.query(Colleita.cantidade, Colleita.unidade).filter_by(
        lote_id=lote_id, baixa=False)
    producions = session.query(ProducionAnimal.cantidade - func.coalesce(
        ProducionAnimal.retirada, 0), ProducionAnimal.unidade).filter_by(
        lote_id=lote_id, baixa=False)
    return [(float(c), u) for c, u in [*colleitas, *producions]]


def _na_unidade(lote: Lote, cantidades: list[tuple[float, str]]) -> float:
    return sum(converter(c, u, lote.unidade) or 0 for c, u in cantidades)


def entrado(session: Session, lote: Lote) -> float:
    return _na_unidade(lote, _entradas(session, lote.id))


def saido(session: Session, lote: Lote, excepto_saida: int | None = None) -> float:
    consulta = session.query(LoteSaida.cantidade, LoteSaida.unidade).filter_by(
        lote_id=lote.id, baixa=False)
    if excepto_saida is not None:
        consulta = consulta.filter(LoteSaida.id != excepto_saida)
    return _na_unidade(lote, [(float(c), u) for c, u in consulta])


def queda(session: Session, lote: Lote) -> float:
    return entrado(session, lote) - saido(session, lote)


def comprobar_entrada(session: Session, lote_id: int, cantidade_antes: float,
                      cantidade_despois: float, unidade: str) -> None:
    """Unha entrada (colleita ou produción) non pode baixar por debaixo do que xa saíu do
    lote. cantidade_despois = 0 ao dala de baixa."""
    lote = session.get(Lote, lote_id)
    if lote is None:
        return
    baixa = (converter(cantidade_antes, unidade, lote.unidade) or 0) - (
        converter(cantidade_despois, unidade, lote.unidade) or 0)
    if baixa > 0 and entrado(session, lote) - baixa < saido(session, lote) - 1e-9:
        raise OperacionNonPermitidaError(
            f"Do lote {lote.codigo} xa saíron {saido(session, lote):g} {lote.unidade}: "
            "non pode entrar menos ca iso")


def listar_lotes(session: Session, actor: Usuario, horta_id: int) -> list[Lote]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Lote).filter_by(horta_id=horta_id, baixa=False)
                .order_by(Lote.data.desc(), Lote.id.desc()))


def resumo_lotes(session: Session, actor: Usuario, horta_id: int
                 ) -> dict[int, tuple[float, float, float]]:
    """Para cada lote: entrou, saíu e queda, na unidade do lote."""
    resumo = {}
    for lote in listar_lotes(session, actor, horta_id):
        dentro, fora = entrado(session, lote), saido(session, lote)
        resumo[lote.id] = (dentro, fora, dentro - fora)
    return resumo


def actualizar_lote(session: Session, actor: Usuario, lote: Lote,
                    categoria_venda_directa: str | None, protexido: bool) -> Lote:
    """A categoría da venda directa e se é de invernadoiro (para os máximos do anexo II)."""
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_ESCRITURA)
    if categoria_venda_directa not in (None, *CATEGORIAS_VENDA_DIRECTA):
        raise OperacionNonPermitidaError("Categoría da venda directa descoñecida")
    lote.categoria_venda_directa = categoria_venda_directa
    lote.protexido = protexido
    session.commit()
    return lote


@dataclass
class DatosSaida:
    lote_id: int
    data: date
    tipo: str
    cantidade: float
    unidade: str
    persoa_id: int | None
    data_fin: date | None = None
    canle: str | None = None
    lugar: str | None = None
    comprador_id: int | None = None
    albaran_factura: str | None = None
    importe: float | None = None
    data_pago: date | None = None
    horas: float | None = None
    maquina_id: int | None = None
    notas: str | None = None


def _lote(session: Session, lote_id: int) -> Lote:
    lote = session.get(Lote, lote_id)
    if lote is None or lote.baixa:
        raise OperacionNonPermitidaError("Ese lote non existe")
    return lote


def _validar(session: Session, datos: DatosSaida, lote: Lote, hoxe: date,
             excepto_id: int | None) -> None:
    if datos.tipo not in TIPOS_SAIDA:
        raise OperacionNonPermitidaError("Escolle a onde vai: venda, casa...")
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    cantidade = converter(datos.cantidade, datos.unidade, lote.unidade)
    if cantidade is None:
        raise OperacionNonPermitidaError(f"O lote vai en {lote.unidade}")
    fin = datos.data_fin or datos.data
    if fin < datos.data:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if fin > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data < lote.data:
        raise OperacionNonPermitidaError(
            f"O lote empezou o {lote.data:%d/%m/%Y}: a saída non pode ser anterior")
    disponible = entrado(session, lote) - saido(session, lote, excepto_id)
    if cantidade > disponible + 1e-9:
        raise OperacionNonPermitidaError(
            f"Do lote {lote.codigo} só quedan {disponible:g} {lote.unidade}")
    comprobar_quen(session, lote.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, lote.horta_id, datos.maquina_id)
    if datos.tipo != "venda":
        return
    if datos.canle not in CANLES:
        raise OperacionNonPermitidaError("Indica a quen ou onde se vendeu")
    if datos.canle in _CON_COMPRADOR and datos.comprador_id is None:
        raise OperacionNonPermitidaError("Indica a que tenda, almacén ou cooperativa")
    # Decreto 125/2014 art. 7.3
    if datos.canle == "tenda" and lote.categoria_venda_directa == "ovos":
        raise OperacionNonPermitidaError("Os ovos non se poden vender a tendas")
    if datos.importe is not None and datos.importe < 0:
        raise OperacionNonPermitidaError("O prezo non pode ser negativo")
    comprobar_pago(fin, datos.data_pago, hoxe)
    persoa_co_papel(session, lote.horta_id, datos.comprador_id, "cliente")


def _copiar(saida: LoteSaida, datos: DatosSaida, lote: Lote) -> None:
    venda = datos.tipo == "venda"
    saida.horta_id = lote.horta_id
    saida.lote_id = lote.id
    saida.data = datos.data
    saida.data_fin = datos.data_fin or datos.data
    saida.tipo = datos.tipo
    saida.cantidade = datos.cantidade
    saida.unidade = datos.unidade
    # Cada tipo garda só os seus datos
    saida.canle = datos.canle if venda else None
    saida.lugar = (datos.lugar or None) if venda else None
    saida.comprador_id = datos.comprador_id if venda else None
    saida.albaran_factura = (datos.albaran_factura or None) if venda else None
    saida.importe = datos.importe if venda else None
    saida.data_pago = datos.data_pago if venda else None
    saida.persoa_id = datos.persoa_id
    saida.horas = datos.horas
    saida.maquina_id = datos.maquina_id
    saida.notas = datos.notas or None


def crear_saida(session: Session, actor: Usuario, datos: DatosSaida,
                hoxe: date | None = None) -> LoteSaida:
    lote = _lote(session, datos.lote_id)
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, lote, hoxe or date.today(), None)
    saida = LoteSaida(creado_por=actor.id)
    _copiar(saida, datos, lote)
    session.add(saida)
    session.commit()
    return saida


def actualizar_saida(session: Session, actor: Usuario, saida: LoteSaida, datos: DatosSaida,
                     hoxe: date | None = None) -> LoteSaida:
    if saida.baixa:
        raise OperacionNonPermitidaError("Unha saída dada de baixa non se pode modificar")
    comprobar_rol_horta(session, saida.horta_id, actor, _ROLES_ESCRITURA)
    lote = _lote(session, datos.lote_id)
    if lote.horta_id != saida.horta_id:
        raise OperacionNonPermitidaError("Ese lote non é desta explotación")
    _validar(session, datos, lote, hoxe or date.today(), saida.id)
    _copiar(saida, datos, lote)
    session.commit()
    return saida


def dar_de_baixa_saida(session: Session, actor: Usuario, saida: LoteSaida) -> None:
    comprobar_rol_horta(session, saida.horta_id, actor, _ROLES_ESCRITURA)
    saida.baixa = True
    session.commit()


def listar_saidas(session: Session, actor: Usuario, horta_id: int,
                  lote_id: int | None = None) -> list[LoteSaida]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(LoteSaida).filter_by(horta_id=horta_id, baixa=False)
    if lote_id is not None:
        consulta = consulta.filter_by(lote_id=lote_id)
    return list(consulta.order_by(LoteSaida.data.desc(), LoteSaida.id.desc()))


def vendido_no_ano(session: Session, horta_id: int, categoria: str, ano: int,
                   excepto_id: int | None = None) -> float:
    """Venda directa do ano nesa categoría (Decreto 125/2014), na unidade do anexo II."""
    unidade = CATEGORIAS_VENDA_DIRECTA[categoria][3]
    consulta = (session.query(LoteSaida.cantidade, LoteSaida.unidade)
                .join(Lote, Lote.id == LoteSaida.lote_id)
                .filter(LoteSaida.horta_id == horta_id, LoteSaida.baixa.is_(False),
                        LoteSaida.tipo == "venda", LoteSaida.canle.in_(CANLES_DIRECTAS),
                        Lote.categoria_venda_directa == categoria,
                        LoteSaida.data >= date(ano, 1, 1), LoteSaida.data <= date(ano, 12, 31)))
    if excepto_id is not None:
        consulta = consulta.filter(LoteSaida.id != excepto_id)
    return sum(converter(float(c), u, unidade) or 0 for c, u in consulta)


def avisos_saida(session: Session, actor: Usuario, datos: DatosSaida,
                 excepto_id: int | None = None) -> list[str]:
    """Avisos que non bloquean: máximo anual da venda directa, tempo de espera dos animais e
    prazo de seguridade dos tratamentos."""
    from horta.services.fito_consulta import aviso_prazo_colleita
    from horta.services.producions_animais import aviso_tempo_espera

    lote = session.get(Lote, datos.lote_id)
    if lote is None:
        return []
    avisos = []
    categoria = lote.categoria_venda_directa
    if (datos.tipo == "venda" and datos.canle in CANLES_DIRECTAS and categoria
            and datos.cantidade):
        nome, maximo, maximo_protexido, unidade = CATEGORIAS_VENDA_DIRECTA[categoria]
        limite = maximo_protexido if lote.protexido and maximo_protexido else maximo
        total = vendido_no_ano(session, lote.horta_id, categoria, datos.data.year,
                               excepto_id) + (converter(datos.cantidade, datos.unidade,
                                                        unidade) or 0)
        if total > limite:
            avisos.append(
                f"Con esta venda levas {total:g} {unidade} de {nome.lower()} en venda directa "
                f"este ano: o máximo son {limite:g} {unidade} (Decreto 125/2014). Pasado iso "
                "precisas outro rexistro sanitario.")
    for pr in session.query(ProducionAnimal).filter_by(lote_id=lote.id, baixa=False):
        aviso = aviso_tempo_espera(session, actor, lote.horta_id, pr.animal_id, pr.data,
                                   pr.data_fin)
        if aviso:
            avisos.append(aviso)
            break
    for col in session.query(Colleita).filter_by(lote_id=lote.id, baixa=False):
        aviso = aviso_prazo_colleita(session, col.cultivo_id, col.data)
        if aviso:
            avisos.append(aviso)
            break
    return avisos


def ten_saidas(session: Session, lote_id: int) -> bool:
    return session.query(LoteSaida).filter_by(lote_id=lote_id, baixa=False).first() is not None


def cultivo_protexido(cultivo: Cultivo) -> bool:
    return (cultivo.sistema_cultivo or "") in SISTEMAS_PROTEXIDOS

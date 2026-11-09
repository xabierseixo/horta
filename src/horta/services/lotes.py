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

from horta.idiomas import N_
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.lote import (
    Clasificacion,
    Lote,
    LoteSaida,
    Mestura,
    MesturaOrixe,
    ProdutoVenda,
    Transformacion,
    TransformacionEntrada,
)
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
    "explotacion": N_("Na explotación"),
    "mercado": N_("Nun mercado"),
    "domicilio": N_("A domicilio"),
    "tenda": N_("A unha tenda"),
    "almacen": N_("A un almacén ou cooperativa"),
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
# Como se agrupa cada produto en lotes: a lei
# (Directiva 2011/91/UE) deixa decidir ao produtor; o sector fai un por colleita
AGRUPACIONS: dict[str, str] = {
    "colleita": "Un lote por colleita",
    "dia": "Un lote por día",
    "semana": "Un lote por semana",
    "mes": "Un lote por mes",
    "man": "Escríboo eu",
}


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
        ficha = ficha_para(session, horta_id, produto, unidade, cultivo_siex_codigo,
                           produto_animal)
        lote = Lote(horta_id=horta_id, codigo=codigo, produto=produto, unidade=unidade,
                    data=data, cultivo_siex_codigo=cultivo_siex_codigo,
                    produto_animal=produto_animal, protexido=protexido,
                    produto_venda_id=ficha.id)
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
    if produto_animal is None and lote.protexido != protexido:
        # A venda directa ten máximos distintos para cada un (G6)
        onde = "de invernadoiro" if lote.protexido else "ao aire libre"
        raise OperacionNonPermitidaError(
            f"O lote {codigo} é {onde}: as colleitas de invernadoiro e as de aire libre "
            "van en lotes distintos")
    lote.data = min(lote.data, data)
    return lote


def ficha_para(session: Session, horta_id: int, nome: str, unidade: str,
               cultivo_siex_codigo: int | None = None, produto_animal: str | None = None,
               crear: bool = True) -> ProdutoVenda:
    """A ficha do produto que sae: a do mesmo cultivo oficial, produto animal ou nome; se non
    hai, unha nova (non garda: faino quen apunta; con crear=False non se engade á sesión)."""
    consulta = session.query(ProdutoVenda).filter_by(horta_id=horta_id)
    if cultivo_siex_codigo:
        ficha = consulta.filter_by(cultivo_siex_codigo=cultivo_siex_codigo).first()
    elif produto_animal:
        ficha = consulta.filter_by(produto_animal=produto_animal).first()
    else:
        ficha = next((f for f in consulta.filter_by(cultivo_siex_codigo=None,
                                                    produto_animal=None)
                      if f.nome.strip().lower() == nome.strip().lower()), None)
    if ficha is None:
        ficha = ProdutoVenda(horta_id=horta_id, nome=nome.strip(), unidade=unidade,
                             cultivo_siex_codigo=cultivo_siex_codigo,
                             produto_animal=produto_animal, agrupacion="colleita",
                             categoria_venda_directa=_CATEGORIA_ANIMAL.get(produto_animal or ""))
        if crear:
            session.add(ficha)
            session.flush()
    return ficha


def codigo_por_agrupacion(session: Session, ficha: ProdutoVenda, data: date) -> str:
    """O código que lle toca a unha colleita ou produción segundo como se agrupa o produto:
    se é por día, semana ou mes, o mesmo código ata que cambie o período."""
    base = f"{data.year}-{nome_para_codigo(ficha.nome)}-"
    if ficha.agrupacion == "dia":
        return f"{base}{data:%m%d}"
    if ficha.agrupacion == "semana":
        ano, semana, _ = data.isocalendar()
        return f"{ano}-{nome_para_codigo(ficha.nome)}-S{semana:02d}"
    if ficha.agrupacion == "mes":
        return f"{base}M{data:%m}"
    return propor_codigo(session, ficha.horta_id, ficha.nome, data)


def ficha_do_lote(session: Session, lote: Lote) -> ProdutoVenda:
    ficha = session.get(ProdutoVenda, lote.produto_venda_id)
    assert ficha is not None
    return ficha


def clases_da_ficha(ficha: ProdutoVenda) -> list[str]:
    return [c.strip() for c in (ficha.clases or "").split(";") if c.strip()]


def _entradas(session: Session, lote_id: int) -> list[tuple[float, str]]:
    colleitas = session.query(Colleita.cantidade, Colleita.unidade).filter_by(
        lote_id=lote_id, baixa=False)
    producions = session.query(ProducionAnimal.cantidade - func.coalesce(
        ProducionAnimal.retirada, 0), ProducionAnimal.unidade).filter_by(
        lote_id=lote_id, baixa=False)
    lista = [(float(c), u) for c, u in [*colleitas, *producions]]
    # O que entrou dunha mestura, na unidade de cada lote de orixe
    for cantidade, unidade in (session.query(MesturaOrixe.cantidade, Lote.unidade)
                               .join(Mestura, Mestura.id == MesturaOrixe.mestura_id)
                               .join(Lote, Lote.id == MesturaOrixe.lote_id)
                               .filter(Mestura.lote_id == lote_id, Mestura.baixa.is_(False))):
        lista.append((float(cantidade), unidade))
    # O que saíu dunha transformación
    for cantidade, unidade in (session.query(Transformacion.cantidade, Lote.unidade)
                               .join(Lote, Lote.id == Transformacion.lote_id)
                               .filter(Transformacion.lote_id == lote_id,
                                       Transformacion.baixa.is_(False))):
        lista.append((float(cantidade), unidade))
    return lista


@dataclass
class Movementos:
    """O que saíu dun lote, por clase (None = sen clase)."""

    clasificado: dict[str, float]
    refugo: float
    saido: dict[str | None, float]


def _movementos(session: Session, lote: Lote, excepto_saida: int | None = None,
                excepto_clasificacion: int | None = None) -> Movementos:
    clasificado: dict[str, float] = {}
    refugo = 0.0
    for cl in session.query(Clasificacion).filter_by(lote_id=lote.id, baixa=False):
        if cl.id == excepto_clasificacion:
            continue
        refugo += cl.refugo or 0
        for linea in cl.clases:
            clasificado[linea.clase] = clasificado.get(linea.clase, 0) + linea.cantidade
    saido: dict[str | None, float] = {}
    for s in session.query(LoteSaida).filter_by(lote_id=lote.id, baixa=False):
        if s.id != excepto_saida:
            saido[s.clase] = saido.get(s.clase, 0) + (
                converter(s.cantidade, s.unidade, lote.unidade) or 0)
    for orixe in (session.query(MesturaOrixe)
                  .join(Mestura, Mestura.id == MesturaOrixe.mestura_id)
                  .filter(MesturaOrixe.lote_id == lote.id, Mestura.baixa.is_(False))):
        saido[orixe.clase] = saido.get(orixe.clase, 0) + orixe.cantidade
    for entrada in (session.query(TransformacionEntrada)
                    .join(Transformacion, Transformacion.id ==
                          TransformacionEntrada.transformacion_id)
                    .filter(TransformacionEntrada.lote_id == lote.id,
                            Transformacion.baixa.is_(False))):
        saido[entrada.clase] = saido.get(entrada.clase, 0) + entrada.cantidade
    return Movementos(clasificado, refugo, saido)


def queda_por_clase(session: Session, lote: Lote, excepto_saida: int | None = None,
                    excepto_clasificacion: int | None = None) -> dict[str | None, float]:
    """O que queda de cada clase e sen clasificar (None), na unidade do lote."""
    mov = _movementos(session, lote, excepto_saida, excepto_clasificacion)
    queda: dict[str | None, float] = {
        None: entrado(session, lote) - sum(mov.clasificado.values()) - mov.refugo
        - mov.saido.get(None, 0)}
    for clase in {*mov.clasificado, *(c for c in mov.saido if c is not None)}:
        queda[clase] = mov.clasificado.get(clase, 0) - mov.saido.get(clase, 0)
    return {k: round(v, 6) for k, v in queda.items()}


def _na_unidade(lote: Lote, cantidades: list[tuple[float, str]]) -> float:
    return sum(converter(c, u, lote.unidade) or 0 for c, u in cantidades)


def entrado(session: Session, lote: Lote) -> float:
    return _na_unidade(lote, _entradas(session, lote.id))


def saido(session: Session, lote: Lote, excepto_saida: int | None = None) -> float:
    """Saídas, mesturas noutros lotes e refugo das clasificacións."""
    mov = _movementos(session, lote, excepto_saida)
    return sum(mov.saido.values()) + mov.refugo


def queda(session: Session, lote: Lote) -> float:
    return entrado(session, lote) - saido(session, lote)


def comprobar_entrada(
    session: Session,
    lote_id: int,
    cantidade_antes: float,
    unidade_antes: str,
    cantidade_despois: float,
    unidade_despois: str | None = None,
) -> None:
    """Unha entrada (colleita ou produción) non pode baixar por debaixo do que xa saíu do
    lote. cantidade_despois = 0 ao dala de baixa."""
    lote = session.get(Lote, lote_id)
    if lote is None:
        return
    baixa = (converter(cantidade_antes, unidade_antes, lote.unidade) or 0) - (
        converter(cantidade_despois, unidade_despois or unidade_antes, lote.unidade) or 0)
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


def actualizar_lote(session: Session, actor: Usuario, lote: Lote, protexido: bool) -> Lote:
    """Se é de invernadoiro (para os máximos do anexo II)."""
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_ESCRITURA)
    lote.protexido = protexido
    session.commit()
    return lote


def listar_fichas(session: Session, actor: Usuario, horta_id: int) -> list[ProdutoVenda]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return sorted(session.query(ProdutoVenda).filter_by(horta_id=horta_id),
                  key=lambda f: f.nome.lower())


def actualizar_ficha(session: Session, actor: Usuario, ficha: ProdutoVenda, nome: str,
                     categoria_venda_directa: str | None, clases: list[str],
                     agrupacion: str) -> ProdutoVenda:
    """Nome, categoría da venda directa, clases e como se agrupa en lotes."""
    comprobar_rol_horta(session, ficha.horta_id, actor, _ROLES_ESCRITURA)
    if not nome.strip():
        raise OperacionNonPermitidaError("O nome non pode quedar baleiro")
    if categoria_venda_directa not in (None, *CATEGORIAS_VENDA_DIRECTA):
        raise OperacionNonPermitidaError("Categoría da venda directa descoñecida")
    if agrupacion not in AGRUPACIONS:
        raise OperacionNonPermitidaError("Escolle como se fan os lotes")
    limpas = list(dict.fromkeys(c.strip() for c in clases if c.strip()))
    if any(";" in c or len(c) > 60 for c in limpas):
        raise OperacionNonPermitidaError("Cada clase, sen «;» e ata 60 letras")
    ficha.nome = nome.strip()
    ficha.categoria_venda_directa = categoria_venda_directa
    ficha.clases = ";".join(limpas) or None
    ficha.agrupacion = agrupacion
    session.commit()
    return ficha


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
    clase: str | None = None
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
    queda_clases = queda_por_clase(session, lote, excepto_id)
    disponible = queda_clases.get(datos.clase)
    if disponible is None:
        raise OperacionNonPermitidaError(f"O lote {lote.codigo} non ten a clase «{datos.clase}»")
    if cantidade > disponible + 1e-9:
        de = f" de {datos.clase}" if datos.clase else (
            " sen clasificar" if len(queda_clases) > 1 else "")
        raise OperacionNonPermitidaError(
            f"Do lote {lote.codigo} só quedan {disponible:g} {lote.unidade}{de}")
    comprobar_quen(session, lote.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, lote.horta_id, datos.maquina_id)
    if datos.tipo != "venda":
        return
    if datos.canle not in CANLES:
        raise OperacionNonPermitidaError("Indica a quen ou onde se vendeu")
    if datos.canle in _CON_COMPRADOR and datos.comprador_id is None:
        raise OperacionNonPermitidaError("Indica a que tenda, almacén ou cooperativa")
    # Decreto 125/2014 art. 7.3
    if datos.canle == "tenda" and ficha_do_lote(session, lote).categoria_venda_directa == "ovos":
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
    saida.clase = datos.clase or None
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
                .join(ProdutoVenda, ProdutoVenda.id == Lote.produto_venda_id)
                .filter(LoteSaida.horta_id == horta_id, LoteSaida.baixa.is_(False),
                        LoteSaida.tipo == "venda", LoteSaida.canle.in_(CANLES_DIRECTAS),
                        ProdutoVenda.categoria_venda_directa == categoria,
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
    categoria = ficha_do_lote(session, lote).categoria_venda_directa
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

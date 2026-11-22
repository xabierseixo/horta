from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.tratamento_fito import (
    TIPOS_PROBLEMA,
    TratamentoAplicador,
    TratamentoAsesor,
    TratamentoCultivo,
    TratamentoFito,
    TratamentoMedida,
    TratamentoProblema,
    TratamentoProduto,
    TratamentoXustificacion,
)
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import ropo_vixente
from horta.services.produtos import comprobar_entrada_do_produto, produto_ou_novo

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass
class LinhaCultivo:
    cultivo_id: int
    superficie_ha: float | None
    estado_fenoloxico: str | None = None


@dataclass
class Problema:
    tipo: str
    codigo: str


@dataclass
class LinhaProduto:
    tipo_produto: str
    unidade: str
    num_rexistro: str | None = None
    nome_comercial: str | None = None
    materia_activa: str | None = None
    dose: float | None = None
    cantidade: float | None = None
    # De que compra saíu, se se sabe (o produto lígase só polo nº de rexistro ou o nome)
    entrada_id: int | None = None


@dataclass
class LinhaMedida:
    tipo_medida: str
    cantidade: float | None = None
    unidade: str | None = None
    num_rexistro_mdf: str | None = None
    boas_practicas: str | None = None


@dataclass
class LinhaAplicador:
    persoa_id: int
    maquina_id: int | None = None
    aplicacion_manual: bool = False
    horas_utilizacion: float | None = None
    num_repeticions: int | None = None
    duracion: float | None = None


@dataclass
class DatosAsesor:
    persoa_id: int
    data: date | None = None
    validacion: bool = False
    observacions: str | None = None
    confirmacion: bool = False
    contrato: bool = False


@dataclass
class DatosTratamento:
    data_inicio: date
    data_fin: date
    cultivos: list[LinhaCultivo]
    problemas: list[Problema]
    xustificacions: list[str]
    produtos: list[LinhaProduto] = field(default_factory=list)
    medidas: list[LinhaMedida] = field(default_factory=list)
    aplicadores: list[LinhaAplicador] = field(default_factory=list)
    hora: time | None = None
    asesor: DatosAsesor | None = None
    eficacia: str | None = None
    notas: str | None = None
    actividade_cuberta: str | None = None


def _erro(mensaxe: str) -> OperacionNonPermitidaError:
    return OperacionNonPermitidaError(mensaxe)


def _validar(session: Session, horta: Horta, datos: DatosTratamento) -> None:
    profesional = horta.uso_profesional
    d = datos.data_inicio
    if datos.data_fin < datos.data_inicio:
        raise _erro("A data de fin non pode ser anterior á de inicio")
    if not datos.cultivos:
        raise _erro("Indica polo menos un cultivo tratado")
    especies: set[tuple[str, str | None]] = set()
    for linha in datos.cultivos:
        cultivo = session.get(Cultivo, linha.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None or parcela.horta_id != horta.id:
            raise _erro("O cultivo indicado non pertence a esta explotación")
        if cultivo.cultivo_siex_codigo is not None:
            especies.add((str(cultivo.cultivo_siex_codigo), str(cultivo.variedade_siex_id)))
        else:
            especies.add((cultivo.especie.strip().lower(),
                          (cultivo.variedade or "").strip().lower()))
        if linha.superficie_ha is not None:
            if linha.superficie_ha <= 0:
                raise _erro("A superficie tratada ten que ser maior que 0")
            if parcela.superficie and linha.superficie_ha > parcela.superficie:
                raise _erro(f"A superficie tratada é maior ca da parcela {parcela.nome}")
            if cultivo.superficie_ha and linha.superficie_ha > cultivo.superficie_ha:
                raise _erro(f"A superficie tratada é maior ca do cultivo {cultivo.especie}")
        if linha.estado_fenoloxico:
            validar_codigo(session, "estado_fenoloxico", linha.estado_fenoloxico, d)
    if len(especies) > 1:
        raise _erro("Todos os cultivos dun tratamento teñen que ser do mesmo cultivo e variedade")
    if not datos.problemas:
        raise _erro("Indica polo menos un problema (praga, enfermidade, mala herba ou regulador)")
    for problema in datos.problemas:
        if problema.tipo not in TIPOS_PROBLEMA:
            raise _erro(f"Tipo de problema descoñecido: {problema.tipo}")
        validar_codigo(session, problema.tipo, problema.codigo, d)
    if profesional and not datos.xustificacions:
        raise _erro("Indica polo menos unha xustificación do tratamento")
    for codigo in datos.xustificacions:
        validar_codigo(session, "xustificacion", codigo, d)
    if not datos.produtos and not datos.medidas:
        raise _erro("Indica polo menos un produto ou unha medida non química")
    for produto in datos.produtos:
        if not produto.unidade:
            raise _erro("Indica a unidade da dose ou cantidade do produto")
        if (produto.dose is None) == (produto.cantidade is None):
            raise _erro("Indica a dose ou a cantidade do produto (só unha das dúas)")
        valor = produto.dose if produto.dose is not None else produto.cantidade
        if valor is not None and valor <= 0:
            raise _erro("A dose ou cantidade ten que ser maior que 0")
        validar_codigo(session, "tipo_produto", produto.tipo_produto, d)
        validar_codigo(session, "unidade_medida", produto.unidade, d)
        if profesional and produto.tipo_produto == "1" and not produto.num_rexistro:
            raise _erro("Os produtos fitosanitarios rexistrados precisan o nº de rexistro")
    for medida in datos.medidas:
        validar_codigo(session, "tipo_medida_fito", medida.tipo_medida, d)
    if profesional and not datos.aplicadores:
        raise _erro("Indica polo menos un aplicador")
    for linha_aplicador in datos.aplicadores:
        persoa = session.get(Persoa, linha_aplicador.persoa_id)
        if persoa is None or persoa.horta_id != horta.id or not persoa.ten_papel("aplicador"):
            raise _erro("O aplicador indicado non é un aplicador desta explotación")
        if not persoa.activa:
            raise _erro(f"{persoa.nome} está desactivado/a e non pode figurar como aplicador")
        if profesional and not ropo_vixente(persoa, d):
            raise _erro(
                f"O carné ROPO de {persoa.nome} caducou o "
                f"{persoa.ropo_caducidade:%d/%m/%Y}" if persoa.ropo_caducidade
                else f"{persoa.nome} non ten data de caducidade do carné ROPO"
            )
        if linha_aplicador.maquina_id is not None:
            maquina = session.get(Maquina, linha_aplicador.maquina_id)
            if maquina is None or maquina.horta_id != horta.id:
                raise _erro("A máquina indicada non é desta explotación")
            if not maquina.activa:
                raise _erro(f"A máquina {maquina.alias} está desactivada")
    if datos.asesor is not None:
        asesor = session.get(Persoa, datos.asesor.persoa_id)
        if asesor is None or asesor.horta_id != horta.id or not asesor.ten_papel("asesor"):
            raise _erro("O asesor indicado non é un asesor desta explotación")
    if datos.eficacia:
        validar_codigo(session, "eficacia", datos.eficacia, d)


def _aplicar(tratamento: TratamentoFito, datos: DatosTratamento) -> None:
    tratamento.data_inicio = datos.data_inicio
    tratamento.data_fin = datos.data_fin
    tratamento.hora = datos.hora
    tratamento.eficacia = datos.eficacia
    tratamento.notas = datos.notas
    tratamento.actividade_cuberta = datos.actividade_cuberta
    tratamento.cultivos = [TratamentoCultivo(cultivo_id=c.cultivo_id, superficie_ha=c.superficie_ha,
                                             estado_fenoloxico=c.estado_fenoloxico)
                           for c in datos.cultivos]
    tratamento.problemas = [TratamentoProblema(tipo=p.tipo, codigo=p.codigo)
                            for p in datos.problemas]
    tratamento.xustificacions = [TratamentoXustificacion(codigo=c) for c in datos.xustificacions]
    tratamento.produtos = [TratamentoProduto(**vars(p)) for p in datos.produtos]
    tratamento.medidas = [TratamentoMedida(**vars(m)) for m in datos.medidas]
    tratamento.aplicadores = [TratamentoAplicador(**vars(a)) for a in datos.aplicadores]
    tratamento.asesor = TratamentoAsesor(**vars(datos.asesor)) if datos.asesor else None


def _ligar_produtos(session: Session, actor: Usuario, horta_id: int,
                    tratamento: TratamentoFito) -> None:
    """Cada fitosanitario do tratamento é un produto da explotación (polo nº de rexistro ou o
    nome): así se contan as existencias. A compra, se se indicou, ten que ser dese produto."""
    for linha in tratamento.produtos:
        if not (linha.num_rexistro or linha.nome_comercial):
            continue
        produto = produto_ou_novo(session, actor, horta_id, "fitosanitario",
                                  linha.nome_comercial or linha.num_rexistro or "",
                                  "litros", num_rexistro=linha.num_rexistro)
        linha.produto_id = produto.id
        comprobar_entrada_do_produto(session, horta_id, linha.entrada_id, produto.id)


def crear_tratamento_fito(
    session: Session, actor: Usuario, horta_id: int, datos: DatosTratamento
) -> TratamentoFito:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    horta = session.get(Horta, horta_id)
    assert horta is not None
    _validar(session, horta, datos)
    tratamento = TratamentoFito(horta_id=horta_id, data_inicio=datos.data_inicio,
                                data_fin=datos.data_fin, creado_por=actor.id)
    _aplicar(tratamento, datos)
    _ligar_produtos(session, actor, horta_id, tratamento)
    session.add(tratamento)
    session.commit()
    return tratamento


def actualizar_tratamento_fito(
    session: Session, actor: Usuario, tratamento: TratamentoFito, datos: DatosTratamento
) -> TratamentoFito:
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    horta = session.get(Horta, tratamento.horta_id)
    assert horta is not None
    _validar(session, horta, datos)
    _aplicar(tratamento, datos)
    _ligar_produtos(session, actor, tratamento.horta_id, tratamento)
    session.commit()
    return tratamento


def dar_de_baixa_tratamento_fito(
    session: Session, actor: Usuario, tratamento: TratamentoFito
) -> None:
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    tratamento.baixa = True
    session.commit()


def listar_tratamentos_fito(
    session: Session, actor: Usuario, horta_id: int
) -> list[TratamentoFito]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(TratamentoFito)
        .filter_by(horta_id=horta_id, baixa=False)
        .order_by(TratamentoFito.data_inicio.desc(), TratamentoFito.id.desc())
        .all()
    )


def faltas_para_cue(tratamento: TratamentoFito) -> list[str]:
    """O que lle falta a un tratamento (p.ex. migrado ou de autoconsumo) para o CUE."""
    faltas = []
    if not tratamento.problemas:
        faltas.append("problema fitosanitario codificado")
    if not tratamento.xustificacions:
        faltas.append("xustificación")
    if not tratamento.produtos and not tratamento.medidas:
        faltas.append("produto ou medida codificados")
    if not tratamento.aplicadores:
        faltas.append("aplicador")
    if tratamento.eficacia is None:
        faltas.append("eficacia")
    return faltas

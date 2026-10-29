"""Diario de traballos: todo o feito e o por facer nunha soa lista. Le os rexistros de cada
tipo de traballo (cada un na súa táboa) e devolve a parte común: que, cando, onde, quen e
estado."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados
from horta.services.analises import listar_analises
from horta.services.animais import ESPECIES, listar_animais
from horta.services.catalogos import describir
from horta.services.coidados_animais import TIPOS_COIDADO, listar_coidados
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import listar_cultivos
from horta.services.labores import listar_labores
from horta.services.lotes import CANLES, TIPOS_SAIDA, listar_lotes, listar_saidas
from horta.services.movementos_animais import TIPOS_MOVEMENTO, listar_movementos
from horta.services.pastoreos import listar_pastoreos
from horta.services.persoas import listar_persoas
from horta.services.producions_animais import PRODUTOS, listar_producions
from horta.services.produtos import listar_entradas, listar_produtos
from horta.services.regas import listar_regas
from horta.services.tarefas import listar_tarefas
from horta.services.tratamentos_fito import listar_tratamentos_fito
from horta.services.tratamentos_instalacion import listar_tratamentos_instalacion

# Tipos de traballo, na orde en que se ofrecen ao apuntar
TIPOS: dict[str, str] = {
    "tratamento": "Tratamento",
    "abonado": "Abonado",
    "rega": "Rega",
    "labor": "Labor",
    "colleita": "Colleita",
    "sementeira": "Sementeira ou plantación",
    "analise": "Toma de mostras",
    "tratamento_instalacion": "Tratamento en almacén ou instalación",
    "coidado_animal": "Coidado de animais",
    "movemento_animal": "Entrada ou saída de animais",
    "producion_animal": "Produción dos animais",
    "pastoreo": "Pastoreo",
    "lote_saida": "Saída de produto (venda, casa...)",
    "entrada_produto": "Entrada de produto (compra)",
    "tarefa": "Tarefa",
}


@dataclass(frozen=True)
class Traballo:
    tipo: str  # clave de TIPOS
    id: int  # id do rexistro na táboa do seu tipo
    data: date | None  # None: tarefa por facer sen data
    feito: bool
    que: str
    onde: str
    parcelas: frozenset[int]
    atrasado: bool = False
    persoas: tuple[int, ...] = ()  # quen o fixo
    sen_quen: bool = False  # feito e sen saber quen o fixo (rexistros de antes)


def nome_grupo(especie: str, raza: str | None) -> str:
    """Como se nomea un grupo de animais nas listas."""
    return f"{especie} ({raza})" if raza else especie


def _quen(*ids: int | None) -> tuple[int, ...]:
    return tuple(i for i in ids if i is not None)


def listar_traballos(
    session: Session, actor: Usuario, horta_id: int, desde: date | None = None,
    ata: date | None = None, hoxe: date | None = None,
) -> list[Traballo]:
    """Primeiro o por facer (sen data, despois por data); logo o feito no período, do máis
    recente ao máis antigo. O por facer sae sempre, sexa cal sexa o período."""
    hoxe = hoxe or date.today()
    cultivos = {c.id: c for c in listar_cultivos(session, actor, horta_id)}
    parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
    grupos = {a.id: nome_grupo(a.especie, a.raza) for a in listar_animais(session, actor, horta_id)}
    nomes = {p.id: p.nome for p in listar_persoas(session, actor, horta_id, so_activas=False)}
    nomes_produtos = {p.id: p.nome
                      for p in listar_produtos(session, actor, horta_id, so_activos=False)}

    def onde(cultivo_id: int | None) -> str:
        c = cultivos.get(cultivo_id) if cultivo_id else None
        if c is None:
            return ""
        return f"{c.especie} {c.variedade or ''}".strip() + f" — {parcelas.get(c.parcela_id, '')}"

    def parcela_de(cultivo_id: int | None) -> frozenset[int]:
        c = cultivos.get(cultivo_id) if cultivo_id else None
        return frozenset({c.parcela_id}) if c else frozenset()

    def onde_leiras(ids: list[int]) -> str:
        return onde(ids[0]) if len(ids) == 1 else f"{len(ids)} leiras"

    def parcelas_de(ids: list[int]) -> frozenset[int]:
        return frozenset().union(*(parcela_de(i) for i in ids))

    def texto(catalogo: str, codigo: str | None) -> str:
        return describir(session, catalogo, codigo) if codigo else ""

    traballos: list[Traballo] = []
    for t in listar_tratamentos_fito(session, actor, horta_id):
        ids = [tc.cultivo_id for tc in t.cultivos]
        quen = _quen(*(ap.persoa_id for ap in t.aplicadores))
        traballos.append(Traballo(
            "tratamento", t.id, t.data_inicio, True,
            ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
            or ", ".join(texto(p.tipo, p.codigo) for p in t.problemas),
            onde(ids[0]) if len(ids) == 1 else f"{len(ids)} cultivos",
            frozenset().union(*(parcela_de(i) for i in ids)), persoas=quen,
            sen_quen=not quen))
    for a in listar_abonados(session, actor, horta_id):
        abono = session.get(Fertilizante, a.fertilizante_id) if a.fertilizante_id else None
        quen = _quen(a.persoa_id)
        traballos.append(Traballo(
            "abonado", a.id, a.data_inicio, True, abono.nome if abono else "Abonado en verde",
            onde_leiras([le.cultivo_id for le in a.leiras]),
            parcelas_de([le.cultivo_id for le in a.leiras]), persoas=quen,
            sen_quen=not quen))
    for r in listar_regas(session, actor, horta_id):
        traballos.append(Traballo("rega", r.id, r.data_inicio, True,
                                  texto("sistema_rega", r.sistema_rega),
                                  onde_leiras([le.cultivo_id for le in r.leiras]),
                                  parcelas_de([le.cultivo_id for le in r.leiras]),
                                  persoas=_quen(r.persoa_id), sen_quen=r.persoa_id is None))
    for lab in listar_labores(session, actor, horta_id):
        traballos.append(Traballo("labor", lab.id, lab.data_inicio, True,
                                  texto("tipo_labor", lab.tipo_labor),
                                  onde_leiras([le.cultivo_id for le in lab.leiras]),
                                  parcelas_de([le.cultivo_id for le in lab.leiras]),
                                  persoas=_quen(lab.persoa_id), sen_quen=lab.persoa_id is None))
    for col in listar_colleitas(session, actor, horta_id):
        traballos.append(Traballo("colleita", col.id, col.data, True,
                                  f"{col.cantidade:g} {col.unidade} · lote {col.lote}",
                                  onde(col.cultivo_id), parcela_de(col.cultivo_id),
                                  persoas=_quen(col.persoa_id), sen_quen=col.persoa_id is None))
    for c in cultivos.values():
        if c.data_inicio is not None:
            feita = c.data_inicio <= hoxe
            traballos.append(Traballo(
                "sementeira", c.id, c.data_inicio, feita,
                "Plantación" if c.tipo_inicio == "plantacion" else "Sementeira",
                onde(c.id), parcela_de(c.id), persoas=_quen(c.sementeira_persoa_id),
                sen_quen=feita and c.sementeira_persoa_id is None))
    for an in listar_analises(session, actor, horta_id):
        sitio = onde(an.cultivo_id) or parcelas.get(an.parcela_id or 0, "")
        traballos.append(Traballo(
            "analise", an.id, an.data_mostraxe, True,
            texto("material_analizado", an.material_analizado), sitio,
            parcela_de(an.cultivo_id) or (frozenset({an.parcela_id}) if an.parcela_id
                                          else frozenset()),
            persoas=_quen(an.persoa_id), sen_quen=an.persoa_id is None))
    for ti in listar_tratamentos_instalacion(session, actor, horta_id):
        traballos.append(Traballo("tratamento_instalacion", ti.id, ti.data, True,
                                  ti.nome_comercial or ti.materia_activa or "", ti.obxecto,
                                  frozenset(), persoas=_quen(ti.persoa_id),
                                  sen_quen=ti.persoa_id is None))
    for co in listar_coidados(session, actor, horta_id):
        que = TIPOS_COIDADO[co.tipo].split(" (")[0]
        detalle = nomes_produtos.get(co.produto_id or 0) if co.tipo == "medicamento" else (
            nomes.get(co.visitante_id or 0) if co.tipo == "visita" else co.descricion)
        traballos.append(Traballo("coidado_animal", co.id, co.data_inicio, True,
                                  f"{que} — {detalle}" if detalle else que,
                                  grupos.get(co.animal_id, ""), frozenset(),
                                  persoas=_quen(co.persoa_id), sen_quen=co.persoa_id is None))
    for mo in listar_movementos(session, actor, horta_id):
        traballos.append(Traballo("movemento_animal", mo.id, mo.data, True,
                                  f"{TIPOS_MOVEMENTO[mo.tipo].split(' (')[0]}: {mo.cantidade}",
                                  grupos.get(mo.animal_id, ""), frozenset(),
                                  persoas=_quen(mo.persoa_id), sen_quen=mo.persoa_id is None))
    for pr in listar_producions(session, actor, horta_id):
        retirada = f" ({pr.retirada:g} retirados)" if pr.retirada else ""
        traballos.append(Traballo("producion_animal", pr.id, pr.data, True,
                                  f"{PRODUTOS[pr.produto]}: {pr.cantidade:g} {pr.unidade}"
                                  f"{retirada} · lote {pr.lote}",
                                  grupos.get(pr.animal_id, ""), frozenset(),
                                  persoas=_quen(pr.persoa_id), sen_quen=pr.persoa_id is None))
    for pa in listar_pastoreos(session, actor, horta_id):
        animais = ", ".join(
            f"{li.numero} {grupos.get(li.animal_id, '')}" if li.animal_id else
            f"{li.numero} {ESPECIES.get(li.especie_codigo or '', '')} "
            f"({nomes.get(li.propietario_id or 0, '')})"
            for li in pa.animais)
        ata_cando = f"ata o {pa.data_fin:%d/%m/%Y}" if pa.data_fin else "aínda no pasto"
        ids = [le.cultivo_id for le in pa.leiras]
        traballos.append(Traballo("pastoreo", pa.id, pa.data_inicio, True,
                                  f"{animais} · {ata_cando}",
                                  onde(ids[0]) if len(ids) == 1 else f"{len(ids)} leiras",
                                  frozenset().union(*(parcela_de(i) for i in ids)),
                                  persoas=_quen(pa.persoa_id), sen_quen=pa.persoa_id is None))
    for en in listar_entradas(session, actor, horta_id):
        cantidade = f"{en.cantidade:g} {en.unidade} de " if en.cantidade else ""
        traballos.append(Traballo(
            "entrada_produto", en.id, en.data, True,
            f"Entrada: {cantidade}{nomes_produtos.get(en.produto_id, '')}",
            nomes.get(en.provedor_id or 0, ""), frozenset(), persoas=_quen(en.persoa_id),
            sen_quen=en.persoa_id is None))
    lotes = {lo.id: lo for lo in listar_lotes(session, actor, horta_id)}
    for sa in listar_saidas(session, actor, horta_id):
        lote = lotes.get(sa.lote_id)
        produto = f" de {lote.produto}" if lote else ""
        codigo = f" · lote {lote.codigo}" if lote else ""
        traballos.append(Traballo(
            "lote_saida", sa.id, sa.data, True,
            f"{TIPOS_SAIDA[sa.tipo].split(' (')[0]}: {sa.cantidade:g} {sa.unidade}{produto}"
            f"{codigo}",
            nomes.get(sa.comprador_id or 0) or sa.lugar or CANLES.get(sa.canle or "", "") or "",
            frozenset(), persoas=_quen(sa.persoa_id), sen_quen=sa.persoa_id is None))
    for ta in listar_tarefas(session, actor, horta_id):
        if ta.traballo_id is not None:
            continue  # xa feita: sae o traballo apuntado no seu tipo
        feita = ta.estado == "feito"
        sitio = (onde(ta.cultivo_id) or parcelas.get(ta.parcela_id or 0, "")
                 or grupos.get(ta.animal_id or 0, ""))
        traballos.append(Traballo(
            "tarefa", ta.id, ta.data_feita or ta.data if feita else ta.data or ta.data_limite,
            feita, ta.descricion, sitio,
            parcela_de(ta.cultivo_id) or (frozenset({ta.parcela_id}) if ta.parcela_id
                                          else frozenset()),
            atrasado=not feita and ta.data_limite is not None and ta.data_limite < hoxe,
            persoas=_quen(ta.persoa_id), sen_quen=feita and ta.persoa_id is None))

    por_facer = sorted((t for t in traballos if not t.feito),
                       key=lambda t: (t.data is not None, t.data or hoxe))
    feitos = sorted((t for t in traballos if t.feito
                     and (t.data is None or ((desde is None or t.data >= desde)
                                             and (ata is None or t.data <= ata)))),
                    key=lambda t: (t.data or hoxe, t.id), reverse=True)
    return por_facer + feitos



def ultima_persoa(session: Session, actor: Usuario, horta_id: int) -> int | None:
    """Quen fixo o último traballo apuntado, para propoñelo no seguinte."""
    for t in listar_traballos(session, actor, horta_id):
        if t.feito and t.persoas:
            return t.persoas[0]
    return None


def sen_quen(session: Session, actor: Usuario, horta_id: int) -> dict[str, int]:
    """Cantos traballos feitos de cada tipo non teñen quen o fixo (os apuntados antes)."""
    contas: dict[str, int] = {}
    for t in listar_traballos(session, actor, horta_id):
        if t.sen_quen:
            contas[t.tipo] = contas.get(t.tipo, 0) + 1
    return contas

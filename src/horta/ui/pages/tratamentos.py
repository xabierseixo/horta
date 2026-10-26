"""Sección de tratamentos fitosanitarios: lista, prazo de seguridade e diálogo con varias filas."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.models.fito_rexistro import FitoProduto
from horta.models.parcela import Parcela
from horta.models.tratamento_fito import TIPOS_PROBLEMA, TratamentoFito
from horta.services.catalogos import describir, valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.fito_consulta import prazo_seguridade
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas
from horta.services.tratamentos_fito import (
    dar_de_baixa_tratamento_fito,
    faltas_para_cue,
    listar_tratamentos_fito,
)
from horta.ui.accions import executar_accion
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.dialogo_tratamento import OpcionsTratamento, crear_dialogo_tratamento
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def _opcions(session, catalogo: str) -> dict[str, str]:
    return {v.codigo: v.descricion for v in valores_vixentes(session, catalogo)}


def seccion_tratamentos_fito(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        filas = []
        for t in listar_tratamentos_fito(session, actor, horta_id):
            cultivos = [session.get(Cultivo, c.cultivo_id) for c in t.cultivos]
            prazo = prazo_seguridade(session, t)
            filas.append({
                "id": t.id,
                "data": f"{t.data_inicio:%d/%m/%Y}",
                "cultivos": ", ".join(c.especie for c in cultivos if c),
                "problemas": ", ".join(describir(session, p.tipo, p.codigo) for p in t.problemas)
                or (t.observacions or ""),
                "produtos": ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
                or (t.orixinal_produto or ""),
                "prazo": f"{prazo:%d/%m/%Y}" if prazo else "",
                "cue": "completo" if not faltas_para_cue(t)
                else "falta: " + ", ".join(faltas_para_cue(t)),
            })

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivos", "Cultivos"), ("problemas", "Problema"),
            ("produtos", "Produtos"), ("prazo", "Non colleitar antes do"), ("cue", "CUE"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai tratamentos rexistrados" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return
    abrir = dialogo_tratamento_fito(horta_id)

    def seleccionado() -> int | None:
        if not taboa.selected:
            ui.notify("Selecciona un tratamento na táboa", type="warning")
            return None
        return int(taboa.selected[0]["id"])

    def editar() -> None:
        tratamento_id = seleccionado()
        if tratamento_id is None:
            return
        with get_session() as session:
            t = session.get(TratamentoFito, tratamento_id)
            if t is not None:
                abrir(t)

    def dar_de_baixa() -> None:
        tratamento_id = seleccionado()
        if tratamento_id is None:
            return

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                tratamento = session.get(TratamentoFito, tratamento_id)
                if actor_actual is None or tratamento is None:
                    return
                ok = executar_accion(
                    session,
                    lambda: dar_de_baixa_tratamento_fito(session, actor_actual, tratamento),
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este tratamento? Non se borra: consérvase no histórico "
            "(obriga legal), pero deixa de aparecer na lista.",
            confirmar,
        )

    with ui.row():
        ui.button("Novo tratamento", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa o seleccionado", icon="archive", on_click=dar_de_baixa).props(
            "outline"
        )


def dialogo_tratamento_fito(horta_id: int) -> Callable[[TratamentoFito | None], None]:
    """Constrúe o diálogo do tratamento fitosanitario e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        persoas = listar_persoas(session, actor, horta_id)
        opcions = OpcionsTratamento(
            cultivos={c.id: f"{c.especie} {c.variedade or ''} — "
                            f"{parcelas[c.parcela_id].nome}".strip() for c in cultivos_horta},
            problemas={tipo: _opcions(session, tipo) for tipo in TIPOS_PROBLEMA},
            xustificacions=_opcions(session, "xustificacion"),
            estados=_opcions(session, "estado_fenoloxico"),
            unidades=_opcions(session, "unidade_medida"),
            tipos_produto=_opcions(session, "tipo_produto"),
            tipos_medida=_opcions(session, "tipo_medida_fito"),
            eficacias=_opcions(session, "eficacia"),
            aplicadores={p.id: p.nome for p in persoas if p.e_aplicador},
            asesores={p.id: p.nome for p in persoas if p.e_asesor},
            maquinas={m.id: m.alias for m in listar_maquinas(session, actor, horta_id)},
            rexistro={p.num_rexistro: f"{p.nome} ({p.num_rexistro})"
                      for p in session.query(FitoProduto).order_by(FitoProduto.nome)},
        )
    if not opcions.problemas["enfermidade"]:
        ui.label(AVISO_SEN_CATALOGOS).classes("text-warning")
    if not opcions.rexistro:
        ui.label("Falta o rexistro de fitosanitarios do MAPA: sen el non se comproban os "
                 "produtos. Un administrador debe executar `horta-catalogos fitosanitarios`."
                 ).classes("text-warning")
    return crear_dialogo_tratamento(horta_id, opcions)

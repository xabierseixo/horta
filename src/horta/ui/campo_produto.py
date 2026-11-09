"""Escoller un produto (insumo) nun formulario de traballo e, se se sabe, de que compra saíu.
Se o produto aínda non está, o botón «Novo» créao alí mesmo co nome
."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.idiomas import _
from horta.services.produtos import (
    TIPOS_PRODUTO,
    UNIDADES_PRODUTO,
    crear_produto,
    listar_entradas,
    listar_produtos,
)
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual


def opcions_entradas(horta_id: int, produto_id: int | None = None, tipo: str | None = None
                     ) -> dict[int, str]:
    """As compras dun produto (ou dun tipo), da máis recente á máis antiga."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return {}
        produtos = {p.id: p.nome for p in listar_produtos(session, actor, horta_id,
                                                           so_activos=False)}
        entradas = listar_entradas(session, actor, horta_id, produto_id=produto_id, tipo=tipo)
    return {e.id: " · ".join(x for x in (
        f"{e.data:%d/%m/%Y}", produtos.get(e.produto_id, ""),
        _("lote {lote}").format(lote=e.lote_provedor) if e.lote_provedor else "") if x)
        for e in entradas}


class CampoProduto:
    """Selector dos produtos dun tipo e botón para crear un novo. `value` é o id do produto."""

    def __init__(self, horta_id: int, tipo: str, etiqueta: str) -> None:
        self.horta_id = horta_id
        self.tipo = tipo
        with ui.row().classes("w-full no-wrap items-center gap-1") as self.fila:
            self.select = ui.select({}, label=etiqueta, with_input=True,
                                    clearable=True).classes("col")
            ui.button(icon="add", on_click=self._abrir_novo).props(
                f'flat round dense aria-label="{_("Novo produto")}"'
            ).tooltip(_("Novo"))
        self._cargar()
        with (ui.dialog().props("persistent") as self.dialogo,
              ui.card().style("width: min(26rem, 94vw)")):
            tipo_nome = _(TIPOS_PRODUTO[tipo]).lower()
            ui.label(_("Novo: {tipo}").format(tipo=tipo_nome)).classes("text-h6")
            self.nome = ui.input(_("Nome")).classes("w-full")
            self.unidade = ui.select(list(UNIDADES_PRODUTO), label=_("Cóntase en"),
                                     value="unidades").classes("w-full")
            with ui.row():
                ui.button(_("Gardar"), icon="check", on_click=self._gardar)
                ui.button(_("Cancelar"), on_click=self.dialogo.close).props("flat")

    def _cargar(self) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                return
            produtos = listar_produtos(session, actor, self.horta_id, tipo=self.tipo)
        self.select.set_options({p.id: p.nome for p in produtos})

    def _abrir_novo(self) -> None:
        self.nome.value = ""
        self.dialogo.open()

    def _gardar(self) -> None:
        creado: list[int] = []
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            ok = executar_accion(session, lambda: creado.append(crear_produto(
                session, actor, self.horta_id, self.tipo, self.nome.value or "",
                self.unidade.value).id))
        if ok and creado:
            self._cargar()
            self.select.value = creado[0]
            self.dialogo.close()

    @property
    def value(self) -> int | None:
        return self.select.value

    @value.setter
    def value(self, produto_id: int | None) -> None:
        self.select.value = produto_id if produto_id in self.select.options else None

    def set_visibility(self, visible: bool) -> None:
        self.fila.set_visibility(visible)

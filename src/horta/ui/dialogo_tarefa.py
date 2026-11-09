"""Diálogo «Nova tarefa»: un traballo por facer. Ábrese desde Tarefas e desde «Apuntar
traballo»."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.usuario import Usuario
from horta.services.animais import listar_animais
from horta.services.cultivos import listar_cultivos
from horta.services.diario import TIPOS, nome_grupo
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_quen
from horta.services.tarefas import TIPOS_TAREFA, crear_tarefa
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual

PRIORIDADES_TAREFA = ("baixa", "media", "alta")
_PRIORIDADES = {
    "baixa": N_("baixa"),
    "media": N_("media"),
    "alta": N_("alta"),
}


def opcions_tarefa(
    session: Session, actor: Usuario, horta_id: int
) -> tuple[dict[str, str], dict[int | str, str]]:
    """Que traballo é (baleiro = outro) e quen o vai facer (opcional)."""
    tipos = {
        "": _("Outro traballo"),
        **{tipo: _(TIPOS[tipo]) if tipo in TIPOS else tipo for tipo in TIPOS_TAREFA},
    }
    persoas: dict[int | str, str] = {
        "": _("(sen decidir)"),
        **{p.id: p.nome for p in listar_quen(session, actor, horta_id)},
    }
    return tipos, persoas


def opcions_animais(session: Session, actor: Usuario, horta_id: int) -> dict[int | str, str]:
    """Os grupos de animais de alta, para unha tarefa que se refira a eles (opcional)."""
    return {
        "": _("(sen animais)"),
        **{
            a.id: nome_grupo(a.especie, a.raza)
            for a in listar_animais(session, actor, horta_id)
            if a.estado == "activo"
        },
    }


def dialogo_nova_tarefa(horta_id: int) -> Callable[[], None]:
    """Constrúe o diálogo e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda: None
        opcions_parcela: dict[int | str, str] = {
            "": _("(sen parcela)"),
            **{
                p.id: p.nome
                for p in listar_parcelas(session, actor, horta_id)
                if p.estado != "baixa"
            },
        }
        opcions_cultivo: dict[int | str, str] = {
            "": _("(sen cultivo)"),
            **{c.id: c.especie for c in listar_cultivos(session, actor, horta_id)},
        }
        opcions_tipo, opcions_persoa = opcions_tarefa(session, actor, horta_id)
        opcions_animal = opcions_animais(session, actor, horta_id)

    with ui.dialog().props("persistent") as dialogo, ui.card():
        ui.label(_("Nova tarefa")).classes("text-md font-bold")
        descricion = ui.input(_("Que hai que facer")).classes("w-full")
        tipo = ui.select(opcions_tipo, label=_("Que traballo é"), value="").classes("w-full")
        parcela = ui.select(
            opcions_parcela, label=_("Parcela"), value=""
        ).classes("w-full")
        cultivo = ui.select(
            opcions_cultivo, label=_("Cultivo"), value=""
        ).classes("w-full")
        animal = ui.select(opcions_animal, label=_("Animais"), value="").classes("w-full")
        persoa = ui.select(
            opcions_persoa, label=_("Quen o vai facer"), value=""
        ).classes("w-full")
        data = campo_data(_("Data (opcional)"))
        prioridade = ui.select(
            {k: _(v) for k, v in _PRIORIDADES.items()},
            label=_("Prioridade"),
            value="media",
        )

        def crear() -> None:
            if not descricion.value:
                ui.notify(_("Escribe que hai que facer"), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                creada = executar_accion(
                    session,
                    lambda: crear_tarefa(
                        session,
                        actor_actual,
                        horta_id,
                        descricion.value,
                        parcela_id=parcela.value or None,
                        cultivo_id=cultivo.value or None,
                        animal_id=animal.value or None,
                        tipo=tipo.value or None,
                        persoa_id=persoa.value or None,
                        data=parsear_data(data.value),
                        prioridade=prioridade.value,
                    ),
                )
            if creada:
                ui.navigate.reload()

        with ui.row():
            ui.button(_("Crear"), icon="check", on_click=crear)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    def abrir() -> None:
        descricion.value = ""
        parcela.value = cultivo.value = animal.value = tipo.value = persoa.value = ""
        data.value = ""
        prioridade.value = "media"
        dialogo.open()

    return abrir

"""Diálogo do historial dun recurso (paso 12): parcela (cultivos coa rotación e traballos),
grupo de animais ou máquina."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.idiomas import _
from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.instalacion import Instalacion
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.services.diario import TIPOS
from horta.services.historial import (
    historial_animal,
    historial_maquina,
    historial_parcela,
    por_referencia,
    rotacion,
)
from horta.services.hortas import comprobar_rol_horta
from horta.ui.sesion import pechar_sesion, usuario_actual

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def _data(d: date | None) -> str:
    return f"{d:%d/%m/%Y} · " if d else ""


def abrir_historial(que: str, ref_id: int) -> None:
    """que: parcela, animal, maquina ou instalacion."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        seccions: list[tuple[str, list[tuple[str, str | None]]]] = []
        if que == "parcela":
            parcela = session.get(Parcela, ref_id)
            if parcela is None:
                return
            titulo = parcela.nome
            seccions.append((_("Cultivos (rotación)"), [
                (f"{_data(c.cultivo.data_inicio)}{c.cultivo.especie}"
                 f"{f' ({c.cultivo.variedade})' if c.cultivo.variedade else ''}", c.aviso)
                for c in rotacion(session, actor, parcela)]))
            seccions.append((_("Traballos"), [
                (
                    f"{_data(t.data)}"
                    f"{_(TIPOS[t.tipo]) if t.tipo in TIPOS else t.tipo}"
                    f"{f': {t.que}' if t.que else ''}",
                    None,
                )
                for t in historial_parcela(session, actor, parcela)
            ]))
        else:
            if que == "animal":
                animal = session.get(Animal, ref_id)
                if animal is None:
                    return
                titulo, feitos = animal.especie, historial_animal(session, actor, animal)
            elif que == "instalacion":
                instalacion = session.get(Instalacion, ref_id)
                if instalacion is None:
                    return
                comprobar_rol_horta(session, instalacion.horta_id, actor, _ROLES_LECTURA)
                titulo = instalacion.nome
                feitos = por_referencia(session, "instalacion", instalacion.id)
            else:
                maquina = session.get(Maquina, ref_id)
                if maquina is None:
                    return
                titulo, feitos = maquina.alias, historial_maquina(session, actor, maquina)
            seccions.append((_("Traballos"), [(f"{_data(f.data)}{f.que}", None) for f in feitos]))
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 96vw)"):
        ui.label(_("Historial: {titulo}").format(titulo=titulo)).classes("text-h6")
        for nome, lineas in seccions:
            ui.label(nome).classes("text-subtitle1 text-weight-bold q-mt-sm")
            if not lineas:
                ui.label(_("Nada apuntado.")).classes("texto-suave")
            for texto, aviso in lineas:
                ui.label(texto)
                if aviso:
                    ui.label(aviso).classes("etiqueta-aviso")
        ui.button(_("Pechar"), on_click=dialogo.close).props("flat")
    dialogo.open()

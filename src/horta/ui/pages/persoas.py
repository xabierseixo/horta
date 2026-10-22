from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.persoa import TipoCarne
from horta.services.persoas import crear_persoa, listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual

_AVISO_DIAS = 30


def _data(texto: str | None) -> date | None:
    return date.fromisoformat(texto) if texto else None


def seccion_persoas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        persoas = listar_persoas(session, actor, horta_id, so_activas=False)

    hoxe = date.today()
    for p in persoas:
        if p.activa and p.e_aplicador and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(f"⚠ O carné ROPO de {p.nome} caducou o {p.ropo_caducidade:%d/%m/%Y}") \
                    .classes("text-negative")
            elif dias <= _AVISO_DIAS:
                ui.label(f"⚠ O carné ROPO de {p.nome} caduca en {dias} días").classes(
                    "text-warning"
                )

    filas = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(), "nif": p.nif or "",
         "funcion": ", ".join(x for x, s in (("aplicador", p.e_aplicador),
                                              ("asesor", p.e_asesor)) if s),
         "ropo": p.ropo_numero or "",
         "caducidade": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "activa": "si" if p.activa else "non"}
        for p in persoas
    ]
    ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Nome"), ("nif", "NIF"), ("funcion", "Función"), ("ropo", "Nº ROPO"),
            ("caducidade", "Caducidade ROPO"), ("activa", "Activa"))],
        rows=filas, row_key="id",
    ).classes("w-full")

    if not pode_editar:
        return

    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        ui.label("Nova persoa").classes("text-h6")
        nome = ui.input("Nome")
        apelidos = ui.input("Apelidos")
        nif = ui.input("NIF")
        aplicador = ui.checkbox("Aplicador de fitosanitarios")
        asesor = ui.checkbox("Asesor")
        ropo = ui.input("Nº ROPO")
        tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                         label="Tipo de carné")
        caducidade = ui.input("Caducidade do carné (AAAA-MM-DD)")
        regfer = ui.input("Nº REGFER")

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                ok = executar_accion(session, lambda: crear_persoa(
                    session, actor, horta_id, nome.value, apelidos=apelidos.value or None,
                    nif=nif.value or None, e_aplicador=aplicador.value, e_asesor=asesor.value,
                    ropo_numero=ropo.value or None,
                    ropo_tipo_carne=TipoCarne(tipo.value) if tipo.value else None,
                    ropo_caducidade=_data(caducidade.value), regfer_numero=regfer.value or None))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    ui.button("Nova persoa", icon="person_add", on_click=dialogo.open)


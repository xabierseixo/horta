from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.persoa import Persoa, TipoCarne
from horta.services.persoas import actualizar_persoa, crear_persoa, listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual

_AVISO_DIAS = 30


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
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Nome"), ("nif", "NIF"), ("funcion", "Función"), ("ropo", "Nº ROPO"),
            ("caducidade", "Caducidade ROPO"), ("activa", "Activa"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full").props('no-data-label="Aínda non hai persoas rexistradas"')

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        titulo = ui.label("Nova persoa").classes("text-h6")
        nome = ui.input("Nome").classes("w-full")
        apelidos = ui.input("Apelidos").classes("w-full")
        nif = ui.input("NIF").classes("w-full")
        aplicador = ui.checkbox("Aplicador de fitosanitarios")
        asesor = ui.checkbox("Asesor")
        ropo = ui.input("Nº ROPO").classes("w-full")
        tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                         label="Tipo de carné").classes("w-full")
        caducidade = ui.input("Caducidade do carné (AAAA-MM-DD)").classes("w-full")
        regfer = ui.input("Nº REGFER").classes("w-full")
        activa = ui.checkbox("Activa", value=True)

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    datos = dict(
                        apelidos=apelidos.value or None, nif=nif.value or None,
                        e_aplicador=aplicador.value, e_asesor=asesor.value,
                        ropo_numero=ropo.value or None,
                        ropo_tipo_carne=TipoCarne(tipo.value) if tipo.value else None,
                        ropo_caducidade=parsear_data(caducidade.value),
                        regfer_numero=regfer.value or None,
                    )
                    if editando["id"] is None:
                        crear_persoa(session, actor, horta_id, nome.value, **datos)
                    else:
                        persoa = session.get(Persoa, editando["id"])
                        if persoa is None:
                            return
                        actualizar_persoa(session, actor, persoa, nome=nome.value,
                                          activa=activa.value, **datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova persoa"
        for campo in (nome, apelidos, nif, ropo, caducidade, regfer):
            campo.value = ""
        aplicador.value = asesor.value = False
        tipo.value = None
        activa.value = True
        dialogo.open()

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha persoa na táboa", type="warning")
            return
        persoa = next(p for p in persoas if p.id == taboa.selected[0]["id"])
        editando["id"] = persoa.id
        titulo.text = "Editar persoa"
        nome.value = persoa.nome
        apelidos.value = persoa.apelidos or ""
        nif.value = persoa.nif or ""
        aplicador.value = persoa.e_aplicador
        asesor.value = persoa.e_asesor
        ropo.value = persoa.ropo_numero or ""
        tipo.value = persoa.ropo_tipo_carne.value if persoa.ropo_tipo_carne else None
        caducidade.value = persoa.ropo_caducidade.isoformat() if persoa.ropo_caducidade else ""
        regfer.value = persoa.regfer_numero or ""
        activa.value = persoa.activa
        dialogo.open()

    with ui.row():
        ui.button("Nova persoa", icon="person_add", on_click=abrir_nova)
        ui.button("Editar seleccionada", icon="edit", on_click=abrir_edicion).props("outline")

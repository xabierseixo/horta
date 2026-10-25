"""Sección Equipo: a xente da explotación, as súas funcións e o seu acceso á app."""

from __future__ import annotations

from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.horta import RolHorta
from horta.models.persoa import Persoa, TipoCarne
from horta.models.usuario import Usuario
from horta.services.auth import normalizar_email
from horta.services.equipo import (
    HORAS_UTA,
    acceso_da_persoa,
    conceder_acceso,
    retirar_acceso,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import (
    VINCULOS,
    XENEROS,
    actualizar_persoa,
    crear_persoa,
    listar_persoas,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_AVISO_DIAS = 30
_ACCESOS = {"": "Sen acceso", "lector": "Só mirar", "editor": "Editar", "admin": "Administrador"}
_ROL = {"lector": RolHorta.LECTOR, "editor": RolHorta.EDITOR, "admin": RolHorta.ADMIN}


def _funcions(p: Persoa) -> str:
    return ", ".join(nome for nome, si in (
        ("titular", p.e_titular), ("traballador", p.e_traballador),
        ("aplicador", p.e_aplicador), ("asesor", p.e_asesor)) if si)


def _clave_acceso(rol: RolHorta | None) -> str:
    return rol.value if rol is not None else ""


def seccion_equipo(horta_id: int, pode_editar: bool, e_admin: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        persoas = listar_persoas(session, actor, horta_id, so_activas=False)
        accesos = {p.id: acceso_da_persoa(session, p) for p in persoas}

    hoxe = date.today()
    for p in persoas:
        if p.activa and p.e_aplicador and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(f"⚠ O carné ROPO de {p.nome} caducou o {p.ropo_caducidade:%d/%m/%Y}") \
                    .classes("aviso w-full")
            elif dias <= _AVISO_DIAS:
                ui.label(f"⚠ O carné ROPO de {p.nome} caduca en {dias} días").classes(
                    "aviso w-full"
                )

    horas = sum(p.horas_ano or 0 for p in persoas if p.activa)
    ui.label(f"Traballo ao ano: {horas:g} horas = {horas / HORAS_UTA:.2f} UTA").classes(
        "texto-suave")

    filas = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(), "funcions": _funcions(p),
         "ropo": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "acceso": _ACCESOS[_clave_acceso(accesos[p.id])],
         "activa": "si" if p.activa else "non"}
        for p in persoas
    ]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Nome"), ("funcions", "Funcións"), ("ropo", "Carné ROPO ata"),
            ("acceso", "Acceso á app"), ("activa", "Activa"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai ninguén no equipo" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Nova persoa").classes("text-h6")
        nome = ui.input("Nome").classes("w-full")
        apelidos = ui.input("Apelidos").classes("w-full")
        nif = ui.input("NIF").classes("w-full")
        telefono = ui.input("Teléfono").classes("w-full")
        email = ui.input("Email de contacto").classes("w-full")
        with ui.expansion("Enderezo (para o caderno, se é o titular)").classes("w-full"):
            enderezo = ui.input("Enderezo").classes("w-full")
            localidade = ui.input("Localidade").classes("w-full")
            codigo_postal = ui.input("Código postal").classes("w-full")
            provincia = ui.input("Provincia").classes("w-full")
        ui.label("Funcións").classes("text-subtitle2 q-mt-sm")
        with ui.row():
            titular = ui.checkbox("Titular")
            traballador = ui.checkbox("Traballador")
            aplicador = ui.checkbox("Aplica fitosanitarios")
            asesor = ui.checkbox("Asesor")
        ropo = ui.input("Nº ROPO").classes("w-full")
        tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                         label="Tipo de carné", clearable=True).classes("w-full")
        caducidade = campo_data("Caducidade do carné")
        regfer = ui.input("Nº REGFER").classes("w-full")
        with ui.expansion("Traballo (para o plan de empresa)").classes("w-full"):
            vinculo = ui.select(list(VINCULOS), label="Vínculo coa explotación",
                                clearable=True).classes("w-full")
            horas_ano = ui.input("Horas ao ano").classes("w-full")
            formacion = ui.input("Formación agraria").classes("w-full")
        with ui.expansion("Colectivo (opcional, para axudas ao emprego)").classes("w-full"):
            xenero = ui.select(list(XENEROS), label="Xénero", clearable=True).classes("w-full")
            nacemento = campo_data("Data de nacemento")
            discapacidade = ui.checkbox("Persoa con discapacidade")
        activa = ui.checkbox("Activa", value=True)
        with ui.column().classes("w-full gap-1") as bloque_acceso:
            ui.label("Acceso á app").classes("text-subtitle2 q-mt-sm")
            acceso = ui.select(_ACCESOS, value="", label="Permiso").classes("w-full")
            email_conta = ui.input("Email da súa conta na app").classes("w-full")
        bloque_acceso.set_visibility(e_admin)

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            datos: dict[str, Any] = dict(
                apelidos=apelidos.value or None, nif=nif.value or None,
                telefono=telefono.value or None, email=email.value or None,
                enderezo=enderezo.value or None, localidade=localidade.value or None,
                codigo_postal=codigo_postal.value or None, provincia=provincia.value or None,
                e_titular=titular.value, e_traballador=traballador.value,
                e_aplicador=aplicador.value, e_asesor=asesor.value,
                ropo_numero=ropo.value or None,
                ropo_tipo_carne=TipoCarne(tipo.value) if tipo.value else None,
                ropo_caducidade=parsear_data(caducidade.value),
                regfer_numero=regfer.value or None,
                vinculo=vinculo.value, horas_ano=parsear_decimal(horas_ano.value),
                formacion_agraria=formacion.value or None,
                xenero=xenero.value, data_nacemento=parsear_data(nacemento.value),
                discapacidade=discapacidade.value,
            )
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    if e_admin and acceso.value:
                        if not email_conta.value:
                            raise OperacionNonPermitidaError(
                                "Indica o email da conta para darlle acceso"
                            )
                        conta = session.query(Usuario).filter_by(
                            email=normalizar_email(email_conta.value)).one_or_none()
                        if conta is None:
                            raise OperacionNonPermitidaError(
                                "Non hai ningunha conta con ese email. "
                                "Pídelle ao administrador que a cree."
                            )
                    if editando["id"] is None:
                        persoa = crear_persoa(session, actor, horta_id, nome.value, **datos)
                    else:
                        existente = session.get(Persoa, editando["id"])
                        if existente is None:
                            return
                        persoa = existente
                        actualizar_persoa(session, actor, persoa, nome=nome.value,
                                          activa=activa.value, **datos)
                    if not e_admin:
                        return
                    if acceso.value:
                        conceder_acceso(session, actor, persoa, email_conta.value,
                                        _ROL[acceso.value])
                    elif persoa.usuario_id is not None:
                        retirar_acceso(session, actor, persoa)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    textos = (nome, apelidos, nif, telefono, email, enderezo, localidade, codigo_postal,
              provincia, ropo, caducidade, regfer, horas_ano,
              formacion, nacemento, email_conta)
    casillas = (titular, traballador, aplicador, asesor, discapacidade)

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova persoa"
        for campo in textos:
            campo.value = ""
        for casilla in casillas:
            casilla.value = False
        tipo.value = vinculo.value = xenero.value = None
        activa.value = True
        acceso.value = ""
        dialogo.open()

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha persoa na táboa", type="warning")
            return
        p = next(x for x in persoas if x.id == taboa.selected[0]["id"])
        editando["id"] = p.id
        titulo.text = "Editar persoa"
        nome.value = p.nome
        apelidos.value = p.apelidos or ""
        nif.value = p.nif or ""
        telefono.value = p.telefono or ""
        email.value = p.email or ""
        enderezo.value = p.enderezo or ""
        localidade.value = p.localidade or ""
        codigo_postal.value = p.codigo_postal or ""
        provincia.value = p.provincia or ""
        titular.value, traballador.value = p.e_titular, p.e_traballador
        aplicador.value, asesor.value = p.e_aplicador, p.e_asesor
        ropo.value = p.ropo_numero or ""
        tipo.value = p.ropo_tipo_carne.value if p.ropo_tipo_carne else None
        caducidade.value = p.ropo_caducidade.isoformat() if p.ropo_caducidade else ""
        regfer.value = p.regfer_numero or ""
        vinculo.value = p.vinculo
        horas_ano.value = "" if p.horas_ano is None else f"{p.horas_ano:g}"
        formacion.value = p.formacion_agraria or ""
        xenero.value = p.xenero
        nacemento.value = p.data_nacemento.isoformat() if p.data_nacemento else ""
        discapacidade.value = p.discapacidade
        activa.value = p.activa
        rol = accesos[p.id]
        acceso.value = rol.value if rol else ""
        email_conta.value = p.email or ""
        dialogo.open()

    with ui.row():
        ui.button("Nova persoa", icon="person_add", on_click=abrir_nova)
        ui.button("Editar", icon="edit", on_click=abrir_edicion).props("outline")

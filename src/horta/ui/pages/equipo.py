"""Sección Persoas: toda a xente e as empresas coas que trata a explotación, cos seus papeis.
Pestana Equipo (quen traballa nela, coas horas e o acceso á app) e pestana Contactos (o resto:
clientes, provedores, laboratorios...). É unha soa lista: quen ten papeis dos dous lados sae
nas dúas."""

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
    PAPEIS,
    PAPEIS_CONTACTO,
    PAPEIS_EQUIPO,
    TIPOS_PERSOA,
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


# Os rexistros que pode ter unha persoa ou entidade, segundo o seu papel
_REXISTROS = (("rega", "REGA (ES + 12 díxitos)"), ("reaga", "REAGA"), ("nima", "NIMA"),
              ("ropveg", "Nº ROPVEG"), ("rexistro_dixital", "Nº de rexistro dixital de alimentos"),
              ("num_asesoramento", "Nº de identificación da entidade de asesoramento"))
_CONTACTO = (("telefono", "Teléfono"), ("email", "Email de contacto"),
             ("enderezo", "Enderezo"), ("localidade", "Localidade"),
             ("codigo_postal", "Código postal"), ("provincia", "Provincia"),
             ("concello_codigo", "Concello (código INE)"), ("pais", "País, se non é España"))
_CON_ROPO = ("aplicador", "asesor", "servizos")


def _papeis(p: Persoa, cales: dict[str, str]) -> str:
    return ", ".join(nome for clave, nome in cales.items() if p.ten_papel(clave))


def _e_equipo(p: Persoa) -> bool:
    return p.ten_papel(*PAPEIS_EQUIPO)


def _e_contacto(p: Persoa) -> bool:
    return p.ten_papel(*PAPEIS_CONTACTO) or not p.papeis


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
        if p.activa and p.ten_papel("aplicador") and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(f"⚠ O carné ROPO de {p.nome} caducou o {p.ropo_caducidade:%d/%m/%Y}") \
                    .classes("aviso w-full")
            elif dias <= _AVISO_DIAS:
                ui.label(f"⚠ O carné ROPO de {p.nome} caduca en {dias} días").classes(
                    "aviso w-full"
                )

    horas = sum(p.horas_ano or 0 for p in persoas if p.activa and _e_equipo(p))

    filas_equipo = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(),
         "funcions": _papeis(p, PAPEIS_EQUIPO),
         "ropo": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "acceso": _ACCESOS[_clave_acceso(accesos[p.id])],
         "activa": "si" if p.activa else "non"}
        for p in persoas if _e_equipo(p)
    ]
    filas_contactos = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(),
         "papeis": _papeis(p, PAPEIS_CONTACTO), "nif": p.nif or "",
         "telefono": p.telefono or "", "activa": "si" if p.activa else "non"}
        for p in persoas if _e_contacto(p)
    ]
    with ui.tabs().classes("w-full") as pestanas:
        pestana_equipo = ui.tab("Equipo", icon="groups")
        pestana_contactos = ui.tab("Contactos", icon="contacts")
    with ui.tab_panels(pestanas, value=pestana_equipo).classes("w-full"):
        with ui.tab_panel(pestana_equipo):
            ui.label(f"Traballo ao ano: {horas:g} horas = {horas / HORAS_UTA:.2f} UTA").classes(
                "texto-suave")
            taboa_equipo = ui.table(
                columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
                    ("nome", "Nome"), ("funcions", "Funcións"), ("ropo", "Carné ROPO ata"),
                    ("acceso", "Acceso á app"), ("activa", "Activa"))],
                rows=filas_equipo, row_key="id",
                selection="single" if pode_editar else None,
            ).classes("w-full taboa").props(
                f'flat bordered no-data-label="Aínda non hai ninguén no equipo" {TEXTOS_TABOA}')
        with ui.tab_panel(pestana_contactos):
            taboa_contactos = ui.table(
                columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
                    ("nome", "Nome"), ("papeis", "Que é"), ("nif", "NIF"),
                    ("telefono", "Teléfono"), ("activa", "Activa"))],
                rows=filas_contactos, row_key="id",
                selection="single" if pode_editar else None,
            ).classes("w-full taboa").props(
                'flat bordered no-data-label="Aínda non hai clientes, provedores nin outros '
                f'contactos" {TEXTOS_TABOA}')

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Nova persoa").classes("text-h6")
        tipo_persoa = ui.radio(TIPOS_PERSOA, value="persoa").props("inline")
        nome = ui.input("Nome ou razón social").classes("w-full")
        apelidos = ui.input("Apelidos").classes("w-full")
        apelidos.bind_visibility_from(tipo_persoa, "value", value="persoa")
        nif = ui.input("NIF").classes("w-full")
        papeis = ui.select(PAPEIS, label="Que é (pode ser varias cousas)", multiple=True,
                           value=[]).classes("w-full").props("use-chips")
        with ui.expansion("Contacto e enderezo").classes("w-full"):
            contacto = {campo: ui.input(etiqueta).classes("w-full")
                        for campo, etiqueta in _CONTACTO}
        with ui.expansion("Rexistros (REGA, NIMA, ROPVEG...)").classes("w-full"):
            rexistros = {campo: ui.input(etiqueta).classes("w-full")
                         for campo, etiqueta in _REXISTROS}
        with ui.column().classes("w-full gap-0") as bloque_ropo:
            ropo = ui.input("Nº ROPO").classes("w-full")
            tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                             label="Tipo de carné", clearable=True).classes("w-full")
            caducidade = campo_data("Caducidade do carné")
            regfer = ui.input("Nº REGFER").classes("w-full")
        with ui.expansion("Traballo (para o plan de empresa)").classes("w-full") as bloque_traballo:
            vinculo = ui.select(list(VINCULOS), label="Vínculo coa explotación",
                                clearable=True).classes("w-full")
            horas_ano = ui.input("Horas ao ano").classes("w-full")
            formacion = ui.input("Formación agraria").classes("w-full")
        with ui.expansion("Colectivo (opcional, para axudas ao emprego)").classes(
                "w-full") as bloque_colectivo:
            xenero = ui.select(list(XENEROS), label="Xénero", clearable=True).classes("w-full")
            nacemento = campo_data("Data de nacemento")
            discapacidade = ui.checkbox("Persoa con discapacidade")
        activa = ui.checkbox("Activa", value=True)
        with ui.column().classes("w-full gap-1") as bloque_acceso:
            ui.label("Acceso á app").classes("text-subtitle2 q-mt-sm")
            acceso = ui.select(_ACCESOS, value="", label="Permiso").classes("w-full")
            email_conta = ui.input("Email da súa conta na app").classes("w-full")

        def mostrar_bloques() -> None:
            escollidos = set(papeis.value or [])
            bloque_ropo.set_visibility(bool(escollidos & set(_CON_ROPO)))
            equipo = bool(escollidos & set(PAPEIS_EQUIPO))
            bloque_traballo.set_visibility(equipo)
            bloque_colectivo.set_visibility(equipo and tipo_persoa.value == "persoa")
            # O acceso á app só para quen traballa na explotación (e só o dá quen administra)
            bloque_acceso.set_visibility(e_admin and equipo)

        papeis.on_value_change(mostrar_bloques)
        tipo_persoa.on_value_change(mostrar_bloques)

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            datos: dict[str, Any] = dict(
                tipo=tipo_persoa.value,
                apelidos=(apelidos.value or None) if tipo_persoa.value == "persoa" else None,
                nif=nif.value or None,
                **{c: (e.value or None) for c, e in {**contacto, **rexistros}.items()},
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
                        persoa = crear_persoa(session, actor, horta_id, nome.value,
                                              papeis=set(papeis.value or []), **datos)
                    else:
                        existente = session.get(Persoa, editando["id"])
                        if existente is None:
                            return
                        persoa = existente
                        actualizar_persoa(session, actor, persoa, nome=nome.value,
                                          papeis=set(papeis.value or []), activa=activa.value,
                                          **datos)
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

    textos = (nome, apelidos, nif, *contacto.values(), *rexistros.values(), ropo, caducidade,
              regfer, horas_ano, formacion, nacemento, email_conta)

    def en_equipo() -> bool:
        return pestanas.value in (None, pestana_equipo, pestana_equipo.props["name"])

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova persoa ou entidade"
        for campo in textos:
            campo.value = ""
        tipo_persoa.value = "persoa"
        papeis.value = ["traballador"] if en_equipo() else []
        discapacidade.value = False
        tipo.value = vinculo.value = xenero.value = None
        activa.value = True
        acceso.value = ""
        mostrar_bloques()
        dialogo.open()

    def abrir_edicion() -> None:
        taboa = taboa_equipo if en_equipo() else taboa_contactos
        if not taboa.selected:
            ui.notify("Selecciona unha persoa na táboa", type="warning")
            return
        p = next(x for x in persoas if x.id == taboa.selected[0]["id"])
        editando["id"] = p.id
        titulo.text = "Editar persoa ou entidade"
        tipo_persoa.value = p.tipo
        nome.value = p.nome
        apelidos.value = p.apelidos or ""
        nif.value = p.nif or ""
        for campo, entrada in {**contacto, **rexistros}.items():
            entrada.value = getattr(p, campo) or ""
        papeis.value = [clave for clave in PAPEIS if p.ten_papel(clave)]
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
        mostrar_bloques()
        dialogo.open()

    with ui.row():
        ui.button("Nova persoa ou entidade", icon="person_add", on_click=abrir_nova)
        ui.button("Editar", icon="edit", on_click=abrir_edicion).props("outline")

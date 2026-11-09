"""Equipo (quen traballa na explotación, coas horas e o acceso á app) e Contactos (clientes,
provedores, quen fai traballos..., con categorías libres): dúas entradas do menú sobre a mesma
táboa de persoas (deseño global §2bis). Quen ten papeis dos dous lados sae
nas dúas."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _, ngettext
from horta.models.categoria import Categoria
from horta.models.horta import RolHorta
from horta.models.persoa import Persoa, TipoCarne
from horta.models.usuario import Usuario
from horta.services.accesos import listar_accesos
from horta.services.categorias import (
    asignar_categorias,
    borrar_categoria,
    categorias_da_persoa,
    crear_categoria,
    listar_categorias,
    renomear_categoria,
)
from horta.services.equipo import (
    HORAS_UTA,
    acceso_da_persoa,
    cambiar_permiso,
    crear_convite,
    duplicados,
    retirar_acceso,
    xuntar_persoas,
)
from horta.services.persoas import (
    PAPEIS_CONTACTO,
    PAPEIS_EQUIPO,
    TIPOS_PERSOA,
    VINCULOS,
    XENEROS,
    actualizar_persoa,
    crear_persoa,
    listar_persoas,
)
from horta.services.tempo import concellos
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.etiquetas import TIPOS_CARNE
from horta.ui.etiquetas import VINCULOS as ETIQUETAS_VINCULO
from horta.ui.ficha_persoa import abrir_ficha_persoa
from horta.ui.lista_tarxetas import lista_tarxetas
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_AVISO_DIAS = 30
_ACCESOS = {
    "": N_("Sen acceso"),
    "lector": N_("Só mirar"),
    "editor": N_("Editar"),
    "admin": N_("Administrador"),
}
_ROL = {"lector": RolHorta.LECTOR, "editor": RolHorta.EDITOR, "admin": RolHorta.ADMIN}


# Os rexistros que pode ter unha persoa ou entidade, segundo o seu papel
_REXISTROS = (
    ("rega", N_("REGA (ES + 12 díxitos)")),
    ("reaga", N_("REAGA")),
    ("nima", N_("NIMA")),
    ("ropveg", N_("Nº ROPVEG")),
    ("rexistro_dixital", N_("Nº de rexistro dixital de alimentos")),
    ("num_asesoramento", N_("Nº de identificación da entidade de asesoramento")),
)
_CONTACTO = (
    ("telefono", N_("Teléfono")),
    ("email", N_("Email de contacto")),
    ("enderezo", N_("Enderezo")),
    ("localidade", N_("Localidade")),
    ("codigo_postal", N_("Código postal")),
    ("provincia", N_("Provincia")),
    ("concello_codigo", N_("Concello")),
    ("pais", N_("País, se non é España")),
)
_CON_ROPO = ("aplicador", "asesor", "servizos")
_MOTIVOS_CONVITE = {
    "": N_("Ningún"),
    "inspeccion": N_("Inspección"),
    "auditoria": N_("Auditoría"),
    "certificacion": N_("Certificación"),
}


def _papeis(p: Persoa, cales: dict[str, str]) -> str:
    return ", ".join(_(nome) for clave, nome in cales.items() if p.ten_papel(clave))


def _e_equipo(p: Persoa) -> bool:
    return p.ten_papel(*PAPEIS_EQUIPO)


def _e_contacto(p: Persoa) -> bool:
    return p.ten_papel(*PAPEIS_CONTACTO) or not p.papeis


def _clave_acceso(rol: RolHorta | None) -> str:
    return rol.value if rol is not None else ""


def detalle_tarxeta_equipo(fila: dict[str, Any]) -> str:
    """Devolve o texto de detalle para a tarxeta dun membro do equipo."""
    partes: list[str] = []
    funcions = str(fila.get("funcions") or "").strip()
    if funcions:
        partes.append(funcions)
    ropo = str(fila.get("ropo") or "").strip()
    if ropo:
        partes.append(_("ROPO ata {data}").format(data=ropo))
    return " · ".join(partes)


def detalle_tarxeta_contacto(fila: dict[str, Any]) -> str:
    """Devolve o texto de detalle para a tarxeta dun contacto."""
    partes: list[str] = []
    papeis = str(fila.get("papeis") or "").strip()
    if papeis:
        partes.append(papeis)
    telefono = str(fila.get("telefono") or "").strip()
    if telefono:
        partes.append(telefono)
    return " · ".join(partes)


def seccion_equipo(horta_id: int, pode_editar: bool, e_admin: bool,
                   modo: str = "equipo") -> None:
    equipo = modo == "equipo"
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        persoas = listar_persoas(session, actor, horta_id, so_activas=False)
        categorias = {c.id: c.nome for c in listar_categorias(session, actor, horta_id)}
        papel_da_categoria = {c.id: c.papel for c in listar_categorias(session, actor, horta_id)
                              if c.papel}
        das_persoas = {p.id: categorias_da_persoa(session, p) for p in persoas}
        accesos = {p.id: acceso_da_persoa(session, p) for p in persoas}
        contas = {p.id: u.email for p in persoas if p.usuario_id
                  and (u := session.get(Usuario, p.usuario_id)) is not None}
        accesos_rexistrados = (
            listar_accesos(session, actor, horta_id) if (e_admin and equipo) else []
        )

    hoxe = date.today()
    for p in persoas:
        if p.activa and p.ten_papel("aplicador") and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(
                    _("⚠ O carné ROPO de {nome} caducou o {data}").format(
                        nome=p.nome, data=f"{p.ropo_caducidade:%d/%m/%Y}"
                    )
                ).classes("aviso w-full")
            elif dias <= _AVISO_DIAS:
                ui.label(
                    ngettext(
                        "⚠ O carné ROPO de {nome} caduca en {dias} día",
                        "⚠ O carné ROPO de {nome} caduca en {dias} días",
                        dias,
                    ).format(nome=p.nome, dias=dias)
                ).classes("aviso w-full")

    horas = sum(p.horas_ano or 0 for p in persoas if p.activa and _e_equipo(p))

    filas_equipo = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(),
         "funcions": _papeis(p, PAPEIS_EQUIPO),
         "ropo": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "acceso": _(_ACCESOS[_clave_acceso(accesos[p.id])]),
         "activa": _("si") if p.activa else _("non")}
        for p in persoas if _e_equipo(p)
    ]
    filas_contactos: list[dict[str, Any]] = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(),
         "papeis": ", ".join(sorted(categorias[i] for i in das_persoas[p.id])),
         "categorias": sorted(das_persoas[p.id]), "nif": p.nif or "",
         "telefono": p.telefono or "", "activa": _("si") if p.activa else _("non")}
        for p in persoas if _e_contacto(p)
    ]

    accions_fn: dict[str, Callable[[Persoa], None]] = {}

    def tocar(pid: int) -> None:
        atopada = next((p for p in persoas if p.id == pid), None)
        if atopada is None:
            return
        persoa: Persoa = atopada
        accions: list[tuple[str, str, Callable[[], None]]] | None = None
        if pode_editar and "editar" in accions_fn:
            accions = [(_("Editar"), "edit", lambda: accions_fn["editar"](persoa))]
            if e_admin and "xuntar" in accions_fn:
                accions.append(
                    (_("Xuntar con outra"), "merge", lambda: accions_fn["xuntar"](persoa))
                )
        abrir_ficha_persoa(horta_id, pid, accions=accions)

    if equipo:
        ui.label(
            _("Traballo ao ano: {horas:g} horas = {uta:.2f} UTA").format(
                horas=horas, uta=horas / HORAS_UTA
            )
        ).classes("texto-suave")
        taboa = ui.table(
            columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
                ("nome", _("Nome")), ("funcions", _("Funcións")), ("ropo", _("Carné ROPO ata")),
                ("acceso", _("Acceso á app")), ("activa", _("Activa")))],
            rows=filas_equipo, row_key="id",
            selection="single" if pode_editar else None,
        ).classes("w-full taboa so-ordenador").props(
            f'flat bordered no-data-label="{_("Aínda non hai ninguén no equipo")}" '
            f"{TEXTOS_TABOA}"
        )

        @ui.refreshable
        def debuxar_tarxetas_equipo() -> None:
            elementos = [
                (int(r["id"]), str(r["nome"]), detalle_tarxeta_equipo(r))
                for r in taboa.rows
            ]
            lista_tarxetas(elementos, ao_tocar=tocar)

        debuxar_tarxetas_equipo()
    else:
        with ui.row().classes("w-full items-center gap-2"):
            filtro = ui.select({0: _("Todas as categorías"), **categorias}, value=0,
                               label=_("Categoría")).classes("w-64")
            if pode_editar:
                ui.button(_("Categorías"), icon="label",
                          on_click=lambda: _dialogo_categorias(horta_id)).props("flat")
        taboa = ui.table(
            columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
                ("nome", _("Nome")), ("papeis", _("Categorías")), ("nif", _("NIF")),
                ("telefono", _("Teléfono")), ("activa", _("Activa")))],
            rows=filas_contactos, row_key="id",
            selection="single" if pode_editar else None,
        ).classes("w-full taboa so-ordenador").props(
            'flat bordered no-data-label="'
            f'{_("Aínda non hai clientela, empresas provedoras nin outros contactos")}" '
            f"{TEXTOS_TABOA}"
        )

        @ui.refreshable
        def debuxar_tarxetas_contactos() -> None:
            elementos = [
                (int(r["id"]), str(r["nome"]), detalle_tarxeta_contacto(r))
                for r in taboa.rows
            ]
            lista_tarxetas(elementos, ao_tocar=tocar)

        debuxar_tarxetas_contactos()

        def filtrar() -> None:
            taboa.rows = [f for f in filas_contactos
                          if not filtro.value or filtro.value in das_persoas[int(f["id"])]]
            debuxar_tarxetas_contactos.refresh()

        filtro.on_value_change(filtrar)

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label(_("Nova persoa")).classes("text-h6")
        tipo_persoa = ui.radio(
            {k: _(v) for k, v in TIPOS_PERSOA.items()}, value="persoa"
        ).props("inline")
        nome = ui.input(_("Nome ou razón social")).classes("w-full")
        apelidos = ui.input(_("Apelidos")).classes("w-full")
        apelidos.bind_visibility_from(tipo_persoa, "value", value="persoa")
        nif = ui.input(_("NIF")).classes("w-full")
        papeis = ui.select(
            {k: _(v) for k, v in PAPEIS_EQUIPO.items()} if equipo else categorias,
            label=_("Que fai (pode ser varias cousas)") if equipo else _("Categorías"),
            multiple=True,
            value=[],
        ).classes("w-full").props("use-chips")
        with ui.expansion(_("Contacto e enderezo")).classes("w-full"):
            contacto: dict[str, Any] = {
                campo: (ui.select(concellos(), label=_(etiqueta), with_input=True,
                                  clearable=True).classes("w-full")
                        if campo == "concello_codigo" else
                        ui.input(_(etiqueta)).classes("w-full"))
                for campo, etiqueta in _CONTACTO
            }
        with ui.expansion(_("Rexistros (REGA, NIMA, ROPVEG...)")).classes("w-full"):
            rexistros = {campo: ui.input(_(etiqueta)).classes("w-full")
                         for campo, etiqueta in _REXISTROS}
        with ui.column().classes("w-full gap-0") as bloque_ropo:
            ropo = ui.input(_("Nº ROPO")).classes("w-full")
            tipo = ui.select({t.value: _(TIPOS_CARNE[t.value]) for t in TipoCarne},
                             label=_("Tipo de carné"), clearable=True).classes("w-full")
            caducidade = campo_data(_("Caducidade do carné"))
            regfer = ui.input(_("Nº REGFER")).classes("w-full")
        with ui.expansion(
            _("Traballo (para o plan de empresa)")
        ).classes("w-full") as bloque_traballo:
            vinculo = ui.select({v: _(ETIQUETAS_VINCULO[v]) for v in VINCULOS},
                                label=_("Vínculo coa explotación"),
                                clearable=True).classes("w-full")
            horas_ano = ui.input(_("Horas ao ano")).classes("w-full")
            custo_hora = ui.input(_("Custo da hora (€)")).classes("w-full")
            formacion = ui.input(_("Formación agraria")).classes("w-full")
        with ui.expansion(
            _("Colectivo (opcional, para axudas ao emprego)")
        ).classes("w-full") as bloque_colectivo:
            xenero = ui.select(
                {x: _(x) for x in XENEROS}, label=_("Xénero"), clearable=True
            ).classes("w-full")
            nacemento = campo_data(_("Data de nacemento"))
            discapacidade = ui.checkbox(_("Persoa con discapacidade"))
        activa = ui.checkbox(_("Activa"), value=True)
        # Acceso á app (deseño global §2bis): por convite, sen escribir correos de contas
        with ui.column().classes("w-full gap-1") as bloque_acceso:
            ui.label(_("Acceso á app")).classes("text-subtitle2 q-mt-sm")
            estado_acceso = ui.label("").classes("text-caption texto-suave")
            acceso = ui.select({k: _(v) for k, v in _ACCESOS.items() if k}, value="editor",
                               label=_("Permiso")).classes("w-full")
            with ui.column().classes("w-full gap-1") as bloque_inspeccion:
                motivo_convite = ui.select(
                    {k: _(v) for k, v in _MOTIVOS_CONVITE.items()},
                    value="", label=_("Motivo"),
                ).classes("w-full")
                acceso_ata_convite = campo_data(_("Acceso ata"))
            with ui.row():
                boton_convite = ui.button(_("Crear convite"), icon="link").props("outline")
                boton_quitar = ui.button(_("Quitar acceso"), icon="block").props(
                    "flat color=negative")
            ligazon = ui.input(_("Ligazón para mandarlle (vale 7 días)")).props(
                "readonly").classes("w-full")

        def actualizar_inspeccion() -> None:
            bloque_inspeccion.set_visibility(acceso.value == "lector")

        acceso.on_value_change(actualizar_inspeccion)

        def mostrar_acceso() -> None:
            persoa_id = editando["id"]
            ligada = persoa_id is not None and persoa_id in contas
            if persoa_id is None:
                estado_acceso.text = _("Garda primeiro a persoa para darlle acceso")
            elif ligada:
                estado_acceso.text = _("Entra coa conta {conta}").format(conta=contas[persoa_id])
            else:
                estado_acceso.text = _(
                    "Non ten acceso. Escolle o permiso e crea un convite: "
                    "unha ligazón para mandarlle"
                )
            acceso.set_visibility(persoa_id is not None)
            actualizar_inspeccion()
            boton_convite.set_visibility(persoa_id is not None and not ligada)
            boton_quitar.set_visibility(ligada)
            ligazon.set_visibility(False)

        def convidar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                persoa = session.get(Persoa, editando["id"] or 0)
                if actor is None or persoa is None:
                    return
                creado: list[str] = []
                data_ata = (parsear_data(acceso_ata_convite.value)
                            if acceso.value == "lector" else None)
                mot_val = (motivo_convite.value
                           if (acceso.value == "lector" and motivo_convite.value) else None)
                ok = executar_accion(session, lambda: creado.append(crear_convite(
                    session, actor, persoa, _ROL[acceso.value],
                    acceso_ata=data_ata, motivo=mot_val).token))
            if ok and creado:
                base = str(ui.context.client.request.base_url).rstrip("/")
                ligazon.value = f"{base}/convite/{creado[0]}"
                ligazon.set_visibility(True)
                ui.notify(_("Copia a ligazón e mándalla (WhatsApp, correo…)"), type="positive")

        def quitar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                persoa = session.get(Persoa, editando["id"] or 0)
                if actor is None or persoa is None:
                    return
                ok = executar_accion(session, lambda: retirar_acceso(session, actor, persoa))
            if ok:
                ui.navigate.reload()

        boton_convite.on_click(convidar)
        boton_quitar.on_click(quitar)

        def mostrar_bloques() -> None:
            escollidos = (set(papeis.value or []) if equipo else
                          {papel_da_categoria.get(i) for i in papeis.value or []})
            bloque_ropo.set_visibility(bool(escollidos & set(_CON_ROPO)))
            do_equipo = bool(escollidos & set(PAPEIS_EQUIPO))
            bloque_traballo.set_visibility(do_equipo)
            bloque_colectivo.set_visibility(do_equipo and tipo_persoa.value == "persoa")
            # O acceso á app só para quen traballa na explotación (e só o dá quen administra)
            bloque_acceso.set_visibility(e_admin and do_equipo)

        papeis.on_value_change(mostrar_bloques)
        tipo_persoa.on_value_change(mostrar_bloques)

        def gardar(confirmado: bool = False) -> None:
            if not nome.value:
                ui.notify(_("O nome é obrigatorio"), type="negative")
                return
            if not confirmado:
                with get_session() as session:
                    iguais = duplicados(session, horta_id, nome.value, apelidos.value,
                                        nif.value, contacto["email"].value, editando["id"])
                if iguais:
                    with ui.dialog() as aviso, ui.card():
                        persoas_iguais = ", ".join(
                            f"{p.nome} {p.apelidos or ''}".strip() for p in iguais
                        )
                        ui.label(
                            _(
                                "Xa hai alguén igual: {persoas}. "
                                "Se é a mesma persoa, edita esa ou xúntaas."
                            ).format(persoas=persoas_iguais)
                        )
                        with ui.row():
                            def igual() -> None:
                                aviso.close()
                                gardar(True)

                            ui.button(_("Gardar igual"), on_click=igual)
                            ui.button(_("Cancelar"), on_click=aviso.close).props("flat")
                    aviso.open()
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
                custo_hora=parsear_decimal(custo_hora.value),
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
                    existente = (session.get(Persoa, editando["id"]) if editando["id"]
                                 else None)
                    antes = existente.papeis if existente else set()
                    # Cada pantalla toca só os seus papeis: o resto consérvanse
                    if equipo:
                        novos = set(papeis.value or []) | (antes - set(PAPEIS_EQUIPO))
                    else:
                        novos = antes & set(PAPEIS_EQUIPO)
                    if existente is None:
                        persoa = crear_persoa(session, actor, horta_id, nome.value,
                                              papeis=novos, **datos)
                    else:
                        persoa = existente
                        actualizar_persoa(session, actor, persoa, nome=nome.value,
                                          papeis=novos, activa=activa.value, **datos)
                    if not equipo:
                        asignar_categorias(session, actor, persoa, set(papeis.value or []))
                    rol = accesos.get(persoa.id)
                    if e_admin and rol is not None and acceso.value != rol.value:
                        cambiar_permiso(session, actor, persoa, _ROL[acceso.value])

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=lambda: gardar())
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    textos = (nome, apelidos, nif, *(v for c, v in contacto.items() if c != "concello_codigo"),
              *rexistros.values(), ropo, caducidade, regfer, horas_ano, custo_hora, formacion,
              nacemento)

    def en_equipo() -> bool:
        return equipo

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = _("Nova persoa ou entidade")
        for campo in textos:
            campo.value = ""
        contacto["concello_codigo"].value = None
        tipo_persoa.value = "persoa"
        papeis.value = ["traballador"] if en_equipo() else []
        discapacidade.value = False
        tipo.value = vinculo.value = xenero.value = None
        activa.value = True
        acceso.value = "editor"
        motivo_convite.value = ""
        acceso_ata_convite.value = ""
        mostrar_bloques()
        mostrar_acceso()
        dialogo.open()

    def escollida() -> Persoa | None:
        if not taboa.selected:
            ui.notify(_("Selecciona unha persoa na táboa"), type="warning")
            return None
        return next(x for x in persoas if x.id == taboa.selected[0]["id"])

    def abrir_ficha() -> None:
        p = escollida()
        if p is None:
            return
        abrir_ficha_persoa(horta_id, p.id)

    def xuntar_con(queda: Persoa) -> None:
        outras = {p.id: f"{p.nome} {p.apelidos or ''}".strip() for p in persoas
                  if p.id != queda.id}
        with ui.dialog().props("persistent") as ventá, ui.card().style("width: min(30rem, 94vw)"):
            ui.label(_("Xuntar con {nome}").format(nome=queda.nome)).classes("text-h6")
            ui.label(
                _(
                    "Todo o da outra (traballos, compras, vendas, papeis, conta) pasa a "
                    "{nome}, e a outra bórrase."
                ).format(nome=queda.nome)
            ).classes("text-caption")
            sae = ui.select(outras, label=_("A outra (a repetida)"), with_input=True).classes(
                "w-full")

            def confirmar() -> None:
                with get_session() as session:
                    actor = usuario_actual(session)
                    q, s = session.get(Persoa, queda.id), session.get(Persoa, sae.value or 0)
                    if actor is None or q is None or s is None:
                        return
                    ok = executar_accion(session, lambda: xuntar_persoas(session, actor, q, s))
                if ok:
                    ui.navigate.reload()

            with ui.row():
                ui.button(_("Xuntar"), icon="merge", on_click=confirmar)
                ui.button(_("Cancelar"), on_click=ventá.close).props("flat")
        ventá.open()

    def xuntar() -> None:
        queda = escollida()
        if queda is None:
            return
        xuntar_con(queda)

    accions_fn["xuntar"] = xuntar_con

    def editar_persoa(p: Persoa) -> None:
        editando["id"] = p.id
        titulo.text = _("Editar persoa ou entidade")
        tipo_persoa.value = p.tipo
        nome.value = p.nome
        apelidos.value = p.apelidos or ""
        nif.value = p.nif or ""
        for campo, entrada in {**contacto, **rexistros}.items():
            valor = getattr(p, campo)
            if campo == "concello_codigo":
                # Un concello de fóra de Galicia gardado antes tamén ten que poder verse
                if valor and valor not in entrada.options:
                    entrada.set_options({**entrada.options, valor: valor})
                entrada.value = valor or None
            else:
                entrada.value = valor or ""
        papeis.value = ([clave for clave in PAPEIS_EQUIPO if p.ten_papel(clave)] if equipo
                        else sorted(das_persoas[p.id]))
        ropo.value = p.ropo_numero or ""
        tipo.value = p.ropo_tipo_carne.value if p.ropo_tipo_carne else None
        caducidade.value = p.ropo_caducidade.isoformat() if p.ropo_caducidade else ""
        regfer.value = p.regfer_numero or ""
        vinculo.value = p.vinculo
        horas_ano.value = "" if p.horas_ano is None else f"{p.horas_ano:g}"
        custo_hora.value = "" if p.custo_hora is None else f"{p.custo_hora:g}"
        formacion.value = p.formacion_agraria or ""
        xenero.value = p.xenero
        nacemento.value = p.data_nacemento.isoformat() if p.data_nacemento else ""
        discapacidade.value = p.discapacidade
        activa.value = p.activa
        rol = accesos[p.id]
        acceso.value = rol.value if rol else "editor"
        motivo_convite.value = ""
        acceso_ata_convite.value = ""
        mostrar_bloques()
        mostrar_acceso()
        dialogo.open()

    def abrir_edicion() -> None:
        p = escollida()
        if p is None:
            return
        editar_persoa(p)

    accions_fn["editar"] = editar_persoa

    with ui.row():
        ui.button(
            _("Nova persoa no equipo") if equipo else _("Novo contacto"),
            icon="person_add",
            on_click=abrir_nova,
        )
        ui.button(_("Editar"), icon="edit", on_click=abrir_edicion).props("outline").classes(
            "so-ordenador"
        )
        ui.button(_("Ficha"), icon="description", on_click=abrir_ficha).props("outline").classes(
            "so-ordenador"
        )
        if e_admin:
            ui.button(
                _("Xuntar con outra"), icon="merge", on_click=xuntar
            ).props("outline").classes("so-ordenador")

    if equipo and e_admin and accesos_rexistrados:
        with ui.column().classes("w-full q-mt-lg gap-2"):
            ui.label(_("Accesos de inspección e auditoría")).classes(
                "text-subtitle1 text-weight-bold"
            )
            filas_accesos = [
                {
                    "id": a.id,
                    "data_hora": a.data_hora.strftime("%d/%m/%Y %H:%M"),
                    "conta": a.usuario.nome if a.usuario else str(a.usuario_id),
                    "seccion": a.seccion,
                }
                for a in accesos_rexistrados
            ]
            ui.table(
                columns=[
                    {"name": "data_hora", "label": _("Data e hora"), "field": "data_hora"},
                    {"name": "conta", "label": _("Conta"), "field": "conta"},
                    {"name": "seccion", "label": _("Sección"), "field": "seccion"},
                ],
                rows=filas_accesos,
                row_key="id",
            ).classes("w-full taboa").props(
                f"flat bordered {TEXTOS_TABOA}"
            )


def _dialogo_categorias(horta_id: int) -> None:
    """Crear, cambiar o nome e borrar categorías. As da app non se borran."""
    with get_session() as session:
        actor = usuario_actual(session)
        cats = listar_categorias(session, actor, horta_id) if actor else []
    with ui.dialog().props("persistent") as ventá, ui.card().style("width: min(30rem, 94vw)"):
        ui.label(_("Categorías dos contactos")).classes("text-h6")
        nomes = {c.id: ui.input(value=c.nome).classes("w-full") for c in cats}
        borrar = {c.id: ui.checkbox(_("Borrar")) for c in cats if c.papel is None}
        nova = ui.input(_("Nova categoría (p.ex. Vendedores)")).classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    return

                def accion() -> None:
                    for c in session.query(Categoria).filter_by(horta_id=horta_id):
                        if c.id in borrar and borrar[c.id].value:
                            borrar_categoria(session, actor, c)
                        elif c.id in nomes and nomes[c.id].value != c.nome:
                            renomear_categoria(session, actor, c, nomes[c.id].value or "")
                    if nova.value:
                        crear_categoria(session, actor, horta_id, nova.value)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=ventá.close).props("flat")
    ventá.open()

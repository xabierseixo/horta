from __future__ import annotations

from typing import Any

from nicegui import app, ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.tempo import EstacionMeteo
from horta.models.usuario import RolGlobal
from horta.services.accesos import rexistrar_acceso
from horta.services.animais import listar_animais
from horta.services.catalogos import describir
from horta.services.catalogos_estado import avisos_catalogos
from horta.services.certificacions import avisos_certificacions
from horta.services.cultivos import (
    listar_cultivos,
    nome_cultivo,
)
from horta.services.documentos import documentos_con_aviso
from horta.services.en_regra import requisitos_en_regra
from horta.services.envio_cue import avisos_cue
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import (
    TIPOS_XIP,
    actualizar_horta,
    comprobar_rol_horta,
    eliminar_horta,
    estado_rexistro,
    listar_hortas_usuario,
)
from horta.services.observacions import avisos_pragas
from horta.services.parcelas import (
    listar_parcelas,
)
from horta.services.persoas import nome_completo, titular_da_horta
from horta.services.recomendacions import recomendacions_pendentes
from horta.services.sensores import avisos_sensores
from horta.services.tarefas import (
    actualizar_tarefa,
    contar_tarefas_pendentes,
    eliminar_tarefa,
    listar_tarefas,
    listar_tarefas_atrasadas,
    listar_tarefas_pendentes_hoxe,
    listar_tarefas_proximas,
    marcar_pendente,
)
from horta.services.tempo import concellos, gardar_lugar
from horta.services.visitas import proximas_visitas
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.dialogo_tarefa import (
    PRIORIDADES_TAREFA,
    dialogo_nova_tarefa,
    opcions_animais,
    opcions_tarefa,
)
from horta.ui.filtros import filtrar_filas
from horta.ui.layout import (
    SECCIONS,
    cabeceira_seccion,
    marco_horta,
    normalizar_seccion,
    url_seccion,
)
from horta.ui.nav import cabeceira_paxina
from horta.ui.numeros import parsear_data
from horta.ui.pages.abonados import seccion_abonados
from horta.ui.pages.analises import seccion_analises
from horta.ui.pages.animais import seccion_animais
from horta.ui.pages.calendario import seccion_calendario
from horta.ui.pages.cartos import seccion_cartos
from horta.ui.pages.certificacions import seccion_certificacions
from horta.ui.pages.coidados_animais import seccion_coidados
from horta.ui.pages.colleitas import seccion_colleitas
from horta.ui.pages.cultivos import seccion_cultivos
from horta.ui.pages.diario import Formularios, boton_apuntar_traballo, seccion_diario
from horta.ui.pages.documentos import seccion_documentos, texto_aviso_documento
from horta.ui.pages.equipo import seccion_equipo
from horta.ui.pages.estatisticas import seccion_estatisticas
from horta.ui.pages.estercos import seccion_estercos
from horta.ui.pages.informes import seccion_informes
from horta.ui.pages.instalacions import seccion_instalacions
from horta.ui.pages.labores import seccion_labores
from horta.ui.pages.lotes import seccion_lotes
from horta.ui.pages.maquinaria import seccion_maquinaria
from horta.ui.pages.movementos_animais import seccion_movementos
from horta.ui.pages.observacions import seccion_observacions
from horta.ui.pages.parcelas import seccion_parcelas
from horta.ui.pages.pastoreos import seccion_pastoreo
from horta.ui.pages.plan_empresa import seccion_plan_empresa
from horta.ui.pages.producions_animais import seccion_producion
from horta.ui.pages.produtos import seccion_produtos
from horta.ui.pages.recomendacions import (
    seccion_recomendacions,
    texto_aviso_recomendacions,
)
from horta.ui.pages.regas import seccion_regas
from horta.ui.pages.sensores import seccion_sensores
from horta.ui.pages.terras import seccion_terras
from horta.ui.pages.tratamentos import seccion_tratamentos_fito
from horta.ui.pages.tratamentos_instalacion import seccion_tratamentos_instalacion
from horta.ui.pages.visitas import seccion_visitas, texto_aviso_proxima_visita
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import CampoLugarTempo, predicion_inicio

_PROPS_TABOA = f'flat bordered no-data-label="{N_("Aínda non hai rexistros")}" {TEXTOS_TABOA}'

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
# Datos da explotación para o caderno da Xunta (1.1)
_DATOS_CADERNO = (
    ("enderezo", N_("Enderezo")),
    ("localidade", N_("Localidade")),
    ("codigo_postal", N_("Código postal")),
    ("provincia", N_("Provincia")),
    ("email", N_("Email")),
    ("rega_clasificacion", N_("Clasificación no REGA (se ten animais)")),
    ("rega_capacidade", N_("Capacidade máxima de animais (REGA)")),
    ("tipo_representacion", N_("Tipo de representación (se asina un representante)")),
)
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_ESTADOS_PARCELA = ("activa", "inactiva")
_ROLES_HORTA = ("admin", "editor", "lector")

_ESTADOS_CULTIVO = ("planificado", "sementado", "plantado", "colleitado", "finalizado")
_UNIDADES_CULTIVO = ("kg", "unidades", "ducias", "mazos")



@ui.page("/hortas/{horta_id}")
def horta_detalle_redirixir(horta_id: int) -> None:
    ui.navigate.to(url_seccion(horta_id, "resumo"))


@ui.page("/hortas/{horta_id}/{seccion}")
def horta_detalle_page(horta_id: int, seccion: str) -> None:
    seccion = normalizar_seccion(seccion)
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
            app.storage.user["ultima_horta"] = horta_id
            rexistrar_acceso(session, actor, horta_id, seccion)
        except PermisoDenegadoError:
            cabeceira_paxina()
            ui.label(_("Non tes acceso a esta explotación")).classes("text-negative")
            return
        horta = session.get(Horta, horta_id)
        if horta is None:
            cabeceira_paxina()
            ui.label(_("Esta explotación xa non existe")).classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        tarefas = listar_tarefas(session, actor, horta_id)
        tarefas_pendentes_hoxe = listar_tarefas_pendentes_hoxe(session, actor, horta_id)
        tarefas_proximas = listar_tarefas_proximas(session, actor, horta_id)
        tarefas_atrasadas = listar_tarefas_atrasadas(session, actor, horta_id)
        n_tarefas_pendentes = contar_tarefas_pendentes(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA
        e_horta_admin = membro.rol == RolHorta.ADMIN
        e_admin_global = actor.rol == RolGlobal.ADMIN
        avisos_admin = avisos_catalogos(session) if e_admin_global else []
        avisos_xunta = avisos_cue(session, actor, horta_id)
        avisos_de_pragas = []
        for a_praga in avisos_pragas(session, actor, horta_id):
            obs = a_praga.observacion
            cultivo_obs = session.get(Cultivo, obs.cultivo_id)
            praga = describir(session, obs.problema_tipo, obs.problema_codigo)
            nome_c = nome_cultivo(cultivo_obs) if cultivo_obs else ""
            avisos_de_pragas.append(f"{nome_c} · {praga}: {a_praga.texto}")
        docs_aviso = documentos_con_aviso(session, actor, horta_id)
        avisos_cert = avisos_certificacions(session, actor, horta_id)
        avisos_sen = avisos_sensores(session, actor, horta_id)
        recs_pendentes = len(recomendacions_pendentes(session, actor, horta_id))
        visitas_proximas = proximas_visitas(session, actor, horta_id)
        horta_nome = horta.nome
        horta_descricion = horta.descricion
        horta_uso_profesional = horta.uso_profesional
        datos_horta = {campo: getattr(horta, campo) or "" for campo, _x in _DATOS_CADERNO}
        horta_tipo_xip = horta.tipo_xip
        horta_fertilizacion = horta.asesoramento_fertilizacion
        titular = titular_da_horta(session, horta_id)
        nome_titular = nome_completo(titular)
        horta_codigo_reaga = horta.codigo_reaga or ""
        horta_codigo_rega = horta.codigo_rega or ""
        lugar_tempo = (horta.concello_ine, horta.estacion_meteo_id, horta.lat, horta.lon)
        estacion_meteo = (session.get(EstacionMeteo, horta.estacion_meteo_id)
                          if horta.estacion_meteo_id else None)
        horta_estacion = estacion_meteo.nome if estacion_meteo else ""
        estado = estado_rexistro(session, horta)
        requisitos = requisitos_en_regra(session, actor, horta)
        hortas_usuario = {h.id: h.nome for h, _x in listar_hortas_usuario(session, actor)}
        nome_usuario = actor.nome

    marco_horta(
        horta_id=horta_id,
        seccion=seccion,
        hortas=hortas_usuario,
        nome_usuario=nome_usuario,
        e_horta_admin=e_horta_admin,
        e_admin_global=e_admin_global,
    )

    if e_horta_admin:
        with (ui.dialog().props("persistent") as dialog_config_horta,
              ui.card().style("width: min(36rem, 94vw)")):
            ui.label(_("Datos da explotación")).classes("text-md font-bold")
            nome_horta_input = ui.input(_("Nome"), value=horta_nome).classes("w-full")
            descricion_horta_input = ui.input(
                _("Descrición"), value=horta_descricion or ""
            ).classes("w-full")
            ui.label(_("Tipo de explotación")).classes("text-caption texto-suave")
            tipo_radio = ui.radio(
                {True: _("Profesional"), False: _("Non profesional")},
                value=horta_uso_profesional,
            ).props("inline")
            with ui.column().classes("w-full gap-1").bind_visibility_from(tipo_radio, "value"):
                reaga_input = ui.input(
                    _("Nº REAGA (ES + 12 díxitos)"), value=horta_codigo_reaga
                ).classes("w-full")
            rega_input = ui.input(
                _("Nº REGA, se ten animais (ES + 12 díxitos)"), value=horta_codigo_rega
            ).classes("w-full")
            # Caderno da Xunta 1.1 e 1.4. O titular, o representante e o asesor son persoas
            with ui.expansion(_("Datos para o caderno")).classes("w-full"):
                datos_inputs = {
                    campo: ui.input(_(etiqueta), value=datos_horta[campo]).classes("w-full")
                    for campo, etiqueta in _DATOS_CADERNO
                }
                tipo_xip_input = ui.select(
                    {k: _(v) for k, v in TIPOS_XIP.items()},
                    label=_("Xestión integrada de pragas (XIP)"),
                    clearable=True,
                    value=horta_tipo_xip,
                ).classes("w-full")
                fertilizacion_input = ui.checkbox(
                    _("Recibe asesoramento en fertilización"),
                    value=horta_fertilizacion,
                )
            ui.label(
                _("A persoa titular, a representante e a asesora indícanse en Equipo.")
            ).classes("text-caption texto-suave")
            with ui.expansion(_("O tempo")).classes("w-full"):
                lugar = CampoLugarTempo()
                ui.label(
                    _(
                        "A estación vale para os traballos sen parcela e para as parcelas "
                        "sen estación propia."
                    )
                ).classes("text-caption texto-suave")

            def abrir_config_horta() -> None:
                lugar.cargar(*lugar_tempo)
                dialog_config_horta.open()

            def gardar_horta() -> None:
                if not nome_horta_input.value:
                    ui.notify(_("O nome é obrigatorio"), type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    horta_obxectivo = session.get(Horta, horta_id)
                    if horta_obxectivo is None:
                        ui.notify(_("Esta explotación xa non existe"), type="negative")
                        return
                    def accion() -> None:
                        actualizar_horta(
                            session,
                            actor_actual,
                            horta_obxectivo,
                            nome=nome_horta_input.value,
                            descricion=descricion_horta_input.value or None,
                            uso_profesional=tipo_radio.value,
                            tipo_xip=tipo_xip_input.value,
                            asesoramento_fertilizacion=fertilizacion_input.value,
                            **{c: (i.value or None) for c, i in datos_inputs.items()},
                            codigo_reaga=reaga_input.value or None,
                            codigo_rega=rega_input.value or None,
                        )
                        gardar_lugar(session, actor_actual, horta_obxectivo,
                                     lugar.concello_ine, lugar.estacion_escollida)

                    gardado = executar_accion(session, accion)
                if not gardado:
                    return
                ui.navigate.reload()

            def eliminar_horta_actual() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    horta_obxectivo = session.get(Horta, horta_id)
                    if horta_obxectivo is None:
                        ui.notify(_("Esta explotación xa non existe"), type="negative")
                        return
                    eliminada = executar_accion(
                        session, lambda: eliminar_horta(session, actor_actual, horta_obxectivo)
                    )
                if not eliminada:
                    return
                ui.navigate.to("/")

            with ui.row().classes("w-full items-center justify-between"):
                with ui.row():
                    ui.button(_("Gardar"), icon="check", on_click=gardar_horta)
                    ui.button(_("Cancelar"), on_click=dialog_config_horta.close).props("flat")
                ui.button(
                    _("Eliminar explotación"),
                    icon="delete",
                    on_click=lambda: confirmar_eliminacion(
                        _(
                            "Eliminar «{nome}» e TODAS as súas parcelas, animais e "
                            "membros? Esta acción non se pode desfacer."
                        ).format(nome=horta_nome),
                        eliminar_horta_actual,
                    ),
                ).props("flat color=negative")

    seccions = {s.clave: s for s in SECCIONS}
    if seccion == "resumo":
        accions = cabeceira_seccion(horta_nome, horta_descricion or _("Inicio"))
        if pode_editar:
            with accions:
                boton_apuntar_traballo(Formularios(horta_id))
        texto_estado, clase_estado = {
            "rexistrada": (_("Explotación rexistrada"), "etiqueta-ok"),
            "en_preparacion": (_("En preparación"), "etiqueta-aviso"),
            "non_profesional": (_("Non profesional"), "etiqueta-ok"),
        }[estado]
        ui.label(_("Estado da explotación")).classes("text-subtitle1 text-weight-bold q-mt-md")
        ui.label(texto_estado).classes(clase_estado)
        for aviso in avisos_admin:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(aviso)
                ui.link(_("Catálogos oficiais"), "/admin/catalogos")
        for aviso in avisos_xunta:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(aviso)
                ui.link(_("Informes"), url_seccion(horta_id, "informes"))
        for aviso_praga in avisos_de_pragas:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(aviso_praga)
                ui.link(_("Seguimento de pragas"), url_seccion(horta_id, "pragas"))
        for doc in docs_aviso:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(texto_aviso_documento(doc))
                ui.link(_("Documentos"), url_seccion(horta_id, "documentos"))
        for aviso_cert in avisos_cert:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(aviso_cert)
                ui.link(_("Certificacións"), url_seccion(horta_id, "certificacions"))
        for aviso_sensor in avisos_sen:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(aviso_sensor)
                ui.link(_("Sensores"), url_seccion(horta_id, "sensores"))
        if recs_pendentes:
            with ui.row().classes("items-center gap-2 q-mt-sm"):
                ui.icon("warning").classes("text-warning")
                ui.label(texto_aviso_recomendacions(recs_pendentes))
                ui.link(_("Recomendacións"), url_seccion(horta_id, "recomendacions"))
        for v_prox in visitas_proximas:
            if v_prox.proxima_visita:
                with ui.row().classes("items-center gap-2 q-mt-sm"):
                    ui.icon("event").classes("text-primary")
                    ui.label(texto_aviso_proxima_visita(v_prox.proxima_visita))
                    ui.link(_("Visitas técnicas"), url_seccion(horta_id, "visitas"))
        if requisitos:
            with ui.column().classes("tarxeta w-full gap-2 q-my-md"):
                ui.label(_("Para estar en regra")).classes("text-subtitle1 text-weight-bold")
                for requisito in requisitos:
                    with ui.row().classes("items-center gap-2"):
                        if requisito.cumprido:
                            ui.icon("check_circle").classes("text-positive")
                        else:
                            ui.icon("radio_button_unchecked").classes("texto-suave")
                        ui.label(requisito.texto)
                        if not requisito.cumprido:
                            ui.label(requisito.axuda).classes("texto-suave text-caption")
        predicion_inicio(lugar_tempo[0], lugar_tempo[1], tarefas)
        _seccion_dashboard(
            len(parcelas),
            len(cultivos),
            len(animais),
            n_tarefas_pendentes,
            tarefas_pendentes_hoxe,
            tarefas_proximas,
            tarefas_atrasadas,
        )
        return
    if seccions[seccion].no_menu:
        ui.link(_("← Diario"), url_seccion(horta_id, "diario")).classes("text-caption")
    cabeceira_seccion(seccions[seccion].etiqueta, horta_nome)
    if seccion == "diario":
        seccion_diario(horta_id, pode_editar)
    elif seccion == "informes":
        seccion_informes(horta_id, horta_uso_profesional)
    elif seccion == "explotacion" and e_horta_admin:
        ui.label(
            {
                "rexistrada": _("Explotación rexistrada"),
                "en_preparacion": _("En preparación"),
                "non_profesional": _("Non profesional"),
            }[estado]
        ).classes("q-mb-md")
        ui.label(
            _("Titular: {nome}").format(nome=nome_titular)
            if nome_titular
            else _("Aínda non se indicou a persoa titular")
        ).classes("q-mb-sm")
        concello_nome = concellos().get(lugar_tempo[0] or "", lugar_tempo[0] or "")
        visibles = [
            (_("Nome"), horta_nome),
            (_("Descrición"), horta_descricion or ""),
            (
                _("Tipo de explotación"),
                _("Profesional") if horta_uso_profesional else _("Non profesional"),
            ),
            (_("Nº REAGA"), horta_codigo_reaga),
            (_("Nº REGA"), horta_codigo_rega),
            *((_(etiqueta), datos_horta[campo]) for campo, etiqueta in _DATOS_CADERNO),
            (_("Concello"), concello_nome),
            (_("Estación de MeteoGalicia"), horta_estacion),
            (
                _("Xestión integrada de pragas (XIP)"),
                _(TIPOS_XIP[horta_tipo_xip]) if horta_tipo_xip in TIPOS_XIP else "",
            ),
            (_("Asesoramento en fertilización"), _("Si") if horta_fertilizacion else ""),
        ]
        with ui.column().classes("tarxeta w-full gap-1 q-mb-md"):
            for etiqueta, valor in visibles:
                if valor:
                    ui.label(f"{etiqueta}: {valor}")
        with ui.row().classes("gap-2"):
            ui.button(
                _("Editar datos da explotación"),
                icon="settings",
                on_click=abrir_config_horta,
            ).props("outline")
            ui.button(
                _("Persoa titular e asesora en Equipo"),
                icon="groups",
                on_click=lambda: ui.navigate.to(url_seccion(horta_id, "equipo")),
            ).props("outline")
    elif seccion == "parcelas":
        seccion_parcelas(horta_id, pode_editar)
    elif seccion == "cultivos":
        seccion_cultivos(horta_id, pode_editar)
    elif seccion == "colleitas":
        seccion_colleitas(horta_id, pode_editar)
    elif seccion == "tratamentos":
        seccion_tratamentos_fito(horta_id, pode_editar)
        seccion_tratamentos_instalacion(horta_id, pode_editar)
    elif seccion == "pragas":
        seccion_observacions(horta_id, pode_editar)
    elif seccion == "recomendacions":
        seccion_recomendacions(horta_id, pode_editar)
    elif seccion == "fertilizacion":
        seccion_abonados(horta_id, pode_editar)
    elif seccion == "estercos":
        seccion_estercos(horta_id, pode_editar)
    elif seccion == "visitas":
        seccion_visitas(horta_id, pode_editar)
    elif seccion == "rega":
        seccion_regas(horta_id, pode_editar)
    elif seccion == "labores":
        seccion_labores(horta_id, pode_editar)
    elif seccion == "analises":
        seccion_analises(horta_id, pode_editar)
    elif seccion == "tarefas":
        _seccion_tarefas(horta_id, tarefas, parcelas, cultivos, pode_editar)
    elif seccion == "animais":
        seccion_animais(horta_id, pode_editar)
    elif seccion == "sensores":
        seccion_sensores(horta_id, pode_editar, e_horta_admin)
    elif seccion == "movementos":
        seccion_movementos(horta_id, pode_editar)
    elif seccion == "producion":
        seccion_producion(horta_id, pode_editar)
    elif seccion == "pastoreo":
        seccion_pastoreo(horta_id, pode_editar)
    elif seccion == "lotes":
        seccion_lotes(horta_id, pode_editar)
    elif seccion == "produtos":
        seccion_produtos(horta_id, pode_editar)
    elif seccion == "coidados":
        seccion_coidados(horta_id, pode_editar)
    elif seccion == "equipo":
        seccion_equipo(horta_id, pode_editar, e_horta_admin)
    elif seccion == "contactos":
        seccion_equipo(horta_id, pode_editar, e_horta_admin, modo="contactos")
    elif seccion == "maquinaria":
        seccion_maquinaria(horta_id, pode_editar)
    elif seccion == "cartos":
        seccion_cartos(horta_id, pode_editar)
    elif seccion == "documentos":
        seccion_documentos(horta_id, pode_editar)
    elif seccion == "calendario":
        seccion_calendario(horta_id, pode_editar)
    elif seccion == "mapa":
        seccion_terras(horta_id, pode_editar)
    elif seccion == "instalacions":
        seccion_instalacions(horta_id, pode_editar)
    elif seccion == "estatisticas":
        seccion_estatisticas(horta_id, pode_editar)
    elif seccion == "plan":
        seccion_plan_empresa(horta_id, pode_editar)
    elif seccion == "certificacions":
        seccion_certificacions(horta_id, pode_editar)


def _seccion_dashboard(
    n_parcelas: int,
    n_cultivos: int,
    n_animais: int,
    n_tarefas_pendentes: int,
    tarefas_hoxe: list,
    tarefas_proximas: list,
    tarefas_atrasadas: list,
) -> None:
    ui.label(_("A explotación en números")).classes("text-subtitle1 text-weight-bold q-mt-md")
    with ui.row().classes("w-full q-gutter-md q-mb-md"):
        with ui.card().classes("items-center"):
            ui.label(str(n_parcelas)).classes("text-h4 font-bold")
            ui.label(_("Parcelas")).classes("text-caption text-grey")
        with ui.card().classes("items-center"):
            ui.label(str(n_cultivos)).classes("text-h4 font-bold")
            ui.label(_("Cultivos")).classes("text-caption text-grey")
        with ui.card().classes("items-center"):
            ui.label(str(n_animais)).classes("text-h4 font-bold")
            ui.label(_("Grupos de animais")).classes("text-caption text-grey")
        with ui.card().classes("items-center"):
            ui.label(str(n_tarefas_pendentes)).classes("text-h4 font-bold")
            ui.label(_("Tarefas pendentes")).classes("text-caption text-grey")

    if tarefas_atrasadas:
        ui.label(
            _("⚠ Tes {n} tarefa(s) atrasada(s)").format(n=len(tarefas_atrasadas))
        ).classes("text-negative text-bold q-mb-md")

    with ui.row().classes("w-full q-gutter-md"):
        with ui.column().classes("col"):
            ui.label(_("Tarefas de hoxe")).classes("text-subtitle1 text-weight-bold")
            if tarefas_hoxe:
                for tarefa in tarefas_hoxe:
                    ui.label(f"☐ {tarefa.descricion}").classes("text-body2")
            else:
                ui.label(_("Non hai tarefas para hoxe.")).classes("text-caption text-grey")
        with ui.column().classes("col"):
            ui.label(_("Próximas actividades")).classes("text-subtitle1 text-weight-bold")
            if tarefas_proximas:
                for tarefa in tarefas_proximas:
                    data_texto = tarefa.data.isoformat() if tarefa.data else "?"
                    ui.label(f"{data_texto} — {tarefa.descricion}").classes("text-body2")
            else:
                ui.label(_("Non hai próximas actividades.")).classes("text-caption text-grey")


def _seccion_tarefas(
    horta_id: int, tarefas: list, parcelas: list, cultivos: list, pode_editar: bool
) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}
    cultivos_por_id = {c.id: c.especie for c in cultivos}
    opcions_parcela = {"": _("(sen parcela)"), **{p.id: p.nome for p in parcelas}}
    opcions_cultivo = {"": _("(sen cultivo)"), **{c.id: c.especie for c in cultivos}}

    def _parsear_data(texto: str) -> Any:
        if not texto:
            return None
        return parsear_data(texto)

    if pode_editar:
        abrir_nova_tarefa = dialogo_nova_tarefa(horta_id)
        formularios = Formularios(horta_id)
        with get_session() as session:
            actor = usuario_actual(session)
            opcions_tipo, opcions_persoa = (
                opcions_tarefa(session, actor, horta_id) if actor else ({}, {}))
            opcions_animal = opcions_animais(session, actor, horta_id) if actor else {}

    with ui.row().classes("w-full items-center justify-between"):
        ui.space()
        if pode_editar:
            ui.button(_("Nova tarefa"), icon="add", on_click=abrir_nova_tarefa)

    todas_as_filas = [
        {
            "id": t.id,
            "descricion": t.descricion,
            "parcela": parcelas_por_id.get(t.parcela_id, "") if t.parcela_id else "",
            "cultivo": cultivos_por_id.get(t.cultivo_id, "") if t.cultivo_id else "",
            "data": t.data.isoformat() if t.data else "",
            "data_limite": t.data_limite.isoformat() if t.data_limite else "",
            "prioridade": t.prioridade,
            "estado": t.estado,
        }
        for t in tarefas
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input(_("Buscar")).props("dense clearable")
        estado_select = ui.select(
            {"Todos": _("Todos"), "pendente": _("pendente"), "feito": _("feito")},
            label=_("Estado"),
            value="Todos",
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "descricion", "label": _("Descrición"), "field": "descricion"},
                {"name": "parcela", "label": _("Parcela"), "field": "parcela"},
                {"name": "cultivo", "label": _("Cultivo"), "field": "cultivo"},
                {"name": "data", "label": _("Data"), "field": "data"},
                {"name": "data_limite", "label": _("Data límite"), "field": "data_limite"},
                {"name": "prioridade", "label": _("Prioridade"), "field": "prioridade"},
                {"name": "estado", "label": _("Estado"), "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(f'flat bordered no-data-label="{_("Aínda non hai rexistros")}" {TEXTOS_TABOA}')
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["descricion", "parcela", "cultivo", "prioridade"],
            {"estado": estado_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button(_("Editar"), icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            _("Marcar feita/pendente"),
            icon="check_circle",
            on_click=lambda: alternar_estado(),
        ).props("outline")
        ui.button(
            _("Eliminar"),
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                _(
                    "Eliminar a tarefa «{descricion}»? Esta acción non se pode desfacer."
                ).format(descricion=taboa.selected[0]["descricion"]),
                eliminar_seleccionada,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog().props("persistent") as dialog_editar, ui.card():
        ui.label(_("Editar tarefa")).classes("text-md font-bold")
        descricion_edit = ui.input(_("Descrición"))
        tipo_edit = ui.select(opcions_tipo, label=_("Que traballo é"))
        persoa_edit = ui.select(opcions_persoa, label=_("Quen o vai facer"))
        parcela_edit = ui.select(opcions_parcela, label=_("Parcela"))
        cultivo_edit = ui.select(opcions_cultivo, label=_("Cultivo"))
        animal_edit = ui.select(opcions_animal, label=_("Animais"))
        data_edit = campo_data(_("Data (opcional)"))
        data_limite_edit = campo_data(_("Data límite (opcional)"))
        prioridade_edit = ui.select(list(PRIORIDADES_TAREFA), label=_("Prioridade"))
        notas_edit = ui.textarea(_("Notas"))

        def gardar() -> None:
            if not taboa.selected:
                return
            tarefa_id = taboa.selected[0]["id"]
            if not descricion_edit.value:
                ui.notify(_("A descrición é obrigatoria"), type="negative")
                return
            try:
                data_valor = _parsear_data(data_edit.value)
                data_limite_valor = _parsear_data(data_limite_edit.value)
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        t
                        for t in listar_tarefas(session, actor_actual, horta_id)
                        if t.id == tarefa_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify(_("Esa tarefa xa non existe"), type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_tarefa(
                        session,
                        actor_actual,
                        obxectivo,
                        descricion=descricion_edit.value,
                        tipo=tipo_edit.value or None,
                        persoa_id=persoa_edit.value or None,
                        parcela_id=parcela_edit.value or None,
                        cultivo_id=cultivo_edit.value or None,
                        animal_id=animal_edit.value or None,
                        data=data_valor,
                        data_limite=data_limite_valor,
                        prioridade=prioridade_edit.value,
                        notas=notas_edit.value or None,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        tarefa_id = taboa.selected[0]["id"]
        tarefa_completa = next((t for t in tarefas if t.id == tarefa_id), None)
        if tarefa_completa is None:
            return
        descricion_edit.value = tarefa_completa.descricion
        tipo_edit.value = tarefa_completa.tipo or ""
        persoa_edit.value = (tarefa_completa.persoa_id
                             if tarefa_completa.persoa_id in opcions_persoa else "")
        parcela_edit.value = tarefa_completa.parcela_id or ""
        cultivo_edit.value = tarefa_completa.cultivo_id or ""
        animal_edit.value = (tarefa_completa.animal_id
                             if tarefa_completa.animal_id in opcions_animal else "")
        data_edit.value = tarefa_completa.data.isoformat() if tarefa_completa.data else ""
        data_limite_edit.value = (
            tarefa_completa.data_limite.isoformat() if tarefa_completa.data_limite else ""
        )
        prioridade_edit.value = tarefa_completa.prioridade
        notas_edit.value = tarefa_completa.notas or ""
        dialog_editar.open()

    def alternar_estado() -> None:
        if not taboa.selected:
            return
        tarefa_id = taboa.selected[0]["id"]
        tarefa_completa = next((t for t in tarefas if t.id == tarefa_id), None)
        if tarefa_completa is None:
            return
        if tarefa_completa.estado != "feito":
            formularios.facer(tarefa_completa)
            return
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (t for t in listar_tarefas(session, actor_actual, horta_id) if t.id == tarefa_id),
                None,
            )
            if obxectivo is None:
                ui.notify(_("Esa tarefa xa non existe"), type="negative")
                return
            feito = executar_accion(
                session, lambda: marcar_pendente(session, actor_actual, obxectivo))
        if not feito:
            return
        ui.navigate.reload()

    def eliminar_seleccionada() -> None:
        if not taboa.selected:
            return
        tarefa_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (t for t in listar_tarefas(session, actor_actual, horta_id) if t.id == tarefa_id),
                None,
            )
            if obxectivo is None:
                ui.notify(_("Esa tarefa xa non existe"), type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_tarefa(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()

"""Sección de seguimento de pragas, enfermidades e malas herbas (GIP)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.observacion import LimiarPraga, ObservacionPraga
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
from horta.services.catalogos import describir, valores_vixentes
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.fito_consulta import (
    etiqueta_problema,
    nomes_comuns_problemas,
    problemas_do_cultivo,
)
from horta.services.observacions import (
    METODOS,
    NIVEIS,
    TIPOS_PROBLEMA,
    UNIDADES_CONTO,
    actualizar_observacion,
    avisos_pragas,
    crear_observacion,
    dar_de_baixa_limiar,
    dar_de_baixa_observacion,
    gardar_limiar,
    limiar_para,
    listar_limiares,
    listar_observacions,
    supera_limiar,
)
from horta.services.persoas import listar_quen
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.fotos import abrir_fotos
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pasos_tratamento import ordenar_problemas
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

OPCIONS_TIPO_PROBLEMA: dict[str, str] = {
    "praga": "Praga",
    "enfermidade": "Enfermidade",
    "mala_herba": "Mala herba",
}


def texto_conto_ou_nivel(
    conto: float | None,
    unidade: str | None = None,
    nivel: str | None = None,
) -> str:
    """Texto descritivo do conto ou nivel observado para a táboa e as tarxetas."""
    nivel_str = NIVEIS.get(nivel, nivel) if nivel else ""
    if conto is not None:
        u_str = UNIDADES_CONTO.get(unidade, unidade).lower() if unidade else ""
        txt = f"{conto:g} {u_str}".strip() if u_str else f"{conto:g}"
        if nivel_str:
            txt = f"{txt} ({nivel_str})"
        return txt
    if nivel_str:
        return nivel_str
    return ""


def texto_limiar(limiar: LimiarPraga | float | None) -> str:
    """Valor numérico do limiar de intervención ou '—' se non hai limiar."""
    if limiar is None:
        return "—"
    valor = limiar.valor if hasattr(limiar, "valor") else limiar
    if valor is None:
        return "—"
    return f"{valor:g}"


def texto_supera(e_supera: bool) -> str:
    """Indica 'Si' cando a observación supera o limiar ou baleiro no caso contrario."""
    return "Si" if e_supera else ""


LIGAZON_GUIAS_MAPA = (
    "https://www.mapa.gob.es/es/agricultura/temas/sanidad-vegetal/"
    "productos-fitosanitarios/guias-gestion-plagas"
)

HINT_FONTE_LIMIAR = (
    "Por exemplo, a guía de xestión integrada de pragas do MAPA para este cultivo"
)


def texto_cultivo_limiar(
    cultivo_siex_codigo: int | None,
    cultivos_horta: list[Any] | None = None,
) -> str:
    """Nome do cultivo asociado ao limiar ou 'Xeral' se aplica a todos."""
    if cultivo_siex_codigo is None:
        return "Xeral (todos os cultivos)"
    if cultivos_horta:
        coincidentes = [
            nome_cultivo(c)
            for c in cultivos_horta
            if getattr(c, "cultivo_siex_codigo", None) == cultivo_siex_codigo
        ]
        if coincidentes:
            return ", ".join(dict.fromkeys(coincidentes))
    return f"Cultivo SIEX {cultivo_siex_codigo}"


def opcions_grafica_evolucion(
    observacions: list[Any],
    problemas_nomes: dict[Any, str] | None = None,
    limiares: dict[Any, Any] | None = None,
) -> dict[str, Any] | None:
    """Configuración de ui.echart coa evolución temporal do conto por problema.

    Xera unha liña por cada problema observado con conto numérico e, se existe
    un limiar para ese problema, debúxase como liña horizontal discontinua (markLine).
    """
    obs_con_conto = [o for o in observacions if getattr(o, "conto", None) is not None]
    if not obs_con_conto:
        return None

    datas_unicas = sorted({o.data for o in obs_con_conto})
    datas_str = [d.strftime("%d/%m/%Y") for d in datas_unicas]

    chaves_problemas: list[tuple[str, str]] = list(
        dict.fromkeys((o.problema_tipo, o.problema_codigo) for o in obs_con_conto)
    )

    nomes = problemas_nomes or {}
    lim_map = limiares or {}
    series: list[dict[str, Any]] = []

    for tipo, cod in chaves_problemas:
        chave = (tipo, cod)
        nome = nomes.get(chave) or nomes.get(cod) or f"{tipo}: {cod}"
        valores: list[float | None] = []
        for d in datas_unicas:
            obs_dia = [
                o
                for o in obs_con_conto
                if o.data == d and (o.problema_tipo, o.problema_codigo) == chave
            ]
            if obs_dia:
                valores.append(float(obs_dia[-1].conto))
            else:
                valores.append(None)

        serie: dict[str, Any] = {
            "name": nome,
            "type": "line",
            "data": valores,
            "connectNulls": True,
        }

        lim_obj = lim_map.get(chave)
        if lim_obj is None:
            lim_obj = lim_map.get(cod)

        valor_limiar: float | None = None
        if isinstance(lim_obj, (int, float)):
            valor_limiar = float(lim_obj)
        elif hasattr(lim_obj, "valor") and lim_obj.valor is not None:
            valor_limiar = float(lim_obj.valor)

        if valor_limiar is not None:
            serie["markLine"] = {
                "lineStyle": {"type": "dashed"},
                "data": [{"yAxis": valor_limiar, "name": "Limiar"}],
            }

        series.append(serie)

    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 0},
        "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
        "xAxis": {"type": "category", "data": datas_str},
        "yAxis": {"type": "value", "name": "Conto"},
        "series": series,
    }


def seccion_observacions(horta_id: int, pode_editar: bool) -> None:
    """Pantalla principal de seguimento de pragas: avisos, filtro, táboa e accións."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        observacions = listar_observacions(session, actor, horta_id)
        avisos = avisos_pragas(session, actor, horta_id)
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {
            c.id: f"{nome_cultivo(c)} — {parcelas.get(c.parcela_id, '')}"
            for c in cultivos_horta
        }
        nomes_comuns = {t: nomes_comuns_problemas(session, t) for t in TIPOS_PROBLEMA}
        problemas_opcions: dict[str, dict[str, str]] = {
            t: {
                v.codigo: etiqueta_problema(v.descricion, nomes_comuns[t].get(v.codigo, []))
                for v in valores_vixentes(session, t)
            }
            for t in TIPOS_PROBLEMA
        }

        filas = []
        for obs in observacions:
            limiar = None
            if obs.unidade_conto:
                limiar = limiar_para(
                    session,
                    horta_id,
                    obs.cultivo_id,
                    obs.problema_tipo,
                    obs.problema_codigo,
                    obs.metodo,
                    obs.unidade_conto,
                )
            supera = limiar is not None and supera_limiar(obs, limiar)
            prob_txt = (
                problemas_opcions.get(obs.problema_tipo, {}).get(obs.problema_codigo)
                or describir(session, obs.problema_tipo, obs.problema_codigo)
            )
            filas.append(
                {
                    "id": obs.id,
                    "cultivo_id": obs.cultivo_id,
                    "data": f"{obs.data:%d/%m/%Y}",
                    "cultivo": cultivos.get(obs.cultivo_id, ""),
                    "problema": prob_txt,
                    "metodo": METODOS.get(obs.metodo, obs.metodo),
                    "conto": texto_conto_ou_nivel(obs.conto, obs.unidade_conto, obs.nivel),
                    "limiar": texto_limiar(limiar),
                    "supera": texto_supera(supera),
                }
            )

    with ui.column().classes("tarxeta w-full gap-1 q-mb-md"):
        ui.label("Avisos de pragas e enfermidades").classes(
            "text-subtitle1 text-weight-bold"
        )
        if avisos:
            for a in avisos:
                c_nome = cultivos.get(a.observacion.cultivo_id, "")
                p_nome = (
                    problemas_opcions.get(a.observacion.problema_tipo, {})
                    .get(a.observacion.problema_codigo)
                    or a.observacion.problema_codigo
                )
                with ui.row().classes("items-center gap-2"):
                    ui.icon("warning").classes("text-negative")
                    ui.label(f"{c_nome} · {p_nome}: {a.texto}").classes("text-negative")
        else:
            ui.label("Ningunha praga supera o limiar nas dúas últimas semanas").classes(
                "texto-suave"
            )

    with ui.row().classes("w-full items-center q-mb-sm"):
        opcions_filtro = {0: "Todos os cultivos", **cultivos}
        filtro_cultivo = ui.select(
            opcions_filtro, value=0, label="Filtrar por cultivo"
        ).classes("w-64")

    columnas = [
        {"name": "data", "label": "Data", "field": "data"},
        {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
        {"name": "problema", "label": "Problema", "field": "problema"},
        {"name": "metodo", "label": "Método", "field": "metodo"},
        {"name": "conto", "label": "Conto ou nivel", "field": "conto"},
        {"name": "limiar", "label": "Limiar", "field": "limiar"},
        {
            "name": "supera",
            "label": "Supera",
            "field": "supera",
            "classes": "text-negative text-weight-bold",
        },
    ]

    taboa = (
        ui.table(
            columns=columnas,
            rows=filas,
            row_key="id",
            selection="single" if pode_editar else None,
        )
        .classes("w-full taboa so-ordenador")
        .props(f'flat bordered no-data-label="Aínda non hai observacións" {TEXTOS_TABOA}')
    )

    taboa.add_slot(
        "body-cell-supera",
        """
        <q-td :props="props">
            <span class="text-negative text-weight-bold">{{ props.value }}</span>
        </q-td>
        """,
    )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    debuxar_tarxetas = tarxetas_da_taboa(
        taboa, "data", ["cultivo", "problema", "conto"], accions_tarxeta
    )

    @ui.refreshable
    def debuxar_grafica() -> None:
        cid = filtro_cultivo.value
        c_filtrado = cid if (cid and cid != 0) else None
        obs_c = [
            o
            for o in observacions
            if (c_filtrado is None or o.cultivo_id == c_filtrado) and o.conto is not None
        ]
        if not obs_c:
            return

        limiares_map: dict[tuple[str, str], float] = {}
        with get_session() as session:
            for o in obs_c:
                chave = (o.problema_tipo, o.problema_codigo)
                if chave not in limiares_map and o.unidade_conto:
                    lim = limiar_para(
                        session,
                        horta_id,
                        c_filtrado or o.cultivo_id,
                        o.problema_tipo,
                        o.problema_codigo,
                        o.metodo,
                        o.unidade_conto,
                    )
                    if lim is not None and lim.valor is not None:
                        limiares_map[chave] = lim.valor

        nomes_dict = {
            (t, cod): problemas_opcions.get(t, {}).get(cod, cod)
            for t in TIPOS_PROBLEMA
            for cod in problemas_opcions.get(t, {})
        }
        opcions = opcions_grafica_evolucion(
            obs_c,
            problemas_nomes=nomes_dict,
            limiares=limiares_map,
        )
        if opcions:
            with ui.column().classes("tarxeta w-full gap-1 q-pa-md q-my-md"):
                titulo = (
                    f"Evolución do conto — {cultivos.get(c_filtrado, '')}"
                    if c_filtrado
                    else "Evolución do conto por problema"
                )
                ui.label(titulo).classes("text-subtitle1 text-weight-bold")
                ui.echart(opcions).classes("w-full").style("height: 320px")

    debuxar_grafica()

    def refrescar_taboa() -> None:
        cid = filtro_cultivo.value
        if cid and cid != 0:
            taboa.rows = [f for f in filas if f["cultivo_id"] == cid]
        else:
            taboa.rows = list(filas)
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
        taboa.update()
        debuxar_tarxetas.refresh()
        debuxar_grafica.refresh()

    filtro_cultivo.on_value_change(refrescar_taboa)

    abrir_limiares = dialogo_limiares(horta_id, pode_editar)

    if not pode_editar:
        with ui.row().classes("gap-2 items-center"):
            ui.button("Limiares", icon="tune", on_click=abrir_limiares).props("outline")
        return

    abrir = dialogo_observacion(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha observación na táboa", type="warning")
            return
        obs_id = taboa.selected[0]["id"]
        with get_session() as session:
            obs = session.get(ObservacionPraga, obs_id)
            if obs is not None:
                abrir(obs)

    def fotos() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha observación na táboa", type="warning")
            return
        obs_id = taboa.selected[0]["id"]
        abrir_fotos(horta_id, "observacion", obs_id, "Observación de pragas", pode_editar)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha observación na táboa", type="warning")
            return
        obs_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                obs = session.get(ObservacionPraga, obs_id)
                if actor_actual is None or obs is None:
                    return
                ok = executar_accion(
                    session,
                    lambda: dar_de_baixa_observacion(session, actor_actual, obs),
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta observación? Non se borra: consérvase no histórico.",
            confirmar,
        )

    accions_tarxeta += [
        ("Editar", "edit", editar),
        ("Fotos", "photo_camera", fotos),
        ("Dar de baixa", "archive", dar_de_baixa),
    ]

    with ui.row().classes("gap-2 items-center"):
        ui.button("Nova observación", icon="add", on_click=lambda: abrir(None))
        ui.button("Limiares", icon="tune", on_click=abrir_limiares).props("outline")
        with ui.row().classes("so-ordenador gap-2"):
            ui.button("Editar", icon="edit", on_click=editar).props("outline")
            ui.button("Fotos", icon="photo_camera", on_click=fotos).props("outline")
            ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_observacion(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de rexistrar ou editar unha observación e devolve quen o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_: None
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {
            c.id: f"{nome_cultivo(c)} — {parcelas.get(c.parcela_id, '')}"
            for c in cultivos_horta
        }
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        estados_fenoloxicos = {
            v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
            for v in valores_vixentes(session, "estado_fenoloxico")
        }
        nomes_comuns = {t: nomes_comuns_problemas(session, t) for t in TIPOS_PROBLEMA}
        opcions_problemas = {
            t: {
                v.codigo: etiqueta_problema(v.descricion, nomes_comuns[t].get(v.codigo, []))
                for v in valores_vixentes(session, t)
            }
            for t in TIPOS_PROBLEMA
        }
        problemas_cultivo = {
            c.id: {
                tipo: problemas_do_cultivo(session, c.cultivo_siex_codigo, tipo)
                for tipo in TIPOS_PROBLEMA
            }
            for c in cultivos_horta
            if c.cultivo_siex_codigo is not None
        }

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with (
        ui.dialog().props("persistent") as dialogo,
        ui.card().style("width: min(36rem, 94vw)"),
    ):
        titulo = ui.label("Nova observación").classes("text-h6")
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        with ui.row().classes("w-full no-wrap gap-2"):
            tipo_problema = ui.select(
                OPCIONS_TIPO_PROBLEMA, value="praga", label="Tipo de problema"
            ).classes("w-44")
            problema = ui.select({}, label="Problema", with_input=True).classes("grow")
        metodo = ui.select(METODOS, value="trampa", label="Método").classes("w-full")
        with ui.row().classes("w-full no-wrap gap-2"):
            conto = ui.input("Conto").classes("col")
            unidade = ui.select(
                UNIDADES_CONTO, label="Unidade de conto", clearable=True
            ).classes("col")
        nivel = ui.select(NIVEIS, label="Nivel", clearable=True).classes("w-full")
        estado_fenoloxico = ui.select(
            estados_fenoloxicos, label="Estado fenolóxico", clearable=True
        ).classes("w-full")
        persoa = ui.select(persoas, label="Quen o observou").classes("w-full")
        notas = ui.textarea("Notas").classes("w-full")

        def actualizar_problemas(codigo_escollido: str | None = None) -> None:
            t = tipo_problema.value or "praga"
            cid = cultivo.value
            do_cultivo = problemas_cultivo.get(cid, {}).get(t, set()) if cid else set()
            escollido = codigo_escollido if codigo_escollido is not None else problema.value
            novas = ordenar_problemas(opcions_problemas.get(t, {}), do_cultivo, escollido)
            problema.options = novas
            if escollido in novas:
                problema.value = escollido
            elif problema.value not in novas:
                problema.value = None
            problema.update()

        cultivo.on_value_change(lambda: actualizar_problemas())
        tipo_problema.on_value_change(lambda: actualizar_problemas())

        def gardar() -> None:
            if not cultivo.value:
                ui.notify("Escolle un cultivo", type="warning")
                return
            inicio = parsear_data(data.value)
            if inicio is None:
                ui.notify("Indica a data", type="warning")
                return
            if not tipo_problema.value or not problema.value:
                ui.notify("Escolle o problema", type="warning")
                return
            if not metodo.value:
                ui.notify("Escolle o método", type="warning")
                return
            c_val = parsear_decimal(conto.value)
            n_val = nivel.value if nivel.value else None
            if c_val is None and not n_val:
                ui.notify("Indica o conto ou o nivel da observación", type="warning")
                return
            if c_val is not None and not unidade.value:
                ui.notify("Indica a unidade de conto", type="warning")
                return
            if not persoa.value:
                ui.notify("Indica quen observou", type="warning")
                return

            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    u_val = unidade.value if c_val is not None else None
                    fenoloxico = estado_fenoloxico.value or None
                    notas_txt = notas.value.strip() if notas.value and notas.value.strip() else None
                    if editando["id"] is None:
                        novo = crear_observacion(
                            session,
                            actor_actual,
                            horta_id,
                            cultivo_id=cultivo.value,
                            data=inicio,
                            problema_tipo=tipo_problema.value,
                            problema_codigo=problema.value,
                            metodo=metodo.value,
                            conto=c_val,
                            unidade_conto=u_val,
                            nivel=n_val,
                            estado_fenoloxico=fenoloxico,
                            notas=notas_txt,
                            persoa_id=persoa.value,
                        )
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        obs_existente = session.get(ObservacionPraga, editando["id"])
                        if obs_existente is not None:
                            actualizar_observacion(
                                session,
                                actor_actual,
                                obs_existente,
                                cultivo_id=cultivo.value,
                                data=inicio,
                                problema_tipo=tipo_problema.value,
                                problema_codigo=problema.value,
                                metodo=metodo.value,
                                conto=c_val,
                                unidade_conto=u_val,
                                nivel=n_val,
                                estado_fenoloxico=fenoloxico,
                                notas=notas_txt,
                                persoa_id=persoa.value,
                            )

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("observacion", data.value)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(
        obs: ObservacionPraga | None = None,
        tarefa: Tarefa | None = None,
    ) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = obs.id if obs else None
        titulo.text = "Editar observación" if obs else "Nova observación"
        cultivo.value = (
            obs.cultivo_id
            if obs
            else (tarefa.cultivo_id if tarefa and tarefa.cultivo_id in cultivos else None)
        )
        data.value = (obs.data if obs else date.today()).isoformat()
        tipo_problema.value = obs.problema_tipo if obs else "praga"
        actualizar_problemas(codigo_escollido=obs.problema_codigo if obs else None)
        problema.value = obs.problema_codigo if obs else None
        metodo.value = obs.metodo if obs else "trampa"
        conto.value = f"{obs.conto:g}" if obs and obs.conto is not None else ""
        unidade.value = obs.unidade_conto if obs else None
        nivel.value = obs.nivel if obs else None
        estado_fenoloxico.value = obs.estado_fenoloxico if obs else None
        persoa.value = (
            (obs.persoa_id if obs.persoa_id in persoas else None)
            if obs
            else proposta_quen(horta_id, tarefa)
        )
        notas.value = obs.notas or "" if obs else ""
        dialogo.open()

    return abrir


def dialogo_limiares(horta_id: int, pode_editar: bool = True) -> Callable[[], None]:
    """Constrúe o diálogo coa táboa de limiares e o formulario para engadir un."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda: None
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        nomes_comuns = {t: nomes_comuns_problemas(session, t) for t in TIPOS_PROBLEMA}
        opcions_problemas = {
            t: {
                v.codigo: etiqueta_problema(v.descricion, nomes_comuns[t].get(v.codigo, []))
                for v in valores_vixentes(session, t)
            }
            for t in TIPOS_PROBLEMA
        }
        problemas_cultivo = {
            c.id: {
                tipo: problemas_do_cultivo(session, c.cultivo_siex_codigo, tipo)
                for tipo in TIPOS_PROBLEMA
            }
            for c in cultivos_horta
            if c.cultivo_siex_codigo is not None
        }

    opcions_cultivo: dict[int, str] = {
        c.id: f"{nome_cultivo(c)} — {parcelas.get(c.parcela_id, '')}"
        for c in cultivos_horta
    }
    cultivo_siex_map: dict[int, int | None] = {
        c.id: c.cultivo_siex_codigo for c in cultivos_horta
    }

    with (
        ui.dialog().props("persistent") as dialogo,
        ui.card().style("width: min(56rem, 95vw); max-height: 90vh").classes("overflow-y-auto"),
    ):
        ui.label("Limiares de intervención (GIP)").classes("text-h6")

        @ui.refreshable
        def debuxar_taboa_limiares() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    return
                limiares = listar_limiares(session, actor_actual, horta_id)

            filas_limiares = []
            for lim in limiares:
                filas_limiares.append(
                    {
                        "id": lim.id,
                        "cultivo": texto_cultivo_limiar(lim.cultivo_siex_codigo, cultivos_horta),
                        "problema": (
                            opcions_problemas.get(lim.problema_tipo, {}).get(lim.problema_codigo)
                            or lim.problema_codigo
                        ),
                        "metodo": METODOS.get(lim.metodo, lim.metodo),
                        "limiar": f"{lim.valor:g} {lim.unidade_conto}",
                        "fonte": lim.fonte,
                    }
                )

            columnas_limiares = [
                {"name": "cultivo", "label": "Cultivo", "field": "cultivo", "align": "left"},
                {"name": "problema", "label": "Problema", "field": "problema", "align": "left"},
                {"name": "metodo", "label": "Método", "field": "metodo", "align": "left"},
                {"name": "limiar", "label": "Limiar", "field": "limiar", "align": "left"},
                {"name": "fonte", "label": "Fonte", "field": "fonte", "align": "left"},
            ]
            if pode_editar:
                columnas_limiares.append(
                    {"name": "accions", "label": "", "field": "accions", "align": "right"}
                )

            taboa_lim = (
                ui.table(
                    columns=columnas_limiares,
                    rows=filas_limiares,
                    row_key="id",
                )
                .classes("w-full taboa q-my-sm")
                .props(
                    f'flat bordered dense no-data-label="Aínda non hai limiares configurados" '
                    f"{TEXTOS_TABOA}"
                )
            )
            if pode_editar:

                def dar_de_baixa(lim_id: int) -> None:
                    def confirmar() -> None:
                        with get_session() as s:
                            act = usuario_actual(s)
                            lim_obx = s.get(LimiarPraga, lim_id)
                            if act and lim_obx:
                                ok = executar_accion(
                                    s, lambda: dar_de_baixa_limiar(s, act, lim_obx)
                                )
                                if ok:
                                    ui.notify("Limiar eliminado", type="positive")
                                    debuxar_taboa_limiares.refresh()
                                    ui.navigate.reload()

                    confirmar_eliminacion(
                        "Dar de baixa este limiar de intervención? Non se borra: "
                        "consérvase no histórico.",
                        confirmar,
                    )

                taboa_lim.add_slot(
                    "body-cell-accions",
                    """
                    <q-td :props="props" auto-width>
                        <q-btn flat round dense icon="delete" color="negative"
                               @click="() => $parent.$emit('eliminar', props.row.id)" />
                    </q-td>
                    """,
                )
                taboa_lim.on("eliminar", lambda e: dar_de_baixa(e.args))

        debuxar_taboa_limiares()

        if pode_editar:
            ui.label("Engadir ou actualizar limiar").classes(
                "text-subtitle1 text-weight-bold q-mt-md"
            )
            cultivo_sel = ui.select(
                opcions_cultivo,
                label="Cultivo (opcional: baleiro para xeral)",
                clearable=True,
                with_input=True,
            ).classes("w-full")

            with ui.row().classes("w-full no-wrap gap-2"):
                tipo_prob = ui.select(
                    OPCIONS_TIPO_PROBLEMA, value="praga", label="Tipo de problema"
                ).classes("w-44")
                prob_sel = ui.select({}, label="Problema", with_input=True).classes("grow")

            with ui.row().classes("w-full no-wrap gap-2"):
                metodo_sel = ui.select(METODOS, value="trampa", label="Método").classes("col")
                unidade_sel = ui.select(
                    UNIDADES_CONTO, value="capturas por trampa", label="Unidade de conto"
                ).classes("col")
                valor_input = ui.input("Valor").classes("w-28")

            fonte_input = (
                ui.input("Fonte")
                .classes("w-full")
                .props(f'hint="{HINT_FONTE_LIMIAR}" persistent-hint')
            )

            def actualizar_problemas_limiar() -> None:
                t = tipo_prob.value or "praga"
                cid = cultivo_sel.value
                do_cultivo = (
                    problemas_cultivo.get(cid, {}).get(t, set())
                    if cid
                    else set()
                )
                novas = ordenar_problemas(
                    opcions_problemas.get(t, {}), do_cultivo, prob_sel.value
                )
                prob_sel.options = novas
                if prob_sel.value not in novas:
                    prob_sel.value = None
                prob_sel.update()

            cultivo_sel.on_value_change(actualizar_problemas_limiar)
            tipo_prob.on_value_change(actualizar_problemas_limiar)
            actualizar_problemas_limiar()

            def gardar() -> None:
                if not tipo_prob.value or not prob_sel.value:
                    ui.notify("Escolle o problema", type="warning")
                    return
                if not metodo_sel.value:
                    ui.notify("Escolle o método", type="warning")
                    return
                if not unidade_sel.value:
                    ui.notify("Escolle a unidade de conto", type="warning")
                    return
                v_num = parsear_decimal(valor_input.value)
                if v_num is None or v_num < 0:
                    ui.notify("Indica un valor numérico non negativo", type="warning")
                    return
                if not fonte_input.value or not fonte_input.value.strip():
                    ui.notify("A fonte é obrigatoria", type="warning")
                    return

                with get_session() as s:
                    act = usuario_actual(s)
                    if act is None:
                        pechar_sesion()
                        return
                    cid = cultivo_sel.value
                    siex_cod = cultivo_siex_map.get(cid) if cid else None
                    ok = executar_accion(
                        s,
                        lambda: gardar_limiar(
                            s,
                            act,
                            horta_id,
                            problema_tipo=tipo_prob.value,
                            problema_codigo=prob_sel.value,
                            metodo=metodo_sel.value,
                            unidade_conto=unidade_sel.value,
                            valor=v_num,
                            fonte=fonte_input.value.strip(),
                            cultivo_siex_codigo=siex_cod,
                        ),
                    )
                if ok:
                    ui.notify("Limiar gardado con éxito", type="positive")
                    valor_input.value = ""
                    fonte_input.value = ""
                    debuxar_taboa_limiares.refresh()
                    ui.navigate.reload()

            with ui.row().classes("q-mt-sm"):
                ui.button("Gardar limiar", icon="check", on_click=gardar)

        with ui.row().classes("w-full items-center justify-between q-mt-md"):
            ui.link(
                "Guías de xestión integrada de pragas do MAPA",
                LIGAZON_GUIAS_MAPA,
                new_tab=True,
            ).classes("text-caption")
            ui.button("Pechar", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        debuxar_taboa_limiares.refresh()
        dialogo.open()

    return abrir

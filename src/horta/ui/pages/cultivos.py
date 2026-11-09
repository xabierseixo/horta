"""Sección Cultivos: un só formulario para crear e editar, cos campos do REA."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.cultivo import Cultivo
from horta.services.catalogos import buscar_cultivos, listar_variedades, valores_vixentes
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    estado_cultivo,
    estados_cultivos,
    listar_cultivos,
    nome_cultivo,
    ten_rexistros,
)
from horta.services.historial import aviso_rotacion
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_quen
from horta.services.textos_catalogo import texto_catalogo
from horta.services.zonas import listar_zonas
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campo_produto import opcions_entradas
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA

_ESTADOS = {
    "planificado": N_("Planificado"),
    "en_curso": N_("En curso"),
    "rematado": N_("Rematado"),
}
_CATALOGOS = {
    "sistema_cultivo": "sistema_cultivo",
    "sistema_explotacion": "sistema_explotacion",
    "destino": "destino_cultivo",
    "certificacion_ecoloxica": "certificacion_ecoloxica",
    "procedencia_material": "procedencia_material_vexetal",
    "causa_baixa": "causa_baixa",
    "tipo_cobertura_solo": "tipo_cobertura_solo",
}
_POR_DEFECTO = {"sistema_cultivo": "1", "destino": "1", "certificacion_ecoloxica": "1"}


def _enteiro(texto: Any) -> int | None:
    valor = parsear_decimal(texto)
    return int(valor) if valor is not None else None


def seccion_cultivos(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        cultivos = listar_cultivos(session, actor, horta_id)
        parcelas = listar_parcelas(session, actor, horta_id)
        colleitas = listar_colleitas(session, actor, horta_id)
        estados = estados_cultivos(session, actor, horta_id)

    nome_parcela = {p.id: p.nome for p in parcelas}
    colleitado: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for c in colleitas:
        colleitado[c.cultivo_id][c.unidade] += c.cantidade
    filas = [
        {
            "id": c.id,
            "cultivo": nome_cultivo(c),
            "parcela": nome_parcela.get(c.parcela_id, ""),
            "superficie": formatar_superficie(c.superficie_ha),
            "inicio": f"{c.data_inicio:%d/%m/%Y}" if c.data_inicio else "",
            "estado": _(_ESTADOS[estados[c.id]]),
            "colleitado": " + ".join(
                f"{cantidade:g} {unidade}" for unidade, cantidade in colleitado[c.id].items()
            ),
            "faltan": "" if c.cultivo_siex_codigo and c.superficie_ha else _("Faltan datos"),
        }
        for c in cultivos
    ]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("cultivo", _("Cultivo")), ("parcela", _("Parcela")), ("superficie", _("Superficie")),
            ("inicio", _("Inicio")), ("estado", _("Estado")), ("colleitado", _("Colleitado")),
            ("faltan", ""))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="{_("Aínda non hai cultivos")}" {TEXTOS_TABOA}'
    )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "cultivo", ["parcela", "inicio"], accions_tarxeta)

    if not pode_editar:
        return

    abrir = dialogo_cultivo(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify(_("Selecciona un cultivo na táboa"), type="warning")
            return
        abrir(next(x for x in cultivos if x.id == taboa.selected[0]["id"]))

    def eliminar() -> None:
        if not taboa.selected:
            ui.notify(_("Selecciona un cultivo na táboa"), type="warning")
            return
        cultivo_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                cultivo = session.get(Cultivo, cultivo_id)
                if actor is None or cultivo is None:
                    return
                ok = executar_accion(session, lambda: eliminar_cultivo(session, actor, cultivo))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(_("Eliminar este cultivo?"), confirmar)

    accions_tarxeta += [(_("Editar"), "edit", editar),
                        (_("Eliminar"), "delete", eliminar)]

    with ui.row():
        ui.button(_("Novo cultivo"), icon="add", on_click=lambda: abrir(None))
        with ui.row().classes("so-ordenador"):
            ui.button(_("Editar"), icon="edit", on_click=editar).props("outline")
            ui.button(_("Eliminar"), icon="delete", on_click=eliminar).props(
                "outline color=negative")


def dialogo_cultivo(horta_id: int) -> Callable[[Cultivo | None], None]:
    """Constrúe o diálogo de crear ou editar un cultivo (tamén a súa sementeira ou plantación)
    e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _x: None
        cultivos = listar_cultivos(session, actor, horta_id)
        parcelas = listar_parcelas(session, actor, horta_id)
        zonas = {p.id: {z.id: z.nome for z in listar_zonas(session, actor, p)}
                 for p in parcelas}
        opcions_cultivo = {c.codigo: nome for c, nome in buscar_cultivos(session, "", 2000)}
        opcions = {
            campo: {
                v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                for v in valores_vixentes(session, catalogo)
            }
            for campo, catalogo in _CATALOGOS.items()
        }
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
    nome_parcela = {p.id: p.nome for p in parcelas}

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label(_("Novo cultivo")).classes("text-h6")
        ui.label(_("Que e onde")).classes("text-subtitle2")
        parcela = ui.select(nome_parcela, label=_("Parcela")).classes("w-full")
        zona = ui.select({}, label=_("Zona da parcela (bancal, sector…)"), clearable=True).classes(
            "w-full")
        cultivo_oficial = ui.select(
            opcions_cultivo, label=_("Cultivo (lista oficial)"), with_input=True
        ).classes("w-full")
        variedade_oficial = ui.select({}, label=_("Variedade oficial"), with_input=True,
                                      clearable=True).classes("w-full")
        variedade_texto = ui.input(_("Variedade (se non está na lista)")).classes("w-full")
        superficie = CampoSuperficie(_("Superficie"))
        tipo_inicio = ui.radio(
            {"sementeira": _("Sementeira"), "plantacion": _("Plantación")},
            value="sementeira",
        ).props("inline")
        data_inicio = campo_data(_("Data de sementeira ou plantación"))
        quen = ui.select(persoas, label=_("Quen sementou ou plantou"), clearable=True).classes(
            "w-full")
        data_prevista = campo_data(_("Colleita prevista"))
        data_fin = campo_data(_("Data de fin (cando remata)"))

        ui.label(_("Como se cultiva")).classes("text-subtitle2 q-mt-md")
        sistema = ui.select(opcions["sistema_cultivo"], label=_("Sistema de cultivo"),
                            with_input=True).classes("w-full")
        secano = ui.select(opcions["sistema_explotacion"], label=_("Secano ou regadío"),
                           clearable=True).classes("w-full")
        destino = ui.select(opcions["destino"], label=_("Destino"), with_input=True).classes(
            "w-full")
        eco = ui.select(opcions["certificacion_ecoloxica"], label=_("Ecolóxico")).classes("w-full")
        data_conversion = campo_data(_("Inicio da conversión a ecolóxico"))
        integrada = ui.checkbox(_("Produción integrada"))
        cobertura = ui.select(opcions["tipo_cobertura_solo"],
                              label=_("Cobertura do chan (cultivos permanentes)"),
                              clearable=True).classes("w-full")

        with ui.expansion(_("Sementeira ou plantación (caderno)")).classes("w-full"):
            data_fin_sementeira = campo_data(_("Data de fin da sementeira/plantación"))
            horas_sementeira = ui.input(_("Horas de traballo")).classes("w-full")
            ui.label(_("Indica só un destes catro:")).classes("text-caption")
            cantidade_semente = ui.input(_("Semente usada (kg)")).classes("w-full")
            dose_sementeira = ui.input(_("Dose de sementeira (kg/ha)")).classes("w-full")
            densidade = ui.input(_("Plantas por hectárea")).classes("w-full")
            sementeira_directa = ui.checkbox(_("Sementeira directa"))
            material_tratado = ui.checkbox(_("A semente ou planta vén tratada"))
            with ui.column().classes("w-full gap-1").bind_visibility_from(
                    material_tratado, "value"):
                semente_produto = ui.input(
                    _("Produto do tratamento (nome comercial ou materia activa)")
                ).classes("w-full")
                semente_rexistro = ui.input(_("Nº de rexistro do produto")).classes("w-full")

        with ui.expansion(_("Orixe da semente ou planta")).classes("w-full"):
            procedencia = ui.select(opcions["procedencia_material"], label=_("Procedencia"),
                                    clearable=True).classes("w-full")
            # A compra (provedor, lote, data e pasaporte): apúntase en Produtos → Nova entrada
            compra_semente = ui.select(opcions_entradas(horta_id, tipo="semente"),
                                       label=_("De que compra (se se mercou)"), clearable=True
                                       ).classes("w-full")
        with ui.expansion(_("Árbores e viña")).classes("w-full"):
            num_arbores = ui.input(_("Número de árbores")).classes("w-full")
            marco = ui.input(_("Marco de plantación (p.ex. 4x4)")).classes("w-full")
            ano_plantacion = ui.input(_("Ano de plantación")).classes("w-full")
            castineiros = ui.input(_("Castiñeiros")).classes("w-full")
            abeleiras = ui.input(_("Abeleiras")).classes("w-full")
            nogueiras = ui.input(_("Nogueiras")).classes("w-full")
            amendoeiras = ui.input(_("Amendoeiras")).classes("w-full")
            outros_casca = ui.input(_("Outras árbores de froitos de casca")).classes("w-full")
        with ui.expansion(_("Cogomelos")).classes("w-full"):
            unidades = ui.input(_("Unidades produtivas (sacos, bandexas...)")).classes("w-full")
            ciclos = ui.input(_("Ciclos ao ano")).classes("w-full")
            duracion = ui.input(_("Duración de cada ciclo (días)")).classes("w-full")
        with ui.expansion(_("Plan de abonado")).classes("w-full"):
            anterior = ui.select(opcions_cultivo, label=_("Cultivo anterior"), with_input=True,
                                 clearable=True).classes("w-full")
            obxectivo = ui.input(_("Colleita esperada (kg/ha)")).classes("w-full")
            ui.label(_("Necesidades do cultivo (kg/ha)")).classes("text-caption")
            with ui.row().classes("w-full no-wrap"):
                necesidade_n = ui.input("N").classes("col")
                necesidade_p = ui.input("P₂O₅").classes("col")
                necesidade_k = ui.input("K₂O").classes("col")
            plan_data = campo_data(_("Data do plan"))
            ferramenta = ui.checkbox(_("Calculouse cunha ferramenta de nutrientes"))
            auga_n = ui.input(_("Nitróxeno nítrico da auga de rega (mg/l)")).classes("w-full")
            auga_p = ui.input(_("P₂O₅ da auga de rega (mg/l)")).classes("w-full")
        with ui.expansion(_("Baixa e notas")).classes("w-full"):
            causa_baixa = ui.select(opcions["causa_baixa"], label=_("Causa da baixa"),
                                    clearable=True).classes("w-full")
            notas = ui.textarea(_("Notas")).classes("w-full")

        def cargar_variedades() -> None:
            variedade_oficial.value = None
            if cultivo_oficial.value is None:
                variedade_oficial.set_options({})
                return
            with get_session() as session:
                variedade_oficial.set_options(
                    {v.id: nome for v, nome in listar_variedades(session, cultivo_oficial.value)}
                )

        cultivo_oficial.on_value_change(cargar_variedades)

        def propor_da_parcela() -> None:
            if editando["id"] is not None or parcela.value is None:
                return
            p = next(x for x in parcelas if x.id == parcela.value)
            if p.secano_regadio is not None:
                secano.value = "R" if p.secano_regadio.value == "regadio" else "S"
            if superficie.ha is None and p.superficie:
                ocupada = sum(c.superficie_ha or 0 for c in cultivos
                              if c.parcela_id == p.id and estado_cultivo(c) != "rematado")
                if p.superficie - ocupada > 0:
                    superficie.establecer(round(p.superficie - ocupada, 4))

        parcela.on_value_change(propor_da_parcela)

        def zonas_da_parcela() -> None:
            opcions = zonas.get(parcela.value or 0, {})
            zona.set_options(opcions, value=zona.value if zona.value in opcions else None)
            zona.set_visibility(bool(opcions))

        parcela.on_value_change(zonas_da_parcela)

        def gardar() -> None:
            if not parcela.value or cultivo_oficial.value is None:
                ui.notify(_("Parcela e cultivo son obrigatorios"), type="negative")
                return
            inicio = parsear_data(data_inicio.value)
            if inicio is not None and inicio <= date.today() and quen.value is None:
                ui.notify(_("Indica quen sementou ou plantou"), type="negative")
                return
            datos: dict[str, Any] = dict(
                especie=opcions_cultivo.get(cultivo_oficial.value, ""),
                cultivo_siex_codigo=cultivo_oficial.value,
                variedade_siex_id=variedade_oficial.value,
                variedade=variedade_texto.value or None,
                superficie_ha=superficie.ha,
                tipo_inicio=tipo_inicio.value,
                data_inicio=inicio,
                sementeira_persoa_id=quen.value,
                sementeira_horas=parsear_decimal(horas_sementeira.value),
                data_colleita_prevista=parsear_data(data_prevista.value),
                data_fin=parsear_data(data_fin.value),
                sistema_cultivo=sistema.value,
                sistema_explotacion=secano.value,
                destino=destino.value,
                certificacion_ecoloxica=eco.value,
                data_inicio_conversion=parsear_data(data_conversion.value),
                producion_integrada=integrada.value,
                procedencia_material=procedencia.value,
                entrada_semente_id=compra_semente.value,
                zona_id=zona.value,
                num_arbores=_enteiro(num_arbores.value),
                marco_plantacion=marco.value or None,
                ano_plantacion=_enteiro(ano_plantacion.value),
                unidades_produtivas=_enteiro(unidades.value),
                ciclos_ano=_enteiro(ciclos.value),
                duracion_ciclo_dias=_enteiro(duracion.value),
                cultivo_anterior_codigo=anterior.value,
                obxectivo_colleita_kg_ha=parsear_decimal(obxectivo.value),
                plan_necesidade_n=parsear_decimal(necesidade_n.value),
                plan_necesidade_p2o5=parsear_decimal(necesidade_p.value),
                plan_necesidade_k2o=parsear_decimal(necesidade_k.value),
                plan_data=parsear_data(plan_data.value),
                plan_ferramenta_sostibilidade=ferramenta.value,
                plan_auga_n_nitrico=parsear_decimal(auga_n.value),
                plan_auga_p2o5=parsear_decimal(auga_p.value),
                causa_baixa=causa_baixa.value,
                actividade_agraria="1",
                notas=notas.value or None,
                tipo_cobertura_solo=cobertura.value,
                data_fin_sementeira=parsear_data(data_fin_sementeira.value),
                cantidade_semente_kg=parsear_decimal(cantidade_semente.value),
                dose_sementeira_kg_ha=parsear_decimal(dose_sementeira.value),
                densidade_plantas_ha=parsear_decimal(densidade.value),
                sementeira_directa=sementeira_directa.value,
                material_tratado=material_tratado.value,
                semente_tratamento_produto=(semente_produto.value or None)
                if material_tratado.value else None,
                semente_tratamento_num_rexistro=(semente_rexistro.value or None)
                if material_tratado.value else None,
                num_castineiros=_enteiro(castineiros.value),
                num_abeleiras=_enteiro(abeleiras.value),
                num_nogueiras=_enteiro(nogueiras.value),
                num_amendoeiras=_enteiro(amendoeiras.value),
                num_outros_froitos_casca=_enteiro(outros_casca.value),
            )
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                gardado: list[Cultivo] = []

                def accion() -> None:
                    if editando["id"] is None:
                        especie = datos.pop("especie")
                        gardado.append(crear_cultivo(session, actor, parcela.value, especie,
                                                     **datos))
                    else:
                        cultivo = session.get(Cultivo, editando["id"])
                        if cultivo is not None:
                            gardado.append(actualizar_cultivo(session, actor, cultivo, **datos))

                ok = executar_accion(session, accion)
                # Rotación (paso 12): avisa, nunca bloquea
                aviso = (aviso_rotacion(list(session.query(Cultivo).filter_by(
                    parcela_id=gardado[0].parcela_id)), gardado[0]) if ok and gardado else None)
            if ok:
                if aviso:
                    ui.notify(aviso, type="warning", timeout=4000)
                    ui.timer(3, ui.navigate.reload, once=True)
                else:
                    recargar_apuntado("sementeira", data_inicio.value)

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    campos_texto = (variedade_texto, data_inicio, data_prevista, data_fin, data_conversion,
                    num_arbores, marco,
                    ano_plantacion, unidades, ciclos, duracion, obxectivo, notas,
                    necesidade_n, necesidade_p, necesidade_k, plan_data, auga_n, auga_p,
                    semente_produto, semente_rexistro,
                    data_fin_sementeira, cantidade_semente, dose_sementeira, densidade,
                    castineiros, abeleiras, nogueiras, amendoeiras, outros_casca,
                    horas_sementeira)
    campos_select = (variedade_oficial, secano, procedencia, anterior, causa_baixa, cobertura)
    casillas = (sementeira_directa, material_tratado, ferramenta)

    def _texto(valor: Any) -> str:
        return "" if valor is None else str(valor)

    def abrir(c: Cultivo | None) -> None:
        if c is None:
            editando["id"] = None
            titulo.text = _("Novo cultivo")
            parcela.value = cultivo_oficial.value = zona.value = None
            cultivo_oficial.set_enabled(True)
            for campo in campos_texto:
                campo.value = ""
            for selector in campos_select:
                selector.value = None
            compra_semente.value = None
            superficie.establecer(None)
            tipo_inicio.value = "sementeira"
            quen.value = proposta_quen(horta_id)
            sistema.value = _POR_DEFECTO["sistema_cultivo"]
            destino.value = _POR_DEFECTO["destino"]
            eco.value = _POR_DEFECTO["certificacion_ecoloxica"]
            integrada.value = False
            for casilla in casillas:
                casilla.value = False
            dialogo.open()
            return
        editando["id"] = c.id
        titulo.text = _("Editar cultivo")
        parcela.value = c.parcela_id
        zonas_da_parcela()
        zona.value = c.zona_id
        cultivo_oficial.value = c.cultivo_siex_codigo
        # Cun cultivo oficial e traballos apuntados xa non se pode cambiar a outro
        with get_session() as session:
            con_rexistros = ten_rexistros(session, c.id)
        cultivo_oficial.set_enabled(not (con_rexistros and c.cultivo_siex_codigo is not None))
        variedade_oficial.value = c.variedade_siex_id
        variedade_texto.value = "" if c.variedade_siex_id else _texto(c.variedade)
        superficie.establecer(c.superficie_ha)
        tipo_inicio.value = c.tipo_inicio or "sementeira"
        data_inicio.value = _texto(c.data_inicio)
        quen.value = c.sementeira_persoa_id if c.sementeira_persoa_id in persoas else None
        horas_sementeira.value = "" if c.sementeira_horas is None else f"{c.sementeira_horas:g}"
        data_prevista.value = _texto(c.data_colleita_prevista)
        data_fin.value = _texto(c.data_fin)
        sistema.value = c.sistema_cultivo or _POR_DEFECTO["sistema_cultivo"]
        secano.value = c.sistema_explotacion
        destino.value = c.destino or _POR_DEFECTO["destino"]
        eco.value = c.certificacion_ecoloxica or _POR_DEFECTO["certificacion_ecoloxica"]
        data_conversion.value = _texto(c.data_inicio_conversion)
        integrada.value = bool(c.producion_integrada)
        procedencia.value = c.procedencia_material
        compra_semente.value = (c.entrada_semente_id if c.entrada_semente_id
                                in compra_semente.options else None)
        num_arbores.value = _texto(c.num_arbores)
        marco.value = _texto(c.marco_plantacion)
        ano_plantacion.value = _texto(c.ano_plantacion)
        unidades.value = _texto(c.unidades_produtivas)
        ciclos.value = _texto(c.ciclos_ano)
        duracion.value = _texto(c.duracion_ciclo_dias)
        anterior.value = c.cultivo_anterior_codigo
        obxectivo.value = _texto(c.obxectivo_colleita_kg_ha)
        necesidade_n.value = _texto(c.plan_necesidade_n)
        necesidade_p.value = _texto(c.plan_necesidade_p2o5)
        necesidade_k.value = _texto(c.plan_necesidade_k2o)
        plan_data.value = _texto(c.plan_data)
        ferramenta.value = bool(c.plan_ferramenta_sostibilidade)
        auga_n.value = _texto(c.plan_auga_n_nitrico)
        auga_p.value = _texto(c.plan_auga_p2o5)
        causa_baixa.value = c.causa_baixa
        notas.value = _texto(c.notas)
        cobertura.value = c.tipo_cobertura_solo
        data_fin_sementeira.value = _texto(c.data_fin_sementeira)
        cantidade_semente.value = _texto(c.cantidade_semente_kg)
        dose_sementeira.value = _texto(c.dose_sementeira_kg_ha)
        densidade.value = _texto(c.densidade_plantas_ha)
        sementeira_directa.value = bool(c.sementeira_directa)
        material_tratado.value = bool(c.material_tratado)
        semente_produto.value = _texto(c.semente_tratamento_produto)
        semente_rexistro.value = _texto(c.semente_tratamento_num_rexistro)
        castineiros.value = _texto(c.num_castineiros)
        abeleiras.value = _texto(c.num_abeleiras)
        nogueiras.value = _texto(c.num_nogueiras)
        amendoeiras.value = _texto(c.num_amendoeiras)
        outros_casca.value = _texto(c.num_outros_froitos_casca)
        dialogo.open()

    return abrir

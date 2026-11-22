# Tarefa 086b — Produtos (3/3): a páxina Produtos e o Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 086a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Explotación → Produtos: cada produto co que queda, «Nova entrada (compra)» e o historial; no Diario e en «Apuntar traballo», a entrada de produto. Probado no navegador (escritorio e móbil) o 2026-10-29. Deseño: `docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md` (paso 7 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/pages/produtos.py` (**ficheiro novo**)
- `src/horta/ui/pages/diario.py`
- `src/horta/ui/layout.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/pages/produtos.py`

Contido completo:
```python
"""Sección Produtos: os insumos da explotación (sementes, abonos, fitosanitarios, medicamentos,
pensos, enerxía) co que entrou, o que se usou e o que queda; e as entradas (compras)
(docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.produto import EntradaProduto
from horta.models.tarefa import Tarefa
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import listar_persoas, listar_quen
from horta.services.produtos import (
    TIPOS_PRODUTO,
    UNIDADES_ENTRADA,
    UNIDADES_PRODUTO,
    DatosEntrada,
    actualizar_entrada,
    crear_entrada,
    crear_produto,
    dar_de_baixa_entrada,
    existencias,
    listar_entradas,
    listar_produtos,
)
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_produtos(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        produtos = listar_produtos(session, actor, horta_id)
        contas = {p.id: existencias(session, p) for p in produtos}
        entradas = listar_entradas(session, actor, horta_id)
        nomes = {p.id: p.nome for p in listar_persoas(session, actor, horta_id,
                                                       so_activas=False)}
    nome_produto = {p.id: p.nome for p in produtos}

    def queda(produto_id: int, unidade: str) -> str:
        conta = contas[produto_id]
        texto = f"{conta.queda:g} {unidade}"
        # Se hai usos ou compras sen cantidade, o número non é seguro
        return f"{texto} (?)" if conta.sen_contar or conta.entradas_sen_cantidade else texto

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("produto", "Produto"), ("queda", "Queda"), ("tipo", "Que é"),
            ("entrou", "Entrou"), ("usado", "Usado"))],
        rows=[{"id": p.id, "produto": p.nome, "queda": queda(p.id, p.unidade),
               "tipo": TIPOS_PRODUTO[p.tipo], "entrou": f"{contas[p.id].entrou:g} {p.unidade}",
               "usado": f"{contas[p.id].usado:g} {p.unidade}"} for p in produtos],
        row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        'flat bordered no-data-label="Aínda non hai produtos: apunta a primeira compra" '
        f'{TEXTOS_TABOA}')
    if any(c.sen_contar or c.entradas_sen_cantidade for c in contas.values()):
        ui.label("(?) hai compras ou usos sen cantidade: o que queda non é seguro.").classes(
            "text-caption texto-suave")
    abrir = dialogo_entrada(horta_id) if pode_editar else None
    if pode_editar and abrir is not None:
        abrir_produto = _dialogo_produto(horta_id)

        def nova_entrada() -> None:
            abrir(None, None, taboa.selected[0]["id"] if taboa.selected else None)

        with ui.row():
            ui.button("Nova entrada (compra)", icon="shopping_cart", on_click=nova_entrada)
            ui.button("Novo produto", icon="add", on_click=abrir_produto).props("outline")

    ui.label("Entradas").classes("text-h6 q-mt-md")
    taboa_entradas = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("produto", "Produto"), ("canto", "Canto"),
            ("provedor", "Provedor"), ("albaran", "Albará"), ("prezo", "Prezo"))],
        rows=[{"id": e.id, "data": f"{e.data:%d/%m/%Y}",
               "produto": nome_produto.get(e.produto_id, ""),
               "canto": f"{e.cantidade:g} {e.unidade}" if e.cantidade else "",
               "provedor": nomes.get(e.provedor_id or 0, ""), "albaran": e.albaran_factura or "",
               "prezo": f"{e.importe:.2f} €" if e.importe is not None else ""}
              for e in entradas],
        row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai entradas" {TEXTOS_TABOA}')
    if not pode_editar or abrir is None:
        return

    def editar() -> None:
        if not taboa_entradas.selected:
            ui.notify("Escolle primeiro unha entrada na táboa", type="warning")
            return
        with get_session() as session:
            entrada = session.get(EntradaProduto, taboa_entradas.selected[0]["id"])
        if entrada is not None:
            abrir(entrada)

    def dar_de_baixa() -> None:
        if not taboa_entradas.selected:
            ui.notify("Escolle primeiro unha entrada na táboa", type="warning")
            return
        entrada_id = taboa_entradas.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                entrada = session.get(EntradaProduto, entrada_id)
                if actor_actual is None or entrada is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_entrada(
                    session, actor_actual, entrada))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta entrada? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def _dialogo_produto(horta_id: int) -> Callable[[], None]:
    with ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
        ui.label("Novo produto").classes("text-h6")
        tipo = ui.select(TIPOS_PRODUTO, label="Que é", value="outro").classes("w-full")
        nome = ui.input("Nome").classes("w-full")
        unidade = ui.select(list(UNIDADES_PRODUTO), label="Cóntase en", value="kg").classes(
            "w-full")
        rexistro = ui.input("Nº de rexistro (fitosanitario ou medicamento)").classes("w-full")
        ui.label("Os abonos créanse dende o abonado («Novo abono»), coa súa composición."
                 ).classes("text-caption texto-suave")

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                ok = executar_accion(session, lambda: crear_produto(
                    session, actor, horta_id, tipo.value, nome.value or "", unidade.value,
                    num_rexistro=rexistro.value or None))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        dialogo.open()

    return abrir


def dialogo_entrada(horta_id: int) -> Callable[..., None]:
    """O diálogo de apuntar ou editar unha entrada (compra) e a función que o abre:
    abrir(entrada, tarefa=None, produto_id=None)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        produtos = listar_produtos(session, actor, horta_id)
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
    opcions = {p.id: f"{p.nome} ({TIPOS_PRODUTO[p.tipo].lower()})" for p in produtos}
    unidades = {p.id: p.unidade for p in produtos}
    tipos = {p.id: p.tipo for p in produtos}
    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Entrada de produto").classes("text-h6")
        if not produtos:
            ui.label("Primeiro crea o produto en Explotación → Produtos.").classes(
                "text-warning text-caption")
        produto = ui.select(opcions, label="Produto", with_input=True).classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        with ui.row().classes("w-full no-wrap"):
            cantidade = ui.input("Canto").classes("col")
            unidade = ui.select(list(UNIDADES_ENTRADA), label="Unidade", value="kg").classes(
                "col")
        provedor = CampoPersoa(horta_id, "provedor", "Provedor")
        with ui.row().classes("w-full no-wrap"):
            albaran = ui.input("Albará ou factura").classes("col")
            importe = ui.input("Prezo total (€)").classes("col")
        persoa = ui.select(persoas, label="Quen o recibiu").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            lote = ui.input("Lote do provedor").classes("w-full")
            caducidade = campo_data("Caducidade", "")
            pasaporte = ui.input("Pasaporte fitosanitario (sementes e plantas)").classes(
                "w-full")
            horas = ui.input("Horas de traballo").classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def cambiar_produto() -> None:
            if produto.value in unidades and editando["id"] is None:
                unidade.value = unidades[produto.value]
            pasaporte.set_visibility(tipos.get(produto.value) == "semente")

        produto.on_value_change(cambiar_produto)

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if produto.value is None or dia is None:
                        raise OperacionNonPermitidaError("Escolle o produto e a data")
                    datos = DatosEntrada(
                        produto_id=produto.value, data=dia, persoa_id=persoa.value,
                        provedor_id=provedor.value, cantidade=parsear_decimal(cantidade.value),
                        unidade=unidade.value, lote_provedor=lote.value or None,
                        albaran_factura=albaran.value or None,
                        importe=parsear_decimal(importe.value),
                        data_caducidade=parsear_data(caducidade.value),
                        pasaporte_fitosanitario=pasaporte.value or None,
                        horas=parsear_decimal(horas.value), notas=notas.value or None)
                    existente = (session.get(EntradaProduto, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        nova = crear_entrada(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], nova)
                    else:
                        actualizar_entrada(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(entrada: EntradaProduto | None, tarefa: Tarefa | None = None,
              produto_id: int | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = entrada.id if entrada else None
        titulo.text = "Editar entrada de produto" if entrada else "Entrada de produto"
        produto.value = entrada.produto_id if entrada else produto_id
        data.value = (entrada.data if entrada else date.today()).isoformat()
        cantidade.value = f"{entrada.cantidade:g}" if entrada and entrada.cantidade else ""
        cambiar_produto()
        if entrada and entrada.unidade:
            unidade.value = entrada.unidade
        provedor.value = entrada.provedor_id if entrada else None
        albaran.value = (entrada.albaran_factura or "") if entrada else ""
        importe.value = (f"{entrada.importe:g}" if entrada and entrada.importe is not None
                         else "")
        lote.value = (entrada.lote_provedor or "") if entrada else ""
        caducidade.value = (entrada.data_caducidade.isoformat()
                            if entrada and entrada.data_caducidade else "")
        pasaporte.value = (entrada.pasaporte_fitosanitario or "") if entrada else ""
        persoa.value = (entrada.persoa_id if entrada.persoa_id in persoas else None) \
            if entrada else proposta_quen(horta_id, tarefa)
        horas.value = f"{entrada.horas:g}" if entrada and entrada.horas else ""
        notas.value = (entrada.notas or "") if entrada else ""
        dialogo.open()

    return abrir
```

### Paso 2 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.models.producion_animal import ProducionAnimal
```

Despois:
```python
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto
```

### Paso 3 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets",
    "movemento_animal": "swap_horiz", "producion_animal": "egg", "pastoreo": "landscape",
    "lote_saida": "sell", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "producion_animal": "producion", "pastoreo": "pastoreo",
    "lote_saida": "lotes", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
    "pastoreo": Pastoreo, "lote_saida": LoteSaida,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
    "producion_animal": dialogo_producion, "pastoreo": dialogo_pastoreo,
    "lote_saida": dialogo_saida,
```

Despois:
```python
from horta.ui.pages.produtos import dialogo_entrada
from horta.ui.pages.regas import dialogo_rega
from horta.ui.pages.tratamentos import dialogo_tratamento_fito
from horta.ui.pages.tratamentos_instalacion import dialogo_tratamento_instalacion
from horta.ui.sesion import pechar_sesion, usuario_actual

ICONAS = {
    "tratamento": "sanitizer", "abonado": "compost", "rega": "water_drop", "labor": "grass",
    "colleita": "inventory_2", "sementeira": "spa", "analise": "science",
    "tratamento_instalacion": "warehouse", "coidado_animal": "pets",
    "movemento_animal": "swap_horiz", "producion_animal": "egg", "pastoreo": "landscape",
    "lote_saida": "sell", "entrada_produto": "shopping_cart", "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "producion_animal": "producion", "pastoreo": "pastoreo",
    "lote_saida": "lotes", "entrada_produto": "produtos", "tarefa": "tarefas",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
    "pastoreo": Pastoreo, "lote_saida": LoteSaida, "entrada_produto": EntradaProduto,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
    "producion_animal": dialogo_producion, "pastoreo": dialogo_pastoreo,
    "lote_saida": dialogo_saida, "entrada_produto": dialogo_entrada,
```

### Paso 4 — `src/horta/ui/layout.py`

Antes:
```python
    Seccion("maquinaria", "Maquinaria", "agriculture", "Explotación"),
```

Despois:
```python
    Seccion("maquinaria", "Maquinaria", "agriculture", "Explotación"),
    Seccion("produtos", "Produtos", "shopping_basket", "Explotación"),
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.pages.producions_animais import seccion_producion
```

Despois:
```python
from horta.ui.pages.producions_animais import seccion_producion
from horta.ui.pages.produtos import seccion_produtos
```

### Paso 6 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        seccion_lotes(horta_id, pode_editar)
```

Despois:
```python
        seccion_lotes(horta_id, pode_editar)
    elif seccion == "produtos":
        seccion_produtos(horta_id, pode_editar)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produtos (3/3): a páxina Produtos e o Diario: feito.

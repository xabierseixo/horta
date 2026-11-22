# Tarefa 087a — Outro traballo (2/2): o formulario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 087. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Apuntar traballo» → Outro traballo: que se fixo, datas, parcela ou animais, quen e horas; editalo e dalo de baixa dende o Diario. Probado no navegador (escritorio e móbil) o 2026-10-29. Deseño: `docs/superpowers/specs/2026-10-29-outro-traballo-design.md` (paso 8 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/pages/outros_traballos.py` (**ficheiro novo**)
- `src/horta/ui/pages/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/pages/outros_traballos.py`

Contido completo:
```python
"""Formulario de «Outro traballo» (mantemento, limpeza, arranxos…). Non ten táboa propia: a
súa lista é o Diario (docs/superpowers/specs/2026-10-29-outro-traballo-design.md)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.outro_traballo import OutroTraballo
from horta.models.tarefa import Tarefa
from horta.services.animais import listar_animais
from horta.services.diario import nome_grupo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.outros_traballos import (
    DatosOutroTraballo,
    actualizar_outro_traballo,
    crear_outro_traballo,
    dar_de_baixa_outro_traballo,
)
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual


def dialogo_outro_traballo(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar outro traballo e devolve a función que o abre:
    abrir(traballo, tarefa=None)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        parcelas = {p.id: p.nome for p in listar_parcelas(session, actor, horta_id)}
        animais = {a.id: nome_grupo(a.especie, a.raza)
                   for a in listar_animais(session, actor, horta_id)}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Apuntar outro traballo").classes("text-h6")
        descricion = ui.input("Que se fixo (p.ex. arranxar o peche)").classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        data_fin = campo_data("Data de fin (se durou máis dun día)")
        parcela = ui.select(parcelas, label="Parcela (se foi nunha)", clearable=True).classes(
            "w-full")
        animal = ui.select(animais, label="Animais (se foi con eles)", clearable=True).classes(
            "w-full")
        ui.label("Sen parcela nin animais, é un traballo da explotación enteira.").classes(
            "text-caption texto-suave")
        with ui.row().classes("w-full no-wrap"):
            persoa = ui.select(persoas, label="Quen o fixo").classes("col")
            horas = ui.input("Horas").classes("col")
        with ui.expansion("Máis datos").classes("w-full"):
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data_inicio.value)
                    if dia is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    datos = DatosOutroTraballo(
                        horta_id=horta_id, data_inicio=dia,
                        data_fin=parsear_data(data_fin.value),
                        descricion=descricion.value or "", parcela_id=parcela.value,
                        animal_id=animal.value, persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value), maquina_id=maquina.value,
                        notas=notas.value or None)
                    existente = (session.get(OutroTraballo, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_outro_traballo(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_outro_traballo(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        def dar_de_baixa() -> None:
            def confirmar() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    traballo = session.get(OutroTraballo, editando["id"])
                    if traballo is None:
                        return
                    ok = executar_accion(session, lambda: dar_de_baixa_outro_traballo(
                        session, actor_actual, traballo))
                if ok:
                    ui.navigate.reload()

            confirmar_eliminacion(
                "Dar de baixa este traballo? Non se borra: consérvase no histórico.", confirmar)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            baixa = ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props(
                "flat")
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(traballo: OutroTraballo | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = traballo.id if traballo else None
        titulo.text = "Editar outro traballo" if traballo else "Apuntar outro traballo"
        descricion.value = (traballo.descricion if traballo
                            else tarefa.descricion if tarefa else "")
        data_inicio.value = (traballo.data_inicio if traballo else date.today()).isoformat()
        data_fin.value = (traballo.data_fin.isoformat()
                          if traballo and traballo.data_fin != traballo.data_inicio else "")
        if traballo:
            parcela.value = traballo.parcela_id if traballo.parcela_id in parcelas else None
            animal.value = traballo.animal_id if traballo.animal_id in animais else None
        else:
            parcela.value = tarefa.parcela_id if tarefa and tarefa.parcela_id in parcelas \
                else None
            animal.value = tarefa.animal_id if tarefa and tarefa.animal_id in animais else None
        persoa.value = ((traballo.persoa_id if traballo.persoa_id in persoas else None)
                        if traballo else proposta_quen(horta_id, tarefa))
        horas.value = f"{traballo.horas:g}" if traballo and traballo.horas else ""
        maquina.value = (traballo.maquina_id if traballo and traballo.maquina_id in maquinas
                         else None)
        notas.value = (traballo.notas or "") if traballo else ""
        baixa.set_visibility(traballo is not None)
        dialogo.open()

    return abrir
```

### Paso 2 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.models.movemento_animal import MovementoAnimal
```

Despois:
```python
from horta.models.movemento_animal import MovementoAnimal
from horta.models.outro_traballo import OutroTraballo
```

### Paso 3 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.ui.pages.movementos_animais import dialogo_movemento
```

Despois:
```python
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.pages.outros_traballos import dialogo_outro_traballo
```

### Paso 4 — `src/horta/ui/pages/diario.py`

Antes:
```python
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

Despois:
```python
    "lote_saida": "sell", "entrada_produto": "shopping_cart", "outro_traballo": "build",
    "tarefa": "task_alt",
}
# A táboa de cada tipo, cos seus datos propios (p.ex. «non colleitar antes do»)
SECCION_DO_TIPO = {
    "tratamento": "tratamentos", "abonado": "fertilizacion", "rega": "rega", "labor": "labores",
    "colleita": "colleitas", "sementeira": "cultivos", "analise": "analises",
    "tratamento_instalacion": "tratamentos", "coidado_animal": "coidados",
    "movemento_animal": "movementos", "producion_animal": "producion", "pastoreo": "pastoreo",
    "lote_saida": "lotes", "entrada_produto": "produtos", "tarefa": "tarefas",
    # Sen táboa propia: a súa lista é o propio Diario
    "outro_traballo": "diario",
}
_MODELOS: dict[str, type[Base]] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
    "pastoreo": Pastoreo, "lote_saida": LoteSaida, "entrada_produto": EntradaProduto,
    "outro_traballo": OutroTraballo,
}
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
    "tratamento": dialogo_tratamento_fito, "abonado": dialogo_abonado, "rega": dialogo_rega,
    "labor": dialogo_labor, "colleita": dialogo_colleita, "sementeira": dialogo_cultivo,
    "analise": dialogo_analise, "tratamento_instalacion": dialogo_tratamento_instalacion,
    "coidado_animal": dialogo_coidado, "movemento_animal": dialogo_movemento,
    "producion_animal": dialogo_producion, "pastoreo": dialogo_pastoreo,
    "lote_saida": dialogo_saida, "entrada_produto": dialogo_entrada,
    "outro_traballo": dialogo_outro_traballo,
```

### Paso 5 — `src/horta/ui/pages/diario.py`

Antes:
```python
        if tipo.value:
```

Despois:
```python
        if tipo.value and SECCION_DO_TIPO[tipo.value] != "diario":
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Outro traballo (2/2): o formulario: feito.

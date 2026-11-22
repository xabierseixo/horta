# Tarefa 084b — Varias leiras (3/5): formularios

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 084a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Nos formularios de labor, rega e abonado escóllense unha ou varias leiras; a superficie só cunha. Deseño: `docs/superpowers/specs/2026-10-28-varias-leiras-design.md` (paso 5 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/superficie.py`
- `src/horta/ui/leiras.py` (**ficheiro novo**)
- `src/horta/ui/pages/labores.py`
- `src/horta/ui/pages/regas.py`
- `src/horta/ui/pages/abonados.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/superficie.py`

Antes:
```python
        with ui.row().classes("w-full no-wrap items-end gap-2"):
            self.numero = ui.number(etiqueta, min=0).classes("col-grow")
            self.unidade = ui.select(
                list(UNIDADES_SUPERFICIE), value=unidade, label="Unidade",
                on_change=self._cambiar_unidade,
            ).classes("w-24")

    @property
    def ha(self) -> float | None:
        return a_hectareas(self.numero.value, self.unidade.value)
```

Despois:
```python
        with ui.row().classes("w-full no-wrap items-end gap-2") as self.fila:
            self.numero = ui.number(etiqueta, min=0).classes("col-grow")
            self.unidade = ui.select(
                list(UNIDADES_SUPERFICIE), value=unidade, label="Unidade",
                on_change=self._cambiar_unidade,
            ).classes("w-24")

    @property
    def ha(self) -> float | None:
        return a_hectareas(self.numero.value, self.unidade.value)

    def set_visibility(self, visible: bool) -> None:
        self.fila.set_visibility(visible)
```

### Paso 2 — crear o ficheiro `src/horta/ui/leiras.py`

Contido completo:
```python
"""Escoller unha ou varias leiras nos formularios de labor, rega e abonado
(docs/superpowers/specs/2026-10-28-varias-leiras-design.md)."""

from __future__ import annotations

from horta.services.leiras import LeiraTraballo


def leiras_escollidas(cultivos: list[int] | None, superficie_ha: float | None
                      ) -> list[LeiraTraballo]:
    """As leiras do formulario. A superficie só se pode indicar cunha leira; con varias, cada
    unha leva a do seu cultivo."""
    cultivos = list(cultivos or [])
    return [LeiraTraballo(c, superficie_ha if len(cultivos) == 1 else None) for c in cultivos]
```

### Paso 3 — `src/horta/ui/pages/labores.py`

Antes:
```python
from horta.ui.facer_tarefa import rematar_tarefa
```

Despois:
```python
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.leiras import leiras_escollidas
```

### Paso 4 — `src/horta/ui/pages/labores.py`

Antes:
```python
        "cultivo": cultivos.get(lab.cultivo_id, ""),
```

Despois:
```python
        "cultivo": ", ".join(cultivos.get(le.cultivo_id, "") for le in lab.leiras),
```

### Paso 5 — `src/horta/ui/pages/labores.py`

Antes:
```python
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        tipo = ui.select(tipos, label="Labor").classes("w-full")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        restos_desbroce = ui.checkbox("Os restos do desbroce quedaron no chan")
        restos_poda = ui.checkbox("Os restos da poda quedaron no chan")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas_traballo = ui.input("Horas de traballo").classes("w-full")
            superficie = CampoSuperficie("Superficie (baleiro = a do cultivo)")
```

Despois:
```python
        cultivo = ui.select(cultivos, label="Leiras (unha ou varias)", with_input=True,
                            multiple=True, value=[]).classes("w-full").props("use-chips")
        data_inicio = campo_data("Data", date.today().isoformat())
        tipo = ui.select(tipos, label="Labor").classes("w-full")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        restos_desbroce = ui.checkbox("Os restos do desbroce quedaron no chan")
        restos_poda = ui.checkbox("Os restos da poda quedaron no chan")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas_traballo = ui.input("Horas de traballo").classes("w-full")
            superficie = CampoSuperficie("Superficie (baleiro = a do cultivo; só cunha leira)")
```

### Paso 6 — `src/horta/ui/pages/labores.py`

Antes:
```python
        def propor_labor() -> None:
            if cultivo.value is not None and tipo.value is None:
                with get_session() as session:
                    tipo.value = ultimo_labor(session, cultivo.value)

        cultivo.on_value_change(propor_labor)

        def gardar() -> None:
            if cultivo.value is None or tipo.value is None:
                ui.notify("Escolle o cultivo e o labor", type="warning")
```

Despois:
```python
        def cambiar_leiras() -> None:
            superficie.set_visibility(len(cultivo.value or []) == 1)
            if cultivo.value and tipo.value is None:
                with get_session() as session:
                    tipo.value = ultimo_labor(session, cultivo.value[0])

        cultivo.on_value_change(cambiar_leiras)

        def gardar() -> None:
            if not cultivo.value or tipo.value is None:
                ui.notify("Escolle as leiras e o labor", type="warning")
```

### Paso 7 — `src/horta/ui/pages/labores.py`

Antes:
```python
                        cultivo_id=cultivo.value, data_inicio=inicio, tipo_labor=tipo.value,
                        data_fin=parsear_data(data_fin.value), superficie_ha=superficie.ha,
```

Despois:
```python
                        leiras=leiras_escollidas(cultivo.value, superficie.ha),
                        data_inicio=inicio, tipo_labor=tipo.value,
                        data_fin=parsear_data(data_fin.value),
```

### Paso 8 — `src/horta/ui/pages/labores.py`

Antes:
```python
        cultivo.value = lab.cultivo_id if lab else (tarefa.cultivo_id if tarefa else None)
        data_inicio.value = (lab.data_inicio if lab else date.today()).isoformat()
        data_fin.value = (lab.data_fin.isoformat()
                          if lab and lab.data_fin != lab.data_inicio else "")
        superficie.establecer(lab.superficie_ha if lab else None)
```

Despois:
```python
        cultivo.value = ([le.cultivo_id for le in lab.leiras] if lab else
                         [tarefa.cultivo_id] if tarefa and tarefa.cultivo_id else [])
        data_inicio.value = (lab.data_inicio if lab else date.today()).isoformat()
        data_fin.value = (lab.data_fin.isoformat()
                          if lab and lab.data_fin != lab.data_inicio else "")
        superficie.establecer(lab.leiras[0].superficie_ha if lab and len(lab.leiras) == 1
                              else None)
```

### Paso 9 — `src/horta/ui/pages/labores.py`

Antes:
```python
        mostrar_restos()
```

Despois:
```python
        mostrar_restos()
        cambiar_leiras()
```

### Paso 10 — `src/horta/ui/pages/regas.py`

Antes:
```python
"""Sección Rega: cada rega dun cultivo (CUE bloque 10). Baixa lóxica."""
```

Despois:
```python
"""Sección Rega: cada rega, nunha ou varias leiras (CUE bloque 10). Baixa lóxica."""
```

### Paso 11 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.ui.facer_tarefa import rematar_tarefa
```

Despois:
```python
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.leiras import leiras_escollidas
```

### Paso 12 — `src/horta/ui/pages/regas.py`

Antes:
```python
        "cultivo": cultivos.get(r.cultivo_id, ""),
```

Despois:
```python
        "cultivo": ", ".join(cultivos.get(le.cultivo_id, "") for le in r.leiras),
```

### Paso 13 — `src/horta/ui/pages/regas.py`

Antes:
```python
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        superficie = CampoSuperficie("Superficie regada (baleiro = a do cultivo)")
```

Despois:
```python
        cultivo = ui.select(cultivos, label="Leiras (unha ou varias)", with_input=True,
                            multiple=True, value=[]).classes("w-full").props("use-chips")
        data_inicio = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        superficie = CampoSuperficie("Superficie regada (baleiro = a do cultivo; só cunha leira)")
```

### Paso 14 — `src/horta/ui/pages/regas.py`

Antes:
```python
        def propor_sistema() -> None:
            if cultivo.value is not None and sistema.value is None:
                with get_session() as session:
                    sistema.value = ultimo_sistema_rega(session, cultivo.value)

        cultivo.on_value_change(propor_sistema)

        def gardar() -> None:
            if cultivo.value is None:
                ui.notify("Escolle o cultivo", type="warning")
```

Despois:
```python
        def cambiar_leiras() -> None:
            superficie.set_visibility(len(cultivo.value or []) == 1)
            if cultivo.value and sistema.value is None:
                with get_session() as session:
                    sistema.value = ultimo_sistema_rega(session, cultivo.value[0])

        cultivo.on_value_change(cambiar_leiras)

        def gardar() -> None:
            if not cultivo.value:
                ui.notify("Escolle as leiras", type="warning")
```

### Paso 15 — `src/horta/ui/pages/regas.py`

Antes:
```python
                        cultivo_id=cultivo.value, data_inicio=inicio,
                        data_fin=parsear_data(data_fin.value), superficie_ha=superficie.ha,
```

Despois:
```python
                        leiras=leiras_escollidas(cultivo.value, superficie.ha),
                        data_inicio=inicio, data_fin=parsear_data(data_fin.value),
```

### Paso 16 — `src/horta/ui/pages/regas.py`

Antes:
```python
        cultivo.value = r.cultivo_id if r else (tarefa.cultivo_id if tarefa else None)
        data_inicio.value = (r.data_inicio if r else date.today()).isoformat()
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        persoa.value = (r.persoa_id if r.persoa_id in persoas else None) if r else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{r.horas:g}" if r and r.horas else ""
        maquina.value = r.maquina_id if r and r.maquina_id in maquinas else None
        superficie.establecer(r.superficie_ha if r else None)
```

Despois:
```python
        cultivo.value = ([le.cultivo_id for le in r.leiras] if r else
                         [tarefa.cultivo_id] if tarefa and tarefa.cultivo_id else [])
        data_inicio.value = (r.data_inicio if r else date.today()).isoformat()
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        persoa.value = (r.persoa_id if r.persoa_id in persoas else None) if r else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{r.horas:g}" if r and r.horas else ""
        maquina.value = r.maquina_id if r and r.maquina_id in maquinas else None
        superficie.establecer(r.leiras[0].superficie_ha if r and len(r.leiras) == 1 else None)
        cambiar_leiras()
```

### Paso 17 — `src/horta/ui/pages/abonados.py`

Antes:
```python
"""Sección Fertilización: cada abonado dun cultivo (CUE bloque 9). Baixa lóxica."""
```

Despois:
```python
"""Sección Fertilización: cada abonado, nunha ou varias leiras (CUE bloque 9). Baixa lóxica."""
```

### Paso 18 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from horta.ui.facer_tarefa import rematar_tarefa
```

Despois:
```python
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.leiras import leiras_escollidas
```

### Paso 19 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        abonados_cultivos = {a.cultivo_id for a in abonados}
        balances = {c.id: balance_do_cultivo(session, actor, horta_id, c) for c in lista_cultivos
                    if c.id in abonados_cultivos or c.plan_necesidade_n}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
        unidades_cat = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
        filas = [{
            "id": a.id,
            "data": f"{a.data_inicio:%d/%m/%Y}",
            "cultivo": cultivos.get(a.cultivo_id, ""),
```

Despois:
```python
        abonados_cultivos = {le.cultivo_id for a in abonados for le in a.leiras}
        balances = {c.id: balance_do_cultivo(session, actor, horta_id, c) for c in lista_cultivos
                    if c.id in abonados_cultivos or c.plan_necesidade_n}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
        unidades_cat = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
        filas = [{
            "id": a.id,
            "data": f"{a.data_inicio:%d/%m/%Y}",
            "cultivo": ", ".join(cultivos.get(le.cultivo_id, "") for le in a.leiras),
```

### Paso 20 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        aplicador = ui.select(persoas, label="Quen o botou (persoa ou empresa de servizos)",
                              clearable=True).classes("w-full")
        superficie = CampoSuperficie("Superficie abonada (baleiro = a do cultivo)")
```

Despois:
```python
        cultivo = ui.select(cultivos, label="Leiras (unha ou varias)", with_input=True,
                            multiple=True, value=[]).classes("w-full").props("use-chips")
        data_inicio = campo_data("Data", date.today().isoformat())
        aplicador = ui.select(persoas, label="Quen o botou (persoa ou empresa de servizos)",
                              clearable=True).classes("w-full")
        superficie = CampoSuperficie("Superficie abonada (baleiro = a do cultivo; só cunha leira)")
        cultivo.on_value_change(
            lambda: superficie.set_visibility(len(cultivo.value or []) == 1))
```

### Paso 21 — `src/horta/ui/pages/abonados.py`

Antes:
```python
            if cultivo.value is None:
                ui.notify("Escolle o cultivo", type="warning")
```

Despois:
```python
            if not cultivo.value:
                ui.notify("Escolle as leiras", type="warning")
```

### Paso 22 — `src/horta/ui/pages/abonados.py`

Antes:
```python
                        cultivo_id=cultivo.value, data_inicio=inicio,
                        data_fin=parsear_data(data_fin.value), superficie_ha=superficie.ha,
```

Despois:
```python
                        leiras=leiras_escollidas(cultivo.value, superficie.ha),
                        data_inicio=inicio, data_fin=parsear_data(data_fin.value),
```

### Paso 23 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        cultivo.value = a.cultivo_id if a else (tarefa.cultivo_id if tarefa else None)
        data_inicio.value = (a.data_inicio if a else date.today()).isoformat()
        data_fin.value = a.data_fin.isoformat() if a and a.data_fin != a.data_inicio else ""
        superficie.establecer(a.superficie_ha if a else None)
```

Despois:
```python
        cultivo.value = ([le.cultivo_id for le in a.leiras] if a else
                         [tarefa.cultivo_id] if tarefa and tarefa.cultivo_id else [])
        data_inicio.value = (a.data_inicio if a else date.today()).isoformat()
        data_fin.value = a.data_fin.isoformat() if a and a.data_fin != a.data_inicio else ""
        superficie.establecer(a.leiras[0].superficie_ha if a and len(a.leiras) == 1 else None)
        superficie.set_visibility(len(cultivo.value) == 1)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Varias leiras (3/5): formularios: feito.

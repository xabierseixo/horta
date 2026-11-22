# Tarefa 076l — Tarefas por facer (13/16): facela desde o Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 076d a 076k. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

No Diario, tocar unha tarefa por facer ofrece «Facela agora» (o formulario do seu tipo xa enchido, ou quen a fixo se non ten tipo) ou editala. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/diario.py`

Antes:
```python
from functools import partial
from typing import Any
```

Despois:
```python
from functools import partial
```

### Paso 2 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.services.diario import TIPOS, Traballo, listar_traballos
from horta.services.persoas import listar_persoas
from horta.ui.campos import campo_data
from horta.ui.dialogo_tarefa import dialogo_nova_tarefa
```

Despois:
```python
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.services.diario import TIPOS, Traballo, listar_traballos
from horta.services.persoas import listar_persoas
from horta.ui.campos import campo_data
from horta.ui.dialogo_tarefa import dialogo_nova_tarefa
from horta.ui.facer_tarefa import dialogo_tarefa_feita
```

### Paso 3 — `src/horta/ui/pages/diario.py`

Antes:
```python
_CONSTRUTORES: dict[str, Callable[[int], Callable[[Any], None]]] = {
```

Despois:
```python
_CONSTRUTORES: dict[str, Callable[[int], Callable[..., None]]] = {
```

### Paso 4 — `src/horta/ui/pages/diario.py`

Antes:
```python
        self._abrir: dict[str, Callable[[Any], None]] = {}

    def _abridor(self, tipo: str) -> Callable[[Any], None]:
        if tipo not in self._abrir:
            with self._contedor:
                if tipo == "tarefa":
                    abrir_tarefa = dialogo_nova_tarefa(self.horta_id)
                    self._abrir[tipo] = lambda _: abrir_tarefa()
                else:
                    self._abrir[tipo] = _CONSTRUTORES[tipo](self.horta_id)
        return self._abrir[tipo]

    def novo(self, tipo: str) -> None:
        self._abridor(tipo)(None)

    def editar(self, traballo: Traballo) -> None:
        if traballo.tipo == "tarefa":
            ui.navigate.to(url_seccion(self.horta_id, "tarefas"))
```

Despois:
```python
        self._abrir: dict[str, Callable[..., None]] = {}

    def _abridor(self, tipo: str) -> Callable[..., None]:
        if tipo not in self._abrir:
            with self._contedor:
                if tipo == "tarefa":
                    abrir_tarefa = dialogo_nova_tarefa(self.horta_id)
                    self._abrir[tipo] = lambda _: abrir_tarefa()
                elif tipo == "tarefa_feita":
                    self._abrir[tipo] = dialogo_tarefa_feita(self.horta_id)
                else:
                    self._abrir[tipo] = _CONSTRUTORES[tipo](self.horta_id)
        return self._abrir[tipo]

    def novo(self, tipo: str) -> None:
        self._abridor(tipo)(None)

    def facer(self, tarefa: Tarefa) -> None:
        """Facer unha tarefa: o formulario do seu tipo xa enchido ou, sen tipo, quen a fixo."""
        if tarefa.tipo:
            self._abridor(tarefa.tipo)(None, tarefa)
        else:
            self._abridor("tarefa_feita")(tarefa)

    def _escoller(self, tarefa: Tarefa) -> None:
        with self._contedor, ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
            ui.label(tarefa.descricion).classes("text-h6")

            def facela() -> None:
                dialogo.close()
                self.facer(tarefa)

            with ui.row():
                ui.button("Facela agora", icon="check", on_click=facela)
                ui.button("Editar a tarefa", icon="edit", on_click=lambda: ui.navigate.to(
                    url_seccion(self.horta_id, "tarefas"))).props("flat")
        dialogo.open()

    def editar(self, traballo: Traballo) -> None:
        if traballo.tipo == "tarefa":
            with get_session() as session:
                tarefa = session.get(Tarefa, traballo.id)
            if tarefa is not None and not traballo.feito:
                self._escoller(tarefa)
            else:
                ui.navigate.to(url_seccion(self.horta_id, "tarefas"))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (13/16): facela desde o Diario: feito.

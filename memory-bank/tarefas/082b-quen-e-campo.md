# Tarefa 082b — Persoas (3/11): quen o fixo e escoller persoas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o fixo» ofrece o equipo e as empresas de servizos; peza común para escoller unha persoa ou crear unha nova dende un formulario. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/campo_persoa.py` (**ficheiro novo**)
- `src/horta/ui/facer_tarefa.py`
- `src/horta/ui/dialogo_tarefa.py`
- `src/horta/ui/pages/producions_animais.py`
- `src/horta/ui/pages/regas.py`
- `src/horta/ui/pages/colleitas.py`
- `src/horta/ui/pages/labores.py`
- `src/horta/ui/pages/tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/campo_persoa.py`

Contido completo:
```python
"""Escoller unha persoa ou entidade nun formulario de traballo (quen merca, o provedor, o
laboratorio, a outra explotación...). Se aínda non está, o botón «Nova» créaa alí mesmo co
nome e os datos que pide ese papel, e queda escollida
(docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md)."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import PAPEIS, TIPOS_PERSOA, crear_contacto, listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual

# Os datos que se piden ao crear a persoa dende un formulario, segundo o papel que fai alí
_DATOS_DO_PAPEL: dict[str | None, tuple[tuple[str, str], ...]] = {
    "explotacion": (("rega", "REGA da súa explotación (ES + 12 díxitos)"),
                    ("enderezo", "Enderezo")),
    "provedor": (("nif", "NIF"), ("rega", "REGA, se é unha granxa"),
                 ("nima", "NIMA, se é un xestor de residuos"), ("ropveg", "Nº ROPVEG")),
    "cliente": (("nif", "NIF"), ("enderezo", "Enderezo")),
    "laboratorio": (("nif", "NIF"),),
    "servizos": (("nif", "NIF"), ("regfer_numero", "Nº REGFER")),
    "veterinario": (("telefono", "Teléfono"),),
    None: (("nif", "NIF"),),
}
_ENTIDADE_POR_DEFECTO = ("laboratorio", "servizos")


class CampoPersoa:
    """Un selector de persoas da explotación (primeiro as que xa teñen o papel) e un botón
    para crear unha nova. `value` é o id da persoa escollida (ou None)."""

    def __init__(self, horta_id: int, papel: str | None, etiqueta: str) -> None:
        self.horta_id = horta_id
        self.papel = papel
        with ui.row().classes("w-full no-wrap items-center gap-1") as self.fila:
            self.select = ui.select({}, label=etiqueta, with_input=True,
                                    clearable=True).classes("col")
            ui.button(icon="person_add", on_click=self._abrir_nova).props(
                'flat round dense aria-label="Nova persoa ou entidade"').tooltip("Nova")
        self._cargar()
        self._dialogo_nova()

    def _cargar(self) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                return
            persoas = listar_persoas(session, actor, self.horta_id)
        co_papel = [p for p in persoas if self.papel is None or p.ten_papel(self.papel)]
        resto = [p for p in persoas if p not in co_papel]
        self.select.set_options({p.id: p.nome for p in [*co_papel, *resto]})

    def _dialogo_nova(self) -> None:
        with ui.dialog() as self.dialogo, ui.card().style("width: min(28rem, 94vw)"):
            titulo = PAPEIS.get(self.papel or "", "Persoa ou entidade")
            ui.label(f"Nova: {titulo.lower()}").classes("text-h6")
            self.tipo = ui.radio(TIPOS_PERSOA, value="persoa").props("inline")
            self.nome = ui.input("Nome ou razón social").classes("w-full")
            self.datos = {campo: ui.input(etiqueta).classes("w-full")
                          for campo, etiqueta in _DATOS_DO_PAPEL.get(self.papel,
                                                                     _DATOS_DO_PAPEL[None])}
            ui.label("O resto dos datos complétanse despois en Explotación → Persoas.").classes(
                "text-caption texto-suave")
            with ui.row():
                ui.button("Gardar", icon="check", on_click=self._gardar)
                ui.button("Cancelar", on_click=self.dialogo.close).props("flat")

    def _abrir_nova(self) -> None:
        self.tipo.value = "entidade" if self.papel in _ENTIDADE_POR_DEFECTO else "persoa"
        self.nome.value = ""
        for entrada in self.datos.values():
            entrada.value = ""
        self.dialogo.open()

    def _gardar(self) -> None:
        creada: list[int] = []
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return

            def accion() -> None:
                if not (self.nome.value or "").strip():
                    raise OperacionNonPermitidaError("Indica o nome")
                persoa = crear_contacto(
                    session, actor, self.horta_id, self.nome.value, self.papel,
                    tipo=self.tipo.value,
                    **{c: (e.value or None) for c, e in self.datos.items()})
                creada.append(persoa.id)

            ok = executar_accion(session, accion)
        if ok and creada:
            self._cargar()
            self.select.value = creada[0]
            self.dialogo.close()

    @property
    def value(self) -> int | None:
        return self.select.value

    @value.setter
    def value(self, persoa_id: int | None) -> None:
        self.select.value = persoa_id if persoa_id in self.select.options else None

    def set_visibility(self, visible: bool) -> None:
        self.fila.set_visibility(visible)

    def set_label(self, etiqueta: str) -> None:
        self.select.props(f'label="{etiqueta}"')
```

### Paso 2 — `src/horta/ui/facer_tarefa.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 3 — `src/horta/ui/facer_tarefa.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 4 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 5 — `src/horta/ui/dialogo_tarefa.py`

Antes:
```python
        p.id: p.nome for p in listar_persoas(session, actor, horta_id)}}
```

Despois:
```python
        p.id: p.nome for p in listar_quen(session, actor, horta_id)}}
```

### Paso 6 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_persoas, listar_quen
```

### Paso 7 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 8 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 9 — `src/horta/ui/pages/regas.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 10 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 11 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 12 — `src/horta/ui/pages/labores.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 13 — `src/horta/ui/pages/labores.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 14 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 15 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (3/11): quen o fixo e escoller persoas: feito.

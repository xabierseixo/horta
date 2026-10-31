"""Escoller unha persoa ou entidade nun formulario de traballo (quen merca, o provedor, o
laboratorio, a outra explotación...). Se aínda non está, o botón «Nova» créaa alí mesmo co
nome e os datos que pide ese papel, e queda escollida
."""

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
        with (ui.dialog().props("persistent") as self.dialogo,
              ui.card().style("width: min(28rem, 94vw)")):
            titulo = PAPEIS.get(self.papel or "", "Persoa ou entidade")
            ui.label(f"Nova: {titulo.lower()}").classes("text-h6")
            self.tipo = ui.radio(TIPOS_PERSOA, value="persoa").props("inline")
            self.nome = ui.input("Nome ou razón social").classes("w-full")
            self.datos = {campo: ui.input(etiqueta).classes("w-full")
                          for campo, etiqueta in _DATOS_DO_PAPEL.get(self.papel,
                                                                     _DATOS_DO_PAPEL[None])}
            ui.label("O resto dos datos complétanse despois en Equipo ou Contactos.").classes(
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

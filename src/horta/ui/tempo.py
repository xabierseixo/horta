"""O tempo na pantalla: escoller o
concello e a estación de MeteoGalicia, e ver o tempo dun día mentres se apunta un traballo.
As consultas a MeteoGalicia fanse sen bloquear a pantalla."""

from __future__ import annotations

from datetime import date

from nicegui import background_tasks, run, ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.tarefa import Tarefa
from horta.models.tempo import EstacionMeteo
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.lua import fase_lua
from horta.services.meteogalicia import (
    NIVEIS_AVISO,
    Aviso,
    DiaPredicion,
    Estacion,
    MeteoGalicia,
    SenTempo,
)
from horta.services.tempo import (
    LONXE_KM,
    TempoDoTraballo,
    avisos_tarefas,
    concellos,
    distancia_km,
    encher_tempo,
    estacion_do_lugar,
    horas_frio,
    tempo_do_traballo,
)
from horta.ui.numeros import parsear_data
from horta.ui.sesion import usuario_actual


def _estacions_meteogalicia() -> list[Estacion]:
    try:
        return MeteoGalicia().estacions()
    except SenTempo:
        return []


def _estacions_gardadas() -> list[Estacion]:
    with get_session() as session:
        return [Estacion(e.id, e.nome, e.concello, e.lat, e.lon, e.altitude)
                for e in session.query(EstacionMeteo)]


def _nome_concello(texto: str | None) -> str:
    """MeteoGalicia dá os concellos en maiúsculas: «SANTIAGO DE COMPOSTELA»."""
    palabras = (texto or "").title().split()
    return " ".join(p.lower() if i and p.lower() in ("de", "do", "da", "dos", "das") else p
                    for i, p in enumerate(palabras))


class CampoLugarTempo:
    """Concello (para a predición) e estación (para o tempo de cada día). Con coordenadas,
    as estacións ordénanse pola distancia e proponse a máis próxima."""

    def __init__(self, baleiro: str | None = None) -> None:
        # baleiro: na parcela, o texto de «o da explotación»
        self.baleiro = baleiro
        opcions = {**({"": baleiro} if baleiro else {}), **concellos()}
        self.concello = ui.select(opcions, label="Concello (para a predición)",
                                  with_input=True, clearable=True).classes("w-full")
        self.estacion = ui.select({}, label="Estación de MeteoGalicia", with_input=True,
                                  clearable=True).classes("w-full")
        self.nota = ui.label("").classes("text-caption texto-suave")
        self._estacions: dict[int, Estacion] = {}
        self._lat: float | None = None
        self._lon: float | None = None
        self.estacion.on_value_change(self._avisar)

    def cargar(self, concello_ine: str | None, estacion_id: int | None,
               lat: float | None, lon: float | None) -> None:
        self._lat, self._lon = lat, lon
        self.concello.value = concello_ine or ("" if self.baleiro else None)
        self._pintar(_estacions_gardadas(), estacion_id)
        background_tasks.create(self._buscar(estacion_id))

    def situar(self, lat: float | None, lon: float | None) -> None:
        """Ao cambiar as coordenadas: as estacións volven ordenarse pola distancia."""
        self._lat, self._lon = lat, lon
        self._pintar([], self.estacion.value or None)

    async def _buscar(self, estacion_id: int | None) -> None:
        estacions = await run.io_bound(_estacions_meteogalicia)
        if not estacions:
            self.nota.text = "Sen conexión con MeteoGalicia: só as estacións xa gardadas"
            return
        self._pintar(estacions, self.estacion.value or estacion_id, propor=True)

    def _km(self, estacion: Estacion) -> float | None:
        if self._lat is None or self._lon is None:
            return None
        return distancia_km(self._lat, self._lon, estacion.lat, estacion.lon)

    def _pintar(self, estacions: list[Estacion], escollida: int | None,
                propor: bool = False) -> None:
        self._estacions.update({e.id: e for e in estacions})
        lista = sorted(self._estacions.values(),
                       key=lambda e: (self._km(e) or 0, e.nome))

        def etiqueta(e: Estacion) -> str:
            km = self._km(e)
            partes = [f"{e.nome} ({_nome_concello(e.concello)})",
                      f"{km:.1f} km" if km is not None else "",
                      f"{e.altitude:.0f} m de altitude" if e.altitude is not None else ""]
            return " · ".join(p for p in partes if p)

        opcions: dict[int | str, str] = {**({"": self.baleiro} if self.baleiro else {}),
                                         **{e.id: etiqueta(e) for e in lista}}
        self.estacion.set_options(opcions)
        if escollida in self._estacions:
            self.estacion.value = escollida
        elif propor and lista and self._km(lista[0]) is not None and not self.baleiro:
            self.estacion.value = lista[0].id
        else:
            self.estacion.value = "" if self.baleiro else None
        self._avisar()

    def _avisar(self) -> None:
        estacion = self._estacions.get(self.estacion.value or 0)
        km = self._km(estacion) if estacion else None
        self.nota.text = (f"A estación está a {km:.0f} km: o tempo pode ser distinto"
                          if km is not None and km > LONXE_KM else "")

    @property
    def concello_ine(self) -> str | None:
        return self.concello.value or None

    @property
    def estacion_escollida(self) -> Estacion | None:
        return self._estacions.get(self.estacion.value or 0)


def _id_usuario() -> int | None:
    """O usuario da sesión, lido aquí: os fíos de fondo non ven a sesión do navegador."""
    with get_session() as session:
        actor = usuario_actual(session)
        return actor.id if actor else None


def _consultar(usuario_id: int, horta_id: int, tipo: str, cultivo_id: int | None, dia: date
               ) -> TempoDoTraballo | None:
    with get_session() as session:
        actor = session.get(Usuario, usuario_id)
        if actor is None:
            return None
        comprobar_rol_horta(session, horta_id, actor,
                            {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR})
        cultivo = session.get(Cultivo, cultivo_id) if cultivo_id is not None else None
        estacion_id = estacion_do_lugar(session, horta_id,
                                        cultivo.parcela_id if cultivo else None)
        return tempo_do_traballo(session, MeteoGalicia(), tipo, estacion_id, dia)


class EtiquetaTempo:
    """O tempo dese día na estación da leira, cos avisos. Non bloquea nada."""

    def __init__(self, horta_id: int, tipo: str) -> None:
        self.horta_id = horta_id
        self.tipo = tipo
        with ui.column().classes("w-full gap-0") as self.caixa:
            with ui.row().classes("items-center gap-1 no-wrap"):
                ui.icon("cloud").classes("texto-suave")
                self.texto = ui.label("").classes("text-caption")
            self.avisos = ui.column().classes("w-full gap-0")
        self.caixa.set_visibility(False)
        self._peticion = 0

    def actualizar(self, dia: str | None, cultivos: list[int] | None) -> None:
        """Co texto do campo da data e as leiras escollidas (vale a primeira)."""
        self.caixa.set_visibility(False)
        self._peticion += 1
        try:
            data = parsear_data(dia)
        except ValueError:
            data = None
        usuario_id = _id_usuario()
        if data is not None and usuario_id is not None:
            cultivo_id = cultivos[0] if cultivos else None
            background_tasks.create(self._buscar(self._peticion, usuario_id, data, cultivo_id))

    async def _buscar(self, peticion: int, usuario_id: int, dia: date, cultivo_id: int | None
                      ) -> None:
        tempo = await run.io_bound(_consultar, usuario_id, self.horta_id, self.tipo,
                                   cultivo_id, dia)
        # Se mentres tanto cambiou a data ou a leira, xa non vale
        if tempo is None or peticion != self._peticion:
            return
        self.texto.text = f"MeteoGalicia · {tempo.resumo}"
        self.avisos.clear()
        with self.avisos:
            for aviso in tempo.avisos:
                ui.label(aviso).classes("etiqueta-aviso")
            for texto in tempo.info:
                ui.label(texto).classes("text-caption texto-suave")
        self.caixa.set_visibility(True)


def _encher(usuario_id: int, horta_id: int) -> None:
    with get_session() as session:
        actor = session.get(Usuario, usuario_id)
        if actor is not None:
            encher_tempo(session, actor, horta_id, MeteoGalicia())


def encher_tempo_que_falta(horta_id: int) -> None:
    """Ao abrir o Diario: o tempo dos traballos apuntados sen conexión ou no día en curso."""
    usuario_id = _id_usuario()
    if usuario_id is not None:
        background_tasks.create(run.io_bound(_encher, usuario_id, horta_id))


_DIAS_SEMANA = ("Luns", "Martes", "Mércores", "Xoves", "Venres", "Sábado", "Domingo")


def _predicion(concello_ine: str) -> tuple[list[DiaPredicion], list[Aviso]]:
    try:
        return MeteoGalicia().predicion(concello_ine), MeteoGalicia().avisos(concello_ine)
    except SenTempo:
        return [], []


def _horas_frio(estacion_id: int | None) -> float | None:
    with get_session() as session:
        return horas_frio(session, MeteoGalicia(), estacion_id)


# Icona de cada estado do ceo (código de MeteoGalicia sen a centena)
_ICONAS_CEO = {1: "wb_sunny", 2: "filter_drama", 3: "filter_drama", 16: "filter_drama",
               4: "cloud", 5: "cloud", 25: "cloud", 6: "blur_on", 14: "blur_on",
               15: "blur_on", 24: "blur_on", 11: "umbrella", 13: "flash_on", 19: "flash_on",
               9: "ac_unit", 12: "ac_unit", 20: "ac_unit", 23: "ac_unit"}


def _tarxeta_dia(d: DiaPredicion) -> None:
    icona = _ICONAS_CEO.get((d.ceo_codigo or 0) % 100, "grain" if d.ceo_codigo else "help")
    with ui.column().classes("items-center gap-0 q-pa-sm").style(
            "min-width: 8.5rem; border: 1px solid rgba(0,0,0,.12); border-radius: 8px"):
        ui.label(f"{_DIAS_SEMANA[d.data.weekday()]} {d.data:%d/%m}").classes(
            "text-weight-bold")
        ui.icon(icona, size="2rem").classes("text-primary")
        ui.label(d.ceo or "").classes("text-caption text-center")
        if d.t_min is not None and d.t_max is not None:
            ui.label(f"{d.t_min}° / {d.t_max}°").classes("text-h6")
        for icona_dato, texto in (("water_drop", f"{d.choiva_pct} %"
                                   if d.choiva_pct is not None else ""),
                                  ("air", (d.vento or "").replace("Vento ", "")),
                                  ("light_mode", f"UV {d.uv}" if d.uv is not None else ""),
                                  ("dark_mode", fase_lua(d.data))):
            if texto:
                with ui.row().classes("items-center gap-1 no-wrap"):
                    ui.icon(icona_dato, size="1rem").classes("texto-suave")
                    ui.label(texto).classes("text-caption")


def predicion_inicio(concello_ine: str | None, estacion_id: int | None,
                     tarefas: list[Tarefa]) -> None:
    """Inicio: a predición do concello da explotación e os avisos das tarefas de tratamento.
    Non se garda: consúltase ao abrir, sen bloquear a pantalla."""
    if not concello_ine:
        ui.label("Para ver a predición do tempo, escolle o concello en Datos da explotación "
                 "→ O tempo.").classes("text-caption texto-suave q-my-sm")
        return
    with ui.column().classes("tarxeta w-full gap-1 q-my-md"):
        ui.label(f"O tempo en {concellos().get(concello_ine, concello_ine)}").classes(
            "text-subtitle1 text-weight-bold")
        corpo = ui.column().classes("w-full gap-0")
        with corpo:
            ui.label("Consultando MeteoGalicia…").classes("texto-suave")
        ui.label("Fonte: MeteoGalicia").classes("text-caption texto-suave")

    async def cargar() -> None:
        resultado = await run.io_bound(_predicion, concello_ine)
        dias, avisos_oficiais = resultado if resultado else ([], [])
        frio = await run.io_bound(_horas_frio, estacion_id)
        corpo.clear()
        with corpo:
            if not dias:
                ui.label("Sen conexión con MeteoGalicia agora mesmo.").classes("texto-suave")
                return
            if avisos_oficiais:
                ui.label("Avisos").classes("text-subtitle2 q-mt-sm")
            for aviso in avisos_oficiais:
                ui.label(f"Aviso {NIVEIS_AVISO[aviso.nivel]}: {aviso.tipo.lower()}, "
                         f"{aviso.inicio:%d/%m %H:%M}–{aviso.fin:%H:%M}").classes(
                    "etiqueta-aviso")
            ui.label("Próximos días").classes("text-subtitle2 q-mt-sm")
            with ui.row().classes("w-full gap-2"):
                for d in dias:
                    _tarxeta_dia(d)
            avisos_das_tarefas = avisos_tarefas(tarefas, dias)
            if avisos_das_tarefas:
                ui.label("As túas tarefas").classes("text-subtitle2 q-mt-sm")
            for aviso_tarefa in avisos_das_tarefas:
                ui.label(aviso_tarefa).classes("etiqueta-aviso")
            if frio is not None:
                ui.label("Froiteiros").classes("text-subtitle2 q-mt-sm")
                ui.label(f"Horas de frío desde o 1 de novembro: {frio:.0f} h (para os "
                         "froiteiros)").classes("text-caption")

    background_tasks.create(cargar())

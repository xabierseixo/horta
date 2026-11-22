# Tarefa 088a — O tempo (2/2): nas pantallas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 088. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Escoller o concello e a estación (ordenadas pola distancia, coa altitude) na explotación e en cada parcela; o tempo do día e os avisos nos formularios de rega, abonado e tratamento; ao abrir o Diario énchese o tempo que falta. Probado no navegador o 2026-10-29. Deseño: `docs/superpowers/specs/2026-10-29-tempo-design.md` (paso 9 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/ui/tempo.py` (**ficheiro novo**)
- `src/horta/ui/pages/parcelas.py`
- `src/horta/ui/pages/horta_detalle.py`
- `src/horta/ui/pages/regas.py`
- `src/horta/ui/pages/abonados.py`
- `src/horta/ui/dialogo_tratamento.py`
- `src/horta/ui/pages/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/tempo.py`

Contido completo:
```python
"""O tempo na pantalla (docs/superpowers/specs/2026-10-29-tempo-design.md): escoller o
concello e a estación de MeteoGalicia, e ver o tempo dun día mentres se apunta un traballo.
As consultas a MeteoGalicia fanse sen bloquear a pantalla."""

from __future__ import annotations

from datetime import date

from nicegui import background_tasks, run, ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.tempo import EstacionMeteo
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.meteogalicia import Estacion, MeteoGalicia, SenTempo
from horta.services.tempo import (
    LONXE_KM,
    TempoDoTraballo,
    concellos,
    distancia_km,
    encher_tempo,
    estacion_do_lugar,
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
```

### Paso 2 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA
```

Despois:
```python
from horta.services.tempo import gardar_lugar
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import CampoLugarTempo
```

### Paso 3 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
            notas = ui.textarea("Notas").classes("w-full")
```

Despois:
```python
            notas = ui.textarea("Notas").classes("w-full")
        with ui.expansion("O tempo").classes("w-full"):
            lugar = CampoLugarTempo("O da explotación")

        def situar() -> None:
            try:
                lugar.situar(parsear_decimal(lat.value), parsear_decimal(lon.value))
            except ValueError:
                lugar.situar(None, None)

        for coordenada in (lat, lon):
            coordenada.on_value_change(situar)
```

### Paso 4 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
                        crear_parcela(session, actor, horta_id, nome.value, **datos)
                    else:
                        parcela = session.get(Parcela, editando["id"])
                        if parcela is not None:
                            actualizar_parcela(session, actor, parcela, nome=nome.value, **datos)
```

Despois:
```python
                        parcela = crear_parcela(session, actor, horta_id, nome.value, **datos)
                    else:
                        existente = session.get(Parcela, editando["id"])
                        if existente is None:
                            return
                        parcela = actualizar_parcela(session, actor, existente, nome=nome.value,
                                                     **datos)
                    gardar_lugar(session, actor, parcela, lugar.concello_ine,
                                 lugar.estacion_escollida)
```

### Paso 5 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
        superficie.establecer(None)
```

Despois:
```python
        superficie.establecer(None)
        lugar.cargar(None, None, None, None)
```

### Paso 6 — `src/horta/ui/pages/parcelas.py`

Antes:
```python
        zona_ha.value = _texto(p.zona_especifica_ha)
```

Despois:
```python
        zona_ha.value = _texto(p.zona_especifica_ha)
        lugar.cargar(p.concello_ine, p.estacion_meteo_id, p.lat, p.lon)
```

### Paso 7 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    marcar_pendente,
)
```

Despois:
```python
    marcar_pendente,
)
from horta.services.tempo import gardar_lugar
```

### Paso 8 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.taboas import TEXTOS_TABOA
```

Despois:
```python
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import CampoLugarTempo
```

### Paso 9 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        horta_codigo_rega = horta.codigo_rega or ""
```

Despois:
```python
        horta_codigo_rega = horta.codigo_rega or ""
        lugar_tempo = (horta.concello_ine, horta.estacion_meteo_id, horta.lat, horta.lon)
```

### Paso 10 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                "text-caption texto-suave")
```

Despois:
```python
                "text-caption texto-suave")
            with ui.expansion("O tempo").classes("w-full"):
                lugar = CampoLugarTempo()
                ui.label("A estación vale para os traballos sen parcela e para as parcelas "
                         "sen estación propia.").classes("text-caption texto-suave")

            def abrir_config_horta() -> None:
                lugar.cargar(*lugar_tempo)
                dialog_config_horta.open()
```

### Paso 11 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                    gardado = executar_accion(
                        session,
                        lambda: actualizar_horta(
```

Despois:
```python
                    def accion() -> None:
                        actualizar_horta(
```

### Paso 12 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                        ),
                    )
```

Despois:
```python
                        )
                        gardar_lugar(session, actor_actual, horta_obxectivo,
                                     lugar.concello_ine, lugar.estacion_escollida)

                    gardado = executar_accion(session, accion)
```

### Paso 13 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                      on_click=dialog_config_horta.open).props("outline")
```

Despois:
```python
                      on_click=abrir_config_horta).props("outline")
```

### Paso 14 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.ui.taboas import TEXTOS_TABOA
```

Despois:
```python
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import EtiquetaTempo
```

### Paso 15 — `src/horta/ui/pages/regas.py`

Antes:
```python
        data_inicio = campo_data("Data", date.today().isoformat())
```

Despois:
```python
        data_inicio = campo_data("Data", date.today().isoformat())
        tempo = EtiquetaTempo(horta_id, "rega")
```

### Paso 16 — `src/horta/ui/pages/regas.py`

Antes:
```python

        cultivo.on_value_change(cambiar_leiras)
```

Despois:
```python
            tempo.actualizar(data_inicio.value, cultivo.value)

        cultivo.on_value_change(cambiar_leiras)
        data_inicio.on_value_change(lambda: tempo.actualizar(data_inicio.value, cultivo.value))
```

### Paso 17 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from horta.ui.taboas import TEXTOS_TABOA
```

Despois:
```python
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import EtiquetaTempo
```

### Paso 18 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        aplicador = ui.select(persoas, label="Quen o botou (persoa ou empresa de servizos)",
                              clearable=True).classes("w-full")
        superficie = CampoSuperficie("Superficie abonada (baleiro = a do cultivo; só cunha leira)")
        cultivo.on_value_change(
            lambda: superficie.set_visibility(len(cultivo.value or []) == 1))
```

Despois:
```python
        tempo = EtiquetaTempo(horta_id, "abonado")
        aplicador = ui.select(persoas, label="Quen o botou (persoa ou empresa de servizos)",
                              clearable=True).classes("w-full")
        superficie = CampoSuperficie("Superficie abonada (baleiro = a do cultivo; só cunha leira)")
        cultivo.on_value_change(
            lambda: superficie.set_visibility(len(cultivo.value or []) == 1))
        for campo in (cultivo, data_inicio):
            campo.on_value_change(lambda: tempo.actualizar(data_inicio.value, cultivo.value))
```

### Paso 19 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        calcular()
```

Despois:
```python
        calcular()
        tempo.actualizar(data_inicio.value, cultivo.value)
```

### Paso 20 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.tempo import EtiquetaTempo
```

### Paso 21 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
                ui.label("Cultivos tratados (mesmo cultivo e variedade)").classes("text-bold")

                @ui.refreshable
                def filas_cultivos() -> None:
                    for fila in estado["cultivos"]:
                        with ui.row().classes("w-full items-end gap-2"):
                            ui.select(op.cultivos, label="Cultivo e parcela",
                                      with_input=True).bind_value(fila, "cultivo_id").classes(
                                "grow")
```

Despois:
```python
                tempo = EtiquetaTempo(horta_id, "tratamento")

                def mirar_tempo() -> None:
                    cultivos = [f["cultivo_id"] for f in estado["cultivos"] if f["cultivo_id"]]
                    tempo.actualizar(data_inicio.value, cultivos)

                data_inicio.on_value_change(mirar_tempo)
                ui.label("Cultivos tratados (mesmo cultivo e variedade)").classes("text-bold")

                @ui.refreshable
                def filas_cultivos() -> None:
                    for fila in estado["cultivos"]:
                        with ui.row().classes("w-full items-end gap-2"):
                            ui.select(op.cultivos, label="Cultivo e parcela",
                                      with_input=True, on_change=mirar_tempo).bind_value(
                                fila, "cultivo_id").classes("grow")
```

### Paso 22 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
        pasos.set_value("1. Que e onde")
```

Despois:
```python
        pasos.set_value("1. Que e onde")
        mirar_tempo()
```

### Paso 23 — `src/horta/ui/pages/diario.py`

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.tempo import encher_tempo_que_falta
```

### Paso 24 — `src/horta/ui/pages/diario.py`

Antes:
```python
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}

```

Despois:
```python
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}

    encher_tempo_que_falta(horta_id)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O tempo (2/2): nas pantallas: feito.

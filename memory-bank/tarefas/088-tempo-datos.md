# Tarefa 088 — O tempo (1/2): estacións, tempo de cada día e avisos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 087a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Concello (INE) e estación de MeteoGalicia na explotación e nas parcelas; o tempo dun día nunha estación gárdase unha vez e cada traballo enlázase co do seu día; avisos do abonado (RD 1051/2022), do tratamento e da rega; enchido do que falta cunha consulta por estación. As probas len exemplos gardados (tests/datos/meteogalicia), nunca a rede. Deseño: `docs/superpowers/specs/2026-10-29-tempo-design.md` (paso 9 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/models/tempo.py` (**ficheiro novo**)
- `src/horta/models/traballo.py`
- `src/horta/models/horta.py`
- `src/horta/models/parcela.py`
- `src/horta/models/__init__.py`
- `alembic/versions/d7b9f1a3c5e8_tempo.py` (**ficheiro novo**)
- `src/horta/services/meteogalicia.py` (**ficheiro novo**)
- `src/horta/services/tempo.py` (**ficheiro novo**)
- `tests/services/test_tempo.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/tempo.py`

Contido completo:
```python
"""O tempo (docs/superpowers/specs/2026-10-29-tempo-design.md): as estacións de MeteoGalicia
que usa a explotación e o tempo dun día nunha estación, que se garda unha vez e comparten
todos os traballos dese día alí. Cada traballo enlázase só co tempo do seu día ao gardalo."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, UniqueConstraint, event
from sqlalchemy.orm import Mapped, Session, mapped_column

from horta.db import Base


class EstacionMeteo(Base):
    """Unha estación de MeteoGalicia, gardada ao escollela (o id é o de MeteoGalicia)."""

    __tablename__ = "estacion_meteo"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome: Mapped[str] = mapped_column(String(120))
    concello: Mapped[str | None] = mapped_column(String(120), default=None)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    altitude: Mapped[float | None] = mapped_column(Float, default=None)


class TempoDia(Base):
    """O tempo dun día rematado nunha estación. As medidas sen validar quedan baleiras."""

    __tablename__ = "tempo_dia"
    __table_args__ = (UniqueConstraint("estacion_id", "data"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    estacion_id: Mapped[int] = mapped_column(ForeignKey("estacion_meteo.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    t_min: Mapped[float | None] = mapped_column(Float, default=None)  # ºC
    t_max: Mapped[float | None] = mapped_column(Float, default=None)
    t_media: Mapped[float | None] = mapped_column(Float, default=None)
    choiva: Mapped[float | None] = mapped_column(Float, default=None)  # l/m²
    vento_medio: Mapped[float | None] = mapped_column(Float, default=None)  # m/s, a 10 m
    refacho: Mapped[float | None] = mapped_column(Float, default=None)  # m/s
    humidade: Mapped[float | None] = mapped_column(Float, default=None)  # %
    et0: Mapped[float | None] = mapped_column(Float, default=None)  # l/m²
    fonte: Mapped[str] = mapped_column(String(50), default="MeteoGalicia")
    consultado: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


def onde_e_cando(session: Session, traballo: object) -> tuple[int | None, int | None, date | None]:
    """A explotación, a estación e a data dun traballo: a estación da parcela da primeira
    leira ou, sen parcela (ou se a parcela non ten), a da explotación."""
    from horta.models.cultivo import Cultivo
    from horta.models.horta import Horta
    from horta.models.parcela import Parcela

    data = next((getattr(traballo, campo) for campo in ("data_inicio", "data", "data_mostraxe")
                 if getattr(traballo, campo, None) is not None), None)
    leiras = list(getattr(traballo, "leiras", None) or getattr(traballo, "cultivos", None) or [])
    cultivo_id = leiras[0].cultivo_id if leiras else getattr(traballo, "cultivo_id", None)
    parcela_id = getattr(traballo, "parcela_id", None)
    if cultivo_id is not None:
        cultivo = session.get(Cultivo, cultivo_id)
        parcela_id = cultivo.parcela_id if cultivo else parcela_id
    parcela = session.get(Parcela, parcela_id) if parcela_id is not None else None
    horta_id = getattr(traballo, "horta_id", None) or (parcela.horta_id if parcela else None)
    horta = session.get(Horta, horta_id) if horta_id is not None else None
    estacion_id = ((parcela.estacion_meteo_id if parcela else None)
                   or (horta.estacion_meteo_id if horta else None))
    return horta_id, estacion_id, data


def ligar_tempo(session: Session, traballo: object) -> None:
    """Enlaza o traballo co tempo xa gardado dese día na súa estación (sen consultar a rede:
    o que falte énchese despois, services.tempo.encher_tempo)."""
    _, estacion_id, data = onde_e_cando(session, traballo)
    tempo = (session.query(TempoDia).filter_by(estacion_id=estacion_id, data=data).first()
             if estacion_id is not None and data is not None else None)
    setattr(traballo, "tempo_id", tempo.id if tempo else None)


def _ao_gardar(session: Session, _contexto: object, _instancias: object) -> None:
    from horta.models.traballo import ParteComun

    with session.no_autoflush:
        for obxecto in (*session.new, *session.dirty):
            if isinstance(obxecto, ParteComun):
                ligar_tempo(session, obxecto)


event.listen(Session, "before_flush", _ao_gardar)
```

### Paso 2 — `src/horta/models/traballo.py`

Antes:
```python
from sqlalchemy.orm import Mapped, mapped_column
```

Despois:
```python
from sqlalchemy.orm import Mapped, mapped_column

# Rexistra o enlace de cada traballo co tempo do seu día (e a táboa tempo_dia)
import horta.models.tempo  # noqa: F401
```

### Paso 3 — `src/horta/models/traballo.py`

Antes:
```python
    )
```

Despois:
```python
    )
    # O tempo dese día na estación da primeira leira ou da explotación
    # (docs/superpowers/specs/2026-10-29-tempo-design.md)
    tempo_id: Mapped[int | None] = mapped_column(ForeignKey("tempo_dia.id"), default=None)
```

### Paso 4 — `src/horta/models/horta.py`

Antes:
```python
    provincia: Mapped[str | None] = mapped_column(String(50), default=None)
```

Despois:
```python
    provincia: Mapped[str | None] = mapped_column(String(50), default=None)
    # O tempo: concello (código INE) e estación de MeteoGalicia da explotación
    # (docs/superpowers/specs/2026-10-29-tempo-design.md)
    concello_ine: Mapped[str | None] = mapped_column(String(5), default=None)
    estacion_meteo_id: Mapped[int | None] = mapped_column(ForeignKey("estacion_meteo.id"),
                                                          default=None)
```

### Paso 5 — `src/horta/models/parcela.py`

Antes:
```python
    secano_regadio: Mapped[SecanoRegadio | None] = mapped_column(Enum(SecanoRegadio), default=None)
```

Despois:
```python
    secano_regadio: Mapped[SecanoRegadio | None] = mapped_column(Enum(SecanoRegadio), default=None)
    # O tempo: concello (código INE) e estación de MeteoGalicia; baleiros = os da explotación
    concello_ine: Mapped[str | None] = mapped_column(String(5), default=None)
    estacion_meteo_id: Mapped[int | None] = mapped_column(ForeignKey("estacion_meteo.id"),
                                                          default=None)
```

### Paso 6 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.tarefa import Tarefa
```

Despois:
```python
from horta.models.tarefa import Tarefa
from horta.models.tempo import EstacionMeteo, TempoDia
```

### Paso 7 — `src/horta/models/__init__.py`

Antes:
```python
    "OutroTraballo",
```

Despois:
```python
    "OutroTraballo",
    "EstacionMeteo",
    "TempoDia",
```

### Paso 8 — crear o ficheiro `alembic/versions/d7b9f1a3c5e8_tempo.py`

Contido completo:
```python
"""o tempo: estacións de MeteoGalicia, o tempo de cada día e tempo_id na parte común

Revision ID: d7b9f1a3c5e8
Revises: c6a8e0b2d4f7
Create Date: 2026-10-29 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7b9f1a3c5e8'
down_revision: Union[str, Sequence[str], None] = 'c6a8e0b2d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Os traballos coa parte común (horta.models.traballo.ParteComun)
_TRABALLOS = ("abonado", "analise", "coidado_animal", "colleita", "entrada_produto", "labor",
              "lote_saida", "movemento_animal", "outro_traballo", "pastoreo",
              "producion_animal", "rega", "tratamento_fito", "tratamento_instalacion")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "estacion_meteo",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("concello", sa.String(length=120), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tempo_dia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("estacion_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("t_min", sa.Float(), nullable=True),
        sa.Column("t_max", sa.Float(), nullable=True),
        sa.Column("t_media", sa.Float(), nullable=True),
        sa.Column("choiva", sa.Float(), nullable=True),
        sa.Column("vento_medio", sa.Float(), nullable=True),
        sa.Column("refacho", sa.Float(), nullable=True),
        sa.Column("humidade", sa.Float(), nullable=True),
        sa.Column("et0", sa.Float(), nullable=True),
        sa.Column("fonte", sa.String(length=50), nullable=False),
        sa.Column("consultado", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["estacion_id"], ["estacion_meteo.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("estacion_id", "data"),
    )
    op.create_index(op.f("ix_tempo_dia_estacion_id"), "tempo_dia", ["estacion_id"],
                    unique=False)
    for taboa in ("horta", "parcela"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("concello_ine", sa.String(length=5), nullable=True))
            batch.add_column(sa.Column("estacion_meteo_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_estacion_meteo_id", "estacion_meteo",
                                     ["estacion_meteo_id"], ["id"])
    for taboa in _TRABALLOS:
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("tempo_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_tempo_id", "tempo_dia", ["tempo_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in _TRABALLOS:
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_tempo_id", type_="foreignkey")
            batch.drop_column("tempo_id")
    for taboa in ("horta", "parcela"):
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_estacion_meteo_id", type_="foreignkey")
            batch.drop_column("estacion_meteo_id")
            batch.drop_column("concello_ine")
    op.drop_index(op.f("ix_tempo_dia_estacion_id"), table_name="tempo_dia")
    op.drop_table("tempo_dia")
    op.drop_table("estacion_meteo")
```

### Paso 9 — crear o ficheiro `src/horta/services/meteogalicia.py`

Contido completo:
```python
"""Servizos web de MeteoGalicia (JSON, sen clave): estacións, datos diarios e predición por
concello (docs/superpowers/specs/2026-10-29-tempo-design.md). Só se consulta ao abrir unha
pantalla ou ao apuntar un traballo: nada corre de fondo neste ordenador."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

URL = "https://servizos.meteogalicia.gal/mgrss"
FONTE = "MeteoGalicia"
_ESPERA_S = 10
# Medidas diarias que se gardan (código de MeteoGalicia → campo de TempoDia)
MEDIDAS = {
    "TA_MIN_1.5m": "t_min",
    "TA_MAX_1.5m": "t_max",
    "TA_AVG_1.5m": "t_media",
    "PP_SUM_1.5m": "choiva",
    "VV_AVG_10m": "vento_medio",
    "VV_MAX_10m": "refacho",
    "HR_AVG_1.5m": "humidade",
    "ET0_SUM_1.5m": "et0",
}
_VALIDADO = 1  # lnCodigoValidacion dun dato válido


class SenTempo(Exception):
    """MeteoGalicia non respondeu (sen conexión ou servizo caído)."""


@dataclass(frozen=True)
class Estacion:
    id: int
    nome: str
    concello: str | None
    lat: float
    lon: float
    altitude: float | None


@dataclass(frozen=True)
class Dia:
    """O tempo dun día nunha estación; None nas medidas que faltan ou sen validar."""

    estacion_id: int
    data: date
    medidas: dict[str, float | None]


@dataclass(frozen=True)
class DiaPredicion:
    data: date
    t_min: float | None
    t_max: float | None
    # Probabilidade de choiva (%): a maior da mañá, a tarde e a noite
    choiva_pct: int | None
    nivel_aviso: int | None


def ler_estacions(datos: dict[str, Any]) -> list[Estacion]:
    return [Estacion(e["idEstacion"], e["estacion"], e.get("concello"), e["lat"], e["lon"],
                     e.get("altitude"))
            for e in datos.get("listaEstacionsMeteo") or []]


def ler_dias(datos: dict[str, Any]) -> list[Dia]:
    dias: list[Dia] = []
    for dia in datos.get("listDatosDiarios") or []:
        data = datetime.fromisoformat(dia["data"]).date()
        for estacion in dia.get("listaEstacions") or []:
            medidas: dict[str, float | None] = dict.fromkeys(MEDIDAS.values())
            for medida in estacion.get("listaMedidas") or []:
                campo = MEDIDAS.get(medida.get("codigoParametro"))
                if campo and medida.get("lnCodigoValidacion") == _VALIDADO:
                    medidas[campo] = medida.get("valor")
            dias.append(Dia(estacion["idEstacion"], data, medidas))
    return dias


def ler_predicion(datos: dict[str, Any]) -> list[DiaPredicion]:
    dias: list[DiaPredicion] = []
    for dia in (datos.get("predConcello") or {}).get("listaPredDiaConcello") or []:
        choiva = [v for v in (dia.get("pchoiva") or {}).values() if v is not None and v >= 0]
        dias.append(DiaPredicion(
            datetime.fromisoformat(dia["dataPredicion"]).date(), dia.get("tMin"),
            dia.get("tMax"), max(choiva) if choiva else None, dia.get("nivelAviso")))
    return dias


class Fonte(Protocol):
    """De onde vén o tempo. Nas probas, un exemplo gardado; na app, MeteoGalicia."""

    def estacions(self) -> list[Estacion]: ...

    def dias(self, estacion_id: int, desde: date, ata: date) -> list[Dia]: ...

    def predicion(self, concello_ine: str) -> list[DiaPredicion]: ...


class MeteoGalicia:
    def _ler(self, ruta: str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(f"{URL}/{ruta}", timeout=_ESPERA_S) as resposta:
                datos: dict[str, Any] = json.load(resposta)
                return datos
        except (OSError, ValueError) as erro:
            raise SenTempo(str(erro)) from erro

    def estacions(self) -> list[Estacion]:
        return ler_estacions(self._ler("observacion/listaEstacionsMeteo.action"))

    def dias(self, estacion_id: int, desde: date, ata: date) -> list[Dia]:
        return ler_dias(self._ler(
            f"observacion/datosDiariosEstacionsMeteo.action?idEst={estacion_id}"
            f"&dataIni={desde:%d/%m/%Y}&dataFin={ata:%d/%m/%Y}"))

    def predicion(self, concello_ine: str) -> list[DiaPredicion]:
        return ler_predicion(self._ler(
            f"predicion/jsonPredConcellos.action?idConc={int(concello_ine)}"))
```

### Paso 10 — crear o ficheiro `src/horta/services/tempo.py`

Contido completo:
```python
"""O tempo de cada traballo e de cada lugar (docs/superpowers/specs/2026-10-29-tempo-design.md):
concellos (INE), estacións de MeteoGalicia, o tempo dun día e os avisos. Os avisos nunca
bloquean."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.db import Base
from horta.models.horta import Horta, RolHorta
from horta.models.parcela import Parcela
from horta.models.tempo import EstacionMeteo, TempoDia, ligar_tempo, onde_e_cando
from horta.models.traballo import ParteComun
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.meteogalicia import FONTE, Estacion, Fonte, SenTempo

# Guías de extensión agraria: para decidir no campo, a estación a menos de ~10 km
# (docs/estado-e-evolucion.md §8decies)
LONXE_KM = 10.0
# Boas prácticas: non tratar con vento de máis de 3 m/s (Junta de Andalucía, guía de
# contaminación difusa 2021)
VENTO_DERIVA_MS = 3.0
_CONCELLOS = Path(__file__).resolve().parents[1] / "data" / "concellos_galicia.csv"
# Días que se miran cara atrás ao encher o tempo que falta
DIAS_ATRAS = 365


@cache
def concellos() -> dict[str, str]:
    """Os concellos de Galicia (código INE → nome), da relación oficial do INE (2026)."""
    with _CONCELLOS.open(encoding="utf-8") as ficheiro:
        return {fila["codigo_ine"]: fila["nome"] for fila in csv.DictReader(ficheiro)}


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia sobre a Terra (fórmula do haverseno)."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df, dl = f2 - f1, math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def por_distancia(estacions: list[Estacion], lat: float, lon: float
                  ) -> list[tuple[Estacion, float]]:
    """As estacións da máis próxima á máis lonxana, coa distancia en km."""
    return sorted(((e, distancia_km(lat, lon, e.lat, e.lon)) for e in estacions),
                  key=lambda par: par[1])


def gardar_lugar(session: Session, actor: Usuario, sitio: Horta | Parcela,
                 concello_ine: str | None, estacion: Estacion | None) -> None:
    """O concello e a estación da explotación ou dunha parcela (baleiros na parcela: os da
    explotación). A estación gárdase para mostrala e medir distancias sen conexión."""
    horta_id = sitio.id if isinstance(sitio, Horta) else sitio.horta_id
    comprobar_rol_horta(session, horta_id, actor,
                        {RolHorta.ADMIN} if isinstance(sitio, Horta)
                        else {RolHorta.ADMIN, RolHorta.EDITOR})
    if concello_ine is not None and concello_ine not in concellos():
        raise OperacionNonPermitidaError("Ese concello non está na lista de Galicia")
    if estacion is not None:
        gardada = session.get(EstacionMeteo, estacion.id) or EstacionMeteo(id=estacion.id)
        gardada.nome, gardada.concello = estacion.nome, estacion.concello
        gardada.lat, gardada.lon, gardada.altitude = estacion.lat, estacion.lon, estacion.altitude
        session.add(gardada)
        # Sen relationship entre as táboas: a estación vai á BD antes de apuntala
        session.flush()
    sitio.concello_ine = concello_ine
    sitio.estacion_meteo_id = estacion.id if estacion else None
    session.commit()


def aviso_distancia(estacion: EstacionMeteo | None, lat: float | None, lon: float | None
                    ) -> str | None:
    if estacion is None or lat is None or lon is None:
        return None
    km = distancia_km(lat, lon, estacion.lat, estacion.lon)
    if km <= LONXE_KM:
        return None
    return (f"A estación está a {km:.0f} km: o tempo pode ser distinto. Escolle outra máis "
            "próxima se a hai")


def _gardar_dia(session: Session, estacion_id: int, data: date,
                medidas: dict[str, float | None]) -> TempoDia:
    tempo = TempoDia(estacion_id=estacion_id, data=data, fonte=FONTE, **medidas)
    session.add(tempo)
    session.flush()
    return tempo


def consultar_tempo(session: Session, fonte: Fonte, estacion_id: int, data: date,
                    hoxe: date | None = None) -> TempoDia | None:
    """O tempo dun día rematado nunha estación: o gardado ou, se non o hai, de MeteoGalicia
    (e gárdase). None se o día non rematou ou se non hai conexión."""
    if data >= (hoxe or date.today()):
        return None
    tempo = session.query(TempoDia).filter_by(estacion_id=estacion_id, data=data).first()
    if tempo is not None:
        return tempo
    if session.get(EstacionMeteo, estacion_id) is None:
        return None
    try:
        dias = fonte.dias(estacion_id, data, data)
    except SenTempo:
        return None
    dia = next((d for d in dias if d.estacion_id == estacion_id and d.data == data), None)
    if dia is None:
        return None
    tempo = _gardar_dia(session, estacion_id, data, dia.medidas)
    session.commit()
    return tempo


def _modelos_con_parte_comun() -> list[type[Any]]:
    return [m.class_ for m in Base.registry.mappers if issubclass(m.class_, ParteComun)]


def encher_tempo(session: Session, actor: Usuario, horta_id: int, fonte: Fonte,
                 hoxe: date | None = None) -> int:
    """Enche o tempo dos traballos que non o teñen (sen conexión ao apuntalos, ou do día en
    curso). Unha consulta por estación para todos os días que faltan. Devolve cantos."""
    comprobar_rol_horta(session, horta_id, actor,
                        {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR})
    hoxe = hoxe or date.today()
    desde = hoxe - timedelta(days=DIAS_ATRAS)
    sen_tempo: dict[int, list[tuple[object, date]]] = defaultdict(list)
    for modelo in _modelos_con_parte_comun():
        for traballo in session.query(modelo).filter_by(tempo_id=None, baixa=False):
            horta, estacion_id, data = onde_e_cando(session, traballo)
            if horta == horta_id and estacion_id is not None and data is not None \
                    and desde <= data < hoxe:
                sen_tempo[estacion_id].append((traballo, data))
    enchidos = 0
    for estacion_id, traballos in sen_tempo.items():
        datas = {data for _, data in traballos}
        gardados = {t.data for t in session.query(TempoDia).filter(
            TempoDia.estacion_id == estacion_id, TempoDia.data.in_(datas))}
        faltan = datas - gardados
        if faltan:
            try:
                dias = fonte.dias(estacion_id, min(faltan), max(faltan))
            except SenTempo:
                continue
            for dia in dias:
                if dia.estacion_id == estacion_id and dia.data in faltan:
                    _gardar_dia(session, estacion_id, dia.data, dia.medidas)
        for sen, _ in traballos:
            ligar_tempo(session, sen)
            enchidos += getattr(sen, "tempo_id") is not None
    session.commit()
    return enchidos


@dataclass(frozen=True)
class TempoDoTraballo:
    """O tempo para mostrar nun formulario: o resumo e os avisos."""

    resumo: str
    avisos: list[str]


def _n(valor: float | None, unidade: str) -> str:
    return "?" if valor is None else f"{valor:.1f}".rstrip("0").rstrip(".") + unidade


def resumo(tempo: TempoDia, estacion: str) -> str:
    return (f"{estacion}, {tempo.data:%d/%m}: {_n(tempo.t_min, '')}–{_n(tempo.t_max, ' ºC')}, "
            f"{_n(tempo.choiva, ' l/m²')}, vento {_n(tempo.vento_medio, ' m/s')} "
            f"(refacho {_n(tempo.refacho, '')})")


def avisos(tipo: str, tempo: TempoDia, choiva_antes: float | None = None) -> list[str]:
    """Os avisos do tempo dun traballo (tipos do Diario). Nunca bloquean."""
    lista: list[str] = []
    choveu = tempo.choiva is not None and tempo.choiva > 0
    if tipo == "abonado":
        if choveu:
            lista.append(f"Choveu {_n(tempo.choiva, ' l/m²')} ese día: non se pode abonar en "
                         "terreo encharcado ou inundado (RD 1051/2022, art. 4.4)")
        if tempo.t_min is not None and tempo.t_min <= 0:
            lista.append("Xeou ese día: non se pode abonar en terreo xeado "
                         "(RD 1051/2022, art. 4.4)")
    elif tipo == "tratamento":
        if choveu:
            lista.append(f"Choveu {_n(tempo.choiva, ' l/m²')} ese día: o produto pode lavarse. "
                         "Mira a etiqueta")
        if tempo.vento_medio is not None and tempo.vento_medio > VENTO_DERIVA_MS:
            lista.append(f"Vento medio de {_n(tempo.vento_medio, ' m/s')} ese día: risco de "
                         "deriva. É a media do día, non da hora do tratamento")
    elif tipo == "rega" and choiva_antes:
        lista.append(f"Choveron {_n(choiva_antes, ' l/m²')} nos dous días anteriores")
    return lista


def tempo_do_traballo(session: Session, fonte: Fonte, tipo: str, estacion_id: int | None,
                      data: date | None, hoxe: date | None = None) -> TempoDoTraballo | None:
    """O tempo dese día na estación, para mostralo no formulario mentres se apunta."""
    if estacion_id is None or data is None:
        return None
    tempo = consultar_tempo(session, fonte, estacion_id, data, hoxe)
    estacion = session.get(EstacionMeteo, estacion_id)
    if tempo is None or estacion is None:
        return None
    choiva_antes = None
    if tipo == "rega":
        antes = [consultar_tempo(session, fonte, estacion_id, data - timedelta(days=d), hoxe)
                 for d in (1, 2)]
        choiva_antes = sum(t.choiva or 0 for t in antes if t is not None)
    return TempoDoTraballo(resumo(tempo, estacion.nome), avisos(tipo, tempo, choiva_antes))


def estacion_do_lugar(session: Session, horta_id: int, parcela_id: int | None) -> int | None:
    """A estación dunha parcela ou, sen ela, a da explotación."""
    parcela = session.get(Parcela, parcela_id) if parcela_id is not None else None
    horta = session.get(Horta, horta_id)
    return ((parcela.estacion_meteo_id if parcela else None)
            or (horta.estacion_meteo_id if horta else None))
```

### Paso 11 — crear o ficheiro `tests/services/test_tempo.py`

Contido completo:
```python
"""O tempo (docs/superpowers/specs/2026-10-29-tempo-design.md). As probas nunca usan a rede:
len exemplos gardados de MeteoGalicia (tests/datos/meteogalicia)."""

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from horta.models.persoa import Persoa
from horta.models.tempo import TempoDia, onde_e_cando
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.meteogalicia import (
    SenTempo,
    ler_dias,
    ler_estacions,
    ler_predicion,
)
from horta.services.outros_traballos import DatosOutroTraballo, crear_outro_traballo
from horta.services.parcelas import crear_parcela
from horta.services.tempo import (
    aviso_distancia,
    avisos,
    concellos,
    consultar_tempo,
    encher_tempo,
    gardar_lugar,
    por_distancia,
    tempo_do_traballo,
)

DATOS = Path(__file__).resolve().parents[1] / "datos" / "meteogalicia"
HOXE = date(2026, 10, 29)
MABEGONDO, TORRE, XIPRO = 10045, 10157, 10136


def _ler(nome):
    return json.loads((DATOS / nome).read_text(encoding="utf-8"))


class Exemplo:
    """MeteoGalicia de mentira: os exemplos gardados, e conta as consultas."""

    def __init__(self, falla=False):
        self.falla = falla
        self.consultas = []

    def estacions(self):
        return ler_estacions(_ler("estacions.json"))

    def dias(self, estacion_id, desde, ata):
        self.consultas.append((estacion_id, desde, ata))
        if self.falla:
            raise SenTempo("sen conexión")
        return [d for d in ler_dias(_ler("dias.json"))
                if d.estacion_id == estacion_id and desde <= d.data <= ata]

    def predicion(self, concello_ine):
        return ler_predicion(_ler("predicion.json"))


def _estacion(id_):
    return next(e for e in Exemplo().estacions() if e.id == id_)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    return ana, horta, quen


def test_le_os_datos_de_meteogalicia():
    [dia1, dia2] = ler_dias(_ler("dias.json"))
    assert (dia1.estacion_id, dia1.data) == (MABEGONDO, date(2026, 10, 1))
    assert dia1.medidas == {"t_min": 8.55, "t_max": 20.46, "t_media": 13.94, "choiva": 0.0,
                            "vento_medio": 1.14, "refacho": 8.5, "humidade": 83.0,
                            "et0": 2.63}
    # O refacho do día 2 non está validado: queda baleiro
    assert dia2.medidas["refacho"] is None and dia2.medidas["vento_medio"] == 0.86
    assert {e.id for e in Exemplo().estacions()} == {MABEGONDO, TORRE, XIPRO}
    [hoxe, mañá] = ler_predicion(_ler("predicion.json"))
    assert (hoxe.data, hoxe.t_min, hoxe.t_max, hoxe.choiva_pct) == (HOXE, 10, 20, 5)
    assert concellos()["15078"] == "Santiago de Compostela" and len(concellos()) == 313


def test_estacion_mais_proxima_e_lonxe():
    # Unha leira en Abegondo, a uns centos de metros de Mabegondo
    [(primeira, km), *_] = por_distancia(Exemplo().estacions(), 43.245, -8.265)
    assert primeira.id == MABEGONDO and km < 1
    xipro = SimpleNamespace(lat=_estacion(XIPRO).lat, lon=_estacion(XIPRO).lon)
    assert aviso_distancia(xipro, 43.245, -8.265).startswith("A estación está a ")
    assert aviso_distancia(SimpleNamespace(lat=43.241, lon=-8.262), 43.245, -8.265) is None


def test_lugar_da_explotacion_e_da_parcela(session):
    ana, horta, _ = _escenario(session)
    gardar_lugar(session, ana, horta, "15001", _estacion(TORRE))
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    with pytest.raises(OperacionNonPermitidaError, match="concello"):
        gardar_lugar(session, ana, parcela, "99999", None)
    cultivo = crear_cultivo(session, ana, parcela.id, "Millo")
    sen_estacion = SimpleNamespace(horta_id=horta.id, data_inicio=date(2026, 10, 1),
                                   leiras=[SimpleNamespace(cultivo_id=cultivo.id)])
    # Sen estación na parcela, a da explotación
    assert onde_e_cando(session, sen_estacion) == (horta.id, TORRE, date(2026, 10, 1))
    gardar_lugar(session, ana, parcela, None, _estacion(MABEGONDO))
    assert onde_e_cando(session, sen_estacion)[1] == MABEGONDO


def test_o_traballo_garda_o_tempo_do_seu_dia(session):
    ana, horta, quen = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    gardar_lugar(session, ana, parcela, None, _estacion(MABEGONDO))
    fonte = Exemplo()
    tempo = consultar_tempo(session, fonte, MABEGONDO, date(2026, 10, 1), HOXE)
    assert (tempo.t_max, tempo.fonte) == (20.46, "MeteoGalicia")
    # Xa gardado: non se volve consultar nin se duplica
    assert consultar_tempo(session, fonte, MABEGONDO, date(2026, 10, 1), HOXE) is tempo
    assert len(fonte.consultas) == 1
    # O día de hoxe aínda non rematou
    assert consultar_tempo(session, fonte, MABEGONDO, HOXE, HOXE) is None
    traballo = crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 1), descricion="Peche",
        parcela_id=parcela.id, persoa_id=quen.id), hoxe=HOXE)
    assert traballo.tempo_id == tempo.id


def test_sen_conexion_apuntase_e_enchese_despois(session):
    ana, horta, quen = _escenario(session)
    gardar_lugar(session, ana, horta, None, _estacion(MABEGONDO))

    def apuntar(dia):
        return crear_outro_traballo(session, ana, DatosOutroTraballo(
            horta_id=horta.id, data_inicio=dia, descricion="Limpar", persoa_id=quen.id),
            hoxe=HOXE)

    sen_rede = Exemplo(falla=True)
    assert tempo_do_traballo(session, sen_rede, "outro_traballo", MABEGONDO,
                             date(2026, 10, 1), HOXE) is None
    primeiro, segundo, de_hoxe = (apuntar(date(2026, 10, 1)), apuntar(date(2026, 10, 2)),
                                  apuntar(HOXE))
    assert primeiro.tempo_id is None
    assert encher_tempo(session, ana, horta.id, sen_rede, HOXE) == 0
    fonte = Exemplo()
    assert encher_tempo(session, ana, horta.id, fonte, HOXE) == 2
    # Unha soa consulta para os dous días
    assert fonte.consultas == [(MABEGONDO, date(2026, 10, 1), date(2026, 10, 2))]
    assert primeiro.tempo_id and segundo.tempo_id and de_hoxe.tempo_id is None
    assert session.query(TempoDia).count() == 2


def test_avisos():
    def tempo(**medidas):
        return TempoDia(data=date(2026, 10, 1), **{"choiva": 0, "t_min": 5,
                                                   "vento_medio": 1, **medidas})

    assert avisos("abonado", tempo()) == []
    assert [a.split(":")[0] for a in avisos("abonado", tempo(choiva=12, t_min=-1))] == [
        "Choveu 12 l/m² ese día", "Xeou ese día"]
    assert "risco de deriva" in avisos("tratamento", tempo(vento_medio=4.2))[0]
    assert avisos("tratamento", tempo(vento_medio=3)) == []
    assert avisos("rega", tempo(), choiva_antes=8.5) == [
        "Choveron 8.5 l/m² nos dous días anteriores"]
    assert avisos("rega", tempo(), choiva_antes=0) == []
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O tempo (1/2): estacións, tempo de cada día e avisos: feito.

"""O tempo: as estacións de MeteoGalicia
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

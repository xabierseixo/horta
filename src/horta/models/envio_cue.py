"""O que horta envía ao CUE da Xunta (XEAGA) e en que estado está cada actividade
."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base

# Estado de cada actividade no CUE da Xunta
ESTADOS_CUE = {"enviado": "Enviado, sen comprobar", "aceptado": "Aceptado na Xunta",
               "erro": "Con erro na Xunta", "pechado": "Pechado na Xunta (xa non se cambia)"}


class EnvioCue(Base):
    """Cada envío (método crear): o período, a petición e o que respondeu a Xunta."""

    __tablename__ = "envio_cue"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    enviado: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))
    desde: Mapped[date] = mapped_column(Date)
    ata: Mapped[date] = mapped_column(Date)
    actividades: Mapped[int] = mapped_column(default=0)
    peticion: Mapped[int | None] = mapped_column(BigInteger, default=None)
    # pendente (sen procesar na Xunta), OK, PARCIAL ou FALLO
    resultado: Mapped[str] = mapped_column(String(20), default="pendente")
    mensaxes: Mapped[str | None] = mapped_column(Text, default=None)
    comprobado: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class RexistroCue(Base):
    """Unha actividade (ou leira allea) enviada: o último que se mandou e o seu estado."""

    __tablename__ = "rexistro_cue"
    __table_args__ = (UniqueConstraint("horta_id", "bloque", "id_ajena"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    bloque: Mapped[str] = mapped_column(String(40))
    id_ajena: Mapped[int] = mapped_column(BigInteger)
    # De que traballo saíu (services.cue.Orixe)
    orixe_tipo: Mapped[str] = mapped_column(String(30))
    orixe_id: Mapped[int | None] = mapped_column(default=None)
    data: Mapped[date | None] = mapped_column(Date, default=None)
    # sha256 do bloque enviado: se cambia, hai que volver envialo
    pegada: Mapped[str] = mapped_column(String(64))
    datos: Mapped[str] = mapped_column(Text)
    borrado: Mapped[bool] = mapped_column(default=False)
    estado: Mapped[str] = mapped_column(String(20), default="enviado")
    mensaxe: Mapped[str | None] = mapped_column(String(500), default=None)
    id_cuaderno: Mapped[int | None] = mapped_column(BigInteger, default=None)
    envio_id: Mapped[int] = mapped_column(ForeignKey("envio_cue.id"))

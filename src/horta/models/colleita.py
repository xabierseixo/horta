from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Colleita(ParteComun, FeitoPor, ConMaquina, Base):
    """Cada colleita dun cultivo (CUE bloque Cosecha) co seu lote. Baixa lóxica."""

    __tablename__ = "colleita"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    lote: Mapped[str] = mapped_column(String(40))
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    # Caderno 5 (colleita comercializada): cliente; trazabilidade (Reg. CE 178/2002 art. 18)
    cliente_nome: Mapped[str | None] = mapped_column(String(200), default=None)
    cliente_nif: Mapped[str | None] = mapped_column(String(14), default=None)
    cliente_enderezo: Mapped[str | None] = mapped_column(String(250), default=None)
    cliente_reaga: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_colleita: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_restos: Mapped[str | None] = mapped_column(String(20), default=None)
    # Anexo V CUE 11 (colleita): respostas S/N obrigatorias e maquinaria (voluntaria)
    obten_sementes: Mapped[bool] = mapped_column(Boolean, default=False)
    obten_plantas: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_colleita_ambiental: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)

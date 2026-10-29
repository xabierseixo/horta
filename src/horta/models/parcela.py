from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class SecanoRegadio(enum.Enum):
    SECANO = "secano"
    REGADIO = "regadio"


class Parcela(Base):
    __tablename__ = "parcela"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    nome: Mapped[str] = mapped_column(String(120))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)  # hectáreas
    posicion: Mapped[str | None] = mapped_column(String(120), default=None)
    lat: Mapped[float | None] = mapped_column(Float, default=None)
    lon: Mapped[float | None] = mapped_column(Float, default=None)
    uso_aproveitamento: Mapped[str | None] = mapped_column(String(120), default=None)
    secano_regadio: Mapped[SecanoRegadio | None] = mapped_column(Enum(SecanoRegadio), default=None)
    # O tempo: concello (código INE) e estación de MeteoGalicia; baleiros = os da explotación
    concello_ine: Mapped[str | None] = mapped_column(String(5), default=None)
    estacion_meteo_id: Mapped[int | None] = mapped_column(ForeignKey("estacion_meteo.id"),
                                                          default=None)
    sigpac_provincia: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_concello: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_poligono: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_parcela: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_subparcela: Mapped[str | None] = mapped_column(String(10), default=None)  # recinto
    # REA bloque 12 (DGC): resto da referencia SIGPAC, catastro, tenencia, alta e baixa
    sigpac_agregado: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_zona: Mapped[str | None] = mapped_column(String(10), default=None)
    referencia_catastral: Mapped[str | None] = mapped_column(String(20), default=None)
    rexime_tenencia: Mapped[str | None] = mapped_column(String(20), default=None)
    arrendador_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    pequena_superficie: Mapped[bool] = mapped_column(Boolean, default=False)
    data_alta: Mapped[date | None] = mapped_column(Date, default=None)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    causa_baixa: Mapped[str | None] = mapped_column(String(20), default=None)
    orixe_auga: Mapped[str | None] = mapped_column(String(20), default=None)
    # Caderno 2.2 (RD 1311/2012 art. 33-35, Anexo III): auga para consumo humano e zonas
    auga_consumo: Mapped[bool] = mapped_column(Boolean, default=False)
    auga_consumo_na_parcela: Mapped[bool] = mapped_column(Boolean, default=False)
    auga_consumo_distancia_m: Mapped[float | None] = mapped_column(Float, default=None)
    auga_consumo_utm: Mapped[str | None] = mapped_column(String(50), default=None)
    auga_consumo_denominacion: Mapped[str | None] = mapped_column(String(150), default=None)
    zona_especifica: Mapped[str | None] = mapped_column(String(10), default=None)
    zona_especifica_ha: Mapped[float | None] = mapped_column(Float, default=None)
    geometria: Mapped[str | None] = mapped_column(Text, default=None)
    imaxe: Mapped[str | None] = mapped_column(String(500), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="activa")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

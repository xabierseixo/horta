from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class TipoCarne(enum.Enum):
    basico = "basico"
    cualificado = "cualificado"
    fumigador = "fumigador"
    piloto = "piloto"
    sector_suministrador = "sector_suministrador"
    sector_tratamentos = "sector_tratamentos"


class Persoa(Base):
    """Toda a xente e as empresas coas que trata a explotación, de dentro e de fóra, cos seus
    papeis."""

    __tablename__ = "persoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # persoa (física) ou entidade (empresa, cooperativa, laboratorio...)
    tipo: Mapped[str] = mapped_column(String(10), default="persoa")
    # Nome, ou razón social se é unha entidade
    nome: Mapped[str] = mapped_column(String(200))
    apelidos: Mapped[str | None] = mapped_column(String(200), default=None)
    nif: Mapped[str | None] = mapped_column(String(9), default=None)
    ropo_numero: Mapped[str | None] = mapped_column(String(14), default=None)
    ropo_tipo_carne: Mapped[TipoCarne | None] = mapped_column(Enum(TipoCarne), default=None)
    ropo_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    regfer_numero: Mapped[str | None] = mapped_column(String(20), default=None)
    # Enderezo (caderno de explotación 1.1, para o titular)
    enderezo: Mapped[str | None] = mapped_column(String(200), default=None)
    localidade: Mapped[str | None] = mapped_column(String(100), default=None)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), default=None)
    provincia: Mapped[str | None] = mapped_column(String(50), default=None)
    # CUE 3 (quen merca): concello (código INE) e país se non é España
    concello_codigo: Mapped[str | None] = mapped_column(String(5), default=None)
    pais: Mapped[str | None] = mapped_column(String(50), default=None)
    # Rexistros, segundo o papel: REGA (outra explotación), REAGA, NIMA (residuos),
    # ROPVEG (provedor de plantas), rexistro dixital de alimentos (CUE 3), nº de asesoramento
    rega: Mapped[str | None] = mapped_column(String(14), default=None)
    reaga: Mapped[str | None] = mapped_column(String(14), default=None)
    nima: Mapped[str | None] = mapped_column(String(50), default=None)
    ropveg: Mapped[str | None] = mapped_column(String(50), default=None)
    rexistro_dixital: Mapped[str | None] = mapped_column(String(50), default=None)
    num_asesoramento: Mapped[str | None] = mapped_column(String(50), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    # Equipo (deseño 2026-10-23-equipo): conta, funcións e datos de emprego (UTA, AGADER)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    telefono: Mapped[str | None] = mapped_column(String(30), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    vinculo: Mapped[str | None] = mapped_column(String(20), default=None)
    horas_ano: Mapped[float | None] = mapped_column(Float, default=None)
    formacion_agraria: Mapped[str | None] = mapped_column(String(200), default=None)
    xenero: Mapped[str | None] = mapped_column(String(10), default=None)
    data_nacemento: Mapped[date | None] = mapped_column(Date, default=None)
    discapacidade: Mapped[bool] = mapped_column(Boolean, default=False)

    papeis_rexistro: Mapped[list[PersoaPapel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def papeis(self) -> set[str]:
        """Os papeis da persoa (services.persoas.PAPEIS)."""
        return {p.papel for p in self.papeis_rexistro}

    def ten_papel(self, *papeis: str) -> bool:
        return bool(self.papeis & set(papeis))


class PersoaPapel(Base):
    """Cada papel dunha persoa: titular, traballador, aplicador, cliente, provedor..."""

    __tablename__ = "persoa_papel"
    __table_args__ = (UniqueConstraint("persoa_id", "papel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"), index=True)
    papel: Mapped[str] = mapped_column(String(20))

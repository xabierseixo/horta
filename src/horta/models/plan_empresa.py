"""Plan de empresa (paso 16):
AGADER Anexo III (resumo e conta a 5 anos) e Anexo V (investimento por partidas)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class PlanEmpresa(Base):
    __tablename__ = "plan_empresa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    linea: Mapped[str] = mapped_column(String(20), default="agader")
    ano_inicio: Mapped[int] = mapped_column(Integer)
    empresa_nova: Mapped[bool] = mapped_column(Boolean, default=False)
    cnae: Mapped[str | None] = mapped_column(String(10), default=None)
    descricion: Mapped[str | None] = mapped_column(Text, default=None)
    proceso: Mapped[str | None] = mapped_column(Text, default=None)
    formacion: Mapped[str | None] = mapped_column(Text, default=None)
    # Emprego en UTA (Anexo III, 3)
    uta_mantidas: Mapped[float] = mapped_column(Float, default=0)
    uta_creadas: Mapped[float] = mapped_column(Float, default=0)
    uta_mulleres: Mapped[float] = mapped_column(Float, default=0)
    uta_mozas: Mapped[float] = mapped_column(Float, default=0)
    uta_maiores: Mapped[float] = mapped_column(Float, default=0)
    uta_discapacidade: Mapped[float] = mapped_column(Float, default=0)
    uta_outros: Mapped[float] = mapped_column(Float, default=0)
    # Para o VAN (en tanto por un)
    taxa_desconto: Mapped[float] = mapped_column(Float, default=0.03)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc))

    investimentos: Mapped[list[PlanInvestimento]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    financiamento: Mapped[list[PlanFinanciamento]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    anos: Mapped[list[PlanAno]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="PlanAno.ano_n")


class PlanInvestimento(Base):
    __tablename__ = "plan_investimento"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan_empresa.id"), index=True)
    # services.plan_empresa.PARTIDAS (Anexo V)
    partida: Mapped[str] = mapped_column(String(2))
    concepto: Mapped[str] = mapped_column(String(200))
    importe_sen_iva: Mapped[float] = mapped_column(Float)
    iva_pct: Mapped[float] = mapped_column(Float, default=21)
    # Amortización lineal; 0 = non se amortiza (terreos)
    vida_util_anos: Mapped[int] = mapped_column(Integer, default=10)
    # Cantas ofertas de provedores hai (art. 18.h: tres por gasto)
    ofertas: Mapped[int] = mapped_column(Integer, default=0)


class PlanFinanciamento(Base):
    __tablename__ = "plan_financiamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan_empresa.id"), index=True)
    # services.plan_empresa.FONTES
    tipo: Mapped[str] = mapped_column(String(20))
    importe: Mapped[float] = mapped_column(Float)
    # Só nos préstamos: xuro anual (%) e anos (cota constante)
    xuro_pct: Mapped[float | None] = mapped_column(Float, default=None)
    anos: Mapped[int | None] = mapped_column(Integer, default=None)


class PlanAno(Base):
    __tablename__ = "plan_ano"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plan_empresa.id"), index=True)
    ano_n: Mapped[int] = mapped_column(Integer)  # 1–5
    vendas: Mapped[float] = mapped_column(Float, default=0)
    custos_variables: Mapped[float] = mapped_column(Float, default=0)
    custos_fixos: Mapped[float] = mapped_column(Float, default=0)

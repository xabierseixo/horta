"""Plan de empresa (paso 16): AGADER Anexo III (resumo e conta a 5
anos), Anexo V (investimento por partidas) e Anexo VI-A (ofertas)."""

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
    # services.plan_empresa.TIPOLOXIAS (arts. 11–15 da convocatoria)
    tipoloxia: Mapped[str | None] = mapped_column(String(30), default=None)
    ano_inicio: Mapped[int] = mapped_column(Integer)
    # Datos do proxecto (Anexo III): os dá o GDR ao rexistrar a solicitude
    expediente: Mapped[str | None] = mapped_column(String(30), default=None)
    anualidade: Mapped[int | None] = mapped_column(Integer, default=None)
    submedida: Mapped[str | None] = mapped_column(String(20), default=None)
    gdr: Mapped[str | None] = mapped_column(String(100), default=None)
    empresa_nova: Mapped[bool] = mapped_column(Boolean, default=False)
    cnae: Mapped[str | None] = mapped_column(String(10), default=None)
    # Pequena empresa (art. 4.2.c; anexo I do Reg. UE 651/2014), da empresa ou do grupo
    participada: Mapped[bool] = mapped_column(Boolean, default=False)
    traballadores: Mapped[float | None] = mapped_column(Float, default=None)
    facturacion: Mapped[float | None] = mapped_column(Float, default=None)
    balance: Mapped[float | None] = mapped_column(Float, default=None)
    # Art. 8.b: o IVE recuperable non se subvenciona
    iva_recuperable: Mapped[bool] = mapped_column(Boolean, default=True)
    descricion: Mapped[str | None] = mapped_column(Text, default=None)
    proceso: Mapped[str | None] = mapped_column(Text, default=None)
    formacion: Mapped[str | None] = mapped_column(Text, default=None)
    # Memoria (art. 18.1.f): situación de partida e metodoloxía de traballo
    situacion_partida: Mapped[str | None] = mapped_column(Text, default=None)
    metodoloxia: Mapped[str | None] = mapped_column(Text, default=None)
    mercado: Mapped[str | None] = mapped_column(Text, default=None)
    # Anexo VI-B: declaracións sobre os provedores
    ofertas_autenticas: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_vinculo_promotor: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_vinculo_entre_provedores: Mapped[bool] = mapped_column(Boolean, default=False)
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
    # Art. 20.1: por que non hai tres ofertas (non hai provedores abondo)
    motivo_sen_ofertas: Mapped[str | None] = mapped_column(Text, default=None)

    ofertas: Mapped[list[PlanOferta]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="PlanOferta.importe_sen_iva")


class PlanOferta(Base):
    """Unha oferta pedida para un concepto do investimento (Anexo VI-A)."""

    __tablename__ = "plan_oferta"

    id: Mapped[int] = mapped_column(primary_key=True)
    investimento_id: Mapped[int] = mapped_column(ForeignKey("plan_investimento.id"),
                                                 index=True)
    provedor_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    importe_sen_iva: Mapped[float] = mapped_column(Float)
    elixida: Mapped[bool] = mapped_column(Boolean, default=False)
    criterio: Mapped[str | None] = mapped_column(String(200), default=None)
    # Se a elixida non é a máis económica (art. 20.4)
    xustificacion: Mapped[str | None] = mapped_column(Text, default=None)


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
    ingresos_financeiros: Mapped[float] = mapped_column(Float, default=0)

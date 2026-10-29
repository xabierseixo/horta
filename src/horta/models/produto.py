"""Produtos (insumos) da explotación e as súas entradas (compras ou recepcións):
o deseño. Mércase unha vez e úsase
moitas: os usos (abonado, tratamento, coidado, sementeira) apuntan ao produto e á entrada."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # services.produtos.TIPOS_PRODUTO: fitosanitario, abono, semente, medicamento, penso,
    # enerxia, outro
    tipo: Mapped[str] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(250))
    # Unidade das existencias: kg, l ou unidades
    unidade: Mapped[str] = mapped_column(String(20))
    # Fitosanitario: nº do rexistro do MAPA; medicamento: nº de autorización
    num_rexistro: Mapped[str | None] = mapped_column(String(20), default=None)
    # Abono: a súa composición
    fertilizante_id: Mapped[int | None] = mapped_column(
        ForeignKey("fertilizante.id"), unique=True, default=None)
    # Enerxía: catálogo tipo_enerxia (CUE 2)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class EntradaProduto(ParteComun, FeitoPor, Base):
    """Cada compra ou recepción dun produto: un traballo coa parte común."""

    __tablename__ = "entrada_produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    # Baleira se non se sabe (datos de antes do paso 7)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    lote_provedor: Mapped[str | None] = mapped_column(String(50), default=None)
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    importe: Mapped[float | None] = mapped_column(Float, default=None)
    data_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    # Sementes e plantas (Reg. UE 2016/2031)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)

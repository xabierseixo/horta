"""Rexistro de accesos para inspección e auditoría (tarefa 182b)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.usuario import Usuario


class RexistroAcceso(Base):
    __tablename__ = "rexistro_acceso"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    data_hora: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    seccion: Mapped[str] = mapped_column(String(40))

    usuario: Mapped[Usuario] = relationship("Usuario", lazy="joined")

    @property
    def conta(self) -> str:
        return self.usuario.nome if self.usuario else ""

    @property
    def nome_conta(self) -> str:
        return self.conta

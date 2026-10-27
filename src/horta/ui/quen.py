"""«Quen o fixo» nos formularios de traballo: todo traballo o fai unha persoa do equipo."""

from __future__ import annotations

from horta.db import get_session
from horta.services.diario import ultima_persoa
from horta.ui.sesion import usuario_actual


def proposta_quen(horta_id: int) -> int | None:
    """Quen fixo o último traballo, para propoñelo ao apuntar o seguinte."""
    with get_session() as session:
        actor = usuario_actual(session)
        return ultima_persoa(session, actor, horta_id) if actor else None

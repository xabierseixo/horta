"""«Quen o fixo» nos formularios de traballo: todo traballo o fai unha persoa do equipo."""

from __future__ import annotations

from horta.db import get_session
from horta.models.persoa import Persoa
from horta.models.tarefa import Tarefa
from horta.services.diario import ultima_persoa
from horta.ui.sesion import usuario_actual


def proposta_quen(horta_id: int, tarefa: Tarefa | None = None) -> int | None:
    """Quen ía facer a tarefa ou, se non, quen fixo o último traballo, para propoñelo (só se
    segue activa no equipo: os formularios só ofrecen as persoas activas)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return None
        persoa_id = (tarefa.persoa_id if tarefa is not None and tarefa.persoa_id is not None
                     else ultima_persoa(session, actor, horta_id))
        persoa = session.get(Persoa, persoa_id) if persoa_id is not None else None
        return persoa.id if persoa is not None and persoa.activa else None

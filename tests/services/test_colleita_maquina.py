from datetime import date

import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import (
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    crear_colleitas,
)
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

HOXE = date(2026, 10, 23)


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.5, data_inicio=date(2026, 3, 1))
    return ana, horta, cultivo


def _datos(cultivo, **cambios) -> DatosColleita:
    base = {
        "cultivo_id": cultivo.id,
        "data": date(2026, 7, 15),
        "cantidade": 1000.0,
        "unidade": "kg",
        "lote": "2026-PATACA-001",
    }
    return DatosColleita(**{"persoa_id": QUEN, **base, **cambios})


def test_crear_colleita_maquina_doutra_explotacion(session):
    ana, _, cultivo = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    maquina_allea = crear_maquina(
        session, ana, outra.id, "Tractor alleo", id_equipo_non_inscribible="M1"
    )
    with pytest.raises(OperacionNonPermitidaError, match="máquina"):
        crear_colleita(session, ana, _datos(cultivo, maquina_id=maquina_allea.id), hoxe=HOXE)


def test_crear_colleita_maquina_propia(session):
    ana, horta, cultivo = _escenario(session)
    maquina_propia = crear_maquina(
        session, ana, horta.id, "Tractor propio", id_equipo_non_inscribible="M2"
    )
    colleita = crear_colleita(
        session, ana, _datos(cultivo, maquina_id=maquina_propia.id), hoxe=HOXE
    )
    assert colleita.maquina_id == maquina_propia.id


def test_actualizar_colleita_maquina(session):
    ana, horta, cultivo = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    maquina_propia = crear_maquina(
        session, ana, horta.id, "Tractor propio", id_equipo_non_inscribible="M1"
    )
    maquina_allea = crear_maquina(
        session, ana, outra.id, "Tractor alleo", id_equipo_non_inscribible="M2"
    )
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert colleita.maquina_id is None

    with pytest.raises(OperacionNonPermitidaError, match="máquina"):
        actualizar_colleita(
            session, ana, colleita, _datos(cultivo, maquina_id=maquina_allea.id), hoxe=HOXE
        )

    actualizar_colleita(
        session, ana, colleita, _datos(cultivo, maquina_id=maquina_propia.id), hoxe=HOXE
    )
    assert colleita.maquina_id == maquina_propia.id

    actualizar_colleita(session, ana, colleita, _datos(cultivo, maquina_id=None), hoxe=HOXE)
    assert colleita.maquina_id is None


def test_crear_colleitas_varias_leiras_maquina(session):
    ana, horta, cultivo1 = _escenario(session)
    parcela2 = crear_parcela(session, ana, horta.id, "P2")
    cultivo2 = crear_cultivo(session, ana, parcela2.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo2, superficie_ha=0.5, data_inicio=date(2026, 3, 1))
    outra = crear_horta(session, ana, "Outra")
    maquina_propia = crear_maquina(
        session, ana, horta.id, "Tractor propio", id_equipo_non_inscribible="M1"
    )
    maquina_allea = crear_maquina(
        session, ana, outra.id, "Tractor alleo", id_equipo_non_inscribible="M2"
    )
    cantidades = {cultivo1.id: 500.0, cultivo2.id: 500.0}

    with pytest.raises(OperacionNonPermitidaError, match="máquina"):
        crear_colleitas(
            session,
            ana,
            _datos(cultivo1, maquina_id=maquina_allea.id),
            cantidades,
            hoxe=HOXE,
        )

    colleitas = crear_colleitas(
        session,
        ana,
        _datos(cultivo1, maquina_id=maquina_propia.id),
        cantidades,
        hoxe=HOXE,
    )
    assert len(colleitas) == 2
    assert all(c.maquina_id == maquina_propia.id for c in colleitas)

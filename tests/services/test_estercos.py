"""Probas dos movementos de esterco e purín (RD 1051/2022)."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.estercos import (
    ORIXES_COMPOSICION,
    actualizar_movemento,
    crear_movemento,
    dar_de_baixa_movemento,
    faltas_documento,
    listar_movementos,
)
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.persoas import crear_contacto


def _usuario(session, email: str) -> Usuario:
    u = Usuario(
        nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True
    )
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    # "1" (purín de porco) e "5" (esterco de bovino) son estercos; "14" é abono químico
    for codigo in ("1", "5", "14"):
        session.add(
            CatalogoValor(
                catalogo="material_fertilizante",
                codigo=codigo,
                descricion=f"Material {codigo}",
                version_id=v.id,
            )
        )
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    outra_parte = crear_contacto(
        session, ana, horta.id, "Granxa Veciña", "explotacion", rega="ES150000001"
    )
    return ana, horta, outra_parte


def test_crear_cesion_correcta(session):
    ana, horta, outra_parte = _escenario(session)
    mov = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="cesion",
        data=date(2026, 4, 10),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino de leite",
        tipo_animais="01",
        material="5",
        cantidade=12.5,
        unidade="t",
        n_total=2.4,
        p2o5=1.2,
        k2o=3.1,
        materia_organica=25.0,
        orixe_composicion="analise",
        parcelas_destino="Parcela norte",
        notas="Esterco maduro",
    )
    assert mov.id is not None
    assert mov.horta_id == horta.id
    assert mov.tipo == "cesion"
    assert mov.cantidade == 12.5
    assert mov.unidade == "t"
    assert mov.n_total == 2.4
    assert mov.p2o5 == 1.2
    assert mov.k2o == 3.1
    assert mov.materia_organica == 25.0
    assert mov.orixe_composicion == "analise"
    assert mov.outra_parte_id == outra_parte.id
    assert mov.tipo_explotacion == "Bovino de leite"
    assert mov.tipo_animais == "01"
    assert mov.parcelas_destino == "Parcela norte"
    assert mov.notas == "Esterco maduro"
    assert mov.creado_por == ana.id
    assert mov.baixa is False
    assert faltas_documento(mov) == []


def test_crear_recepcion_correcta(session):
    ana, horta, outra_parte = _escenario(session)
    mov = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="recepcion",
        data=date(2026, 5, 2),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Porcino de ceba",
        tipo_animais="02",
        material="1",
        cantidade=20.0,
        unidade="m3",
    )
    assert mov.tipo == "recepcion"
    assert mov.cantidade == 20.0
    assert mov.unidade == "m3"
    assert mov.n_total is None
    assert mov.orixe_composicion is None


def test_outra_parte_doutra_horta(session):
    ana, horta, _ = _escenario(session)
    outra_horta = crear_horta(session, ana, "Outra Horta")
    contacto_alleo = crear_contacto(
        session, ana, outra_horta.id, "Alleo", "explotacion"
    )
    with pytest.raises(OperacionNonPermitidaError, match="outra parte"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=contacto_alleo.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_material_que_non_e_esterco(session):
    ana, horta, outra_parte = _escenario(session)
    # Material "14" é abono químico, non é esterco
    with pytest.raises(OperacionNonPermitidaError, match="esterco ou purín"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="14",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_material_non_existente_no_catalogo(session):
    ana, horta, outra_parte = _escenario(session)
    # Código "2" está en ESTERCOS pero non está rexistrado no catálogo
    with pytest.raises(OperacionNonPermitidaError, match="catálogo"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="2",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


@pytest.mark.parametrize("cantidade", [0, -1.0, -100])
def test_cantidade_invalida(session, cantidade):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="cantidade"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=cantidade,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_unidade_invalida(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="unidade"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="kg",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_tipo_invalido(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tipo"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="compra",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_cesion_sen_n_total(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="N total"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=None,
            orixe_composicion="analise",
        )


def test_cesion_sen_orixe_composicion(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="orixe"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion=None,
        )


def test_orixe_composicion_invalida(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="orixe"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="inventada",
        )


@pytest.mark.parametrize(("campo", "valor"), [
    ("n_total", 101.0),
    ("p2o5", -0.5),
    ("k2o", 150.0),
    ("materia_organica", -2.0),
])
def test_riqueza_fora_de_rango(session, campo, valor):
    ana, horta, outra_parte = _escenario(session)
    kwargs = {
        "tipo": "cesion",
        "data": date(2026, 4, 10),
        "outra_parte_id": outra_parte.id,
        "tipo_explotacion": "Bovino",
        "tipo_animais": "01",
        "material": "5",
        "cantidade": 10.0,
        "unidade": "t",
        "n_total": 2.0,
        "orixe_composicion": "analise",
        campo: valor,
    }
    with pytest.raises(OperacionNonPermitidaError, match="0 e 100"):
        crear_movemento(session, ana, horta.id, **kwargs)


def test_tipo_animais_invalido(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tipo de animais"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="especie_inexistente_999",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_tipo_explotacion_baleiro(session):
    ana, horta, outra_parte = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tipo de explotación"):
        crear_movemento(
            session,
            ana,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="   ",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_lector_non_pode_crear(session):
    ana, horta, outra_parte = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_movemento(
            session,
            bea,
            horta.id,
            tipo="cesion",
            data=date(2026, 4, 10),
            outra_parte_id=outra_parte.id,
            tipo_explotacion="Bovino",
            tipo_animais="01",
            material="5",
            cantidade=10.0,
            unidade="t",
            n_total=2.0,
            orixe_composicion="analise",
        )


def test_faltas_documento(session):
    ana, horta, outra_parte = _escenario(session)
    # Movemento de cesión onde só se puxeron n_total e orixe (o resto non bloquea)
    mov = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="cesion",
        data=date(2026, 4, 10),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino",
        tipo_animais="01",
        material="5",
        cantidade=10.0,
        unidade="t",
        n_total=2.0,
        orixe_composicion="analise",
    )
    faltas = faltas_documento(mov)
    assert "Fósforo (P₂O₅)" in faltas
    assert "Potasio (K₂O)" in faltas
    assert "Materia orgánica" in faltas
    assert "Nitróxeno total (N)" not in faltas
    assert "Orixe da composición" not in faltas

    # Movemento de recepción sen composición
    mov_rec = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="recepcion",
        data=date(2026, 4, 10),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino",
        tipo_animais="01",
        material="5",
        cantidade=10.0,
        unidade="t",
    )
    faltas_rec = faltas_documento(mov_rec)
    assert "Nitróxeno total (N)" in faltas_rec
    assert "Orixe da composición" in faltas_rec


def test_actualizar_movemento(session):
    ana, horta, outra_parte = _escenario(session)
    mov = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="cesion",
        data=date(2026, 4, 10),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino",
        tipo_animais="01",
        material="5",
        cantidade=10.0,
        unidade="t",
        n_total=2.0,
        orixe_composicion="analise",
    )
    actualizar_movemento(
        session,
        ana,
        mov,
        cantidade=15.0,
        p2o5=1.5,
        notas="Carga revisada",
    )
    assert mov.cantidade == 15.0
    assert mov.p2o5 == 1.5
    assert mov.notas == "Carga revisada"

    with pytest.raises(ValueError, match="non editables"):
        actualizar_movemento(session, ana, mov, horta_id=999)

    with pytest.raises(OperacionNonPermitidaError, match="N total"):
        actualizar_movemento(session, ana, mov, n_total=None)


def test_dar_de_baixa_movemento(session):
    ana, horta, outra_parte = _escenario(session)
    mov = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="cesion",
        data=date(2026, 4, 10),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino",
        tipo_animais="01",
        material="5",
        cantidade=10.0,
        unidade="t",
        n_total=2.0,
        orixe_composicion="analise",
    )
    dar_de_baixa_movemento(session, ana, mov)
    assert mov.baixa is True
    assert listar_movementos(session, ana, horta.id) == []

    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_movemento(session, ana, mov, cantidade=20.0)


def test_listar_movementos_filtros(session):
    ana, horta, outra_parte = _escenario(session)
    mov1 = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="cesion",
        data=date(2025, 6, 1),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino",
        tipo_animais="01",
        material="5",
        cantidade=5.0,
        unidade="t",
        n_total=1.5,
        orixe_composicion="analise",
    )
    mov2 = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="cesion",
        data=date(2026, 4, 10),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Bovino",
        tipo_animais="01",
        material="5",
        cantidade=10.0,
        unidade="t",
        n_total=2.0,
        orixe_composicion="analise",
    )
    mov3 = crear_movemento(
        session,
        ana,
        horta.id,
        tipo="recepcion",
        data=date(2026, 7, 15),
        outra_parte_id=outra_parte.id,
        tipo_explotacion="Porcino",
        tipo_animais="02",
        material="1",
        cantidade=30.0,
        unidade="m3",
    )

    # Todos: ordenados das máis novas ás máis vellas
    todos = listar_movementos(session, ana, horta.id)
    assert [m.id for m in todos] == [mov3.id, mov2.id, mov1.id]

    # Por ano
    do_2026 = listar_movementos(session, ana, horta.id, ano=2026)
    assert [m.id for m in do_2026] == [mov3.id, mov2.id]

    do_2025 = listar_movementos(session, ana, horta.id, ano=2025)
    assert [m.id for m in do_2025] == [mov1.id]

    # Por tipo
    cesions = listar_movementos(session, ana, horta.id, tipo="cesion")
    assert [m.id for m in cesions] == [mov2.id, mov1.id]

    recepcions = listar_movementos(session, ana, horta.id, tipo="recepcion")
    assert [m.id for m in recepcions] == [mov3.id]

    # Permisos de lectura
    bea = _usuario(session, "bea_lectora@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    assert len(listar_movementos(session, bea, horta.id)) == 3

    outra_horta = crear_horta(session, ana, "Outra Horta Sen Acceso")
    with pytest.raises(PermisoDenegadoError):
        listar_movementos(session, bea, outra_horta.id)

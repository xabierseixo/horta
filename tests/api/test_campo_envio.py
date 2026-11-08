"""Probas da API de envío de rexistros dende a app do campo (sen cobertura)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from horta.api.campo import obter_session, router
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.colleita import Colleita
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.observacion import ObservacionPraga
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.dispositivos import crear_dispositivo
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela
from horta.services.tarefas import crear_tarefa


@pytest.fixture()
def client(session: Session) -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[obter_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client


def _crear_usuario(session: Session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0].capitalize(),
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _configurar_catalogos(session: Session) -> None:
    v = CatalogoVersion(
        catalogo="proba",
        nome_ficheiro="proba.xlsx",
        sha256="c" * 64,
        filas=3,
    )
    session.add(v)
    session.flush()
    for cat, cod in [
        ("praga", "10"),
        ("sistema_rega", "6"),
        ("tipo_labor", "5"),
    ]:
        session.add(
            CatalogoValor(
                catalogo=cat,
                codigo=cod,
                descricion=f"{cat} {cod}",
                version_id=v.id,
            )
        )
    session.commit()


def test_observacion_e_rega_crean_rexistros_co_uuid(
    client: TestClient, session: Session, cultivos_siex: Any
) -> None:
    """Unha observación e unha rega crean os seus rexistros co uuid."""
    _configurar_catalogos(session)
    cultivos_siex(101)

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")
    parcela = crear_parcela(session, ana, horta.id, "Agra da Cruz")
    cultivo = crear_cultivo(
        session, ana, parcela.id, "Pataca", cultivo_siex_codigo=101, superficie_ha=0.5
    )

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_obs = "11111111-1111-1111-1111-111111111111"
    uuid_rega = "22222222-2222-2222-2222-222222222222"

    rexistros = [
        {
            "uuid": uuid_obs,
            "tipo": "observacion",
            "datos": {
                "cultivo_id": cultivo.id,
                "data": "2026-11-08",
                "problema_tipo": "praga",
                "problema_codigo": "10",
                "metodo": "trampa",
                "conto": 3.0,
                "unidade_conto": "capturas por trampa",
                "notas": "Trampa sur revisada",
            },
        },
        {
            "uuid": uuid_rega,
            "tipo": "rega",
            "datos": {
                "cultivo_id": cultivo.id,
                "data_inicio": "2026-11-08",
                "sistema_rega": "6",
                "cantidade": 250.0,
                "unidade": "4",
                "notas": "Rega por goteo ao serán",
            },
        },
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 2

    assert corpo[0]["uuid"] == uuid_obs
    assert corpo[0]["estado"] == "creado"
    assert corpo[0]["id"] is not None
    assert corpo[0]["mensaxe"] is None

    assert corpo[1]["uuid"] == uuid_rega
    assert corpo[1]["estado"] == "creado"
    assert corpo[1]["id"] is not None
    assert corpo[1]["mensaxe"] is None

    # Comprobar na base de datos que se gardaron co seu uuid
    obs_bd = session.get(ObservacionPraga, corpo[0]["id"])
    assert obs_bd is not None
    assert obs_bd.uuid == uuid_obs
    assert obs_bd.horta_id == horta.id
    assert obs_bd.cultivo_id == cultivo.id
    assert obs_bd.conto == 3.0

    rega_bd = session.get(Rega, corpo[1]["id"])
    assert rega_bd is not None
    assert rega_bd.uuid == uuid_rega
    assert rega_bd.horta_id == horta.id
    assert rega_bd.cantidade == 250.0


def test_mesmo_uuid_outra_vez_devolve_xa_estaba_sen_duplicados(
    client: TestClient, session: Session, cultivos_siex: Any
) -> None:
    """Mandar o mesmo uuid outra vez devolve xa_estaba e non hai duplicados."""
    _configurar_catalogos(session)
    cultivos_siex(101)

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")
    parcela = crear_parcela(session, ana, horta.id, "Agra da Cruz")
    cultivo = crear_cultivo(
        session, ana, parcela.id, "Pataca", cultivo_siex_codigo=101, superficie_ha=0.5
    )

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_obs = "33333333-3333-3333-3333-333333333333"
    uuid_rega = "44444444-4444-4444-4444-444444444444"

    rexistros = [
        {
            "uuid": uuid_obs,
            "tipo": "observacion",
            "datos": {
                "cultivo_id": cultivo.id,
                "data": "2026-11-08",
                "problema_tipo": "praga",
                "problema_codigo": "10",
                "metodo": "trampa",
                "conto": 1.0,
                "unidade_conto": "capturas por trampa",
            },
        },
        {
            "uuid": uuid_rega,
            "tipo": "rega",
            "datos": {
                "cultivo_id": cultivo.id,
                "data_inicio": "2026-11-08",
                "sistema_rega": "6",
                "cantidade": 120.0,
            },
        },
    ]

    r1 = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert r1.status_code == 200
    c1 = r1.json()
    id_obs_1 = c1[0]["id"]
    id_rega_1 = c1[1]["id"]
    assert c1[0]["estado"] == "creado"
    assert c1[1]["estado"] == "creado"

    # Segunda chamada cos mesmos uuids
    r2 = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert r2.status_code == 200
    c2 = r2.json()
    assert len(c2) == 2
    assert c2[0]["uuid"] == uuid_obs
    assert c2[0]["estado"] == "xa_estaba"
    assert c2[0]["id"] == id_obs_1

    assert c2[1]["uuid"] == uuid_rega
    assert c2[1]["estado"] == "xa_estaba"
    assert c2[1]["id"] == id_rega_1

    # Verificar que non hai duplicados na base de datos
    total_obs = session.query(ObservacionPraga).filter_by(horta_id=horta.id).count()
    assert total_obs == 1
    total_regas = session.query(Rega).filter_by(horta_id=horta.id).count()
    assert total_regas == 1


def test_rexistro_mal_da_erro_e_os_outros_creanse(
    client: TestClient, session: Session, cultivos_siex: Any
) -> None:
    """Un rexistro mal (cultivo doutra horta) dá erro, e os outros da petición créanse."""
    _configurar_catalogos(session)
    cultivos_siex(101, 102)

    ana = _crear_usuario(session, "ana@example.com")
    horta_ana = crear_horta(session, ana, "Horta de Ana")
    parcela_ana = crear_parcela(session, ana, horta_ana.id, "Leira de Ana")
    cultivo_ana = crear_cultivo(
        session, ana, parcela_ana.id, "Cenoria", cultivo_siex_codigo=101, superficie_ha=0.2
    )

    bea = _crear_usuario(session, "bea@example.com")
    horta_bea = crear_horta(session, bea, "Horta de Bea")
    parcela_bea = crear_parcela(session, bea, horta_bea.id, "Leira de Bea")
    cultivo_bea = crear_cultivo(
        session, bea, parcela_bea.id, "Espinaca", cultivo_siex_codigo=102, superficie_ha=0.3
    )

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_1 = "55555555-5555-5555-5555-555555555555"
    uuid_mal = "66666666-6666-6666-6666-666666666666"
    uuid_2 = "77777777-7777-7777-7777-777777777777"

    rexistros = [
        {
            "uuid": uuid_1,
            "tipo": "observacion",
            "datos": {
                "cultivo_id": cultivo_ana.id,
                "data": "2026-11-08",
                "problema_tipo": "praga",
                "problema_codigo": "10",
                "metodo": "trampa",
                "conto": 2.0,
                "unidade_conto": "capturas por trampa",
            },
        },
        {
            # Cultivo doutra explotación: debe fallar con erro
            "uuid": uuid_mal,
            "tipo": "observacion",
            "datos": {
                "cultivo_id": cultivo_bea.id,
                "data": "2026-11-08",
                "problema_tipo": "praga",
                "problema_codigo": "10",
                "metodo": "trampa",
                "conto": 5.0,
                "unidade_conto": "capturas por trampa",
            },
        },
        {
            "uuid": uuid_2,
            "tipo": "rega",
            "datos": {
                "cultivo_id": cultivo_ana.id,
                "data_inicio": "2026-11-08",
                "sistema_rega": "6",
                "cantidade": 50.0,
            },
        },
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta_ana.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 3

    assert corpo[0]["uuid"] == uuid_1
    assert corpo[0]["estado"] == "creado"
    assert corpo[0]["id"] is not None

    assert corpo[1]["uuid"] == uuid_mal
    assert corpo[1]["estado"] == "erro"
    assert corpo[1]["id"] is None
    assert "non pertence a esta explotación" in corpo[1]["mensaxe"]

    assert corpo[2]["uuid"] == uuid_2
    assert corpo[2]["estado"] == "creado"
    assert corpo[2]["id"] is not None

    # O rexistro correcto 1 existe na base de datos
    assert session.get(ObservacionPraga, corpo[0]["id"]) is not None
    # O que fallou non se gardou
    obs_mal = session.query(ObservacionPraga).filter_by(uuid=uuid_mal).first()
    assert obs_mal is None
    # O rexistro correcto 2 existe na base de datos
    assert session.get(Rega, corpo[2]["id"]) is not None


def test_tarefa_feita_marca_a_tarefa(
    client: TestClient, session: Session
) -> None:
    """tarefa_feita marca a tarefa como feita e garda o uuid."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")
    tarefa = crear_tarefa(
        session,
        ana,
        horta.id,
        "Revisar o valado perimetral",
        data=date(2026, 11, 7),
    )
    assert tarefa.estado == "pendente"

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_tarefa = "88888888-8888-8888-8888-888888888888"
    rexistros = [
        {
            "uuid": uuid_tarefa,
            "tipo": "tarefa_feita",
            "datos": {
                "id": tarefa.id,
                "data": "2026-11-08",
                "horas": 1.5,
            },
        }
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["uuid"] == uuid_tarefa
    assert corpo[0]["estado"] == "creado"
    assert corpo[0]["id"] == tarefa.id

    session.refresh(tarefa)
    assert tarefa.estado == "feito"
    assert tarefa.data_feita == date(2026, 11, 8)
    assert tarefa.horas == 1.5
    assert tarefa.uuid == uuid_tarefa

    # Repetir o envío devolve xa_estaba
    r2 = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert r2.status_code == 200
    c2 = r2.json()
    assert c2[0]["estado"] == "xa_estaba"
    assert c2[0]["id"] == tarefa.id


def test_usuario_lector_da_403(
    client: TestClient, session: Session
) -> None:
    """Un usuario con rol lector recibe un erro 403 para toda a petición."""
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    _, clave_carlos = crear_dispositivo(session, carlos, "Móbil de Carlos")
    headers = {"Authorization": f"Bearer {clave_carlos}"}

    rexistros = [
        {
            "uuid": "99999999-9999-9999-9999-999999999999",
            "tipo": "tarefa_feita",
            "datos": {"id": 1, "data": "2026-11-08"},
        }
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 403


def test_tipo_desconecido_da_erro(
    client: TestClient, session: Session
) -> None:
    """Un tipo de rexistro descoñecido devolve estado erro no elemento."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_raro = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    rexistros = [
        {
            "uuid": uuid_raro,
            "tipo": "tipo_inexistente",
            "datos": {"algo": "calquera"},
        }
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["uuid"] == uuid_raro
    assert corpo[0]["estado"] == "erro"
    assert corpo[0]["id"] is None
    assert "Tipo de rexistro descoñecido" in corpo[0]["mensaxe"]


def test_campo_desconecido_nos_datos_da_erro(
    client: TestClient, session: Session, cultivos_siex: Any
) -> None:
    """Campos non recoñecidos polo servizo dan erro co texto 'Campo descoñecido: ...'."""
    _configurar_catalogos(session)
    cultivos_siex(101)

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")
    parcela = crear_parcela(session, ana, horta.id, "Agra da Cruz")
    cultivo = crear_cultivo(
        session, ana, parcela.id, "Pataca", cultivo_siex_codigo=101, superficie_ha=0.5
    )

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_campo_raro = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    rexistros = [
        {
            "uuid": uuid_campo_raro,
            "tipo": "observacion",
            "datos": {
                "cultivo_id": cultivo.id,
                "data": "2026-11-08",
                "problema_tipo": "praga",
                "problema_codigo": "10",
                "metodo": "trampa",
                "campo_inventado": 123,
            },
        }
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["uuid"] == uuid_campo_raro
    assert corpo[0]["estado"] == "erro"
    assert corpo[0]["id"] is None
    assert "Campo descoñecido: campo_inventado" in corpo[0]["mensaxe"]


def test_labor_e_colleita_creanse_co_uuid(
    client: TestClient, session: Session, cultivos_siex: Any
) -> None:
    """labor e colleita tamén crean os seus rexistros co uuid."""
    _configurar_catalogos(session)
    cultivos_siex(101)

    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta de Ana")
    parcela = crear_parcela(session, ana, horta.id, "Agra da Cruz")
    cultivo = crear_cultivo(
        session, ana, parcela.id, "Pataca", cultivo_siex_codigo=101, superficie_ha=0.5
    )

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    headers = {"Authorization": f"Bearer {clave}"}

    uuid_labor = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    uuid_colleita = "dddddddd-dddd-dddd-dddd-dddddddddddd"

    rexistros = [
        {
            "uuid": uuid_labor,
            "tipo": "labor",
            "datos": {
                "cultivo_id": cultivo.id,
                "data_inicio": "2026-11-08",
                "tipo_labor": "5",
                "superficie_ha": 0.5,
                "horas": 2.0,
            },
        },
        {
            "uuid": uuid_colleita,
            "tipo": "colleita",
            "datos": {
                "cultivo_id": cultivo.id,
                "data": "2026-11-08",
                "cantidade": 500.0,
                "unidade": "kg",
            },
        },
    ]

    resposta = client.post(
        f"/api/campo/explotacions/{horta.id}/rexistros",
        json=rexistros,
        headers=headers,
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 2

    assert corpo[0]["uuid"] == uuid_labor
    assert corpo[0]["estado"] == "creado"
    assert corpo[1]["uuid"] == uuid_colleita
    assert corpo[1]["estado"] == "creado"

    # Verificar na base de datos
    labor_bd = session.get(Labor, corpo[0]["id"])
    assert labor_bd is not None
    assert labor_bd.uuid == uuid_labor
    assert labor_bd.tipo_labor == "5"

    colleita_bd = session.get(Colleita, corpo[1]["id"])
    assert colleita_bd is not None
    assert colleita_bd.uuid == uuid_colleita
    assert colleita_bd.cantidade == 500.0

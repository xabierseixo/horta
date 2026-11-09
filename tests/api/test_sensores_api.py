"""Probas para a API de sensores IoT e importación de CSV (tarefa 183b)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from horta.api.sensores import _ultimos_envios, obter_session, router
from horta.models.horta import RolHorta
from horta.models.sensor import LecturaSensor
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.sensores import (
    baixa_sensor,
    crear_sensor,
    importar_csv,
)


def _crear_usuario(session: Session, email: str, rol: RolGlobal = RolGlobal.USUARIO) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=rol,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session: Session):
    ana = _crear_usuario(session, "ana@example.com")
    pepe = _crear_usuario(session, "pepe@example.com")
    luis = _crear_usuario(session, "luis@example.com")
    alleo = _crear_usuario(session, "alleo@example.com")

    horta = crear_horta(session, ana, "Horta do Val")
    engadir_membro(session, ana, horta.id, pepe, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)
    return ana, pepe, luis, alleo, horta


@pytest.fixture()
def client(session: Session) -> Iterator[TestClient]:
    def _override_session():
        yield session

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[obter_session] = _override_session
    _ultimos_envios.clear()
    with TestClient(app) as test_client:
        yield test_client
    _ultimos_envios.clear()


def test_clave_mala(client: TestClient, session: Session):
    ana, _, _, _, horta = _escenario(session)
    sensor, clave = crear_sensor(session, ana, horta.id, "Sonda Chan", "humidade_chan")

    # Sen cabeceira X-Clave-Sensor
    r_sen = client.post("/api/sensores/lecturas", json={"valor": 23.5})
    assert r_sen.status_code == 401

    # Con cabeceira inventada
    r_mala = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": "clave_inventada_123"},
        json={"valor": 23.5},
    )
    assert r_mala.status_code == 401

    # Cabeceira baleira
    r_baleira = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": "   "},
        json={"valor": 23.5},
    )
    assert r_baleira.status_code == 401

    # Sensor dado de baixa
    baixa_sensor(session, ana, sensor)
    r_baixa = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 23.5},
    )
    assert r_baixa.status_code == 401

    # Endpoint de TTN con clave mala
    r_ttn = client.post(
        "/api/sensores/ttn",
        headers={"X-Clave-Sensor": "clave_mala"},
        json={},
    )
    assert r_ttn.status_code == 401


def test_un_valor_e_unha_lista(client: TestClient, session: Session):
    ana, _, _, _, horta = _escenario(session)
    sensor, clave = crear_sensor(session, ana, horta.id, "Sonda Humidade", "humidade_chan")

    # 1. Un valor único sen momento (asume agora UTC)
    r1 = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 45.2},
    )
    assert r1.status_code == 200
    assert r1.json() == {"gardadas": 1}

    # 2. Un valor con momento explícito
    _ultimos_envios.clear()
    r2 = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 46.0, "momento": "2026-11-01T08:00:00"},
    )
    assert r2.status_code == 200
    assert r2.json() == {"gardadas": 1}

    # 3. Unha lista de lecturas
    _ultimos_envios.clear()
    lista = [
        {"valor": 47.1, "momento": "2026-11-01T08:10:00"},
        {"valor": 47.5, "momento": "2026-11-01T08:20:00"},
    ]
    r3 = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json=lista,
    )
    assert r3.status_code == 200
    assert r3.json() == {"gardadas": 2}

    # Comprobar que hai 4 lecturas rexistradas na base de datos
    total = session.query(LecturaSensor).filter_by(sensor_id=sensor.id).count()
    assert total == 4


def test_fora_de_rango(client: TestClient, session: Session):
    ana, _, _, _, horta = _escenario(session)
    # humidade_chan ten rango [0.0, 100.0]
    sensor, clave = crear_sensor(session, ana, horta.id, "Humidade Chan", "humidade_chan")

    # Valor superior ao máximo (150.0 > 100.0)
    r_alto = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 150.0},
    )
    assert r_alto.status_code == 422
    assert "fóra de rango" in r_alto.json()["detail"].lower()

    # Valor inferior ao mínimo (-5.0 < 0.0)
    _ultimos_envios.clear()
    r_baixo = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": -5.0},
    )
    assert r_baixo.status_code == 422
    assert "fóra de rango" in r_baixo.json()["detail"].lower()

    # Data a máis de 10 minutos no futuro
    _ultimos_envios.clear()
    futuro = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    r_futuro = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 50.0, "momento": futuro},
    )
    assert r_futuro.status_code == 422
    assert "futuro" in r_futuro.json()["detail"].lower()

    # Valor non numérico
    _ultimos_envios.clear()
    r_non_num = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": "abc"},
    )
    assert r_non_num.status_code == 422

    # Lista con máis de 500 elementos
    _ultimos_envios.clear()
    moitos = [{"valor": 50.0} for _ in range(501)]
    r_moitos = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json=moitos,
    )
    assert r_moitos.status_code == 422
    assert "500" in r_moitos.json()["detail"]


def test_limite_429(client: TestClient, session: Session):
    ana, _, _, _, horta = _escenario(session)
    sensor, clave = crear_sensor(session, ana, horta.id, "Sensor Cadencia", "temperatura_aire")

    _ultimos_envios.clear()

    # Primeiro envío: correcto
    r1 = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 20.0},
    )
    assert r1.status_code == 200

    # Segundo envío inmediato (mesmo sensor): rexeitado con 429
    r2 = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 20.5},
    )
    assert r2.status_code == 429
    assert "10 segundos" in r2.json()["detail"]

    # Baleirar o dicionario entre probas permite un novo envío
    _ultimos_envios.clear()
    r3 = client.post(
        "/api/sensores/lecturas",
        headers={"X-Clave-Sensor": clave},
        json={"valor": 21.0},
    )
    assert r3.status_code == 200
    assert r3.json() == {"gardadas": 1}


def test_ttn_correcto_e_sen_campo(client: TestClient, session: Session):
    ana, _, _, _, horta = _escenario(session)
    sensor1, clave1 = crear_sensor(
        session,
        ana,
        horta.id,
        "Sensor LoRaWAN",
        "temperatura_aire",
        campo_payload="temperatura",
    )

    # 1. Mensaxe TTN correcta
    payload_ok = {
        "received_at": "2026-11-01T09:00:00Z",
        "uplink_message": {
            "decoded_payload": {
                "temperatura": 18.5,
                "bateria": 3.7,
            }
        },
    }
    r1 = client.post(
        "/api/sensores/ttn",
        headers={"X-Clave-Sensor": clave1},
        json=payload_ok,
    )
    assert r1.status_code == 200
    assert r1.json() == {"gardadas": 1}

    # 2. Mensaxe TTN sen o campo configurado en decoded_payload
    _ultimos_envios.clear()
    payload_sen_campo = {
        "uplink_message": {
            "decoded_payload": {
                "humidade": 80.0,
            }
        }
    }
    r2 = client.post(
        "/api/sensores/ttn",
        headers={"X-Clave-Sensor": clave1},
        json=payload_sen_campo,
    )
    assert r2.status_code == 422
    assert "temperatura" in r2.json()["detail"]

    # 3. Sensor que non ten campo_payload configurado
    sensor2, clave2 = crear_sensor(
        session,
        ana,
        horta.id,
        "Sensor Sen Campo Payload",
        "choiva",
        campo_payload=None,
    )
    _ultimos_envios.clear()
    r3 = client.post(
        "/api/sensores/ttn",
        headers={"X-Clave-Sensor": clave2},
        json=payload_ok,
    )
    assert r3.status_code == 422
    det = r3.json()["detail"].lower()
    assert "campo_payload" in det or "non ten" in det


def test_csv_coma_decimal_e_data_galega(session: Session):
    ana, pepe, luis, _, horta = _escenario(session)
    sensor, _ = crear_sensor(session, ana, horta.id, "Sonda CSV", "humidade_chan")

    # CSV con ';' e coma decimal e data galega DD/MM/AAAA HH:MM
    csv_1 = (
        "momento;valor\n"
        "01/11/2026 10:00;23,5\n"
        "01/11/2026 10:15;24,1\n"
    ).encode("utf-8")

    gardadas_1 = importar_csv(session, ana, sensor.id, csv_1)
    assert gardadas_1 == 2

    # CSV con ',' e data ISO (usuario EDITOR: pepe)
    csv_2 = (
        "momento,valor\n"
        "2026-11-01 10:30,25.3\n"
    ).encode("utf-8")

    gardadas_2 = importar_csv(session, pepe, sensor.id, csv_2)
    assert gardadas_2 == 1

    # CSV sen cabeceira
    csv_3 = "01/11/2026 10:45;26,8\n".encode("utf-8")
    gardadas_3 = importar_csv(session, ana, sensor.id, csv_3)
    assert gardadas_3 == 1

    # Permisos: usuario LECTOR (luis) non pode importar CSV
    with pytest.raises(PermisoDenegadoError):
        importar_csv(session, luis, sensor.id, csv_3)

    # Verificar que se gardaron as 4 lecturas
    total = session.query(LecturaSensor).filter_by(sensor_id=sensor.id).count()
    assert total == 4


def test_csv_fila_mala(session: Session):
    ana, _, _, _, horta = _escenario(session)
    sensor, _ = crear_sensor(session, ana, horta.id, "Sensor Proba Erros", "humidade_chan")

    # Fila cun valor non numérico
    csv_non_num = (
        "momento;valor\n"
        "01/11/2026 10:00;23,5\n"
        "01/11/2026 10:15;non_numero\n"
    ).encode("utf-8")

    with pytest.raises(OperacionNonPermitidaError) as exc_1:
        importar_csv(session, ana, sensor.id, csv_non_num)
    assert "liña 3" in str(exc_1.value).lower()

    # Fila cunha data non válida
    csv_data_mala = (
        "momento;valor\n"
        "data_inventada;23,5\n"
    ).encode("utf-8")

    with pytest.raises(OperacionNonPermitidaError) as exc_2:
        importar_csv(session, ana, sensor.id, csv_data_mala)
    assert "liña 2" in str(exc_2.value).lower()

    # Fila con valor fóra de rango (150 > 100 para humidade_chan)
    csv_rango = (
        "momento;valor\n"
        "01/11/2026 10:00;23,5\n"
        "01/11/2026 10:15;150,0\n"
    ).encode("utf-8")

    with pytest.raises(OperacionNonPermitidaError) as exc_3:
        importar_csv(session, ana, sensor.id, csv_rango)
    assert "liña 3" in str(exc_3.value).lower()
    assert "fóra de rango" in str(exc_3.value).lower()

    # Fila con momento a máis de 10 minutos no futuro
    csv_futuro = (
        "momento;valor\n"
        "2099-01-01 12:00;50,0\n"
    ).encode("utf-8")

    with pytest.raises(OperacionNonPermitidaError) as exc_4:
        importar_csv(session, ana, sensor.id, csv_futuro)
    assert "liña 2" in str(exc_4.value).lower()
    assert "futuro" in str(exc_4.value).lower()


def test_importar_json(session) -> None:
    """Lista JSON con data galega e coma decimal; elemento sen valor dá erro co número."""
    from horta.services.sensores import crear_sensor, importar_ficheiro

    ana, _, _, _, horta = _escenario(session)
    sensor, _ = crear_sensor(session, ana, horta.id, "Aire", "temperatura_aire")
    contido = b'[{"momento": "01/11/2026 10:00", "valor": "12,5"},' \
              b' {"momento": "2026-11-01T11:00", "valor": 13}]'
    assert importar_ficheiro(session, ana, sensor.id, "lecturas.json", contido) == 2
    with pytest.raises(OperacionNonPermitidaError, match="lectura 2"):
        importar_ficheiro(session, ana, sensor.id, "l.json",
                          b'[{"momento": "2026-11-02T10:00", "valor": 1}, {"momento": "x"}]')

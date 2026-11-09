"""API REST para recepción de lecturas de sensores IoT (HTTP e TTN LoRaWAN).

Rutas dispoñibles baixo o prefixo `/api/sensores`:
- `POST /api/sensores/lecturas`: recepción de lecturas por HTTP desde microcontroladores ou scripts.
- `POST /api/sensores/ttn`: webhook para recibir lecturas desde The Things Network (TTN v3).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Any

from dateutil.parser import isoparse
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.services.errors import OperacionNonPermitidaError
from horta.services.sensores import rexistrar_lecturas, sensor_da_clave

router = APIRouter(prefix="/api/sensores")

# Dicionario en memoria para controlar o límite de peticións (sensor_id -> último envío)
_ultimos_envios: dict[int, datetime] = {}
INTERVALO_MINIMO_SEGUNDOS = 10.0


def obter_session() -> Iterator[Session]:
    """Dependencia que proporciona unha sesión de base de datos."""
    with get_session() as session:
        yield session


def _comprobar_limite(sensor_id: int) -> None:
    """Comproba se se respecta o intervalo mínimo de 10 segundos entre envíos."""
    agora = datetime.now(timezone.utc)
    if sensor_id in _ultimos_envios:
        diferenza = (agora - _ultimos_envios[sensor_id]).total_seconds()
        if diferenza < INTERVALO_MINIMO_SEGUNDOS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Demasiadas peticións: só se permite un envío cada "
                    f"{int(INTERVALO_MINIMO_SEGUNDOS)} segundos"
                ),
            )


def _rexistrar_envio(sensor_id: int) -> None:
    """Actualiza a marca temporal do último envío procesado para o sensor."""
    _ultimos_envios[sensor_id] = datetime.now(timezone.utc)


def _interpretar_momento_api(momento_raw: Any) -> datetime:
    """Interpreta un momento en formato ISO recibido na API."""
    if isinstance(momento_raw, datetime):
        return momento_raw
    if isinstance(momento_raw, str):
        t = momento_raw.strip()
        if not t:
            raise ValueError("O momento non pode ser un texto baleiro")
        try:
            return datetime.fromisoformat(t)
        except ValueError:
            try:
                return isoparse(t)
            except Exception:
                raise ValueError(f"Formato de data e hora non válido: '{t}'")
    raise ValueError("O momento debe ser un texto en formato ISO")


@router.post("/lecturas")
async def recibir_lecturas(
    request: Request,
    session: Session = Depends(obter_session),
    x_clave_sensor: str | None = Header(None, alias="X-Clave-Sensor"),
) -> dict[str, Any]:
    """Recibe lecturas dun sensor enviadas por HTTP directo.

    Admite un obxecto único {"valor": 23.5} ou {"valor": 23.5, "momento": "ISO"},
    ou unha lista deses obxectos ata un máximo de 500.
    """
    if not x_clave_sensor or not x_clave_sensor.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta a cabeceira de autenticación X-Clave-Sensor",
        )

    sensor = sensor_da_clave(session, x_clave_sensor.strip())
    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de sensor non válida ou sensor inactivo",
        )

    _comprobar_limite(sensor.id)

    try:
        corpo = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O corpo da petición debe ser un JSON válido",
        )

    if isinstance(corpo, dict):
        items = [corpo]
    elif isinstance(corpo, list):
        items = corpo
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O corpo debe ser un obxecto JSON ou unha lista de obxectos",
        )

    if len(items) > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Superouse o límite de 500 lecturas por petición",
        )

    lecturas_a_gardar: list[tuple[datetime, float]] = []
    ref_agora = datetime.now(timezone.utc)

    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O elemento {idx} non é un obxecto JSON válido",
            )
        if "valor" not in item or item["valor"] is None or isinstance(item["valor"], bool):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O elemento {idx} non contén un campo 'valor' numérico válido",
            )
        try:
            valor = float(item["valor"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O valor do elemento {idx} non é numérico",
            )

        momento_raw = item.get("momento")
        if momento_raw is not None:
            try:
                momento = _interpretar_momento_api(momento_raw)
            except ValueError as err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Erro no elemento {idx}: {err}",
                )
        else:
            momento = ref_agora

        lecturas_a_gardar.append((momento, valor))

    try:
        gardadas = rexistrar_lecturas(session, sensor, lecturas_a_gardar)
    except (OperacionNonPermitidaError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )

    _rexistrar_envio(sensor.id)
    return {"gardadas": gardadas}


@router.post("/ttn")
async def recibir_ttn(
    request: Request,
    session: Session = Depends(obter_session),
    x_clave_sensor: str | None = Header(None, alias="X-Clave-Sensor"),
) -> dict[str, Any]:
    """Webhook para recibir lecturas desde The Things Network (TTN v3)."""
    if not x_clave_sensor or not x_clave_sensor.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta a cabeceira de autenticación X-Clave-Sensor",
        )

    sensor = sensor_da_clave(session, x_clave_sensor.strip())
    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de sensor non válida ou sensor inactivo",
        )

    _comprobar_limite(sensor.id)

    try:
        corpo = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O corpo da mensaxe TTN debe ser un JSON válido",
        )

    if not isinstance(corpo, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O corpo da mensaxe TTN debe ser un obxecto JSON",
        )

    if not sensor.campo_payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O sensor non ten configurado o campo de payload para TTN",
        )

    uplink = corpo.get("uplink_message")
    if not isinstance(uplink, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Falta o obxecto 'uplink_message' na mensaxe de TTN",
        )

    decoded = uplink.get("decoded_payload")
    if not isinstance(decoded, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Falta o obxecto 'decoded_payload' dentro de 'uplink_message'",
        )

    if sensor.campo_payload not in decoded:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O campo '{sensor.campo_payload}' non vén no payload decodificado",
        )

    valor_raw = decoded[sensor.campo_payload]
    if valor_raw is None or isinstance(valor_raw, bool):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O campo '{sensor.campo_payload}' non contén un valor numérico",
        )

    try:
        valor = float(valor_raw)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O valor do campo '{sensor.campo_payload}' non é numérico",
        )

    ref_agora = datetime.now(timezone.utc)
    received_at_raw = uplink.get("received_at") or corpo.get("received_at")
    if received_at_raw is not None:
        try:
            momento = _interpretar_momento_api(received_at_raw)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Erro no momento da mensaxe TTN: {err}",
            )
    else:
        momento = ref_agora

    try:
        gardadas = rexistrar_lecturas(session, sensor, [(momento, valor)])
    except (OperacionNonPermitidaError, ValueError) as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )

    _rexistrar_envio(sensor.id)
    return {"gardadas": gardadas}

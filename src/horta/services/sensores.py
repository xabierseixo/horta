"""Servizo de xestión de sensores IoT, lecturas e avisos (tarefa 183a)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.instalacion import Instalacion
from horta.models.parcela import Parcela
from horta.models.sensor import LecturaDiaria, LecturaSensor, Sensor
from horta.models.usuario import Usuario
from horta.services.dispositivos import hash_token
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

DIAS_LECTURAS = 90

_SEN_CAMBIO: Any = object()


@dataclass(frozen=True)
class TipoSensor:
    """Configuración e rangos válidos para un tipo de sensor."""

    nome: str
    unidade: str
    minimo: float | None
    maximo: float | None
    acumulado: bool = False


TIPOS_SENSOR: dict[str, TipoSensor] = {
    "humidade_chan": TipoSensor("Humidade do chan", "%", 0.0, 100.0),
    "temperatura_chan": TipoSensor("Temperatura do chan", "°C", -30.0, 70.0),
    "temperatura_aire": TipoSensor("Temperatura do aire", "°C", -40.0, 60.0),
    "humidade_aire": TipoSensor("Humidade do aire", "%", 0.0, 100.0),
    "choiva": TipoSensor("Choiva", "mm", 0.0, 500.0),
    "mollado_folla": TipoSensor("Mollado de folla", "%", 0.0, 100.0),
    "contador_auga": TipoSensor("Contador de auga", "m³", 0.0, 10_000_000.0, acumulado=True),
    "nivel": TipoSensor("Nivel de depósito ou fosa", "%", 0.0, 100.0),
    "temperatura_camara": TipoSensor("Temperatura de cámara ou almacén", "°C", -40.0, 60.0),
    "outro": TipoSensor("Outro", "", None, None),
}


def _comprobar_recursos_horta(
    session: Session,
    horta_id: int,
    parcela_id: int | None,
    cultivo_id: int | None,
    instalacion_id: int | None,
) -> None:
    """Comproba que parcela, cultivo e instalación pertenzan á mesma explotación."""
    if parcela_id is not None:
        parcela = session.get(Parcela, parcela_id)
        if parcela is None or parcela.horta_id != horta_id:
            raise OperacionNonPermitidaError("A parcela non pertence a esta explotación")

    if cultivo_id is not None:
        cultivo = session.get(Cultivo, cultivo_id)
        if cultivo is None:
            raise OperacionNonPermitidaError("O cultivo non existe")
        parcela_c = session.get(Parcela, cultivo.parcela_id)
        if parcela_c is None or parcela_c.horta_id != horta_id:
            raise OperacionNonPermitidaError("O cultivo non pertence a esta explotación")

    if instalacion_id is not None:
        instalacion = session.get(Instalacion, instalacion_id)
        if instalacion is None or instalacion.horta_id != horta_id:
            raise OperacionNonPermitidaError("A instalación non pertence a esta explotación")


def _harmonizar_datetime(dt: datetime, ref: datetime) -> datetime:
    """Axusta dt ao mesmo estado de tzinfo ca ref para poder comparar sen erros."""
    if ref.tzinfo is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    if ref.tzinfo is None and dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _fmt_numero(val: float) -> str:
    """Formata un valor float sen decimais superfluos (ex. 15 en vez de 15.0)."""
    return f"{val:g}"


def crear_sensor(
    session: Session,
    actor: Usuario,
    horta_id: int,
    nome: str,
    tipo: str,
    unidade: str | None = None,
    parcela_id: int | None = None,
    cultivo_id: int | None = None,
    instalacion_id: int | None = None,
    campo_payload: str | None = None,
    limiar_min: float | None = None,
    limiar_max: float | None = None,
) -> tuple[Sensor, str]:
    """Crea un sensor novo, garda o hash da clave e devolve o sensor e a clave en claro."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)

    nome_limpo = (nome or "").strip()
    if not nome_limpo:
        raise OperacionNonPermitidaError("O nome do sensor é obrigatorio")

    if tipo not in TIPOS_SENSOR:
        raise OperacionNonPermitidaError(f"Tipo de sensor non válido: {tipo}")
    tipo_info = TIPOS_SENSOR[tipo]

    unidade_final = (
        unidade.strip() if unidade is not None and unidade.strip() else tipo_info.unidade
    )

    if limiar_min is not None and limiar_max is not None and limiar_min > limiar_max:
        raise OperacionNonPermitidaError("O limiar mínimo non pode ser maior ca o máximo")

    _comprobar_recursos_horta(session, horta_id, parcela_id, cultivo_id, instalacion_id)

    clave = secrets.token_urlsafe(32)
    clave_hash = hash_token(clave)

    sensor = Sensor(
        horta_id=horta_id,
        nome=nome_limpo,
        tipo=tipo,
        unidade=unidade_final,
        parcela_id=parcela_id,
        cultivo_id=cultivo_id,
        instalacion_id=instalacion_id,
        clave_hash=clave_hash,
        campo_payload=campo_payload.strip() if campo_payload and campo_payload.strip() else None,
        limiar_min=limiar_min,
        limiar_max=limiar_max,
        activo=True,
        created_at=datetime.now(timezone.utc),
    )
    session.add(sensor)
    session.commit()
    return sensor, clave


def actualizar_sensor(
    session: Session,
    actor: Usuario,
    sensor: Sensor,
    nome: str | None = _SEN_CAMBIO,
    unidade: str | None = _SEN_CAMBIO,
    parcela_id: int | None = _SEN_CAMBIO,
    cultivo_id: int | None = _SEN_CAMBIO,
    instalacion_id: int | None = _SEN_CAMBIO,
    campo_payload: str | None = _SEN_CAMBIO,
    limiar_min: float | None = _SEN_CAMBIO,
    limiar_max: float | None = _SEN_CAMBIO,
    activo: bool | None = _SEN_CAMBIO,
) -> Sensor:
    """Actualiza os campos permitidos dun sensor existente."""
    comprobar_rol_horta(session, sensor.horta_id, actor, _ROLES_ESCRITURA)
    if not sensor.activo and activo is not True:
        raise OperacionNonPermitidaError("Un sensor dado de baixa non se pode modificar")

    if nome is not _SEN_CAMBIO:
        nome_limpo = (nome or "").strip()
        if not nome_limpo:
            raise OperacionNonPermitidaError("O nome do sensor non pode quedar baleiro")
        sensor.nome = nome_limpo

    if unidade is not _SEN_CAMBIO:
        sensor.unidade = (unidade or "").strip()

    novo_parcela = parcela_id if parcela_id is not _SEN_CAMBIO else sensor.parcela_id
    novo_cultivo = cultivo_id if cultivo_id is not _SEN_CAMBIO else sensor.cultivo_id
    novo_inst = instalacion_id if instalacion_id is not _SEN_CAMBIO else sensor.instalacion_id
    _comprobar_recursos_horta(session, sensor.horta_id, novo_parcela, novo_cultivo, novo_inst)

    if parcela_id is not _SEN_CAMBIO:
        sensor.parcela_id = parcela_id
    if cultivo_id is not _SEN_CAMBIO:
        sensor.cultivo_id = cultivo_id
    if instalacion_id is not _SEN_CAMBIO:
        sensor.instalacion_id = instalacion_id

    if campo_payload is not _SEN_CAMBIO:
        sensor.campo_payload = (
            campo_payload.strip() if campo_payload and campo_payload.strip() else None
        )

    novo_min = limiar_min if limiar_min is not _SEN_CAMBIO else sensor.limiar_min
    novo_max = limiar_max if limiar_max is not _SEN_CAMBIO else sensor.limiar_max
    if novo_min is not None and novo_max is not None and novo_min > novo_max:
        raise OperacionNonPermitidaError("O limiar mínimo non pode ser maior ca o máximo")

    if limiar_min is not _SEN_CAMBIO:
        sensor.limiar_min = limiar_min
    if limiar_max is not _SEN_CAMBIO:
        sensor.limiar_max = limiar_max

    if activo is not _SEN_CAMBIO and activo is not None:
        sensor.activo = activo

    session.commit()
    return sensor


def baixa_sensor(session: Session, actor: Usuario, sensor: Sensor) -> None:
    """Dá de baixa lóxica un sensor."""
    comprobar_rol_horta(session, sensor.horta_id, actor, _ROLES_ESCRITURA)
    sensor.activo = False
    session.commit()


def nova_clave(session: Session, actor: Usuario, sensor_id: int) -> str:
    """Xera unha nova clave aleatoria para o sensor e invalida a anterior."""
    sensor = session.get(Sensor, sensor_id)
    if sensor is None:
        raise OperacionNonPermitidaError("O sensor non existe")
    comprobar_rol_horta(session, sensor.horta_id, actor, _ROLES_ESCRITURA)
    if not sensor.activo:
        raise OperacionNonPermitidaError("Non se pode xerar unha clave para un sensor inactivo")

    clave = secrets.token_urlsafe(32)
    sensor.clave_hash = hash_token(clave)
    session.commit()
    return clave


def listar_sensores(
    session: Session,
    actor: Usuario,
    horta_id: int,
    so_activos: bool = False,
) -> list[Sensor]:
    """Lista os sensores da explotación."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    q = session.query(Sensor).filter_by(horta_id=horta_id)
    if so_activos:
        q = q.filter(Sensor.activo.is_(True))
    return list(q.order_by(Sensor.nome.asc(), Sensor.id.asc()).all())


def sensor_da_clave(session: Session, clave: str) -> Sensor | None:
    """Obtén o sensor correspondente á clave indicada, só se está activo."""
    if not clave:
        return None
    thash = hash_token(clave)
    return session.query(Sensor).filter_by(clave_hash=thash, activo=True).one_or_none()


def compactar(session: Session, sensor: Sensor, hoxe: date) -> None:
    """Pasa a LecturaDiaria as lecturas de hai máis de 90 días e bórraas de lectura_sensor."""
    if sensor.compactado_ata == hoxe:
        return

    limiar_data = hoxe - timedelta(days=DIAS_LECTURAS)
    corte_dt = datetime(limiar_data.year, limiar_data.month, limiar_data.day)

    vellas = (
        session.query(LecturaSensor)
        .filter(LecturaSensor.sensor_id == sensor.id, LecturaSensor.momento < corte_dt)
        .order_by(LecturaSensor.momento.asc())
        .all()
    )

    if vellas:
        por_dia: dict[date, list[float]] = {}
        for lect in vellas:
            por_dia.setdefault(lect.momento.date(), []).append(lect.valor)

        for d, valores in por_dia.items():
            diaria = (
                session.query(LecturaDiaria)
                .filter_by(sensor_id=sensor.id, data=d)
                .one_or_none()
            )
            min_v = float(min(valores))
            max_v = float(max(valores))
            n_v = len(valores)
            media_v = float(sum(valores) / n_v)

            if diaria is None:
                diaria = LecturaDiaria(
                    sensor_id=sensor.id,
                    data=d,
                    minimo=min_v,
                    maximo=max_v,
                    media=media_v,
                    n=n_v,
                )
                session.add(diaria)
            else:
                novo_n = diaria.n + n_v
                diaria.minimo = min(diaria.minimo, min_v)
                diaria.maximo = max(diaria.maximo, max_v)
                diaria.media = (diaria.media * diaria.n + sum(valores)) / novo_n
                diaria.n = novo_n

        for lect in vellas:
            session.delete(lect)

    sensor.compactado_ata = hoxe
    session.commit()


def rexistrar_lecturas(
    session: Session,
    sensor: Sensor,
    lecturas: list[tuple[datetime, float]],
    agora: datetime | None = None,
) -> int:
    """Rexistra lecturas sen actor (a clave xa é o permiso).

    Rexeita momentos a máis de 10 minutos no futuro e valores fóra de rango do tipo.
    Ignora duplicados polo mesmo sensor e momento.
    Actualiza ultima_lectura_en, compacta lecturas vellas e devolve as gardadas.
    """
    if not sensor.activo:
        raise OperacionNonPermitidaError("O sensor non está activo")

    # Todo en UTC sen zona, como garda a app as datas e horas
    ref_agora = _harmonizar_datetime(agora or datetime.now(timezone.utc), datetime.now())
    lecturas = [(_harmonizar_datetime(m, ref_agora), v) for m, v in lecturas]
    limite_futuro = ref_agora + timedelta(minutes=10)
    tipo_info = TIPOS_SENSOR.get(sensor.tipo)

    # 1. Validación previa de tódalas lecturas
    for momento, valor in lecturas:
        m_cmp = _harmonizar_datetime(momento, ref_agora)
        if m_cmp > limite_futuro:
            raise OperacionNonPermitidaError(
                f"O momento da lectura non pode estar máis de 10 minutos no futuro: {momento}"
            )
        if tipo_info is not None:
            if tipo_info.minimo is not None and valor < tipo_info.minimo:
                raise OperacionNonPermitidaError(
                    f"Valor {valor} fóra de rango para {sensor.tipo} (mínimo: {tipo_info.minimo})"
                )
            if tipo_info.maximo is not None and valor > tipo_info.maximo:
                raise OperacionNonPermitidaError(
                    f"Valor {valor} fóra de rango para {sensor.tipo} (máximo: {tipo_info.maximo})"
                )

    if not lecturas:
        compactar(session, sensor, ref_agora.date())
        return 0

    # 2. Rexistro ignorando duplicados
    momentos = [m for m, _ in lecturas]
    existentes = {
        row[0]
        for row in session.query(LecturaSensor.momento)
        .filter(LecturaSensor.sensor_id == sensor.id, LecturaSensor.momento.in_(momentos))
        .all()
    }

    gardadas = 0
    vistos: set[datetime] = set(existentes)
    max_momento: datetime | None = None

    for momento, valor in lecturas:
        if momento in vistos:
            continue
        vistos.add(momento)
        lect = LecturaSensor(sensor_id=sensor.id, momento=momento, valor=float(valor))
        session.add(lect)
        gardadas += 1
        if max_momento is None or momento > max_momento:
            max_momento = momento

    if max_momento is not None:
        if sensor.ultima_lectura_en is None or max_momento > sensor.ultima_lectura_en:
            sensor.ultima_lectura_en = max_momento

    compactar(session, sensor, ref_agora.date())
    session.commit()
    return gardadas


def lecturas(
    session: Session,
    actor: Usuario,
    sensor_id: int,
    desde: datetime,
    ata: datetime,
) -> list[tuple[datetime, float]]:
    """Devolve as lecturas cruas e diarias (ás 12:00) do período, ordenadas por momento."""
    sensor = session.get(Sensor, sensor_id)
    if sensor is None:
        raise OperacionNonPermitidaError("O sensor non existe")
    comprobar_rol_horta(session, sensor.horta_id, actor, _ROLES_LECTURA)

    resultado: list[tuple[datetime, float]] = []

    cruas = (
        session.query(LecturaSensor)
        .filter(
            LecturaSensor.sensor_id == sensor_id,
            LecturaSensor.momento >= desde,
            LecturaSensor.momento <= ata,
        )
        .all()
    )
    for c in cruas:
        resultado.append((c.momento, c.valor))

    desde_data = desde.date()
    ata_data = ata.date()
    diarias = (
        session.query(LecturaDiaria)
        .filter(
            LecturaDiaria.sensor_id == sensor_id,
            LecturaDiaria.data >= desde_data,
            LecturaDiaria.data <= ata_data,
        )
        .all()
    )
    for d in diarias:
        momento_d = datetime(d.data.year, d.data.month, d.data.day, 12, 0)
        momento_cmp = _harmonizar_datetime(momento_d, desde)
        if desde <= momento_cmp <= ata:
            resultado.append((momento_cmp, d.media))

    resultado.sort(key=lambda item: _harmonizar_datetime(item[0], desde))
    return resultado


def ultima_lectura(
    session: Session,
    actor: Usuario,
    sensor_id: int,
) -> tuple[datetime, float] | None:
    """Obtén o momento e valor da última lectura do sensor (crua ou compactada)."""
    sensor = session.get(Sensor, sensor_id)
    if sensor is None:
        raise OperacionNonPermitidaError("O sensor non existe")
    comprobar_rol_horta(session, sensor.horta_id, actor, _ROLES_LECTURA)

    ult_crua = (
        session.query(LecturaSensor)
        .filter_by(sensor_id=sensor_id)
        .order_by(LecturaSensor.momento.desc())
        .first()
    )
    ult_diaria = (
        session.query(LecturaDiaria)
        .filter_by(sensor_id=sensor_id)
        .order_by(LecturaDiaria.data.desc())
        .first()
    )

    if ult_crua is None and ult_diaria is None:
        return None
    if ult_crua is not None and ult_diaria is None:
        return (ult_crua.momento, ult_crua.valor)
    if ult_crua is None and ult_diaria is not None:
        m_d = datetime(ult_diaria.data.year, ult_diaria.data.month, ult_diaria.data.day, 12, 0)
        return (m_d, ult_diaria.media)

    assert ult_crua is not None and ult_diaria is not None
    m_d = datetime(ult_diaria.data.year, ult_diaria.data.month, ult_diaria.data.day, 12, 0)
    m_d_cmp = _harmonizar_datetime(m_d, ult_crua.momento)
    if ult_crua.momento >= m_d_cmp:
        return (ult_crua.momento, ult_crua.valor)
    return (m_d, ult_diaria.media)


def consumo_periodo(
    session: Session,
    actor: Usuario,
    sensor_id: int,
    desde: datetime,
    ata: datetime,
) -> float | None:
    """Para sensores acumulados, a diferenza entre a última e a primeira lectura do período."""
    sensor = session.get(Sensor, sensor_id)
    if sensor is None:
        raise OperacionNonPermitidaError("O sensor non existe")
    comprobar_rol_horta(session, sensor.horta_id, actor, _ROLES_LECTURA)

    tipo_info = TIPOS_SENSOR.get(sensor.tipo)
    if tipo_info is None or not tipo_info.acumulado:
        return None

    lista = lecturas(session, actor, sensor_id, desde, ata)
    if not lista:
        return None

    primeira = lista[0][1]
    ultima = lista[-1][1]
    return float(ultima - primeira)


def avisos_sensores(
    session: Session,
    actor: Usuario,
    horta_id: int,
    agora: datetime | None = None,
) -> list[str]:
    """Avisos de sensores para a páxina de Inicio.

    - «<nome>: <valor> <unidade>, por debaixo do límite (<min>)» ou «por riba do límite (<max>)»;
    - «<nome>: sen datos desde DD/MM HH:MM» se a última lectura ten máis de 24 h.
    """
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)

    ref_agora = agora or datetime.now(timezone.utc)
    sensores = (
        session.query(Sensor)
        .filter_by(horta_id=horta_id, activo=True)
        .order_by(Sensor.nome.asc())
        .all()
    )

    avisos: list[str] = []
    for s in sensores:
        ult = (
            session.query(LecturaSensor)
            .filter_by(sensor_id=s.id)
            .order_by(LecturaSensor.momento.desc())
            .first()
        )
        if ult is None:
            continue

        u_str = f" {s.unidade}" if s.unidade else ""
        if s.limiar_min is not None and ult.valor < s.limiar_min:
            val_u = f"{_fmt_numero(ult.valor)}{u_str}".strip()
            min_str = _fmt_numero(s.limiar_min)
            avisos.append(f"{s.nome}: {val_u}, por debaixo do límite ({min_str})")
        elif s.limiar_max is not None and ult.valor > s.limiar_max:
            val_u = f"{_fmt_numero(ult.valor)}{u_str}".strip()
            max_str = _fmt_numero(s.limiar_max)
            avisos.append(f"{s.nome}: {val_u}, por riba do límite ({max_str})")

        m_cmp = _harmonizar_datetime(ult.momento, ref_agora)
        if ref_agora - m_cmp > timedelta(hours=24):
            data_fmt = ult.momento.strftime("%d/%m %H:%M")
            avisos.append(f"{s.nome}: sen datos desde {data_fmt}")

    return avisos

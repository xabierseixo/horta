"""Textos para amosar as necesidades de rega (método FAO-56 / SiAR)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from horta.idiomas import _
from horta.models.cultivo import Cultivo
from horta.models.sensor import Sensor
from horta.models.usuario import Usuario
from horta.services.necesidades_rega import NecesidadeRega
from horta.services.sensores import ultima_lectura
from horta.ui.numeros import formatar_decimal


def texto_humidade_chan(nome_sensor: str, valor: float) -> str:
    """Texto para a lectura actual de humidade do chan dun sensor."""
    return _("Humidade do chan agora: {valor:g} % (sensor {sensor})").format(
        valor=valor, sensor=nome_sensor
    )


def buscar_humidade_chan(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    parcela_id: int | None = None,
) -> tuple[str, float] | None:
    """Busca o sensor humidade_chan do cultivo ou da súa parcela e a súa última lectura."""
    sensor = (
        session.query(Sensor)
        .filter_by(cultivo_id=cultivo_id, tipo="humidade_chan", activo=True)
        .first()
    )
    if sensor is None:
        p_id = parcela_id
        if p_id is None:
            c = session.get(Cultivo, cultivo_id)
            if c is not None:
                p_id = c.parcela_id
        if p_id is not None:
            sensor = (
                session.query(Sensor)
                .filter_by(parcela_id=p_id, tipo="humidade_chan", activo=True)
                .first()
            )
    if sensor is None:
        return None

    ult = ultima_lectura(session, actor, sensor.id)
    if ult is None:
        return None
    _x, valor = ult
    return (sensor.nome, valor)


def texto_necesidade(
    n: NecesidadeRega,
    humidade_chan: float | tuple[str, float] | None = None,
    nome_sensor: str | None = None,
) -> str:
    """Devolve a explicación en texto das necesidades de rega calculadas para un cultivo."""
    if n.estado == "ok":
        falta = formatar_decimal(round(n.falta_mm, 1))
        etc = formatar_decimal(round(n.etc_mm, 1))
        choiva = formatar_decimal(round(n.choiva_efectiva_mm, 1))
        rega = formatar_decimal(round(n.rega_mm, 1))
        if n.falta_mm > 0:
            texto = _(
                "Faltan uns {falta} l/m² (gastou {etc}, choveu {choiva} útiles, regouse {rega})"
            ).format(falta=falta, etc=etc, choiva=choiva, rega=rega)
        else:
            texto = _(
                "Non fai falta regar (gastou {etc} l/m², choveu {choiva} útiles, regouse {rega})"
            ).format(etc=etc, choiva=choiva, rega=rega)
        if n.et0_estimada:
            texto += _(
                " · aproximado: a estación non mide a evapotranspiración "
                "e calcúlase coa temperatura (FAO-56)"
            )
        elif n.aproximado:
            texto += _(" · cálculo aproximado")
    elif n.estado == "secano":
        texto = _("Cultivo de secano")
    elif n.estado == "sen_coeficiente":
        texto = _("Non hai coeficiente oficial para este cultivo")
    elif n.estado == "sen_estacion":
        texto = _("Nin a parcela nin a explotación teñen estación de MeteoGalicia")
    elif n.estado == "sen_data_inicio":
        texto = _("Falta a data de sementeira ou plantación")
    elif n.estado == "sen_datos":
        texto = _("A estación non ten datos de temperatura nin evapotranspiración destes días")
    else:
        texto = ""

    if humidade_chan is not None:
        if isinstance(humidade_chan, tuple):
            s_nome, s_val = humidade_chan
        else:
            s_nome = nome_sensor or ""
            s_val = humidade_chan
        txt_h = texto_humidade_chan(s_nome, s_val)
        if texto:
            texto = f"{texto} · {txt_h}"
        else:
            texto = txt_h

    return texto

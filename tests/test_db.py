from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from horta.db import engine

SENSIBLE = "$2b$12$SEGREDO-QUE-NON-DEBE-APARECER-NOS-LOGS"


def test_engine_oculta_parametros() -> None:
    """O motor real da app debe agochar os parámetros SQL en erros/logs.

    Isto evita que valores sensibles (p.ex. o hash de contrasinal) aparezan
    en `str(excepcion)` cando un erro de BD non-IntegrityError chega a un
    `logger.exception(...)` (ver executar_accion e manexador_500).
    """
    assert engine.hide_parameters is True


def test_erro_sql_non_integrity_non_expon_parametro_sensible() -> None:
    """Un OperationalError (non capturado especificamente coma IntegrityError)
    non debe conter o valor dos parámetros vinculados na súa representación
    en texto, grazas a hide_parameters=True.
    """
    motor = create_engine("sqlite:///:memory:", hide_parameters=True)
    with motor.connect() as conexion:
        conexion.execute(text("CREATE TABLE proba (id INTEGER PRIMARY KEY, valor TEXT NOT NULL)"))
        try:
            conexion.execute(
                text(
                    "INSERT INTO proba (id, valor, columna_inexistente) "
                    "VALUES (:id, :valor, :valor)"
                ),
                {"id": 1, "valor": SENSIBLE},
            )
        except OperationalError as erro:
            assert SENSIBLE not in str(erro)
        else:
            raise AssertionError("Esperábase un OperationalError")

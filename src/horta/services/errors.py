from __future__ import annotations


class PermisoDenegadoError(Exception):
    """O usuario que executa a acción non ten permiso suficiente."""


class OperacionNonPermitidaError(ValueError):
    """A operación deixaría os datos nun estado non válido.

    Por exemplo: unha horta sen ningún administrador, ou un administrador
    desactivando a súa propia conta.
    """

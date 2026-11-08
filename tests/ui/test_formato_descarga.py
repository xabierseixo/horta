"""Proba de importación de horta.ui.formato_descarga."""

from __future__ import annotations

import horta.ui.formato_descarga
from horta.ui.formato_descarga import descargar_informe, selector_formato


def test_importar_formato_descarga() -> None:
    assert horta.ui.formato_descarga is not None
    assert callable(selector_formato)
    assert callable(descargar_informe)

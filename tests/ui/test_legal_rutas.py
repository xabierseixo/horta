"""Probas para a lóxica de rutas públicas e petición de aceptación da política."""

from __future__ import annotations

from horta.main import ruta_e_publica, ruta_pide_aceptacion


def test_rutas_publicas_sen_sesion() -> None:
    assert ruta_e_publica("/login") is True
    assert ruta_e_publica("/convite/abc-123") is True
    assert ruta_e_publica("/lote/xyz-789") is True
    assert ruta_e_publica("/legal/aviso") is True
    assert ruta_e_publica("/legal/privacidade") is True


def test_rutas_privadas_non_son_publicas() -> None:
    assert ruta_e_publica("/") is False
    assert ruta_e_publica("/conta") is False
    assert ruta_e_publica("/admin/legal") is False
    assert ruta_e_publica("/admin/copias") is False
    assert ruta_e_publica("/legal/aceptar") is False


def test_ruta_pide_aceptacion_en_rutas_rexistradas() -> None:
    assert ruta_pide_aceptacion("/", True) is True
    assert ruta_pide_aceptacion("/conta", True) is True
    assert ruta_pide_aceptacion("/admin/legal", True) is True
    assert ruta_pide_aceptacion("/hortas/1/resumo", True) is True


def test_ruta_non_pide_aceptacion_en_rutas_especiais() -> None:
    # Login e rutas baixo /legal/ non deben redirixir a /legal/aceptar
    assert ruta_pide_aceptacion("/login", True) is False
    assert ruta_pide_aceptacion("/legal/aceptar", True) is False
    assert ruta_pide_aceptacion("/legal/aviso", True) is False
    assert ruta_pide_aceptacion("/legal/privacidade", True) is False


def test_ruta_non_rexistrada_non_pide_aceptacion() -> None:
    # Recursos estáticos, fotos, teselas non deben disparar comprobación na BD
    assert ruta_pide_aceptacion("/fotos/1", False) is False
    assert ruta_pide_aceptacion("/teselas/pnoa/1/2/3", False) is False
    assert ruta_pide_aceptacion("/_nicegui/client", False) is False

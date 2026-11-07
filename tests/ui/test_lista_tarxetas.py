"""Probas para o compoñente común lista_tarxetas."""

from __future__ import annotations

from horta.ui.lista_tarxetas import lista_tarxetas


def test_importar_lista_tarxetas() -> None:
    """Comproba que lista_tarxetas existe e é un callable."""
    assert callable(lista_tarxetas)


def test_lista_tarxetas_sen_elementos() -> None:
    """Se non hai elementos, non debuxa nada nin falla ao chamala."""
    lista_tarxetas([], lambda _id: None)

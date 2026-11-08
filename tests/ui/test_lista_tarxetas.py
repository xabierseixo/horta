"""Probas para o compoñente común lista_tarxetas."""

from __future__ import annotations

from horta.ui.lista_tarxetas import datos_da_fila, lista_tarxetas, tarxetas_da_taboa


def test_importar_lista_tarxetas() -> None:
    """Comproba que lista_tarxetas existe e é un callable."""
    assert callable(lista_tarxetas)


def test_importar_tarxetas_da_taboa() -> None:
    """Comproba que tarxetas_da_taboa existe e é un callable."""
    assert callable(tarxetas_da_taboa)


def test_importar_datos_da_fila() -> None:
    """Comproba que datos_da_fila existe e é un callable."""
    assert callable(datos_da_fila)


def test_lista_tarxetas_sen_elementos() -> None:
    """Se non hai elementos, non debuxa nada nin falla ao chamala."""
    lista_tarxetas([], lambda _id: None)


def test_datos_da_fila_con_valores() -> None:
    """Comproba que devolve todas as columnas cando teñen valores válidos."""
    columnas = [
        {"name": "data", "label": "Data", "field": "data"},
        {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
        {"name": "auga", "label": "Auga", "field": "auga"},
    ]
    fila = {"data": "08/11/2026", "cultivo": "Tomates", "auga": "500 l"}
    assert datos_da_fila(columnas, fila) == [
        ("Data", "08/11/2026"),
        ("Cultivo", "Tomates"),
        ("Auga", "500 l"),
    ]


def test_datos_da_fila_con_baleiros_e_none() -> None:
    """Comproba que se omiten os campos baleiros (cadea baleira) e con None."""
    columnas = [
        {"name": "data", "label": "Data", "field": "data"},
        {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
        {"name": "sistema", "label": "Sistema", "field": "sistema"},
        {"name": "auga", "label": "Auga", "field": "auga"},
    ]
    fila = {"data": "08/11/2026", "cultivo": "", "sistema": None, "auga": "300 l"}
    assert datos_da_fila(columnas, fila) == [
        ("Data", "08/11/2026"),
        ("Auga", "300 l"),
    ]


def test_datos_da_fila_orde_das_columnas() -> None:
    """Comproba que o resultado respecta a orde das columnas da táboa."""
    columnas = [
        {"name": "auga", "label": "Auga", "field": "auga"},
        {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
        {"name": "data", "label": "Data", "field": "data"},
    ]
    fila = {"data": "08/11/2026", "cultivo": "Leitugas", "auga": "100 l"}
    assert datos_da_fila(columnas, fila) == [
        ("Auga", "100 l"),
        ("Cultivo", "Leitugas"),
        ("Data", "08/11/2026"),
    ]

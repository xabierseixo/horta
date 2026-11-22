from horta.ui.filtros import filtrar_filas

_FILAS = [
    {"nome": "Parcela do Alto", "estado": "activa"},
    {"nome": "Parcela do Río", "estado": "inactiva"},
    {"nome": "Horta Vella", "estado": "activa"},
]


def test_filtrar_filas_texto_baleiro_devolve_todo():
    assert filtrar_filas(_FILAS, "", ["nome"]) == _FILAS


def test_filtrar_filas_busca_por_subcadea_sen_distinguir_maiusculas():
    resultado = filtrar_filas(_FILAS, "ALTO", ["nome"])
    assert resultado == [_FILAS[0]]


def test_filtrar_filas_busca_sen_coincidencias():
    assert filtrar_filas(_FILAS, "inexistente", ["nome"]) == []


def test_filtrar_filas_so_filtro_estruturado():
    resultado = filtrar_filas(_FILAS, "", ["nome"], {"estado": "activa"})
    assert resultado == [_FILAS[0], _FILAS[2]]


def test_filtrar_filas_texto_e_filtro_combinados():
    resultado = filtrar_filas(_FILAS, "horta", ["nome"], {"estado": "activa"})
    assert resultado == [_FILAS[2]]


def test_filtrar_filas_sentinela_todos_non_filtra():
    assert filtrar_filas(_FILAS, "", ["nome"], {"estado": None}) == _FILAS
    assert filtrar_filas(_FILAS, "", ["nome"], {"estado": ""}) == _FILAS


def test_filtrar_filas_non_normaliza_acentos():
    # Límite coñecido e aceptado: buscar sen til non atopa "Río".
    assert filtrar_filas(_FILAS, "rio", ["nome"]) == []


def test_filtrar_filas_lista_baleira_devolve_baleira():
    assert filtrar_filas([], "alto", ["nome"]) == []


def test_filtrar_filas_sen_campos_busca_non_atopa_nada():
    assert filtrar_filas(_FILAS, "alto", []) == []


def test_filtrar_filas_fila_sen_campo_buscado_non_falla():
    filas = [{"nome": "Parcela do Alto", "estado": "activa"}, {"estado": "activa"}]
    assert filtrar_filas(filas, "alto", ["nome"]) == [filas[0]]

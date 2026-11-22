import zipfile

from openpyxl import Workbook

from horta.models.catalogo import CatalogoValor, CultivoSiex, VariedadeSiex
from horta.services.catalogos_ficheiros import (
    expandir,
    identificar_catalogo,
    revisar,
    sen_catalogos,
)


def _xlsx(ruta, folla, cabeceira, filas):
    libro = Workbook()
    ws = libro.active
    ws.title = folla
    ws.append(cabeceira)
    for fila in filas:
        ws.append(fila)
    libro.save(ruta)
    return ruta


def _pragas(ruta, codigos, folla="Artrópodos y gasterópodos"):
    return _xlsx(ruta, folla, ["Código SIEX", "Nombre científico"],
                 [[str(c), f"Especie {c}"] for c in codigos])


def test_identifica_portal_zip_e_titulo_da_folla(tmp_path):
    assert identificar_catalogo(_pragas(tmp_path / "PLAGAS.xlsx", [1])) == "praga"
    assert identificar_catalogo(
        _xlsx(tmp_path / "20260311 Actividad agraria.xlsx", "Datos", ["Código SIEX"], [])
    ) == "actividade_agraria"
    assert identificar_catalogo(
        _xlsx(tmp_path / "20260508_CULTIVO_INTEGRADO SI.xlsx", "Hoja1", ["Código"], [])
    ) == "cultivo"
    # Nome calquera do navegador: recoñécese polo título da folla (cortado a 31 caracteres)
    assert identificar_catalogo(_pragas(tmp_path / "descarga (3).xlsx", [1])) == "praga"
    assert identificar_catalogo(
        _xlsx(tmp_path / "x.xlsx", "Certificación producción ecoló", ["Código SIEX"], [])
    ) == "certificacion_ecoloxica"
    assert identificar_catalogo(
        _xlsx(tmp_path / "Tipo de titular.xlsx", "Datos", ["Código SIEX"], [])) is None


def test_revisar_non_garda_e_aplicar_si(session, tmp_path):
    ficheiro = _pragas(tmp_path / "PLAGAS.xlsx", [1, 2])
    [revision] = revisar(session, [ficheiro])
    assert (revision.catalogo, revision.informe.altas) == ("praga", 2)
    assert session.query(CatalogoValor).count() == 0
    assert sen_catalogos(session)
    revisar(session, [ficheiro], aplicar=True)
    assert session.query(CatalogoValor).count() == 2
    assert not sen_catalogos(session)


def test_formato_novo_non_importa_nada(session, tmp_path):
    ficheiro = _xlsx(tmp_path / "PLAGAS.xlsx", "Artrópodos y gasterópodos",
                     ["Codigo", "Nombre científico"], [["1", "x"]])
    [revision] = revisar(session, [ficheiro], aplicar=True)
    assert "fáltalle a columna «Código SIEX»" in revision.erro
    assert "hai que adaptar a app" in revision.erro
    assert session.query(CatalogoValor).count() == 0


def test_moitas_baixas_marcanse_como_sospeitosas(session, tmp_path):
    revisar(session, [_pragas(tmp_path / "PLAGAS.xlsx", range(1, 21))], aplicar=True)
    [revision] = revisar(session, [_pragas(tmp_path / "PLAGAS.xlsx", [1, 2])])
    assert revision.informe.baixas == 18 and revision.informe.sospeitoso
    [revision] = revisar(session, [_pragas(tmp_path / "PLAGAS.xlsx", range(1, 20))])
    assert revision.informe.baixas == 1 and not revision.informe.sospeitoso


def test_cultivos_e_variedades_no_mesmo_lote(session, tmp_path):
    cultivos = _xlsx(tmp_path / "PRODUCTOS.xlsx", "Cultivo", ["Código", "Cultivo"],
                     [[99, "PATATA"]])
    variedades = _xlsx(tmp_path / "VARIEDAD_ESPECIE_TIPO.xlsx", "Variedad  Especie  Tipo",
                       ["Código cultivo", "Código Variedad/ Especie/ Tipo",
                        "Variedad/ Especie/ Tipo"], [[99, 1, "KENNEBEC"]])
    revisions = revisar(session, [variedades, cultivos])
    assert [(r.catalogo, r.erro, r.informe.altas) for r in revisions] == [
        ("cultivo", None, 1), ("variedade", None, 1)]
    assert session.query(CultivoSiex).count() == 0
    revisar(session, [variedades, cultivos], aplicar=True)
    assert session.query(VariedadeSiex).one().nome_oficial == "KENNEBEC"


def test_ficheiro_que_non_e_catalogo(session, tmp_path):
    [revision] = revisar(session, [_xlsx(tmp_path / "notas.xlsx", "Folla1", ["a"], [])])
    assert revision.catalogo is None and "Non é un catálogo" in revision.erro


def test_expandir_zip(tmp_path):
    pragas = _pragas(tmp_path / "PLAGAS.xlsx", [1])
    with zipfile.ZipFile(tmp_path / "c.zip", "w") as z:
        z.write(pragas, "Catálogos 2026/PLAGAS.xlsx")
        z.writestr("Catálogos 2026/leme.txt", "x")
    destino = tmp_path / "saida"
    destino.mkdir()
    assert [p.name for p in expandir([tmp_path / "c.zip"], destino)] == ["PLAGAS.xlsx"]

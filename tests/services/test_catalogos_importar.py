from datetime import date
from pathlib import Path

from openpyxl import Workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex
from horta.services.catalogos_importar import (
    importar_catalogo,
    importar_cultivos,
    importar_variedades,
)

_CAB_PRAGAS = ["Código SIEX", "Código", "Categoría", "Nombre científico", "EPPO cd",
               "Observaciones", "Fecha de alta", "Fecha de modificación", "Fecha de baja"]


def _xlsx(ruta: Path, cabeceira: list[str], filas: list[list]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.append(cabeceira)
    for fila in filas:
        ws.append(fila)
    wb.save(ruta)
    return ruta


def test_importa_altas_con_eppo_e_categoria(session, tmp_path):
    f = _xlsx(tmp_path / "PLAGAS.xlsx", _CAB_PRAGAS, [
        ["1", "6", "Artrópodos", "Arthropoda", "1ARTHP", "", "30/06/2023", None, None],
        ["2", "7", "Insectos", "Insecta", "1INSEC", "", "30/06/2023", None, None],
    ])
    informe = importar_catalogo(session, "praga", f)
    assert (informe.altas, informe.baixas, informe.cambios) == (2, 0, 0)
    valor = session.query(CatalogoValor).filter_by(catalogo="praga", codigo="1").one()
    assert valor.descricion == "Arthropoda"
    assert valor.codigo_eppo == "1ARTHP"
    assert valor.categoria == "Artrópodos"
    assert valor.data_alta == date(2023, 6, 30)


def test_mesmo_ficheiro_dúas_veces_non_cambia_nada(session, tmp_path):
    f = _xlsx(tmp_path / "PLAGAS.xlsx", _CAB_PRAGAS,
              [["1", "6", "Artrópodos", "Arthropoda", "1ARTHP", "", None, None, None]])
    importar_catalogo(session, "praga", f)
    informe = importar_catalogo(session, "praga", f)
    assert informe.xa_importado is True
    assert session.query(CatalogoVersion).count() == 1


def test_codigo_que_desaparece_queda_de_baixa_non_se_borra(session, tmp_path):
    f1 = _xlsx(tmp_path / "v1.xlsx", _CAB_PRAGAS, [
        ["1", "6", "Artrópodos", "Arthropoda", "1ARTHP", "", None, None, None],
        ["2", "7", "Insectos", "Insecta", "1INSEC", "", None, None, None],
    ])
    importar_catalogo(session, "praga", f1)
    f2 = _xlsx(tmp_path / "v2.xlsx", _CAB_PRAGAS, [
        ["1", "6", "Artrópodos", "Arthropoda nova", "1ARTHP", "", None, None, None],
    ])
    informe = importar_catalogo(session, "praga", f2, hoxe=date(2026, 11, 1))
    assert (informe.altas, informe.baixas, informe.cambios) == (0, 1, 1)
    dous = session.query(CatalogoValor).filter_by(catalogo="praga", codigo="2").one()
    assert dous.data_baixa == date(2026, 11, 1)
    assert session.query(CatalogoValor).filter_by(catalogo="praga").count() == 2


def test_baixa_oficial_do_ficheiro(session, tmp_path):
    f = _xlsx(tmp_path / "PLAGAS.xlsx", _CAB_PRAGAS,
              [["1", "6", "A", "Arthropoda", "", "", None, None, "15/03/2025"]])
    importar_catalogo(session, "praga", f)
    valor = session.query(CatalogoValor).one()
    assert valor.data_baixa == date(2025, 3, 15)


def test_catalogo_con_columna_de_descricion_por_defecto(session, tmp_path):
    f = _xlsx(tmp_path / "UNIDADES_MEDIDA.xlsx",
              ["Código SIEX", "Unidades de medida", "Fecha de alta", "Fecha de modificación",
               "Fecha de baja"],
              [["1", "m2", "20/09/2023", None, None]])
    importar_catalogo(session, "unidade_medida", f)
    assert session.query(CatalogoValor).one().descricion == "m2"


def test_catalogo_con_outra_columna_de_codigo(session, tmp_path):
    f = _xlsx(tmp_path / "TIPO_MAQUINA_UNE.xlsx", ["Código UNE", "Descripción"],
              [["0000000_88", "Máquinas sin clasificar"]])
    importar_catalogo(session, "tipo_maquinaria_une", f)
    assert session.query(CatalogoValor).one().codigo == "0000000_88"


def test_importa_cultivos_e_variedades(session, tmp_path):
    fc = _xlsx(tmp_path / "PRODUCTOS.xlsx",
               ["Código", "Cultivo", "Latín", "EPPO", "C. UPOV", "Hortícola", "Integrado",
                "Fecha de alta", "Fecha de modificación", "Fecha de baja"],
               [["99", "PATATA", "Solanum tuberosum", "SOLTU", "SOLAN_TUB", "SI", "SI",
                 "30/06/2023", None, None]])
    importar_cultivos(session, fc)
    pataca = session.get(CultivoSiex, 99)
    assert pataca is not None and pataca.codigo_eppo == "SOLTU" and pataca.horticola is True
    fv = _xlsx(tmp_path / "VARIEDAD_ESPECIE_TIPO.xlsx",
               ["Código cultivo", "Cultivo", "Latín", "EPPO", "C. UPOV",
                "Código Variedad/ Especie/ Tipo", "Variedad/ Especie/ Tipo",
                "Admisible Ayudas Asociadas", "Vinificable", "Integrado", "Fecha de alta",
                "Fecha de modificación", "Fecha de baja"],
               [["99", "PATATA", "", "", "", "0", "SIN VARIEDAD", "NO", "NO", "SI", None, None,
                 None],
                ["99", "PATATA", "", "", "", "12", "KENNEBEC", "NO", "NO", "SI", None, None,
                 None]])
    informe = importar_variedades(session, fv)
    assert informe.altas == 2
    assert session.query(VariedadeSiex).filter_by(cultivo_codigo=99, codigo=12).one() \
        .nome_oficial == "KENNEBEC"


def test_variedades_sen_cultivos_non_queda_marcado_como_importado(session, tmp_path):
    import pytest

    from horta.services.errors import OperacionNonPermitidaError

    fv = _xlsx(tmp_path / "VARIEDAD_ESPECIE_TIPO.xlsx",
               ["Código cultivo", "Código Variedad/ Especie/ Tipo", "Variedad/ Especie/ Tipo",
                "Fecha de baja"],
               [["99", "12", "KENNEBEC", None]])
    with pytest.raises(OperacionNonPermitidaError, match="Importa primeiro os cultivos"):
        importar_variedades(session, fv)
    assert session.query(CatalogoVersion).count() == 0

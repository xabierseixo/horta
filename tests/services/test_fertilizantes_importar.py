from datetime import date
from pathlib import Path

from openpyxl import Workbook

import horta.models  # noqa: F401
from horta.models.fertilizante import FertilizanteSiex
from horta.services.fertilizantes_importar import importar_fertilizantes

_CAB = ["Código SIEX", "Tipo material fertilizantes según lista SIEX", "C_FERTILIZANTE",
        "D_CLASIFICA_NIVEL1", "D_CLASIFICA_NIVEL2", "Nombre producto", "Fabricante",
        "D_FERTILIZANTE_2", "N_% TOTAL", "P2O5 % total", "K2O % total",
        "¿Inhibidor de la nitrificación? Si/No", "¿Inhibidor de la ureasa? Si/No",
        "Estado de agregación", "Densidad (g/cm3)"]


def _xlsx(ruta: Path, filas: list[list]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.append(_CAB)
    for fila in filas:
        ws.append(fila)
    wb.save(ruta)
    return ruta


def _fila(codigo: str, nome: str, n: str, liquido: str = "Sólido") -> list:
    return ["14", "Productos fertilizantes: abonos inorgánicos", codigo, "Simple",
            "NITROGENADO", nome, "GENÉRICO", f"{nome} de GENÉRICO", n, "0", "0", "NO", "SI",
            liquido, "1.41" if liquido == "Líquido" else "0"]


def test_importa_riqueza_e_estado(session, tmp_path):
    f = _xlsx(tmp_path / "DETALLE_MATERIAL_FERT.xlsx", [
        _fila("1", "ÁCIDO NÍTRICO (15-00-00)", "15", "Líquido"),
        _fila("2", "NITRATO AMÓNICO-NA (34,5-00-00)", "34.5"),
    ])
    informe = importar_fertilizantes(session, f)
    assert informe.altas == 2
    acido = session.get(FertilizanteSiex, 1)
    assert acido.material == "14"
    assert acido.n_pct == 15.0 and acido.liquido and acido.densidade == 1.41
    assert acido.inhibidor_ureasa and not acido.inhibidor_nitrificacion
    nitrato = session.get(FertilizanteSiex, 2)
    assert nitrato.n_pct == 34.5 and not nitrato.liquido and nitrato.densidade is None


def test_produto_que_desaparece_queda_de_baixa(session, tmp_path):
    importar_fertilizantes(session, _xlsx(tmp_path / "v1.xlsx", [
        _fila("1", "A (15-00-00)", "15"), _fila("2", "B (20-00-00)", "20")]))
    informe = importar_fertilizantes(session, _xlsx(tmp_path / "v2.xlsx", [
        _fila("1", "A (15-00-00)", "15")]), hoxe=date(2026, 11, 1))
    assert informe.baixas == 1
    assert session.get(FertilizanteSiex, 2).data_baixa == date(2026, 11, 1)


def test_mesmo_ficheiro_dúas_veces(session, tmp_path):
    f = _xlsx(tmp_path / "DETALLE_MATERIAL_FERT.xlsx", [_fila("1", "A (15-00-00)", "15")])
    importar_fertilizantes(session, f)
    assert importar_fertilizantes(session, f).xa_importado

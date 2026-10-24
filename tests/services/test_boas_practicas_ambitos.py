from openpyxl import Workbook

from horta.models.catalogo import CatalogoValor
from horta.services.catalogos_importar import importar_catalogo


def test_boas_practicas_gardan_os_ambitos(session, tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Código SIEX", "Buenas prácticas", "Ámbito Fitosanitario",
               "Ámbito Fertilización", "Ámbito Riego", "Fecha de alta"])
    ws.append(["12", "Fertirrigación", "NO", "SI", "SI", "25/11/2025"])
    ws.append(["50", "Variedades resistentes", "SI", "NO", "NO", "25/11/2025"])
    ruta = tmp_path / "BUENAS_PRACTICAS_AMBITOS.xlsx"
    wb.save(ruta)
    importar_catalogo(session, "boas_practicas", ruta)
    valores = {v.codigo: v.categoria for v in session.query(CatalogoValor)}
    assert valores == {"12": "fertilizacion,rega", "50": "fito"}

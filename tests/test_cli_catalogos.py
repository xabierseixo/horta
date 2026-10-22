from openpyxl import Workbook

from horta import cli_catalogos


def _xlsx(ruta, cab, filas):
    wb = Workbook()
    ws = wb.active
    ws.append(cab)
    for f in filas:
        ws.append(f)
    wb.save(ruta)


def test_importar_directorio(tmp_path, monkeypatch, session, capsys):
    monkeypatch.setattr(cli_catalogos, "get_session", lambda: _ContextoSesion(session))
    _xlsx(tmp_path / "PRODUCTOS.xlsx",
          ["Código", "Cultivo", "Latín", "EPPO", "C. UPOV", "Hortícola", "Integrado",
           "Fecha de alta", "Fecha de modificación", "Fecha de baja"],
          [["99", "PATATA", "", "SOLTU", "", "SI", "SI", None, None, None]])
    _xlsx(tmp_path / "UNIDADES_MEDIDA.xlsx",
          ["Código SIEX", "Unidades de medida", "Fecha de alta", "Fecha de modificación",
           "Fecha de baja"], [["1", "m2", None, None, None]])
    assert cli_catalogos.main(["importar", str(tmp_path)]) == 0
    saida = capsys.readouterr().out
    assert "cultivo: 1 altas" in saida
    assert "unidade_medida: 1 altas" in saida


class _ContextoSesion:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        return False

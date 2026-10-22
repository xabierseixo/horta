"""horta-catalogos: importa os catálogos oficiais do FEGA descargados do portal SIEX."""

from __future__ import annotations

import argparse
from pathlib import Path

from horta.db import get_session
from horta.services.catalogos import cargar_nomes_galegos
from horta.services.catalogos_importar import (
    CATALOGOS_XERAIS,
    InformeImportacion,
    importar_catalogo,
    importar_cultivos,
    importar_variedades,
)

_NOMES_GALEGOS = Path(__file__).parent / "data" / "nomes_galegos.csv"


def _imprimir(informe: InformeImportacion) -> None:
    if informe.xa_importado:
        print(f"{informe.catalogo}: xa importado (sen cambios)")
    else:
        print(f"{informe.catalogo}: {informe.altas} altas, {informe.baixas} baixas, "
              f"{informe.cambios} cambios")


def _importar(directorio: Path) -> int:
    with get_session() as session:
        cultivos = directorio / "PRODUCTOS.xlsx"
        if cultivos.exists():
            _imprimir(importar_cultivos(session, cultivos))
        variedades = directorio / "VARIEDAD_ESPECIE_TIPO.xlsx"
        if variedades.exists():
            _imprimir(importar_variedades(session, variedades))
        for clave, (ficheiro, _, _) in CATALOGOS_XERAIS.items():
            ruta = directorio / f"{ficheiro}.xlsx"
            if ruta.exists():
                _imprimir(importar_catalogo(session, clave, ruta))
            else:
                print(f"{clave}: falta {ruta.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="horta-catalogos")
    sub = parser.add_subparsers(dest="orde", required=True)
    p_imp = sub.add_parser("importar", help="importa os XLSX dun directorio")
    p_imp.add_argument("directorio", type=Path)
    p_nom = sub.add_parser("nomes-galegos", help="carga os nomes galegos dos cultivos")
    p_nom.add_argument("csv", type=Path, nargs="?", default=_NOMES_GALEGOS)
    args = parser.parse_args(argv)
    if args.orde == "importar":
        return _importar(args.directorio)
    with get_session() as session:
        print(f"nomes galegos cargados: {cargar_nomes_galegos(session, args.csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""horta-catalogos: importa os catálogos oficiais do FEGA e o rexistro de fitosanitarios do MAPA."""

from __future__ import annotations

import argparse
from pathlib import Path

from horta.db import get_session
from horta.services.catalogos import cargar_nomes_galegos
from horta.services.catalogos_ficheiros import DIRECTORIO_APP, Revision, revisar
from horta.services.catalogos_importar import InformeImportacion
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_importar import importar_fitosanitarios

_NOMES_GALEGOS = Path(__file__).parent / "data" / "nomes_galegos.csv"


def _imprimir(informe: InformeImportacion) -> None:
    if informe.xa_importado:
        print(f"{informe.catalogo}: xa importado (sen cambios)")
    else:
        print(f"{informe.catalogo}: {informe.altas} altas, {informe.baixas} baixas, "
              f"{informe.cambios} cambios")


def _con_problemas(revisions: list[Revision]) -> list[Revision]:
    return [r for r in revisions if r.catalogo is not None
            and (r.erro or (r.informe is not None and r.informe.sospeitoso))]


def _importar(directorio: Path | None, forzar: bool) -> int:
    rutas = sorted((directorio or DIRECTORIO_APP).glob("*.xlsx"))
    with get_session() as session:
        # Primeiro revísase sen gardar: un ficheiro con erros ou sospeitoso detén todo
        problemas = _con_problemas(revisar(session, rutas))
        for r in problemas:
            if r.erro or r.informe is None:
                print(f"{r.ficheiro}: {r.erro}")
            else:
                print(f"{r.ficheiro}: daría de baixa {r.informe.baixas} de "
                      f"{r.informe.existentes} códigos (usa --forzar se é correcto)")
        if problemas and not forzar:
            return 1
        revisions = revisar(session, rutas, aplicar=True)
    for r in revisions:
        if r.informe is not None:
            _imprimir(r.informe)
        elif r.catalogo is not None:
            print(f"{r.ficheiro}: {r.erro}")
    ignorados = sum(r.catalogo is None for r in revisions)
    if ignorados:
        print(f"{ignorados} ficheiros non son catálogos dos que usa a app")
    return 1 if _con_problemas(revisions) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="horta-catalogos")
    sub = parser.add_subparsers(dest="orde", required=True)
    p_imp = sub.add_parser("importar", help="importa os XLSX do FEGA (por defecto, os da app)")
    p_imp.add_argument("directorio", type=Path, nargs="?", default=None)
    p_imp.add_argument("--forzar", action="store_true",
                       help="importar aínda que un ficheiro dea de baixa moitos códigos")
    p_fito = sub.add_parser("fitosanitarios", help="importa o rexistro de fitosanitarios do MAPA")
    p_fito.add_argument("directorio", type=Path)
    p_nom = sub.add_parser("nomes-galegos", help="carga os nomes galegos dos cultivos")
    p_nom.add_argument("csv", type=Path, nargs="?", default=_NOMES_GALEGOS)
    args = parser.parse_args(argv)
    if args.orde == "importar":
        return _importar(args.directorio, args.forzar)
    if args.orde == "fitosanitarios":
        with get_session() as session:
            try:
                _imprimir(importar_fitosanitarios(session, args.directorio))
            except OperacionNonPermitidaError as erro:
                print(f"fitosanitarios: {erro}")
                return 1
        return 0
    with get_session() as session:
        print(f"nomes galegos cargados: {cargar_nomes_galegos(session, args.csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

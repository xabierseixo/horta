"""Descarga o rexistro de fitosanitarios do MAPA (regfiweb) e impórtao.

Os dous JSON son descargas públicas directas, sen captcha. O FEGA indica que son a fonte
oficial de produtos para os cadernos comerciais. A resposta vén codificada dúas veces:
texto JSON → {Contenido, Fecha…} → «Contenido» é o JSON real.
"""

from __future__ import annotations

import json
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from horta.models.comprobacion_catalogo import ComprobacionCatalogo
from horta.services.catalogos_importar import InformeImportacion
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_importar import importar_fitosanitarios

CATALOGO = "fitosanitarios"
DIAS_ENTRE_DESCARGAS = 7
_BASE = "https://servicio.mapa.gob.es/regfiweb/Exportaciones"
_FICHEIROS = {
    "ProductosAutorizados.json": ("ExportJsonProductosAutorizados",
                                  {"tipoExportacion": "ProductosAutorizados"}),
    "Cultivos.json": ("ExportJsonCultivos", {}),
}


def _pedir(endpoint: str, extra: dict[str, str]) -> str:
    datos = urllib.parse.urlencode({**extra, "dataDto": "{}"}).encode()
    peticion = urllib.request.Request(f"{_BASE}/{endpoint}", data=datos,
                                      headers={"User-Agent": "horta (caderno de explotación)"})
    with urllib.request.urlopen(peticion, timeout=300) as resposta:
        envoltorio = json.loads(json.loads(resposta.read().decode("utf-8")))
    texto = envoltorio["Contenido"]
    if not json.loads(texto):
        raise OperacionNonPermitidaError(f"O MAPA devolveu {endpoint} baleiro")
    return str(texto)


def descargar_rexistro(destino: Path) -> None:
    for nome, (endpoint, extra) in _FICHEIROS.items():
        (destino / nome).write_text(_pedir(endpoint, extra), encoding="utf-8")


def ultima_comprobacion(session: Session) -> ComprobacionCatalogo | None:
    return session.get(ComprobacionCatalogo, CATALOGO)


def toca_actualizar(session: Session, agora: datetime | None = None) -> bool:
    agora = agora or datetime.now()
    ultima = ultima_comprobacion(session)
    return (ultima is None or ultima.erro is not None
            or agora - ultima.data >= timedelta(days=DIAS_ENTRE_DESCARGAS))


def _anotar(session: Session, agora: datetime, erro: str | None) -> None:
    ultima = ultima_comprobacion(session) or ComprobacionCatalogo(catalogo=CATALOGO, data=agora)
    ultima.data, ultima.erro = agora, erro
    session.add(ultima)
    session.commit()


def actualizar_fitosanitarios(session: Session, forzar: bool = False,
                              agora: datetime | None = None) -> InformeImportacion | None:
    """Descarga e importa se pasaron 7 días (ou se forzar). None = aínda non tocaba."""
    agora = agora or datetime.now()
    if not forzar and not toca_actualizar(session, agora):
        return None
    try:
        with tempfile.TemporaryDirectory() as directorio:
            descargar_rexistro(Path(directorio))
            informe = importar_fitosanitarios(session, Path(directorio))
    except Exception as erro:
        session.rollback()
        mensaxe = f"Non se puido actualizar o rexistro do MAPA: {erro}"[:500]
        _anotar(session, agora, mensaxe)
        raise OperacionNonPermitidaError(mensaxe) from erro
    _anotar(session, agora, None)
    return informe

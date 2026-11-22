# Tarefa 072e — Rexistro do MAPA: descarga automática

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072d. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Descarga os JSON do MAPA (sen captcha) e impórtaos se pasaron 7 días desde a última comprobación; anota o erro se falla. Probado contra o MAPA real o 2026-10-25 (2.091 produtos, 63.364 usos). Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/fito_descargar.py` (**ficheiro novo**)
- `tests/services/test_fito_descargar.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/fito_descargar.py`

Contido completo:
```python
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
```

### Paso 2 — crear o ficheiro `tests/services/test_fito_descargar.py`

Contido completo:
```python
import json
from datetime import datetime, timedelta

import pytest

from horta.models.fito_rexistro import FitoProduto
from horta.services import fito_descargar
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_descargar import (
    actualizar_fitosanitarios,
    toca_actualizar,
    ultima_comprobacion,
)

AGORA = datetime(2026, 10, 25, 12, 0)
_PRODUTOS = {"Productos": [{"DATOSPRODUCTO": {"Num_Registro": "ES-1", "Nombre": "A",
                                              "Estado": "Vigente"},
                            "COMPOSICION": [], "USOS": []}]}
_CULTIVOS = [{"CodigoEppo": "SOLTU", "CodigoCultivo": "0102090000000000"}]


@pytest.fixture
def mapa(monkeypatch):
    chamadas = []

    def pedir(endpoint, extra):
        chamadas.append(endpoint)
        return json.dumps(_PRODUTOS if "Productos" in endpoint else _CULTIVOS)

    monkeypatch.setattr(fito_descargar, "_pedir", pedir)
    return chamadas


def test_descarga_e_importa(session, mapa):
    informe = actualizar_fitosanitarios(session, agora=AGORA)
    assert informe.altas == 1 and session.get(FitoProduto, "ES-1")
    assert ultima_comprobacion(session).data == AGORA
    assert ultima_comprobacion(session).erro is None


def test_non_volve_descargar_ata_os_7_dias(session, mapa):
    actualizar_fitosanitarios(session, agora=AGORA)
    assert actualizar_fitosanitarios(session, agora=AGORA + timedelta(days=6)) is None
    assert len(mapa) == 2
    assert not toca_actualizar(session, AGORA + timedelta(days=6))
    # Sen cambios no MAPA: impórtase nada pero anótase a comprobación
    informe = actualizar_fitosanitarios(session, agora=AGORA + timedelta(days=7))
    assert informe.xa_importado and len(mapa) == 4
    assert ultima_comprobacion(session).data == AGORA + timedelta(days=7)


def test_erro_anotase_e_reinténtase(session, monkeypatch):
    def falla(endpoint, extra):
        raise OSError("sen rede")

    monkeypatch.setattr(fito_descargar, "_pedir", falla)
    with pytest.raises(OperacionNonPermitidaError, match="sen rede"):
        actualizar_fitosanitarios(session, agora=AGORA)
    assert "sen rede" in ultima_comprobacion(session).erro
    assert toca_actualizar(session, AGORA + timedelta(hours=6))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Rexistro do MAPA: descarga automática: feito.

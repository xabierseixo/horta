# Tarefa 072h — Catálogos: estado, aviso e permisos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072g2. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Estado de cada catálogo (códigos e data), aviso para a administración (faltan catálogos, máis de 60 días sen revisar, fallou o MAPA) e actualización só para a administración global. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/catalogos_estado.py` (**ficheiro novo**)
- `tests/services/test_catalogos_estado.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/catalogos_estado.py`

Contido completo:
```python
"""Estado dos catálogos oficiais, aviso para a administración e actualización con permisos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex
from horta.models.comprobacion_catalogo import ComprobacionCatalogo
from horta.models.fertilizante import FertilizanteSiex
from horta.models.usuario import RolGlobal, Usuario
from horta.services.catalogos_ficheiros import CATALOGOS_APP, Revision, revisar
from horta.services.catalogos_importar import InformeImportacion
from horta.services.errors import PermisoDenegadoError
from horta.services.fito_descargar import actualizar_fitosanitarios, ultima_comprobacion

DIAS_AVISO = 60
FEGA = "fega"  # comprobación manual dos catálogos do FEGA (aínda que non trouxesen cambios)


@dataclass
class EstadoCatalogo:
    clave: str
    nome: str
    ficheiro: str
    codigos: int
    importado: datetime | None


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só a administración pode actualizar os catálogos oficiais")


def estado_catalogos(session: Session) -> list[EstadoCatalogo]:
    ultimas: dict[str, datetime] = {
        catalogo: data for catalogo, data in session.query(
            CatalogoVersion.catalogo, func.max(CatalogoVersion.data_importacion)
        ).group_by(CatalogoVersion.catalogo)}
    codigos: dict[str, int] = {
        catalogo: n for catalogo, n in session.query(
            CatalogoValor.catalogo, func.count()).filter(CatalogoValor.data_baixa.is_(None)
                                                        ).group_by(CatalogoValor.catalogo)}
    codigos["cultivo"] = session.query(CultivoSiex).filter(CultivoSiex.data_baixa.is_(None)).count()
    codigos["variedade"] = session.query(VariedadeSiex).filter(
        VariedadeSiex.data_baixa.is_(None)).count()
    codigos["fertilizante"] = session.query(FertilizanteSiex).filter(
        FertilizanteSiex.data_baixa.is_(None)).count()
    return [EstadoCatalogo(clave, nome, f"{codigo}.xlsx", codigos.get(clave, 0),
                           ultimas.get(clave))
            for clave, (codigo, _, nome) in CATALOGOS_APP.items()]


def ultima_revision_fega(session: Session) -> datetime | None:
    """Última vez que alguén revisou os catálogos do FEGA: importación con cambios ou subida
    revisada aínda que non trouxese cambios."""
    datas = [e.importado for e in estado_catalogos(session) if e.importado]
    comprobacion = session.get(ComprobacionCatalogo, FEGA)
    if comprobacion is not None:
        datas.append(comprobacion.data)
    return max(datas) if datas else None


def avisos_catalogos(session: Session, agora: datetime | None = None) -> list[str]:
    agora = agora or datetime.now()
    avisos = []
    faltan = [e.nome for e in estado_catalogos(session) if e.importado is None]
    if faltan:
        avisos.append(f"Faltan catálogos oficiais: {', '.join(faltan)}.")
    revision = ultima_revision_fega(session)
    if revision is not None and (agora - revision).days > DIAS_AVISO:
        avisos.append(f"Os catálogos oficiais do FEGA levan {(agora - revision).days} días sen "
                      "revisar: descárgaos de novo e súbeos.")
    fito = ultima_comprobacion(session)
    if fito is not None and fito.erro:
        avisos.append(f"Fallou a descarga do rexistro de fitosanitarios do MAPA o "
                      f"{fito.data:%d/%m/%Y}. A app segue coa copia anterior.")
    return avisos


def revisar_ficheiros(session: Session, actor: Usuario, rutas: list[Path],
                      aplicar: bool = False, agora: datetime | None = None) -> list[Revision]:
    _esixir_admin(actor)
    revisions = revisar(session, rutas, aplicar=aplicar)
    if aplicar and any(r.informe is not None for r in revisions):
        comprobacion = session.get(ComprobacionCatalogo, FEGA) or ComprobacionCatalogo(
            catalogo=FEGA, data=agora or datetime.now())
        comprobacion.data, comprobacion.erro = agora or datetime.now(), None
        session.add(comprobacion)
        session.commit()
    return revisions


def actualizar_rexistro_mapa(session: Session, actor: Usuario) -> InformeImportacion:
    _esixir_admin(actor)
    informe = actualizar_fitosanitarios(session, forzar=True)
    assert informe is not None
    return informe
```

### Paso 2 — crear o ficheiro `tests/services/test_catalogos_estado.py`

Contido completo:
```python
from datetime import datetime, timedelta

import pytest
from openpyxl import Workbook

from horta.models.catalogo import CatalogoVersion
from horta.models.comprobacion_catalogo import ComprobacionCatalogo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.catalogos_estado import (
    avisos_catalogos,
    estado_catalogos,
    revisar_ficheiros,
    ultima_revision_fega,
)
from horta.services.errors import PermisoDenegadoError
from horta.services.fito_descargar import CATALOGO as FITO

AGORA = datetime(2026, 10, 25, 12, 0)


def _usuario(session, rol):
    u = Usuario(nome=rol.value, email=f"{rol.value}@example.com", password_hash="x", rol=rol,
                activo=True)
    session.add(u)
    session.commit()
    return u


def _pragas(ruta):
    libro = Workbook()
    ws = libro.active
    ws.title = "Artrópodos y gasterópodos"
    ws.append(["Código SIEX", "Nombre científico"])
    ws.append(["1", "Especie 1"])
    libro.save(ruta)
    return ruta


def test_sen_catalogos_avisa_de_que_faltan(session):
    [aviso] = avisos_catalogos(session, AGORA)
    assert aviso.startswith("Faltan catálogos oficiais: Cultivos, Variedades")


def test_aviso_aos_60_dias_e_subida_reinicia(session, tmp_path):
    admin = _usuario(session, RolGlobal.ADMIN)
    revisar_ficheiros(session, admin, [_pragas(tmp_path / "PLAGAS.xlsx")], aplicar=True,
                      agora=AGORA - timedelta(days=61))
    version = session.query(CatalogoVersion).filter_by(catalogo="praga").one()
    version.data_importacion = AGORA - timedelta(days=61)
    session.commit()
    estado = {e.clave: e for e in estado_catalogos(session)}
    assert estado["praga"].codigos == 1
    assert any("levan 61 días sen revisar" in a for a in avisos_catalogos(session, AGORA))
    # Volver subir o mesmo ficheiro (sen cambios) conta como revisión
    revisar_ficheiros(session, admin, [_pragas(tmp_path / "PLAGAS.xlsx")], aplicar=True,
                      agora=AGORA)
    assert ultima_revision_fega(session) == AGORA
    assert not any("sen revisar" in a for a in avisos_catalogos(session, AGORA))


def test_aviso_se_fallou_o_mapa(session):
    session.add(ComprobacionCatalogo(catalogo=FITO, data=AGORA, erro="sen rede"))
    session.commit()
    assert any("Fallou a descarga do rexistro" in a for a in avisos_catalogos(session, AGORA))


def test_so_a_administracion_actualiza(session, tmp_path):
    usuario = _usuario(session, RolGlobal.USUARIO)
    with pytest.raises(PermisoDenegadoError):
        revisar_ficheiros(session, usuario, [_pragas(tmp_path / "PLAGAS.xlsx")])
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Catálogos: estado, aviso e permisos: feito.

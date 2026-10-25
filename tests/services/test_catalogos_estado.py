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

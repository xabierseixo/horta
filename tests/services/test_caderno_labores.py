from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1



def test_labores_no_caderno(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="tipo_labor", codigo="7", descricion="Poda",
                              version_id=v.id))
    session.add(CatalogoValor(catalogo="unidade_medida", codigo="41", descricion="kW",
                              version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Maceira")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2)
    maquina = crear_maquina(session, ana, horta.id, "Tesoira", id_equipo_non_inscribible="T1",
                            potencia=0.5, unidade_potencia="41")
    crear_labor(session, ana, DatosLabor(cultivo_id=cultivo.id, data_inicio=date(2026, 2, 10),
                                         persoa_id=QUEN,
                                         tipo_labor="7", restos_poda_no_solo=True,
                                         maquina_id=maquina.id, num_repeticions=1,
                                         duracion_h=3), hoxe=date(2026, 10, 25))
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = list(libro["9 Labores (CUE)"].iter_rows(values_only=True))
    assert filas[0][0] == "9. LABORES CULTURAIS (CUE, bloque 5)"
    assert list(filas[4][:6]) == [1, 0.2, "Poda", "10/02/2026", None, "SI"]
    assert filas[4][8] == 0.5 and filas[4][10] == 1 and filas[4][11] == 3
    # Fóra do período non sae
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 3, 1),
                                                date(2026, 12, 31))))
    assert len(list(libro["9 Labores (CUE)"].iter_rows(values_only=True))) == 4

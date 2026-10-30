"""O REA da Xunta fronte á app: emparellar os cultivos coas DGC por recinto SIGPAC, as
diferenzas, e o CUE con CodigoDGC ou cambio de cultivo
."""

import json
from pathlib import Path

from test_cue import ATA, DESDE, _escenario

from horta.services.cue import xerar_cue
from horta.services.rea import aceptar, comparar, ler_dgcs
from horta.services.xeaga import ler_resultado

DATOS = Path(__file__).parent.parent / "datos" / "xeaga"


def _dgcs():
    return ler_dgcs(ler_resultado(json.loads((DATOS / "rea_dgc.json").read_text())).rea)


def test_le_as_dgc_vixentes():
    dgcs = _dgcs()
    assert [d.codigo for d in dgcs] == [5001, 5002, 5003]
    assert dgcs[0].recinto == (15, 78, 0, 0, 12, 101, 1)
    assert dgcs[0].cultivos[0].identificador == 9001


def test_emparella_e_mostra_as_diferenzas(session):
    ana, horta, _, (uno, dous) = _escenario(session)
    comparacion = comparar(session, ana, horta.id, _dgcs())
    por_cultivo = {e.cultivo_id: e for e in comparacion.emparellados}
    # Leira 1: mesmo cultivo (tomate) na DGC 5001, pero máis superficie na app
    assert (por_cultivo[uno.id].codigo_dgc, por_cultivo[uno.id].codigo_cultivo_rea) == (5001,
                                                                                          9001)
    assert "superficie" in por_cultivo[uno.id].diferenzas[0]
    # Leira 2: no REA hai outro cultivo: cambio de cultivo
    assert (por_cultivo[dous.id].codigo_dgc, por_cultivo[dous.id].codigo_cultivo_rea) == (5002,
                                                                                           None)
    assert [d.codigo for d in comparacion.so_na_xunta] == [5003]
    assert comparacion.so_na_app == []


def test_aceptado_o_cue_usa_a_dgc_do_rea(session):
    ana, horta, _, (uno, dous) = _escenario(session)
    comparacion = comparar(session, ana, horta.id, _dgcs())
    assert aceptar(session, ana, horta.id, comparacion.emparellados) == 2
    datos = xerar_cue(session, ana, horta.id, DESDE, ATA).datos
    assert "AltaDGC" not in datos.get("DatosExplotacion", {})
    [cambio] = datos["DatosExplotacion"]["CambioCultivoDGC"]
    assert (cambio["CodigoDGC"], cambio["Cultivo"]) == (5002, 37)
    sementeiras = datos["ActividadesExplotacion"]["SiembraPlantacion"]
    dgcs = {s["DGCs"][0]["CodigoDGC"]: s["DGCs"][0] for s in sementeiras}
    assert dgcs[5001]["CodigoCultivo"] == 9001 and "CodigoCultivo" not in dgcs[5002]

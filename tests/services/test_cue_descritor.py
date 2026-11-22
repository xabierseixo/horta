"""O descritor oficial do CUE (FEGA, Anexo VI v3.11.4) e o comprobador."""

from horta.services.cue_descritor import descritor, validar

ACTIVIDADES = ["EnergiaUtilizada", "ActividadAgraria", "TratamientosPostCosecha",
               "TratamientosEdifInstalaciones", "SiembraPlantacion", "UsoSemillaTratada",
               "Cosecha", "TratamFito", "Fertilizacion", "PlanAbonado", "ComercializacionVD",
               "Analitica", "Pastoreo", "DatosCubierta", "LaboresCulturales", "Riego"]


def test_le_todos_os_bloques():
    cuaderno = descritor()
    assert [f.nome for f in cuaderno.fillo("ActividadesExplotacion").fillos] == ACTIVIDADES
    riego = cuaderno.fillo("ActividadesExplotacion").fillo("Riego")
    cantidade = riego.fillo("Cantidad")
    assert (cantidade.obrigatorio, cantidade.tipo, cantidade.lonxitude, cantidade.decimais) == (
        True, "number", 8, 2)
    assert riego.fillo("DGCs").minimo == 1 and riego.fillo("DGCs").maximo is None


def _cuaderno(**riego):
    base = {"IdAjenaRiego": 1, "FechaInicio": "01/06/2026", "FechaFin": "01/06/2026",
            "SistemaRiego": 6, "Cantidad": 12.5, "UnidadMedida": 3,
            "DGCs": [{"CodigoDGCAjena": 7, "Superficie": 0.1}]}
    base.update(riego)
    return {"CAExplotacion": "12", "IdTitular": "12345678Z", "UnidadGestora": "12345678Z",
            "CodigoRea": "ES150010000001", "ActividadesExplotacion": {"Riego": [base]}}


def test_un_rexistro_correcto_non_ten_erros():
    assert validar(_cuaderno()) == []


def test_detecta_os_erros():
    erros = {e.ruta.rsplit("/", 1)[-1]: e.mensaxe for e in validar(_cuaderno(
        FechaInicio="2026-06-01", Cantidad=1.234, SistemaRiego=None, NumContador="X" * 20,
        Inventado=1, DGCs=[]))}
    assert "data" in erros["FechaInicio"]
    assert "decimais" in erros["Cantidad"]
    assert erros["SistemaRiego"] == "é obrigatorio"
    assert "caracteres" in erros["NumContador"]
    assert "non existe" in erros["Inventado"]
    assert erros["DGCs"] == "é obrigatorio"

import json

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_importar import NON_FIGURA, importar_fitosanitarios
from horta.services.fito_normalizar import (
    aplicacions_max,
    intervalo_min_dias,
    nome_cientifico,
    prazo_seguridade,
    unidade_dose,
)


def _produto(num, nome, usos, estado="Vigente"):
    return {
        "DATOSPRODUCTO": {"IdProducto": 1, "Num_Registro": num, "Nombre": nome,
                          "Titular": "Empresa", "Estado": estado,
                          "Fecha_Caducidad": "2030-07-31T00:00:00"},
        "COMPOSICION": [{"Nombre Sustancia": "AZUFRE", "Concentracion": 80,
                         "DescripcionNota": "% p/p"}],
        "USOS": usos,
    }


_USO = {"CodigoCultivo": "0102090000000000", "Cultivo": "Patata",
        "CodigoAgente": "8.48.4.5",
        "Agente": "Mildiu de la patata y el tomate, Phytophthora infestans",
        "TipoUsuario": "Profesional", "Dosis_Min": 0.38, "Dosis_Max": 1.25,
        "Unidad Medida dosis": "%", "Plazo Seguridad": "14", "Aplicaciones": "Máx. 5",
        "IntervaloAplicaciones": "7-10 días"}


def _escribir(directorio, produtos):
    (directorio / "ProductosAutorizados.json").write_text(
        json.dumps({"Productos": produtos}), encoding="utf-8")
    (directorio / "Cultivos.json").write_text(json.dumps([
        {"NombreComun": "Patata", "CodigoEppo": "SOLTU", "CodigoCultivo": "0102090000000000"},
    ]), encoding="utf-8")


def _catalogos_siex(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CultivoSiex(codigo=99, nome_oficial="PATATA", codigo_eppo="SOLTU",
                            version_id=v.id))
    session.add(CatalogoValor(catalogo="enfermidade", codigo="77",
                              descricion="Phytophthora infestans", version_id=v.id))
    session.commit()


def test_importa_produtos_usos_e_pontes(session, tmp_path):
    _catalogos_siex(session)
    _escribir(tmp_path, [_produto("ES-001", "FUNXICIDA", [_USO])])
    informe = importar_fitosanitarios(session, tmp_path)
    assert informe.altas == 1
    produto = session.get(FitoProduto, "ES-001")
    assert produto.nome == "FUNXICIDA" and produto.data_caducidade.year == 2030
    assert session.query(FitoMateria).one().sustancia == "AZUFRE"
    uso = session.query(FitoUso).one()
    assert (uso.dose_max, uso.unidade_dose, uso.ps_dias, uso.aplicacions_max,
            uso.intervalo_min_dias) == (1.25, "%", 14, 5, 7)
    ponte = session.query(FitoPonteCultivo).one()
    assert (ponte.cultivo_siex_codigo, ponte.codigo_cultivo) == (99, "0102090000000000")
    axente = session.query(FitoPonteAxente).one()
    assert (axente.catalogo, axente.codigo, axente.codigo_agente) == (
        "enfermidade", "77", "8.48.4.5")


def test_reimportar_igual_non_fai_nada(session, tmp_path):
    _escribir(tmp_path, [_produto("ES-001", "FUNXICIDA", [_USO])])
    importar_fitosanitarios(session, tmp_path)
    assert importar_fitosanitarios(session, tmp_path).xa_importado


def test_produto_que_desaparece_queda_como_non_figura(session, tmp_path):
    _escribir(tmp_path, [_produto("ES-001", "A", [_USO]), _produto("ES-002", "B", [])])
    importar_fitosanitarios(session, tmp_path)
    _escribir(tmp_path, [_produto("ES-001", "A", [_USO])])
    informe = importar_fitosanitarios(session, tmp_path)
    assert informe.baixas == 1
    assert session.get(FitoProduto, "ES-002").estado == NON_FIGURA
    assert session.query(FitoUso).count() == 1


def test_falta_un_ficheiro(session, tmp_path):
    with pytest.raises(OperacionNonPermitidaError):
        importar_fitosanitarios(session, tmp_path)


@pytest.mark.parametrize(("texto", "esperado"), [
    ("14", ("dias", 14)), ("No procede", ("non_procede", 0)), ("NP", ("non_procede", 0)),
    ("10 aire libre, 3 invernadero", ("condicional", 10)), ("", ("sen_dato", None)),
])
def test_prazo_seguridade(texto, esperado):
    assert prazo_seguridade(texto) == esperado


def test_outros_campos():
    assert aplicacions_max("1-3") == 3
    assert intervalo_min_dias("3-4 semanas") == 21
    assert unidade_dose("Kg/Ha") == "kg/ha"
    assert nome_cientifico("Bledos, Amaranthus spp.") == "AMARANTHUS SPP."

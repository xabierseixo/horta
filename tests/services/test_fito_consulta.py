from datetime import date

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex
from horta.models.cultivo import Cultivo
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.services.fito_consulta import (
    AVISO,
    FORTE,
    INFO,
    aviso_prazo_colleita,
    buscar_produtos,
    comprobar_tratamento,
    materia_activa,
    prazo_seguridade,
)
from horta.services.tratamentos_fito import DatosTratamento, LinhaCultivo, LinhaProduto, Problema

D = date(2026, 6, 1)
PATATA, HORTALIZAS = "0102090000000000", "0102000000000000"
MILDIU = "8.48.4.5"


def _uso(num, cultivo, agente, nome, **extra):
    datos = dict(num_rexistro=num, codigo_cultivo=cultivo, cultivo="c", codigo_agente=agente,
                 agente=nome, tipo_usuario="Profesional", dose_min=0.5, dose_max=1.0,
                 unidade_dose="l/ha", ps_tipo="dias", ps_dias=14, aplicacions_max=2)
    datos.update(extra)
    return FitoUso(**datos)


def _escenario(session, profesional=True, siex=True):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CultivoSiex(codigo=99, nome_oficial="PATATA", codigo_eppo="SOLTU",
                            version_id=v.id))
    for catalogo, codigo, texto in [("enfermidade", "77", "Phytophthora infestans"),
                                    ("enfermidade", "78", "Botrytis cinerea"),
                                    ("unidade_medida", "18", "L/ha")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=texto,
                                  version_id=v.id))
    session.add(FitoProduto(num_rexistro="ES-1", nome="MILDIUCIDA", estado="Vigente",
                            version_id=v.id))
    session.add(FitoProduto(num_rexistro="ES-2", nome="XERAL", estado="Vigente",
                            version_id=v.id))
    session.add(FitoProduto(num_rexistro="ES-3", nome="VELLO", estado="Cancelado",
                            data_cancelacion=date(2025, 1, 1), version_id=v.id))
    session.flush()
    session.add(FitoMateria(num_rexistro="ES-1", sustancia="COBRE", concentracion=20,
                            unidade="% p/p"))
    session.add(_uso("ES-1", PATATA, MILDIU, "Mildiu de la patata, Phytophthora infestans"))
    session.add(_uso("ES-2", HORTALIZAS, "8.48", "Mildius, Peronosporaceae", ps_dias=3))
    session.add(FitoPonteCultivo(cultivo_siex_codigo=99, codigo_cultivo=PATATA))
    session.add(FitoPonteAxente(catalogo="enfermidade", codigo="77", codigo_agente=MILDIU))
    session.add(FitoPonteAxente(catalogo="enfermidade", codigo="78", codigo_agente="8.20.1"))
    horta = Horta(nome="H", uso_profesional=profesional)
    session.add(horta)
    session.flush()
    parcela = Parcela(horta_id=horta.id, nome="P", estado="activa")
    session.add(parcela)
    session.flush()
    cultivo = Cultivo(parcela_id=parcela.id, especie="Pataca",
                      cultivo_siex_codigo=99 if siex else None)
    session.add(cultivo)
    session.commit()
    return horta, cultivo


def _datos(cultivo, num="ES-1", problema="77", dose=1.0):
    return DatosTratamento(
        data_inicio=D, data_fin=D, cultivos=[LinhaCultivo(cultivo.id, None)],
        problemas=[Problema("enfermidade", problema)], xustificacions=[],
        produtos=[LinhaProduto(tipo_produto="1", unidade="18", num_rexistro=num, dose=dose)],
    )


def _textos(avisos, nivel):
    return " | ".join(a.texto for a in avisos if a.nivel == nivel)


def test_uso_autorizado_informa_da_etiqueta(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "autorizado contra Mildiu de la patata" in _textos(avisos, INFO)
    assert "prazo de seguridade 14 días" in _textos(avisos, INFO)
    assert not _textos(avisos, FORTE)


def test_problema_non_autorizado(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo, problema="78"))
    assert "non atopamos o uso contra Botrytis cinerea" in _textos(avisos, FORTE)


def test_categorias_superiores_do_cultivo_e_do_problema(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo, num="ES-2"))
    assert "XERAL: autorizado contra Mildius" in _textos(avisos, INFO)


def test_problema_sen_ponte(session):
    horta, cultivo = _escenario(session)
    datos = _datos(cultivo)
    datos.problemas = [Problema("enfermidade", "79")]
    avisos = comprobar_tratamento(session, horta, datos)
    assert "non podemos comprobar o problema" in _textos(avisos, INFO)


def test_cultivo_sen_codigo_siex(session):
    horta, cultivo = _escenario(session, siex=False)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "non podemos comprobar automaticamente o uso" in _textos(avisos, INFO)


def test_dose_por_riba_da_maxima(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo, dose=1.5))
    assert "pasa da máxima da etiqueta (1 l/ha)" in _textos(avisos, FORTE)


def test_autoconsumo_e_produto_profesional(session):
    horta, cultivo = _escenario(session, profesional=False)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "só para usuarios profesionais" in _textos(avisos, AVISO)


def test_produto_cancelado_ou_descoñecido(session):
    horta, cultivo = _escenario(session)
    assert "cancelado no rexistro o 01/01/2025" in _textos(
        comprobar_tratamento(session, horta, _datos(cultivo, num="ES-3")), FORTE)
    assert "non figura no rexistro" in _textos(
        comprobar_tratamento(session, horta, _datos(cultivo, num="ES-9")), FORTE)


def test_maximo_de_aplicacions(session):
    horta, cultivo = _escenario(session)
    for _ in range(2):
        t = TratamentoFito(horta_id=horta.id, data_inicio=D, data_fin=D)
        t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
        t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1")]
        session.add(t)
    session.commit()
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "aplicación nº 3" in _textos(avisos, FORTE)
    # Ao editar un dos dous xa gardados non conta el mesmo
    assert "aplicación nº" not in _textos(
        comprobar_tratamento(session, horta, _datos(cultivo), tratamento_id=t.id), FORTE)


def test_prazo_seguridade(session):
    horta, cultivo = _escenario(session)
    t = TratamentoFito(horta_id=horta.id, data_inicio=D, data_fin=D)
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
    t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1"),
                  TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-2")]
    session.add(t)
    session.commit()
    assert prazo_seguridade(session, t) == date(2026, 6, 15)


def test_buscar_e_materia_activa(session):
    _escenario(session)
    assert [p.num_rexistro for p in buscar_produtos(session, "mildi")] == ["ES-1"]
    assert [p.nome for p in buscar_produtos(session, "ES-2")] == ["XERAL"]
    assert buscar_produtos(session, "m") == []
    assert materia_activa(session, "ES-1") == "COBRE 20 % p/p"


def test_aviso_prazo_colleita(session):
    horta, cultivo = _escenario(session)
    t = TratamentoFito(horta_id=horta.id, data_inicio=D, data_fin=D)
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
    t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1",
                                    nome_comercial="MILDIUCIDA")]
    session.add(t)
    session.commit()
    aviso = aviso_prazo_colleita(session, cultivo.id, date(2026, 6, 10))
    assert aviso and "MILDIUCIDA" in aviso and "15/06/2026" in aviso
    assert aviso_prazo_colleita(session, cultivo.id, date(2026, 6, 15)) is None
    assert aviso_prazo_colleita(session, cultivo.id, date(2026, 5, 1)) is None

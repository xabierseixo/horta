from datetime import date, timedelta

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import Horta, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
from horta.services.recomendacions import (
    _a_datos,
    actualizar_recomendacion,
    aplicar_recomendacion,
    avisos_recomendacion,
    crear_recomendacion,
    dar_de_baixa_recomendacion,
    descartar_recomendacion,
    ligar_tratamento,
    listar_recomendacions,
    recomendacions_pendentes,
)
from horta.services.tratamentos_fito import (
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaMedida,
    LinhaProduto,
    Problema,
    crear_tratamento_fito,
)

D = date(2026, 5, 10)


def _usuario(session, email: str) -> Usuario:
    u = Usuario(
        nome=email,
        email=email,
        password_hash="x",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(u)
    session.commit()
    return u


def _catalogos(session) -> None:
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [
        ("enfermidade", "10"),
        ("xustificacion", "1"),
        ("tipo_produto", "1"),
        ("unidade_medida", "5"),
        ("unidade_medida", "17"),
        ("estado_fenoloxico", "6"),
        ("eficacia", "1"),
    ]:
        session.add(
            CatalogoValor(
                catalogo=catalogo,
                codigo=codigo,
                descricion=catalogo,
                version_id=v.id,
            )
        )
    session.commit()


def _escenario(session, profesional: bool = True):
    _catalogos(session)
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    session.get(Horta, horta.id).uso_profesional = profesional
    session.commit()
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.2)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    xan = crear_persoa(
        session,
        ana,
        horta.id,
        "Xan",
        papeis={"aplicador"},
        ropo_numero="1",
        ropo_caducidade=D,
    )
    bieito = crear_persoa(
        session,
        ana,
        horta.id,
        "Bieito",
        papeis={"asesor"},
        ropo_numero="2",
        ropo_caducidade=D,
    )
    maquina = crear_maquina(
        session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1"
    )
    return ana, horta, parcela, cultivo, xan, bieito, maquina


def _datos_rec(cultivo, bieito, **cambios):
    base = dict(
        asesor_persoa_id=bieito.id,
        data=D,
        cultivos=[
            LinhaCultivo(
                cultivo_id=cultivo.id,
                superficie_ha=0.1,
                estado_fenoloxico="6",
            )
        ],
        problemas=[Problema(tipo="enfermidade", codigo="10")],
        xustificacions=["1"],
        produtos=[
            LinhaProduto(
                tipo_produto="1",
                unidade="17",
                num_rexistro="ES-1",
                nome_comercial="Cobre",
                dose=2.0,
            )
        ],
        medidas=[],
        valida_ata=None,
        observacions="Observación de proba",
    )
    base.update(cambios)
    return base


def test_crear_recomendacion_correcta(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    valida = D + timedelta(days=15)
    datos = _datos_rec(cultivo, bieito, valida_ata=valida, observacions="Tratar cedo")
    rec = crear_recomendacion(session, ana, horta.id, **datos)

    assert rec.id is not None
    assert rec.horta_id == horta.id
    assert rec.asesor_persoa_id == bieito.id
    assert rec.data == D
    assert rec.valida_ata == valida
    assert rec.observacions == "Tratar cedo"
    assert rec.estado == "pendente"
    assert rec.baixa is False
    assert len(rec.cultivos) == 1
    assert rec.cultivos[0]["cultivo_id"] == cultivo.id
    assert rec.problemas[0]["codigo"] == "10"
    assert rec.xustificacions == ["1"]
    assert rec.produtos[0]["nome_comercial"] == "Cobre"

    datos_t = _a_datos(rec)
    assert datos_t.data_inicio == D
    assert datos_t.cultivos[0].cultivo_id == cultivo.id
    assert datos_t.asesor is not None
    assert datos_t.asesor.persoa_id == bieito.id
    assert datos_t.asesor.validacion is True


def test_crear_asesor_sen_papel_rexeitase(session):
    ana, horta, _, cultivo, _, _, _ = _escenario(session)
    pepe = crear_persoa(session, ana, horta.id, "Pepe", papeis={"traballador"})
    datos = _datos_rec(cultivo, pepe)
    with pytest.raises(OperacionNonPermitidaError, match="Escolle un asesor"):
        crear_recomendacion(session, ana, horta.id, **datos)


def test_crear_asesor_doutra_horta_rexeitase(session):
    ana, horta, _, cultivo, _, _, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra Horta")
    asesor_outra = crear_persoa(
        session, ana, outra.id, "Asesor Outra", papeis={"asesor"},
        ropo_numero="9", ropo_caducidade=D,
    )
    datos = _datos_rec(cultivo, asesor_outra)
    with pytest.raises(OperacionNonPermitidaError, match="Escolle un asesor"):
        crear_recomendacion(session, ana, horta.id, **datos)


def test_crear_cultivo_doutra_horta_rexeitase(session):
    ana, horta, _, _, _, bieito, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra Horta")
    p_outra = crear_parcela(session, ana, outra.id, "P2")
    c_outra = crear_cultivo(session, ana, p_outra.id, "Cenoria")
    datos = _datos_rec(c_outra, bieito)
    with pytest.raises(
        OperacionNonPermitidaError, match="non pertence a esta explotación"
    ):
        crear_recomendacion(session, ana, horta.id, **datos)


def test_crear_cultivo_pechado_rexeitase(session):
    ana, horta, parcela, _, _, bieito, _ = _escenario(session)
    cultivo_pechado = crear_cultivo(session, ana, parcela.id, "Tomate")
    cultivo_pechado.data_fin = date(2026, 5, 1)
    session.commit()
    datos = _datos_rec(cultivo_pechado, bieito)
    with pytest.raises(OperacionNonPermitidaError, match="pechado"):
        crear_recomendacion(session, ana, horta.id, **datos)


def test_crear_sen_produtos_nin_medidas_rexeitase(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    datos = _datos_rec(cultivo, bieito, produtos=[], medidas=[])
    with pytest.raises(
        OperacionNonPermitidaError, match="produto ou unha medida"
    ):
        crear_recomendacion(session, ana, horta.id, **datos)


def test_crear_con_medida_sen_produto(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    medida = LinhaMedida(tipo_medida="1", cantidade=10.0, unidade="kg")
    datos = _datos_rec(cultivo, bieito, produtos=[], medidas=[medida])
    rec = crear_recomendacion(session, ana, horta.id, **datos)
    assert len(rec.medidas) == 1
    assert rec.medidas[0]["tipo_medida"] == "1"


def test_crear_valida_ata_anterior_rexeitase(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    datos = _datos_rec(cultivo, bieito, data=D, valida_ata=date(2026, 5, 9))
    with pytest.raises(OperacionNonPermitidaError, match="anterior"):
        crear_recomendacion(session, ana, horta.id, **datos)


def test_lector_non_pode_crear(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    datos = _datos_rec(cultivo, bieito)
    with pytest.raises(PermisoDenegadoError):
        crear_recomendacion(session, carlos, horta.id, **datos)


def test_recomendacions_pendentes_exclue_caducadas_e_aplicadas(session):
    ana, horta, _, cultivo, xan, bieito, maquina = _escenario(session)

    # 1. Válida con data límite futura
    rec1 = crear_recomendacion(
        session,
        ana,
        horta.id,
        **_datos_rec(cultivo, bieito, valida_ata=D + timedelta(days=5)),
    )
    # 2. Válida sen límite
    rec2 = crear_recomendacion(
        session,
        ana,
        horta.id,
        **_datos_rec(cultivo, bieito, valida_ata=None),
    )
    # 3. Caducada
    crear_recomendacion(
        session,
        ana,
        horta.id,
        **_datos_rec(
            cultivo,
            bieito,
            data=D - timedelta(days=10),
            valida_ata=D - timedelta(days=1),
        ),
    )
    # 4. Aplicada
    rec4 = crear_recomendacion(
        session,
        ana,
        horta.id,
        **_datos_rec(cultivo, bieito, valida_ata=D + timedelta(days=5)),
    )
    aplicar_recomendacion(
        session,
        ana,
        rec4,
        data_inicio=D,
        data_fin=D,
        aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
        cantidades={0: 3.0},
    )
    # 5. Descartada
    rec5 = crear_recomendacion(
        session,
        ana,
        horta.id,
        **_datos_rec(cultivo, bieito, valida_ata=D + timedelta(days=5)),
    )
    descartar_recomendacion(session, ana, rec5, motivo="Non necesaria")

    # 6. Dada de baixa
    rec6 = crear_recomendacion(
        session,
        ana,
        horta.id,
        **_datos_rec(cultivo, bieito, valida_ata=D + timedelta(days=5)),
    )
    dar_de_baixa_recomendacion(session, ana, rec6)

    pendentes = recomendacions_pendentes(session, ana, horta.id, hoxe=D)
    ids_pendentes = [r.id for r in pendentes]
    assert rec1.id in ids_pendentes
    assert rec2.id in ids_pendentes
    assert rec4.id not in ids_pendentes
    assert rec5.id not in ids_pendentes
    assert rec6.id not in ids_pendentes
    assert len(pendentes) == 2


def test_aplicar_recomendacion(session):
    ana, horta, _, cultivo, xan, bieito, maquina = _escenario(session)
    rec = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))

    tratamento = aplicar_recomendacion(
        session,
        ana,
        rec,
        data_inicio=D,
        data_fin=D,
        aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
        cantidades={0: 5.0},
    )

    assert tratamento.id is not None
    assert [c.cultivo_id for c in tratamento.cultivos] == [cultivo.id]
    assert [p.codigo for p in tratamento.problemas] == ["10"]
    assert len(tratamento.produtos) == 1
    assert tratamento.produtos[0].cantidade == 5.0
    assert tratamento.produtos[0].dose is None
    assert tratamento.produtos[0].unidade == "5"
    assert tratamento.asesor is not None
    assert tratamento.asesor.persoa_id == bieito.id
    assert tratamento.asesor.validacion is True
    assert rec.estado == "aplicada"
    assert rec.tratamento_id == tratamento.id

    # Non se pode aplicar dúas veces
    with pytest.raises(OperacionNonPermitidaError, match="pendente"):
        aplicar_recomendacion(
            session,
            ana,
            rec,
            data_inicio=D,
            data_fin=D,
            aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
        )


def test_descartar_recomendacion_con_e_sen_motivo(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    rec = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))

    with pytest.raises(OperacionNonPermitidaError, match="motivo"):
        descartar_recomendacion(session, ana, rec, motivo="")

    with pytest.raises(OperacionNonPermitidaError, match="motivo"):
        descartar_recomendacion(session, ana, rec, motivo="   ")

    descartar_recomendacion(
        session, ana, rec, motivo="Praga controlada con fauna auxiliar"
    )
    assert rec.estado == "descartada"
    assert rec.motivo_descarte == "Praga controlada con fauna auxiliar"

    with pytest.raises(OperacionNonPermitidaError, match="pendente"):
        descartar_recomendacion(session, ana, rec, motivo="Outro motivo")


def test_actualizar_e_dar_de_baixa(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    rec = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))

    actualizar_recomendacion(session, ana, rec, observacions="Observación actualizada")
    assert rec.observacions == "Observación actualizada"

    with pytest.raises(OperacionNonPermitidaError, match="anterior"):
        actualizar_recomendacion(
            session, ana, rec, valida_ata=D - timedelta(days=1)
        )

    dar_de_baixa_recomendacion(session, ana, rec)
    assert rec.baixa is True
    assert listar_recomendacions(session, ana, horta.id) == []

    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_recomendacion(session, ana, rec, observacions="Novo")


def test_avisos_recomendacion(session):
    ana, horta, _, cultivo, _, bieito, _ = _escenario(session)
    rec = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))
    avisos = avisos_recomendacion(session, rec)
    assert isinstance(avisos, list)


def test_ligar_tratamento_correcto(session):
    ana, horta, _, cultivo, xan, bieito, maquina = _escenario(session)
    rec = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))
    datos_t = DatosTratamento(
        data_inicio=D,
        data_fin=D,
        cultivos=[LinhaCultivo(cultivo.id, 0.1, "6")],
        problemas=[Problema("enfermidade", "10")],
        xustificacions=["1"],
        produtos=[LinhaProduto("1", "5", num_rexistro="ES-1", cantidade=2.0)],
        medidas=[],
        aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
    )
    tratamento = crear_tratamento_fito(session, ana, horta.id, datos_t)

    ligar_tratamento(session, ana, rec, tratamento)
    assert rec.estado == "aplicada"
    assert rec.tratamento_id == tratamento.id


def test_ligar_tratamento_validacions(session):
    ana, horta, _, cultivo, xan, bieito, maquina = _escenario(session)
    rec = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))
    datos_t = DatosTratamento(
        data_inicio=D,
        data_fin=D,
        cultivos=[LinhaCultivo(cultivo.id, 0.1, "6")],
        problemas=[Problema("enfermidade", "10")],
        xustificacions=["1"],
        produtos=[LinhaProduto("1", "5", num_rexistro="ES-1", cantidade=2.0)],
        medidas=[],
        aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
    )
    tratamento = crear_tratamento_fito(session, ana, horta.id, datos_t)

    # Lector non pode ligar
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        ligar_tratamento(session, carlos, rec, tratamento)

    # Tratamento doutra horta rexeitase
    outra = crear_horta(session, ana, "Outra")
    p2 = crear_parcela(session, ana, outra.id, "P2")
    c2 = crear_cultivo(session, ana, p2.id, "Alface")
    t_outra = crear_tratamento_fito(
        session,
        ana,
        outra.id,
        DatosTratamento(
            data_inicio=D,
            data_fin=D,
            cultivos=[LinhaCultivo(c2.id, 0.1)],
            problemas=[Problema("enfermidade", "10")],
            xustificacions=["1"],
            produtos=[LinhaProduto("1", "5", cantidade=1.0)],
            medidas=[],
            aplicadores=[],
        ),
    )
    with pytest.raises(OperacionNonPermitidaError, match="mesma explotación"):
        ligar_tratamento(session, ana, rec, t_outra)

    # Ligar con éxito
    ligar_tratamento(session, ana, rec, tratamento)

    # Xa non pendente
    with pytest.raises(OperacionNonPermitidaError, match="pendente"):
        ligar_tratamento(session, ana, rec, tratamento)

    # Dada de baixa
    rec2 = crear_recomendacion(session, ana, horta.id, **_datos_rec(cultivo, bieito))
    dar_de_baixa_recomendacion(session, ana, rec2)
    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        ligar_tratamento(session, ana, rec2, tratamento)

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita, dar_de_baixa_colleita
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    estado_cultivo,
    estados_cultivos,
    listar_cultivos,
)
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela
from horta.services.tarefas import crear_tarefa


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_admin_pode_crear_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate", variedade="Negro de Santiago")

    assert cultivo.id is not None
    assert cultivo.parcela_id == parcela.id
    assert estado_cultivo(cultivo) == "planificado"
    assert cultivo.variedade == "Negro de Santiago"


def test_editor_pode_crear_cultivo_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_cultivo(session, bea, parcela.id, "Tomate")

    with pytest.raises(PermisoDenegadoError):
        crear_cultivo(session, carlos, parcela.id, "Repolo")


def test_crear_cultivo_en_parcela_inexistente_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError):
        crear_cultivo(session, ana, 9999, "Tomate")


def test_listar_cultivos_devolve_os_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    outra_parcela = crear_parcela(session, ana, outra_horta.id, "Parcela de outra horta")
    crear_cultivo(session, ana, parcela.id, "Tomate")
    crear_cultivo(session, ana, outra_parcela.id, "Repolo")

    cultivos = listar_cultivos(session, ana, horta.id)

    assert [c.especie for c in cultivos] == ["Tomate"]


def test_admin_pode_actualizar_e_eliminar_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")

    actualizado = actualizar_cultivo(session, ana, cultivo, notas="regar ben")
    assert actualizado.notas == "regar ben"

    eliminar_cultivo(session, ana, cultivo)
    assert listar_cultivos(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_cultivo(session, carlos, cultivo, notas="regar ben")

    with pytest.raises(PermisoDenegadoError):
        eliminar_cultivo(session, carlos, cultivo)


@pytest.mark.parametrize("campo", ["parcela_id", "id", "created_at", "campo_inexistente"])
def test_actualizar_cultivo_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    outra_parcela = crear_parcela(session, ana, horta.id, "Outra parcela")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    id_orixinal = cultivo.id

    with pytest.raises(ValueError):
        actualizar_cultivo(session, ana, cultivo, especie="Cambiado", **{campo: outra_parcela.id})

    session.refresh(cultivo)
    assert cultivo.id == id_orixinal
    assert cultivo.parcela_id == parcela.id
    assert cultivo.especie == "Tomate"


def test_eliminar_cultivo_desliga_tarefas_sen_borralas(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tarefa = crear_tarefa(session, ana, horta.id, "Tratar", cultivo_id=cultivo.id)

    eliminar_cultivo(session, ana, cultivo)

    session.refresh(tarefa)
    assert tarefa.cultivo_id is None


def test_cultivo_ligado_ao_codigo_siex(session):
    from horta.models.catalogo import CatalogoVersion, CultivoSiex

    v = CatalogoVersion(catalogo="cultivo", nome_ficheiro="x", sha256="d" * 64, filas=1)
    session.add(v)
    session.flush()
    session.add(CultivoSiex(codigo=99, nome_oficial="PATATA", version_id=v.id))
    session.commit()
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca", cultivo_siex_codigo=99)
    assert cultivo.cultivo_siex_codigo == 99
    actualizar_cultivo(session, ana, cultivo, cultivo_siex_codigo=None)
    assert cultivo.cultivo_siex_codigo is None


def _parcela_de_proba(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    return ana, parcela


@pytest.mark.parametrize(
    ("campos", "mensaxe"),
    [
        ({"superficie_ha": 0.8}, "maior ca da parcela"),
        ({"superficie_ha": 0}, "maior que 0"),
        ({"tipo_inicio": "enxerto"}, "Tipo de inicio"),
        ({"data_inicio": date(2026, 5, 1), "data_fin": date(2026, 4, 1)}, "anterior á de inicio"),
        ({"num_arbores": 10, "marco_plantacion": "4x4"}, "non os dous"),
        ({"data_inicio_conversion": date(2026, 1, 1)}, "en conversión"),
        ({"sistema_cultivo": "999"}, "non existe"),
        ({"dose_sementeira_kg_ha": 200, "densidade_plantas_ha": 40000}, "Indica só un"),
    ],
)
def test_validacions_rea_do_cultivo(session, campos, mensaxe):
    ana, parcela = _parcela_de_proba(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_cultivo(session, ana, parcela.id, "Pataca", **campos)


def test_estado_calculase_coas_datas(session):
    ana, parcela = _parcela_de_proba(session)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca", data_inicio=date(2026, 3, 1))
    assert estado_cultivo(cultivo, hoxe=date(2026, 2, 1)) == "planificado"
    assert estado_cultivo(cultivo, hoxe=date(2026, 6, 1)) == "en_curso"
    actualizar_cultivo(session, ana, cultivo, data_fin=date(2026, 7, 1))
    assert estado_cultivo(cultivo, hoxe=date(2026, 7, 2)) == "rematado"


def test_estado_en_curso_desde_a_primeira_colleita(session):
    """Un cultivo sen data de inicio pero con colleita xa non está planificado."""
    ana, parcela = _parcela_de_proba(session)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    assert estados_cultivos(session, ana, parcela.horta_id)[cultivo.id] == "planificado"
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=120, unidade="kg", lote="",
        persoa_id=1), hoxe=date(2026, 10, 1))
    assert estados_cultivos(session, ana, parcela.horta_id)[cultivo.id] == "en_curso"
    dar_de_baixa_colleita(session, ana, colleita)
    assert estados_cultivos(session, ana, parcela.horta_id)[cultivo.id] == "planificado"

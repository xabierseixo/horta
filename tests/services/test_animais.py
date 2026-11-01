import datetime

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
    ten_rexistros,
)
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.movementos_animais import DatosMovemento, crear_movemento
from horta.services.parcelas import crear_parcela
from horta.services.pastoreos import AnimaisPastoreo, DatosPastoreo, LeiraPastoreo, crear_pastoreo
from horta.services.producions_animais import DatosProducion, crear_producion

_DATA_ALTA = datetime.date(2026, 2, 10)


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


def test_admin_da_horta_pode_crear_animal(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    assert animal.id is not None
    assert animal.horta_id == horta.id
    assert animal.estado == "activo"


def test_editor_pode_crear_animal_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_animal(session, bea, horta.id, "coellos", _DATA_ALTA)

    with pytest.raises(PermisoDenegadoError):
        crear_animal(session, carlos, horta.id, "coellos", _DATA_ALTA)


def test_lector_pode_listar_pero_non_actualizar_nin_eliminar(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    animais = listar_animais(session, carlos, horta.id)
    assert [a.especie for a in animais] == ["galiñas"]

    with pytest.raises(PermisoDenegadoError):
        actualizar_animal(session, carlos, animal, raza="Mos")

    with pytest.raises(PermisoDenegadoError):
        eliminar_animal(session, carlos, animal)


def test_admin_pode_actualizar_e_eliminar_animal(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    actualizado = actualizar_animal(session, ana, animal, raza="Galiña de Mos")
    assert (actualizado.raza, actualizado.cantidade) == ("Galiña de Mos", 6)

    eliminar_animal(session, ana, animal)
    assert listar_animais(session, ana, horta.id) == []


@pytest.mark.parametrize("campo", ["horta_id", "id", "created_at", "campo_inexistente"])
def test_actualizar_animal_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)
    id_orixinal = animal.id

    with pytest.raises(ValueError):
        actualizar_animal(session, ana, animal, cantidade=99, **{campo: outra_horta.id})

    session.refresh(animal)
    assert animal.id == id_orixinal
    assert animal.horta_id == horta.id
    assert animal.cantidade == 6


@pytest.mark.parametrize("cantidade", [0, -2])
def test_cantidade_menor_que_un_ao_crear(session, cantidade):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A cantidade ten que ser polo menos 1"):
        crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=cantidade)


def test_cantidade_e_baixa_non_se_escriben_a_man(session):
    """Saen das entradas e saídas (services.movementos_animais)."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    for campo, valor in (("cantidade", 8), ("data_baixa", datetime.date(2026, 3, 1)),
                         ("estado", "baixa")):
        with pytest.raises(ValueError, match="non editables"):
            actualizar_animal(session, ana, animal, **{campo: valor})

    session.refresh(animal)
    assert (animal.cantidade, animal.data_baixa, animal.estado) == (6, None, "activo")


def _cargar_catalogos_animais(session) -> None:
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="a" * 64, filas=0)
    session.add(version)
    session.flush()
    for catalogo, codigo, texto in (
        ("especie_animal", "01", "Bovinos"),
        ("especie_animal", "06", "Gallinas"),
        ("raza", "10010", "RUBIA GALLEGA"),
        ("raza", "60040", "Galiña de Mos"),
    ):
        session.add(CatalogoValor(
            catalogo=catalogo, codigo=codigo, descricion=texto, version_id=version.id
        ))
    session.commit()


@pytest.mark.parametrize("rexistro", ["coidado", "movemento", "producion", "pastoreo"])
def test_non_se_pode_cambiar_a_especie_se_ten_rexistros(session, rexistro):
    _cargar_catalogos_animais(session)
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    animal = crear_animal(
        session, ana, horta.id, "Vacas", _DATA_ALTA, cantidade=6,
        especie_codigo="01", raza="RUBIA GALLEGA",
    )
    assert not ten_rexistros(session, animal.id)

    if rexistro == "coidado":
        crear_coidado(session, ana, DatosCoidado(
            animal_id=animal.id, data_inicio=_DATA_ALTA, tipo="coidado",
            persoa_id=persoa.id, descricion="Auga",
        ))
    elif rexistro == "movemento":
        crear_movemento(session, ana, DatosMovemento(
            animal_id=animal.id, data=_DATA_ALTA, tipo="saida",
            cantidade=1, persoa_id=persoa.id,
        ))
    elif rexistro == "producion":
        crear_producion(session, ana, DatosProducion(
            animal_id=animal.id, data=_DATA_ALTA, produto="leite",
            cantidade=10, unidade="litros", persoa_id=persoa.id,
        ))
    elif rexistro == "pastoreo":
        parcela = crear_parcela(session, ana, horta.id, "Leira")
        pasto = crear_cultivo(session, ana, parcela.id, "Pasto")
        crear_pastoreo(session, ana, DatosPastoreo(
            horta_id=horta.id, data_inicio=_DATA_ALTA, persoa_id=persoa.id,
            leiras=[LeiraPastoreo(cultivo_id=pasto.id)],
            animais=[AnimaisPastoreo(numero=2, animal_id=animal.id)],
        ))

    assert ten_rexistros(session, animal.id)
    with pytest.raises(
        OperacionNonPermitidaError,
        match="Este grupo xa ten rexistros: a especie non se pode cambiar. "
              "Se te enganaches, dá de alta un grupo novo",
    ):
        actualizar_animal(session, ana, animal, especie_codigo="06")

    # O nome do grupo ou as notas pódense editar mantendo a mesma especie
    actualizar_animal(
        session, ana, animal, especie="Vacas de abaixo", especie_codigo="01", notas="Ben",
    )
    assert (animal.especie, animal.especie_codigo, animal.raza) == (
        "Vacas de abaixo", "01", "RUBIA GALLEGA"
    )


def test_cambiar_especie_sen_rexistros_borra_raza_do_catalogo_doutra_especie(session):
    _cargar_catalogos_animais(session)
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(
        session, ana, horta.id, "Vacas", _DATA_ALTA, cantidade=4,
        especie_codigo="01", raza="RUBIA GALLEGA",
    )

    actualizar_animal(session, ana, animal, especie_codigo="06")
    assert (animal.especie_codigo, animal.raza) == ("06", None)

    # Mesmo se se envía á vez a raza da especie anterior, bórrase
    actualizar_animal(session, ana, animal, especie_codigo="01", raza="RUBIA GALLEGA")
    assert (animal.especie_codigo, animal.raza) == ("01", "RUBIA GALLEGA")
    actualizar_animal(session, ana, animal, especie_codigo="06", raza="RUBIA GALLEGA")
    assert (animal.especie_codigo, animal.raza) == ("06", None)

    # Se a raza é da nova especie ou é texto libre fóra do catálogo, consérvase
    actualizar_animal(session, ana, animal, especie_codigo="01", raza="Caseira")
    actualizar_animal(session, ana, animal, especie_codigo="06")
    assert (animal.especie_codigo, animal.raza) == ("06", "Caseira")
    actualizar_animal(session, ana, animal, especie_codigo="01")
    actualizar_animal(session, ana, animal, especie_codigo="06", raza="Galiña de Mos")
    assert (animal.especie_codigo, animal.raza) == ("06", "Galiña de Mos")

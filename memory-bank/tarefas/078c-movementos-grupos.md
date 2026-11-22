# Tarefa 078c — Entradas e saídas de animais (4/11): grupos con especie e cantidade dos movementos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 078a e 078b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O grupo de animais garda a especie oficial; ao crealo, os seus animais quedan como movemento inicial; a cantidade e a baixa xa non se escriben a man; un grupo con movementos non se borra. As probas que había adáptanse. Deseño: `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/animais.py`
- `tests/services/test_animais.py`
- `tests/services/test_en_regra.py`
- `tests/services/test_coidados_animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/animais.py`

Antes:
```python
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.coidados_animais import ten_coidados
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_animal. Quedan fóra id,
# horta_id e created_at: mover un animal a outra horta saltaría o control
# de permisos, que se fai coa horta_id actual.
CAMPOS_EDITABLES_ANIMAL = frozenset(
    {"especie", "raza", "cantidade", "data_alta", "data_baixa", "estado", "notas"}
)


def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 1:
            raise OperacionNonPermitidaError("A cantidade ten que ser polo menos 1")


def _validar_datas(data_alta: date | None, data_baixa: date | None) -> None:
    if data_alta is not None and data_baixa is not None and data_baixa < data_alta:
        raise OperacionNonPermitidaError("A data de baixa non pode ser anterior á de alta")


def crear_animal(
    session: Session,
    actor: Usuario,
    horta_id: int,
    especie: str,
    data_alta: date,
    **campos: Any,
) -> Animal:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    _validar_datas(data_alta, campos.get("data_baixa"))
    estado = campos.pop("estado", "activo")
    animal = Animal(
        horta_id=horta_id, especie=especie, data_alta=data_alta, estado=estado, **campos
    )
    session.add(animal)
    session.commit()
    return animal


def actualizar_animal(
    session: Session,
    actor: Usuario,
    animal: Animal,
    **cambios: Any,
) -> Animal:
    non_editables = set(cambios) - CAMPOS_EDITABLES_ANIMAL
    if non_editables:
        raise ValueError(f"Campos non editables nun animal: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(cambios)
    _validar_datas(
        cambios.get("data_alta", animal.data_alta),
        cambios.get("data_baixa", animal.data_baixa),
    )
    for campo, valor in cambios.items():
        setattr(animal, campo, valor)
    session.commit()
    return animal


def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if ten_coidados(session, animal.id):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados apuntados e debe conservarse (obriga legal): dálle de baixa")
    session.query(Tarefa).filter_by(animal_id=animal.id).update({"animal_id": None})
```

Despois:
```python
from horta.models.movemento_animal import MovementoAnimal
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.coidados_animais import ten_coidados
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.movementos_animais import (
    INICIAL,
    cambiar_data_alta,
    crear_inicial,
    recalcular,
    ten_movementos,
)

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_animal. Quedan fóra id,
# horta_id e created_at: mover un animal a outra horta saltaría o control
# de permisos, que se fai coa horta_id actual. A cantidade, a baixa e o
# estado saen das entradas e saídas (services.movementos_animais).
CAMPOS_EDITABLES_ANIMAL = frozenset(
    {"especie", "especie_codigo", "raza", "data_alta", "notas"}
)

# As especies de granxa do catálogo oficial ESPECIE_ANIMAL, en galego
ESPECIES: dict[str, str] = {
    "06": "Galiñas", "16": "Coellos", "18": "Abellas", "03": "Ovellas", "04": "Cabras",
    "02": "Porcos", "01": "Vacas", "05": "Cabalos e burros", "07": "Pavos",
    "08": "Pintadas", "09": "Patos", "10": "Gansos", "11": "Paspallás", "12": "Pombas",
    "13": "Faisáns", "14": "Perdices", "15": "Avestruces e outras ratites", "17": "Lebres",
    "23": "Cervos", "24": "Corzos", "25": "Gamos", "26": "Xabarís", "27": "Caracois",
    "28": "Ras",
}


def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 1:
            raise OperacionNonPermitidaError("A cantidade ten que ser polo menos 1")


def _validar_especie(session: Session, codigo: str | None, na_data: date) -> None:
    if codigo is not None:
        if codigo not in ESPECIES:
            raise OperacionNonPermitidaError("Escolle a especie da lista")
        validar_codigo(session, "especie_animal", codigo, na_data)


def crear_animal(
    session: Session,
    actor: Usuario,
    horta_id: int,
    especie: str,
    data_alta: date,
    **campos: Any,
) -> Animal:
    """Un grupo de animais. A cantidade inicial queda como o seu primeiro movemento."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    _validar_especie(session, campos.get("especie_codigo"), data_alta)
    cantidade = campos.pop("cantidade", 1)
    for derivado in ("estado", "data_baixa"):
        campos.pop(derivado, None)
    animal = Animal(horta_id=horta_id, especie=especie, data_alta=data_alta,
                    cantidade=cantidade, estado="activo", **campos)
    session.add(animal)
    session.flush()
    crear_inicial(session, animal, cantidade)
    recalcular(session, animal)
    session.commit()
    return animal


def actualizar_animal(
    session: Session,
    actor: Usuario,
    animal: Animal,
    **cambios: Any,
) -> Animal:
    non_editables = set(cambios) - CAMPOS_EDITABLES_ANIMAL
    if non_editables:
        raise ValueError(f"Campos non editables nun animal: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    data_alta = cambios.pop("data_alta", animal.data_alta)
    _validar_especie(session, cambios.get("especie_codigo"), data_alta)
    if data_alta != animal.data_alta:
        primeiro = (session.query(MovementoAnimal)
                    .filter(MovementoAnimal.animal_id == animal.id,
                            MovementoAnimal.tipo != INICIAL, MovementoAnimal.baixa.is_(False))
                    .order_by(MovementoAnimal.data).first())
        if primeiro is not None and primeiro.data < data_alta:
            raise OperacionNonPermitidaError(
                f"Hai entradas ou saídas desde o {primeiro.data:%d/%m/%Y}: "
                "a data de alta non pode ser posterior")
        cambiar_data_alta(session, animal, data_alta)
    for campo, valor in cambios.items():
        setattr(animal, campo, valor)
    recalcular(session, animal)
    session.commit()
    return animal


def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if ten_coidados(session, animal.id) or ten_movementos(session, animal.id):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados ou entradas e saídas apuntados e debe conservarse "
            "(obriga legal). Se xa non ten animais, apunta a súa saída ou morte")
    session.query(Tarefa).filter_by(animal_id=animal.id).update({"animal_id": None})
    session.query(MovementoAnimal).filter_by(animal_id=animal.id).delete()
```

### Paso 2 — `tests/services/test_animais.py`

Antes:
```python
        actualizar_animal(session, carlos, animal, cantidade=10)

    with pytest.raises(PermisoDenegadoError):
        eliminar_animal(session, carlos, animal)


def test_admin_pode_actualizar_e_eliminar_animal(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    actualizado = actualizar_animal(session, ana, animal, cantidade=8)
    assert actualizado.cantidade == 8

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


def test_cantidade_menor_que_un_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    with pytest.raises(ValueError, match="A cantidade ten que ser polo menos 1"):
        actualizar_animal(session, ana, animal, cantidade=0)

    session.refresh(animal)
    assert animal.cantidade == 6


def test_baixa_anterior_a_alta_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A data de baixa non pode ser anterior"):
        crear_animal(
            session,
            ana,
            horta.id,
            "galiñas",
            _DATA_ALTA,
            data_baixa=datetime.date(2026, 1, 1),
        )


def test_baixa_anterior_a_alta_ao_actualizar(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA)

    with pytest.raises(ValueError, match="A data de baixa non pode ser anterior"):
        actualizar_animal(session, ana, animal, data_baixa=datetime.date(2026, 1, 1))

    session.refresh(animal)
    assert animal.data_baixa is None
```

Despois:
```python
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
```

### Paso 3 — `tests/services/test_en_regra.py`

Antes:
```python
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import actualizar_animal, crear_animal
from horta.services.en_regra import requisitos_en_regra
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.persoas import crear_persoa


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


def test_non_profesional_non_ten_requisitos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    assert requisitos_en_regra(session, ana, horta) == []


def test_profesional_sen_datos_ten_tres_pendentes(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == [
        "NIF do titular",
        "Inscrición no REAGA",
        "Aplicador con carné ROPO en vigor",
    ]
    assert not any(r.cumprido for r in requisitos)


def test_profesional_completo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    actualizar_horta(session, ana, horta, titular_nif="12345678Z", codigo_reaga="ES150010000001")
    crear_persoa(
        session,
        ana,
        horta.id,
        "Xan",
        e_aplicador=True,
        ropo_numero="1",
        ropo_caducidade=date(2030, 1, 1),
    )
    requisitos = requisitos_en_regra(session, ana, horta, hoxe=date(2026, 10, 22))
    assert all(r.cumprido for r in requisitos)


def test_con_animais_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=10)
    textos = [r.texto for r in requisitos_en_regra(session, ana, horta)]
    assert "Código REGA do gando" in textos


def test_non_profesional_con_galinas_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=5)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == ["Código REGA do gando"]
    assert not requisitos[0].cumprido


def test_animais_de_baixa_non_contan(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    animal = crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=5)
    actualizar_animal(session, ana, animal, data_baixa=date(2026, 6, 1))
```

Despois:
```python
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.en_regra import requisitos_en_regra
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.movementos_animais import DatosMovemento, crear_movemento
from horta.services.persoas import crear_persoa


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


def test_non_profesional_non_ten_requisitos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    assert requisitos_en_regra(session, ana, horta) == []


def test_profesional_sen_datos_ten_tres_pendentes(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == [
        "NIF do titular",
        "Inscrición no REAGA",
        "Aplicador con carné ROPO en vigor",
    ]
    assert not any(r.cumprido for r in requisitos)


def test_profesional_completo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    actualizar_horta(session, ana, horta, titular_nif="12345678Z", codigo_reaga="ES150010000001")
    crear_persoa(
        session,
        ana,
        horta.id,
        "Xan",
        e_aplicador=True,
        ropo_numero="1",
        ropo_caducidade=date(2030, 1, 1),
    )
    requisitos = requisitos_en_regra(session, ana, horta, hoxe=date(2026, 10, 22))
    assert all(r.cumprido for r in requisitos)


def test_con_animais_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=10)
    textos = [r.texto for r in requisitos_en_regra(session, ana, horta)]
    assert "Código REGA do gando" in textos


def test_non_profesional_con_galinas_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=5)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == ["Código REGA do gando"]
    assert not requisitos[0].cumprido


def test_animais_de_baixa_non_contan(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    animal = crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=5)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    crear_movemento(session, ana, DatosMovemento(
        animal_id=animal.id, data=date(2026, 6, 1), tipo="morte", cantidade=5,
        persoa_id=persoa.id), hoxe=date(2026, 6, 1))
```

### Paso 4 — `tests/services/test_coidados_animais.py`

Antes:
```python
from horta.services.animais import actualizar_animal, crear_animal, eliminar_animal
from horta.services.coidados_animais import (
    DatosCoidado,
    actualizar_coidado,
    crear_coidado,
    dar_de_baixa_coidado,
    en_tempo_espera,
    fin_tempo_espera,
    listar_coidados,
)
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.tarefas import crear_tarefa, facer_tarefa

HOXE = date(2026, 10, 28)


def _escenario(session, nome="Horta"):
    ana = session.query(Usuario).filter_by(email="ana@example.com").one_or_none()
    if ana is None:
        ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
        session.add(ana)
        session.commit()
    horta = crear_horta(session, ana, nome)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=12)
    return ana, horta, persoa, galinas


def _medicamento(galinas, persoa, **campos):
    datos = {"animal_id": galinas.id, "data_inicio": date(2026, 10, 20), "tipo": "medicamento",
             "persoa_id": persoa.id, "medicamento": "Oxitetraciclina", "tempo_espera_dias": 7,
             "duracion_dias": 5, "num_animais": 3, "veterinario": "Marta Vázquez",
             "receita": "R-123"}
    datos.update(campos)
    return DatosCoidado(**datos)


def test_apuntar_un_coidado_diario(session):
    ana, horta, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Limpar o galiñeiro", horas=1.5), hoxe=HOXE)
    assert (co.horta_id, co.data_fin, co.creado_por) == (horta.id, HOXE, ana.id)
    with pytest.raises(OperacionNonPermitidaError, match="Describe"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id),
            hoxe=HOXE)


def test_quen_o_fixo_e_obrigatorio(session):
    ana, _, _, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="quen"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=None,
            descricion="Dar de comer"), hoxe=HOXE)


def test_o_medicamento_pide_o_tempo_de_espera_aínda_que_sexa_cero(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tempo de espera"):
        crear_coidado(session, ana, _medicamento(galinas, persoa, tempo_espera_dias=None),
                      hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="medicamento"):
        crear_coidado(session, ana, _medicamento(galinas, persoa, medicamento=None), hoxe=HOXE)
    co = crear_coidado(session, ana, _medicamento(galinas, persoa, tempo_espera_dias=0),
                       hoxe=HOXE)
    assert co.tempo_espera_dias == 0


def test_cada_tipo_garda_so_os_seus_datos(session):
    ana, _, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id,
        visitante="Veterinaria da ADS", descricion="Revisión", matricula="1234ABC",
        medicamento="Non vai", num_animais=2), hoxe=HOXE)
    assert (co.visitante, co.matricula, co.medicamento, co.num_animais) == (
        "Veterinaria da ADS", "1234ABC", None, None)
    with pytest.raises(OperacionNonPermitidaError, match="quen veu"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id),
            hoxe=HOXE)


def test_os_animais_afectados_non_poden_ser_mais_ca_o_grupo(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="12 animais"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="enfermidade", persoa_id=persoa.id,
            descricion="Tosen", num_animais=13), hoxe=HOXE)


def test_o_grupo_ten_que_ser_da_explotacion_e_estar_de_alta(session):
    ana, horta, persoa, galinas = _escenario(session)
    _, _, _, alleas = _escenario(session, "Outra")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Auga"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        actualizar_coidado(session, ana, co, DatosCoidado(
            animal_id=alleas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
            descricion="Auga"), hoxe=HOXE)
    actualizar_animal(session, ana, galinas, data_baixa=date(2026, 10, 1), estado="baixa")
    with pytest.raises(OperacionNonPermitidaError, match="de baixa"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
            descricion="Auga"), hoxe=HOXE)


def test_tempo_de_espera(session):
    ana, horta, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, _medicamento(galinas, persoa), hoxe=HOXE)
    # 5 días desde o 20 (última o 24) + 7 días de espera
    assert fin_tempo_espera(co) == date(2026, 10, 31)
    assert en_tempo_espera(session, ana, horta.id, hoxe=HOXE) == {galinas.id: date(2026, 10, 31)}
    assert en_tempo_espera(session, ana, horta.id, hoxe=date(2026, 11, 1)) == {}
    dar_de_baixa_coidado(session, ana, co)
    assert listar_coidados(session, ana, horta.id) == []
    assert en_tempo_espera(session, ana, horta.id, hoxe=HOXE) == {}


def test_un_grupo_con_coidados_non_se_borra(session):
    ana, horta, persoa, galinas = _escenario(session)
    coellos = crear_animal(session, ana, horta.id, "Coellos", date(2026, 1, 1))
    tarefa = crear_tarefa(session, ana, horta.id, "Vacinar", animal_id=coellos.id)
    eliminar_animal(session, ana, coellos)
    assert tarefa.animal_id is None
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Auga"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="dálle de baixa"):
```

Despois:
```python
from horta.services.animais import crear_animal, eliminar_animal
from horta.services.coidados_animais import (
    DatosCoidado,
    actualizar_coidado,
    crear_coidado,
    dar_de_baixa_coidado,
    en_tempo_espera,
    fin_tempo_espera,
    listar_coidados,
)
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.movementos_animais import DatosMovemento, crear_movemento
from horta.services.tarefas import crear_tarefa, facer_tarefa

HOXE = date(2026, 10, 28)


def _escenario(session, nome="Horta"):
    ana = session.query(Usuario).filter_by(email="ana@example.com").one_or_none()
    if ana is None:
        ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
        session.add(ana)
        session.commit()
    horta = crear_horta(session, ana, nome)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=12)
    return ana, horta, persoa, galinas


def _medicamento(galinas, persoa, **campos):
    datos = {"animal_id": galinas.id, "data_inicio": date(2026, 10, 20), "tipo": "medicamento",
             "persoa_id": persoa.id, "medicamento": "Oxitetraciclina", "tempo_espera_dias": 7,
             "duracion_dias": 5, "num_animais": 3, "veterinario": "Marta Vázquez",
             "receita": "R-123"}
    datos.update(campos)
    return DatosCoidado(**datos)


def test_apuntar_un_coidado_diario(session):
    ana, horta, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Limpar o galiñeiro", horas=1.5), hoxe=HOXE)
    assert (co.horta_id, co.data_fin, co.creado_por) == (horta.id, HOXE, ana.id)
    with pytest.raises(OperacionNonPermitidaError, match="Describe"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id),
            hoxe=HOXE)


def test_quen_o_fixo_e_obrigatorio(session):
    ana, _, _, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="quen"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=None,
            descricion="Dar de comer"), hoxe=HOXE)


def test_o_medicamento_pide_o_tempo_de_espera_aínda_que_sexa_cero(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tempo de espera"):
        crear_coidado(session, ana, _medicamento(galinas, persoa, tempo_espera_dias=None),
                      hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="medicamento"):
        crear_coidado(session, ana, _medicamento(galinas, persoa, medicamento=None), hoxe=HOXE)
    co = crear_coidado(session, ana, _medicamento(galinas, persoa, tempo_espera_dias=0),
                       hoxe=HOXE)
    assert co.tempo_espera_dias == 0


def test_cada_tipo_garda_so_os_seus_datos(session):
    ana, _, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id,
        visitante="Veterinaria da ADS", descricion="Revisión", matricula="1234ABC",
        medicamento="Non vai", num_animais=2), hoxe=HOXE)
    assert (co.visitante, co.matricula, co.medicamento, co.num_animais) == (
        "Veterinaria da ADS", "1234ABC", None, None)
    with pytest.raises(OperacionNonPermitidaError, match="quen veu"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id),
            hoxe=HOXE)


def test_os_animais_afectados_non_poden_ser_mais_ca_o_grupo(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="12 animais"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="enfermidade", persoa_id=persoa.id,
            descricion="Tosen", num_animais=13), hoxe=HOXE)


def test_o_grupo_ten_que_ser_da_explotacion_e_estar_de_alta(session):
    ana, horta, persoa, galinas = _escenario(session)
    _, _, _, alleas = _escenario(session, "Outra")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Auga"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        actualizar_coidado(session, ana, co, DatosCoidado(
            animal_id=alleas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
            descricion="Auga"), hoxe=HOXE)
    crear_movemento(session, ana, DatosMovemento(
        animal_id=galinas.id, data=date(2026, 10, 1), tipo="saida", cantidade=12,
        persoa_id=persoa.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="de baixa"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
            descricion="Auga"), hoxe=HOXE)


def test_tempo_de_espera(session):
    ana, horta, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, _medicamento(galinas, persoa), hoxe=HOXE)
    # 5 días desde o 20 (última o 24) + 7 días de espera
    assert fin_tempo_espera(co) == date(2026, 10, 31)
    assert en_tempo_espera(session, ana, horta.id, hoxe=HOXE) == {galinas.id: date(2026, 10, 31)}
    assert en_tempo_espera(session, ana, horta.id, hoxe=date(2026, 11, 1)) == {}
    dar_de_baixa_coidado(session, ana, co)
    assert listar_coidados(session, ana, horta.id) == []
    assert en_tempo_espera(session, ana, horta.id, hoxe=HOXE) == {}


def test_un_grupo_con_coidados_non_se_borra(session):
    ana, horta, persoa, galinas = _escenario(session)
    coellos = crear_animal(session, ana, horta.id, "Coellos", date(2026, 1, 1))
    tarefa = crear_tarefa(session, ana, horta.id, "Vacinar", animal_id=coellos.id)
    eliminar_animal(session, ana, coellos)
    assert tarefa.animal_id is None
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Auga"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="debe conservarse"):
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Entradas e saídas de animais (4/11): grupos con especie e cantidade dos movementos: feito.

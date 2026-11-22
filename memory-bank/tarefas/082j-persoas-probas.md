# Tarefa 082j — Persoas (11/11): probas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082i. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Probas dos papeis, de crear persoas dende os formularios e do paso dos textos antigos a fichas. Probado no navegador (escritorio e móbil) o 2026-10-28. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `tests/services/test_persoas_papeis.py` (**ficheiro novo**)
- `tests/test_migracion_persoas.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `tests/services/test_persoas_papeis.py`

Contido completo:
```python
"""Unha soa lista de persoas e entidades, con papeis
(docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.caderno import xerar_caderno
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.persoas import (
    actualizar_persoa,
    crear_contacto,
    crear_persoa,
    listar_persoas,
    listar_quen,
    persoa_co_papel,
    titular_da_horta,
)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_quen_crea_a_explotacion_traballa_nela(session):
    ana, horta = _escenario(session)
    [persoa] = listar_persoas(session, ana, horta.id)
    assert persoa.papeis == {"traballador"}


def test_unha_persoa_pode_ter_varios_papeis(session):
    ana, horta = _escenario(session)
    xan = crear_persoa(session, ana, horta.id, "Xan", papeis={"traballador", "cliente"})
    assert xan.papeis == {"traballador", "cliente"}
    actualizar_persoa(session, ana, xan, papeis={"cliente"})
    assert xan.papeis == {"cliente"}
    assert listar_persoas(session, ana, horta.id, papel="cliente") == [xan]


def test_so_un_titular(session):
    ana, horta = _escenario(session)
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"})
    with pytest.raises(OperacionNonPermitidaError, match="xa ten titular"):
        crear_persoa(session, ana, horta.id, "Xan", papeis={"titular"})
    assert titular_da_horta(session, horta.id).nome == "Ana"


def test_nif_de_persoa_e_de_entidade(session):
    ana, horta = _escenario(session)
    crear_persoa(session, ana, horta.id, "Ana", nif="12345678z")
    crear_persoa(session, ana, horta.id, "Coop", tipo="entidade", nif="F15000000")
    with pytest.raises(OperacionNonPermitidaError, match="NIF"):
        crear_persoa(session, ana, horta.id, "Coop 2", tipo="entidade", nif="12345678Z")


def test_asesor_persoa_precisa_ropo_e_a_entidade_non(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="ROPO"):
        crear_persoa(session, ana, horta.id, "Lúa", papeis={"asesor"})
    crear_persoa(session, ana, horta.id, "ATRIA", tipo="entidade", papeis={"asesor"},
                 num_asesoramento="AT-1")


def test_quen_o_fixo_e_o_equipo_ou_unha_empresa_de_servizos(session):
    ana, horta = _escenario(session)
    cliente = crear_contacto(session, ana, horta.id, "Bar Central", "cliente")
    servizos = crear_contacto(session, ana, horta.id, "Abonos SL", "servizos")
    quen = listar_quen(session, ana, horta.id)
    assert servizos in quen and cliente not in quen


def test_crear_dende_un_formulario_reutiliza_a_persoa(session):
    ana, horta = _escenario(session)
    xan = crear_contacto(session, ana, horta.id, "Xan da Ponte", "cliente", nif="12345678Z")
    # O mesmo NIF (ou o mesmo nome) é a mesma persoa, e gaña o papel novo
    assert crear_contacto(session, ana, horta.id, "Xan", "provedor", nif="12345678Z") is xan
    assert crear_contacto(session, ana, horta.id, "xan da ponte ", "explotacion") is xan
    assert xan.papeis == {"cliente", "provedor", "explotacion"}


def test_a_persoa_dun_traballo_ten_que_ser_da_explotacion(session):
    ana, horta = _escenario(session)
    allea = crear_contacto(session, ana, crear_horta(session, ana, "Outra").id, "X", None)
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        persoa_co_papel(session, horta.id, allea.id, "cliente")


def test_caderno_titular_entidade_e_o_seu_representante(session):
    ana, horta = _escenario(session)
    crear_persoa(session, ana, horta.id, "Agro Ulla SL", tipo="entidade", nif="B15000000",
                 papeis={"titular"})
    crear_persoa(session, ana, horta.id, "Rosa", apelidos="Vilar", nif="12345678Z",
                 papeis={"representante"})
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [[c for c in f if c not in (None, "")] for f in
             libro["1 Información xeral"].iter_rows(values_only=True)]
    assert ["Nome e apelidos ou razón social", "Agro Ulla SL"] in filas
    assert ["Nome e apelidos", "Rosa Vilar"] in filas


def test_o_medicamento_garda_veterinario_e_provedor(session):
    ana, horta = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    marta = crear_contacto(session, ana, horta.id, "Marta Vázquez", None)
    agrovet = crear_contacto(session, ana, horta.id, "Agrovet Lalín", None)
    [quen] = listar_persoas(session, ana, horta.id, papel="traballador")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=quen.id, medicamento="Oxitetraciclina", tempo_espera_dias=7,
        veterinario_id=marta.id, provedor_id=agrovet.id), hoxe=date(2026, 10, 28))
    assert (co.veterinario_id, co.provedor_id) == (marta.id, agrovet.id)
    # Quedan co papel que fixeron, para atopalos despois en Contactos
    assert marta.papeis == {"veterinario"} and agrovet.papeis == {"provedor"}
```

### Paso 2 — crear o ficheiro `tests/test_migracion_persoas.py`

Contido completo:
```python
"""Os textos con persoas e empresas de fóra pasan a fichas de persoa, sen perder nada e sen
duplicar (docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md)."""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]


def _alembic(url: str, *args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=RAIZ,
                   env={**os.environ, "HORTA_DATABASE_URL": url}, check=True,
                   capture_output=True)


def test_os_textos_pasan_a_persoas(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "b2e4a6c8d0f5")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO horta (id, nome, uso_profesional, asesoramento_fertilizacion, "
            "titular_nome, titular_nif, asesoramento_nome, asesoramento_num, created_at) "
            "VALUES (1, 'Horta', 1, 0, 'Agro Ulla SL', 'B15000000', 'ATRIA Ulla', 'AT-7', "
            "'2026-01-01')"))
        conn.execute(text(
            "INSERT INTO persoa (id, horta_id, nome, e_aplicador, e_asesor, e_titular, "
            "e_traballador, activa, discapacidade) VALUES (1, 1, 'Xan', 1, 0, 0, 0, 1, 0), "
            "(2, 1, 'Ana', 0, 0, 0, 0, 1, 0)"))
        conn.execute(text(
            "INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
            "nif_arrendador, created_at) VALUES (1, 1, 'P1', 'activa', 0, '12345678Z', "
            "'2026-01-01')"))
        conn.execute(text(
            "INSERT INTO fertilizante (id, horta_id, nome, material, liquido, activo, "
            "provedor_nome, provedor_nif, created_at) VALUES "
            "(1, 1, 'Esterco', '5', 0, 1, 'Granxa do Monte', '33333333P', '2026-01-01'), "
            "(2, 1, 'Compost', '13', 0, 1, NULL, '33333333P', '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO analise (id, horta_id, material_analizado, data_mostraxe, "
            "laboratorio, laboratorio_nif, baixa, created_at) VALUES "
            "(1, 1, '3', '2026-03-01', 'Laboratorio Agrario', 'Q1500000A', 0, '2026-01-01')"))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        persoas = {fila.nome: fila for fila in conn.execute(text(
            "SELECT p.id, p.nome, p.tipo, p.nif, p.num_asesoramento, "
            "group_concat(pp.papel) AS papeis FROM persoa p "
            "LEFT JOIN persoa_papel pp ON pp.persoa_id = p.id GROUP BY p.id"))}
        provedores = conn.execute(text(
            "SELECT DISTINCT provedor_id FROM fertilizante")).scalars().all()
        laboratorio = conn.execute(text("SELECT laboratorio_id FROM analise")).scalar()
        arrendador = conn.execute(text("SELECT arrendador_id FROM parcela")).scalar()
    # Os papeis de antes; quen non tiña función traballa na explotación
    assert persoas["Xan"].papeis == "aplicador"
    assert persoas["Ana"].papeis == "traballador"
    # O titular e a entidade de asesoramento da explotación
    assert (persoas["Agro Ulla SL"].tipo, persoas["Agro Ulla SL"].papeis) == ("entidade",
                                                                              "titular")
    assert (persoas["ATRIA Ulla"].num_asesoramento, persoas["ATRIA Ulla"].papeis) == (
        "AT-7", "asesor")
    # O mesmo NIF é a mesma persoa: os dous abonos van ao mesmo provedor
    assert provedores == [persoas["Granxa do Monte"].id]
    assert laboratorio == persoas["Laboratorio Agrario"].id
    assert persoas["Laboratorio Agrario"].tipo == "entidade"
    assert arrendador == persoas["Arrendador 12345678Z"].id
    # E pódese volver atrás sen perder os textos
    _alembic(url, "downgrade", "b2e4a6c8d0f5")
    with engine.connect() as conn:
        horta = conn.execute(text("SELECT titular_nome, titular_nif FROM horta")).one()
        nif = conn.execute(text("SELECT nif_arrendador FROM parcela")).scalar()
    assert tuple(horta) == ("Agro Ulla SL", "B15000000") and nif == "12345678Z"
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (11/11): probas: feito.

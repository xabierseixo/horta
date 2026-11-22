# Tarefa 083d — Lotes (5/5): probas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 083c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Probas dos lotes e das saídas e do paso dos lotes de texto. Probado no navegador (escritorio e móbil) o 2026-10-28. Deseño: `docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md` (paso 4 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `tests/services/test_lotes.py` (**ficheiro novo**)
- `tests/test_migracion_lotes.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `tests/services/test_lotes.py`

Contido completo:
```python
"""Lotes e saídas (docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md)."""

from datetime import date

import pytest

from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.colleitas import (
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    dar_de_baixa_colleita,
)
from horta.services.cultivos import crear_cultivo
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.lotes import (
    DatosSaida,
    actualizar_lote,
    avisos_saida,
    converter,
    crear_saida,
    dar_de_baixa_saida,
    listar_lotes,
    queda,
    resumo_lotes,
)
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
from horta.services.producions_animais import DatosProducion, crear_producion
from horta.services.tarefas import crear_tarefa

HOXE = date(2026, 10, 28)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "Leira").id,
                            "Pataca")
    return ana, horta, quen, cultivo


def _colleita(session, ana, cultivo, quen, cantidade=100.0, unidade="kg", lote="L-1"):
    return crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=cantidade, unidade=unidade,
        lote=lote, persoa_id=quen.id), hoxe=HOXE)


def _saida(colleita, quen, **cambios):
    datos = {"lote_id": colleita.lote_id, "data": date(2026, 9, 5), "tipo": "casa",
             "cantidade": 10, "unidade": "kg", "persoa_id": quen.id}
    datos.update(cambios)
    return DatosSaida(**datos)


def test_converter_unidades():
    assert converter(2, "t", "kg") == 2000
    assert converter(3, "ducias", "unidades") == 36
    assert converter(1, "kg", "unidades") is None


def test_o_que_queda_no_lote(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    _colleita(session, ana, cultivo, quen, cantidade=0.05, unidade="t")
    crear_saida(session, ana, _saida(colleita, quen, cantidade=30), hoxe=HOXE)
    [lote] = listar_lotes(session, ana, horta.id)
    assert resumo_lotes(session, ana, horta.id)[lote.id] == (150, 30, 120)
    with pytest.raises(OperacionNonPermitidaError, match="só quedan 120"):
        crear_saida(session, ana, _saida(colleita, quen, cantidade=121), hoxe=HOXE)


def test_cada_tipo_garda_so_os_seus_datos(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    bar = crear_contacto(session, ana, horta.id, "Bar Central", "cliente")
    venda = crear_saida(session, ana, _saida(
        colleita, quen, tipo="venda", canle="mercado", lugar="Lalín", comprador_id=bar.id,
        importe=25), hoxe=HOXE)
    assert (venda.canle, venda.lugar, venda.importe) == ("mercado", "Lalín", 25)
    casa = crear_saida(session, ana, _saida(colleita, quen, canle="mercado", importe=5),
                       hoxe=HOXE)
    assert (casa.canle, casa.importe) == (None, None)


@pytest.mark.parametrize("cambios, erro", [
    ({"tipo": "venda"}, "a quen"),
    ({"tipo": "venda", "canle": "tenda"}, "tenda"),
    ({"data": date(2026, 8, 1)}, "anterior"),
    ({"data": date(2026, 10, 29)}, "futura"),
    ({"cantidade": 0}, "maior que 0"),
    ({"unidade": "unidades"}, "vai en kg"),
    ({"persoa_id": None}, "quen"),
])
def test_validacions(session, cambios, erro):
    ana, _, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    with pytest.raises(OperacionNonPermitidaError, match=erro):
        crear_saida(session, ana, _saida(colleita, quen, **cambios), hoxe=HOXE)


def test_os_ovos_non_van_a_tendas_e_avisa_do_maximo(session):
    ana, horta, quen, _ = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=50)
    ovos = crear_producion(session, ana, DatosProducion(
        animal_id=galinas.id, data=date(2026, 9, 1), produto="ovos", cantidade=1100,
        unidade="ducias", persoa_id=quen.id), hoxe=HOXE)
    tenda = crear_contacto(session, ana, horta.id, "Ultramarinos", "cliente")
    with pytest.raises(OperacionNonPermitidaError, match="ovos"):
        crear_saida(session, ana, DatosSaida(
            lote_id=ovos.lote_id, data=date(2026, 9, 2), tipo="venda", cantidade=10,
            unidade="ducias", canle="tenda", comprador_id=tenda.id, persoa_id=quen.id),
            hoxe=HOXE)
    datos = DatosSaida(lote_id=ovos.lote_id, data=date(2026, 9, 2), tipo="venda",
                       cantidade=1050, unidade="ducias", canle="mercado", persoa_id=quen.id)
    [aviso] = avisos_saida(session, ana, datos)
    assert "1050 ducias" in aviso and "1000 ducias" in aviso


def test_maximo_en_invernadoiro(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen, cantidade=25, unidade="t")
    [lote] = listar_lotes(session, ana, horta.id)
    actualizar_lote(session, ana, lote, "hortalizas", protexido=False)
    venda = _saida(colleita, quen, tipo="venda", canle="explotacion", cantidade=21,
                   unidade="t")
    assert avisos_saida(session, ana, venda)
    actualizar_lote(session, ana, lote, "hortalizas", protexido=True)
    assert avisos_saida(session, ana, venda) == []


def test_aviso_tempo_de_espera(session):
    ana, horta, quen, _ = _escenario(session)
    vacas = crear_animal(session, ana, horta.id, "Vacas", date(2026, 1, 1), cantidade=3)
    crear_coidado(session, ana, DatosCoidado(
        animal_id=vacas.id, data_inicio=date(2026, 9, 1), tipo="medicamento",
        persoa_id=quen.id, medicamento="Penicilina", tempo_espera_dias=10), hoxe=HOXE)
    leite = crear_producion(session, ana, DatosProducion(
        animal_id=vacas.id, data=date(2026, 9, 3), produto="leite", cantidade=40,
        unidade="litros", persoa_id=quen.id), hoxe=HOXE)
    avisos = avisos_saida(session, ana, DatosSaida(
        lote_id=leite.lote_id, data=date(2026, 9, 4), tipo="casa", cantidade=5,
        unidade="litros", persoa_id=quen.id))
    assert any("tempo de espera" in a for a in avisos)


def test_unha_entrada_non_baixa_por_debaixo_do_saido(session):
    ana, _, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    saida = crear_saida(session, ana, _saida(colleita, quen, cantidade=80), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa saíron 80"):
        actualizar_colleita(session, ana, colleita, DatosColleita(
            cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=50, unidade="kg",
            lote="L-1", persoa_id=quen.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa saíron"):
        dar_de_baixa_colleita(session, ana, colleita)
    dar_de_baixa_saida(session, ana, saida)
    dar_de_baixa_colleita(session, ana, colleita)
    assert queda(session, saida_lote(session, saida)) == 0


def saida_lote(session, saida):
    from horta.models.lote import Lote
    return session.get(Lote, saida.lote_id)


def test_diario_e_tarefa(session):
    ana, horta, quen, cultivo = _escenario(session)
    colleita = _colleita(session, ana, cultivo, quen)
    bar = crear_contacto(session, ana, horta.id, "Bar Central", "cliente")
    crear_saida(session, ana, _saida(colleita, quen, tipo="venda", canle="domicilio",
                                     comprador_id=bar.id), hoxe=HOXE)
    [traballo] = [t for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)
                  if t.tipo == "lote_saida"]
    assert traballo.que == "Venda: 10 kg de Pataca · lote L-1" and traballo.onde == "Bar Central"
    tarefa = crear_tarefa(session, ana, horta.id, "Levar patacas ao bar", tipo="lote_saida")
    assert tarefa.tipo == "lote_saida"
```

### Paso 2 — crear o ficheiro `tests/test_migracion_lotes.py`

Contido completo:
```python
"""Os lotes de texto pasan a fichas de lote, e o cliente da colleita a unha venda
(docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md)."""

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


def test_lotes_e_cliente_da_colleita(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "e1b3d5f7a9c4")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, cultivo_siex_codigo, "
            "sistema_cultivo, producion_integrada, certificacion_ecoloxica, sementeira_directa, "
            "material_tratado, material_adquirido, plan_ferramenta_sostibilidade, created_at) "
            "VALUES (1, 1, 'Tomate', 37, '4', 0, NULL, 0, 0, 0, 0, '2026-01-01')"))
        for fila in ("(1, 1, '2026-08-01', 20, 'kg', 'L-1', NULL, NULL)",
                     "(2, 1, '2026-08-08', 30, 'kg', 'L-2', 'Froitas Melide SL', 'A-7')"):
            conn.execute(text(
                "INSERT INTO colleita (id, cultivo_id, data, cantidade, unidade, lote, "
                "cliente_nome, albaran_factura, obten_sementes, obten_plantas, "
                "sen_colleita_ambiental, restos_no_solo, baixa, created_at) VALUES "
                f"{fila[:-1]}, 0, 0, 0, 0, 0, '2026-01-01')"))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        lotes = conn.execute(text(
            "SELECT codigo, produto, cultivo_siex_codigo, unidade, protexido FROM lote "
            "ORDER BY codigo")).all()
        venda = conn.execute(text(
            "SELECT s.tipo, s.cantidade, s.canle, s.albaran_factura, p.nome FROM lote_saida s "
            "JOIN persoa p ON p.id = s.comprador_id")).one()
    assert [tuple(f) for f in lotes] == [("L-1", "Tomate", 37, "kg", 1),
                                         ("L-2", "Tomate", 37, "kg", 1)]
    assert tuple(venda) == ("venda", 30.0, "almacen", "A-7", "Froitas Melide SL")
    _alembic(url, "downgrade", "e1b3d5f7a9c4")
    with engine.connect() as conn:
        colleitas = conn.execute(text(
            "SELECT lote, cliente_nome, albaran_factura FROM colleita ORDER BY id")).all()
    assert [tuple(f) for f in colleitas] == [("L-1", None, None),
                                             ("L-2", "Froitas Melide SL", "A-7")]
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Lotes (5/5): probas: feito.

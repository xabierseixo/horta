# Tarefa 074e — Apuntar o mínimo (6/6): que lle falta ao caderno

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074d. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Servizo que conta, por tipo de traballo, os datos que lle faltan ao apuntado para o caderno oficial. Só avisa. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/services/faltas_caderno.py` (**ficheiro novo**)
- `tests/services/test_apuntar_minimo.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/faltas_caderno.py`

Contido completo:
```python
"""Que lle falta ao apuntado para o caderno oficial (CUE). Só avisa: apuntar un traballo
nunca esixe os datos do caderno, que só é obrigatorio nas explotacións profesionais."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados
from horta.services.labores import listar_labores
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import faltas_para_cue, listar_tratamentos_fito


@dataclass(frozen=True)
class Falta:
    traballo: str  # "Regas"
    dato: str  # "sistema de rega"
    cantos: int


def _contar(traballo: str, rexistros: list[Any],
            comprobacions: Iterable[tuple[str, Callable[[Any], bool]]]) -> list[Falta]:
    faltas = []
    for dato, falta in comprobacions:
        cantos = sum(1 for r in rexistros if falta(r))
        if cantos:
            faltas.append(Falta(traballo, dato, cantos))
    return faltas


def faltas_caderno(session: Session, actor: Usuario, horta_id: int,
                   desde: date | None = None, ata: date | None = None) -> list[Falta]:
    """Os datos que faltan, por tipo de traballo, nos rexistros do período."""
    def no_periodo(data: date) -> bool:
        return (desde is None or data >= desde) and (ata is None or data <= ata)

    regas = [r for r in listar_regas(session, actor, horta_id) if no_periodo(r.data_inicio)]
    abonados = [a for a in listar_abonados(session, actor, horta_id) if no_periodo(a.data_inicio)]
    labores = [lab for lab in listar_labores(session, actor, horta_id)
               if no_periodo(lab.data_inicio)]
    tratamentos = [t for t in listar_tratamentos_fito(session, actor, horta_id)
                   if no_periodo(t.data_inicio)]
    return [
        *_contar("Tratamentos", tratamentos, [
            ("datos do CUE (ver a táboa de tratamentos)", lambda t: bool(faltas_para_cue(t)))]),
        *_contar("Abonados", abonados, [
            ("superficie", lambda a: not a.superficie_ha),
            ("tipo de fertilización", lambda a: not a.tipo_fertilizacion),
            ("método de aplicación", lambda a: not a.metodo),
            ("boas prácticas", lambda a: not a.boas_practicas),
            ("dose", lambda a: a.fertilizante_id is not None and a.dose is None)]),
        *_contar("Regas", regas, [
            ("superficie", lambda r: not r.superficie_ha),
            ("sistema de rega", lambda r: not r.sistema_rega),
            ("cantidade de auga", lambda r: r.cantidade is None)]),
        *_contar("Labores", labores, [("superficie", lambda lab: not lab.superficie_ha)]),
    ]
```

### Paso 2 — crear o ficheiro `tests/services/test_apuntar_minimo.py`

Contido completo:
```python
"""Apuntar un traballo só obriga ao mínimo (que, onde e cando); o resto é opcional e o
caderno avisa do que falta."""

from datetime import date

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.faltas_caderno import Falta, faltas_caderno
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega

HOXE = date(2026, 10, 26)


def _cultivo_sen_superficie(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("material_fertilizante", "13"), ("tipo_labor", "7")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x", rol=RolGlobal.USUARIO,
                  activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta da casa")
    parcela = crear_parcela(session, ana, horta.id, "Horta")
    return ana, horta, crear_cultivo(session, ana, parcela.id, "Tomate")


def test_rega_so_con_cultivo_e_data(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    rega = crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE),
                      hoxe=HOXE)
    assert rega.sistema_rega is None and rega.cantidade is None and rega.superficie_ha is None


def test_abonado_so_co_abono(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost da casa", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id), hoxe=HOXE)
    assert abonado.tipo_fertilizacion is None and abonado.metodo is None
    assert abonado.dose is None and abonado.unidade is None and abonado.boas_practicas == []


def test_colleita_pon_o_lote_soa(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=HOXE, cantidade=5, unidade="kg", lote=""), hoxe=HOXE)
    assert colleita.lote == "2026-TOMATE-001"


def test_labor_sen_superficie(session):
    ana, _, cultivo = _cultivo_sen_superficie(session)
    labor = crear_labor(session, ana, DatosLabor(
        cultivo_id=cultivo.id, data_inicio=HOXE, tipo_labor="7"), hoxe=HOXE)
    assert labor.superficie_ha is None


def test_sen_rexistros_non_falta_nada(session):
    ana, horta, _ = _cultivo_sen_superficie(session)
    assert faltas_caderno(session, ana, horta.id) == []


def test_conta_o_que_falta_en_cada_rega(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    for _ in range(2):
        crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE), hoxe=HOXE)
    assert faltas_caderno(session, ana, horta.id) == [
        Falta("Regas", "superficie", 2), Falta("Regas", "sistema de rega", 2),
        Falta("Regas", "cantidade de auga", 2)]


def test_so_mira_o_periodo(session):
    ana, horta, cultivo = _cultivo_sen_superficie(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE), hoxe=HOXE)
    assert faltas_caderno(session, ana, horta.id, desde=date(2027, 1, 1)) == []
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Apuntar o mínimo (6/6): que lle falta ao caderno: feito.

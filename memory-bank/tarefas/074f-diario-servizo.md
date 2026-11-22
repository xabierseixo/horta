# Tarefa 074f — Diario: lista común de traballos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Servizo que xunta todos os traballos (tratamentos, abonados, regas, labores, colleitas, sementeiras, mostras, tratamentos de instalacións e tarefas) coa parte común: que, cando, onde e estado. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/services/diario.py` (**ficheiro novo**)
- `tests/services/test_diario.py` (**ficheiro novo**)
- `src/horta/ui/catalogos_aviso.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/diario.py`

Contido completo:
```python
"""Diario de traballos: todo o feito e o por facer nunha soa lista. Le os rexistros de cada
tipo de traballo (cada un na súa táboa) e devolve a parte común: que, cando, onde e estado."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados
from horta.services.analises import listar_analises
from horta.services.catalogos import describir
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import listar_cultivos
from horta.services.labores import listar_labores
from horta.services.regas import listar_regas
from horta.services.tarefas import listar_tarefas
from horta.services.tratamentos_fito import listar_tratamentos_fito
from horta.services.tratamentos_instalacion import listar_tratamentos_instalacion

# Tipos de traballo, na orde en que se ofrecen ao apuntar
TIPOS: dict[str, str] = {
    "tratamento": "Tratamento",
    "abonado": "Abonado",
    "rega": "Rega",
    "labor": "Labor",
    "colleita": "Colleita",
    "sementeira": "Sementeira ou plantación",
    "analise": "Toma de mostras",
    "tratamento_instalacion": "Tratamento en almacén ou instalación",
    "tarefa": "Tarefa",
}


@dataclass(frozen=True)
class Traballo:
    tipo: str  # clave de TIPOS
    id: int  # id do rexistro na táboa do seu tipo
    data: date | None  # None: tarefa por facer sen data
    feito: bool
    que: str
    onde: str
    parcelas: frozenset[int]
    atrasado: bool = False


def listar_traballos(
    session: Session, actor: Usuario, horta_id: int, desde: date | None = None,
    ata: date | None = None, hoxe: date | None = None,
) -> list[Traballo]:
    """Primeiro o por facer (sen data, despois por data); logo o feito no período, do máis
    recente ao máis antigo. O por facer sae sempre, sexa cal sexa o período."""
    hoxe = hoxe or date.today()
    cultivos = {c.id: c for c in listar_cultivos(session, actor, horta_id)}
    parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}

    def onde(cultivo_id: int | None) -> str:
        c = cultivos.get(cultivo_id) if cultivo_id else None
        if c is None:
            return ""
        return f"{c.especie} {c.variedade or ''}".strip() + f" — {parcelas.get(c.parcela_id, '')}"

    def parcela_de(cultivo_id: int | None) -> frozenset[int]:
        c = cultivos.get(cultivo_id) if cultivo_id else None
        return frozenset({c.parcela_id}) if c else frozenset()

    def texto(catalogo: str, codigo: str | None) -> str:
        return describir(session, catalogo, codigo) if codigo else ""

    traballos: list[Traballo] = []
    for t in listar_tratamentos_fito(session, actor, horta_id):
        ids = [tc.cultivo_id for tc in t.cultivos]
        traballos.append(Traballo(
            "tratamento", t.id, t.data_inicio, True,
            ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
            or ", ".join(texto(p.tipo, p.codigo) for p in t.problemas),
            onde(ids[0]) if len(ids) == 1 else f"{len(ids)} cultivos",
            frozenset().union(*(parcela_de(i) for i in ids))))
    for a in listar_abonados(session, actor, horta_id):
        abono = session.get(Fertilizante, a.fertilizante_id) if a.fertilizante_id else None
        traballos.append(Traballo(
            "abonado", a.id, a.data_inicio, True, abono.nome if abono else "Abonado en verde",
            onde(a.cultivo_id), parcela_de(a.cultivo_id)))
    for r in listar_regas(session, actor, horta_id):
        traballos.append(Traballo("rega", r.id, r.data_inicio, True,
                                  texto("sistema_rega", r.sistema_rega),
                                  onde(r.cultivo_id), parcela_de(r.cultivo_id)))
    for lab in listar_labores(session, actor, horta_id):
        traballos.append(Traballo("labor", lab.id, lab.data_inicio, True,
                                  texto("tipo_labor", lab.tipo_labor),
                                  onde(lab.cultivo_id), parcela_de(lab.cultivo_id)))
    for col in listar_colleitas(session, actor, horta_id):
        traballos.append(Traballo("colleita", col.id, col.data, True,
                                  f"{col.cantidade:g} {col.unidade} · lote {col.lote}",
                                  onde(col.cultivo_id), parcela_de(col.cultivo_id)))
    for c in cultivos.values():
        if c.data_inicio is not None:
            traballos.append(Traballo(
                "sementeira", c.id, c.data_inicio, c.data_inicio <= hoxe,
                "Plantación" if c.tipo_inicio == "plantacion" else "Sementeira",
                onde(c.id), parcela_de(c.id)))
    for an in listar_analises(session, actor, horta_id):
        sitio = onde(an.cultivo_id) or parcelas.get(an.parcela_id or 0, "")
        traballos.append(Traballo(
            "analise", an.id, an.data_mostraxe, True,
            texto("material_analizado", an.material_analizado), sitio,
            parcela_de(an.cultivo_id) or (frozenset({an.parcela_id}) if an.parcela_id
                                          else frozenset())))
    for ti in listar_tratamentos_instalacion(session, actor, horta_id):
        traballos.append(Traballo("tratamento_instalacion", ti.id, ti.data, True,
                                  ti.nome_comercial or ti.materia_activa or "", ti.obxecto,
                                  frozenset()))
    for ta in listar_tarefas(session, actor, horta_id):
        feita = ta.estado == "feito"
        sitio = onde(ta.cultivo_id) or parcelas.get(ta.parcela_id or 0, "")
        traballos.append(Traballo(
            "tarefa", ta.id, ta.data_feita or ta.data if feita else ta.data or ta.data_limite,
            feita, ta.descricion, sitio,
            parcela_de(ta.cultivo_id) or (frozenset({ta.parcela_id}) if ta.parcela_id
                                          else frozenset()),
            atrasado=not feita and ta.data_limite is not None and ta.data_limite < hoxe))

    por_facer = sorted((t for t in traballos if not t.feito),
                       key=lambda t: (t.data is not None, t.data or hoxe))
    feitos = sorted((t for t in traballos if t.feito
                     and (t.data is None or ((desde is None or t.data >= desde)
                                             and (ata is None or t.data <= ata)))),
                    key=lambda t: (t.data or hoxe, t.id), reverse=True)
    return por_facer + feitos

```

### Paso 2 — crear o ficheiro `tests/services/test_diario.py`

Contido completo:
```python
from datetime import date

from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.diario import listar_traballos
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega
from horta.services.tarefas import crear_tarefa, marcar_feita

HOXE = date(2026, 10, 26)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x", rol=RolGlobal.USUARIO,
                  activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Horta de abaixo")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    return ana, horta, parcela, cultivo


def test_xunta_os_traballos_de_cada_tipo(session):
    ana, horta, parcela, cultivo = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, data_inicio=date(2026, 5, 1),
                       tipo_inicio="plantacion")
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1)),
               hoxe=HOXE)
    traballos = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert [(t.tipo, t.data, t.feito) for t in traballos] == [
        ("rega", date(2026, 7, 1), True), ("sementeira", date(2026, 5, 1), True)]
    assert traballos[1].que == "Plantación"
    assert traballos[0].onde == "Tomate — Horta de abaixo"
    assert traballos[0].parcelas == {parcela.id}


def test_o_por_facer_vai_primeiro_e_sae_sempre(session):
    ana, horta, _, cultivo = _escenario(session)
    crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=date(2026, 1, 10)),
               hoxe=HOXE)
    crear_tarefa(session, ana, horta.id, "Podar a viña", data=date(2026, 11, 2))
    crear_tarefa(session, ana, horta.id, "Mercar sementes")
    crear_tarefa(session, ana, horta.id, "Sulfatar", data_limite=date(2026, 10, 1))
    traballos = listar_traballos(session, ana, horta.id, desde=date(2026, 10, 1), hoxe=HOXE)
    assert [(t.que, t.feito, t.atrasado) for t in traballos] == [
        ("Mercar sementes", False, False), ("Sulfatar", False, True),
        ("Podar a viña", False, False)]


def test_a_tarefa_feita_vai_coa_data_en_que_se_fixo(session):
    ana, horta, _, _ = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Limpar o galiñeiro", data=date(2026, 10, 1))
    marcar_feita(session, ana, tarefa)
    (traballo,) = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert traballo.feito and traballo.data == tarefa.data_feita
```

### Paso 3 — crear o ficheiro `src/horta/ui/catalogos_aviso.py`

Contido completo:
```python
"""Aviso común cando faltan os catálogos oficiais: avísase, pero déixase apuntar."""

AVISO_SEN_CATALOGOS = ("Faltan os catálogos oficiais e algunhas listas están baleiras. Podes "
                       "apuntar o resto; un administrador pode cargalos en «Catálogos oficiais».")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Diario: lista común de traballos: feito.

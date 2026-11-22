# Tarefa 075l — Quen e horas no Diario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075k. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Diario sabe quen fixo cada traballo, quen fixo o último (para propoñelo) e cantos traballos de antes non teñen quen. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/diario.py`
- `tests/services/test_quen.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/diario.py`

Antes:
```python
tipo de traballo (cada un na súa táboa) e devolve a parte común: que, cando, onde e estado."""
```

Despois:
```python
tipo de traballo (cada un na súa táboa) e devolve a parte común: que, cando, onde, quen e
estado."""
```

### Paso 2 — `src/horta/services/diario.py`

Antes:
```python
    atrasado: bool = False
```

Despois:
```python
    atrasado: bool = False
    persoas: tuple[int, ...] = ()  # quen o fixo
    sen_quen: bool = False  # feito e sen saber quen o fixo (rexistros de antes)


def _quen(*ids: int | None) -> tuple[int, ...]:
    return tuple(i for i in ids if i is not None)
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
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
```

Despois:
```python
        quen = _quen(*(ap.persoa_id for ap in t.aplicadores))
        traballos.append(Traballo(
            "tratamento", t.id, t.data_inicio, True,
            ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
            or ", ".join(texto(p.tipo, p.codigo) for p in t.problemas),
            onde(ids[0]) if len(ids) == 1 else f"{len(ids)} cultivos",
            frozenset().union(*(parcela_de(i) for i in ids)), persoas=quen,
            sen_quen=not quen))
    for a in listar_abonados(session, actor, horta_id):
        abono = session.get(Fertilizante, a.fertilizante_id) if a.fertilizante_id else None
        quen = _quen(a.aplicador_persoa_id)
        traballos.append(Traballo(
            "abonado", a.id, a.data_inicio, True, abono.nome if abono else "Abonado en verde",
            onde(a.cultivo_id), parcela_de(a.cultivo_id), persoas=quen,
            sen_quen=not quen and not a.empresa_servizos_regfer))
    for r in listar_regas(session, actor, horta_id):
        traballos.append(Traballo("rega", r.id, r.data_inicio, True,
                                  texto("sistema_rega", r.sistema_rega),
                                  onde(r.cultivo_id), parcela_de(r.cultivo_id),
                                  persoas=_quen(r.persoa_id), sen_quen=r.persoa_id is None))
    for lab in listar_labores(session, actor, horta_id):
        traballos.append(Traballo("labor", lab.id, lab.data_inicio, True,
                                  texto("tipo_labor", lab.tipo_labor),
                                  onde(lab.cultivo_id), parcela_de(lab.cultivo_id),
                                  persoas=_quen(lab.persoa_id), sen_quen=lab.persoa_id is None))
    for col in listar_colleitas(session, actor, horta_id):
        traballos.append(Traballo("colleita", col.id, col.data, True,
                                  f"{col.cantidade:g} {col.unidade} · lote {col.lote}",
                                  onde(col.cultivo_id), parcela_de(col.cultivo_id),
                                  persoas=_quen(col.persoa_id), sen_quen=col.persoa_id is None))
    for c in cultivos.values():
        if c.data_inicio is not None:
            feita = c.data_inicio <= hoxe
            traballos.append(Traballo(
                "sementeira", c.id, c.data_inicio, feita,
                "Plantación" if c.tipo_inicio == "plantacion" else "Sementeira",
                onde(c.id), parcela_de(c.id), persoas=_quen(c.sementeira_persoa_id),
                sen_quen=feita and c.sementeira_persoa_id is None))
    for an in listar_analises(session, actor, horta_id):
        sitio = onde(an.cultivo_id) or parcelas.get(an.parcela_id or 0, "")
        traballos.append(Traballo(
            "analise", an.id, an.data_mostraxe, True,
            texto("material_analizado", an.material_analizado), sitio,
            parcela_de(an.cultivo_id) or (frozenset({an.parcela_id}) if an.parcela_id
                                          else frozenset()),
            persoas=_quen(an.persoa_id), sen_quen=an.persoa_id is None))
    for ti in listar_tratamentos_instalacion(session, actor, horta_id):
        traballos.append(Traballo("tratamento_instalacion", ti.id, ti.data, True,
                                  ti.nome_comercial or ti.materia_activa or "", ti.obxecto,
                                  frozenset(), persoas=_quen(ti.persoa_id),
                                  sen_quen=ti.persoa_id is None))
```

### Paso 4 — `src/horta/services/diario.py`

Antes:
```python
    return por_facer + feitos

```

Despois:
```python
    return por_facer + feitos



def ultima_persoa(session: Session, actor: Usuario, horta_id: int) -> int | None:
    """Quen fixo o último traballo apuntado, para propoñelo no seguinte."""
    for t in listar_traballos(session, actor, horta_id):
        if t.feito and t.persoas:
            return t.persoas[0]
    return None


def sen_quen(session: Session, actor: Usuario, horta_id: int) -> dict[str, int]:
    """Cantos traballos feitos de cada tipo non teñen quen o fixo (os apuntados antes)."""
    contas: dict[str, int] = {}
    for t in listar_traballos(session, actor, horta_id):
        if t.sen_quen:
            contas[t.tipo] = contas.get(t.tipo, 0) + 1
    return contas
```

### Paso 5 — crear o ficheiro `tests/services/test_quen.py`

Contido completo:
```python
"""Todo traballo o fai unha persoa: apuntalo obriga a dicir quen; as horas son opcionais."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.analises import DatosAnalise, crear_analise
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.diario import listar_traballos, sen_quen, ultima_persoa
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    crear_tratamento_instalacion,
)

HOXE = date(2026, 10, 27)


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("material_fertilizante", "13"), ("tipo_labor", "7"),
                             ("material_analizado", "3")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x", rol=RolGlobal.USUARIO,
                  activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    ana_persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    parcela = crear_parcela(session, ana, horta.id, "Horta")
    return ana, horta, ana_persoa, crear_cultivo(session, ana, parcela.id, "Tomate")


def _apuntar(session, ana, horta, cultivo, tipo, persoa_id, horas=None):
    if tipo == "rega":
        return crear_rega(session, ana, DatosRega(
            cultivo_id=cultivo.id, data_inicio=HOXE, persoa_id=persoa_id, horas=horas),
            hoxe=HOXE)
    if tipo == "labor":
        return crear_labor(session, ana, DatosLabor(
            cultivo_id=cultivo.id, data_inicio=HOXE, tipo_labor="7", persoa_id=persoa_id,
            horas=horas), hoxe=HOXE)
    if tipo == "colleita":
        return crear_colleita(session, ana, DatosColleita(
            cultivo_id=cultivo.id, data=HOXE, cantidade=5, unidade="kg", lote="",
            persoa_id=persoa_id, horas=horas), hoxe=HOXE)
    if tipo == "analise":
        return crear_analise(session, ana, horta.id, DatosAnalise(
            material_analizado="3", data_mostraxe=HOXE, persoa_id=persoa_id, horas=horas),
            hoxe=HOXE)
    if tipo == "tratamento_instalacion":
        return crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
            tipo="local", data=HOXE, obxecto="Almacén", materia_activa="Cal",
            persoa_id=persoa_id, horas=horas), hoxe=HOXE)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost", material="13"))
    return crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id,
        aplicador_persoa_id=persoa_id, horas=horas), hoxe=HOXE)


TIPOS = ["rega", "labor", "colleita", "analise", "tratamento_instalacion", "abonado"]


@pytest.mark.parametrize("tipo", TIPOS)
def test_sen_quen_non_se_garda(session, tipo):
    ana, horta, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="Indica quen o fixo"):
        _apuntar(session, ana, horta, cultivo, tipo, None)


@pytest.mark.parametrize("tipo", TIPOS)
def test_garda_quen_e_as_horas(session, tipo):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    rexistro = _apuntar(session, ana, horta, cultivo, tipo, ana_persoa.id, horas=1.5)
    persoa_id = rexistro.aplicador_persoa_id if tipo == "abonado" else rexistro.persoa_id
    assert persoa_id == ana_persoa.id and rexistro.horas == 1.5


def test_as_horas_son_opcionais_pero_positivas(session):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    assert _apuntar(session, ana, horta, cultivo, "rega", ana_persoa.id).horas is None
    with pytest.raises(OperacionNonPermitidaError, match="horas"):
        _apuntar(session, ana, horta, cultivo, "rega", ana_persoa.id, horas=0)


def test_a_persoa_ten_que_ser_da_explotacion(session):
    ana, horta, _, cultivo = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    de_fora = session.query(Persoa).filter_by(horta_id=outra.id).one()
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        _apuntar(session, ana, horta, cultivo, "rega", de_fora.id)


def test_abonado_dunha_empresa_de_servizos_sen_persoa(session):
    ana, horta, _, cultivo = _escenario(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id,
        empresa_servizos_regfer="ES1234"), hoxe=HOXE)
    assert abonado.aplicador_persoa_id is None


def test_sementeira_garda_quen_e_as_horas(session):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, sementeira_persoa_id=ana_persoa.id,
                       sementeira_horas=3)
    assert cultivo.sementeira_persoa_id == ana_persoa.id and cultivo.sementeira_horas == 3
    outra = crear_horta(session, ana, "Outra")
    de_fora = session.query(Persoa).filter_by(horta_id=outra.id).one()
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        actualizar_cultivo(session, ana, cultivo, sementeira_persoa_id=de_fora.id)


def test_o_diario_sabe_quen_o_fixo(session):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    assert ultima_persoa(session, ana, horta.id) is None
    rega = _apuntar(session, ana, horta, cultivo, "rega", ana_persoa.id)
    [traballo] = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert traballo.persoas == (ana_persoa.id,) and not traballo.sen_quen
    assert ultima_persoa(session, ana, horta.id) == ana_persoa.id
    # Os rexistros de antes, sen persoa, avísanse
    rega.persoa_id = None
    session.commit()
    assert sen_quen(session, ana, horta.id) == {"rega": 1}
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas no Diario: feito.

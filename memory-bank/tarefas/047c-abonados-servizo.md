# Tarefa 047c — Servizo dos abonados

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 047b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Crear, editar, dar de baixa e listar abonados, cun cultivo cada un (decisión do usuario). Valida datas, superficie (por defecto a do cultivo), catálogos, polo menos unha boa práctica de fertilización e o abono (opcional só co «abonado en verde»). `nutrientes_do_abonado` dá os kg/ha de N, P₂O₅ e K₂O. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §1–2.

## Ficheiros a tocar

- `src/horta/services/abonados.py` (**ficheiro novo**)
- `tests/services/test_abonados.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/abonados.py`

Contido completo:
```python
"""Abonados dos cultivos (CUE bloque 9, fertilización). Un cultivo por abonado. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, nutrientes_kg_ha
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Boa práctica "Abonado en verde": é a única que permite non indicar abono (CUE)
ABONADO_EN_VERDE = "20"


@dataclass
class DatosAbonado:
    cultivo_id: int
    data_inicio: date
    tipo_fertilizacion: str
    metodo: str
    boas_practicas: list[str] = field(default_factory=list)
    fertilizante_id: int | None = None
    dose: float | None = None
    unidade: str | None = None
    data_fin: date | None = None
    superficie_ha: float | None = None
    xestion_sostible: bool = False
    aplicacion_lodos: bool = False
    albaran_factura: str | None = None
    aplicador_persoa_id: int | None = None
    empresa_servizos_regfer: str | None = None
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h_ha: float | None = None
    notas: str | None = None


def _horta_do_cultivo(session: Session, cultivo_id: int) -> tuple[Cultivo, int]:
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    return cultivo, horta_id


def _validar(
    session: Session, datos: DatosAbonado, cultivo: Cultivo, horta_id: int, hoxe: date
) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do abonado non pode ser futura")
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie abonada é maior ca do cultivo")
    elif not cultivo.superficie_ha:
        raise OperacionNonPermitidaError("Indica a superficie: o cultivo non a ten")
    validar_codigo(session, "tipo_fertilizacion", datos.tipo_fertilizacion, datos.data_inicio)
    validar_codigo(session, "metodo_fertilizacion", datos.metodo, datos.data_inicio)
    if not datos.boas_practicas:
        raise OperacionNonPermitidaError(
            "Indica polo menos unha boa práctica (ou «Non realiza boas prácticas»)"
        )
    for codigo in datos.boas_practicas:
        valor = validar_codigo(session, "boas_practicas", codigo, datos.data_inicio)
        if "fertilizacion" not in (valor.categoria or ""):
            raise OperacionNonPermitidaError(f"A boa práctica {codigo} non é de fertilización")
    if datos.fertilizante_id is None:
        if ABONADO_EN_VERDE not in datos.boas_practicas:
            raise OperacionNonPermitidaError("Escolle o abono")
        return
    fertilizante = session.get(Fertilizante, datos.fertilizante_id)
    if fertilizante is None or fertilizante.horta_id != horta_id:
        raise OperacionNonPermitidaError("Ese abono non é desta explotación")
    if datos.dose is None or datos.dose <= 0:
        raise OperacionNonPermitidaError("A dose ten que ser maior que 0")
    if datos.unidade not in UNIDADES_DOSE:
        raise OperacionNonPermitidaError("Escolle a unidade da dose (por hectárea ou por m²)")


def _copiar(abonado: Abonado, datos: DatosAbonado, horta_id: int, cultivo: Cultivo) -> None:
    abonado.horta_id = horta_id
    abonado.cultivo_id = datos.cultivo_id
    abonado.data_inicio = datos.data_inicio
    abonado.data_fin = datos.data_fin or datos.data_inicio
    abonado.superficie_ha = datos.superficie_ha or cultivo.superficie_ha or 0
    abonado.fertilizante_id = datos.fertilizante_id
    abonado.dose = datos.dose if datos.fertilizante_id else None
    abonado.unidade = datos.unidade if datos.fertilizante_id else None
    abonado.tipo_fertilizacion = datos.tipo_fertilizacion
    abonado.metodo = datos.metodo
    abonado.xestion_sostible = datos.xestion_sostible
    abonado.aplicacion_lodos = datos.aplicacion_lodos
    abonado.albaran_factura = datos.albaran_factura or None
    abonado.aplicador_persoa_id = datos.aplicador_persoa_id
    abonado.empresa_servizos_regfer = datos.empresa_servizos_regfer or None
    abonado.maquina_id = datos.maquina_id
    abonado.num_repeticions = datos.num_repeticions
    abonado.duracion_h_ha = datos.duracion_h_ha
    abonado.notas = datos.notas or None
    abonado.boas_practicas = [AbonadoBoaPractica(codigo=c) for c in datos.boas_practicas]


def crear_abonado(
    session: Session, actor: Usuario, datos: DatosAbonado, hoxe: date | None = None
) -> Abonado:
    cultivo, horta_id = _horta_do_cultivo(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    abonado = Abonado(creado_por=actor.id)
    _copiar(abonado, datos, horta_id, cultivo)
    session.add(abonado)
    session.commit()
    return abonado


def actualizar_abonado(
    session: Session, actor: Usuario, abonado: Abonado, datos: DatosAbonado,
    hoxe: date | None = None,
) -> Abonado:
    if abonado.baixa:
        raise OperacionNonPermitidaError("Un abonado dado de baixa non se pode modificar")
    comprobar_rol_horta(session, abonado.horta_id, actor, _ROLES_ESCRITURA)
    cultivo, horta_id = _horta_do_cultivo(session, datos.cultivo_id)
    if horta_id != abonado.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    _copiar(abonado, datos, horta_id, cultivo)
    session.commit()
    return abonado


def dar_de_baixa_abonado(session: Session, actor: Usuario, abonado: Abonado) -> None:
    comprobar_rol_horta(session, abonado.horta_id, actor, _ROLES_ESCRITURA)
    abonado.baixa = True
    session.commit()


def listar_abonados(
    session: Session, actor: Usuario, horta_id: int, cultivo_id: int | None = None
) -> list[Abonado]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Abonado).filter_by(horta_id=horta_id, baixa=False)
    if cultivo_id is not None:
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Abonado.data_inicio.desc(), Abonado.id.desc()))


def nutrientes_do_abonado(session: Session, abonado: Abonado) -> tuple[float, float, float] | None:
    """kg/ha de N, P₂O₅ e K₂O deste abonado; None sen abono, dose ou densidade."""
    if abonado.fertilizante_id is None or abonado.dose is None or abonado.unidade is None:
        return None
    fertilizante = session.get(Fertilizante, abonado.fertilizante_id)
    return nutrientes_kg_ha(fertilizante, abonado.dose, abonado.unidade) if fertilizante else None
```

### Paso 2 — crear o ficheiro `tests/services/test_abonados.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import (
    DatosAbonado,
    actualizar_abonado,
    crear_abonado,
    dar_de_baixa_abonado,
    listar_abonados,
    nutrientes_do_abonado,
)
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 25)


def _usuario(session, email):
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo, categoria in [
        ("material_fertilizante", "14", None), ("tipo_fertilizacion", "1", None),
        ("metodo_fertilizacion", "1", None), ("boas_practicas", "0", "fito,fertilizacion,rega"),
        ("boas_practicas", "20", "fito,fertilizacion"), ("boas_practicas", "50", "fito"),
    ]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  categoria=categoria, version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK 15-15-15", material="14", n_pct=15, p2o5_pct=15, k2o_pct=15))
    return ana, horta, cultivo, abono


def _datos(cultivo, abono, **cambios):
    base = {"cultivo_id": cultivo.id, "data_inicio": date(2026, 4, 1), "tipo_fertilizacion": "1",
            "metodo": "1", "boas_practicas": ["0"], "fertilizante_id": abono.id, "dose": 200,
            "unidade": "17"}
    base.update(cambios)
    return DatosAbonado(**base)


def test_crear_abonado_coa_superficie_do_cultivo(session):
    ana, horta, cultivo, abono = _escenario(session)
    abonado = crear_abonado(session, ana, _datos(cultivo, abono), hoxe=HOXE)
    assert abonado.superficie_ha == 0.2 and abonado.data_fin == date(2026, 4, 1)
    assert abonado.creado_por == ana.id
    assert [b.codigo for b in abonado.boas_practicas] == ["0"]
    assert nutrientes_do_abonado(session, abonado) == (30.0, 30.0, 30.0)
    assert listar_abonados(session, ana, horta.id) == [abonado]


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_inicio": date(2026, 11, 1)}, "futura"),
    ({"data_fin": date(2026, 3, 1)}, "anterior"),
    ({"superficie_ha": 0.3}, "maior ca do cultivo"),
    ({"boas_practicas": []}, "boa práctica"),
    ({"boas_practicas": ["50"]}, "non é de fertilización"),
    ({"fertilizante_id": None}, "Escolle o abono"),
    ({"dose": 0}, "dose"),
    ({"unidade": "2"}, "unidade"),
])
def test_validacions(session, cambios, mensaxe):
    ana, _, cultivo, abono = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_abonado(session, ana, _datos(cultivo, abono, **cambios), hoxe=HOXE)


def test_abonado_en_verde_sen_abono(session):
    ana, _, cultivo, abono = _escenario(session)
    abonado = crear_abonado(session, ana, _datos(
        cultivo, abono, fertilizante_id=None, boas_practicas=["20"]), hoxe=HOXE)
    assert abonado.fertilizante_id is None and abonado.dose is None
    assert nutrientes_do_abonado(session, abonado) is None


def test_lector_non_pode_abonar(session):
    ana, horta, cultivo, abono = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_abonado(session, bea, _datos(cultivo, abono), hoxe=HOXE)


def test_actualizar_e_dar_de_baixa(session):
    ana, horta, cultivo, abono = _escenario(session)
    abonado = crear_abonado(session, ana, _datos(cultivo, abono), hoxe=HOXE)
    actualizar_abonado(session, ana, abonado, _datos(cultivo, abono, dose=100), hoxe=HOXE)
    assert abonado.dose == 100
    dar_de_baixa_abonado(session, ana, abonado)
    assert listar_abonados(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_abonado(session, ana, abonado, _datos(cultivo, abono), hoxe=HOXE)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense apuntar abonados por servizo, con probas.

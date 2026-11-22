# Tarefa 084 — Varias leiras (1/5): datos e servizos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Labor, rega e abonado gardan as súas leiras (unha ou varias) nunha táboa filla; validación común das leiras. Deseño: `docs/superpowers/specs/2026-10-28-varias-leiras-design.md` (paso 5 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/a3d5f7b9c1e8_varias_leiras.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `src/horta/services/leiras.py` (**ficheiro novo**)
- `src/horta/services/labores.py`
- `src/horta/services/regas.py`
- `src/horta/services/abonados.py`
- `src/horta/services/parcelas.py`
- `src/horta/services/cultivos.py`
- `tests/services/test_abonados.py`
- `tests/services/test_abonados_conservar.py`
- `tests/services/test_abonados_conservar_horta.py`
- `tests/services/test_apuntar_minimo.py`
- `tests/services/test_caderno.py`
- `tests/services/test_caderno_abonos_metais.py`
- `tests/services/test_labores.py`
- `tests/services/test_plan_abonado.py`
- `tests/services/test_regas.py`
- `tests/services/test_regas_conservar.py`
- `src/horta/models/labor.py`
- `src/horta/models/rega.py`
- `src/horta/models/abonado.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/a3d5f7b9c1e8_varias_leiras.py`

Contido completo:
```python
"""varias leiras nun traballo: labor, rega e abonado gardan as súas leiras nunha táboa filla

Revision ID: a3d5f7b9c1e8
Revises: f2c4e6a8b0d5
Create Date: 2026-10-28 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d5f7b9c1e8'
down_revision: Union[str, Sequence[str], None] = 'f2c4e6a8b0d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TRABALLOS = ("labor", "rega", "abonado")


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for taboa in _TRABALLOS:
        filla = f"{taboa}_cultivo"
        op.create_table(
            filla,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(f"{taboa}_id", sa.Integer(), nullable=False),
            sa.Column("cultivo_id", sa.Integer(), nullable=False),
            sa.Column("superficie_ha", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint([f"{taboa}_id"], [f"{taboa}.id"]),
            sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f(f"ix_{filla}_{taboa}_id"), filla, [f"{taboa}_id"])
        op.create_index(op.f(f"ix_{filla}_cultivo_id"), filla, ["cultivo_id"])
        # Cada traballo de agora tiña un cultivo: pasa a ser a súa única leira
        conn.execute(sa.text(
            f"INSERT INTO {filla} ({taboa}_id, cultivo_id, superficie_ha) "
            f"SELECT id, cultivo_id, superficie_ha FROM {taboa}"))
        with op.batch_alter_table(taboa) as batch:
            batch.drop_index(f"ix_{taboa}_cultivo_id")
            batch.drop_column("cultivo_id")
            batch.drop_column("superficie_ha")


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    for taboa in _TRABALLOS:
        filla = f"{taboa}_cultivo"
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("cultivo_id", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("superficie_ha", sa.Float(), nullable=True))
        # Volve a primeira leira de cada traballo (as demais pérdense ao volver atrás)
        conn.execute(sa.text(
            f"UPDATE {taboa} SET (cultivo_id, superficie_ha) = (SELECT cultivo_id, "
            f"superficie_ha FROM {filla} WHERE {filla}.{taboa}_id = {taboa}.id "
            f"ORDER BY {filla}.id LIMIT 1)"))
        with op.batch_alter_table(taboa) as batch:
            batch.alter_column("cultivo_id", existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key(f"fk_{taboa}_cultivo_id", "cultivo", ["cultivo_id"], ["id"])
            batch.create_index(f"ix_{taboa}_cultivo_id", ["cultivo_id"])
        op.drop_index(op.f(f"ix_{filla}_cultivo_id"), table_name=filla)
        op.drop_index(op.f(f"ix_{filla}_{taboa}_id"), table_name=filla)
        op.drop_table(filla)
```

### Paso 2 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, AbonadoCultivo, Fertilizante
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.labor import Labor
from horta.models.lote import Lote, LoteSaida
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.pastoreo import Pastoreo, PastoreoAnimal, PastoreoLeira
from horta.models.persoa import Persoa, PersoaPapel, TipoCarne
from horta.models.producion_animal import ProducionAnimal
from horta.models.rega import Rega, RegaBoaPractica
```

Despois:
```python
from horta.models.labor import Labor, LaborCultivo
from horta.models.lote import Lote, LoteSaida
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.pastoreo import Pastoreo, PastoreoAnimal, PastoreoLeira
from horta.models.persoa import Persoa, PersoaPapel, TipoCarne
from horta.models.producion_animal import ProducionAnimal
from horta.models.rega import Rega, RegaBoaPractica, RegaCultivo
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
    "AbonadoBoaPractica",
    "Rega",
    "Labor",
```

Despois:
```python
    "AbonadoCultivo",
    "AbonadoBoaPractica",
    "Rega",
    "RegaCultivo",
    "Labor",
    "LaborCultivo",
```

### Paso 5 — crear o ficheiro `src/horta/services/leiras.py`

Contido completo:
```python
"""As leiras dun traballo (labor, rega, abonado): unha ou varias, como no tratamento e no
pastoreo (docs/superpowers/specs/2026-10-28-varias-leiras-design.md)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.parcela import Parcela
from horta.services.errors import OperacionNonPermitidaError


@dataclass
class LeiraTraballo:
    cultivo_id: int
    # Baleiro: a do cultivo
    superficie_ha: float | None = None


@dataclass
class LeiraValida:
    cultivo: Cultivo
    parcela: Parcela
    superficie_ha: float | None


def as_leiras(cultivo_id: int | None, superficie_ha: float | None,
              leiras: list[LeiraTraballo]) -> list[LeiraTraballo]:
    """As leiras do traballo: a lista, ou unha soa (cultivo_id e superficie_ha) para apuntar
    nun só cultivo."""
    if leiras:
        return leiras
    return [LeiraTraballo(cultivo_id, superficie_ha)] if cultivo_id is not None else []


def validar_leiras(session: Session, leiras: list[LeiraTraballo],
                   horta_id: int | None = None) -> tuple[int, list[LeiraValida]]:
    """Polo menos unha, sen repetir, todas da mesma explotación (a do traballo, se xa a ten)
    e coa superficie dentro da do seu cultivo. Devolve a explotación e as leiras."""
    if not leiras:
        raise OperacionNonPermitidaError("Escolle polo menos unha leira")
    if len({leira.cultivo_id for leira in leiras}) != len(leiras):
        raise OperacionNonPermitidaError("Hai unha leira repetida")
    validas = []
    for leira in leiras:
        cultivo = session.get(Cultivo, leira.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None:
            raise OperacionNonPermitidaError("Ese cultivo non existe")
        if horta_id is None:
            horta_id = parcela.horta_id
        elif parcela.horta_id != horta_id:
            raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
        if leira.superficie_ha is not None:
            if leira.superficie_ha <= 0:
                raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
            if cultivo.superficie_ha and leira.superficie_ha > cultivo.superficie_ha:
                raise OperacionNonPermitidaError(
                    f"A superficie en {parcela.nome} é maior ca do cultivo")
        validas.append(LeiraValida(cultivo, parcela,
                                   leira.superficie_ha or cultivo.superficie_ha))
    assert horta_id is not None
    return horta_id, validas


def superficie_total(superficies: list[float | None]) -> float | None:
    """A suma das superficies, ou None se falta algunha."""
    if any(s is None for s in superficies):
        return None
    return sum(s for s in superficies if s is not None)
```

### Paso 6 — `src/horta/services/labores.py`

Antes:
```python
"""Labores culturais dos cultivos (CUE bloque 5). Un cultivo por labor. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo TIPO_LABOR: onde o CUE pregunta se os restos quedaron no chan
DESBROCE = "5"
PODAS = ("7", "11", "12")


@dataclass
class DatosLabor:
    cultivo_id: int
    data_inicio: date
    tipo_labor: str
    data_fin: date | None = None
    superficie_ha: float | None = None
```

Despois:
```python
"""Labores culturais (CUE bloque 5), nunha ou varias leiras. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.labor import Labor, LaborCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.leiras import LeiraTraballo, LeiraValida, as_leiras, validar_leiras
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo TIPO_LABOR: onde o CUE pregunta se os restos quedaron no chan
DESBROCE = "5"
PODAS = ("7", "11", "12")


@dataclass(kw_only=True)
class DatosLabor:
    data_inicio: date
    tipo_labor: str
    # As leiras; ou, para unha soa, cultivo_id e superficie_ha
    leiras: list[LeiraTraballo] = field(default_factory=list)
    cultivo_id: int | None = None
    superficie_ha: float | None = None
    data_fin: date | None = None
```

### Paso 7 — `src/horta/services/labores.py`

Antes:
```python
def _cultivo_e_parcela(session: Session, cultivo_id: int) -> tuple[Cultivo, Parcela]:
    cultivo = session.get(Cultivo, cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    return cultivo, parcela


def _validar(session: Session, datos: DatosLabor, cultivo: Cultivo, horta_id: int,
             hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do labor non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie do labor é maior ca do cultivo")
    for valor, texto in ((datos.num_repeticions, "repeticións"), (datos.duracion_h, "horas")):
        if valor is not None and valor <= 0:
            raise OperacionNonPermitidaError(f"O número de {texto} ten que ser maior que 0")
    validar_codigo(session, "tipo_labor", datos.tipo_labor, datos.data_inicio)
    if datos.tipo_cobertura:
        validar_codigo(session, "tipo_cobertura_solo", datos.tipo_cobertura, datos.data_inicio)
    if datos.maquina_id is not None:
        maquina = session.get(Maquina, datos.maquina_id)
        if maquina is None or maquina.horta_id != horta_id:
            raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")


def _copiar(labor: Labor, datos: DatosLabor, cultivo: Cultivo, parcela: Parcela) -> None:
    labor.horta_id = parcela.horta_id
    labor.cultivo_id = datos.cultivo_id
    labor.data_inicio = datos.data_inicio
    labor.data_fin = datos.data_fin or datos.data_inicio
    labor.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
    labor.tipo_labor = datos.tipo_labor
    # Os restos só se anotan nos labores onde o CUE os pregunta
    labor.restos_desbroce_no_solo = datos.tipo_labor == DESBROCE and datos.restos_desbroce_no_solo
    labor.restos_poda_no_solo = datos.tipo_labor in PODAS and datos.restos_poda_no_solo
    labor.tipo_cobertura = datos.tipo_cobertura or cultivo.tipo_cobertura_solo
```

Despois:
```python
def _validar(session: Session, datos: DatosLabor, horta_id: int, hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do labor non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    for valor, texto in ((datos.num_repeticions, "repeticións"), (datos.duracion_h, "horas")):
        if valor is not None and valor <= 0:
            raise OperacionNonPermitidaError(f"O número de {texto} ten que ser maior que 0")
    validar_codigo(session, "tipo_labor", datos.tipo_labor, datos.data_inicio)
    if datos.tipo_cobertura:
        validar_codigo(session, "tipo_cobertura_solo", datos.tipo_cobertura, datos.data_inicio)
    comprobar_maquina(session, horta_id, datos.maquina_id)


def _copiar(labor: Labor, datos: DatosLabor, horta_id: int, leiras: list[LeiraValida]) -> None:
    labor.horta_id = horta_id
    labor.leiras = [LaborCultivo(cultivo_id=le.cultivo.id, superficie_ha=le.superficie_ha)
                    for le in leiras]
    labor.data_inicio = datos.data_inicio
    labor.data_fin = datos.data_fin or datos.data_inicio
    labor.tipo_labor = datos.tipo_labor
    # Os restos só se anotan nos labores onde o CUE os pregunta
    labor.restos_desbroce_no_solo = datos.tipo_labor == DESBROCE and datos.restos_desbroce_no_solo
    labor.restos_poda_no_solo = datos.tipo_labor in PODAS and datos.restos_poda_no_solo
    labor.tipo_cobertura = datos.tipo_cobertura or leiras[0].cultivo.tipo_cobertura_solo
```

### Paso 8 — `src/horta/services/labores.py`

Antes:
```python
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, parcela.horta_id, hoxe or date.today())
    labor = Labor(creado_por=actor.id)
    _copiar(labor, datos, cultivo, parcela)
```

Despois:
```python
    horta_id, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras))
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, horta_id, hoxe or date.today())
    labor = Labor(creado_por=actor.id)
    _copiar(labor, datos, horta_id, leiras)
```

### Paso 9 — `src/horta/services/labores.py`

Antes:
```python
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    if parcela.horta_id != labor.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, labor.horta_id, hoxe or date.today())
    _copiar(labor, datos, cultivo, parcela)
```

Despois:
```python
    _, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras), labor.horta_id)
    _validar(session, datos, labor.horta_id, hoxe or date.today())
    _copiar(labor, datos, labor.horta_id, leiras)
```

### Paso 10 — `src/horta/services/labores.py`

Antes:
```python
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Labor.data_inicio.desc(), Labor.id.desc()))


def ultimo_labor(session: Session, cultivo_id: int) -> str | None:
    """O tipo do último labor dese cultivo, para propoñelo no seguinte."""
    labor = (session.query(Labor).filter_by(cultivo_id=cultivo_id, baixa=False)
```

Despois:
```python
        consulta = consulta.filter(Labor.leiras.any(LaborCultivo.cultivo_id == cultivo_id))
    return list(consulta.order_by(Labor.data_inicio.desc(), Labor.id.desc()))


def ultimo_labor(session: Session, cultivo_id: int) -> str | None:
    """O tipo do último labor dese cultivo, para propoñelo no seguinte."""
    labor = (session.query(Labor).filter(Labor.baixa.is_(False),
                                         Labor.leiras.any(LaborCultivo.cultivo_id == cultivo_id))
```

### Paso 11 — `src/horta/services/regas.py`

Antes:
```python
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.rega import Rega, RegaBoaPractica
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo UNIDADES_MEDIDA: m³ e litros
UNIDADES_AUGA = ("3", "4")


@dataclass
class DatosRega:
    cultivo_id: int
    data_inicio: date
```

Despois:
```python
from horta.models.horta import RolHorta
from horta.models.rega import Rega, RegaBoaPractica, RegaCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.leiras import LeiraTraballo, LeiraValida, as_leiras, validar_leiras
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo UNIDADES_MEDIDA: m³ e litros
UNIDADES_AUGA = ("3", "4")


@dataclass(kw_only=True)
class DatosRega:
    data_inicio: date
    # As leiras; ou, para unha soa, cultivo_id e superficie_ha. A auga é a total
    leiras: list[LeiraTraballo] = field(default_factory=list)
    cultivo_id: int | None = None
```

### Paso 12 — `src/horta/services/regas.py`

Antes:
```python
def _cultivo_e_parcela(session: Session, cultivo_id: int) -> tuple[Cultivo, Parcela]:
    cultivo = session.get(Cultivo, cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    return cultivo, parcela


def _validar(session: Session, datos: DatosRega, cultivo: Cultivo, horta_id: int,
             hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data da rega non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, horta_id, datos.maquina_id)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie regada é maior ca do cultivo")
```

Despois:
```python
def _validar(session: Session, datos: DatosRega, horta_id: int, hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data da rega non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, horta_id, datos.maquina_id)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
```

### Paso 13 — `src/horta/services/regas.py`

Antes:
```python
def _copiar(rega: Rega, datos: DatosRega, cultivo: Cultivo, parcela: Parcela) -> None:
    rega.horta_id = parcela.horta_id
    rega.cultivo_id = datos.cultivo_id
    rega.data_inicio = datos.data_inicio
    rega.data_fin = datos.data_fin or datos.data_inicio
    rega.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
    rega.sistema_rega = datos.sistema_rega or None
    rega.cantidade = datos.cantidade
    rega.unidade = datos.unidade
    rega.orixe_auga = datos.orixe_auga or parcela.orixe_auga
```

Despois:
```python
def _copiar(rega: Rega, datos: DatosRega, horta_id: int, leiras: list[LeiraValida]) -> None:
    rega.horta_id = horta_id
    rega.leiras = [RegaCultivo(cultivo_id=le.cultivo.id, superficie_ha=le.superficie_ha)
                   for le in leiras]
    rega.data_inicio = datos.data_inicio
    rega.data_fin = datos.data_fin or datos.data_inicio
    rega.sistema_rega = datos.sistema_rega or None
    rega.cantidade = datos.cantidade
    rega.unidade = datos.unidade
    rega.orixe_auga = datos.orixe_auga or leiras[0].parcela.orixe_auga
```

### Paso 14 — `src/horta/services/regas.py`

Antes:
```python
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, parcela.horta_id, hoxe or date.today())
    rega = Rega(creado_por=actor.id)
    _copiar(rega, datos, cultivo, parcela)
```

Despois:
```python
    horta_id, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras))
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, horta_id, hoxe or date.today())
    rega = Rega(creado_por=actor.id)
    _copiar(rega, datos, horta_id, leiras)
```

### Paso 15 — `src/horta/services/regas.py`

Antes:
```python
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    if parcela.horta_id != rega.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, rega.horta_id, hoxe or date.today())
    _copiar(rega, datos, cultivo, parcela)
```

Despois:
```python
    _, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras), rega.horta_id)
    _validar(session, datos, rega.horta_id, hoxe or date.today())
    _copiar(rega, datos, rega.horta_id, leiras)
```

### Paso 16 — `src/horta/services/regas.py`

Antes:
```python
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Rega.data_inicio.desc(), Rega.id.desc()))


def ultimo_sistema_rega(session: Session, cultivo_id: int) -> str | None:
    """O sistema de rega da última rega dese cultivo, para propoñelo na seguinte."""
    rega = (session.query(Rega).filter_by(cultivo_id=cultivo_id, baixa=False)
```

Despois:
```python
        consulta = consulta.filter(Rega.leiras.any(RegaCultivo.cultivo_id == cultivo_id))
    return list(consulta.order_by(Rega.data_inicio.desc(), Rega.id.desc()))


def ultimo_sistema_rega(session: Session, cultivo_id: int) -> str | None:
    """O sistema de rega da última rega dese cultivo, para propoñelo na seguinte."""
    rega = (session.query(Rega).filter(Rega.baixa.is_(False),
                                       Rega.leiras.any(RegaCultivo.cultivo_id == cultivo_id))
```

### Paso 17 — `src/horta/services/abonados.py`

Antes:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, nutrientes_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Boa práctica "Abonado en verde": é a única que permite non indicar abono (CUE)
ABONADO_EN_VERDE = "20"


@dataclass
class DatosAbonado:
    cultivo_id: int
    data_inicio: date
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, AbonadoCultivo, Fertilizante
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, nutrientes_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.leiras import LeiraTraballo, LeiraValida, as_leiras, validar_leiras
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Boa práctica "Abonado en verde": é a única que permite non indicar abono (CUE)
ABONADO_EN_VERDE = "20"


@dataclass(kw_only=True)
class DatosAbonado:
    data_inicio: date
    # As leiras; ou, para unha soa, cultivo_id e superficie_ha. A dose é por hectárea
    leiras: list[LeiraTraballo] = field(default_factory=list)
    cultivo_id: int | None = None
```

### Paso 18 — `src/horta/services/abonados.py`

Antes:
```python
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
    # Quen o fixo pode ser unha persoa do equipo ou a empresa de servizos (co seu REGFER)
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie abonada é maior ca do cultivo")
```

Despois:
```python
def _validar(session: Session, datos: DatosAbonado, horta_id: int, hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do abonado non pode ser futura")
    # Quen o fixo pode ser unha persoa do equipo ou a empresa de servizos (co seu REGFER)
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    comprobar_maquina(session, horta_id, datos.maquina_id)
```

### Paso 19 — `src/horta/services/abonados.py`

Antes:
```python
def _copiar(abonado: Abonado, datos: DatosAbonado, horta_id: int, cultivo: Cultivo) -> None:
    abonado.horta_id = horta_id
    abonado.cultivo_id = datos.cultivo_id
    abonado.data_inicio = datos.data_inicio
    abonado.data_fin = datos.data_fin or datos.data_inicio
    abonado.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
```

Despois:
```python
def _copiar(abonado: Abonado, datos: DatosAbonado, horta_id: int,
            leiras: list[LeiraValida]) -> None:
    abonado.horta_id = horta_id
    abonado.leiras = [AbonadoCultivo(cultivo_id=le.cultivo.id, superficie_ha=le.superficie_ha)
                      for le in leiras]
    abonado.data_inicio = datos.data_inicio
    abonado.data_fin = datos.data_fin or datos.data_inicio
```

### Paso 20 — `src/horta/services/abonados.py`

Antes:
```python
    cultivo, horta_id = _horta_do_cultivo(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    abonado = Abonado(creado_por=actor.id)
    _copiar(abonado, datos, horta_id, cultivo)
```

Despois:
```python
    horta_id, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras))
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, horta_id, hoxe or date.today())
    abonado = Abonado(creado_por=actor.id)
    _copiar(abonado, datos, horta_id, leiras)
```

### Paso 21 — `src/horta/services/abonados.py`

Antes:
```python
    cultivo, horta_id = _horta_do_cultivo(session, datos.cultivo_id)
    if horta_id != abonado.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    _copiar(abonado, datos, horta_id, cultivo)
```

Despois:
```python
    _, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras),
        abonado.horta_id)
    _validar(session, datos, abonado.horta_id, hoxe or date.today())
    _copiar(abonado, datos, abonado.horta_id, leiras)
```

### Paso 22 — `src/horta/services/abonados.py`

Antes:
```python
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
```

Despois:
```python
        consulta = consulta.filter(Abonado.leiras.any(AbonadoCultivo.cultivo_id == cultivo_id))
```

### Paso 23 — `src/horta/services/parcelas.py`

Antes:
```python
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
from horta.models.rega import Rega
```

Despois:
```python
from horta.models.abonado import AbonadoCultivo
from horta.models.analise import Analise
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import LaborCultivo
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
from horta.models.rega import RegaCultivo
```

### Paso 24 — `src/horta/services/parcelas.py`

Antes:
```python
    if ids_cultivos and session.query(Abonado).filter(
        Abonado.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten abonados rexistrados e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(Rega).filter(Rega.cultivo_id.in_(ids_cultivos)).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten regas rexistradas e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(Labor).filter(Labor.cultivo_id.in_(ids_cultivos)).first():
```

Despois:
```python
    if ids_cultivos and session.query(AbonadoCultivo).filter(
        AbonadoCultivo.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten abonados rexistrados e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(RegaCultivo).filter(
            RegaCultivo.cultivo_id.in_(ids_cultivos)).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten regas rexistradas e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(LaborCultivo).filter(
            LaborCultivo.cultivo_id.in_(ids_cultivos)).first():
```

### Paso 25 — `src/horta/services/cultivos.py`

Antes:
```python
from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
from horta.models.rega import Rega
```

Despois:
```python
from horta.models.abonado import AbonadoCultivo
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import LaborCultivo
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
from horta.models.rega import RegaCultivo
```

### Paso 26 — `src/horta/services/cultivos.py`

Antes:
```python
    if session.query(Abonado).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten abonados rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Rega).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Labor).filter_by(cultivo_id=cultivo.id).first():
```

Despois:
```python
    if session.query(AbonadoCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten abonados rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(RegaCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(LaborCultivo).filter_by(cultivo_id=cultivo.id).first():
```

### Paso 27 — `tests/services/test_abonados.py`

Antes:
```python
    assert abonado.superficie_ha == 0.2 and abonado.data_fin == date(2026, 4, 1)
```

Despois:
```python
    assert abonado.leiras[0].superficie_ha == 0.2 and abonado.data_fin == date(2026, 4, 1)
```

### Paso 28 — `tests/services/test_abonados_conservar.py`

Antes:
```python
from horta.models.abonado import Abonado
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoCultivo
```

### Paso 29 — `tests/services/test_abonados_conservar.py`

Antes:
```python
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=0.1, tipo_fertilizacion="1",
                        metodo="1"))
```

Despois:
```python
    session.add(Abonado(horta_id=horta.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), tipo_fertilizacion="1",
                        metodo="1",
                        leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1)]))
```

### Paso 30 — `tests/services/test_abonados_conservar_horta.py`

Antes:
```python
from horta.models.abonado import Abonado, Fertilizante
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoCultivo, Fertilizante
```

### Paso 31 — `tests/services/test_abonados_conservar_horta.py`

Antes:
```python
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=0.1, tipo_fertilizacion="1",
                        metodo="1"))
```

Despois:
```python
    session.add(Abonado(horta_id=horta.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), tipo_fertilizacion="1",
                        metodo="1",
                        leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1)]))
```

### Paso 32 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
    assert rega.sistema_rega is None and rega.cantidade is None and rega.superficie_ha is None
```

Despois:
```python
    assert rega.sistema_rega is None and rega.cantidade is None
    assert rega.leiras[0].superficie_ha is None
```

### Paso 33 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
    assert labor.superficie_ha is None
```

Despois:
```python
    assert labor.leiras[0].superficie_ha is None
```

### Paso 34 — `tests/services/test_caderno.py`

Antes:
```python
from horta.models.abonado import Abonado, Fertilizante
from horta.models.analise import Analise
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.rega import Rega
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoCultivo, Fertilizante
from horta.models.analise import Analise
from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.rega import Rega, RegaCultivo
```

### Paso 35 — `tests/services/test_caderno.py`

Antes:
```python
        Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 3, 10),
                data_fin=date(2026, 3, 10), superficie_ha=0.2, fertilizante_id=abono.id,
                dose=200, unidade="17", tipo_fertilizacion="1", metodo="1"),
        Rega(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1),
             data_fin=date(2026, 7, 1), superficie_ha=0.2, sistema_rega="6", cantidade=4,
             unidade="3"),
        Analise(horta_id=horta.id, material_analizado="3", data_mostraxe=date(2026, 2, 1),
                parcela_id=parcela.id, ph=5.6),
        # fóra do período: non debe saír
        Rega(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2025, 7, 1),
             data_fin=date(2025, 7, 1), superficie_ha=0.2, sistema_rega="6", cantidade=9,
             unidade="3"),
```

Despois:
```python
        Abonado(horta_id=horta.id, data_inicio=date(2026, 3, 10),
                data_fin=date(2026, 3, 10), fertilizante_id=abono.id,
                dose=200, unidade="17", tipo_fertilizacion="1", metodo="1",
                leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]),
        Rega(horta_id=horta.id, data_inicio=date(2026, 7, 1),
             data_fin=date(2026, 7, 1), sistema_rega="6", cantidade=4,
             unidade="3",
             leiras=[RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]),
        Analise(horta_id=horta.id, material_analizado="3", data_mostraxe=date(2026, 2, 1),
                parcela_id=parcela.id, ph=5.6),
        # fóra do período: non debe saír
        Rega(horta_id=horta.id, data_inicio=date(2025, 7, 1),
             data_fin=date(2025, 7, 1), sistema_rega="6", cantidade=9,
             unidade="3",
             leiras=[RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]),
```

### Paso 36 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
from horta.models.abonado import Abonado
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoCultivo
```

### Paso 37 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 3, 1),
                        data_fin=date(2026, 3, 1), superficie_ha=0.1, fertilizante_id=compost.id,
                        dose=10, unidade="29", tipo_fertilizacion="1", metodo="1"))
```

Despois:
```python
    session.add(Abonado(horta_id=horta.id, data_inicio=date(2026, 3, 1),
                        data_fin=date(2026, 3, 1), fertilizante_id=compost.id,
                        dose=10, unidade="29", tipo_fertilizacion="1", metodo="1",
                        leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1)]))
```

### Paso 38 — `tests/services/test_labores.py`

Antes:
```python
    assert labor.superficie_ha == 0.2
```

Despois:
```python
    assert labor.leiras[0].superficie_ha == 0.2
```

### Paso 39 — `tests/services/test_plan_abonado.py`

Antes:
```python
from horta.models.abonado import Abonado
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoCultivo
```

### Paso 40 — `tests/services/test_plan_abonado.py`

Antes:
```python
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=superficie,
                        fertilizante_id=abono.id, dose=dose, unidade=unidade,
                        tipo_fertilizacion="1", metodo="1"))
```

Despois:
```python
    session.add(Abonado(horta_id=horta.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), 
                        fertilizante_id=abono.id, dose=dose, unidade=unidade,
                        tipo_fertilizacion="1", metodo="1",
                        leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=superficie)]))
```

### Paso 41 — `tests/services/test_regas.py`

Antes:
```python
    assert rega.superficie_ha == 0.01 and rega.data_fin == date(2026, 7, 1)
```

Despois:
```python
    assert rega.leiras[0].superficie_ha == 0.01 and rega.data_fin == date(2026, 7, 1)
```

### Paso 42 — `tests/services/test_regas_conservar.py`

Antes:
```python
from horta.models.rega import Rega
```

Despois:
```python
from horta.models.rega import Rega, RegaCultivo
```

### Paso 43 — `tests/services/test_regas_conservar.py`

Antes:
```python
    session.add(Rega(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1),
                     data_fin=date(2026, 7, 1), superficie_ha=0.01, sistema_rega="6",
                     cantidade=300, unidade="4"))
```

Despois:
```python
    session.add(Rega(horta_id=horta.id, data_inicio=date(2026, 7, 1),
                     data_fin=date(2026, 7, 1), sistema_rega="6",
                     cantidade=300, unidade="4",
                     leiras=[RegaCultivo(cultivo_id=cultivo.id, superficie_ha=0.01)]))
```

### Paso 44 — `src/horta/models/labor.py`

Antes:
```python
"""Labor cultural (CUE bloque 5): cada labor feito nun cultivo. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Labor(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "labor"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    tipo_labor: Mapped[str] = mapped_column(String(20))
    restos_desbroce_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_poda_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_cobertura: Mapped[str | None] = mapped_column(String(20), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
"""Labor cultural (CUE bloque 5): cada labor, nunha ou varias leiras. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Labor(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "labor"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    tipo_labor: Mapped[str] = mapped_column(String(20))
    restos_desbroce_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_poda_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_cobertura: Mapped[str | None] = mapped_column(String(20), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h: Mapped[float | None] = mapped_column(Float, default=None)
    # As leiras (cultivos) onde se fixo: unha ou varias
    # (docs/superpowers/specs/2026-10-28-varias-leiras-design.md)
    leiras: Mapped[list[LaborCultivo]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha


class LaborCultivo(Base):
    """Cada leira (cultivo) dun labor, coa superficie onde se fixo."""

    __tablename__ = "labor_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    labor_id: Mapped[int] = mapped_column(ForeignKey("labor.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 45 — `src/horta/models/rega.py`

Antes:
```python
"""Rega (CUE bloque 10): cada rega dun cultivo. Baixa lóxica."""
```

Despois:
```python
"""Rega (CUE bloque 10): cada rega, nunha ou varias leiras. Baixa lóxica."""
```

### Paso 46 — `src/horta/models/rega.py`

Antes:
```python
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    sistema_rega: Mapped[str | None] = mapped_column(String(20), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str] = mapped_column(String(20))
    orixe_auga: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)

    boas_practicas: Mapped[list[RegaBoaPractica]] = relationship(cascade="all, delete-orphan")


class RegaBoaPractica(Base):
    __tablename__ = "rega_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    rega_id: Mapped[int] = mapped_column(ForeignKey("rega.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
```

Despois:
```python
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    sistema_rega: Mapped[str | None] = mapped_column(String(20), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str] = mapped_column(String(20))
    orixe_auga: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)

    boas_practicas: Mapped[list[RegaBoaPractica]] = relationship(cascade="all, delete-orphan")
    # As leiras (cultivos) onde se fixo: unha ou varias
    # (docs/superpowers/specs/2026-10-28-varias-leiras-design.md)
    leiras: Mapped[list[RegaCultivo]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha


class RegaBoaPractica(Base):
    __tablename__ = "rega_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    rega_id: Mapped[int] = mapped_column(ForeignKey("rega.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class RegaCultivo(Base):
    """Cada leira (cultivo) dunha rega, coa superficie onde se fixo."""

    __tablename__ = "rega_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    rega_id: Mapped[int] = mapped_column(ForeignKey("rega.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 47 — `src/horta/models/abonado.py`

Antes:
```python
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
```

### Paso 48 — `src/horta/models/abonado.py`

Antes:
```python


class AbonadoBoaPractica(Base):
    __tablename__ = "abonado_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    abonado_id: Mapped[int] = mapped_column(ForeignKey("abonado.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
```

Despois:
```python
    # As leiras (cultivos) onde se fixo: unha ou varias
    # (docs/superpowers/specs/2026-10-28-varias-leiras-design.md)
    leiras: Mapped[list[AbonadoCultivo]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha


class AbonadoBoaPractica(Base):
    __tablename__ = "abonado_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    abonado_id: Mapped[int] = mapped_column(ForeignKey("abonado.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class AbonadoCultivo(Base):
    """Cada leira (cultivo) dun abonado, coa superficie onde se fixo."""

    __tablename__ = "abonado_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    abonado_id: Mapped[int] = mapped_column(ForeignKey("abonado.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Varias leiras (1/5): datos e servizos: feito.

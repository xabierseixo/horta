# Tarefa 081a — Parte común (2/9): o resto dos traballos usan a parte común

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Colleita, pastoreo, coidados, rega, tratamento en instalacións, entradas e saídas, produción e abonado herdan a parte común en vez de repetila. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `src/horta/models/colleita.py`
- `src/horta/models/pastoreo.py`
- `src/horta/models/coidado_animal.py`
- `src/horta/models/rega.py`
- `src/horta/models/tratamento_instalacion.py`
- `src/horta/models/movemento_animal.py`
- `src/horta/models/producion_animal.py`
- `src/horta/models/abonado.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/colleita.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Colleita(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Colleita(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 2 — `src/horta/models/colleita.py`

Antes:
```python
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    # Trazabilidade: quen apuntou a colleita
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 3 — `src/horta/models/pastoreo.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Pastoreo(Base):
    __tablename__ = "pastoreo"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    # Baleira mentres o gando segue no pasto
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Pastoreo(ParteComun, FeitoPor, Base):
    __tablename__ = "pastoreo"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    # Baleira mentres o gando segue no pasto
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
```

### Paso 4 — `src/horta/models/coidado_animal.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class CoidadoAnimal(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class CoidadoAnimal(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 5 — `src/horta/models/coidado_animal.py`

Antes:
```python
    matricula: Mapped[str | None] = mapped_column(String(20), default=None)
    # Parte común
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    matricula: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 6 — `src/horta/models/rega.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Rega(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Rega(ParteComun, FeitoPor, Base):
```

### Paso 7 — `src/horta/models/rega.py`

Antes:
```python
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)
```

### Paso 8 — `src/horta/models/tratamento_instalacion.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base

TIPOS_INSTALACION = {"postcolleita": "Postcolleita (no produto vexetal)",
                     "local": "Local de almacenamento", "transporte": "Medio de transporte"}


class TratamentoInstalacion(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun

TIPOS_INSTALACION = {"postcolleita": "Postcolleita (no produto vexetal)",
                     "local": "Local de almacenamento", "transporte": "Medio de transporte"}


class TratamentoInstalacion(ParteComun, FeitoPor, Base):
```

### Paso 9 — `src/horta/models/tratamento_instalacion.py`

Antes:
```python
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 10 — `src/horta/models/movemento_animal.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class MovementoAnimal(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class MovementoAnimal(ParteComun, FeitoPor, Base):
```

### Paso 11 — `src/horta/models/movemento_animal.py`

Antes:
```python
    causa: Mapped[str | None] = mapped_column(String(300), default=None)
    # Parte común
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    causa: Mapped[str | None] = mapped_column(String(300), default=None)
```

### Paso 12 — `src/horta/models/producion_animal.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ProducionAnimal(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class ProducionAnimal(ParteComun, FeitoPor, Base):
```

### Paso 13 — `src/horta/models/producion_animal.py`

Antes:
```python
    lote: Mapped[str] = mapped_column(String(40))
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    lote: Mapped[str] = mapped_column(String(40))
```

### Paso 14 — `src/horta/models/abonado.py`

Antes:
```python
from horta.db import Base
```

Despois:
```python
from horta.db import Base
from horta.models.traballo import ConMaquina, ParteComun
```

### Paso 15 — `src/horta/models/abonado.py`

Antes:
```python
class Abonado(Base):
```

Despois:
```python
class Abonado(ParteComun, ConMaquina, Base):
```

### Paso 16 — `src/horta/models/abonado.py`

Antes:
```python
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (2/9): o resto dos traballos usan a parte común: feito.

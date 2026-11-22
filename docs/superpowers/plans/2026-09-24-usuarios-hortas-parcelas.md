# Usuarios, Hortas, Parcelas e Animais — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar autenticación de usuarios, xestión de hortas con varios membros por horta, e xestión de parcelas e animais dentro de cada horta, con persistencia real en SQLite vía SQLAlchemy + Alembic, substituíndo o mockup actual de `src/horta/main.py`.

**Architecture:** Capas por tipo (Interface NiceGUI → servizos → modelos SQLAlchemy → SQLite), cada capa dividida en ficheiros por entidade. A capa de servizos non depende de NiceGUI e é onde vive toda a lóxica de permisos; a UI só chama a servizos e amosa o resultado.

**Tech Stack:** Python 3.11, NiceGUI (UI + servidor), SQLAlchemy 2.0 (ORM), Alembic (migracións), SQLite (BD), bcrypt (hash de contrasinais), pytest/Ruff/mypy, xestionado con `uv`.

**Spec:** `docs/superpowers/specs/2026-09-24-usuarios-hortas-parcelas-design.md`

## Global Constraints

- Python >=3.11 (fixado en `.python-version` e `pyproject.toml`).
- Preferir sempre compoñentes/patróns xa presentes no stack decidido (NiceGUI, SQLAlchemy, Alembic, bcrypt) antes ca engadir dependencias novas — non introducir librarías fóra das xa previstas nesta spec.
- Autenticación por sesión de NiceGUI (`app.storage.user`), sen autorrexistro público — usuarios créanse só dende `/admin/usuarios`.
- Toda comprobación de permiso vive na capa de servizos (nunca na UI), lanzando `PermisoDenegadoError` cando corresponda.
- Campos SIGPAC e `uso_aproveitamento`/`secano_regadio` de Parcela son sempre opcionais a nivel de BD.
- Sen borrado lóxico nesta iteración (só se aplicará aos rexistros regulados do caderno de explotación, aínda non implementados).
- Todo o texto de UI e nomes de dominio en galego.

---

## Task 1: Configuración de ferramentas (pytest, Ruff, mypy, bcrypt)

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/` (directorio, sen ficheiros de test aínda)

**Interfaces:**
- Consumes: nada (é a base do resto do plan).
- Produces: `uv run pytest`, `uv run ruff check .` e `uv run mypy src` executables e limpos; dependencia `bcrypt` dispoñible para importar.

- [ ] **Step 1: Engadir a dependencia de execución `bcrypt`**

Run: `uv add bcrypt`

Expected: `pyproject.toml` gaña `bcrypt` en `[project] dependencies`, e `uv.lock` actualízase.

- [ ] **Step 2: Engadir as dependencias de desenvolvemento `pytest`, `ruff`, `mypy`**

Run: `uv add --dev pytest ruff mypy`

Expected: `pyproject.toml` gaña unha sección `[dependency-groups]` (ou `[tool.uv] dev-dependencies`, segundo a versión de uv) con `pytest`, `ruff` e `mypy`.

- [ ] **Step 3: Configurar pytest, Ruff e mypy en `pyproject.toml`**

Engadir ao final de `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true
disallow_untyped_defs = false
```

- [ ] **Step 4: Crear o directorio de tests**

Run: `mkdir -p tests`

- [ ] **Step 5: Verificar que as tres ferramentas corren sen erro**

Run: `uv run pytest`
Expected: `no tests ran` (ou equivalente), sen erros de configuración.

Run: `uv run ruff check .`
Expected: sen erros (pode haber avisos sobre `src/horta/main.py` actual; se os houber, ignóraos nesta tarefa — non é obxecto desta tarefa arranxalos).

Run: `uv run mypy src`
Expected: sen erros de configuración (pode haber avisos sobre o código actual; ignóraos nesta tarefa).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: configurar pytest, ruff, mypy e engadir bcrypt"
```

---

## Task 2: Módulo de base de datos e fixture de tests

**Files:**
- Create: `src/horta/db.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `horta.db.Base` (clase base declarativa de SQLAlchemy, para que todos os modelos herden dela).
  - `horta.db.engine`, `horta.db.SessionLocal` (sessionmaker).
  - `horta.db.get_session()` (context manager que devolve unha `Session` e péchaa ao saír).
  - Fixture de pytest `session` (en `tests/conftest.py`), dispoñible en calquera test sen importar nada — devolve unha `sqlalchemy.orm.Session` sobre unha BD SQLite en memoria nova, coas táboas xa creadas.

- [ ] **Step 1: Crear `src/horta/db.py`**

```python
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("HORTA_DATABASE_URL", "sqlite:///horta.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Step 2: Crear `tests/conftest.py` cunha fixture `session` illada por test**

```python
from __future__ import annotations

from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from horta.db import Base

import horta.models  # noqa: F401  (rexistra todos os modelos en Base.metadata)


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
```

Este `conftest.py` importa `horta.models`, que aínda non existe — créase na Task 3. Este ficheiro non se poderá executar ata completar a Task 3, iso é normal (o test de fume final desa tarefa é o que o verifica).

- [ ] **Step 3: Crear un paquete `horta.models` baleiro provisionalmente para poder importar `horta.db` sen erro**

Run: `mkdir -p src/horta/models && touch src/horta/models/__init__.py`

- [ ] **Step 4: Verificar que `horta.db` se importa sen erro**

Run: `uv run python -c "from horta.db import Base, get_session; print('ok')"`
Expected: imprime `ok`.

- [ ] **Step 5: Commit**

```bash
git add src/horta/db.py src/horta/models/__init__.py tests/conftest.py
git commit -m "feat: engadir módulo de base de datos e fixture de tests"
```

---

## Task 3: Modelo Usuario

**Files:**
- Create: `src/horta/models/usuario.py`
- Modify: `src/horta/models/__init__.py`
- Test: `tests/models/test_usuario.py`

**Interfaces:**
- Consumes: `horta.db.Base` (Task 2).
- Produces:
  - `horta.models.usuario.RolGlobal` (enum: `ADMIN = "admin"`, `USUARIO = "usuario"`).
  - `horta.models.usuario.Usuario` (campos: `id: int`, `nome: str`, `email: str` único, `password_hash: str`, `rol: RolGlobal`, `activo: bool`, `created_at: datetime`).
  - Reexportados en `horta.models` como `Usuario`, `RolGlobal`.

- [ ] **Step 1: Escribir o test que falla**

Crear `tests/models/test_usuario.py`:

```python
from horta.models.usuario import RolGlobal, Usuario


def test_crear_e_consultar_usuario(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    atopado = session.query(Usuario).filter_by(email="ana@example.com").one()

    assert atopado.nome == "Ana"
    assert atopado.rol == RolGlobal.USUARIO
    assert atopado.activo is True
    assert atopado.created_at is not None
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/models/test_usuario.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.models.usuario'`).

- [ ] **Step 3: Implementar `src/horta/models/usuario.py`**

```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class RolGlobal(enum.Enum):
    ADMIN = "admin"
    USUARIO = "usuario"


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[RolGlobal] = mapped_column(Enum(RolGlobal), default=RolGlobal.USUARIO)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 4: Actualizar `src/horta/models/__init__.py`**

```python
from horta.models.usuario import RolGlobal, Usuario

__all__ = ["RolGlobal", "Usuario"]
```

- [ ] **Step 5: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/models/test_usuario.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/usuario.py src/horta/models/__init__.py tests/models/test_usuario.py
git commit -m "feat: engadir modelo Usuario"
```

---

## Task 4: Servizo de autenticación

**Files:**
- Create: `src/horta/services/__init__.py`
- Create: `src/horta/services/auth.py`
- Test: `tests/services/test_auth.py`

**Interfaces:**
- Consumes: `horta.models.usuario.Usuario`, `RolGlobal` (Task 3).
- Produces:
  - `horta.services.auth.hash_password(password: str) -> str`
  - `horta.services.auth.verify_password(password: str, password_hash: str) -> bool`
  - `horta.services.auth.autenticar(session: Session, email: str, password: str) -> Usuario | None`

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_auth.py`:

```python
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import autenticar, hash_password, verify_password


def test_hash_password_non_garda_texto_plano():
    hashed = hash_password("contrasinal123")
    assert hashed != "contrasinal123"


def test_verify_password_acepta_contrasinal_correcto():
    hashed = hash_password("contrasinal123")
    assert verify_password("contrasinal123", hashed) is True


def test_verify_password_rexeita_contrasinal_incorrecto():
    hashed = hash_password("contrasinal123")
    assert verify_password("outra-cousa", hashed) is False


def test_autenticar_con_credenciais_correctas(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    resultado = autenticar(session, "ana@example.com", "segredo")

    assert resultado is not None
    assert resultado.email == "ana@example.com"


def test_autenticar_con_contrasinal_incorrecto(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    assert autenticar(session, "ana@example.com", "incorrecto") is None


def test_autenticar_usuario_inactivo(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=False,
    )
    session.add(usuario)
    session.commit()

    assert autenticar(session, "ana@example.com", "segredo") is None


def test_autenticar_email_inexistente(session):
    assert autenticar(session, "non-existe@example.com", "calquera") is None
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_auth.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services'`).

- [ ] **Step 3: Crear `src/horta/services/__init__.py` (baleiro)**

Run: `mkdir -p src/horta/services && touch src/horta/services/__init__.py`

- [ ] **Step 4: Implementar `src/horta/services/auth.py`**

```python
from __future__ import annotations

import bcrypt
from sqlalchemy.orm import Session

from horta.models.usuario import Usuario


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def autenticar(session: Session, email: str, password: str) -> Usuario | None:
    usuario = session.query(Usuario).filter_by(email=email).one_or_none()
    if usuario is None or not usuario.activo:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario
```

- [ ] **Step 5: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_auth.py -v`
Expected: PASS (7 tests).

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/__init__.py src/horta/services/auth.py tests/services/test_auth.py
git commit -m "feat: engadir servizo de autenticación con bcrypt"
```

---

## Task 5: Excepcións de dominio e servizo de usuarios

**Files:**
- Create: `src/horta/services/errors.py`
- Create: `src/horta/services/usuarios.py`
- Test: `tests/services/test_usuarios.py`

**Interfaces:**
- Consumes: `horta.models.usuario.Usuario`, `RolGlobal` (Task 3); `horta.services.auth.hash_password` (Task 4).
- Produces:
  - `horta.services.errors.PermisoDenegadoError` (Exception).
  - `horta.services.usuarios.crear_usuario(session, actor, nome, email, password, rol=RolGlobal.USUARIO) -> Usuario`
  - `horta.services.usuarios.actualizar_usuario(session, actor, usuario, *, nome=None, rol=None) -> Usuario`
  - `horta.services.usuarios.desactivar_usuario(session, actor, usuario) -> Usuario`
  - `horta.services.usuarios.listar_usuarios(session, actor) -> list[Usuario]`

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_usuarios.py`:

```python
import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import PermisoDenegadoError
from horta.services.usuarios import (
    actualizar_usuario,
    crear_usuario,
    desactivar_usuario,
    listar_usuarios,
)


def _crear_admin(session) -> Usuario:
    admin = Usuario(
        nome="Admin",
        email="admin@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.ADMIN,
        activo=True,
    )
    session.add(admin)
    session.commit()
    return admin


def _crear_usuario_normal(session) -> Usuario:
    normal = Usuario(
        nome="Normal",
        email="normal@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(normal)
    session.commit()
    return normal


def test_admin_pode_crear_usuario(session):
    admin = _crear_admin(session)

    novo = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    assert novo.id is not None
    assert novo.rol == RolGlobal.USUARIO
    assert novo.activo is True


def test_usuario_normal_non_pode_crear_usuario(session):
    normal = _crear_usuario_normal(session)

    with pytest.raises(PermisoDenegadoError):
        crear_usuario(session, normal, "Bea", "bea@example.com", "contrasinal")


def test_admin_pode_actualizar_usuario(session):
    admin = _crear_admin(session)
    usuario = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    actualizado = actualizar_usuario(session, admin, usuario, nome="Beatriz", rol=RolGlobal.ADMIN)

    assert actualizado.nome == "Beatriz"
    assert actualizado.rol == RolGlobal.ADMIN


def test_admin_pode_desactivar_usuario(session):
    admin = _crear_admin(session)
    usuario = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    desactivado = desactivar_usuario(session, admin, usuario)

    assert desactivado.activo is False


def test_listar_usuarios_require_admin(session):
    admin = _crear_admin(session)
    normal = _crear_usuario_normal(session)
    crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    usuarios = listar_usuarios(session, admin)
    assert {u.email for u in usuarios} == {
        "admin@example.com",
        "normal@example.com",
        "bea@example.com",
    }

    with pytest.raises(PermisoDenegadoError):
        listar_usuarios(session, normal)
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_usuarios.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.errors'`).

- [ ] **Step 3: Implementar `src/horta/services/errors.py`**

```python
from __future__ import annotations


class PermisoDenegadoError(Exception):
    """O usuario que executa a acción non ten permiso suficiente."""
```

- [ ] **Step 4: Implementar `src/horta/services/usuarios.py`**

```python
from __future__ import annotations

from sqlalchemy.orm import Session

from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import PermisoDenegadoError


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só un administrador pode xestionar usuarios")


def crear_usuario(
    session: Session,
    actor: Usuario,
    nome: str,
    email: str,
    password: str,
    rol: RolGlobal = RolGlobal.USUARIO,
) -> Usuario:
    _esixir_admin(actor)
    usuario = Usuario(
        nome=nome,
        email=email,
        password_hash=hash_password(password),
        rol=rol,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def actualizar_usuario(
    session: Session,
    actor: Usuario,
    usuario: Usuario,
    *,
    nome: str | None = None,
    rol: RolGlobal | None = None,
) -> Usuario:
    _esixir_admin(actor)
    if nome is not None:
        usuario.nome = nome
    if rol is not None:
        usuario.rol = rol
    session.commit()
    return usuario


def desactivar_usuario(session: Session, actor: Usuario, usuario: Usuario) -> Usuario:
    _esixir_admin(actor)
    usuario.activo = False
    session.commit()
    return usuario


def listar_usuarios(session: Session, actor: Usuario) -> list[Usuario]:
    _esixir_admin(actor)
    return list(session.query(Usuario).order_by(Usuario.nome).all())
```

- [ ] **Step 5: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_usuarios.py -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/errors.py src/horta/services/usuarios.py tests/services/test_usuarios.py
git commit -m "feat: engadir servizo de xestión de usuarios"
```

---

## Task 6: Modelos Horta e HortaMembro

**Files:**
- Create: `src/horta/models/horta.py`
- Modify: `src/horta/models/__init__.py`
- Test: `tests/models/test_horta.py`

**Interfaces:**
- Consumes: `horta.db.Base` (Task 2); `horta.models.usuario.Usuario` (Task 3, para a FK).
- Produces:
  - `horta.models.horta.RolHorta` (enum: `ADMIN = "admin"`, `EDITOR = "editor"`, `LECTOR = "lector"`).
  - `horta.models.horta.Horta` (campos: `id`, `nome`, `descricion: str | None`, `uso_profesional: bool`, `created_at`).
  - `horta.models.horta.HortaMembro` (PK composta `horta_id, usuario_id`; campo `rol: RolHorta`).
  - Reexportados en `horta.models` como `Horta`, `HortaMembro`, `RolHorta`.

- [ ] **Step 1: Escribir o test que falla**

Crear `tests/models/test_horta.py`:

```python
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario


def test_crear_horta_e_membro(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    horta = Horta(nome="A miña horta", uso_profesional=False)
    session.add(horta)
    session.flush()

    membro = HortaMembro(horta_id=horta.id, usuario_id=usuario.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.commit()

    atopado = session.get(HortaMembro, (horta.id, usuario.id))
    assert atopado is not None
    assert atopado.rol == RolHorta.ADMIN
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/models/test_horta.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.models.horta'`).

- [ ] **Step 3: Implementar `src/horta/models/horta.py`**

```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class RolHorta(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    LECTOR = "lector"


class Horta(Base):
    __tablename__ = "horta"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    uso_profesional: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class HortaMembro(Base):
    __tablename__ = "horta_membro"

    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    rol: Mapped[RolHorta] = mapped_column(Enum(RolHorta), default=RolHorta.LECTOR)
```

- [ ] **Step 4: Actualizar `src/horta/models/__init__.py`**

```python
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario

__all__ = ["RolGlobal", "Usuario", "Horta", "HortaMembro", "RolHorta"]
```

- [ ] **Step 5: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/models/test_horta.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/horta.py src/horta/models/__init__.py tests/models/test_horta.py
git commit -m "feat: engadir modelos Horta e HortaMembro"
```

---

## Task 7: Servizo de hortas (crear, membros, listar)

**Files:**
- Create: `src/horta/services/hortas.py`
- Test: `tests/services/test_hortas.py`

**Interfaces:**
- Consumes: `horta.models.horta.{Horta, HortaMembro, RolHorta}` (Task 6); `horta.models.usuario.Usuario` (Task 3); `horta.services.errors.PermisoDenegadoError` (Task 5).
- Produces:
  - `horta.services.hortas.comprobar_rol_horta(session, horta_id, usuario, roles_permitidos: set[RolHorta]) -> HortaMembro` (lanza `PermisoDenegadoError` se non hai membro con rol permitido; úsase tamén dende `services/parcelas.py` na Task 9).
  - `horta.services.hortas.crear_horta(session, actor, nome, descricion=None, uso_profesional=False) -> Horta`
  - `horta.services.hortas.engadir_membro(session, actor, horta_id, usuario_obxectivo, rol: RolHorta) -> HortaMembro`
  - `horta.services.hortas.cambiar_rol_membro(session, actor, horta_id, usuario_obxectivo_id, novo_rol: RolHorta) -> HortaMembro`
  - `horta.services.hortas.quitar_membro(session, actor, horta_id, usuario_obxectivo_id) -> None`
  - `horta.services.hortas.listar_hortas_usuario(session, usuario) -> list[tuple[Horta, RolHorta]]`

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_hortas.py`:

```python
import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import (
    cambiar_rol_membro,
    crear_horta,
    engadir_membro,
    listar_hortas_usuario,
    quitar_membro,
)


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


def test_crear_horta_fai_ao_creador_admin_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")

    horta = crear_horta(session, ana, "A miña horta")

    [(horta_listada, rol)] = listar_hortas_usuario(session, ana)
    assert horta_listada.id == horta.id
    assert rol == RolHorta.ADMIN


def test_admin_da_horta_pode_engadir_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)

    hortas_de_bea = listar_hortas_usuario(session, bea)
    assert hortas_de_bea == [(horta, RolHorta.EDITOR)]


def test_non_admin_non_pode_engadir_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)

    with pytest.raises(PermisoDenegadoError):
        engadir_membro(session, bea, horta.id, carlos, RolHorta.LECTOR)


def test_admin_pode_cambiar_rol_e_quitar_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)

    cambiar_rol_membro(session, ana, horta.id, bea.id, RolHorta.EDITOR)
    assert listar_hortas_usuario(session, bea) == [(horta, RolHorta.EDITOR)]

    quitar_membro(session, ana, horta.id, bea.id)
    assert listar_hortas_usuario(session, bea) == []


def test_usuario_sen_relacion_non_ve_a_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    crear_horta(session, ana, "A miña horta")

    assert listar_hortas_usuario(session, carlos) == []
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_hortas.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.hortas'`).

- [ ] **Step 3: Implementar `src/horta/services/hortas.py`**

```python
from __future__ import annotations

from sqlalchemy.orm import Session

from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import Usuario
from horta.services.errors import PermisoDenegadoError


def _obter_membro(session: Session, horta_id: int, usuario_id: int) -> HortaMembro | None:
    return session.get(HortaMembro, (horta_id, usuario_id))


def comprobar_rol_horta(
    session: Session,
    horta_id: int,
    usuario: Usuario,
    roles_permitidos: set[RolHorta],
) -> HortaMembro:
    membro = _obter_membro(session, horta_id, usuario.id)
    if membro is None or membro.rol not in roles_permitidos:
        raise PermisoDenegadoError("Non tes permiso suficiente nesta horta")
    return membro


def crear_horta(
    session: Session,
    actor: Usuario,
    nome: str,
    descricion: str | None = None,
    uso_profesional: bool = False,
) -> Horta:
    horta = Horta(nome=nome, descricion=descricion, uso_profesional=uso_profesional)
    session.add(horta)
    session.flush()
    membro = HortaMembro(horta_id=horta.id, usuario_id=actor.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.commit()
    return horta


def engadir_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo: Usuario,
    rol: RolHorta,
) -> HortaMembro:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = HortaMembro(horta_id=horta_id, usuario_id=usuario_obxectivo.id, rol=rol)
    session.add(membro)
    session.commit()
    return membro


def cambiar_rol_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo_id: int,
    novo_rol: RolHorta,
) -> HortaMembro:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = _obter_membro(session, horta_id, usuario_obxectivo_id)
    if membro is None:
        raise ValueError("Ese usuario non é membro desta horta")
    membro.rol = novo_rol
    session.commit()
    return membro


def quitar_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo_id: int,
) -> None:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = _obter_membro(session, horta_id, usuario_obxectivo_id)
    if membro is not None:
        session.delete(membro)
        session.commit()


def listar_hortas_usuario(session: Session, usuario: Usuario) -> list[tuple[Horta, RolHorta]]:
    membros = session.query(HortaMembro).filter_by(usuario_id=usuario.id).all()
    resultado: list[tuple[Horta, RolHorta]] = []
    for membro in membros:
        horta = session.get(Horta, membro.horta_id)
        assert horta is not None
        resultado.append((horta, membro.rol))
    return resultado
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_hortas.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add src/horta/services/hortas.py tests/services/test_hortas.py
git commit -m "feat: engadir servizo de hortas e membros"
```

---

## Task 8: Modelo Parcela

**Files:**
- Create: `src/horta/models/parcela.py`
- Modify: `src/horta/models/__init__.py`
- Test: `tests/models/test_parcela.py`

**Interfaces:**
- Consumes: `horta.db.Base` (Task 2); `horta.models.horta.Horta` (Task 6, para a FK).
- Produces:
  - `horta.models.parcela.SecanoRegadio` (enum: `SECANO = "secano"`, `REGADIO = "regadio"`).
  - `horta.models.parcela.Parcela` (campos: `id`, `horta_id`, `nome`, `descricion`, `superficie: float | None`, `posicion: str | None`, `uso_aproveitamento: str | None`, `secano_regadio: SecanoRegadio | None`, `sigpac_provincia/concello/poligono/parcela/subparcela: str | None`, `notas: str | None`, `estado: str`, `created_at`).
  - Reexportados en `horta.models` como `Parcela`, `SecanoRegadio`.

- [ ] **Step 1: Escribir o test que falla**

Crear `tests/models/test_parcela.py`:

```python
from horta.models.horta import Horta
from horta.models.parcela import Parcela, SecanoRegadio


def test_crear_parcela_con_campos_opcionais_baleiros(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()

    parcela = Parcela(horta_id=horta.id, nome="Parcela Norte", estado="activa")
    session.add(parcela)
    session.commit()

    atopada = session.query(Parcela).filter_by(nome="Parcela Norte").one()
    assert atopada.horta_id == horta.id
    assert atopada.superficie is None
    assert atopada.sigpac_provincia is None
    assert atopada.secano_regadio is None


def test_crear_parcela_con_campos_sigpac(session):
    horta = Horta(nome="Explotación", uso_profesional=True)
    session.add(horta)
    session.flush()

    parcela = Parcela(
        horta_id=horta.id,
        nome="Parcela 1",
        estado="activa",
        superficie=1200.5,
        secano_regadio=SecanoRegadio.REGADIO,
        sigpac_provincia="15",
        sigpac_concello="30",
        sigpac_poligono="4",
        sigpac_parcela="120",
        sigpac_subparcela="a",
    )
    session.add(parcela)
    session.commit()

    atopada = session.query(Parcela).filter_by(nome="Parcela 1").one()
    assert atopada.secano_regadio == SecanoRegadio.REGADIO
    assert atopada.sigpac_provincia == "15"
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/models/test_parcela.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.models.parcela'`).

- [ ] **Step 3: Implementar `src/horta/models/parcela.py`**

```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class SecanoRegadio(enum.Enum):
    SECANO = "secano"
    REGADIO = "regadio"


class Parcela(Base):
    __tablename__ = "parcela"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    nome: Mapped[str] = mapped_column(String(120))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
    posicion: Mapped[str | None] = mapped_column(String(120), default=None)
    uso_aproveitamento: Mapped[str | None] = mapped_column(String(120), default=None)
    secano_regadio: Mapped[SecanoRegadio | None] = mapped_column(
        Enum(SecanoRegadio), default=None
    )
    sigpac_provincia: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_concello: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_poligono: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_parcela: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_subparcela: Mapped[str | None] = mapped_column(String(10), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="activa")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 4: Actualizar `src/horta/models/__init__.py`**

```python
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.usuario import RolGlobal, Usuario

__all__ = [
    "RolGlobal",
    "Usuario",
    "Horta",
    "HortaMembro",
    "RolHorta",
    "Parcela",
    "SecanoRegadio",
]
```

- [ ] **Step 5: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/models/test_parcela.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/parcela.py src/horta/models/__init__.py tests/models/test_parcela.py
git commit -m "feat: engadir modelo Parcela con campos SIGPAC opcionais"
```

---

## Task 9: Servizo de parcelas (CRUD con permisos)

**Files:**
- Create: `src/horta/services/parcelas.py`
- Test: `tests/services/test_parcelas.py`

**Interfaces:**
- Consumes: `horta.models.parcela.Parcela` (Task 8); `horta.models.horta.RolHorta` (Task 6); `horta.services.hortas.{comprobar_rol_horta, crear_horta, engadir_membro}` (Task 7); `horta.services.errors.PermisoDenegadoError` (Task 5).
- Produces:
  - `horta.services.parcelas.crear_parcela(session, actor, horta_id, nome, **campos) -> Parcela`
  - `horta.services.parcelas.actualizar_parcela(session, actor, parcela, **cambios) -> Parcela`
  - `horta.services.parcelas.eliminar_parcela(session, actor, parcela) -> None`
  - `horta.services.parcelas.listar_parcelas(session, actor, horta_id) -> list[Parcela]`

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_parcelas.py`:

```python
import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)


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


def test_admin_da_horta_pode_crear_parcela(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte", superficie=500.0)

    assert parcela.id is not None
    assert parcela.horta_id == horta.id
    assert parcela.estado == "activa"


def test_editor_pode_crear_parcela_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_parcela(session, bea, horta.id, "Parcela de Bea")

    with pytest.raises(PermisoDenegadoError):
        crear_parcela(session, carlos, horta.id, "Parcela de Carlos")


def test_lector_pode_listar_pero_non_actualizar_nin_eliminar(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    parcelas = listar_parcelas(session, carlos, horta.id)
    assert [p.nome for p in parcelas] == ["Parcela Norte"]

    with pytest.raises(PermisoDenegadoError):
        actualizar_parcela(session, carlos, parcela, nome="Outro nome")

    with pytest.raises(PermisoDenegadoError):
        eliminar_parcela(session, carlos, parcela)


def test_admin_pode_actualizar_e_eliminar_parcela(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    actualizada = actualizar_parcela(session, ana, parcela, nome="Parcela Sur", superficie=800.0)
    assert actualizada.nome == "Parcela Sur"
    assert actualizada.superficie == 800.0

    eliminar_parcela(session, ana, parcela)
    assert listar_parcelas(session, ana, horta.id) == []


def test_campos_sigpac_son_opcionais_ao_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    assert parcela.sigpac_provincia is None
    assert parcela.secano_regadio is None
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_parcelas.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.parcelas'`).

- [ ] **Step 3: Implementar `src/horta/services/parcelas.py`**

```python
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def crear_parcela(
    session: Session,
    actor: Usuario,
    horta_id: int,
    nome: str,
    **campos: Any,
) -> Parcela:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    estado = campos.pop("estado", "activa")
    parcela = Parcela(horta_id=horta_id, nome=nome, estado=estado, **campos)
    session.add(parcela)
    session.commit()
    return parcela


def actualizar_parcela(
    session: Session,
    actor: Usuario,
    parcela: Parcela,
    **cambios: Any,
) -> Parcela:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
    session.commit()
    return parcela


def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(parcela)
    session.commit()


def listar_parcelas(session: Session, actor: Usuario, horta_id: int) -> list[Parcela]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Parcela).filter_by(horta_id=horta_id).order_by(Parcela.nome).all())
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_parcelas.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Executar toda a suite de tests xunta**

Run: `uv run pytest -v`
Expected: PASS (todos os tests de Tasks 3-9, ningún fallo).

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/parcelas.py tests/services/test_parcelas.py
git commit -m "feat: engadir servizo de parcelas con permisos por rol"
```

---

## Task 10: Modelo Animal

**Files:**
- Create: `src/horta/models/animal.py`
- Modify: `src/horta/models/__init__.py`
- Test: `tests/models/test_animal.py`

**Interfaces:**
- Consumes: `horta.db.Base` (Task 2); `horta.models.horta.Horta` (Task 6, para a FK).
- Produces:
  - `horta.models.animal.Animal` (lote de animais; campos: `id`, `horta_id`, `especie: str`, `raza: str | None`, `cantidade: int`, `data_alta: date`, `data_baixa: date | None`, `estado: str`, `notas: str | None`, `created_at: datetime`). Representa un **lote** por especie/raza (p.ex. "6 galiñas Rubia Galega"), non un animal individual.
  - Reexportado en `horta.models` como `Animal`.

- [ ] **Step 1: Escribir o test que falla**

Crear `tests/models/test_animal.py`:

```python
import datetime

from horta.models.animal import Animal
from horta.models.horta import Horta


def test_crear_animal_lote(session):
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()

    animal = Animal(
        horta_id=horta.id,
        especie="galiñas",
        raza="Rubia Galega",
        cantidade=6,
        data_alta=datetime.date(2026, 2, 10),
        estado="activo",
    )
    session.add(animal)
    session.commit()

    atopado = session.query(Animal).filter_by(especie="galiñas").one()
    assert atopado.horta_id == horta.id
    assert atopado.cantidade == 6
    assert atopado.data_baixa is None
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/models/test_animal.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.models.animal'`).

- [ ] **Step 3: Implementar `src/horta/models/animal.py`**

```python
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Animal(Base):
    __tablename__ = "animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    especie: Mapped[str] = mapped_column(String(80))
    raza: Mapped[str | None] = mapped_column(String(120), default=None)
    cantidade: Mapped[int] = mapped_column(Integer, default=1)
    data_alta: Mapped[date] = mapped_column(Date)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    estado: Mapped[str] = mapped_column(String(50), default="activo")
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 4: Actualizar `src/horta/models/__init__.py`**

```python
from horta.models.animal import Animal
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.usuario import RolGlobal, Usuario

__all__ = [
    "RolGlobal",
    "Usuario",
    "Horta",
    "HortaMembro",
    "RolHorta",
    "Parcela",
    "SecanoRegadio",
    "Animal",
]
```

- [ ] **Step 5: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/models/test_animal.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/animal.py src/horta/models/__init__.py tests/models/test_animal.py
git commit -m "feat: engadir modelo Animal"
```

---

## Task 11: Servizo de animais (CRUD con permisos)

**Files:**
- Create: `src/horta/services/animais.py`
- Test: `tests/services/test_animais.py`

**Interfaces:**
- Consumes: `horta.models.animal.Animal` (Task 10); `horta.models.horta.RolHorta` (Task 6); `horta.services.hortas.comprobar_rol_horta` (Task 7).
- Produces:
  - `horta.services.animais.crear_animal(session, actor, horta_id, especie, data_alta, **campos) -> Animal`
  - `horta.services.animais.actualizar_animal(session, actor, animal, **cambios) -> Animal`
  - `horta.services.animais.eliminar_animal(session, actor, animal) -> None`
  - `horta.services.animais.listar_animais(session, actor, horta_id) -> list[Animal]`

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_animais.py`:

```python
import datetime

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro

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
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_animais.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.animais'`).

- [ ] **Step 3: Implementar `src/horta/services/animais.py`**

```python
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def crear_animal(
    session: Session,
    actor: Usuario,
    horta_id: int,
    especie: str,
    data_alta: date,
    **campos: Any,
) -> Animal:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
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
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(animal, campo, valor)
    session.commit()
    return animal


def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(animal)
    session.commit()


def listar_animais(session: Session, actor: Usuario, horta_id: int) -> list[Animal]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Animal).filter_by(horta_id=horta_id).order_by(Animal.especie).all()
    )
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_animais.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Executar toda a suite de tests xunta**

Run: `uv run pytest -v`
Expected: PASS (todos os tests de Tasks 3-11, ningún fallo).

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/animais.py tests/services/test_animais.py
git commit -m "feat: engadir servizo de animais con permisos por rol"
```

---

## Task 12: Migracións Alembic

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako` (xérao Alembic)
- Create: `alembic/versions/<hash>_create_usuario_horta_horta_membro_parcela_animal.py` (xérao Alembic)
- Modify: `.gitignore` (engadir `horta.db`)

**Interfaces:**
- Consumes: `horta.db.Base`, `horta.db.DATABASE_URL` (Task 2); `horta.models` completo (Tasks 3, 6, 8, 10).
- Produces: unha BD SQLite (`horta.db`, ignorada por git) coas cinco táboas creadas por `alembic upgrade head`.

- [ ] **Step 1: Engadir `horta.db` a `.gitignore`**

Engadir ao `.gitignore` existente:

```
horta.db
```

- [ ] **Step 2: Inicializar Alembic**

Run: `uv run alembic init alembic`

Expected: créanse `alembic.ini` na raíz e o directorio `alembic/` con `env.py`, `script.py.mako`, `versions/`.

- [ ] **Step 3: Configurar `alembic/env.py` para usar os nosos modelos e URL de BD**

Editar `alembic/env.py`: substituír a liña `target_metadata = None` e engadir os imports necesarios ao principio do ficheiro (despois dos imports existentes de Alembic):

```python
from horta.db import Base, DATABASE_URL
import horta.models  # noqa: F401  (rexistra os modelos en Base.metadata)

target_metadata = Base.metadata
```

E dentro da función `run_migrations_offline()` e `run_migrations_online()`, asegurar que a URL usada é a nosa (non a de `alembic.ini`). En `run_migrations_online()`, buscar onde se crea o `engine` a partir de `config.get_section(...)` e substituír por:

```python
from sqlalchemy import create_engine

connectable = create_engine(DATABASE_URL)
```

(elimina o bloque `engine_from_config(...)` orixinal se o ficheiro xerado o inclúe).

- [ ] **Step 4: Xerar a primeira revisión por autoxeración**

Run: `uv run alembic revision --autogenerate -m "create usuario horta horta_membro parcela animal"`

Expected: créase un ficheiro en `alembic/versions/` cunha función `upgrade()` que crea as táboas `usuario`, `horta`, `horta_membro`, `parcela` e `animal` (e os tipos `Enum` correspondentes).

- [ ] **Step 5: Revisar a migración xerada**

Abrir o ficheiro novo en `alembic/versions/` e comprobar á man que `upgrade()` inclúe as cinco chamadas `op.create_table(...)` (unha por táboa) coas columnas que definimos nos modelos (Tasks 3, 6, 8, 10). Se falta algunha táboa ou columna, non continuar — revisar `alembic/env.py` (probablemente `target_metadata` non está ben configurado) antes de seguir.

- [ ] **Step 6: Aplicar a migración e comprobar o resultado**

Run: `uv run alembic upgrade head`
Expected: sen erros; créase o ficheiro `horta.db` na raíz do proxecto.

Run: `uv run python -c "
import sqlite3
con = sqlite3.connect('horta.db')
tablas = {fila[0] for fila in con.execute(\"select name from sqlite_master where type='table'\")}
assert {'usuario', 'horta', 'horta_membro', 'parcela', 'animal'} <= tablas, tablas
print('ok', sorted(tablas))
"`
Expected: imprime `ok` e a lista de táboas, incluíndo as cinco esperadas.

- [ ] **Step 7: Borrar a BD de proba local (non se garda en git) e commit**

Run: `rm -f horta.db`

```bash
git add .gitignore alembic.ini alembic/
git commit -m "feat: configurar Alembic e crear a migración inicial"
```

---

## Task 13: Esqueleto da app NiceGUI, middleware de sesión e páxina de login

**Files:**
- Create: `src/horta/ui/__init__.py`
- Create: `src/horta/ui/pages/__init__.py`
- Create: `src/horta/ui/pages/login.py`
- Create: `src/horta/main.py` (substitúe o mockup actual)
- Modify: `pyproject.toml` (punto de entrada `horta`)

**Interfaces:**
- Consumes: `horta.db.get_session` (Task 2); `horta.services.auth.autenticar` (Task 4).
- Produces:
  - Ruta `/login` rexistrada.
  - `app.storage.user["usuario_id"]`, `["usuario_nome"]`, `["usuario_rol"]` establecidos tras login correcto — as tarefas 12-15 len destes valores.
  - `horta.main.main()` — arranca o servidor NiceGUI no porto 8081.

- [ ] **Step 1: Crear os paquetes de UI**

Run: `mkdir -p src/horta/ui/pages && touch src/horta/ui/__init__.py src/horta/ui/pages/__init__.py`

- [ ] **Step 2: Implementar `src/horta/ui/pages/login.py`**

```python
from __future__ import annotations

from nicegui import app, ui

from horta.db import get_session
from horta.services.auth import autenticar


@ui.page("/login")
def login_page() -> None:
    if app.storage.user.get("usuario_id"):
        ui.navigate.to("/")
        return

    with ui.card().classes("absolute-center"):
        ui.label("Horta — Acceso").classes("text-xl font-bold")
        email_input = ui.input("Email")
        contrasinal_input = ui.input("Contrasinal", password=True)
        mensaxe_erro = ui.label("").classes("text-negative")

        def tentar_login() -> None:
            with get_session() as session:
                usuario = autenticar(session, email_input.value, contrasinal_input.value)
                if usuario is None:
                    mensaxe_erro.text = "Email ou contrasinal incorrectos"
                    return
                app.storage.user["usuario_id"] = usuario.id
                app.storage.user["usuario_nome"] = usuario.nome
                app.storage.user["usuario_rol"] = usuario.rol.value
            ui.navigate.to("/")

        ui.button("Entrar", on_click=tentar_login)
```

- [ ] **Step 3: Implementar `src/horta/main.py`**

```python
from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app, ui
from starlette.middleware.base import BaseHTTPMiddleware

RUTAS_PUBLICAS = {"/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        usuario_autenticado = app.storage.user.get("usuario_id")
        if not usuario_autenticado and request.url.path not in RUTAS_PUBLICAS:
            return RedirectResponse("/login")
        return await call_next(request)


app.add_middleware(AuthMiddleware)

import horta.ui.pages.login  # noqa: E402,F401


def main() -> None:
    ui.run(
        port=8081,
        title="Horta",
        storage_secret=os.environ.get("HORTA_STORAGE_SECRET", "dev-secret-cambiar-en-produccion"),
        reload=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
```

- [ ] **Step 4: Substituír o contido de `src/horta/__init__.py`**

O ficheiro pasa a estar baleiro (só marca o paquete):

```python
```

- [ ] **Step 5: Actualizar o punto de entrada de consola en `pyproject.toml`**

Cambiar:

```toml
[project.scripts]
horta = "horta:main"
```

por:

```toml
[project.scripts]
horta = "horta.main:main"
```

- [ ] **Step 6: Verificación manual**

Run: `uv run python src/horta/main.py` (en segundo plano ou nunha terminal aparte)

- Abrir `http://localhost:8081/` no navegador → debe redirixir automaticamente a `/login` (aínda non hai sesión).
- A páxina `/login` debe amosar o formulario "Horta — Acceso" con campos Email/Contrasinal e un botón "Entrar".
- Introducir un email calquera → debe amosar "Email ou contrasinal incorrectos" (aínda non hai usuarios na BD).

Parar o servidor despois de verificar (Ctrl+C ou matar o proceso).

- [ ] **Step 7: Commit**

```bash
git add src/horta/ui/ src/horta/main.py src/horta/__init__.py pyproject.toml
git commit -m "feat: substituír o mockup pola app real con login e middleware de sesión"
```

---

## Task 14: Páxina de dashboard (hortas do usuario + crear horta)

**Files:**
- Create: `src/horta/ui/pages/dashboard.py`
- Modify: `src/horta/main.py` (importar a páxina nova)

**Interfaces:**
- Consumes: `app.storage.user["usuario_id"]` (Task 13); `horta.services.hortas.{crear_horta, listar_hortas_usuario}` (Task 7); `horta.models.usuario.RolGlobal` (Task 3).
- Produces: ruta `/` rexistrada (dashboard).

- [ ] **Step 1: Implementar `src/horta/ui/pages/dashboard.py`**

```python
from __future__ import annotations

from nicegui import app, ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.hortas import crear_horta, listar_hortas_usuario


def _actor(session: Session) -> Usuario:
    usuario = session.get(Usuario, app.storage.user["usuario_id"])
    assert usuario is not None
    return usuario


@ui.page("/")
def dashboard_page() -> None:
    with get_session() as session:
        actor = _actor(session)
        hortas = listar_hortas_usuario(session, actor)
        nome = actor.nome
        e_admin_global = actor.rol == RolGlobal.ADMIN

    ui.label(f"Ola, {nome}").classes("text-xl font-bold")

    if e_admin_global:
        ui.link("Administración de usuarios", "/admin/usuarios")

    ui.label("As túas hortas").classes("text-lg font-bold").classes("q-mt-md")

    if not hortas:
        ui.label("Aínda non tes ningunha horta.")
    for horta, rol in hortas:
        with ui.row().classes("items-center"):
            ui.link(horta.nome, f"/hortas/{horta.id}")
            ui.label(f"({rol.value})")

    with ui.card().classes("q-mt-md"):
        ui.label("Crear nova horta").classes("text-md font-bold")
        nome_input = ui.input("Nome")
        profesional_checkbox = ui.checkbox("Uso profesional")

        def crear() -> None:
            if not nome_input.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor_actual = _actor(session)
                crear_horta(
                    session,
                    actor_actual,
                    nome_input.value,
                    uso_profesional=profesional_checkbox.value,
                )
            ui.navigate.reload()

        ui.button("Crear horta", on_click=crear)
```

- [ ] **Step 2: Rexistrar a páxina nova en `src/horta/main.py`**

Engadir despois de `import horta.ui.pages.login`:

```python
import horta.ui.pages.dashboard  # noqa: E402,F401
```

- [ ] **Step 3: Verificación manual**

Run: `uv run python src/horta/main.py`

Como aínda non hai forma de crear o primeiro usuario dende a UI (Task 18), crear un usuario admin á man para poder probar:

Run: `uv run python -c "
from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password

with get_session() as session:
    session.add(Usuario(nome='Admin', email='admin@example.com', password_hash=hash_password('admin1234'), rol=RolGlobal.ADMIN, activo=True))
    session.commit()
print('usuario admin creado')
"`

- Entrar en `/login` con `admin@example.com` / `admin1234` → debe redirixir a `/` e amosar "Ola, Admin", un enlace a "Administración de usuarios" e "Aínda non tes ningunha horta.".
- Crear unha horta co formulario → tras recargar, debe aparecer listada cun enlace e "(admin)" ao lado.

Parar o servidor despois de verificar.

- [ ] **Step 4: Commit**

```bash
git add src/horta/ui/pages/dashboard.py src/horta/main.py
git commit -m "feat: engadir páxina de dashboard con listado e creación de hortas"
```

---

## Task 15: Páxina de detalle de horta — CRUD de parcelas

**Files:**
- Create: `src/horta/ui/pages/horta_detalle.py`
- Modify: `src/horta/main.py` (importar a páxina nova)

**Interfaces:**
- Consumes: `horta.services.hortas.comprobar_rol_horta` (Task 7); `horta.services.parcelas.{crear_parcela, listar_parcelas}` (Task 9); `horta.models.horta.RolHorta` (Task 6); `horta.services.errors.PermisoDenegadoError` (Task 5).
- Produces: ruta `/hortas/{horta_id}` rexistrada, con sección de parcelas. A Task 16 engadirá a sección de animais e a Task 17 a sección de membros, ambas na mesma páxina.

- [ ] **Step 1: Implementar `src/horta/ui/pages/horta_detalle.py`**

```python
from __future__ import annotations

from nicegui import app, ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import comprobar_rol_horta
from horta.services.parcelas import crear_parcela, listar_parcelas

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def _actor(session: Session) -> Usuario:
    usuario = session.get(Usuario, app.storage.user["usuario_id"])
    assert usuario is not None
    return usuario


@ui.page("/hortas/{horta_id}")
def horta_detalle_page(horta_id: int) -> None:
    with get_session() as session:
        actor = _actor(session)
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
        except PermisoDenegadoError:
            ui.label("Non tes acceso a esta horta").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA

    ui.label("Parcelas").classes("text-xl font-bold")
    rows = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
        for p in parcelas
    ]
    ui.table(
        columns=[
            {"name": "nome", "label": "Nome", "field": "nome"},
            {"name": "superficie", "label": "Superficie", "field": "superficie"},
            {"name": "estado", "label": "Estado", "field": "estado"},
        ],
        rows=rows,
        row_key="id",
    )

    if pode_editar:
        with ui.card().classes("q-mt-md"):
            ui.label("Nova parcela").classes("text-md font-bold")
            nome_input = ui.input("Nome")
            superficie_input = ui.number("Superficie (m²)")

            def crear() -> None:
                if not nome_input.value:
                    ui.notify("O nome é obrigatorio", type="negative")
                    return
                with get_session() as session:
                    actor_actual = _actor(session)
                    crear_parcela(
                        session,
                        actor_actual,
                        horta_id,
                        nome_input.value,
                        superficie=superficie_input.value,
                    )
                ui.navigate.reload()

            ui.button("Crear parcela", on_click=crear)
```

- [ ] **Step 2: Rexistrar a páxina nova en `src/horta/main.py`**

Engadir despois de `import horta.ui.pages.dashboard`:

```python
import horta.ui.pages.horta_detalle  # noqa: E402,F401
```

- [ ] **Step 3: Verificación manual**

Run: `uv run python src/horta/main.py`

- Coa sesión do admin creado na Task 14, entrar na horta creada (clic no enlace do dashboard) → debe amosar a táboa de parcelas (baleira) e o formulario "Nova parcela" (o admin da horta pode escribir).
- Crear unha parcela → tras recargar, debe aparecer na táboa.

Parar o servidor despois de verificar.

- [ ] **Step 4: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py src/horta/main.py
git commit -m "feat: engadir páxina de detalle de horta con CRUD de parcelas"
```

---

## Task 16: Páxina de detalle de horta — CRUD de animais

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.services.animais.{crear_animal, listar_animais}` (Task 11); `horta.models.horta.RolHorta` (xa importado na Task 15).
- Produces: sección de animais na mesma páxina `/hortas/{horta_id}`, coa mesma lóxica de permisos que a sección de parcelas (Task 15). A Task 17 engadirá a sección de membros despois desta.

- [ ] **Step 1: Ampliar os imports de `src/horta/ui/pages/horta_detalle.py`**

Engadir ás importacións existentes:

```python
from datetime import date

from horta.services.animais import crear_animal, listar_animais
```

- [ ] **Step 2: Cargar tamén os animais dentro do bloque `with get_session()` inicial**

No bloque inicial da función `horta_detalle_page` (o que xa fai `comprobar_rol_horta` e `listar_parcelas`), engadir a liña `animais = listar_animais(...)` xusto despois de `parcelas = listar_parcelas(session, actor, horta_id)`, quedando así:

```python
    with get_session() as session:
        actor = _actor(session)
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
        except PermisoDenegadoError:
            ui.label("Non tes acceso a esta horta").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA
```

- [ ] **Step 3: Engadir a sección de Animais despois da sección de Parcelas**

Engadir despois do bloque `if pode_editar:` da sección de Parcelas (o que remata en `ui.button("Crear parcela", on_click=crear)`), ao mesmo nivel de indentación que `ui.label("Parcelas")`:

```python
    ui.label("Animais").classes("text-xl font-bold").classes("q-mt-lg")
    rows_animais = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
        }
        for a in animais
    ]
    ui.table(
        columns=[
            {"name": "especie", "label": "Especie", "field": "especie"},
            {"name": "raza", "label": "Raza", "field": "raza"},
            {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
            {"name": "estado", "label": "Estado", "field": "estado"},
        ],
        rows=rows_animais,
        row_key="id",
    )

    if pode_editar:
        with ui.card().classes("q-mt-md"):
            ui.label("Novo animal").classes("text-md font-bold")
            especie_input = ui.input("Especie (p.ex. galiñas, coellos)")
            raza_input = ui.input("Raza (opcional)")
            cantidade_input = ui.number("Cantidade", value=1)

            def crear_animal_novo() -> None:
                if not especie_input.value:
                    ui.notify("A especie é obrigatoria", type="negative")
                    return
                with get_session() as session:
                    actor_actual = _actor(session)
                    crear_animal(
                        session,
                        actor_actual,
                        horta_id,
                        especie_input.value,
                        date.today(),
                        raza=raza_input.value or None,
                        cantidade=int(cantidade_input.value or 1),
                    )
                ui.navigate.reload()

            ui.button("Crear animal", on_click=crear_animal_novo)
```

- [ ] **Step 4: Verificación manual**

Run: `uv run python src/horta/main.py`

- Coa sesión do admin (Task 14), entrar na horta creada → debaixo da táboa de parcelas debe aparecer "Animais" cunha táboa baleira e o formulario "Novo animal".
- Crear un animal (p.ex. especie "galiñas", raza "Rubia Galega", cantidade 6) → tras recargar, debe aparecer na táboa de animais.

Parar o servidor despois de verificar.

- [ ] **Step 5: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir CRUD de animais á páxina de detalle de horta"
```

---

## Task 17: Páxina de detalle de horta — xestión de membros

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.services.hortas.engadir_membro` (Task 7); `horta.models.horta.HortaMembro` (Task 6); `horta.models.usuario.Usuario` (Task 3).
- Produces: sección de membros visible só para `RolHorta.ADMIN` desa horta, na mesma páxina `/hortas/{horta_id}`.

- [ ] **Step 1: Ampliar os imports de `src/horta/ui/pages/horta_detalle.py`**

Engadir ás importacións existentes:

```python
from horta.models.horta import HortaMembro
from horta.services.hortas import engadir_membro
```

- [ ] **Step 2: Engadir a sección de membros ao final da función `horta_detalle_page`**

Engadir tras o bloque `if pode_editar:` da sección de Animais (engadida na Task 16, remata en `ui.button("Crear animal", on_click=crear_animal_novo)`) — é dicir, ao final da función, mesmo nivel de indentación que `ui.label("Parcelas")` / `ui.label("Animais")`:

```python
    if membro.rol == RolHorta.ADMIN:
        with ui.card().classes("q-mt-md"):
            ui.label("Membros da horta").classes("text-md font-bold")

            with get_session() as session:
                membros_bd = session.query(HortaMembro).filter_by(horta_id=horta_id).all()
                filas_membros = []
                for m in membros_bd:
                    usuario_membro = session.get(Usuario, m.usuario_id)
                    assert usuario_membro is not None
                    filas_membros.append(
                        {
                            "usuario_id": m.usuario_id,
                            "nome": usuario_membro.nome,
                            "email": usuario_membro.email,
                            "rol": m.rol.value,
                        }
                    )

            ui.table(
                columns=[
                    {"name": "nome", "label": "Nome", "field": "nome"},
                    {"name": "email", "label": "Email", "field": "email"},
                    {"name": "rol", "label": "Rol", "field": "rol"},
                ],
                rows=filas_membros,
                row_key="usuario_id",
            )

            email_novo_membro = ui.input("Email do usuario a engadir")
            rol_novo_membro = ui.select(["admin", "editor", "lector"], value="lector")

            def engadir() -> None:
                with get_session() as session:
                    actor_actual = _actor(session)
                    usuario_obxectivo = (
                        session.query(Usuario)
                        .filter_by(email=email_novo_membro.value)
                        .one_or_none()
                    )
                    if usuario_obxectivo is None:
                        ui.notify("Non existe ningún usuario con ese email", type="negative")
                        return
                    engadir_membro(
                        session,
                        actor_actual,
                        horta_id,
                        usuario_obxectivo,
                        RolHorta(rol_novo_membro.value),
                    )
                ui.navigate.reload()

            ui.button("Engadir membro", on_click=engadir)
```

- [ ] **Step 3: Verificación manual**

Run: `uv run python src/horta/main.py`

Crear un segundo usuario á man (igual que na Task 14, cambiando email/nome), entrar coa conta admin, ir á horta, e na sección "Membros da horta":

- Debe aparecer o admin como único membro inicial.
- Engadir o segundo usuario por email cun rol (p.ex. `editor`) → tras recargar, debe aparecer na táboa de membros.
- Entrar coa conta dese segundo usuario → debe ver a horta no seu dashboard co rol correcto, e na páxina de detalle **non** debe ver a sección "Membros da horta" (só é admin quen a ve).

Parar o servidor despois de verificar.

- [ ] **Step 4: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir xestión de membros á páxina de detalle de horta"
```

---

## Task 18: Panel de administración de usuarios

**Files:**
- Create: `src/horta/ui/admin/__init__.py`
- Create: `src/horta/ui/admin/usuarios.py`
- Modify: `src/horta/main.py` (importar a páxina nova)

**Interfaces:**
- Consumes: `horta.services.usuarios.{crear_usuario, listar_usuarios}` (Task 5); `horta.models.usuario.RolGlobal` (Task 3); `horta.services.errors.PermisoDenegadoError` (Task 5).
- Produces: ruta `/admin/usuarios` rexistrada.

- [ ] **Step 1: Crear o paquete `src/horta/ui/admin/`**

Run: `mkdir -p src/horta/ui/admin && touch src/horta/ui/admin/__init__.py`

- [ ] **Step 2: Implementar `src/horta/ui/admin/usuarios.py`**

```python
from __future__ import annotations

from nicegui import app, ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.usuarios import crear_usuario, listar_usuarios


def _actor(session: Session) -> Usuario:
    usuario = session.get(Usuario, app.storage.user["usuario_id"])
    assert usuario is not None
    return usuario


@ui.page("/admin/usuarios")
def admin_usuarios_page() -> None:
    with get_session() as session:
        actor = _actor(session)
        try:
            usuarios = listar_usuarios(session, actor)
        except PermisoDenegadoError:
            ui.label("Non tes acceso a esta páxina").classes("text-negative")
            return
        rows = [
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "rol": u.rol.value,
                "activo": "si" if u.activo else "non",
            }
            for u in usuarios
        ]

    ui.label("Xestión de usuarios").classes("text-xl font-bold")
    ui.table(
        columns=[
            {"name": "nome", "label": "Nome", "field": "nome"},
            {"name": "email", "label": "Email", "field": "email"},
            {"name": "rol", "label": "Rol", "field": "rol"},
            {"name": "activo", "label": "Activo", "field": "activo"},
        ],
        rows=rows,
        row_key="id",
    )

    with ui.card().classes("q-mt-md"):
        ui.label("Crear usuario").classes("text-md font-bold")
        nome_input = ui.input("Nome")
        email_input = ui.input("Email")
        contrasinal_input = ui.input("Contrasinal", password=True)
        rol_select = ui.select(["admin", "usuario"], value="usuario")

        def crear() -> None:
            if not (nome_input.value and email_input.value and contrasinal_input.value):
                ui.notify("Todos os campos son obrigatorios", type="negative")
                return
            with get_session() as session:
                actor_actual = _actor(session)
                crear_usuario(
                    session,
                    actor_actual,
                    nome_input.value,
                    email_input.value,
                    contrasinal_input.value,
                    rol=RolGlobal(rol_select.value),
                )
            ui.navigate.reload()

        ui.button("Crear usuario", on_click=crear)
```

- [ ] **Step 3: Rexistrar a páxina nova en `src/horta/main.py`**

Engadir despois de `import horta.ui.pages.horta_detalle`:

```python
import horta.ui.admin.usuarios  # noqa: E402,F401
```

- [ ] **Step 4: Verificación manual**

Run: `uv run python src/horta/main.py`

- Coa conta admin, ir a "/admin/usuarios" (enlace no dashboard) → debe amosar a táboa cos usuarios existentes (admin creado na Task 14, e o segundo usuario creado na Task 17).
- Crear un usuario novo dende o formulario → tras recargar, debe aparecer na táboa.
- Entrar coa conta do usuario non-admin creado na Task 17 e visitar `/admin/usuarios` directamente na URL → debe amosar "Non tes acceso a esta páxina" (non a táboa nin o formulario).

Parar o servidor despois de verificar.

- [ ] **Step 5: Commit**

```bash
git add src/horta/ui/admin/ src/horta/main.py
git commit -m "feat: engadir panel de administración de usuarios"
```

---

## Task 19: Verificación final de conxunto

**Files:**
- Ningún ficheiro novo — só verificación.

**Interfaces:**
- Consumes: todo o anterior.
- Produces: confirmación de que a suite completa de tests pasa, o lint/tipado están limpos, e o fluxo completo de usuario funciona de punta a punta.

- [ ] **Step 1: Executar toda a suite de tests**

Run: `uv run pytest -v`
Expected: todos os tests de Tasks 3-11 en PASS, sen erros.

- [ ] **Step 2: Executar Ruff sobre todo o código novo**

Run: `uv run ruff check src tests`
Expected: sen erros. Se aparece algún, corrixilo directamente (imports sen usar, liñas longas, etc.) e volver executar ata que quede limpo.

- [ ] **Step 3: Executar mypy sobre `src`**

Run: `uv run mypy src`
Expected: sen erros bloqueantes. Se aparecen erros de tipado lexítimos (non falsos positivos de librarías sen stubs), corrixilos.

- [ ] **Step 4: Proba manual de punta a punta nunha BD limpa**

Run: `rm -f horta.db && uv run alembic upgrade head`

Run: `uv run python -c "
from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password

with get_session() as session:
    session.add(Usuario(nome='Admin', email='admin@example.com', password_hash=hash_password('admin1234'), rol=RolGlobal.ADMIN, activo=True))
    session.commit()
print('usuario admin creado')
"`

Run: `uv run horta` (verifica que o punto de entrada de consola arranca a app real, non o stub antigo)

No navegador:
1. `/login` con `admin@example.com` / `admin1234` → entra no dashboard.
2. Crear unha horta.
3. Entrar na horta, crear unha parcela e un animal (p.ex. "galiñas", cantidade 6).
4. Ir a "/admin/usuarios", crear un segundo usuario.
5. Dende o dashboard, engadir ese segundo usuario á horta como `editor` (sección de membros na páxina de detalle).
6. Pechar sesión (borrar `app.storage.user` — pódese facer visitando unha ruta que a limpe, ou simplemente abrindo unha xanela de navegación privada) e entrar coa conta do segundo usuario: debe ver a horta compartida e poder crear parcelas e animais, pero non ver "Administración de usuarios" nin a sección de membros.

Parar o servidor despois de verificar.

- [ ] **Step 5: Commit final (se houbo correccións nos pasos 2-3)**

```bash
git add -A
git commit -m "chore: corrixir avisos de lint/tipado tras a verificación final"
```

(Omitir este commit se non houbo cambios que facer.)

# Tarefa 028 — Email sen distinguir maiúsculas nin espazos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 027 (migración `d4b8e2a6c1f3`).

## Obxectivo

O usuario non podía entrar: o login comparaba o email tal cal, e o móbil pon a primeira letra en maiúscula ou deixa un espazo ao final. Agora o email gárdase e compárase sempre en minúsculas e sen espazos (login, crear usuario e engadir membro). Unha migración normaliza os emails xa gardados.

## Ficheiros a tocar

- `src/horta/services/auth.py`
- `src/horta/services/usuarios.py`
- `src/horta/ui/pages/horta_detalle.py`
- `alembic/versions/e5c9f3b7d2a4_emails_en_minusculas.py` (**ficheiro novo**)
- `tests/services/test_auth.py`
- `tests/services/test_usuarios.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/auth.py`: función nova e usala no login

Antes:
```python
def autenticar(session: Session, email: str, password: str) -> Usuario | None:
    usuario = session.query(Usuario).filter_by(email=email).one_or_none()
```

Despois:
```python
def normalizar_email(email: str) -> str:
    """Os emails gárdanse e compáranse en minúsculas e sen espazos."""
    return email.strip().lower()


def autenticar(session: Session, email: str, password: str) -> Usuario | None:
    email = normalizar_email(email)
    usuario = session.query(Usuario).filter_by(email=email).one_or_none()
```

### Paso 2 — `src/horta/services/usuarios.py`: importar

Antes:
```python
from horta.services.auth import hash_password
```

Despois:
```python
from horta.services.auth import hash_password, normalizar_email
```

### Paso 3 — mesmo ficheiro: gardar o email normalizado

Antes:
```python
        nome=nome,
        email=email,
        password_hash=hash_password(password),
```

Despois:
```python
        nome=nome,
        email=normalizar_email(email),
        password_hash=hash_password(password),
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`: importar

Antes:
```python
from horta.services.cultivos import (
```

Despois:
```python
from horta.services.auth import normalizar_email
from horta.services.cultivos import (
```

### Paso 5 — mesmo ficheiro: buscar o membro polo email normalizado

Antes:
```python
                    session.query(Usuario).filter_by(email=email_input.value).one_or_none()
```

Despois:
```python
                    session.query(Usuario)
                    .filter_by(email=normalizar_email(email_input.value or ""))
                    .one_or_none()
```

### Paso 6 — crear o ficheiro `alembic/versions/e5c9f3b7d2a4_emails_en_minusculas.py`

Contido completo:

```python
"""emails en minusculas

Revision ID: e5c9f3b7d2a4
Revises: d4b8e2a6c1f3
Create Date: 2026-10-23 11:00:00

O login compara o email en minúsculas e sen espazos; normalízanse os xa gardados.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "e5c9f3b7d2a4"
down_revision: Union[str, Sequence[str], None] = "d4b8e2a6c1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE usuario SET email = lower(trim(email))")


def downgrade() -> None:
    pass
```

### Paso 7 — `tests/services/test_auth.py`: engadir ao final do ficheiro

```python
def test_autenticar_ignora_maiusculas_e_espazos(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    assert autenticar(session, "  Ana@Example.COM ", "segredo") is not None
```

### Paso 8 — `tests/services/test_usuarios.py`: engadir ao final do ficheiro

```python
def test_crear_usuario_garda_email_en_minusculas(session):
    admin = _crear_admin(session)
    usuario = crear_usuario(session, admin, "Ana", "  Ana@Example.COM ", "segredo")
    assert usuario.email == "ana@example.com"
```

## Criterios de aceptación

- `autenticar(session, "  Ana@Example.COM ", ...)` atopa a `ana@example.com`.
- Os 2 tests novos pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

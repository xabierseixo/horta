# Deseño: Usuarios, Hortas, Parcelas e Animais (primeira iteración)

## Obxectivo

Implementar a base da aplicación Horta: autenticación de usuarios, xestión de hortas (con varios membros por horta), xestión de parcelas e xestión de animais dentro de cada horta, con persistencia real en SQLite. É o primeiro tramo do alcance descrito en README §23 ("Primeira versión"), ampliado para incluír tamén Animais (README §7, entidade irmá de Parcelas) — cultivos, tarefas e dashboard quedan para iteracións posteriores.

Esta iteración tamén senta as bases do "caderno de explotación" (README §22): a Horta leva un flag `uso_profesional` e a Parcela leva os campos regulados (SIGPAC, uso/aproveitamento) que a normativa esixe cando aplica, aínda que a funcionalidade completa de rexistro (tratamentos, fertilización) non se implementa aínda.

## Alcance

**Inclúe:**
- Autenticación por sesión (login/logout), sen autorrexistro público.
- Xestión de usuarios (CRUD) nun panel de administración, restrinxido ao rol global `admin`.
- Xestión de hortas: crear horta, listar as hortas propias, xestionar membros por horta con rol (`admin`/`editor`/`lector`).
- Xestión de parcelas dentro dunha horta: CRUD completo, respectando os roles por horta.
- Xestión de animais dentro dunha horta (galiñas, coellos, etc., por lote): CRUD completo, coa mesma lóxica de roles por horta que as parcelas.
- Persistencia en SQLite vía SQLAlchemy, con migracións Alembic.
- Configuración inicial de pytest, Ruff e mypy (ferramentas previstas no README, aínda non configuradas).

**Non inclúe (fases posteriores, xa documentadas no README):** cultivos, tarefas, dashboard, calendario, colleitas, plano gráfico da horta, xestión económica (gastos/ingresos), sensores IoT (xeolocalización, cámara, sensores físicos), meteoroloxía, fotografías asociadas a animais/parcelas, e a funcionalidade completa do caderno de explotación (rexistro de tratamentos/fertilización/gandaría).

## Arquitectura

Segue a capa Interface → Lóxica → Modelos/servizos → Base de datos que esixe o README (§19), organizada en capas por tipo, cada unha dividida por entidade para manter os ficheiros pequenos e cun propósito claro:

```
src/horta/
  db.py                        # engine, sesión, Base declarativa
  models/
    __init__.py
    usuario.py                 # Usuario
    horta.py                   # Horta, HortaMembro
    parcela.py                 # Parcela
    animal.py                  # Animal
  services/
    __init__.py
    auth.py                    # hash/verificación de contrasinal, autenticación
    usuarios.py                # CRUD de usuarios (panel admin)
    hortas.py                  # crear horta, xestión de membros
    parcelas.py                # CRUD de parcelas, comprobación de permisos
    animais.py                 # CRUD de animais, comprobación de permisos
  ui/
    __init__.py
    pages/
      login.py
      dashboard.py
      horta_detalle.py
    admin/
      usuarios.py
  main.py                      # monta a app NiceGUI, rutas e middleware de sesión
alembic/                       # migracións, na raíz do repo
alembic.ini
```

`main.py` pasa a ser o punto de entrada real da aplicación (substitúe o mockup actual); o script de consola `horta` (`pyproject.toml`) pasa a chamar a esta nova app en lugar do stub actual en `__init__.py`.

A capa de servizos non depende de NiceGUI; a capa de UI non contén lóxica de negocio nin consultas SQL directas — só chama a servizos.

## Modelo de datos

```
Usuario
  id: int (PK)
  nome: str
  email: str (único)
  password_hash: str
  rol: enum(admin, usuario)       # rol global — só controla acceso ao panel de administración
  activo: bool
  created_at: datetime

Horta
  id: int (PK)
  nome: str
  descricion: str | None
  uso_profesional: bool           # autoconsumo (False) vs. actividade comercial (True)
  created_at: datetime

HortaMembro                       # táboa de asociación Usuario <-> Horta
  horta_id: int (FK -> Horta)
  usuario_id: int (FK -> Usuario)
  rol: enum(admin, editor, lector)  # rol dentro desta horta en concreto
  # PK composta (horta_id, usuario_id)

Parcela
  id: int (PK)
  horta_id: int (FK -> Horta)
  nome: str
  descricion: str | None
  superficie: float | None
  posicion: str | None            # campo simple; preparación para futuro plano gráfico
  uso_aproveitamento: str | None  # cultivo/uso da parcela; relevante para caderno de explotación
  secano_regadio: enum(secano, regadio) | None
  sigpac_provincia: str | None
  sigpac_concello: str | None
  sigpac_poligono: str | None
  sigpac_parcela: str | None
  sigpac_subparcela: str | None
  notas: str | None
  estado: str
  created_at: datetime

Animal                            # lote de animais (galiñas, coellos...), non individuos
  id: int (PK)
  horta_id: int (FK -> Horta)
  especie: str                    # "galiñas", "coellos", etc.
  raza: str | None
  cantidade: int
  data_alta: date
  data_baixa: date | None
  estado: str
  notas: str | None
  created_at: datetime
```

Notas:
- Os campos SIGPAC e `uso_aproveitamento`/`secano_regadio` son sempre opcionais a nivel de base de datos; só se mostran/solicitan na UI cando `Horta.uso_profesional` é `True`.
- Non se aplica borrado lóxico nesta iteración: a obriga de conservación de 3 anos (README §22) só afecta aos rexistros regulados (tratamentos, fertilización) que aínda non existen. Parcela/Horta/Usuario/Animal usan borrado físico normal por agora.
- Animal representa un lote (por especie/raza), non un animal individual — coincide co modelo xa descrito en README §7. Un perfil por animal individual queda como idea para unha fase posterior, non desta iteración.

## Autenticación e permisos

- **Autenticación**: sesión de NiceGUI (`app.storage.user`) máis un middleware que redirixe a `/login` calquera ruta non autenticada, seguindo o patrón oficial de autenticación de NiceGUI. Contrasinais con hash mediante `bcrypt`.
- **Creación de usuarios**: só dende o panel `/admin/usuarios`, restrinxido a `Usuario.rol == admin`. Non hai autorrexistro público.
- **Rol global** (`Usuario.rol`): `admin` accede ao panel de xestión de usuarios; `usuario` non.
- **Rol por horta** (`HortaMembro.rol`): independente do rol global.
  - `lector`: só pode ver a horta, as súas parcelas e os seus animais.
  - `editor`: ademais, pode crear/editar/eliminar parcelas e animais.
  - `admin` (da horta): ademais, pode xestionar os membros da horta (engadir/quitar usuarios, cambiar roles).
- Quen crea unha horta pasa a ser automaticamente `admin` desa horta.
- As comprobacións de permiso viven na capa de servizos (non na UI): cada función de `services/hortas.py`, `services/parcelas.py` e `services/animais.py` recibe o usuario que realiza a acción e lanza unha excepción de dominio (`PermisoDenegadoError`) se non ten permiso. A UI captura esas excepcións e mostra `ui.notify` en negativo.

## Páxinas UI

- `/login`: formulario de email + contrasinal.
- `/` (dashboard, requira sesión): lista das hortas nas que o usuario é membro, cos seus roles; formulario/botón para crear unha horta nova; se `Usuario.rol == admin`, enlace ao panel de administración.
- `/hortas/{id}`: detalle da horta — táboa de parcelas con CRUD (segundo o rol na horta); táboa de animais con CRUD (mesma lóxica de rol); sección de membros (visible/editable só se o usuario é `admin` desa horta).
- `/admin/usuarios` (só rol global `admin`): listado de usuarios con estado (activo/inactivo) e rol global; crear usuario, editar datos/rol, activar/desactivar.

## Probas

Configúrase pytest (aínda non existe no proxecto). Probas unitarias sobre a capa de servizos, usando SQLite en memoria (unha sesión de BD nova por test):

- `auth`: hash e verificación de contrasinal; autenticación con credenciais correctas/incorrectas/usuario inactivo.
- `usuarios`: crear/editar/desactivar usuario; só un admin global pode facelo.
- `hortas`: crear horta (o creador queda como admin da horta); engadir/quitar membros e cambiar roles (só admin da horta); listar hortas dun usuario.
- `parcelas`: CRUD respectando os tres roles por horta (lector non pode escribir, editor e admin si); validación de que os campos SIGPAC son opcionais.
- `animais`: CRUD respectando os tres roles por horta, mesma lóxica que parcelas.

Configúrase tamén Ruff e mypy básicos (configuración por defecto razoable), sen bloquear esta iteración en regras estritas.

## Migracións

Alembic inicializado na raíz do proxecto (`alembic/`, `alembic.ini`), cunha primeira revisión que crea as cinco táboas (`usuario`, `horta`, `horta_membro`, `parcela`, `animal`).

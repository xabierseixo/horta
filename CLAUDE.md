# CLAUDE.md

Este ficheiro dá indicacións a Claude Code (claude.ai/code) para traballar co código deste repositorio.

## Proxecto

Horta é unha aplicación web para a xestión integral dunha ou varias hortas: parcelas, cultivos, tarefas, sementeiras, plantacións, colleitas e histórico por parcela. Pretende ser unha base de coñecemento estruturada do que se fixo, onde, cando e con que resultados — non un simple calendario agrícola. Os textos da UI e o vocabulario do dominio están en galego.

Modelo conceptual central:

```
Usuario
   └── Horta
          ├── Parcelas → Cultivos
          ├── Animais (galiñas, coellos, ...)
          ├── Tarefas
          ├── Sementeiras, Plantacións, Colleitas
          └── Histórico
```

Un usuario pode ter varias hortas e unha horta pódese compartir entre varios usuarios, cada un cun rol **na horta** (`admin`/`editor`/`lector`, táboa `HortaMembro`). Isto é independente do rol **global** do usuario (`admin`/`usuario`), que só dá acceso ao panel de administración de usuarios.

Unha horta ten un flag booleano **uso profesional** (autoconsumo vs. actividade comercial). Determina se se activan os campos/comportamentos de cumprimento normativo — ver "Cumprimento normativo" máis abaixo.

Estado actual: completo o alcance da "Primeira versión" (README §23) — autenticación, xestión de usuarios (panel de admin), hortas con membros e roles, CRUD de parcelas/animais/cultivos/tratamentos/fertilización/tarefas dentro de cada horta, un dashboard básico por horta (`/hortas/{id}`, pestana "Dashboard"), busca/filtro/paxinación nas táboas, e persistencia real en SQLite. Tratamentos e Fertilización usan baixa lóxica (nunca se borran fisicamente por unha acción individual — conservación legal de 3 anos, ver "Cumprimento normativo"); o resto de entidades bórranse fisicamente en cascada. Seguintes iteracións acordadas: Exportación (CSV/JSON/Excel), Historial/actividade, e Deseño visual — ver memoria do proxecto para o detalle da secuencia.

## Coordinación e estado do proxecto

- Neste repositorio traballa tamén un modelo local (ornith-88 e qwen-66, vía Cline). Protocolo común: `AGENTS.md`. Ao comezar unha sesión, usar a skill `/sincronizar` para revisar o que fixo o outro axente.
- O estado do proxecto, as decisións e o plan de evolución da app unificada (plan de empresa AGADER, fitosanitarios, fontes oficiais, trazabilidade) están en `docs/estado-e-evolucion.md`.
- Commits de Claude co rodapé `Axente: claude`. Ao rematar unha tarefa, actualizar `memory-bank/activeContext.md`.

## Comandos

As dependencias xestiónanse con `uv` (ver `uv.lock`, `pyproject.toml`; `.python-version` fixa Python 3.11).

- Instalar/sincronizar dependencias (incluídas as de desenvolvemento): `uv sync`
- Crear/actualizar o esquema da BD: `uv run alembic upgrade head` (crea `horta.db` na raíz, ignorado por git).
- Executar a app (NiceGUI no porto 8081): `uv run horta` (ou `uv run python src/horta/main.py`). Abrir http://localhost:8081 — sen sesión redirixe a `/login`.
- Tests: `uv run pytest` (un só ficheiro: `uv run pytest tests/services/test_hortas.py`; un só test: `-k nome_do_test`).
- Lint: `uv run ruff check src tests` · Tipado: `uv run mypy src`.
- Catálogos oficiais do FEGA: descargalos no navegador (ver `docs/referencia/siex/descarga-catalogos.md`) e `uv run horta-catalogos importar <directorio>`; despois `uv run horta-catalogos nomes-galegos`. Sen catálogos, o formulario de tratamentos avisa e non deixa rexistrar.
- Rexistro de fitosanitarios do MAPA (para buscar produtos e comprobar usos nos tratamentos): `uv run horta-catalogos fitosanitarios <directorio>`, co `ProductosAutorizados.json` e o `Cultivos.json` de regfiweb (o snapshot semanal de `../fitosanitarios/datos/snapshots/<data>/json` vale). Importar despois dos catálogos do FEGA: calcula as pontes cos cultivos (EPPO) e pragas (nome científico) do SIEX. Os avisos só informan; nunca bloquean.
- Nova migración tras cambiar un modelo: `uv run alembic revision --autogenerate -m "descricion"`, revisar o ficheiro xerado en `alembic/versions/` e aplicar con `uv run alembic upgrade head`.

Variables de contorno:
- `HORTA_DATABASE_URL` (por defecto `sqlite:///horta.db`) — úsana tanto a app coma Alembic (`alembic/env.py` le `horta.db.DATABASE_URL`, non o `sqlalchemy.url` de `alembic.ini`).
- `HORTA_STORAGE_SECRET` — segredo para asinar a cookie de sesión de NiceGUI. O valor por defecto só vale para desenvolvemento.

### Crear o primeiro usuario administrador

Aínda non hai xeito de crear o primeiro admin dende a app (o panel `/admin/usuarios` require xa un admin). Tras `uv run alembic upgrade head`, crealo así (cambiar email e contrasinal):

```bash
uv run python -c "
from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
with get_session() as session:
    session.add(Usuario(nome='Admin', email='admin@example.com', password_hash=hash_password('cambiar-isto'), rol=RolGlobal.ADMIN, activo=True))
    session.commit()
"
```

Despois, ese admin crea o resto de usuarios dende `/admin/usuarios`.

## Arquitectura

Capas (segundo o README), coa UI separada da lóxica de negocio:

```
src/horta/
  main.py            # punto de entrada: AuthMiddleware, importa as páxinas, ui.run()
  db.py              # engine, SessionLocal, Base (DeclarativeBase), get_session()
  models/            # modelos SQLAlchemy 2.0 (Mapped/mapped_column): usuario, horta (+HortaMembro), parcela, animal, cultivo (+Fertilizacion), tarefa, catalogo (catálogos SIEX versionados + capa galega), persoa (aplicadores/asesores ROPO), maquina (ROMA/REGANIP), tratamento_fito (tratamento CUE con fillos)
  services/          # lóxica de negocio e permisos: auth, usuarios, hortas, parcelas, animais, cultivos, tratamentos_fito (CUE), persoas, maquinaria, catalogos (consultas), catalogos_importar, fertilizacions, tarefas, errors
  cli_catalogos.py   # comando `horta-catalogos` (importar XLSX do FEGA, nomes galegos)
  data/              # nomes_galegos.csv (capa galega dos cultivos)
  ui/
    sesion.py        # usuario_actual(), pechar_sesion(), boton_pechar_sesion()
    accions.py       # executar_accion(): captura erros esperables e fai ui.notify
    filtros.py       # filtrar_filas(): busca de texto + filtros estruturados para as táboas
    pages/           # login, dashboard (/, lista de hortas), horta_detalle (/hortas/{id}, con pestana "Dashboard" propia por horta)
    admin/           # usuarios (/admin/usuarios)
alembic/             # migracións (unha por entidade engadida despois da revisión inicial)
tests/               # pytest: models/, services/, ui/ — fixture `session` en conftest.py (SQLite en memoria)
```

Convencións e padróns a respectar ao estender a app:
- **Os servizos son a fronteira de seguridade.** Cada función de servizo recibe `session` e o `actor` (o `Usuario` que executa a acción) e comproba os permisos ela mesma: `comprobar_rol_horta(session, horta_id, actor, roles)` para datos dunha horta (volve comprobar `HortaMembro` en cada chamada), ou `_esixir_admin(actor)` para a xestión de usuarios. A UI nunca debe ser a única barreira.
- Erros de dominio en `services/errors.py`: `PermisoDenegadoError` (falta de permiso) e `OperacionNonPermitidaError` (subclase de `ValueError`; a operación deixaría os datos nun estado inválido, p.ex. unha horta sen ningún admin, o último admin global degradado/desactivado, ou un admin desactivándose a si mesmo).
- `actualizar_parcela`/`actualizar_animal` só aceptan os campos das listas `CAMPOS_EDITABLES_PARCELA`/`CAMPOS_EDITABLES_ANIMAL` (nunca `id`, `horta_id` nin `created_at`); calquera outro levanta `ValueError`.
- **Sesión**: o login garda `usuario_id` en `app.storage.user`. `AuthMiddleware` (en `main.py`) só comproba que exista ese id e redirixe a `/login` as rutas de páxina rexistradas. Cada páxina e cada manexador obtén o usuario con `usuario_actual(session)` (de `ui/sesion.py`), que volve comprobar na BD que o usuario existe e segue `activo`; se devolve `None`, chamar a `pechar_sesion()` e saír. Así desactivar un usuario revoga tamén as sesións que xa tiña abertas.
- **Manexadores da UI**: abrir unha sesión nova con `with get_session() as session:` en cada manexador (non reutilizar a da construción da páxina) e envolver a chamada ao servizo que modifica datos en `executar_accion(session, lambda: ...)`, que fai rollback e mostra un `ui.notify(..., type="negative")` ante `PermisoDenegadoError`, `OperacionNonPermitidaError` ou `IntegrityError` (duplicados). Se devolve `True`, `ui.navigate.reload()`.
- Táboas editables: `ui.table(..., selection="single")` + `on_select` que mostra un formulario/fila de accións para a fila seleccionada (ver `admin/usuarios.py` e a sección de membros de `horta_detalle.py`).
- `SessionLocal` usa `expire_on_commit=False`, polo que os obxectos seguen lexibles tras pechar a sesión (a páxina constrúese despois de saír do `with get_session()`).
- Identificadores, mensaxes e textos da UI en galego.
- Tests: un ficheiro por servizo/modelo; crear os usuarios de proba directamente co modelo `Usuario` (ver helpers `_crear_usuario` nos tests existentes). Engadir tests de servizo para toda regra nova de permisos ou validación.

Principios de deseño do README a aplicar ao estender esta app:
- Data-centric: a información estruturada da horta é a fonte de verdade; calquera funcionalidade futura (incluído un eventual asistente de IA, ver README §18) constrúese enriba dela, non ao revés.
- Complexidade mínima necesaria: evitar dependencias innecesarias, datos duplicados ou lóxica de negocio mesturada co código de UI. **Preferir sempre os compoñentes nativos de NiceGUI antes ca librarías externas** — ver "Decisións tecnolóxicas" máis abaixo.
- Autenticación: non implementar a man a xestión de contrasinais — os hashes fanse con `bcrypt` (`services/auth.py`); para calquera ampliación (recuperación de contrasinal, OAuth...) usar unha solución madura axeitada ao stack FastAPI/NiceGUI.
- O alcance da primeira versión (README §23) é deliberadamente estreito: usuarios/autenticación, crear horta, parcelas, cultivos, tarefas, un dashboard básico, persistencia en SQLite, CRUD completo, tests básicos. Calendario, plano da horta, colleitas, produción animal (galiñas, coellos...), o cumprimento normativo completo (ver abaixo), xestión económica, fotografías, meteoroloxía, sensores IoT, rotación, estatísticas, API REST e o asistente de IA son explicitamente fases posteriores — non adiantar traballo desta secuencia sen que se pida.

## Decisións tecnolóxicas para fases futuras

Segundo README §2/§5/§12/§13/§14: cando se implementen estas fases, usar os compoñentes nativos de NiceGUI en lugar de engadir librarías JS externas:
- `ui.leaflet` para o plano da horta (§5) — parcelas coma polígonos editables, animais/instalacións coma marcadores.
- `ui.echart` para gráficas (produción, gastos/ingresos, §12).
- `ui.date` / `ui.timeline` para vistas de calendario/liña de tempo (§9).
- Meteoroloxía (§13): **MeteoGalicia** (estacións galegas, sen clave) e **AEMET OpenData** (previsión e avisos; clave gratuíta que pide o titular). Decisión do usuario do 2026-10-28; substitúe Open-Meteo.
- **WeasyPrint** (HTML→PDF) e **openpyxl** (Excel) son as únicas dependencias novas previstas, para exportar o caderno de explotación (§22) — non hai equivalente nativo en NiceGUI para xerar documentos.
- Sensores IoT (§14): xeolocalización do navegador (`ui.run_javascript` + Geolocation API) e captura de foto dende a cámara son só código, sen hardware novo — baixo custo, engadir cando toque §5/§6/§7/§15. Sensores físicos (humidade/temperatura do solo vía ESP32/Raspberry Pi + MQTT) requiren hardware adicional e unha dependencia nova (cliente MQTT): son opcionais, non un requisito do produto — non asumir que se van implementar sen que se pida explicitamente.

## Cumprimento normativo ("caderno de explotación")

A app pretende servir tamén coma caderno de explotación (cuaderno de campo) legalmente válido para pequenas explotacións profesionais, non só coma ferramenta hobby — ver README §22 para toda a investigación legal (Regulamento UE 1107/2009, RD 1311/2012 Anexo III español, REAGA/XEAGA galego). Puntos clave que afectan ao modelo de datos:
- A obriga legal só aplica cando unha horta está marcada como **uso profesional** (actividade comercial e/ou uso profesional de fitosanitarios e/ou gandaría non exenta) — unha horta de autoconsumo non ten obriga legal de rexistro.
- Parcela xa leva os campos de referencia SIGPAC e uso/aproveitamento (README §5) esixidos polo RD 1311/2012 Anexo III, opcionais e só relevantes cando a horta pai é de uso profesional.
- Cando se implementen Cultivos/tratamentos/fertilización, modelar cada tratamento fitosanitario e cada aplicación de fertilización coma o seu propio rexistro cos campos literais do Anexo III (data, praga, produto + número de rexistro, dose, eficacia, aplicador, etc.) en lugar dun log de texto libre xenérico — isto é o que fai que a funcionalidade sirva tamén coma rexistro de cumprimento normativo.
- Os rexistros regulados deben soportar unha conservación mínima de 3 anos: non facer borrado físico, usar baixa lóxica.
- **Caderno Dixital (CUE) e SIEX — decisión do 2026-10-22**: dende o 1/1/2027 o rexistro de tratamentos das explotacións profesionais é o Caderno Dixital de Explotación Agrícola integrado no SIEX (RD 1311/2012 art. 16.1, modificado polo RD 1039/2025; ata o 31/12/2026 vale o papel). **Obxectivo a longo prazo: que horta sexa unha aplicación CUE comercial autorizada** (conectada ao SIEX). **Mentres tanto**: exportación de PDF/Excel do caderno (por horta e por ano) seguindo os modelos oficiais **e** exportación nun formato que se poida cargar na ferramenta pública do CUE. Deseñar o modelo de datos de tratamentos e fertilización co Anexo V do SIEX (catálogos e códigos) en mente para non ter que refacelo. Ver `docs/estado-e-evolucion.md` §2.2.
- Nota de deseño (inspirada en farmOS) — **resolta**: en vez dun único rexistro xenérico de "evento", cada fase implementou a súa propia entidade (Cultivo, Tratamento, Fertilización, Tarefa), seguindo o criterio de complexidade mínima. Para Tarefas en concreto, marcar unha tarefa coma `feito` (con `data_feita`) xa fai de rexistro histórico — non hai unha táboa Histórico separada nin duplicación de datos (README §10 cúmprese consultando tarefas feitas por parcela/cultivo, ordenadas por `data_feita`).

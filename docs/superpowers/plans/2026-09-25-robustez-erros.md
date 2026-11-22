# Robustez: páxinas de erro e rexistro — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituír os erros técnicos en bruto (404/500) por páxinas propias en galego, rexistrar eses erros con loguru, e facer que `executar_accion` e as páxinas capturen o inesperado en vez de petar.

**Architecture:** Dous niveis de captura — manexadores de excepción de FastAPI/NiceGUI para erros durante a carga dunha páxina (404/500), e unha captura xenérica final en `executar_accion` para erros durante un clic xa en marcha. Ambos rexistran con loguru.

**Tech Stack:** Python 3.11, NiceGUI/FastAPI/Starlette, loguru (xa dependencia, aínda sen usar), pytest.

**Spec:** `docs/superpowers/specs/2026-09-25-robustez-erros-design.md`

## Global Constraints

- Identificadores, mensaxes e textos da UI en galego.
- Os servizos son a fronteira de seguridade; este plan non toca lóxica de permisos, só xestión de erros.
- `diagnose=False` no rexistro de loguru — nunca incluír valores de variables locais no log (poderían filtrar contrasinais/hashes).
- Non introducir dependencias novas — loguru xa está en `pyproject.toml`.

## Review Focus

- Visitar unha ruta que non existe (erro de escritura na URL) → páxina propia "Páxina non atopada" (404), non a resposta por defecto de Starlette. [Task 3]
- Unha excepción sen capturar durante a carga dunha páxina (un bug futuro, coma o `AssertionError` xa visto) → páxina propia "Ocorreu un erro" (500) e rexistro completo en `logs/horta.log`, non un traceback en bruto no navegador. [Task 3]
- Unha excepción inesperada (non `PermisoDenegadoError`/`OperacionNonPermitidaError`/`IntegrityError`) dentro dun manexador de clic xa executando → `executar_accion` faille rollback, notifícao xenericamente, e devolve `False` en vez de deixalo propagar. [Task 4]
- Un `HortaMembro` cuxo `Usuario` xa non se resolve (dato inconsistente) → a fila omítese na táboa de Membros, non petan toda a páxina de detalle da horta. [Task 5]
- Unha horta eliminada entre a comprobación de permiso e a lectura do seu rexistro en `horta_detalle_page` (concorrencia) → mensaxe "Esta horta xa non existe", non un `AssertionError`. [Task 5]

---

## Task 1: Configuración de loguru

**Files:**
- Create: `src/horta/log.py`
- Modify: `.gitignore`
- Test: `tests/test_log.py`

**Interfaces:**
- Produces: `horta.log.configurar_rexistro() -> None` — idempotente (chamalo varias veces non duplica handlers nin falla); crea o directorio `logs/` se non existe.

- [ ] **Step 1: Escribir o test que falla**

Crear `tests/test_log.py`:

```python
from pathlib import Path

from horta.log import configurar_rexistro


def test_configurar_rexistro_crea_directorio_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    configurar_rexistro()

    assert (tmp_path / "logs").is_dir()


def test_configurar_rexistro_e_idempotente(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    configurar_rexistro()
    configurar_rexistro()  # non debe fallar nin duplicar

    # Non hai xeito directo de contar handlers de loguru dende fóra sen
    # tocar API interna, así que a proba real é que a segunda chamada
    # non levanta excepción e o directorio segue existindo.
    assert (tmp_path / "logs").is_dir()
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/test_log.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.log'`)

- [ ] **Step 3: Implementar `src/horta/log.py`**

```python
from __future__ import annotations

from pathlib import Path

from loguru import logger

_xa_configurado = False


def configurar_rexistro() -> None:
    """Configura loguru para escribir en logs/horta.log. Idempotente."""
    global _xa_configurado
    if _xa_configurado:
        return
    Path("logs").mkdir(exist_ok=True)
    logger.add(
        "logs/horta.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        backtrace=True,
        diagnose=False,
    )
    _xa_configurado = True
```

- [ ] **Step 4: Engadir `logs/` ao `.gitignore`**

Engadir ao final do `.gitignore` existente:

```
# Rexistros da app
logs/
```

- [ ] **Step 5: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/test_log.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add src/horta/log.py tests/test_log.py .gitignore
git commit -m "feat: configurar loguru para rexistro de erros"
```

---

## Task 2: Páxina HTML de erro

**Files:**
- Create: `src/horta/ui/erros.py`
- Test: `tests/ui/test_erros.py`

**Interfaces:**
- Consumes: `horta.ui.nav.{COR_PRIMARIA, COR_TEXTO, COR_NEGATIVA, COR_FONDO}` (xa existen).
- Produces: `horta.ui.erros.pagina_erro_html(titulo: str, mensaxe: str, codigo: int) -> fastapi.responses.HTMLResponse`. Task 3 chama a esta función dende os manexadores de excepción.

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/ui/test_erros.py`:

```python
from horta.ui.erros import pagina_erro_html


def test_pagina_erro_html_inclue_titulo_e_mensaxe():
    resposta = pagina_erro_html("Páxina non atopada", "A ruta non existe.", 404)

    corpo = resposta.body.decode("utf-8")
    assert "Páxina non atopada" in corpo
    assert "A ruta non existe." in corpo
    assert resposta.status_code == 404


def test_pagina_erro_html_devolve_o_codigo_indicado():
    resposta = pagina_erro_html("Ocorreu un erro", "Algo saíu mal.", 500)

    assert resposta.status_code == 500


def test_pagina_erro_html_inclue_enlace_a_inicio():
    resposta = pagina_erro_html("Ocorreu un erro", "Algo saíu mal.", 500)

    corpo = resposta.body.decode("utf-8")
    assert 'href="/"' in corpo
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/ui/test_erros.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.ui.erros'`)

- [ ] **Step 3: Implementar `src/horta/ui/erros.py`**

```python
from __future__ import annotations

from fastapi.responses import HTMLResponse

from horta.ui.nav import COR_FONDO, COR_NEGATIVA, COR_PRIMARIA, COR_TEXTO


def pagina_erro_html(titulo: str, mensaxe: str, codigo: int) -> HTMLResponse:
    """Páxina de erro autocontida (sen NiceGUI), coa paleta da app.

    Úsase dende manexadores de excepción de FastAPI, que corren fóra do
    ciclo normal dunha páxina NiceGUI — por iso é HTML simple en vez de
    construírse con ui.*.
    """
    cor_titulo = COR_NEGATIVA if codigo >= 500 else COR_PRIMARIA
    html = f"""<!DOCTYPE html>
<html lang="gl">
<head>
    <meta charset="utf-8">
    <title>{titulo} — Horta</title>
    <style>
        body {{
            background: {COR_FONDO};
            color: {COR_TEXTO};
            font-family: sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }}
        .caixa {{ text-align: center; max-width: 420px; padding: 1rem; }}
        h1 {{ color: {cor_titulo}; }}
        a {{ color: {COR_PRIMARIA}; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="caixa">
        <h1>{titulo}</h1>
        <p>{mensaxe}</p>
        <a href="/">← Volver ao inicio</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=codigo)
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/ui/test_erros.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/horta/ui/erros.py tests/ui/test_erros.py
git commit -m "feat: engadir páxina HTML de erro coa paleta da app"
```

---

## Task 3: Manexadores de erro 404/500 en main.py

**Files:**
- Modify: `src/horta/main.py`
- Test: `tests/test_main_erros.py`

**Interfaces:**
- Consumes: `horta.log.configurar_rexistro` (Task 1); `horta.ui.erros.pagina_erro_html` (Task 2).
- Produces: rutas HTTP con manexadores de erro rexistrados en `app` (a instancia de NiceGUI/FastAPI). Non produce funcións novas reutilizables por outras tarefas — é o punto final desta funcionalidade.

- [ ] **Step 1: Escribir os tests que fallan**

Estes manexadores son funcións `async def` que reciben `(request, exc)`. Próbanse chamándoas directamente (sen levantar un servidor real), cun obxecto `Request` mínimo — só se le `request.url.path`, así que abonda un dobre simple.

Crear `tests/test_main_erros.py`:

```python
import anyio

from horta import main


class _RequestFalso:
    class _URLFalsa:
        path = "/isto-non-existe"

    url = _URLFalsa()


def test_manexador_404_devolve_pagina_propia():
    resposta = anyio.run(main.manexador_404, _RequestFalso(), Exception("non atopado"))

    corpo = resposta.body.decode("utf-8")
    assert resposta.status_code == 404
    assert "Páxina non atopada" in corpo


def test_manexador_500_devolve_pagina_propia_e_rexistra(caplog):
    resposta = anyio.run(main.manexador_500, _RequestFalso(), ValueError("boom"))

    corpo = resposta.body.decode("utf-8")
    assert resposta.status_code == 500
    assert "Ocorreu un erro" in corpo
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/test_main_erros.py -v`
Expected: FAIL (`AttributeError: module 'horta.main' has no attribute 'manexador_404'`)

- [ ] **Step 3: Implementar en `src/horta/main.py`**

Engadir os imports necesarios ao bloque de imports existente (despois de `from starlette.middleware.base import BaseHTTPMiddleware`):

```python
from fastapi.responses import HTMLResponse
from loguru import logger

from horta.log import configurar_rexistro
from horta.ui.erros import pagina_erro_html
```

Engadir, despois de `app.add_middleware(AuthMiddleware)` e antes dos imports de páxinas (`import horta.ui.admin.usuarios`, etc.):

```python
configurar_rexistro()


@app.exception_handler(404)
async def manexador_404(request: Request, exc: Exception) -> HTMLResponse:
    return pagina_erro_html("Páxina non atopada", "A ruta que buscas non existe.", 404)


@app.exception_handler(Exception)
async def manexador_500(request: Request, exc: Exception) -> HTMLResponse:
    logger.exception("Erro non controlado en {}: {}", request.url.path, exc)
    return pagina_erro_html(
        "Ocorreu un erro", "Algo saíu mal. Téntao de novo máis tarde.", 500
    )
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/test_main_erros.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Verificación manual de punta a punta (require servidor real)**

Estes tests unitarios comproban as funcións manexadoras directamente, pero non que FastAPI as invoque realmente ante un erro real do servidor — iso require unha comprobación manual:

Run: `uv run python src/horta/main.py` (en segundo plano)

Run: `curl -s http://localhost:8081/isto-non-existe`
Expected: o HTML devolto contén "Páxina non atopada" (non a resposta por defecto de Starlette, que sería un JSON `{"detail":"Not Found"}` ou similar).

Para comprobar o 500, non hai un xeito limpo de provocar un erro real sen modificar código de produción — se atopas algún fluxo existente que provoque un erro non controlado durante esta verificación, confirma que a resposta é a páxina propia e que aparece unha entrada nova en `logs/horta.log`. Se non atopas ningún, anota no informe que este camiño quedou verificado só polos tests unitarios do Step 4, non de punta a punta — é un límite coñecido, non o ignores en silencio.

Parar o servidor despois de verificar.

- [ ] **Step 6: Commit**

```bash
git add src/horta/main.py tests/test_main_erros.py
git commit -m "feat: engadir páxinas de erro 404/500 propias con rexistro"
```

---

## Task 4: Captura xenérica en executar_accion

**Files:**
- Modify: `src/horta/ui/accions.py`
- Test: `tests/ui/test_accions.py`

**Interfaces:**
- Consumes: nada novo (usa `loguru.logger`, xa dependencia).
- Produces: `executar_accion` mantén a mesma sinatura (`(session, accion) -> bool`), pero agora tamén captura calquera `Exception` non recoñecida.

- [ ] **Step 1: Escribir o test que falla**

Engadir a `tests/ui/test_accions.py` (despois do test existente `test_executar_accion_notifica_duplicado_e_fai_rollback`):

```python
def test_executar_accion_captura_erro_inesperado_e_fai_rollback(session, notificacions):
    def accion() -> None:
        raise RuntimeError("fallo inesperado non prantexado")

    resultado = accions.executar_accion(session, accion)

    assert resultado is False
    assert notificacions == [("Ocorreu un erro inesperado. Téntao de novo.", "negative")]
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/ui/test_accions.py::test_executar_accion_captura_erro_inesperado_e_fai_rollback -v`
Expected: FAIL — `RuntimeError` propágase sen capturar (o test falla porque a excepción sae de `executar_accion` en vez de devolver `False`).

- [ ] **Step 3: Implementar en `src/horta/ui/accions.py`**

Engadir `from loguru import logger` aos imports, e engadir unha captura final despois do bloque `except IntegrityError:` existente:

```python
    except IntegrityError:
        session.rollback()
        ui.notify("Xa existe un rexistro con eses datos", type="negative")
        return False
    except Exception as erro:  # noqa: BLE001 — límite deliberado da capa de UI
        session.rollback()
        logger.exception("Erro non previsto en executar_accion: {}", erro)
        ui.notify("Ocorreu un erro inesperado. Téntao de novo.", type="negative")
        return False
    return True
```

- [ ] **Step 4: Executar todos os tests de accions.py e comprobar que pasan**

Run: `uv run pytest tests/ui/test_accions.py -v`
Expected: PASS (todos, incluído o novo)

- [ ] **Step 5: Commit**

```bash
git add src/horta/ui/accions.py tests/ui/test_accions.py
git commit -m "feat: capturar erros inesperados en executar_accion"
```

---

## Task 5: Endurecer os asserts de horta_detalle.py

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: nada novo.
- Produces: nada reutilizable — é UI final. Sen tests automáticos (as páxinas NiceGUI non teñen infraestrutura de test neste proxecto, por deseño — ver `docs/superpowers/specs/2026-09-24-usuarios-hortas-parcelas-design.md`); a verificación é a suite completa (sen regresións) máis unha comprobación manual.

- [ ] **Step 1: Confirmar que non quedan outros `assert` na UI**

Run: `grep -rn assert src/horta/ui/`
Expected: só as dúas liñas xa coñecidas (`horta_detalle.py:56` e `horta_detalle.py:489` — os números de liña poden variar lixeiramente se o ficheiro cambiou; localízaas por contido, non por número). Se aparece algún `assert` máis, avalíao co mesmo criterio do Step 2/3 antes de continuar.

- [ ] **Step 2: Substituír `assert horta is not None` en `horta_detalle_page`**

Localizar (dentro de `horta_detalle_page`, tras a comprobación de `comprobar_rol_horta`):

```python
        horta = session.get(Horta, horta_id)
        assert horta is not None
        parcelas = listar_parcelas(session, actor, horta_id)
```

Substituír por:

```python
        horta = session.get(Horta, horta_id)
        if horta is None:
            cabeceira_paxina()
            ui.label("Esta horta xa non existe").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
```

- [ ] **Step 3: Substituír `assert usuario_membro is not None` en `_seccion_membros`**

Localizar (dentro de `_seccion_membros`):

```python
        for m in membros_bd:
            usuario_membro = session.get(Usuario, m.usuario_id)
            assert usuario_membro is not None
            filas.append(
```

Substituír por (omitir a fila en vez de petar, e rexistrar o caso inconsistente):

```python
        for m in membros_bd:
            usuario_membro = session.get(Usuario, m.usuario_id)
            if usuario_membro is None:
                logger.warning(
                    "HortaMembro horta_id={} usuario_id={} referencia un usuario inexistente",
                    horta_id,
                    m.usuario_id,
                )
                continue
            filas.append(
```

Engadir `from loguru import logger` aos imports de `horta_detalle.py` se non está xa presente.

- [ ] **Step 4: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (todos os tests existentes, sen regresións — esta tarefa non engade tests novos, só endurece código xa non cuberto por tests automáticos)

- [ ] **Step 5: Executar ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 6: Verificación manual**

Run: `uv run python src/horta/main.py` (en segundo plano)

Con sesión de admin, entrar en `/hortas/{id}` dunha horta existente e confirmar que a páxina segue a cargar con normalidade (a sección de Membros segue amosando os membros reais). Isto confirma que o cambio non rompeu o camiño normal — o camiño de erro (horta/usuario inexistente) non é reproducible sen manipular a BD a man, así que non fai falta forzalo.

Parar o servidor despois de verificar.

- [ ] **Step 7: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "fix: substituír asserts fráxiles por comprobacións explícitas"
```

---

## Task 6: Verificación final de conxunto

**Files:**
- Ningún ficheiro novo — só verificación.

**Interfaces:**
- Consumes: todo o anterior.

- [ ] **Step 1: Executar toda a suite de tests**

Run: `uv run pytest -v`
Expected: todos os tests pasan (os existentes máis os desta plan: `test_log.py`, `test_erros.py`, `test_main_erros.py`, e o novo test en `test_accions.py`).

- [ ] **Step 2: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 3: Verificación manual de punta a punta**

Run: `rm -f logs/horta.log` (para partir dun rexistro limpo, se existía)

Run: `uv run python src/horta/main.py` (en segundo plano)

1. `curl -s http://localhost:8081/isto-non-existe` → confirmar corpo con "Páxina non atopada", status 404.
2. Confirmar que `logs/` existe e (se se conseguiu provocar algún erro real na Task 3/5) que `logs/horta.log` ten contido.
3. Login normal e navegación básica (dashboard → horta → parcelas/animais/membros) para confirmar que nada se rompeu coas capturas xenéricas novas.

Parar o servidor despois de verificar.

- [ ] **Step 4: Commit final (só se houbo que corrixir algo nos pasos 1-2)**

```bash
git add -A
git commit -m "chore: corrixir avisos tras a verificación final"
```

(Omitir este commit se non houbo cambios que facer.)

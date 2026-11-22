# Deseño: Robustez — páxinas de erro e rexistro

## Contexto

Esta é a primeira das tres iteracións acordadas para levar a app a un nivel "profesional" tras a revisión de UX (navegación, diálogos, confirmacións): robustez, funcionalidades (busca/filtros/exportar), e deseño visual. Esta spec cobre só a primeira.

Motivación concreta: durante o desenvolvemento, o usuario final visitou `/` cunha sesión cun `usuario_id` que xa non existía na base de datos (tras un reset de BD en desenvolvemento) e viu un erro técnico en bruto (`500 Server error / AssertionError`) en vez dunha páxina comprensible. Aínda que ese caso concreto xa quedou arranxado (`usuario_actual()` revalida a sesión e redirixe a `/login`), o problema de fondo segue existindo: calquera erro non previsto (un bug futuro, un dato inconsistente) segue amosando o erro técnico en bruto de Starlette/FastAPI, sen rexistro para poder investigalo despois.

## Obxectivo

1. Que calquera erro non controlado (404 ou 500) amose unha páxina propia en galego, nunca o erro técnico en bruto.
2. Que ese tipo de erro quede rexistrado no servidor (con loguru) para poder investigalo despois.
3. Que as accións que xa pasan por `executar_accion` (crear/editar/eliminar) capturen tamén erros non previstos, non só os xa coñecidos (`PermisoDenegadoError`, `OperacionNonPermitidaError`, `IntegrityError`), amosando un aviso xenérico en vez de fallar en silencio ou propagar ao navegador.
4. Eliminar os `assert` restantes na capa de UI que dependen de invariantes que poderían romperse por datos externos (non por un erro de programación), substituíndoos por comprobacións que dean un aviso claro.

## Fóra de alcance

Busca/filtros/exportación/paxinación/historial (iteración "Funcionalidades"), sistema de deseño visual máis elaborado (iteración "Deseño visual"), estados de carga/spinners durante accións (non se pediu, e cos volumes de datos actuais non achega valor claro).

## Arquitectura

Dous niveis de captura:

```
Petición HTTP
    │
    ├─ Erro durante a carga dunha páxina (404 / calquera Exception)
    │      → manexador de excepción de FastAPI/NiceGUI
    │      → páxina HTML propia (erros.py) + rexistro con loguru
    │
    └─ Erro dentro dun manexador de clic xa en execución
           → executar_accion (accions.py)
           → captura específica xa existente (PermisoDenegadoError,
             OperacionNonPermitidaError, IntegrityError)
           → NOVO: captura xenérica final para calquera outra excepción
             → ui.notify xenérico + rexistro con loguru
```

## Compoñentes

### `src/horta/log.py` (novo)

Configura loguru unha soa vez, chamado ao arrincar a app (`main.py`, antes de `ui.run()`):

```python
from __future__ import annotations

from pathlib import Path

from loguru import logger

_XA_CONFIGURADO = False


def configurar_rexistro() -> None:
    global _XA_CONFIGURADO
    if _XA_CONFIGURADO:
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
    _XA_CONFIGURADO = True
```

`diagnose=False` porque `diagnose=True` inclúe valores de variables locais no traceback, o que podería filtrar contrasinais/hash en claro nos logs — mellor evitalo por defecto.

Engadir `logs/` ao `.gitignore`.

### `src/horta/ui/erros.py` (novo)

```python
from __future__ import annotations

from fastapi.responses import HTMLResponse

from horta.ui.nav import COR_FONDO, COR_NEGATIVA, COR_PRIMARIA, COR_TEXTO


def pagina_erro_html(titulo: str, mensaxe: str, codigo: int) -> HTMLResponse:
    html = f"""
    <!DOCTYPE html>
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
            h1 {{ color: {COR_NEGATIVA if codigo >= 500 else COR_PRIMARIA}; }}
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
    </html>
    """
    return HTMLResponse(content=html, status_code=codigo)
```

(`COR_FONDO`/`COR_NEGATIVA`/`COR_PRIMARIA`/`COR_TEXTO` xa existen en `nav.py` — reutilízanse, non se duplican.)

### `src/horta/main.py` (modificado)

Engadir, antes de `def main()`:

```python
from fastapi import Request
from horta.log import configurar_rexistro
from horta.ui.erros import pagina_erro_html
from loguru import logger

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

### `src/horta/ui/accions.py` (modificado)

`executar_accion` engade unha última captura xenérica (despois das específicas xa existentes):

```python
except (PermisoDenegadoError, OperacionNonPermitidaError) as e:
    ...  # xa existente
except IntegrityError:
    ...  # xa existente
except Exception as e:  # noqa: BLE001 — captura deliberada, é o límite da UI
    session.rollback()
    logger.exception("Erro non previsto en executar_accion: {}", e)
    ui.notify("Ocorreu un erro inesperado. Téntao de novo.", type="negative")
    return False
```

### Auditoría de `assert` na UI

Buscar todos os `assert` en `src/horta/ui/` (`grep -rn assert src/horta/ui/`) e avaliar cada un individualmente: se o dato podería faltar por unha causa alcanzable en uso normal (non só un bug de programación), substituír por unha comprobación explícita. Casos xa identificados:
- `horta_detalle.py`, sección de Membros: `assert usuario_membro is not None` ao construír a táboa — se un `HortaMembro` referenciase un `Usuario` inexistente (hoxe non debería pasar, xa que non hai borrado de usuarios, só desactivación), a fila omítese e rexístrase un aviso en vez de petar toda a páxina.
- `horta_detalle.py`, `horta_detalle_page`: `assert horta is not None` tras `session.get(Horta, horta_id)` — se a horta se eliminou nun intre entre a comprobación de permiso e esta liña (pouco probable pero posible con dous usuarios concorrentes), amosar "Esta horta xa non existe" en vez de petar.
- Calquera outro `assert` que apareza na busca e cumpra o mesmo criterio.

## Probas

- **`tests/ui/test_accions.py`**: novo test confirmando que unha excepción xenérica non recoñecida (p.ex. `ValueError` simple, distinto de `OperacionNonPermitidaError`) é capturada por `executar_accion`, devolve `False`, e non se propaga.
- **Manual (curl, sen navegador dispoñible neste entorno)**:
  - `curl http://localhost:8081/isto-non-existe` → debe devolver 404 coa páxina propia (comprobar que o corpo conten "Páxina non atopada", non un traceback).
  - Provocar un 500 real (p.ex. unha cookie de sesión cun `usuario_id` que xa non exista, reproducindo o caso orixinal) → debe devolver 500 coa páxina propia, e debe aparecer unha entrada nova en `logs/horta.log`.
- Suite completa (`uv run pytest`), ruff, mypy — deben seguir pasando/limpos.

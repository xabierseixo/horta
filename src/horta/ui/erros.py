from __future__ import annotations

from fastapi.responses import HTMLResponse

from horta.ui.tema import COR_ERRO as COR_NEGATIVA
from horta.ui.tema import COR_FONDO, COR_PRIMARIA, COR_TEXTO


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

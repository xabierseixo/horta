"""Probas dos ficheiros estáticos da PWA do campo."""

from __future__ import annotations

import json
from starlette.testclient import TestClient

from horta.main import app


def test_campo_index_devolve_html() -> None:
    client = TestClient(app)
    response = client.get("/campo/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "AgroXest360 Campo" in response.text
    assert "manifest.webmanifest" in response.text
    assert "sw.js" in response.text

    resp_redirect = client.get("/campo", follow_redirects=True)
    assert resp_redirect.status_code == 200
    assert "AgroXest360 Campo" in resp_redirect.text


def test_campo_manifest_json_valido() -> None:
    client = TestClient(app)
    response = client.get("/campo/manifest.webmanifest")
    assert response.status_code == 200
    datos = json.loads(response.text)
    assert datos.get("name") == "AgroXest360 Campo"
    assert datos.get("display") == "standalone"
    assert datos.get("theme_color") == "#2F7D4F"
    assert "icons" in datos and len(datos["icons"]) > 0


def test_campo_service_worker_existe() -> None:
    client = TestClient(app)
    response = client.get("/campo/sw.js")
    assert response.status_code == 200
    assert "agroxest360-campo" in response.text
    assert "CACHE_NAME" in response.text


def test_campo_icona_e_recursos_adicionais() -> None:
    client = TestClient(app)

    resp_icon = client.get("/campo/icona.svg")
    assert resp_icon.status_code == 200
    assert "<svg" in resp_icon.text

    resp_css = client.get("/campo/estilo.css")
    assert resp_css.status_code == 200
    assert "--cor-primaria" in resp_css.text

    resp_js = client.get("/campo/app.js")
    assert resp_js.status_code == 200
    assert "crypto.randomUUID" in resp_js.text

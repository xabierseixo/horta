"""Probas da API de lectura do campo (app móbil sen conexión)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from horta.api.campo import obter_session, router
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.dispositivos import crear_dispositivo, revogar_dispositivo
from horta.services.hortas import crear_horta
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
from horta.services.tarefas import crear_tarefa


@pytest.fixture()
def client(session: Session) -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[obter_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client


def _crear_usuario(session: Session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0].capitalize(),
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_autenticacion_sen_clave_ou_invalida(client: TestClient) -> None:
    r_sen_cabeceira = client.get("/api/campo/explotacions")
    assert r_sen_cabeceira.status_code == 401

    r_clave_falsa = client.get(
        "/api/campo/explotacions",
        headers={"Authorization": "Bearer clave-non-existente"},
    )
    assert r_clave_falsa.status_code == 401

    r_basic = client.get(
        "/api/campo/explotacions",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert r_basic.status_code == 401


def test_crear_dispositivo_devolve_clave_que_funciona(
    client: TestClient, session: Session
) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")

    resposta = client.get(
        "/api/campo/explotacions",
        headers={"Authorization": f"Bearer {clave}"},
    )
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_clave_revogada_da_401(client: TestClient, session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    disp, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    revogar_dispositivo(session, ana, disp)

    resposta = client.get(
        "/api/campo/explotacions",
        headers={"Authorization": f"Bearer {clave}"},
    )
    assert resposta.status_code == 401


def test_explotacions_so_lista_as_do_usuario(
    client: TestClient, session: Session
) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")

    horta_ana = crear_horta(session, ana, "Horta de Ana")
    crear_horta(session, bea, "Horta de Bea")

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")

    resposta = client.get(
        "/api/campo/explotacions",
        headers={"Authorization": f"Bearer {clave}"},
    )
    assert resposta.status_code == 200
    assert resposta.json() == [
        {"id": horta_ana.id, "nome": "Horta de Ana", "rol": "admin"}
    ]


def test_datos_dunha_horta_allea_da_403(
    client: TestClient, session: Session
) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")

    horta_bea = crear_horta(session, bea, "Horta de Bea")
    _, clave_ana = crear_dispositivo(session, ana, "Móbil de Ana")

    resposta = client.get(
        f"/api/campo/explotacions/{horta_bea.id}/datos",
        headers={"Authorization": f"Bearer {clave_ana}"},
    )
    assert resposta.status_code == 403


def test_datos_dunha_propia_trae_parcelas_cultivos_e_persoas(
    client: TestClient, session: Session, cultivos_siex: Any
) -> None:
    cultivos_siex(101)
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta propia")

    parcela = crear_parcela(session, ana, horta.id, "Agra da Cruz")
    cultivo_aberto = crear_cultivo(
        session, ana, parcela.id, "Pemento de Padrón", cultivo_siex_codigo=101
    )
    cultivo_pechado = crear_cultivo(
        session, ana, parcela.id, "Espinaca", data_fin=date(2025, 1, 1)
    )
    persoa = crear_persoa(session, ana, horta.id, "Xan", papeis={"traballador"})
    maquina = crear_maquina(session, ana, horta.id, "Mochila pulverizadora")
    tarefa = crear_tarefa(
        session,
        ana,
        horta.id,
        "Revisar trampas",
        data=date.today(),
        parcela_id=parcela.id,
        cultivo_id=cultivo_aberto.id,
        tipo="observacion",
    )

    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")

    resposta = client.get(
        f"/api/campo/explotacions/{horta.id}/datos",
        headers={"Authorization": f"Bearer {clave}"},
    )
    assert resposta.status_code == 200
    datos = resposta.json()

    # Parcelas
    assert {"id": parcela.id, "nome": "Agra da Cruz"} in datos["parcelas"]

    # Cultivos abertos (o pechado non debe saír)
    ids_cultivos = [c["id"] for c in datos["cultivos"]]
    assert cultivo_aberto.id in ids_cultivos
    assert cultivo_pechado.id not in ids_cultivos
    cultivo_dto = next(c for c in datos["cultivos"] if c["id"] == cultivo_aberto.id)
    assert cultivo_dto["nome"] == "Pemento de Padrón"
    assert cultivo_dto["parcela_id"] == parcela.id

    # Persoas activas
    persoas_nomes = [p["nome"] for p in datos["persoas"]]
    assert persoa.nome in persoas_nomes
    xan_dto = next(p for p in datos["persoas"] if p["nome"] == persoa.nome)
    assert "traballador" in xan_dto["papeis"]

    # Máquinas
    assert {"id": maquina.id, "alias": "Mochila pulverizadora"} in datos["maquinas"]

    # Tarefas pendentes
    ids_tarefas = [t["id"] for t in datos["tarefas_pendentes"]]
    assert tarefa.id in ids_tarefas
    tarefa_dto = next(t for t in datos["tarefas_pendentes"] if t["id"] == tarefa.id)
    assert tarefa_dto["descricion"] == "Revisar trampas"
    assert tarefa_dto["tipo"] == "observacion"

    # Pragas por cultivo e catálogos de apoio
    assert str(cultivo_aberto.id) in datos["pragas_por_cultivo"]
    assert "trampa" in datos["metodos"]
    assert "capturas por trampa" in datos["unidades_conto"]
    assert "alto" in datos["niveis"]
    assert isinstance(datos["tipos_labor"], dict)
    assert isinstance(datos["sistemas_rega"], dict)
    assert "xerado_en" in datos

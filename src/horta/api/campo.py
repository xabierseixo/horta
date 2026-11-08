"""API REST para a app do campo sen cobertura (PWA)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.usuario import Usuario
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.dispositivos import usuario_do_token
from horta.services.errors import PermisoDenegadoError
from horta.services.fito_consulta import (
    etiqueta_problema,
    nomes_comuns_problemas,
    problemas_do_cultivo,
)
from horta.services.hortas import listar_hortas_usuario
from horta.services.maquinaria import listar_maquinas
from horta.services.observacions import METODOS, NIVEIS, TIPOS_PROBLEMA, UNIDADES_CONTO
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_persoas
from horta.services.tarefas import listar_tarefas
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.pasos_tratamento import ordenar_problemas

router = APIRouter(prefix="/api/campo")
_bearer = HTTPBearer(auto_error=False)


def obter_session() -> Iterator[Session]:
    """Dependencia que proporciona unha sesión de base de datos."""
    with get_session() as session:
        yield session


def obter_usuario_actual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(obter_session),
) -> Usuario:
    """Valida a cabeceira Bearer e devolve o usuario dono do dispositivo."""
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta a cabeceira de autorización Bearer",
        )
    usuario = usuario_do_token(session, credenciais.credentials)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave de dispositivo non válida ou revogada",
        )
    return usuario


@router.get("/explotacions")
def explotacions(
    usuario: Usuario = Depends(obter_usuario_actual),
    session: Session = Depends(obter_session),
) -> list[dict[str, Any]]:
    """Lista as explotacións nas que participa o usuario."""
    hortas = listar_hortas_usuario(session, usuario)
    return [
        {
            "id": horta.id,
            "nome": horta.nome,
            "rol": rol.value if hasattr(rol, "value") else str(rol),
        }
        for horta, rol in hortas
    ]


@router.get("/explotacions/{horta_id}/datos")
def datos_explotacion(
    horta_id: int,
    usuario: Usuario = Depends(obter_usuario_actual),
    session: Session = Depends(obter_session),
) -> dict[str, Any]:
    """Devolve todo o necesario para que a app poida traballar sen conexión nunha horta."""
    try:
        parcelas = listar_parcelas(session, usuario, horta_id)
        cultivos = listar_cultivos(session, usuario, horta_id)
        persoas = listar_persoas(session, usuario, horta_id, so_activas=True)
        maquinas = listar_maquinas(session, usuario, horta_id, so_activas=True)
        tarefas = listar_tarefas(session, usuario, horta_id)
    except PermisoDenegadoError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    hoxe = date.today()
    cultivos_abertos = [
        c for c in cultivos
        if c.data_fin is None or c.data_fin >= hoxe
    ]

    nomes_comuns = {t: nomes_comuns_problemas(session, t) for t in TIPOS_PROBLEMA}
    opcions_problemas = {
        t: {
            v.codigo: etiqueta_problema(
                v.descricion, nomes_comuns[t].get(v.codigo, [])
            )
            for v in valores_vixentes(session, t)
        }
        for t in TIPOS_PROBLEMA
    }

    pragas_por_cultivo: dict[str, dict[str, dict[str, str]]] = {
        str(c.id): {
            tipo: ordenar_problemas(
                opcions_problemas.get(tipo, {}),
                problemas_do_cultivo(session, c.cultivo_siex_codigo, tipo),
                None,
            )
            for tipo in TIPOS_PROBLEMA
        }
        for c in cultivos_abertos
    }

    tipos_labor = {
        v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
        for v in valores_vixentes(session, "tipo_labor")
    }
    sistemas_rega = {
        v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
        for v in valores_vixentes(session, "sistema_rega")
    }

    return {
        "parcelas": [{"id": p.id, "nome": p.nome} for p in parcelas],
        "cultivos": [
            {
                "id": c.id,
                "nome": nome_cultivo(c),
                "parcela_id": c.parcela_id,
            }
            for c in cultivos_abertos
        ],
        "persoas": [
            {"id": p.id, "nome": p.nome, "papeis": sorted(p.papeis)}
            for p in persoas
        ],
        "maquinas": [{"id": m.id, "alias": m.alias} for m in maquinas],
        "tarefas_pendentes": [
            {
                "id": t.id,
                "descricion": t.descricion,
                "data": t.data.isoformat() if t.data else None,
                "parcela_id": t.parcela_id,
                "cultivo_id": t.cultivo_id,
                "tipo": t.tipo,
            }
            for t in tarefas
            if t.estado == "pendente"
        ],
        "pragas_por_cultivo": pragas_por_cultivo,
        "metodos": METODOS,
        "unidades_conto": UNIDADES_CONTO,
        "niveis": NIVEIS,
        "tipos_labor": tipos_labor,
        "sistemas_rega": sistemas_rega,
        "xerado_en": datetime.now(timezone.utc).isoformat(),
    }

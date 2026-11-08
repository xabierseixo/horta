"""API REST para a app do campo sen cobertura (PWA).

Inclúe as rutas de sincronización co dispositivo móbil:
- `GET /api/campo/explotacions`: lista as explotacións onde participa o usuario.
- `GET /api/campo/explotacions/{horta_id}/datos`: descarga datos mestres para traballo sen rede.
- `POST /api/campo/explotacions/{horta_id}/rexistros`: envía traballos apuntados no móbil.

Formato do corpo en `POST /api/campo/explotacions/{horta_id}/rexistros`:
Lista de obxectos JSON:
[
    {
        "uuid": "<identificador único xerado polo dispositivo, str de ata 36 caracteres>",
        "tipo": "observacion" | "rega" | "labor" | "colleita" | "tarefa_feita",
        "datos": { ... }
    }
]

Formato de `datos` segundo o `tipo` (os nomes coinciden cos argumentos dos servizos;
as datas van en formato ISO `AAAA-MM-DD`):

1. "observacion" (servizo `crear_observacion` en `services/observacions.py`):
   - cultivo_id (int, obrigatorio): identificador do cultivo na explotación.
   - data (str ISO, obrigatorio): data da observación.
   - problema_tipo (str, obrigatorio): tipo de problema ("praga", "enfermidade", "mala_herba").
   - problema_codigo (str, obrigatorio): código do catálogo oficial do problema.
   - metodo (str, obrigatorio): método ("trampa", "mostraxe", "sintomas").
   - conto (float, opcional): reconto numérico obtido.
   - unidade_conto (str, opcional): unidade de conto ("capturas por trampa", "% de plantas", etc.).
   - nivel (str, opcional): nivel cualitativo ("sen", "baixo", "medio", "alto").
   - estado_fenoloxico (str, opcional): código do catálogo de estado fenolóxico.
   - notas (str, opcional): texto de notas adicionais.
   - persoa_id (int, opcional): persoa que fixo a observación.
   - visita_id (int, opcional): identificador da visita de campo asociada.

2. "rega" (servizo `crear_rega` en `services/regas.py`, estrutura `DatosRega`):
   - data_inicio (str ISO, obrigatorio; tamén admite data): data de inicio da rega.
   - cultivo_id (int, opcional): cultivo regado (ou especificarse a través de leiras).
   - sistema_rega (str, opcional): código do catálogo de sistema de rega.
   - cantidade (float, opcional): cantidade de auga achegada.
   - unidade (str, opcional): unidade de medida ("4" para litros por defecto, ou "3" para m³).
   - data_fin (str ISO, opcional): data de remate se durou varios días.
   - superficie_ha (float, opcional): superficie regada en hectáreas.
   - orixe_auga (str, opcional): código do catálogo de orixe da auga.
   - tipo_enerxia (str, opcional): código do catálogo de tipo de enerxía.
   - num_contador (str, opcional): lectura ou número de contador de auga.
   - persoa_id (int, opcional): persoa que realizou a rega.
   - horas (float, opcional): horas de traballo adicadas.
   - maquina_id (int, opcional): máquina utilizada.
   - boas_practicas (list[str], opcional): lista de códigos de boas prácticas de rega.
   - notas (str, opcional): notas adicionais.
   - leiras (list, opcional): lista de obxectos con cultivo e superficie se abrangue varias.

3. "labor" (servizo `crear_labor` en `services/labores.py`, estrutura `DatosLabor`):
   - data_inicio (str ISO, obrigatorio; tamén admite data): data de inicio do labor.
   - tipo_labor (str, obrigatorio): código do catálogo de tipos de labor.
   - cultivo_id (int, opcional): cultivo onde se realiza o labor.
   - data_fin (str ISO, opcional): data de fin do labor.
   - superficie_ha (float, opcional): superficie traballada en hectáreas.
   - restos_desbroce_no_solo (bool, opcional): se os restos de desbroce quedan no solo.
   - restos_poda_no_solo (bool, opcional): se os restos de poda quedan no solo.
   - tipo_cobertura (str, opcional): código do catálogo de tipo de cobertura do solo.
   - maquina_id (int, opcional): máquina utilizada.
   - num_repeticions (int, opcional): número de repeticións.
   - duracion_h (float, opcional): duración do labor en horas.
   - persoa_id (int, opcional): persoa que realizou o labor.
   - horas (float, opcional): horas de traballo da persoa.
   - notas (str, opcional): notas adicionais.
   - leiras (list, opcional): lista de leiras se abrangue varias.

4. "colleita" (servizo `crear_colleita` en `services/colleitas.py`, estrutura `DatosColleita`):
   - cultivo_id (int, obrigatorio): cultivo colleitado.
   - data (str ISO, obrigatorio): data da colleita.
   - cantidade (float, obrigatorio): cantidade colleitada (maior que 0).
   - unidade (str, obrigatorio): unidade de colleita ("kg", "t", "unidades", etc.).
   - lote (str, opcional): código do lote onde entra (se vai baleiro, propónse automaticamente).
   - superficie_ha (float, opcional): superficie colleitada en hectáreas.
   - destino_colleita (str, opcional): código do destino ("22", "23", etc.).
   - destino_restos (str, opcional): código do destino dos restos.
   - notas (str, opcional): notas adicionais.
   - data_fin (str ISO, opcional): data de fin da colleita.
   - obten_sementes (bool, opcional): se se obteñen sementes.
   - obten_plantas (bool, opcional): se se obteñen plantas.
   - sen_colleita_ambiental (bool, opcional): se non houbo colleita por causas ambientais.
   - restos_no_solo (bool, opcional): se os restos quedan no solo.
   - maquina_id (int, opcional): máquina empregada.
   - num_repeticions (int, opcional): número de repeticións.
   - duracion_h_ha (float, opcional): horas por hectárea.
   - persoa_id (int, opcional): persoa que fixo a colleita.
   - horas (float, opcional): horas traballadas pola persoa.

5. "tarefa_feita" (servizo `marcar_feita` en `services/tarefas.py`):
   - id (int, obrigatorio): identificador da tarefa que se dá por feita.
   - data (str ISO, opcional): data na que se completou (por defecto a data actual).
   - persoa_id (int, opcional): persoa que realizou a tarefa.
   - horas (float, opcional): horas traballadas na tarefa.

Resposta da API:
Lista de obxectos co resultado de cada elemento enviado:
[
    {
        "uuid": "<uuid>",
        "estado": "creado" | "xa_estaba" | "erro",
        "id": <int | None>,
        "mensaxe": <str | None>
    }
]
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.observacion import ObservacionPraga
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.catalogos import valores_vixentes
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.dispositivos import usuario_do_token
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.fito_consulta import (
    etiqueta_problema,
    nomes_comuns_problemas,
    problemas_do_cultivo,
)
from horta.services.hortas import comprobar_rol_horta, listar_hortas_usuario
from horta.services.labores import DatosLabor, crear_labor
from horta.services.maquinaria import listar_maquinas
from horta.services.observacions import (
    METODOS,
    NIVEIS,
    TIPOS_PROBLEMA,
    UNIDADES_CONTO,
    crear_observacion,
)
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_persoas
from horta.services.regas import DatosRega, crear_rega
from horta.services.tarefas import listar_tarefas, marcar_feita
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.pasos_tratamento import ordenar_problemas

router = APIRouter(prefix="/api/campo")
_bearer = HTTPBearer(auto_error=False)

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_TIPOS_ADMITIDOS = frozenset({"observacion", "rega", "labor", "colleita", "tarefa_feita"})

_CAMPOS_OBSERVACION = frozenset(
    {
        "cultivo_id",
        "data",
        "problema_tipo",
        "problema_codigo",
        "metodo",
        "conto",
        "unidade_conto",
        "nivel",
        "estado_fenoloxico",
        "notas",
        "persoa_id",
        "visita_id",
    }
)

_CAMPOS_REGA = frozenset(
    {
        "cultivo_id",
        "data_inicio",
        "data",
        "data_fin",
        "sistema_rega",
        "cantidade",
        "unidade",
        "superficie_ha",
        "orixe_auga",
        "tipo_enerxia",
        "num_contador",
        "persoa_id",
        "horas",
        "maquina_id",
        "boas_practicas",
        "notas",
        "leiras",
    }
)

_CAMPOS_LABOR = frozenset(
    {
        "cultivo_id",
        "data_inicio",
        "data",
        "tipo_labor",
        "data_fin",
        "superficie_ha",
        "restos_desbroce_no_solo",
        "restos_poda_no_solo",
        "tipo_cobertura",
        "maquina_id",
        "num_repeticions",
        "duracion_h",
        "persoa_id",
        "horas",
        "notas",
        "leiras",
    }
)

_CAMPOS_COLLEITA = frozenset(
    {
        "cultivo_id",
        "data",
        "cantidade",
        "unidade",
        "lote",
        "superficie_ha",
        "destino_colleita",
        "destino_restos",
        "notas",
        "data_fin",
        "obten_sementes",
        "obten_plantas",
        "sen_colleita_ambiental",
        "restos_no_solo",
        "maquina_id",
        "num_repeticions",
        "duracion_h_ha",
        "persoa_id",
        "horas",
    }
)

_CAMPOS_TAREFA_FEITA = frozenset(
    {
        "id",
        "data",
        "persoa_id",
        "horas",
    }
)

_CAMPOS_PERMITIDOS: dict[str, frozenset[str]] = {
    "observacion": _CAMPOS_OBSERVACION,
    "rega": _CAMPOS_REGA,
    "labor": _CAMPOS_LABOR,
    "colleita": _CAMPOS_COLLEITA,
    "tarefa_feita": _CAMPOS_TAREFA_FEITA,
}


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


def _buscar_existente(session: Session, horta_id: int, tipo: str, item_uuid: str) -> Any:
    """Busca se xa existe un rexistro dese modelo co mesmo uuid na explotación."""
    if tipo == "observacion":
        return (
            session.query(ObservacionPraga)
            .filter(
                ObservacionPraga.horta_id == horta_id,
                ObservacionPraga.uuid == item_uuid,
            )
            .first()
        )
    if tipo == "rega":
        return (
            session.query(Rega)
            .filter(
                Rega.horta_id == horta_id,
                Rega.uuid == item_uuid,
            )
            .first()
        )
    if tipo == "labor":
        return (
            session.query(Labor)
            .filter(
                Labor.horta_id == horta_id,
                Labor.uuid == item_uuid,
            )
            .first()
        )
    if tipo == "colleita":
        return (
            session.query(Colleita)
            .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
            .join(Parcela, Cultivo.parcela_id == Parcela.id)
            .filter(
                Parcela.horta_id == horta_id,
                Colleita.uuid == item_uuid,
            )
            .first()
        )
    if tipo == "tarefa_feita":
        return (
            session.query(Tarefa)
            .filter(
                Tarefa.horta_id == horta_id,
                Tarefa.uuid == item_uuid,
            )
            .first()
        )
    return None


def _converter_data(valor: Any, nome_campo: str = "data") -> date:
    """Converte un valor a obxecto date, validando o formato ISO AAAA-MM-DD."""
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and valor.strip():
        try:
            return date.fromisoformat(valor.strip())
        except ValueError:
            raise ValueError(
                f"Formato de data non válido en {nome_campo}: {valor} (debe ser AAAA-MM-DD)"
            )
    raise ValueError(f"Falta a data obrigatoria: {nome_campo}")


def _converter_data_opcional(valor: Any, nome_campo: str = "data") -> date | None:
    """Converte unha data opcional a date ou None."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    return _converter_data(valor, nome_campo)


def _obter_persoa_defecto(session: Session, horta_id: int, usuario: Usuario) -> int | None:
    """Busca o identificador de persoa correspondente ao usuario na horta se existe."""
    persoa = (
        session.query(Persoa)
        .filter(
            Persoa.horta_id == horta_id,
            Persoa.usuario_id == usuario.id,
            Persoa.activa.is_(True),
        )
        .first()
    )
    return persoa.id if persoa else None


@router.post("/explotacions/{horta_id}/rexistros")
def enviar_rexistros(
    horta_id: int,
    rexistros: list[dict[str, Any]] = Body(...),
    usuario: Usuario = Depends(obter_usuario_actual),
    session: Session = Depends(obter_session),
) -> list[dict[str, Any]]:
    """Recibe unha lista de rexistros apuntados sen conexión e procesa cada un."""
    try:
        comprobar_rol_horta(session, horta_id, usuario, _ROLES_ESCRITURA)
    except PermisoDenegadoError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    resultados: list[dict[str, Any]] = []

    for item in rexistros:
        if not isinstance(item, dict):
            resultados.append({
                "uuid": "",
                "estado": "erro",
                "id": None,
                "mensaxe": "O rexistro enviado non ten o formato de obxecto axeitado",
            })
            continue

        item_uuid = item.get("uuid")
        if not item_uuid or not isinstance(item_uuid, str):
            resultados.append({
                "uuid": str(item_uuid or ""),
                "estado": "erro",
                "id": None,
                "mensaxe": "Falta o identificador único (uuid)",
            })
            continue
        item_uuid = item_uuid.strip()

        tipo = item.get("tipo")
        if tipo not in _TIPOS_ADMITIDOS:
            resultados.append({
                "uuid": item_uuid,
                "estado": "erro",
                "id": None,
                "mensaxe": f"Tipo de rexistro descoñecido: {tipo}",
            })
            continue

        datos_raw = item.get("datos")
        if not isinstance(datos_raw, dict):
            resultados.append({
                "uuid": item_uuid,
                "estado": "erro",
                "id": None,
                "mensaxe": "Os datos do rexistro teñen que ser un obxecto",
            })
            continue
        datos = dict(datos_raw)

        # Se xa existía ese rexistro co mesmo uuid na horta, devolvemos xa_estaba
        existente = _buscar_existente(session, horta_id, tipo, item_uuid)
        if existente is not None:
            resultados.append({
                "uuid": item_uuid,
                "estado": "xa_estaba",
                "id": existente.id,
                "mensaxe": None,
            })
            continue

        try:
            campos_permitidos = _CAMPOS_PERMITIDOS[tipo]
            desconecidos = sorted(set(datos.keys()) - campos_permitidos)
            if desconecidos:
                raise ValueError(f"Campo descoñecido: {', '.join(desconecidos)}")

            novo_id: int | None = None
            persoa_defecto = _obter_persoa_defecto(session, horta_id, usuario)

            if tipo == "observacion":
                if "cultivo_id" not in datos:
                    raise ValueError("Falta o campo obrigatorio: cultivo_id")
                if "data" not in datos:
                    raise ValueError("Falta o campo obrigatorio: data")
                if "problema_tipo" not in datos:
                    raise ValueError("Falta o campo obrigatorio: problema_tipo")
                if "problema_codigo" not in datos:
                    raise ValueError("Falta o campo obrigatorio: problema_codigo")
                if "metodo" not in datos:
                    raise ValueError("Falta o campo obrigatorio: metodo")

                data_obs = _converter_data(datos["data"], "data")
                persoa_obs = datos.get("persoa_id") or persoa_defecto

                obs = crear_observacion(
                    session,
                    usuario,
                    horta_id,
                    cultivo_id=datos["cultivo_id"],
                    data=data_obs,
                    problema_tipo=datos["problema_tipo"],
                    problema_codigo=datos["problema_codigo"],
                    metodo=datos["metodo"],
                    conto=float(datos["conto"]) if datos.get("conto") is not None else None,
                    unidade_conto=datos.get("unidade_conto"),
                    nivel=datos.get("nivel"),
                    estado_fenoloxico=datos.get("estado_fenoloxico"),
                    notas=datos.get("notas"),
                    persoa_id=persoa_obs,
                    visita_id=datos.get("visita_id"),
                )
                obs.uuid = item_uuid
                session.commit()
                novo_id = obs.id

            elif tipo == "rega":
                data_inicio_raw = datos.get("data_inicio") or datos.get("data")
                if data_inicio_raw is None:
                    raise ValueError("Falta a data obrigatoria da rega (data_inicio)")
                data_inicio_rega = _converter_data(data_inicio_raw, "data_inicio")
                data_fin_rega = _converter_data_opcional(datos.get("data_fin"), "data_fin")
                persoa_rega = datos.get("persoa_id") or persoa_defecto

                datos_rega = DatosRega(
                    data_inicio=data_inicio_rega,
                    data_fin=data_fin_rega,
                    cultivo_id=datos.get("cultivo_id"),
                    sistema_rega=datos.get("sistema_rega"),
                    cantidade=(
                        float(datos["cantidade"])
                        if datos.get("cantidade") is not None
                        else None
                    ),
                    unidade=str(datos.get("unidade", "4")),
                    superficie_ha=(
                        float(datos["superficie_ha"])
                        if datos.get("superficie_ha") is not None
                        else None
                    ),
                    orixe_auga=datos.get("orixe_auga"),
                    tipo_enerxia=datos.get("tipo_enerxia"),
                    num_contador=datos.get("num_contador"),
                    persoa_id=persoa_rega,
                    horas=(
                        float(datos["horas"])
                        if datos.get("horas") is not None
                        else None
                    ),
                    maquina_id=datos.get("maquina_id"),
                    boas_practicas=list(datos.get("boas_practicas") or []),
                    notas=datos.get("notas"),
                    leiras=list(datos.get("leiras") or []),
                )
                rega = crear_rega(session, usuario, datos_rega)
                rega.uuid = item_uuid
                session.commit()
                novo_id = rega.id

            elif tipo == "labor":
                data_inicio_raw = datos.get("data_inicio") or datos.get("data")
                if data_inicio_raw is None:
                    raise ValueError("Falta a data obrigatoria do labor (data_inicio)")
                data_inicio_labor = _converter_data(data_inicio_raw, "data_inicio")
                data_fin_labor = _converter_data_opcional(datos.get("data_fin"), "data_fin")
                if "tipo_labor" not in datos:
                    raise ValueError("Falta o tipo de labor obrigatorio (tipo_labor)")
                persoa_labor = datos.get("persoa_id") or persoa_defecto

                datos_labor = DatosLabor(
                    data_inicio=data_inicio_labor,
                    tipo_labor=str(datos["tipo_labor"]),
                    cultivo_id=datos.get("cultivo_id"),
                    superficie_ha=(
                        float(datos["superficie_ha"])
                        if datos.get("superficie_ha") is not None
                        else None
                    ),
                    data_fin=data_fin_labor,
                    restos_desbroce_no_solo=bool(datos.get("restos_desbroce_no_solo", False)),
                    restos_poda_no_solo=bool(datos.get("restos_poda_no_solo", False)),
                    tipo_cobertura=datos.get("tipo_cobertura"),
                    maquina_id=datos.get("maquina_id"),
                    num_repeticions=(
                        int(datos["num_repeticions"])
                        if datos.get("num_repeticions") is not None
                        else None
                    ),
                    duracion_h=(
                        float(datos["duracion_h"])
                        if datos.get("duracion_h") is not None
                        else None
                    ),
                    persoa_id=persoa_labor,
                    horas=(
                        float(datos["horas"])
                        if datos.get("horas") is not None
                        else None
                    ),
                    notas=datos.get("notas"),
                    leiras=list(datos.get("leiras") or []),
                )
                labor = crear_labor(session, usuario, datos_labor)
                labor.uuid = item_uuid
                session.commit()
                novo_id = labor.id

            elif tipo == "colleita":
                if "cultivo_id" not in datos:
                    raise ValueError("Falta o campo obrigatorio: cultivo_id")
                if "data" not in datos:
                    raise ValueError("Falta a data obrigatoria da colleita (data)")
                data_colleita = _converter_data(datos["data"], "data")
                data_fin_colleita = _converter_data_opcional(datos.get("data_fin"), "data_fin")
                if "cantidade" not in datos:
                    raise ValueError("Falta a cantidade colleitada (cantidade)")
                if "unidade" not in datos:
                    raise ValueError("Falta a unidade de colleita (unidade)")
                persoa_colleita = datos.get("persoa_id") or persoa_defecto

                datos_colleita = DatosColleita(
                    cultivo_id=int(datos["cultivo_id"]),
                    data=data_colleita,
                    cantidade=float(datos["cantidade"]),
                    unidade=str(datos["unidade"]),
                    lote=str(datos.get("lote") or ""),
                    superficie_ha=(
                        float(datos["superficie_ha"])
                        if datos.get("superficie_ha") is not None
                        else None
                    ),
                    destino_colleita=datos.get("destino_colleita"),
                    destino_restos=datos.get("destino_restos"),
                    notas=datos.get("notas"),
                    data_fin=data_fin_colleita,
                    obten_sementes=bool(datos.get("obten_sementes", False)),
                    obten_plantas=bool(datos.get("obten_plantas", False)),
                    sen_colleita_ambiental=bool(datos.get("sen_colleita_ambiental", False)),
                    restos_no_solo=bool(datos.get("restos_no_solo", False)),
                    maquina_id=datos.get("maquina_id"),
                    num_repeticions=(
                        int(datos["num_repeticions"])
                        if datos.get("num_repeticions") is not None
                        else None
                    ),
                    duracion_h_ha=(
                        float(datos["duracion_h_ha"])
                        if datos.get("duracion_h_ha") is not None
                        else None
                    ),
                    persoa_id=persoa_colleita,
                    horas=(
                        float(datos["horas"])
                        if datos.get("horas") is not None
                        else None
                    ),
                )
                colleita = crear_colleita(session, usuario, datos_colleita)
                colleita.uuid = item_uuid
                session.commit()
                novo_id = colleita.id

            elif tipo == "tarefa_feita":
                if "id" not in datos:
                    raise ValueError("Falta o identificador da tarefa (id)")
                tarefa_id = int(datos["id"])
                tarefa = session.get(Tarefa, tarefa_id)
                if tarefa is None or tarefa.horta_id != horta_id:
                    raise OperacionNonPermitidaError(
                        "A tarefa indicada non pertence a esta explotación"
                    )
                data_feita = (
                    _converter_data(datos["data"], "data")
                    if datos.get("data")
                    else None
                )
                persoa_tarefa = (
                    datos.get("persoa_id")
                    or tarefa.persoa_id
                    or persoa_defecto
                )
                horas_tarefa = (
                    float(datos["horas"])
                    if datos.get("horas") is not None
                    else tarefa.horas
                )

                marcar_feita(
                    session,
                    usuario,
                    tarefa,
                    persoa_id=persoa_tarefa,
                    data=data_feita,
                    horas=horas_tarefa,
                )
                tarefa.uuid = item_uuid
                session.commit()
                novo_id = tarefa.id

            resultados.append({
                "uuid": item_uuid,
                "estado": "creado",
                "id": novo_id,
                "mensaxe": None,
            })

        except (OperacionNonPermitidaError, ValueError) as e:
            session.rollback()
            resultados.append({
                "uuid": item_uuid,
                "estado": "erro",
                "id": None,
                "mensaxe": str(e),
            })
        except IntegrityError:
            session.rollback()
            resultados.append({
                "uuid": item_uuid,
                "estado": "erro",
                "id": None,
                "mensaxe": "Erro de integridade ou duplicado na base de datos",
            })
        except Exception as e:
            session.rollback()
            resultados.append({
                "uuid": item_uuid,
                "estado": "erro",
                "id": None,
                "mensaxe": f"Erro ao procesar o rexistro: {e}",
            })

    return resultados

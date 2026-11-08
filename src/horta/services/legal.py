"""Servizo de cumprimento do RGPD e textos legais."""

from __future__ import annotations

import json
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.legal import ConfiguracionLegal
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError

VERSION_POLITICA = "2026-11-08"

CAMPOS_CONFIGURACION = {
    "nome",
    "nif",
    "enderezo",
    "correo",
    "dpd",
    "localizacion",
}


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só un administrador pode xestionar a configuración legal")


def _formatear_data_politica(version_iso: str) -> str:
    try:
        partes = version_iso.strip().split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
    except Exception:
        pass
    return version_iso


def _ler_ficheiro_legal(cal: str) -> str:
    try:
        from importlib.resources import files

        return files("horta.data.legal").joinpath(f"{cal}.md").read_text(encoding="utf-8")
    except Exception:
        ruta = Path(__file__).resolve().parents[1] / "data" / "legal" / f"{cal}.md"
        return ruta.read_text(encoding="utf-8")


def ler_configuracion(session: Session) -> ConfiguracionLegal | None:
    """Devolve a configuración legal actual, ou None se aínda non se gardou."""
    return session.query(ConfiguracionLegal).first()


def gardar_configuracion(
    session: Session,
    actor: Usuario,
    **campos: Any,
) -> ConfiguracionLegal:
    """Garda ou actualiza os datos do responsable do tratamento (só admin global)."""
    _esixir_admin(actor)
    desconhecidos = set(campos) - CAMPOS_CONFIGURACION
    if desconhecidos:
        raise ValueError(
            f"Campos descoñecidos na configuración legal: {', '.join(sorted(desconhecidos))}"
        )

    config = session.query(ConfiguracionLegal).first()
    if config is None:
        config = ConfiguracionLegal()
        session.add(config)

    for campo, valor in campos.items():
        setattr(config, campo, valor)

    config.actualizado_en = datetime.now(timezone.utc)
    session.commit()
    return config


def texto_legal(session: Session, cal: str) -> str:
    """Xera o texto legal ('aviso' ou 'privacidade') substituíndo os marcadores."""
    if cal not in ("aviso", "privacidade"):
        raise ValueError(f"Texto legal descoñecido: {cal}")

    texto = _ler_ficheiro_legal(cal)
    config = ler_configuracion(session)

    pendente = "(pendente de configurar)"
    nome = config.nome.strip() if config and config.nome and config.nome.strip() else pendente
    nif = config.nif.strip() if config and config.nif and config.nif.strip() else pendente
    enderezo = (
        config.enderezo.strip()
        if config and config.enderezo and config.enderezo.strip()
        else pendente
    )
    correo = (
        config.correo.strip()
        if config and config.correo and config.correo.strip()
        else pendente
    )

    if config and config.dpd and config.dpd.strip():
        dpd = f"- **Delegado de protección de datos:** {config.dpd.strip()}"
    else:
        dpd = ""

    if config and config.localizacion and config.localizacion.strip():
        localizacion = config.localizacion.strip()
    else:
        localizacion = ""

    version = _formatear_data_politica(VERSION_POLITICA)

    substitucions = {
        "{version}": version,
        "{nome}": nome,
        "{nif}": nif,
        "{enderezo}": enderezo,
        "{correo}": correo,
        "{dpd}": dpd,
        "{localizacion}": localizacion,
    }

    for marcador, valor in substitucions.items():
        texto = texto.replace(marcador, valor)

    return texto


def precisa_aceptar(usuario: Usuario) -> bool:
    """Indica se o usuario ten pendente aceptar a versión actual da política."""
    return usuario.politica_version != VERSION_POLITICA


def aceptar_politica(session: Session, actor: Usuario) -> None:
    """Rexistra a aceptación da política de privacidade por parte do usuario."""
    actor.politica_version = VERSION_POLITICA
    actor.politica_aceptada_en = datetime.now(timezone.utc)
    session.add(actor)
    session.commit()


def exportar_meus_datos(session: Session, actor: Usuario) -> bytes:
    """Exporta todos os datos persoais e referencias do usuario en formato JSON UTF-8."""
    conta_info = {
        "nome": actor.nome,
        "email": actor.email,
        "rol": actor.rol.value if hasattr(actor.rol, "value") else str(actor.rol),
        "activo": actor.activo,
        "data_alta": actor.created_at.isoformat() if actor.created_at else None,
        "created_at": actor.created_at.isoformat() if actor.created_at else None,
        "version": actor.politica_version,
        "politica_version": actor.politica_version,
        "data_politica": (
            actor.politica_aceptada_en.isoformat() if actor.politica_aceptada_en else None
        ),
        "politica_aceptada_en": (
            actor.politica_aceptada_en.isoformat() if actor.politica_aceptada_en else None
        ),
    }

    membros = session.query(HortaMembro).filter_by(usuario_id=actor.id).all()
    explotacions_info = []
    for m in membros:
        horta = session.get(Horta, m.horta_id)
        nome_horta = horta.nome if horta else ""
        rol_membro = m.rol.value if hasattr(m.rol, "value") else str(m.rol)
        explotacions_info.append({
            "id": m.horta_id,
            "nome": nome_horta,
            "rol": rol_membro,
        })

    persoas = session.query(Persoa).filter_by(usuario_id=actor.id).all()
    persoas_info = []
    for p in persoas:
        p_dict: dict[str, Any] = {}
        for col in Persoa.__table__.columns:
            val = getattr(p, col.name)
            if isinstance(val, (datetime, date)):
                p_dict[col.name] = val.isoformat()
            elif hasattr(val, "value"):
                p_dict[col.name] = val.value
            else:
                p_dict[col.name] = val
        persoas_info.append(p_dict)

    resultado = {
        "conta": conta_info,
        "explotacions": explotacions_info,
        "persoas": persoas_info,
    }

    return json.dumps(resultado, indent=2, ensure_ascii=False).encode("utf-8")


def borrar_minha_conta(session: Session, actor: Usuario) -> None:
    """Borrado anónimo da conta do usuario conservando a integridade histórica."""
    # 1. Comprobar que non sexa o único admin dunha horta con outros membros
    membros = session.query(HortaMembro).filter_by(usuario_id=actor.id).all()
    for m in membros:
        if m.rol == RolHorta.ADMIN:
            total_membros = session.query(HortaMembro).filter_by(horta_id=m.horta_id).count()
            if total_membros > 1:
                outros_admins = (
                    session.query(HortaMembro)
                    .filter(
                        HortaMembro.horta_id == m.horta_id,
                        HortaMembro.rol == RolHorta.ADMIN,
                        HortaMembro.usuario_id != actor.id,
                    )
                    .count()
                )
                if outros_admins == 0:
                    horta = session.get(Horta, m.horta_id)
                    nome_horta = horta.nome if horta else ""
                    raise OperacionNonPermitidaError(
                        "Antes de borrar a conta, dálle o papel de administrador a outra persoa "
                        f"en {nome_horta}"
                    )

    # 2. Comprobar que non sexa o último admin global activo
    if actor.rol == RolGlobal.ADMIN and actor.activo:
        admins_activos = session.query(Usuario).filter_by(
            rol=RolGlobal.ADMIN, activo=True
        ).count()
        if admins_activos <= 1:
            raise OperacionNonPermitidaError("Non se pode desactivar o último administrador activo")

    # 3. Borrar as súas filas de HortaMembro
    for m in membros:
        session.delete(m)

    # 4. Nas Persoa con usuario_id == actor.id, poñer usuario_id = None
    persoas = session.query(Persoa).filter_by(usuario_id=actor.id).all()
    for persoa in persoas:
        persoa.usuario_id = None

    # 5. Anonimizar o usuario
    actor.nome = "Conta borrada"
    actor.email = f"borrada-{actor.id}@invalido.local"
    actor.password_hash = hash_password(secrets.token_urlsafe(32))
    actor.activo = False

    # 6. Confirmar cambios
    session.commit()

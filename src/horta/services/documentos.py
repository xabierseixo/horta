"""Documentos e certificacións da explotación (paso N2).

Gardar certificados e documentos da explotación ou ligados a un recurso concreto
(parcela, cultivo, animal, máquina, persoa, lote, instalación), con control de
caducidade e avisos aos 30 días. O ficheiro vai a un cartafol por explotación; a
base de datos garda a referencia. Admite PDF, JPEG, PNG e WEBP de ata 20 MB.
Baixa lóxica: o ficheiro non se borra."""

from __future__ import annotations

import os
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.cultivo import Cultivo
from horta.models.documento import Documento
from horta.models.horta import RolHorta
from horta.models.instalacion import Instalacion
from horta.models.lote import Lote
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fotos import extension as foto_extension
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_DOCUMENTO: dict[str, str] = {
    "certificado_calidade": "Certificado de calidade (ecolóxico, GlobalG.A.P., IFS…)",
    "autorizacion": "Autorización ou inscrición",
    "carne_formacion": "Carné ou formación",
    "inspeccion": "Inspección (ITEAF, sanitaria…)",
    "seguro": "Seguro",
    "contrato": "Contrato",
    "analise_externa": "Análise externa",
    "outro": "Outro",
}

REFERENCIAS: dict[str, Any] = {
    "parcela": Parcela,
    "cultivo": Cultivo,
    "animal": Animal,
    "maquina": Maquina,
    "persoa": Persoa,
    "lote": Lote,
    "instalacion": Instalacion,
}

AVISO_DIAS = 30
TAMANO_MAXIMO = 20 * 1024 * 1024

CAMPOS_EDITABLES = frozenset({
    "tipo",
    "nome",
    "emisor",
    "numero",
    "data_emision",
    "data_caducidade",
    "que",
    "ref_id",
    "notas",
})


def cartafol_documentos() -> Path:
    """HORTA_DOCUMENTOS_DIR ou, se non está, ~/.local/share/horta/documentos."""
    return Path(
        os.environ.get("HORTA_DOCUMENTOS_DIR")
        or Path.home() / ".local" / "share" / "horta" / "documentos"
    )


def extension(contido: bytes) -> str | None:
    """pdf (empeza por %PDF), jpg, png ou webp. Para as imaxes reutiliza fotos.extension."""
    if contido.startswith(b"%PDF"):
        return "pdf"
    return foto_extension(contido)


def _horta_de(session: Session, rexistro: Any) -> int | None:
    if hasattr(rexistro, "horta_id"):
        return int(rexistro.horta_id)
    if isinstance(rexistro, Cultivo):
        parcela = session.get(Parcela, rexistro.parcela_id)
        return parcela.horta_id if parcela else None
    return None


def _validar_referencia(
    session: Session, horta_id: int, que: str | None, ref_id: int | None
) -> None:
    if que is None and ref_id is None:
        return
    if que is None or ref_id is None:
        raise OperacionNonPermitidaError("Iso non é desta explotación")
    modelo = REFERENCIAS.get(que)
    if modelo is None:
        raise OperacionNonPermitidaError("Iso non é desta explotación")
    rexistro = session.get(modelo, ref_id)
    if rexistro is None or _horta_de(session, rexistro) != horta_id:
        raise OperacionNonPermitidaError("Iso non é desta explotación")


def crear_documento(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    tipo: str,
    nome: str,
    emisor: str | None = None,
    numero: str | None = None,
    data_emision: date | None = None,
    data_caducidade: date | None = None,
    que: str | None = None,
    ref_id: int | None = None,
    notas: str | None = None,
) -> Documento:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if tipo not in TIPOS_DOCUMENTO:
        raise ValueError(f"Tipo de documento descoñecido: {tipo}")
    if not nome or not nome.strip():
        raise OperacionNonPermitidaError("O nome do documento é obrigatorio")
    _validar_referencia(session, horta_id, que, ref_id)
    if data_emision and data_caducidade and data_caducidade < data_emision:
        raise OperacionNonPermitidaError(
            "A data de caducidade non pode ser anterior á de emisión"
        )

    doc = Documento(
        horta_id=horta_id,
        tipo=tipo,
        nome=nome.strip(),
        emisor=emisor.strip() if emisor and emisor.strip() else None,
        numero=numero.strip() if numero and numero.strip() else None,
        data_emision=data_emision,
        data_caducidade=data_caducidade,
        que=que,
        ref_id=ref_id,
        notas=notas.strip() if notas and notas.strip() else None,
        creado_por=actor.id,
    )
    session.add(doc)
    session.commit()
    return doc


def actualizar_documento(
    session: Session,
    actor: Usuario,
    documento: Documento,
    **campos: Any,
) -> Documento:
    non_editables = set(campos) - CAMPOS_EDITABLES
    if non_editables:
        raise ValueError(
            f"Campos non editables nun documento: {', '.join(sorted(non_editables))}"
        )
    comprobar_rol_horta(session, documento.horta_id, actor, _ROLES_ESCRITURA)

    if "tipo" in campos:
        tipo = campos["tipo"]
        if tipo not in TIPOS_DOCUMENTO:
            raise ValueError(f"Tipo de documento descoñecido: {tipo}")

    if "nome" in campos:
        nome = campos["nome"]
        if not nome or not str(nome).strip():
            raise OperacionNonPermitidaError("O nome do documento é obrigatorio")

    que = campos["que"] if "que" in campos else documento.que
    ref_id = campos["ref_id"] if "ref_id" in campos else documento.ref_id
    _validar_referencia(session, documento.horta_id, que, ref_id)

    emision = (
        campos["data_emision"] if "data_emision" in campos else documento.data_emision
    )
    caducidade = (
        campos["data_caducidade"] if "data_caducidade" in campos else documento.data_caducidade
    )
    if emision and caducidade and caducidade < emision:
        raise OperacionNonPermitidaError(
            "A data de caducidade non pode ser anterior á de emisión"
        )

    for campo, valor in campos.items():
        if campo == "nome" and isinstance(valor, str):
            setattr(documento, campo, valor.strip())
        elif campo in ("emisor", "numero", "notas") and isinstance(valor, str):
            setattr(documento, campo, valor.strip() if valor.strip() else None)
        else:
            setattr(documento, campo, valor)

    session.commit()
    return documento


def gardar_ficheiro(
    session: Session,
    actor: Usuario,
    documento: Documento,
    contido: bytes,
    nome_orixinal: str | None = None,
) -> Documento:
    comprobar_rol_horta(session, documento.horta_id, actor, _ROLES_ESCRITURA)
    if len(contido) > TAMANO_MAXIMO:
        raise OperacionNonPermitidaError("O documento ocupa máis de 20 MB")
    ext = extension(contido)
    if ext is None:
        raise OperacionNonPermitidaError("Só se admiten PDF ou imaxes JPEG, PNG ou WEBP")

    ficheiro = f"{uuid.uuid4().hex}.{ext}"
    destino = cartafol_documentos() / str(documento.horta_id)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / ficheiro).write_bytes(contido)

    documento.ficheiro = ficheiro
    documento.nome_orixinal = (
        nome_orixinal.strip()[:200] if nome_orixinal and nome_orixinal.strip() else None
    )
    session.commit()
    return documento


def ficheiro_do_documento(session: Session, actor: Usuario, documento_id: int) -> Path:
    documento = session.get(Documento, documento_id)
    if documento is None or documento.baixa:
        raise OperacionNonPermitidaError("Ese documento non existe")
    comprobar_rol_horta(session, documento.horta_id, actor, _ROLES_LECTURA)
    if not documento.ficheiro:
        raise OperacionNonPermitidaError("O documento non ten ningún ficheiro adxunto")
    return cartafol_documentos() / str(documento.horta_id) / documento.ficheiro


def dar_de_baixa_documento(session: Session, actor: Usuario, documento: Documento) -> None:
    comprobar_rol_horta(session, documento.horta_id, actor, _ROLES_ESCRITURA)
    documento.baixa = True
    session.commit()


def listar_documentos(
    session: Session,
    actor: Usuario,
    horta_id: int,
    que: str | None = None,
    ref_id: int | None = None,
) -> list[Documento]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    query = session.query(Documento).filter_by(horta_id=horta_id, baixa=False)
    if que is not None and ref_id is not None:
        query = query.filter_by(que=que, ref_id=ref_id)
    return list(
        query.order_by(
            Documento.data_caducidade.asc().nulls_last(),
            Documento.nome.asc(),
        ).all()
    )


def estado_documento(documento: Documento, hoxe: date) -> str:
    """Calcula o estado dun documento respecto a unha data:
    - caducado: se data_caducidade < hoxe
    - caduca_pronto: se caduca nos próximos AVISO_DIAS días (incluído hoxe)
    - vixente: noutro caso, tamén se non ten data de caducidade
    """
    if documento.data_caducidade is None:
        return "vixente"
    if documento.data_caducidade < hoxe:
        return "caducado"
    if documento.data_caducidade <= hoxe + timedelta(days=AVISO_DIAS):
        return "caduca_pronto"
    return "vixente"


def documentos_con_aviso(
    session: Session,
    actor: Usuario,
    horta_id: int,
    hoxe: date | None = None,
) -> list[Documento]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    dia = hoxe or date.today()
    return [
        doc
        for doc in listar_documentos(session, actor, horta_id)
        if estado_documento(doc, dia) in ("caducado", "caduca_pronto")
    ]

"""Fotos (paso 11a): dunha foto ou desde o móbil, en calquera traballo do Diario, parcela,
animal ou lote. O ficheiro vai a un cartafol por explotación; a BD garda a referencia. Só
imaxes JPEG, PNG ou WEBP de ata 10 MB. Baixa lóxica: o ficheiro non se borra."""

from __future__ import annotations

import os
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from horta.models.abonado import Abonado
from horta.models.analise import Analise
from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.foto import Foto
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.lote import Clasificacion, Lote, LoteSaida, Mestura, Transformacion
from horta.models.movemento_animal import MovementoAnimal
from horta.models.observacion import ObservacionPraga
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela
from horta.models.pastoreo import Pastoreo
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.models.tratamento_instalacion import TratamentoInstalacion
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
TAMANO_MAXIMO = 10 * 1024 * 1024
# A que pode ir unha foto: os tipos do Diario, as parcelas, os animais e os lotes
MODELOS: dict[str, Any] = {
    "tratamento": TratamentoFito, "abonado": Abonado, "rega": Rega, "labor": Labor,
    "colleita": Colleita, "sementeira": Cultivo, "analise": Analise,
    "tratamento_instalacion": TratamentoInstalacion, "coidado_animal": CoidadoAnimal,
    "movemento_animal": MovementoAnimal, "producion_animal": ProducionAnimal,
    "pastoreo": Pastoreo, "lote_saida": LoteSaida,
    "clasificacion": Clasificacion, "mestura": Mestura,
    "transformacion": Transformacion, "entrada_produto": EntradaProduto,
    "outro_traballo": OutroTraballo, "tarefa": Tarefa,
    "parcela": Parcela, "animal": Animal, "lote": Lote,
    "observacion": ObservacionPraga,
}


def cartafol_fotos() -> Path:
    """HORTA_FOTOS_DIR ou, se non, ~/.local/share/horta/fotos."""
    return Path(os.environ.get("HORTA_FOTOS_DIR")
                or Path.home() / ".local" / "share" / "horta" / "fotos")


def extension(contido: bytes) -> str | None:
    """O tipo da imaxe polos seus primeiros bytes (non polo nome do ficheiro)."""
    if contido.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if contido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contido[:4] == b"RIFF" and contido[8:12] == b"WEBP":
        return "webp"
    return None


def _horta_de(session: Session, rexistro: Any) -> int | None:
    if hasattr(rexistro, "horta_id"):
        return int(rexistro.horta_id)
    if isinstance(rexistro, Colleita):
        rexistro = session.get(Cultivo, rexistro.cultivo_id)
    parcela = session.get(Parcela, rexistro.parcela_id) if rexistro is not None else None
    return parcela.horta_id if parcela else None


def gardar_foto(session: Session, actor: Usuario, horta_id: int, que: str, ref_id: int,
                contido: bytes, nome_orixinal: str | None = None, nota: str | None = None,
                hoxe: date | None = None) -> Foto:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    modelo = MODELOS.get(que)
    rexistro = session.get(modelo, ref_id) if modelo is not None else None
    if rexistro is None or _horta_de(session, rexistro) != horta_id:
        raise OperacionNonPermitidaError("Iso non é desta explotación")
    if len(contido) > TAMANO_MAXIMO:
        raise OperacionNonPermitidaError("A foto ocupa máis de 10 MB")
    ext = extension(contido)
    if ext is None:
        raise OperacionNonPermitidaError("Só se admiten fotos JPEG, PNG ou WEBP")
    ficheiro = f"{uuid.uuid4().hex}.{ext}"
    destino = cartafol_fotos() / str(horta_id)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / ficheiro).write_bytes(contido)
    foto = Foto(horta_id=horta_id, que=que, ref_id=ref_id, ficheiro=ficheiro,
                nome_orixinal=(nome_orixinal or None) and nome_orixinal[:200],
                data=hoxe or date.today(), nota=(nota or None) and nota[:300],
                creado_por=actor.id)
    session.add(foto)
    session.commit()
    return foto


def listar_fotos(session: Session, actor: Usuario, horta_id: int, que: str, ref_id: int
                 ) -> list[Foto]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Foto).filter_by(horta_id=horta_id, que=que, ref_id=ref_id,
                                              baixa=False).order_by(Foto.id))


def contar_fotos(session: Session, actor: Usuario, horta_id: int
                 ) -> dict[tuple[str, int], int]:
    """Cantas fotos ten cada cousa, para marcalo nas listas."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return {(que, ref_id): n for que, ref_id, n in session.query(
        Foto.que, Foto.ref_id, func.count()).filter_by(horta_id=horta_id, baixa=False)
        .group_by(Foto.que, Foto.ref_id)}


def dar_de_baixa_foto(session: Session, actor: Usuario, foto: Foto) -> None:
    comprobar_rol_horta(session, foto.horta_id, actor, _ROLES_ESCRITURA)
    foto.baixa = True
    session.commit()


def ficheiro_da_foto(session: Session, actor: Usuario, foto_id: int) -> Path:
    """A ruta do ficheiro, se quen a pide pode ver esa explotación."""
    foto = session.get(Foto, foto_id)
    if foto is None or foto.baixa:
        raise OperacionNonPermitidaError("Esa foto non existe")
    comprobar_rol_horta(session, foto.horta_id, actor, _ROLES_LECTURA)
    return cartafol_fotos() / str(foto.horta_id) / foto.ficheiro

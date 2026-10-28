from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.persoa import Persoa, PersoaPapel
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Patrón oficial do descritor SIEX (Anexo VI, folla "Patrones texto") para NIF de persoa física.
_PATRON_NIF = re.compile(r"^[KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$")
# NIF dunha entidade (CIF): letra da forma xurídica, 7 díxitos e control (díxito ou letra)
_PATRON_CIF = re.compile(r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$")
_PATRON_REXISTRO = re.compile(r"^ES\d{12}$")

TIPOS_PERSOA = {"persoa": "Persoa", "entidade": "Empresa ou entidade"}
# Papeis. Os do equipo saen
# na pestana Equipo; o resto, en Contactos. Unha persoa pode ter varios.
PAPEIS_EQUIPO: dict[str, str] = {
    "titular": "Titular",
    "representante": "Representante",
    "traballador": "Traballa na explotación",
    "aplicador": "Aplica fitosanitarios",
    "asesor": "Asesor",
}
PAPEIS_CONTACTO: dict[str, str] = {
    "cliente": "Cliente",
    "provedor": "Provedor",
    "veterinario": "Veterinario",
    "laboratorio": "Laboratorio",
    "servizos": "Empresa de servizos",
    "explotacion": "Outra explotación",
}
PAPEIS: dict[str, str] = PAPEIS_EQUIPO | PAPEIS_CONTACTO
# Quen pode facer un traballo: o equipo ou unha empresa de servizos
PAPEIS_QUEN = (*PAPEIS_EQUIPO, "servizos")

CAMPOS_EDITABLES_PERSOA = frozenset(
    {"tipo", "nome", "apelidos", "nif", "ropo_numero", "ropo_tipo_carne", "ropo_caducidade",
     "regfer_numero", "activa", "telefono", "email", "vinculo", "horas_ano",
     "formacion_agraria", "xenero", "data_nacemento", "discapacidade", "enderezo",
     "localidade", "codigo_postal", "provincia", "concello_codigo", "pais", "rega", "reaga",
     "nima", "ropveg", "rexistro_dixital", "num_asesoramento"}
)


VINCULOS = ("titular", "familiar", "asalariado", "socio", "externo")
XENEROS = ("muller", "home", "outro")


def _normalizar_e_validar(datos: dict[str, Any], papeis: set[str]) -> None:
    if datos.get("tipo", "persoa") not in TIPOS_PERSOA:
        raise OperacionNonPermitidaError("Indica se é unha persoa ou unha entidade")
    if not papeis <= set(PAPEIS):
        raise OperacionNonPermitidaError(f"Papel descoñecido: {', '.join(papeis - set(PAPEIS))}")
    entidade = datos.get("tipo") == "entidade"
    if datos.get("nif"):
        datos["nif"] = datos["nif"].strip().upper().replace("-", "").replace(" ", "")
        if not (_PATRON_CIF if entidade else _PATRON_NIF).match(datos["nif"]):
            raise OperacionNonPermitidaError("O NIF non é válido")
    for campo, nome in (("rega", "REGA"), ("reaga", "REAGA")):
        if datos.get(campo):
            datos[campo] = datos[campo].strip().upper().replace(" ", "")
            if not _PATRON_REXISTRO.match(datos[campo]):
                raise OperacionNonPermitidaError(
                    f"O código {nome} debe ter o formato ES seguido de 12 díxitos")
    if "aplicador" in papeis and not (datos.get("ropo_numero") and datos.get("ropo_caducidade")):
        raise OperacionNonPermitidaError(
            "Un aplicador precisa o nº ROPO e a data de caducidade do carné"
        )
    # A entidade de asesoramento (caderno 1.4) non ten ROPO: leva o seu nº de asesoramento
    if "asesor" in papeis and not entidade and not datos.get("ropo_numero"):
        raise OperacionNonPermitidaError("Un asesor precisa o nº ROPO")
    if datos.get("vinculo") not in (None, *VINCULOS):
        raise OperacionNonPermitidaError(f"Vínculo non válido: {datos['vinculo']}")
    if datos.get("horas_ano") is not None and not 0 <= datos["horas_ano"] <= 4000:
        raise OperacionNonPermitidaError("As horas ao ano teñen que estar entre 0 e 4.000")
    if datos.get("xenero") not in (None, *XENEROS):
        raise OperacionNonPermitidaError(f"Xénero non válido: {datos['xenero']}")
    if datos.get("data_nacemento") is not None and datos["data_nacemento"] > date.today():
        raise OperacionNonPermitidaError("A data de nacemento non pode ser futura")


def _un_so_titular(session: Session, horta_id: int, papeis: set[str], activa: bool,
                   excepto_id: int | None) -> None:
    if "titular" not in papeis or not activa:
        return
    outra = (session.query(Persoa).join(PersoaPapel)
             .filter(Persoa.horta_id == horta_id, Persoa.activa.is_(True),
                     PersoaPapel.papel == "titular", Persoa.id != (excepto_id or 0))
             .first())
    if outra is not None:
        raise OperacionNonPermitidaError(
            f"A explotación xa ten titular ({outra.nome}): quítalle antes ese papel")


def _gardar_papeis(persoa: Persoa, papeis: set[str]) -> None:
    persoa.papeis_rexistro = [p for p in persoa.papeis_rexistro if p.papel in papeis] + [
        PersoaPapel(papel=papel) for papel in sorted(papeis - persoa.papeis)]


def crear_persoa(
    session: Session, actor: Usuario, horta_id: int, nome: str,
    papeis: set[str] | frozenset[str] | tuple[str, ...] = (), **campos: Any
) -> Persoa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not nome.strip():
        raise OperacionNonPermitidaError("Indica o nome")
    _normalizar_e_validar(campos, set(papeis))
    _un_so_titular(session, horta_id, set(papeis), campos.get("activa", True), None)
    persoa = Persoa(horta_id=horta_id, nome=nome.strip(), **campos)
    _gardar_papeis(persoa, set(papeis))
    session.add(persoa)
    session.commit()
    return persoa


def actualizar_persoa(
    session: Session, actor: Usuario, persoa: Persoa,
    papeis: set[str] | frozenset[str] | tuple[str, ...] | None = None, **cambios: Any
) -> Persoa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_PERSOA
    if non_editables:
        raise ValueError(f"Campos non editables nunha persoa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, persoa.horta_id, actor, _ROLES_ESCRITURA)
    novos_papeis = persoa.papeis if papeis is None else set(papeis)
    resultado = {c: getattr(persoa, c) for c in CAMPOS_EDITABLES_PERSOA} | cambios
    _normalizar_e_validar(resultado, novos_papeis)
    _un_so_titular(session, persoa.horta_id, novos_papeis, resultado["activa"], persoa.id)
    for campo in cambios:
        setattr(persoa, campo, resultado[campo])
    _gardar_papeis(persoa, novos_papeis)
    session.commit()
    return persoa


def crear_contacto(
    session: Session, actor: Usuario, horta_id: int, nome: str, papel: str | None,
    **campos: Any
) -> Persoa:
    """Crear unha persoa dende un formulario de traballo (botón «Nova»), xa co papel que fai
    alí. Se xa hai unha co mesmo NIF, ou co mesmo nome se non se dá NIF, úsase esa."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    nif = (campos.get("nif") or "").strip().upper()
    existente = (consulta.filter_by(nif=nif).first() if nif else
                 next((p for p in consulta if p.nome.strip().lower() == nome.strip().lower()),
                      None))
    if existente is not None:
        return persoa_co_papel(session, horta_id, existente.id, papel, gardar=True) or existente
    return crear_persoa(session, actor, horta_id, nome, papeis={papel} if papel else set(),
                        **campos)


def persoa_co_papel(session: Session, horta_id: int, persoa_id: int | None,
                    papel: str | None, gardar: bool = False) -> Persoa | None:
    """A persoa escollida nun traballo ten que ser desta explotación; queda co papel que fai
    (p.ex. quen merca pasa a ser cliente). None se non se escolleu ningunha."""
    if persoa_id is None:
        return None
    persoa = session.get(Persoa, persoa_id)
    if persoa is None or persoa.horta_id != horta_id:
        raise OperacionNonPermitidaError("A persoa ou entidade indicada non é desta explotación")
    if papel is not None and papel not in persoa.papeis:
        persoa.papeis_rexistro.append(PersoaPapel(papel=papel))
        if gardar:
            session.commit()
    return persoa


def con_papel(session: Session, horta_id: int, papel: str) -> list[Persoa]:
    """As persoas activas da explotación con ese papel."""
    return list(session.query(Persoa).join(PersoaPapel)
                .filter(Persoa.horta_id == horta_id, Persoa.activa.is_(True),
                        PersoaPapel.papel == papel)
                .order_by(Persoa.nome))


def titular_da_horta(session: Session, horta_id: int) -> Persoa | None:
    return next(iter(con_papel(session, horta_id, "titular")), None)


def nome_completo(persoa: Persoa | None) -> str:
    if persoa is None:
        return ""
    return " ".join(x for x in (persoa.nome, persoa.apelidos or "") if x)


def listar_persoas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True,
    papel: str | None = None,
) -> list[Persoa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    if papel is not None:
        consulta = consulta.join(PersoaPapel).filter(PersoaPapel.papel == papel)
    return list(consulta.order_by(Persoa.nome).all())


def listar_quen(session: Session, actor: Usuario, horta_id: int) -> list[Persoa]:
    """As persoas activas que poden facer un traballo («Quen o fixo»): o equipo e as
    empresas de servizos. Os clientes, provedores, laboratorios... non."""
    return [p for p in listar_persoas(session, actor, horta_id) if p.ten_papel(*PAPEIS_QUEN)]


def ropo_vixente(persoa: Persoa, na_data: date) -> bool:
    return persoa.ropo_caducidade is not None and persoa.ropo_caducidade >= na_data


def comprobar_quen(
    session: Session, horta_id: int, persoa_id: int | None, horas: float | None,
    obrigatoria: bool = True,
) -> None:
    """Todo traballo o fai unha persoa: tense que indicar e ten que ser desta explotación.
    As horas son opcionais."""
    if persoa_id is None:
        if obrigatoria:
            raise OperacionNonPermitidaError("Indica quen o fixo")
    else:
        persoa = session.get(Persoa, persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("A persoa indicada non é desta explotación")
    if horas is not None and horas <= 0:
        raise OperacionNonPermitidaError("As horas teñen que ser máis de 0")

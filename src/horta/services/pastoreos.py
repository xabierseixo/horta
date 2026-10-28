"""Pastoreo (CUE bloque 12): o gando, propio ou de terceiros, nunha ou máis leiras entre dúas
datas. Avisa se unha leira ten un tratamento co prazo de seguridade sen rematar. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.movemento_animal import MovementoAnimal
from horta.models.parcela import Parcela
from horta.models.pastoreo import Pastoreo, PastoreoAnimal, PastoreoLeira
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_consulta import prazo_seguridade
from horta.services.hortas import comprobar_rol_horta
from horta.services.movementos_animais import SUMAN
from horta.services.persoas import comprobar_quen, persoa_co_papel

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# As abellas (catálogo ESPECIE_ANIMAL) non pastan
NON_PASTAN = ("18",)


@dataclass
class LeiraPastoreo:
    cultivo_id: int
    superficie_ha: float | None = None
    tipo_cobertura: str | None = None


@dataclass
class AnimaisPastoreo:
    numero: int
    # Propios: o grupo. Doutra persoa: a súa explotación (persoa co REGA) e a especie
    animal_id: int | None = None
    propietario_id: int | None = None
    especie_codigo: str | None = None


@dataclass
class DatosPastoreo:
    horta_id: int
    data_inicio: date
    persoa_id: int | None
    data_fin: date | None = None
    leiras: list[LeiraPastoreo] = field(default_factory=list)
    animais: list[AnimaisPastoreo] = field(default_factory=list)
    horas: float | None = None
    notas: str | None = None


def animais_no_dia(session: Session, animal_id: int, dia: date) -> int:
    """Cantos animais tiña o grupo ese día, segundo as súas entradas e saídas."""
    total = 0
    for mov in session.query(MovementoAnimal).filter(
            MovementoAnimal.animal_id == animal_id, MovementoAnimal.baixa.is_(False),
            MovementoAnimal.data <= dia):
        total += mov.cantidade if mov.tipo in SUMAN else -mov.cantidade
    return total


def _no_pasto_a_vez(session: Session, animal_id: int, inicio: date, fin: date | None,
                    excepto_id: int | None) -> int:
    """Animais do grupo noutros pastoreos que coinciden nas datas."""
    total = 0
    for linha, pastoreo in (session.query(PastoreoAnimal, Pastoreo)
                           .join(Pastoreo, PastoreoAnimal.pastoreo_id == Pastoreo.id)
                           .filter(PastoreoAnimal.animal_id == animal_id,
                                   Pastoreo.baixa.is_(False))):
        if pastoreo.id == excepto_id:
            continue
        if ((fin is None or pastoreo.data_inicio <= fin)
                and (pastoreo.data_fin is None or pastoreo.data_fin >= inicio)):
            total += linha.numero
    return total


def _validar_leira(session: Session, datos: DatosPastoreo, leira: LeiraPastoreo) -> None:
    cultivo = session.get(Cultivo, leira.cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None or parcela.horta_id != datos.horta_id:
        raise OperacionNonPermitidaError("Esa leira non é desta explotación")
    if cultivo.data_inicio is not None and datos.data_inicio < cultivo.data_inicio:
        raise OperacionNonPermitidaError(
            f"{cultivo.especie} empezou o {cultivo.data_inicio:%d/%m/%Y}: o pastoreo non pode "
            "ser antes")
    if cultivo.data_fin is not None and datos.data_inicio > cultivo.data_fin:
        raise OperacionNonPermitidaError(
            f"{cultivo.especie} rematou o {cultivo.data_fin:%d/%m/%Y}")
    if leira.superficie_ha is not None:
        if leira.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and leira.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError(
                f"A superficie pastada é maior ca a de {cultivo.especie}")
    if leira.tipo_cobertura:
        validar_codigo(session, "tipo_cobertura_solo", leira.tipo_cobertura, datos.data_inicio)


def _validar_animais(session: Session, datos: DatosPastoreo, linha: AnimaisPastoreo,
                     excepto_id: int | None) -> None:
    if linha.numero is None or linha.numero < 1:
        raise OperacionNonPermitidaError("Indica cantos animais (polo menos 1)")
    if linha.animal_id is None:
        if not linha.especie_codigo or linha.especie_codigo in NON_PASTAN:
            raise OperacionNonPermitidaError("Escolle a especie dos animais")
        validar_codigo(session, "especie_animal", linha.especie_codigo, datos.data_inicio)
        propietario = persoa_co_papel(session, datos.horta_id, linha.propietario_id,
                                      "explotacion")
        if propietario is None:
            raise OperacionNonPermitidaError("Indica de quen son os animais")
        if not propietario.rega:
            raise OperacionNonPermitidaError(
                f"Os animais doutra persoa levan o seu REGA: complétao na ficha de "
                f"{propietario.nome}")
        return
    animal = session.get(Animal, linha.animal_id)
    if animal is None or animal.horta_id != datos.horta_id:
        raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")
    if animal.especie_codigo in NON_PASTAN:
        raise OperacionNonPermitidaError("Ese grupo non pode ir ao pasto")
    if datos.data_inicio < animal.data_alta:
        raise OperacionNonPermitidaError(
            f"O grupo deuse de alta o {animal.data_alta:%d/%m/%Y}: a data non pode ser anterior")
    hai = animais_no_dia(session, animal.id, datos.data_inicio)
    if linha.numero > hai:
        raise OperacionNonPermitidaError(
            f"{animal.especie} tiña {hai} animais o {datos.data_inicio:%d/%m/%Y}")
    outros = _no_pasto_a_vez(session, animal.id, datos.data_inicio, datos.data_fin, excepto_id)
    if outros and linha.numero + outros > hai:
        raise OperacionNonPermitidaError(
            f"{animal.especie}: {outros} animais xa están noutro pasto nesas datas")


def _validar(session: Session, datos: DatosPastoreo, hoxe: date,
             excepto_id: int | None) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data_fin is not None:
        if datos.data_fin < datos.data_inicio:
            raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
        if datos.data_fin > hoxe:
            raise OperacionNonPermitidaError("A data de fin non pode ser futura")
    if not datos.leiras:
        raise OperacionNonPermitidaError("Escolle polo menos unha leira")
    if not datos.animais:
        raise OperacionNonPermitidaError("Indica os animais que foron ao pasto")
    for leira in datos.leiras:
        _validar_leira(session, datos, leira)
    for linha in datos.animais:
        _validar_animais(session, datos, linha, excepto_id)
    comprobar_quen(session, datos.horta_id, datos.persoa_id, datos.horas)


def _copiar(session: Session, pastoreo: Pastoreo, datos: DatosPastoreo) -> None:
    pastoreo.horta_id = datos.horta_id
    pastoreo.data_inicio = datos.data_inicio
    pastoreo.data_fin = datos.data_fin
    pastoreo.persoa_id = datos.persoa_id
    pastoreo.horas = datos.horas
    pastoreo.notas = datos.notas or None
    leiras = []
    for leira in datos.leiras:
        cultivo = session.get(Cultivo, leira.cultivo_id)
        assert cultivo is not None
        leiras.append(PastoreoLeira(
            cultivo_id=leira.cultivo_id,
            superficie_ha=leira.superficie_ha or cultivo.superficie_ha,
            tipo_cobertura=leira.tipo_cobertura or cultivo.tipo_cobertura_solo))
    pastoreo.leiras = leiras
    pastoreo.animais = [
        PastoreoAnimal(animal_id=linha.animal_id, numero=linha.numero,
                       propietario_id=None if linha.animal_id else linha.propietario_id,
                       especie_codigo=None if linha.animal_id else linha.especie_codigo)
        for linha in datos.animais]


def crear_pastoreo(
    session: Session, actor: Usuario, datos: DatosPastoreo, hoxe: date | None = None
) -> Pastoreo:
    comprobar_rol_horta(session, datos.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today(), None)
    pastoreo = Pastoreo(creado_por=actor.id)
    _copiar(session, pastoreo, datos)
    session.add(pastoreo)
    session.commit()
    return pastoreo


def actualizar_pastoreo(
    session: Session, actor: Usuario, pastoreo: Pastoreo, datos: DatosPastoreo,
    hoxe: date | None = None,
) -> Pastoreo:
    if pastoreo.baixa:
        raise OperacionNonPermitidaError("Un pastoreo dado de baixa non se pode modificar")
    comprobar_rol_horta(session, pastoreo.horta_id, actor, _ROLES_ESCRITURA)
    if datos.horta_id != pastoreo.horta_id:
        raise OperacionNonPermitidaError("Ese pastoreo non é desta explotación")
    _validar(session, datos, hoxe or date.today(), pastoreo.id)
    _copiar(session, pastoreo, datos)
    session.commit()
    return pastoreo


def sairon_do_pasto(
    session: Session, actor: Usuario, pastoreo: Pastoreo, data_fin: date,
    hoxe: date | None = None,
) -> Pastoreo:
    """Pecha o pastoreo coa data en que o gando saíu."""
    comprobar_rol_horta(session, pastoreo.horta_id, actor, _ROLES_ESCRITURA)
    if pastoreo.baixa:
        raise OperacionNonPermitidaError("Un pastoreo dado de baixa non se pode modificar")
    if data_fin < pastoreo.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if data_fin > (hoxe or date.today()):
        raise OperacionNonPermitidaError("A data de fin non pode ser futura")
    pastoreo.data_fin = data_fin
    session.commit()
    return pastoreo


def dar_de_baixa_pastoreo(session: Session, actor: Usuario, pastoreo: Pastoreo) -> None:
    comprobar_rol_horta(session, pastoreo.horta_id, actor, _ROLES_ESCRITURA)
    pastoreo.baixa = True
    session.commit()


def listar_pastoreos(
    session: Session, actor: Usuario, horta_id: int, animal_id: int | None = None
) -> list[Pastoreo]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Pastoreo).filter_by(horta_id=horta_id, baixa=False)
    if animal_id is not None:
        consulta = consulta.filter(Pastoreo.animais.any(PastoreoAnimal.animal_id == animal_id))
    return list(consulta.order_by(Pastoreo.data_inicio.desc(), Pastoreo.id.desc()))


def no_pasto(session: Session, actor: Usuario, horta_id: int) -> dict[int, Pastoreo]:
    """Os grupos que están agora no pasto (pastoreo sen data de fin) e o seu pastoreo."""
    grupos: dict[int, Pastoreo] = {}
    for pastoreo in listar_pastoreos(session, actor, horta_id):
        if pastoreo.data_fin is None:
            for linha in pastoreo.animais:
                if linha.animal_id is not None:
                    grupos.setdefault(linha.animal_id, pastoreo)
    return grupos


def nomes_leiras(session: Session, pastoreo: Pastoreo) -> str:
    """As leiras (parcelas) do pastoreo, para as listas."""
    nomes = []
    for leira in pastoreo.leiras:
        cultivo = session.get(Cultivo, leira.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if parcela is not None and parcela.nome not in nomes:
            nomes.append(parcela.nome)
    return ", ".join(nomes)


def ten_pastoreo(session: Session, animal_id: int) -> bool:
    return session.query(PastoreoAnimal).filter_by(animal_id=animal_id).first() is not None


def cultivo_ten_pastoreo(session: Session, cultivo_id: int) -> bool:
    return session.query(PastoreoLeira).filter_by(cultivo_id=cultivo_id).first() is not None


def aviso_prazo_pastoreo(session: Session, cultivo_ids: list[int], data: date) -> str | None:
    """Aviso se o gando entra antes de que remate o prazo de seguridade dalgún tratamento."""
    tratamentos = (session.query(TratamentoFito)
                   .join(TratamentoCultivo, TratamentoCultivo.tratamento_id == TratamentoFito.id)
                   .filter(TratamentoFito.baixa.is_(False),
                           TratamentoCultivo.cultivo_id.in_(cultivo_ids),
                           TratamentoFito.data_fin <= data)
                   .order_by(TratamentoFito.data_fin))
    for t in tratamentos:
        prazo = prazo_seguridade(session, t)
        if prazo is not None and data < prazo:
            produtos = ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
            return (f"Ollo: o tratamento do {t.data_fin:%d/%m/%Y} ({produtos}) ten prazo de "
                    f"seguridade: non se debería meter o gando antes do {prazo:%d/%m/%Y}.")
    return None

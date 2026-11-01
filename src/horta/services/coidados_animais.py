"""Coidado e saúde dos animais: o libro de rexistro gandeiro (RD 787/2023 anexo V 6, 7 e 11)
e os medicamentos veterinarios (Reg. UE 2019/6 art. 108). Un grupo de animais por rexistro.
Baixa lóxica (gárdanse 3 e 5 anos)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.horta import RolHorta
from horta.models.maquina import Maquina
from horta.models.produto import Produto
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen, persoa_co_papel
from horta.services.produtos import comprobar_entrada_do_produto, produto_ou_novo

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_COIDADO: dict[str, str] = {
    "coidado": "Coidado (comida, auga, limpeza…)",
    "enfermidade": "Enfermidade",
    "producion": "Cambio na produción",
    "medicamento": "Medicamento",
    "visita": "Visita ou vehículo",
}
# Os tipos onde se anotan os animais afectados ou tratados
CON_ANIMAIS = ("enfermidade", "producion", "medicamento")
UNIDADES_MEDICAMENTO = ("ml", "L", "g", "kg", "unidades")
_UNIDADE_DO_PRODUTO = {"litros": "L", "kg": "kg", "unidades": "unidades"}
_PRODUTO_DA_UNIDADE = {"ml": "litros", "L": "litros", "g": "kg", "kg": "kg",
                       "unidades": "unidades"}


def unidade_do_medicamento(session: Session, produto_id: int | None) -> str | None:
    """A unidade de medicamento que lle corresponde á unidade na que se conta o produto."""
    produto = session.get(Produto, produto_id) if produto_id is not None else None
    return _UNIDADE_DO_PRODUTO.get(produto.unidade) if produto else None


@dataclass
class DatosCoidado:
    animal_id: int
    data_inicio: date
    tipo: str
    persoa_id: int | None
    descricion: str | None = None
    data_fin: date | None = None
    num_animais: int | None = None
    identificacion: str | None = None
    # O medicamento: o produto (ou o seu nome, e créase) e de que compra saíu, se se sabe.
    # O provedor e a proba de compra van na compra (entrada do produto)
    medicamento: str | None = None
    produto_id: int | None = None
    entrada_id: int | None = None
    cantidade: float | None = None
    unidade: str | None = None
    veterinario_id: int | None = None
    receita: str | None = None
    tempo_espera_dias: int | None = None
    duracion_dias: int | None = None
    visitante_id: int | None = None
    matricula: str | None = None
    horas: float | None = None
    maquina_id: int | None = None
    notas: str | None = None


def _animal(session: Session, animal_id: int) -> Animal:
    animal = session.get(Animal, animal_id)
    if animal is None:
        raise OperacionNonPermitidaError("Ese grupo de animais non existe")
    return animal


def _validar(
    session: Session, datos: DatosCoidado, animal: Animal, hoxe: date,
    unidade_actual: str | None = None,
) -> None:
    if datos.tipo not in TIPOS_COIDADO:
        raise OperacionNonPermitidaError("Escolle que se fixo")
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if animal.data_baixa is not None and datos.data_inicio > animal.data_baixa:
        raise OperacionNonPermitidaError("Ese grupo de animais xa estaba de baixa nesa data")
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
    if datos.maquina_id is not None:
        maquina = session.get(Maquina, datos.maquina_id)
        if maquina is None or maquina.horta_id != animal.horta_id:
            raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")
    if datos.num_animais is not None:
        if datos.num_animais < 1:
            raise OperacionNonPermitidaError("O número de animais ten que ser polo menos 1")
        if datos.num_animais > animal.cantidade:
            raise OperacionNonPermitidaError(
                f"O grupo só ten {animal.cantidade} animais")
    if datos.tipo == "medicamento":
        if not datos.medicamento and datos.produto_id is None:
            raise OperacionNonPermitidaError("Indica o medicamento")
        if datos.tempo_espera_dias is None:
            raise OperacionNonPermitidaError(
                "Indica o tempo de espera (0 se o medicamento non ten)")
        if datos.cantidade is not None and datos.cantidade <= 0:
            raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
        if datos.unidade and datos.unidade not in UNIDADES_MEDICAMENTO and (
                datos.unidade != unidade_actual):
            raise OperacionNonPermitidaError(f"Unidade non válida: {datos.unidade}")
        persoa_co_papel(session, animal.horta_id, datos.veterinario_id, "veterinario")
    elif datos.tipo == "visita":
        if datos.visitante_id is None:
            raise OperacionNonPermitidaError("Indica quen veu")
        persoa_co_papel(session, animal.horta_id, datos.visitante_id, None)
    elif not datos.descricion:
        raise OperacionNonPermitidaError("Describe que se fixo ou que se viu")
    for valor in (datos.tempo_espera_dias, datos.duracion_dias):
        if valor is not None and valor < 0:
            raise OperacionNonPermitidaError("Os días non poden ser negativos")


def _copiar(coidado: CoidadoAnimal, datos: DatosCoidado, animal: Animal) -> None:
    medicamento = datos.tipo == "medicamento"
    visita = datos.tipo == "visita"
    coidado.horta_id = animal.horta_id
    coidado.animal_id = animal.id
    coidado.data_inicio = datos.data_inicio
    coidado.data_fin = datos.data_fin or datos.data_inicio
    coidado.tipo = datos.tipo
    coidado.descricion = datos.descricion or None
    # Cada tipo garda só os seus datos
    con_animais = datos.tipo in CON_ANIMAIS
    coidado.num_animais = datos.num_animais if con_animais else None
    coidado.identificacion = (datos.identificacion or None) if con_animais else None
    coidado.produto_id = datos.produto_id if medicamento else None
    coidado.entrada_id = datos.entrada_id if medicamento else None
    coidado.cantidade = datos.cantidade if medicamento else None
    coidado.unidade = (datos.unidade or None) if medicamento else None
    coidado.veterinario_id = datos.veterinario_id if medicamento else None
    coidado.receita = (datos.receita or None) if medicamento else None
    coidado.tempo_espera_dias = datos.tempo_espera_dias if medicamento else None
    coidado.duracion_dias = datos.duracion_dias if medicamento else None
    coidado.visitante_id = datos.visitante_id if visita else None
    coidado.matricula = (datos.matricula or None) if visita else None
    coidado.persoa_id = datos.persoa_id
    coidado.horas = datos.horas
    coidado.maquina_id = datos.maquina_id
    coidado.notas = datos.notas or None


def _medicamento(session: Session, actor: Usuario, datos: DatosCoidado, horta_id: int) -> None:
    """O medicamento é un produto da explotación: o escollido, ou o do nome (créase)."""
    if datos.tipo != "medicamento":
        return
    if datos.produto_id is None:
        unidade = _PRODUTO_DA_UNIDADE.get(datos.unidade or "", "unidades")
        datos.produto_id = produto_ou_novo(session, actor, horta_id, "medicamento",
                                           datos.medicamento or "", unidade).id
    produto = session.get(Produto, datos.produto_id)
    if produto is None or produto.horta_id != horta_id or produto.tipo != "medicamento":
        raise OperacionNonPermitidaError("Ese medicamento non é desta explotación")
    comprobar_entrada_do_produto(session, horta_id, datos.entrada_id, produto.id)


def crear_coidado(
    session: Session, actor: Usuario, datos: DatosCoidado, hoxe: date | None = None
) -> CoidadoAnimal:
    animal = _animal(session, datos.animal_id)
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, animal, hoxe or date.today())
    _medicamento(session, actor, datos, animal.horta_id)
    coidado = CoidadoAnimal(creado_por=actor.id)
    _copiar(coidado, datos, animal)
    session.add(coidado)
    session.commit()
    return coidado


def actualizar_coidado(
    session: Session, actor: Usuario, coidado: CoidadoAnimal, datos: DatosCoidado,
    hoxe: date | None = None,
) -> CoidadoAnimal:
    if coidado.baixa:
        raise OperacionNonPermitidaError("Un coidado dado de baixa non se pode modificar")
    comprobar_rol_horta(session, coidado.horta_id, actor, _ROLES_ESCRITURA)
    animal = _animal(session, datos.animal_id)
    if animal.horta_id != coidado.horta_id:
        raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")
    _validar(session, datos, animal, hoxe or date.today(), coidado.unidade)
    _medicamento(session, actor, datos, animal.horta_id)
    _copiar(coidado, datos, animal)
    session.commit()
    return coidado


def dar_de_baixa_coidado(session: Session, actor: Usuario, coidado: CoidadoAnimal) -> None:
    comprobar_rol_horta(session, coidado.horta_id, actor, _ROLES_ESCRITURA)
    coidado.baixa = True
    session.commit()


def listar_coidados(
    session: Session, actor: Usuario, horta_id: int, animal_id: int | None = None
) -> list[CoidadoAnimal]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(CoidadoAnimal).filter_by(horta_id=horta_id, baixa=False)
    if animal_id is not None:
        consulta = consulta.filter_by(animal_id=animal_id)
    return list(consulta.order_by(CoidadoAnimal.data_inicio.desc(), CoidadoAnimal.id.desc()))


def fin_tempo_espera(coidado: CoidadoAnimal) -> date | None:
    """Ata que día (incluído) non se poden usar os produtos dos animais tratados. A
    última administración é a data de fin ou, se non a ten, o inicio máis a duración."""
    if coidado.tipo != "medicamento" or coidado.tempo_espera_dias is None:
        return None
    ultima = coidado.data_fin
    if coidado.duracion_dias and ultima == coidado.data_inicio:
        ultima = coidado.data_inicio + timedelta(days=coidado.duracion_dias - 1)
    return ultima + timedelta(days=coidado.tempo_espera_dias)


def en_tempo_espera(
    session: Session, actor: Usuario, horta_id: int, hoxe: date | None = None
) -> dict[int, date]:
    """Os grupos de animais que hoxe están en tempo de espera e ata que día."""
    hoxe = hoxe or date.today()
    grupos: dict[int, date] = {}
    for coidado in listar_coidados(session, actor, horta_id):
        fin = fin_tempo_espera(coidado)
        if fin is not None and fin >= hoxe:
            grupos[coidado.animal_id] = max(fin, grupos.get(coidado.animal_id, fin))
    return grupos


def ten_coidados(session: Session, animal_id: int) -> bool:
    return session.query(CoidadoAnimal).filter_by(animal_id=animal_id).first() is not None

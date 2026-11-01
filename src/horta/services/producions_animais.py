"""Produción dos animais (ovos, leite, mel...) de cada grupo, co seu lote, como as colleitas dos
cultivos (README §7). Avisa se o grupo está en tempo de espera dun medicamento. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.producion_animal import ProducionAnimal
from horta.models.usuario import Usuario
from horta.services.coidados_animais import fin_tempo_espera, listar_coidados
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import (
    codigo_por_agrupacion,
    comprobar_entrada,
    ficha_para,
    lote_para_entrada,
)
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

PRODUTOS: dict[str, str] = {
    "ovos": "Ovos",
    "leite": "Leite",
    "mel": "Mel",
    "cera": "Cera",
    "la": "La",
    "outro": "Outro",
}
# Unidade que se propón para cada produto
UNIDADE_PRODUTO = {"ovos": "unidades", "leite": "litros", "mel": "kg", "cera": "kg",
                   "la": "kg", "outro": "kg"}
UNIDADES_PRODUCION = ("unidades", "ducias", "litros", "kg")
# Os produtos de cada especie (códigos do catálogo ESPECIE_ANIMAL); «outro», en todas
_ESPECIES_DO_PRODUTO = {
    "ovos": ("06", "07", "08", "09", "10", "11", "15"),
    "leite": ("01", "03", "04", "05"),
    "mel": ("18",),
    "cera": ("18",),
    "la": ("03",),
}


@dataclass
class DatosProducion:
    animal_id: int
    data: date
    produto: str
    cantidade: float
    unidade: str
    persoa_id: int | None
    lote: str = ""
    data_fin: date | None = None
    retirada: float | None = None
    horas: float | None = None
    notas: str | None = None
    maquina_id: int | None = None


def produtos_da_especie(especie_codigo: str | None) -> dict[str, str]:
    """Os produtos que dá unha especie. Sen especie (grupos de antes), todos."""
    return {clave: nome for clave, nome in PRODUTOS.items()
            if especie_codigo is None or clave == "outro"
            or especie_codigo in _ESPECIES_DO_PRODUTO[clave]}


def _animal(session: Session, animal_id: int) -> Animal:
    animal = session.get(Animal, animal_id)
    if animal is None:
        raise OperacionNonPermitidaError("Ese grupo de animais non existe")
    return animal


def propor_lote(session: Session, actor: Usuario, horta_id: int, produto: str,
                data: date) -> str:
    """Primeiro lote libre do tipo AAAA-PRODUTO-NNN (p.ex. 2026-OVOS-001)."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    ficha = ficha_para(session, horta_id, PRODUTOS.get(produto, "Outro"),
                       UNIDADE_PRODUTO.get(produto, "kg"), produto_animal=produto, crear=False)
    return codigo_por_agrupacion(session, ficha, data)


def _validar(session: Session, datos: DatosProducion, animal: Animal, hoxe: date,
             excepto_id: int | None) -> None:
    if datos.produto not in produtos_da_especie(animal.especie_codigo):
        raise OperacionNonPermitidaError("Ese produto non o dá esta especie")
    if datos.unidade not in UNIDADES_PRODUCION:
        raise OperacionNonPermitidaError(f"Unidade non válida: {datos.unidade}")
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    if datos.retirada is not None and not 0 <= datos.retirada <= datos.cantidade:
        raise OperacionNonPermitidaError("O retirado non pode ser máis ca o producido")
    fin = datos.data_fin or datos.data
    if fin < datos.data:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if fin > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data < animal.data_alta:
        raise OperacionNonPermitidaError(
            f"O grupo deuse de alta o {animal.data_alta:%d/%m/%Y}: a data non pode ser anterior")
    if animal.data_baixa is not None and fin > animal.data_baixa:
        raise OperacionNonPermitidaError(
            f"O grupo quedou sen animais o {animal.data_baixa:%d/%m/%Y}")
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, animal.horta_id, datos.maquina_id)


def _copiar(pr: ProducionAnimal, datos: DatosProducion, animal: Animal) -> None:
    pr.horta_id = animal.horta_id
    pr.animal_id = animal.id
    pr.data = datos.data
    pr.data_fin = datos.data_fin or datos.data
    pr.produto = datos.produto
    pr.cantidade = datos.cantidade
    pr.unidade = datos.unidade
    pr.retirada = datos.retirada or None
    pr.persoa_id = datos.persoa_id
    pr.horas = datos.horas
    pr.maquina_id = datos.maquina_id
    pr.notas = datos.notas or None


def _lote(session: Session, datos: DatosProducion, animal: Animal) -> int:
    """O lote onde entra (o producido menos o retirado): o do código, se é o mesmo produto,
    ou un novo."""
    return lote_para_entrada(session, animal.horta_id, datos.lote, PRODUTOS[datos.produto],
                             datos.unidade, datos.data, produto_animal=datos.produto).id


def _neto(cantidade: float, retirada: float | None) -> float:
    return cantidade - (retirada or 0)


def crear_producion(
    session: Session, actor: Usuario, datos: DatosProducion, hoxe: date | None = None
) -> ProducionAnimal:
    animal = _animal(session, datos.animal_id)
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, animal.horta_id, datos.produto, datos.data)
    _validar(session, datos, animal, hoxe or date.today(), None)
    pr = ProducionAnimal(creado_por=actor.id, lote_id=_lote(session, datos, animal))
    _copiar(pr, datos, animal)
    session.add(pr)
    session.commit()
    return pr


def actualizar_producion(
    session: Session, actor: Usuario, pr: ProducionAnimal, datos: DatosProducion,
    hoxe: date | None = None,
) -> ProducionAnimal:
    if pr.baixa:
        raise OperacionNonPermitidaError("Unha produción dada de baixa non se pode modificar")
    comprobar_rol_horta(session, pr.horta_id, actor, _ROLES_ESCRITURA)
    animal = _animal(session, datos.animal_id)
    if animal.horta_id != pr.horta_id:
        raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")
    _validar(session, datos, animal, hoxe or date.today(), pr.id)
    lote_id = _lote(session, datos, animal)
    # O lote de antes non pode quedar con menos do que xa saíu del
    comprobar_entrada(session, pr.lote_id, _neto(pr.cantidade, pr.retirada), pr.unidade,
                      _neto(datos.cantidade, datos.retirada) if lote_id == pr.lote_id else 0,
                      datos.unidade)
    pr.lote_id = lote_id
    _copiar(pr, datos, animal)
    session.commit()
    return pr


def dar_de_baixa_producion(session: Session, actor: Usuario, pr: ProducionAnimal) -> None:
    comprobar_rol_horta(session, pr.horta_id, actor, _ROLES_ESCRITURA)
    comprobar_entrada(session, pr.lote_id, _neto(pr.cantidade, pr.retirada), pr.unidade, 0)
    pr.baixa = True
    session.commit()


def listar_producions(
    session: Session, actor: Usuario, horta_id: int, animal_id: int | None = None
) -> list[ProducionAnimal]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(ProducionAnimal).filter_by(horta_id=horta_id, baixa=False)
    if animal_id is not None:
        consulta = consulta.filter_by(animal_id=animal_id)
    return list(consulta.order_by(ProducionAnimal.data.desc(), ProducionAnimal.id.desc()))


def ten_producion(session: Session, animal_id: int) -> bool:
    return session.query(ProducionAnimal).filter_by(animal_id=animal_id).first() is not None


def aviso_tempo_espera(
    session: Session, actor: Usuario, horta_id: int, animal_id: int | None,
    data: date | None, data_fin: date | None = None,
) -> str | None:
    """Avisa (sen bloquear) se o produto saíu mentres o grupo estaba en tempo de espera."""
    if animal_id is None or data is None:
        return None
    fin_periodo = data_fin or data
    ata: date | None = None
    for coidado in listar_coidados(session, actor, horta_id):
        fin = fin_tempo_espera(coidado)
        if (coidado.animal_id == animal_id and fin is not None
                and coidado.data_inicio <= fin_periodo and fin >= data):
            ata = max(fin, ata or fin)
    if ata is None:
        return None
    return (f"Este grupo está en tempo de espera ata o {ata:%d/%m/%Y}: este produto non se "
            "pode vender nin comer")

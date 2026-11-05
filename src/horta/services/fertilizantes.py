"""Os meus abonos: cada explotación garda os seus abonos unha vez e escólleos ao abonar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.fertilizante import FertilizanteSiex
from horta.models.horta import RolHorta
from horta.models.produto import Produto
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo MAT_FERTI: estercos (o 9 son inhibidores) e residuos, que piden provedor (CUE 9)
ESTERCOS = {"1", "2", "3", "4", "5", "6", "7", "8", "10"}
RESIDUOS = {"18", "19", "20", "21", "22", "23"}
# Unidades de dose (catálogo UNIDADES_MEDIDA) -> kg/ha; os líquidos precisan a densidade
_MASA_A_KG_HA = {"17": 1.0, "29": 1000.0, "49": 0.001, "60": 10000.0, "80": 10.0}
_VOLUME_A_L_HA = {"18": 1.0, "19": 1000.0, "59": 10000.0}
UNIDADES_DOSE = (*_MASA_A_KG_HA, *_VOLUME_A_L_HA)
FORMAS_N_P = ("n_organico_pct", "n_ureico_pct", "n_nitrico_pct", "n_amoniacal_pct",
              "p2o5_soluble_pct")
METAIS_RESIDUO = ("cadmio", "cobre", "niquel", "chumbo", "zinc", "mercurio", "cromo_vi",
                  "arsenico", "cromo")


@dataclass
class DatosFertilizante:
    nome: str
    material: str
    fertilizante_siex_codigo: int | None = None
    n_pct: float | None = None
    p2o5_pct: float | None = None
    k2o_pct: float | None = None
    n_organico_pct: float | None = None
    n_ureico_pct: float | None = None
    n_nitrico_pct: float | None = None
    n_amoniacal_pct: float | None = None
    p2o5_soluble_pct: float | None = None
    materia_organica_pct: float | None = None
    cadmio: float | None = None
    cobre: float | None = None
    niquel: float | None = None
    chumbo: float | None = None
    zinc: float | None = None
    mercurio: float | None = None
    cromo_vi: float | None = None
    arsenico: float | None = None
    cromo: float | None = None
    liquido: bool = False
    densidade: float | None = None
    tratamento_estercos: str | None = None


def _validar(session: Session, horta_id: int, datos: DatosFertilizante) -> None:
    hoxe = date.today()
    if not datos.nome.strip():
        raise OperacionNonPermitidaError("Pon un nome ao abono")
    validar_codigo(session, "material_fertilizante", datos.material, hoxe)
    for riqueza in (datos.n_pct, datos.p2o5_pct, datos.k2o_pct, *(
            getattr(datos, c) for c in FORMAS_N_P), datos.materia_organica_pct):
        if riqueza is not None and not 0 <= riqueza <= 100:
            raise OperacionNonPermitidaError("A riqueza ten que estar entre 0 e 100 %")
    if any(getattr(datos, m) is not None and getattr(datos, m) < 0 for m in METAIS_RESIDUO):
        raise OperacionNonPermitidaError("Os metais pesados non poden ser negativos")
    if datos.densidade is not None and datos.densidade <= 0:
        raise OperacionNonPermitidaError("A densidade ten que ser maior que 0")
    if datos.tratamento_estercos:
        if datos.material not in ESTERCOS:
            raise OperacionNonPermitidaError("O tratamento só se indica nos estercos")
        validar_codigo(session, "tratamento_estercos", datos.tratamento_estercos, hoxe)


def crear_fertilizante(
    session: Session, actor: Usuario, horta_id: int, datos: DatosFertilizante
) -> Fertilizante:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, horta_id, datos)
    nome = datos.nome.strip()
    if session.query(Fertilizante).filter_by(horta_id=horta_id, nome=nome).first():
        raise OperacionNonPermitidaError(f"Xa tes un abono chamado {nome}")
    fertilizante = Fertilizante(horta_id=horta_id, **{**vars(datos), "nome": nome})
    session.add(fertilizante)
    session.flush()
    # O abono é un produto da explotación: as súas compras (e o provedor) son entradas
    session.add(Produto(horta_id=horta_id, tipo="abono", nome=nome,
                        unidade="litros" if datos.liquido else "kg",
                        fertilizante_id=fertilizante.id))
    session.commit()
    return fertilizante


def actualizar_fertilizante(
    session: Session, actor: Usuario, fertilizante: Fertilizante, datos: DatosFertilizante
) -> Fertilizante:
    """Corrixe un abono xa dado de alta (Z4) e o seu produto (nome e unidade)."""
    from horta.services.produtos import produto_do_abono, ten_movementos

    comprobar_rol_horta(session, fertilizante.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, fertilizante.horta_id, datos)
    nome = datos.nome.strip()
    if (session.query(Fertilizante)
            .filter(Fertilizante.horta_id == fertilizante.horta_id, Fertilizante.nome == nome,
                    Fertilizante.id != fertilizante.id).first()):
        raise OperacionNonPermitidaError(f"Xa tes un abono chamado {nome}")
    produto = produto_do_abono(session, fertilizante)
    unidade = "litros" if datos.liquido else "kg"
    if unidade != produto.unidade and ten_movementos(session, produto):
        raise OperacionNonPermitidaError(
            "Este abono xa ten compras ou usos: non se pode cambiar se é líquido ou sólido")
    for campo, valor in vars(datos).items():
        setattr(fertilizante, campo, valor)
    fertilizante.nome = nome
    produto.nome, produto.unidade = nome, unidade
    session.commit()
    return fertilizante


def retirar_fertilizante(session: Session, actor: Usuario, fertilizante: Fertilizante) -> None:
    """Deixa de ofrecelo ao abonar; os abonados de antes consérvanse (Z4)."""
    comprobar_rol_horta(session, fertilizante.horta_id, actor, _ROLES_ESCRITURA)
    fertilizante.activo = False
    session.commit()


def listar_fertilizantes(
    session: Session, actor: Usuario, horta_id: int, incluir_inactivos: bool = False
) -> list[Fertilizante]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Fertilizante).filter_by(horta_id=horta_id)
    if not incluir_inactivos:
        consulta = consulta.filter(Fertilizante.activo.is_(True))
    return list(consulta.order_by(Fertilizante.nome))


def datos_desde_siex(session: Session, codigo: int) -> DatosFertilizante:
    """Enche un abono novo cos datos do catálogo oficial (nome, material e riqueza)."""
    oficial = session.get(FertilizanteSiex, codigo)
    if oficial is None or oficial.data_baixa is not None:
        raise OperacionNonPermitidaError("Ese produto non está no catálogo oficial")
    return DatosFertilizante(
        nome=oficial.nome, material=oficial.material, fertilizante_siex_codigo=codigo,
        n_pct=oficial.n_pct, p2o5_pct=oficial.p2o5_pct, k2o_pct=oficial.k2o_pct,
        **{c: getattr(oficial, c) or None for c in FORMAS_N_P},
        liquido=oficial.liquido, densidade=oficial.densidade,
    )


def opcions_siex(session: Session) -> dict[int, str]:
    """Produtos do catálogo oficial vixentes, para escoller ao crear un abono."""
    consulta = session.query(FertilizanteSiex).filter(FertilizanteSiex.data_baixa.is_(None))
    return {f.codigo: f.nome for f in consulta.order_by(FertilizanteSiex.nome)}


def dose_kg_ha(dose: float, unidade: str, densidade: float | None) -> float | None:
    """Dose en kg/ha; None se é un líquido sen densidade coñecida ou a unidade non é de dose."""
    if unidade in _MASA_A_KG_HA:
        return dose * _MASA_A_KG_HA[unidade]
    if unidade in _VOLUME_A_L_HA and densidade:
        return dose * _VOLUME_A_L_HA[unidade] * densidade
    return None


def cantidade_gastada(dose: float, unidade: str, superficie_ha: float, en_litros: bool,
                      densidade: float | None) -> tuple[float, str] | None:
    """Canto abono se gastou, en litros se o produto se conta en litros (G3) ou en kg."""
    if en_litros:
        if unidade in _VOLUME_A_L_HA:
            return dose * _VOLUME_A_L_HA[unidade] * superficie_ha, "litros"
        if unidade in _MASA_A_KG_HA and densidade:
            return dose * _MASA_A_KG_HA[unidade] * superficie_ha / densidade, "litros"
        return None
    kg_ha = dose_kg_ha(dose, unidade, densidade)
    return (kg_ha * superficie_ha, "kg") if kg_ha is not None else None


def nutrientes_kg_ha(
    fertilizante: Fertilizante, dose: float, unidade: str
) -> tuple[float, float, float] | None:
    """kg/ha de N, P₂O₅ e K₂O que leva unha dose; None se non se pode calcular."""
    kg_ha = dose_kg_ha(dose, unidade, fertilizante.densidade)
    if kg_ha is None:
        return None
    n, p, k = (fertilizante.n_pct or 0, fertilizante.p2o5_pct or 0, fertilizante.k2o_pct or 0)
    return round(kg_ha * n / 100, 1), round(kg_ha * p / 100, 1), round(kg_ha * k / 100, 1)

"""Movementos de esterco e purín: cesións e recepcións (RD 1051/2022)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from horta.models.esterco import MovementoEsterco
from horta.models.horta import Horta, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.animais import ESPECIES
from horta.services.catalogos import describir, validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import ESTERCOS
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen, nome_completo, titular_da_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_MOVEMENTO = {"cesion", "recepcion"}
UNIDADES = {"t", "m3"}

ORIXES_COMPOSICION: dict[str, str] = {
    "analise": "Análise de laboratorio",
    "programa": "Programa de cálculo recoñecido",
    "condutivimetro": "Condutivímetro (purín)",
}

CAMPOS_EDITABLES_MOVEMENTO = frozenset({
    "tipo",
    "data",
    "outra_parte_id",
    "outra_parte_rega",
    "tipo_explotacion",
    "tipo_animais",
    "material",
    "cantidade",
    "unidade",
    "n_total",
    "p2o5",
    "k2o",
    "materia_organica",
    "orixe_composicion",
    "parcelas_destino",
    "notas",
    "persoa_id",
    "horas",
})


def _validar_movemento(
    session: Session,
    horta_id: int,
    tipo: str,
    data: date,
    outra_parte_id: int,
    tipo_explotacion: str,
    tipo_animais: str,
    material: str,
    cantidade: float,
    unidade: str,
    n_total: float | None,
    p2o5: float | None,
    k2o: float | None,
    materia_organica: float | None,
    orixe_composicion: str | None,
    persoa_id: int | None,
    horas: float | None,
) -> None:
    if tipo not in TIPOS_MOVEMENTO:
        raise OperacionNonPermitidaError(
            f"O tipo de movemento ten que ser 'cesion' ou 'recepcion', non {tipo!r}"
        )
    if cantidade is None or cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    if unidade not in UNIDADES:
        raise OperacionNonPermitidaError(f"A unidade ten que ser 't' ou 'm3', non {unidade!r}")

    persoa = session.get(Persoa, outra_parte_id)
    if persoa is None or persoa.horta_id != horta_id:
        raise OperacionNonPermitidaError("A outra parte ten que ser unha persoa da explotación")

    if material not in ESTERCOS:
        raise OperacionNonPermitidaError("O material ten que ser un esterco ou purín")
    validar_codigo(session, "material_fertilizante", material, data)

    if tipo_animais not in ESPECIES and tipo_animais not in ESPECIES.values():
        raise OperacionNonPermitidaError("O tipo de animais ten que ser unha especie da lista")
    if not tipo_explotacion or not str(tipo_explotacion).strip():
        raise OperacionNonPermitidaError("Indica o tipo de explotación")

    for nome_campo, val in (
        ("N total", n_total),
        ("P₂O₅", p2o5),
        ("K₂O", k2o),
        ("Materia orgánica", materia_organica),
    ):
        if val is not None and not (0 <= val <= 100):
            raise OperacionNonPermitidaError(
                f"A porcentaxe de {nome_campo} ten que estar entre 0 e 100 %"
            )

    if tipo == "cesion":
        if n_total is None:
            raise OperacionNonPermitidaError(
                "Nunha cesión o contido de N total é obrigatorio (RD 1051/2022 anexo VII)"
            )
        if not orixe_composicion or orixe_composicion not in ORIXES_COMPOSICION:
            raise OperacionNonPermitidaError(
                "Nunha cesión a orixe da composición é obrigatoria (RD 1051/2022 anexo VII)"
            )
    elif orixe_composicion is not None and orixe_composicion not in ORIXES_COMPOSICION:
        raise OperacionNonPermitidaError("A orixe da composición indicada non é válida")

    comprobar_quen(session, horta_id, persoa_id, horas, obrigatoria=False)


def crear_movemento(
    session: Session,
    actor: Usuario,
    horta_id: int,
    tipo: str,
    data: date,
    outra_parte_id: int,
    tipo_explotacion: str,
    tipo_animais: str,
    material: str,
    cantidade: float,
    unidade: str,
    *,
    outra_parte_rega: str | None = None,
    n_total: float | None = None,
    p2o5: float | None = None,
    k2o: float | None = None,
    materia_organica: float | None = None,
    orixe_composicion: str | None = None,
    parcelas_destino: str | None = None,
    notas: str | None = None,
    persoa_id: int | None = None,
    horas: float | None = None,
    **kwargs: Any,
) -> MovementoEsterco:
    """Rexistra un novo movemento (cesión ou recepción) de esterco ou purín."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_movemento(
        session,
        horta_id,
        tipo,
        data,
        outra_parte_id,
        tipo_explotacion,
        tipo_animais,
        material,
        cantidade,
        unidade,
        n_total,
        p2o5,
        k2o,
        materia_organica,
        orixe_composicion,
        persoa_id,
        horas,
    )
    mov = MovementoEsterco(
        horta_id=horta_id,
        tipo=tipo,
        data=data,
        outra_parte_id=outra_parte_id,
        outra_parte_rega=outra_parte_rega.strip() if outra_parte_rega else None,
        tipo_explotacion=tipo_explotacion.strip(),
        tipo_animais=tipo_animais,
        material=material,
        cantidade=float(cantidade),
        unidade=unidade,
        n_total=n_total,
        p2o5=p2o5,
        k2o=k2o,
        materia_organica=materia_organica,
        orixe_composicion=orixe_composicion,
        parcelas_destino=parcelas_destino.strip() if parcelas_destino else None,
        notas=notas.strip() if notas and notas.strip() else None,
        persoa_id=persoa_id,
        horas=horas,
        creado_por=actor.id,
    )
    session.add(mov)
    session.commit()
    return mov


def actualizar_movemento(
    session: Session,
    actor: Usuario,
    movemento: MovementoEsterco,
    **cambios: Any,
) -> MovementoEsterco:
    """Actualiza os datos dun movemento de esterco vixente."""
    if movemento.baixa:
        raise OperacionNonPermitidaError("Un movemento dado de baixa non se pode modificar")
    comprobar_rol_horta(session, movemento.horta_id, actor, _ROLES_ESCRITURA)

    non_editables = set(cambios) - CAMPOS_EDITABLES_MOVEMENTO
    if non_editables:
        raise ValueError(
            f"Campos non editables nun movemento: {', '.join(sorted(non_editables))}"
        )

    tipo = cambios.get("tipo", movemento.tipo)
    data = cambios.get("data", movemento.data)
    outra_parte_id = cambios.get("outra_parte_id", movemento.outra_parte_id)
    tipo_explotacion = cambios.get("tipo_explotacion", movemento.tipo_explotacion)
    tipo_animais = cambios.get("tipo_animais", movemento.tipo_animais)
    material = cambios.get("material", movemento.material)
    cantidade = cambios.get("cantidade", movemento.cantidade)
    unidade = cambios.get("unidade", movemento.unidade)
    n_total = cambios.get("n_total", movemento.n_total)
    p2o5 = cambios.get("p2o5", movemento.p2o5)
    k2o = cambios.get("k2o", movemento.k2o)
    materia_organica = cambios.get("materia_organica", movemento.materia_organica)
    orixe_composicion = cambios.get("orixe_composicion", movemento.orixe_composicion)
    persoa_id = cambios.get("persoa_id", movemento.persoa_id)
    horas = cambios.get("horas", movemento.horas)

    _validar_movemento(
        session,
        movemento.horta_id,
        tipo,
        data,
        outra_parte_id,
        tipo_explotacion,
        tipo_animais,
        material,
        cantidade,
        unidade,
        n_total,
        p2o5,
        k2o,
        materia_organica,
        orixe_composicion,
        persoa_id,
        horas,
    )

    for campo, valor in cambios.items():
        if campo in ("outra_parte_rega", "tipo_explotacion", "parcelas_destino", "notas"):
            setattr(movemento, campo, valor.strip() if valor and str(valor).strip() else None)
        else:
            setattr(movemento, campo, valor)

    session.commit()
    return movemento


def dar_de_baixa_movemento(
    session: Session,
    actor: Usuario,
    movemento: MovementoEsterco,
) -> None:
    """Dá de baixa lóxica un movemento de esterco."""
    comprobar_rol_horta(session, movemento.horta_id, actor, _ROLES_ESCRITURA)
    movemento.baixa = True
    session.commit()


def listar_movementos(
    session: Session,
    actor: Usuario,
    horta_id: int,
    ano: int | None = None,
    tipo: str | None = None,
) -> list[MovementoEsterco]:
    """Lista movementos de esterco vixentes, das máis novas ás máis vellas."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(MovementoEsterco).filter(
        MovementoEsterco.horta_id == horta_id,
        MovementoEsterco.baixa.is_(False),
    )
    if ano is not None:
        desde = date(ano, 1, 1)
        ata = date(ano, 12, 31)
        consulta = consulta.filter(MovementoEsterco.data >= desde, MovementoEsterco.data <= ata)
    if tipo is not None:
        consulta = consulta.filter(MovementoEsterco.tipo == tipo)
    return list(
        consulta.order_by(MovementoEsterco.data.desc(), MovementoEsterco.id.desc()).all()
    )


def faltas_documento(mov: MovementoEsterco) -> list[str]:
    """Comproba os datos do anexo VII punto 1 do RD 1051/2022 que faltan nun movemento."""
    faltas: list[str] = []
    if not getattr(mov, "tipo_explotacion", None):
        faltas.append("Tipo de explotación")
    if not getattr(mov, "tipo_animais", None):
        faltas.append("Tipo de animais")
    cantidade = getattr(mov, "cantidade", None)
    if cantidade is None or cantidade <= 0:
        faltas.append("Cantidade")
    if getattr(mov, "n_total", None) is None:
        faltas.append("Nitróxeno total (N)")
    if getattr(mov, "p2o5", None) is None:
        faltas.append("Fósforo (P₂O₅)")
    if getattr(mov, "k2o", None) is None:
        faltas.append("Potasio (K₂O)")
    if getattr(mov, "materia_organica", None) is None:
        faltas.append("Materia orgánica")
    if not getattr(mov, "orixe_composicion", None):
        faltas.append("Orixe da composición")
    return faltas


class TotaisDict(dict):
    """Dicionario con acceso por tupla (material, unidade) ou por material."""

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, tuple):
            return super().__getitem__(key)
        sub = {uni: val for (mat, uni), val in self.items() if mat == key}
        if sub:
            return sub
        return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def por_material(self) -> dict[str, dict[str, float]]:
        res: dict[str, dict[str, float]] = defaultdict(dict)
        for (mat, uni), val in self.items():
            res[mat][uni] = val
        return dict(res)


@dataclass
class ResumoEsterco:
    """Resumo anual de estercos e puríns: totais e balance de nitróxeno."""

    ano: int
    cedidos: TotaisDict = field(default_factory=TotaisDict)
    recibidos: TotaisDict = field(default_factory=TotaisDict)
    kg_n_cedido: float = 0.0
    kg_n_recibido: float = 0.0
    aviso_m3: bool = False
    nota_m3: str = "Para o cálculo do N con unidade en m³, considérase 1 t = 1 m³."

    @property
    def totais_cedidos(self) -> TotaisDict:
        return self.cedidos

    @property
    def totais_recibidos(self) -> TotaisDict:
        return self.recibidos

    @property
    def total_n_cedido(self) -> float:
        return self.kg_n_cedido

    @property
    def total_n_recibido(self) -> float:
        return self.kg_n_recibido

    @property
    def n_cedido(self) -> float:
        return self.kg_n_cedido

    @property
    def n_recibido(self) -> float:
        return self.kg_n_recibido


def documento_anexo_vii(
    session: Session,
    actor: Usuario,
    movemento_id: int,
) -> bytes:
    """Xera o documento de acompañamento en Excel (RD 1051/2022, anexo VII punto 1).

    Só é aplicable a cesións de esterco ou purín cara a outra explotación ou xestor.
    """
    mov = session.get(MovementoEsterco, movemento_id)
    if mov is None or mov.baixa:
        raise OperacionNonPermitidaError("Movemento de esterco non atopado")

    comprobar_rol_horta(session, mov.horta_id, actor, _ROLES_LECTURA)

    if mov.tipo != "cesion":
        raise OperacionNonPermitidaError(
            "O documento de acompañamento do anexo VII só se pode xerar para cesións"
        )

    horta = session.get(Horta, mov.horta_id)
    assert horta is not None

    titular = titular_da_horta(session, horta.id)
    outra_parte = mov.outra_parte or session.get(Persoa, mov.outra_parte_id)

    # Enderezo do cedente
    end_cedente_partes = [
        horta.enderezo,
        horta.localidade,
        horta.codigo_postal,
        horta.provincia,
    ]
    if not any(end_cedente_partes) and titular:
        end_cedente_partes = [
            titular.enderezo,
            titular.localidade,
            titular.codigo_postal,
            titular.provincia,
        ]
    end_cedente = ", ".join(p for p in end_cedente_partes if p)

    # Identificacións do cedente
    rega_cedente = horta.codigo_rega or (titular.rega if titular else None) or ""
    nima_cedente = (titular.nima if titular else None) or ""
    nif_titular = (titular.nif if titular else None) or ""
    nome_titular = nome_completo(titular) or horta.nome

    # Identificacións do destinatario
    nome_recibe = nome_completo(outra_parte)
    nif_recibe = (outra_parte.nif if outra_parte else None) or ""
    end_recibe_partes = [
        outra_parte.enderezo if outra_parte else None,
        outra_parte.localidade if outra_parte else None,
        outra_parte.codigo_postal if outra_parte else None,
        outra_parte.provincia if outra_parte else None,
    ]
    end_recibe = ", ".join(p for p in end_recibe_partes if p)
    rega_recibe = (
        mov.outra_parte_rega
        or ((outra_parte.rega or outra_parte.nima) if outra_parte else None)
        or ""
    )

    # Datos do produto
    especie_desc = ESPECIES.get(mov.tipo_animais, mov.tipo_animais)
    material_desc = describir(session, "material_fertilizante", mov.material) or mov.material
    orixe_desc = ORIXES_COMPOSICION.get(
        mov.orixe_composicion or "", mov.orixe_composicion or ""
    )

    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Anexo VII"

    filas: list[list[Any]] = [
        ["Documento de acompañamento do esterco (RD 1051/2022, anexo VII)"],
        [],
        ["1. DATOS DE QUEN CEDE (ORIXE)"],
        ["Explotación de orixe", horta.nome],
        ["Titular", nome_titular],
        ["NIF do titular", nif_titular],
        ["Enderezo", end_cedente],
        ["Código REGA", rega_cedente],
        ["Código NIMA", nima_cedente],
        [],
        ["2. DATOS DE QUEN RECIBE (DESTINO)"],
        ["Destinatario / Centro de xestión", nome_recibe],
        ["NIF", nif_recibe],
        ["Enderezo", end_recibe],
        ["Código REGA ou NIMA", rega_recibe],
        [],
        ["3. DATOS DA SUBMINISTRACIÓN"],
        ["Data da entrega", f"{mov.data:%d/%m/%Y}"],
        ["Tipo de explotación de orixe", mov.tipo_explotacion],
        ["Tipo de animais (especie)", especie_desc],
        ["Material fertilizante", material_desc],
        ["Cantidade", mov.cantidade],
        ["Unidade", mov.unidade],
        [],
        ["4. CARACTERÍSTICAS AGRONÓMICAS (COMPOSICIÓN)"],
        [
            "Nitróxeno total (N)",
            f"{mov.n_total:g} %" if mov.n_total is not None else "",
        ],
        [
            "Fósforo (P₂O₅)",
            f"{mov.p2o5:g} %" if mov.p2o5 is not None else "",
        ],
        [
            "Potasio (K₂O)",
            f"{mov.k2o:g} %" if mov.k2o is not None else "",
        ],
        [
            "Materia orgánica",
            f"{mov.materia_organica:g} %" if mov.materia_organica is not None else "",
        ],
        ["Orixe da composición", orixe_desc],
        [],
        ["5. DESTINO"],
        ["Parcelas de destino", mov.parcelas_destino or ""],
    ]

    for fila in filas:
        ws.append(fila)

    ws["A1"].font = Font(bold=True, size=12)

    for row in ws.iter_rows(min_row=3):
        first = row[0].value
        if first and str(first).startswith(("1.", "2.", "3.", "4.", "5.")):
            row[0].font = Font(bold=True)
        elif len(row) > 1 and row[1].value is not None:
            row[0].font = Font(bold=True)

    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 50

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def resumo_ano(
    session: Session,
    actor: Usuario,
    horta_id: int,
    ano: int,
) -> ResumoEsterco:
    """Calcula os totais de esterco cedido e recibido no ano e os kg de N."""
    movs = listar_movementos(session, actor, horta_id, ano=ano)
    cedidos = TotaisDict()
    recibidos = TotaisDict()
    kg_n_cedido = 0.0
    kg_n_recibido = 0.0
    aviso_m3 = False

    for m in movs:
        clave = (m.material, m.unidade)
        if m.unidade == "m3":
            aviso_m3 = True
        if m.tipo == "cesion":
            cedidos[clave] = round(cedidos.get(clave, 0.0) + m.cantidade, 3)
            if m.n_total is not None:
                # 1 t = 1000 kg. Se a unidade é m³, considérase 1 m³ = 1 t = 1000 kg.
                kg_n = m.cantidade * 1000.0 * (m.n_total / 100.0)
                kg_n_cedido += kg_n
        elif m.tipo == "recepcion":
            recibidos[clave] = round(recibidos.get(clave, 0.0) + m.cantidade, 3)
            if m.n_total is not None:
                kg_n = m.cantidade * 1000.0 * (m.n_total / 100.0)
                kg_n_recibido += kg_n

    return ResumoEsterco(
        ano=ano,
        cedidos=cedidos,
        recibidos=recibidos,
        kg_n_cedido=round(kg_n_cedido, 2),
        kg_n_recibido=round(kg_n_recibido, 2),
        aviso_m3=aviso_m3,
    )

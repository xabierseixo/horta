"""Libro de rexistro da explotación gandeira (RD 787/2023, art. 23 e anexo V) e rexistro de
tratamentos con medicamentos veterinarios (RD 666/2023, art. 41; Reg. UE 2019/6, art. 108),
nun Excel. Saen do que xa se apunta (grupos, entradas e saídas, coidados): nada a maiores.
Os animais van por grupos; a identificación individual vai no texto «identificación»."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import Session

from horta.models.animal import Animal, AnimalIdentificado
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.horta import Horta, RolHorta
from horta.models.movemento_animal import MovementoAnimal
from horta.models.persoa import Persoa
from horta.models.produto import EntradaProduto, Produto
from horta.models.usuario import Usuario
from horta.services.animais import DISPOSITIVOS
from horta.services.caderno import folla
from horta.services.coidados_animais import TIPOS_COIDADO
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.movementos_animais import TIPOS_MOVEMENTO
from horta.services.persoas import nome_completo, titular_da_horta

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def _d(valor: date | None) -> str:
    return f"{valor:%d/%m/%Y}" if valor else ""


def _titular_animais(p: Persoa | None, enderezo: Callable[[Persoa | None], str]
                     ) -> tuple[str, str, str]:
    """Nome, NIF e enderezo do titular dos animais, se non é o da explotación."""
    return (nome_completo(p), p.nif or "", enderezo(p)) if p else ("", "", "")


def xerar_libros(session: Session, actor: Usuario, horta_id: int, desde: date, ata: date
                 ) -> bytes:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    if ata < desde:
        raise OperacionNonPermitidaError("A data final non pode ser anterior á inicial")
    horta = session.get(Horta, horta_id)
    assert horta is not None
    titular = titular_da_horta(session, horta_id)
    cab = (f"Explotación: {horta.nome} · REGA: {horta.codigo_rega or '—'} · "
           f"Titular: {nome_completo(titular)} · Período: {_d(desde)} – {_d(ata)}")
    grupos = {a.id: a for a in session.query(Animal).filter_by(horta_id=horta_id)}

    def grupo(animal_id: int) -> str:
        a = grupos.get(animal_id)
        return f"{a.especie}{f' ({a.raza})' if a.raza else ''}" if a else ""

    def persoa(persoa_id: int | None) -> Persoa | None:
        return session.get(Persoa, persoa_id) if persoa_id else None

    def enderezo(p: Persoa | None) -> str:
        return ", ".join(x for x in (p.enderezo, p.codigo_postal, p.localidade) if x) if p \
            else ""

    wb = Workbook()
    wb.remove(wb.active)
    especies = sorted({a.especie_codigo or a.especie for a in grupos.values()})
    folla(wb, "Explotación", "Datos da explotación e do titular (RD 787/2023, anexo V.1–5)",
          cab, ("Dato", "Valor"), [
              ("Código da explotación (REGA)", horta.codigo_rega or ""),
              ("Nome", horta.nome),
              ("Enderezo", ", ".join(x for x in (horta.enderezo, horta.codigo_postal,
                                                  horta.localidade, horta.provincia) if x)),
              ("Coordenadas", f"{horta.lat:.6f}, {horta.lon:.6f}"
               if horta.lat is not None and horta.lon is not None else ""),
              ("Titular", nome_completo(titular)),
              ("NIF do titular", (titular.nif or "") if titular else ""),
              ("Teléfono do titular", (titular.telefono or "") if titular else ""),
              ("Correo do titular", (titular.email or "") if titular else ""),
              ("Enderezo do titular", enderezo(titular)),
              ("Especies", ", ".join(especies)),
              ("Clasificación", horta.rega_clasificacion or ""),
              ("Capacidade máxima", horta.rega_capacidade or "")])
    folla(wb, "Censo", "Libro de rexistro gandeiro: especies e animais (RD 787/2023, anexo V)",
          cab, ("Grupo", "Especie (código)", "Raza", "Animais hoxe", "Alta", "Baixa",
                "Titular dos animais (se é outro)", "NIF", "Enderezo"),
          [(a.especie, a.especie_codigo or "", a.raza or "", a.cantidade, _d(a.data_alta),
            _d(a.data_baixa), *_titular_animais(persoa(a.titular_animais_id), enderezo))
           for a in grupos.values()])
    identificados = (session.query(AnimalIdentificado)
                     .filter(AnimalIdentificado.animal_id.in_(grupos))
                     .order_by(AnimalIdentificado.animal_id, AnimalIdentificado.identificador))
    folla(wb, "Identificación", "Animais identificados individualmente (RD 787/2023, anexo V)",
          cab, ("Grupo", "Identificador", "Dispositivo", "Nome", "Sexo", "Nacemento", "Alta",
                "Baixa"),
          [(grupo(i.animal_id), i.identificador, DISPOSITIVOS.get(i.dispositivo or "", ""),
            i.nome or "", i.sexo or "",
            _d(i.data_nacemento), _d(i.data_alta), _d(i.data_baixa)) for i in identificados])
    movementos = (session.query(MovementoAnimal)
                  .filter(MovementoAnimal.horta_id == horta_id,
                          MovementoAnimal.baixa.is_(False), MovementoAnimal.data >= desde,
                          MovementoAnimal.data <= ata).order_by(MovementoAnimal.data))
    filas_mov = []
    for m in movementos:
        outra = persoa(m.outra_parte_id)
        filas_mov.append((_d(m.data), grupo(m.animal_id),
                          TIPOS_MOVEMENTO.get(m.tipo, m.tipo), m.cantidade,
                          m.identificacion or "", nome_completo(outra) if outra else "",
                          enderezo(outra), outra.rega if outra and outra.rega else "",
                          m.codigo_movemento or "",
                          m.causa or ""))
    folla(wb, "Entradas e saídas", "Entradas e saídas de animais (RD 787/2023, anexo V)", cab,
          ("Data", "Grupo", "Movemento", "Animais", "Identificación",
           "Explotación de orixe ou destino", "Enderezo do titular", "REGA",
           "Código do movemento", "Causa"),
          filas_mov)
    coidados = list(session.query(CoidadoAnimal)
                    .filter(CoidadoAnimal.horta_id == horta_id,
                            CoidadoAnimal.baixa.is_(False), CoidadoAnimal.data_inicio >= desde,
                            CoidadoAnimal.data_inicio <= ata).order_by(CoidadoAnimal.data_inicio))
    folla(wb, "Enfermidades e produción",
          "Enfermidades e cambios nos parámetros de produción (RD 787/2023, anexo V)", cab,
          ("Data", "Grupo", "Que", "Descrición", "Animais afectados", "Identificación"),
          [(_d(c.data_inicio), grupo(c.animal_id), TIPOS_COIDADO[c.tipo], c.descricion or "",
            c.num_animais or "", c.identificacion or "")
           for c in coidados if c.tipo in ("enfermidade", "producion")])
    folla(wb, "Visitas", "Visitas e vehículos (RD 787/2023, anexo V)", cab,
          ("Data", "Grupo", "Quen", "Matrícula", "Motivo"),
          [(_d(c.data_inicio), grupo(c.animal_id), nome_completo(persoa(c.visitante_id)),
            c.matricula or "", c.descricion or "") for c in coidados if c.tipo == "visita"])
    filas_med = []
    for c in coidados:
        if c.tipo != "medicamento":
            continue
        produto = session.get(Produto, c.produto_id) if c.produto_id else None
        entrada = session.get(EntradaProduto, c.entrada_id) if c.entrada_id else None
        provedor = persoa(entrada.provedor_id) if entrada else None
        filas_med.append((
            _d(c.data_inicio), produto.nome if produto else "",
            f"{c.cantidade:g} {c.unidade or ''}".strip() if c.cantidade is not None else "",
            nome_completo(provedor) if provedor else "",
            " ".join(x for x in (provedor.enderezo, provedor.localidade) if x) if provedor
            else "", (entrada.albaran_factura or "") if entrada else "",
            f"{grupo(c.animal_id)} {c.identificacion or ''}".strip(),
            nome_completo(persoa(c.veterinario_id)), c.receita or "",
            c.tempo_espera_dias if c.tempo_espera_dias is not None else "",
            c.duracion_dias or ""))
    folla(wb, "Medicamentos",
          "Tratamentos con medicamentos veterinarios (Reg. UE 2019/6 art. 108; RD 666/2023 "
          "art. 41)", cab,
          ("Data da 1.ª administración", "Medicamento", "Cantidade", "Provedor",
           "Enderezo do provedor", "Proba de compra (albará/factura)",
           "Animais tratados", "Veterinario", "Nº de receita", "Tempo de espera (días)",
           "Duración (días)"), filas_med)
    saida = BytesIO()
    wb.save(saida)
    return saida.getvalue()

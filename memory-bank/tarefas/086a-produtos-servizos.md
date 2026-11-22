# Tarefa 086a — Produtos (2/3): produtos e compras nos traballos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 086. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Produto e EntradaProduto; os abonados, tratamentos, coidados e cultivos apuntan ao produto e á compra; existencias (o que entrou, o usado e o que queda); caderno e CUE collen provedor, albará e lote da compra; nos formularios escóllese o produto e de que compra sae. Deseño: `docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md` (paso 7 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/models/produto.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `src/horta/models/abonado.py`
- `src/horta/models/tratamento_fito.py`
- `src/horta/models/coidado_animal.py`
- `src/horta/models/cultivo.py`
- `src/horta/services/produtos.py` (**ficheiro novo**)
- `src/horta/services/fertilizantes.py`
- `src/horta/services/abonados.py`
- `src/horta/services/tratamentos_fito.py`
- `src/horta/services/coidados_animais.py`
- `src/horta/services/cultivos.py`
- `src/horta/services/caderno.py`
- `src/horta/services/cue.py`
- `src/horta/services/diario.py`
- `src/horta/services/tarefas.py`
- `src/horta/services/hortas.py`
- `src/horta/ui/campo_produto.py` (**ficheiro novo**)
- `src/horta/ui/dialogo_abono.py`
- `src/horta/ui/pages/abonados.py`
- `src/horta/ui/pages/coidados_animais.py`
- `src/horta/ui/pages/cultivos.py`
- `tests/services/test_produtos.py` (**ficheiro novo**)
- `tests/services/test_fertilizantes.py`
- `tests/services/test_caderno_abonos_metais.py`
- `tests/services/test_coidados_animais.py`
- `tests/services/test_cultivos.py`
- `tests/services/test_persoas_papeis.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/produto.py`

Contido completo:
```python
"""Produtos (insumos) da explotación e as súas entradas (compras ou recepcións):
docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md. Mércase unha vez e úsase
moitas: os usos (abonado, tratamento, coidado, sementeira) apuntan ao produto e á entrada."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # services.produtos.TIPOS_PRODUTO: fitosanitario, abono, semente, medicamento, penso,
    # enerxia, outro
    tipo: Mapped[str] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(250))
    # Unidade das existencias: kg, l ou unidades
    unidade: Mapped[str] = mapped_column(String(20))
    # Fitosanitario: nº do rexistro do MAPA; medicamento: nº de autorización
    num_rexistro: Mapped[str | None] = mapped_column(String(20), default=None)
    # Abono: a súa composición
    fertilizante_id: Mapped[int | None] = mapped_column(
        ForeignKey("fertilizante.id"), unique=True, default=None)
    # Enerxía: catálogo tipo_enerxia (CUE 2)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class EntradaProduto(ParteComun, FeitoPor, Base):
    """Cada compra ou recepción dun produto: un traballo coa parte común."""

    __tablename__ = "entrada_produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    # Baleira se non se sabe (datos de antes do paso 7)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    lote_provedor: Mapped[str | None] = mapped_column(String(50), default=None)
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    importe: Mapped[float | None] = mapped_column(Float, default=None)
    data_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    # Sementes e plantas (Reg. UE 2016/2031)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)
```

### Paso 2 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.producion_animal import ProducionAnimal
```

Despois:
```python
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto, Produto
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
    "ProducionAnimal",
```

Despois:
```python
    "ProducionAnimal",
    "Produto",
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
    "VariedadeLocal",
```

Despois:
```python
    "VariedadeLocal",
    "EntradaProduto",
```

### Paso 5 — `src/horta/models/abonado.py`

Antes:
```python
    tratamento_estercos: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

Despois:
```python
    tratamento_estercos: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 6 — `src/horta/models/abonado.py`

Antes:
```python
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
```

Despois:
```python
    # De que compra saíu o abono, se se sabe (o albará e o provedor van nela)
    entrada_id: Mapped[int | None] = mapped_column(ForeignKey("entrada_produto.id"), default=None)
```

### Paso 7 — `src/horta/models/tratamento_fito.py`

Antes:
```python
    unidade: Mapped[str] = mapped_column(String(20))
```

Despois:
```python
    unidade: Mapped[str] = mapped_column(String(20))
    # O produto da explotación e de que compra saíu, se se sabe
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produto.id"), default=None)
    entrada_id: Mapped[int | None] = mapped_column(ForeignKey("entrada_produto.id"), default=None)
```

### Paso 8 — `src/horta/models/coidado_animal.py`

Antes:
```python
    medicamento: Mapped[str | None] = mapped_column(String(250), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    proba_compra: Mapped[str | None] = mapped_column(String(100), default=None)
```

Despois:
```python
    # O medicamento (produto) e de que compra saíu: alí van o provedor e a proba de compra
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produto.id"), default=None)
    entrada_id: Mapped[int | None] = mapped_column(ForeignKey("entrada_produto.id"), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 9 — `src/horta/models/cultivo.py`

Antes:
```python
    provedor_material_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    lote_material: Mapped[str | None] = mapped_column(String(40), default=None)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)
```

Despois:
```python
    # A compra da semente ou planta: provedor, lote, data e pasaporte fitosanitario
    entrada_semente_id: Mapped[int | None] = mapped_column(
        ForeignKey("entrada_produto.id"), default=None)
```

### Paso 10 — `src/horta/models/cultivo.py`

Antes:
```python
    semente_tratamento_num_rexistro: Mapped[str | None] = mapped_column(String(50), default=None)
    material_adquirido: Mapped[bool] = mapped_column(Boolean, default=False)
    data_adquisicion_material: Mapped[date | None] = mapped_column(Date, default=None)
```

Despois:
```python
    semente_tratamento_num_rexistro: Mapped[str | None] = mapped_column(String(50), default=None)
```

### Paso 11 — crear o ficheiro `src/horta/services/produtos.py`

Contido completo:
```python
"""Produtos (insumos) e entradas (compras ou recepcións), e as existencias: o que entrou menos o
que se usou nos abonados, tratamentos, coidados e sementeiras
(docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, Fertilizante
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.produto import EntradaProduto, Produto
from horta.models.tratamento_fito import TratamentoFito, TratamentoProduto
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import dose_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import converter
from horta.services.persoas import comprobar_quen, persoa_co_papel

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_PRODUTO: dict[str, str] = {
    "fitosanitario": "Fitosanitario",
    "abono": "Abono",
    "semente": "Semente ou planta",
    "medicamento": "Medicamento veterinario",
    "penso": "Penso",
    "enerxia": "Enerxía (gasóleo, luz...)",
    "outro": "Outro",
}
UNIDADES_PRODUTO = ("kg", "litros", "unidades")
UNIDADES_ENTRADA = ("kg", "t", "litros", "unidades", "ducias")
# Unidades do catálogo oficial (tratamentos e coidados): absolutas e por hectárea
_ABSOLUTAS = {"5": "kg", "6": "t", "4": "litros", "11": "unidades"}
_POR_HECTAREA = {"17": "kg", "18": "litros", "29": "t"}


# --- Produtos

def crear_produto(session: Session, actor: Usuario, horta_id: int, tipo: str, nome: str,
                  unidade: str, num_rexistro: str | None = None,
                  fertilizante_id: int | None = None, tipo_enerxia: str | None = None,
                  gardar: bool = True) -> Produto:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if tipo not in TIPOS_PRODUTO:
        raise OperacionNonPermitidaError("Escolle que tipo de produto é")
    if not nome.strip():
        raise OperacionNonPermitidaError("Pon un nome ao produto")
    if unidade not in UNIDADES_PRODUTO:
        raise OperacionNonPermitidaError("A unidade é kg, litros ou unidades")
    produto = Produto(horta_id=horta_id, tipo=tipo, nome=nome.strip(), unidade=unidade,
                      num_rexistro=(num_rexistro or "").strip() or None,
                      fertilizante_id=fertilizante_id, tipo_enerxia=tipo_enerxia or None)
    session.add(produto)
    if gardar:
        session.commit()
    else:
        session.flush()
    return produto


def produto_ou_novo(session: Session, actor: Usuario, horta_id: int, tipo: str, nome: str,
                    unidade: str = "unidades", num_rexistro: str | None = None) -> Produto:
    """O produto dese tipo co mesmo nº de rexistro (ou nome), ou un novo. Para os formularios
    e para ligar os tratamentos cos seus fitosanitarios."""
    consulta = session.query(Produto).filter_by(horta_id=horta_id, tipo=tipo)
    if num_rexistro:
        existente = consulta.filter_by(num_rexistro=num_rexistro.strip()).first()
    else:
        existente = next((p for p in consulta
                          if p.nome.strip().lower() == nome.strip().lower()), None)
    if existente is not None:
        return existente
    return crear_produto(session, actor, horta_id, tipo, nome or num_rexistro or "",
                         unidade, num_rexistro=num_rexistro, gardar=False)


def produto_do_abono(session: Session, fertilizante: Fertilizante) -> Produto:
    """O produto dun abono (creado con el)."""
    produto = session.query(Produto).filter_by(fertilizante_id=fertilizante.id).one_or_none()
    if produto is None:
        produto = Produto(horta_id=fertilizante.horta_id, tipo="abono", nome=fertilizante.nome,
                          unidade="litros" if fertilizante.liquido else "kg",
                          fertilizante_id=fertilizante.id)
        session.add(produto)
        session.flush()
    return produto


def listar_produtos(session: Session, actor: Usuario, horta_id: int, tipo: str | None = None,
                    so_activos: bool = True) -> list[Produto]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Produto).filter_by(horta_id=horta_id)
    if tipo is not None:
        consulta = consulta.filter_by(tipo=tipo)
    if so_activos:
        consulta = consulta.filter_by(activo=True)
    return list(consulta.order_by(Produto.tipo, Produto.nome))


# --- Entradas

@dataclass(kw_only=True)
class DatosEntrada:
    produto_id: int
    data: date
    persoa_id: int | None
    provedor_id: int | None = None
    cantidade: float | None = None
    unidade: str | None = None
    lote_provedor: str | None = None
    albaran_factura: str | None = None
    importe: float | None = None
    data_caducidade: date | None = None
    pasaporte_fitosanitario: str | None = None
    horas: float | None = None
    notas: str | None = None


def _validar_entrada(session: Session, datos: DatosEntrada, produto: Produto,
                     hoxe: date) -> None:
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    comprobar_quen(session, produto.horta_id, datos.persoa_id, datos.horas)
    persoa_co_papel(session, produto.horta_id, datos.provedor_id, "provedor")
    if datos.cantidade is not None:
        if datos.cantidade <= 0:
            raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
        if converter(datos.cantidade, datos.unidade or produto.unidade, produto.unidade) is None:
            raise OperacionNonPermitidaError(f"Este produto cóntase en {produto.unidade}")
    if datos.importe is not None and datos.importe < 0:
        raise OperacionNonPermitidaError("O prezo non pode ser negativo")
    if datos.data_caducidade is not None and datos.data_caducidade < datos.data:
        raise OperacionNonPermitidaError("A caducidade non pode ser anterior á entrada")


def _copiar_entrada(entrada: EntradaProduto, datos: DatosEntrada, produto: Produto) -> None:
    entrada.horta_id = produto.horta_id
    entrada.produto_id = produto.id
    entrada.data = datos.data
    entrada.provedor_id = datos.provedor_id
    entrada.cantidade = datos.cantidade
    entrada.unidade = (datos.unidade or produto.unidade) if datos.cantidade else None
    entrada.lote_provedor = datos.lote_provedor or None
    entrada.albaran_factura = datos.albaran_factura or None
    entrada.importe = datos.importe
    entrada.data_caducidade = datos.data_caducidade
    entrada.pasaporte_fitosanitario = (datos.pasaporte_fitosanitario or None
                                       if produto.tipo == "semente" else None)
    entrada.persoa_id = datos.persoa_id
    entrada.horas = datos.horas
    entrada.notas = datos.notas or None


def _produto(session: Session, produto_id: int) -> Produto:
    produto = session.get(Produto, produto_id)
    if produto is None:
        raise OperacionNonPermitidaError("Ese produto non existe")
    return produto


def crear_entrada(session: Session, actor: Usuario, datos: DatosEntrada,
                  hoxe: date | None = None) -> EntradaProduto:
    produto = _produto(session, datos.produto_id)
    comprobar_rol_horta(session, produto.horta_id, actor, _ROLES_ESCRITURA)
    _validar_entrada(session, datos, produto, hoxe or date.today())
    entrada = EntradaProduto(creado_por=actor.id)
    _copiar_entrada(entrada, datos, produto)
    session.add(entrada)
    session.commit()
    return entrada


def actualizar_entrada(session: Session, actor: Usuario, entrada: EntradaProduto,
                       datos: DatosEntrada, hoxe: date | None = None) -> EntradaProduto:
    if entrada.baixa:
        raise OperacionNonPermitidaError("Unha entrada dada de baixa non se pode modificar")
    comprobar_rol_horta(session, entrada.horta_id, actor, _ROLES_ESCRITURA)
    produto = _produto(session, datos.produto_id)
    if produto.horta_id != entrada.horta_id:
        raise OperacionNonPermitidaError("Ese produto non é desta explotación")
    _validar_entrada(session, datos, produto, hoxe or date.today())
    _copiar_entrada(entrada, datos, produto)
    session.commit()
    return entrada


def dar_de_baixa_entrada(session: Session, actor: Usuario, entrada: EntradaProduto) -> None:
    comprobar_rol_horta(session, entrada.horta_id, actor, _ROLES_ESCRITURA)
    entrada.baixa = True
    session.commit()


def listar_entradas(session: Session, actor: Usuario, horta_id: int,
                    produto_id: int | None = None, tipo: str | None = None
                    ) -> list[EntradaProduto]:
    """Do máis recente ao máis antigo."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(EntradaProduto).filter_by(horta_id=horta_id, baixa=False)
    if produto_id is not None:
        consulta = consulta.filter_by(produto_id=produto_id)
    if tipo is not None:
        consulta = consulta.join(Produto, Produto.id == EntradaProduto.produto_id).filter(
            Produto.tipo == tipo)
    return list(consulta.order_by(EntradaProduto.data.desc(), EntradaProduto.id.desc()))


def comprobar_entrada_do_produto(session: Session, horta_id: int, entrada_id: int | None,
                                 produto_id: int | None) -> EntradaProduto | None:
    """A entrada escollida nun uso ten que ser desta explotación e dese produto."""
    if entrada_id is None:
        return None
    entrada = session.get(EntradaProduto, entrada_id)
    if entrada is None or entrada.horta_id != horta_id or entrada.baixa:
        raise OperacionNonPermitidaError("Esa compra non é desta explotación")
    if produto_id is not None and entrada.produto_id != produto_id:
        raise OperacionNonPermitidaError("Esa compra é doutro produto")
    return entrada


# --- Existencias

@dataclass
class Existencias:
    entrou: float
    usado: float
    sen_contar: int  # usos que non se poden contar (sen cantidade ou noutra unidade)
    entradas_sen_cantidade: int

    @property
    def queda(self) -> float:
        return self.entrou - self.usado


def _usos(session: Session, produto: Produto) -> list[tuple[float | None, str | None]]:
    """Cantidade e unidade de cada uso do produto (None se non se pode saber)."""
    usos: list[tuple[float | None, str | None]] = []
    if produto.fertilizante_id is not None:
        fertilizante = session.get(Fertilizante, produto.fertilizante_id)
        for ab in session.query(Abonado).filter_by(fertilizante_id=produto.fertilizante_id,
                                                   baixa=False):
            superficie = sum(le.superficie_ha or 0 for le in ab.leiras)
            kg_ha = (dose_kg_ha(ab.dose, ab.unidade, fertilizante.densidade if fertilizante
                                else None) if ab.dose is not None and ab.unidade else None)
            usos.append((kg_ha * superficie, "kg") if kg_ha is not None and superficie
                        else (None, None))
    for tp in (session.query(TratamentoProduto)
               .join(TratamentoFito, TratamentoFito.id == TratamentoProduto.tratamento_id)
               .filter(TratamentoProduto.produto_id == produto.id,
                       TratamentoFito.baixa.is_(False))):
        if tp.cantidade is not None and tp.unidade in _ABSOLUTAS:
            usos.append((tp.cantidade, _ABSOLUTAS[tp.unidade]))
        elif tp.dose is not None and tp.unidade in _POR_HECTAREA:
            tratamento = session.get(TratamentoFito, tp.tratamento_id)
            superficie = sum(c.superficie_ha or 0 for c in tratamento.cultivos) \
                if tratamento else 0
            usos.append((tp.dose * superficie, _POR_HECTAREA[tp.unidade]) if superficie
                        else (None, None))
        else:
            usos.append((None, None))
    for co in session.query(CoidadoAnimal).filter_by(produto_id=produto.id, baixa=False):
        usos.append((co.cantidade, _ABSOLUTAS.get(co.unidade or ""))
                    if co.cantidade is not None else (None, None))
    for cu in (session.query(Cultivo)
               .join(EntradaProduto, EntradaProduto.id == Cultivo.entrada_semente_id)
               .filter(EntradaProduto.produto_id == produto.id)):
        if cu.cantidade_semente_kg:
            usos.append((cu.cantidade_semente_kg, "kg"))
        elif cu.dose_sementeira_kg_ha and cu.superficie_ha:
            usos.append((cu.dose_sementeira_kg_ha * cu.superficie_ha, "kg"))
        else:
            usos.append((None, None))
    return usos


def existencias(session: Session, produto: Produto) -> Existencias:
    entrou, sen_cantidade = 0.0, 0
    for entrada in session.query(EntradaProduto).filter_by(produto_id=produto.id, baixa=False):
        cantidade = (converter(entrada.cantidade, entrada.unidade or produto.unidade,
                               produto.unidade) if entrada.cantidade is not None else None)
        if cantidade is None:
            sen_cantidade += 1
        else:
            entrou += cantidade
    usado, sen_contar = 0.0, 0
    for cantidade, unidade in _usos(session, produto):
        convertida = (converter(cantidade, unidade, produto.unidade)
                      if cantidade is not None and unidade else None)
        if convertida is None:
            sen_contar += 1
        else:
            usado += convertida
    return Existencias(round(entrou, 3), round(usado, 3), sen_contar, sen_cantidade)


def ten_movementos(session: Session, produto: Produto) -> bool:
    return (session.query(EntradaProduto).filter_by(produto_id=produto.id).first() is not None
            or bool(_usos(session, produto)))
```

### Paso 12 — `src/horta/services/fertilizantes.py`

Antes:
```python
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import persoa_co_papel
```

Despois:
```python
from horta.models.produto import Produto
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

### Paso 13 — `src/horta/services/fertilizantes.py`

Antes:
```python
    tratamento_estercos: str | None = None
    # De onde vén: persoa ou entidade co papel «provedor» (co seu NIF, REGA ou NIMA)
    provedor_id: int | None = None
```

Despois:
```python
    tratamento_estercos: str | None = None
```

### Paso 14 — `src/horta/services/fertilizantes.py`

Antes:
```python
        raise OperacionNonPermitidaError("A densidade ten que ser maior que 0")
    persoa_co_papel(session, horta_id, datos.provedor_id, "provedor")
    if datos.material in ESTERCOS | RESIDUOS and datos.provedor_id is None:
        raise OperacionNonPermitidaError("Nos estercos e residuos indica de onde veñen")
```

Despois:
```python
        raise OperacionNonPermitidaError("A densidade ten que ser maior que 0")
```

### Paso 15 — `src/horta/services/fertilizantes.py`

Antes:
```python
    session.add(fertilizante)
```

Despois:
```python
    session.add(fertilizante)
    session.flush()
    # O abono é un produto da explotación: as súas compras (e o provedor) son entradas
    session.add(Produto(horta_id=horta_id, tipo="abono", nome=nome,
                        unidade="litros" if datos.liquido else "kg",
                        fertilizante_id=fertilizante.id))
```

### Paso 16 — `src/horta/services/abonados.py`

Antes:
```python
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, nutrientes_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.leiras import LeiraTraballo, LeiraValida, as_leiras, validar_leiras
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.models.produto import Produto
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, nutrientes_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.leiras import LeiraTraballo, LeiraValida, as_leiras, validar_leiras
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen
from horta.services.produtos import comprobar_entrada_do_produto
```

### Paso 17 — `src/horta/services/abonados.py`

Antes:
```python
    albaran_factura: str | None = None
```

Despois:
```python
    # De que compra saíu o abono (alí van o provedor e o albará)
    entrada_id: int | None = None
```

### Paso 18 — `src/horta/services/abonados.py`

Antes:
```python
        raise OperacionNonPermitidaError("Ese abono non é desta explotación")
```

Despois:
```python
        raise OperacionNonPermitidaError("Ese abono non é desta explotación")
    produto = session.query(Produto).filter_by(fertilizante_id=fertilizante.id).one_or_none()
    comprobar_entrada_do_produto(session, horta_id, datos.entrada_id,
                                 produto.id if produto else -1)
```

### Paso 19 — `src/horta/services/abonados.py`

Antes:
```python
    abonado.albaran_factura = datos.albaran_factura or None
```

Despois:
```python
    abonado.entrada_id = datos.entrada_id if datos.fertilizante_id else None
```

### Paso 20 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
from horta.services.persoas import ropo_vixente
```

Despois:
```python
from horta.services.persoas import ropo_vixente
from horta.services.produtos import comprobar_entrada_do_produto, produto_ou_novo
```

### Paso 21 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
    dose: float | None = None
    cantidade: float | None = None
```

Despois:
```python
    dose: float | None = None
    cantidade: float | None = None
    # De que compra saíu, se se sabe (o produto lígase só polo nº de rexistro ou o nome)
    entrada_id: int | None = None
```

### Paso 22 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
def crear_tratamento_fito(
    session: Session, actor: Usuario, horta_id: int, datos: DatosTratamento
) -> TratamentoFito:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    horta = session.get(Horta, horta_id)
    assert horta is not None
    _validar(session, horta, datos)
    tratamento = TratamentoFito(horta_id=horta_id, data_inicio=datos.data_inicio,
                                data_fin=datos.data_fin, creado_por=actor.id)
    _aplicar(tratamento, datos)
```

Despois:
```python
def _ligar_produtos(session: Session, actor: Usuario, horta_id: int,
                    tratamento: TratamentoFito) -> None:
    """Cada fitosanitario do tratamento é un produto da explotación (polo nº de rexistro ou o
    nome): así se contan as existencias. A compra, se se indicou, ten que ser dese produto."""
    for linha in tratamento.produtos:
        if not (linha.num_rexistro or linha.nome_comercial):
            continue
        produto = produto_ou_novo(session, actor, horta_id, "fitosanitario",
                                  linha.nome_comercial or linha.num_rexistro or "",
                                  "litros", num_rexistro=linha.num_rexistro)
        linha.produto_id = produto.id
        comprobar_entrada_do_produto(session, horta_id, linha.entrada_id, produto.id)


def crear_tratamento_fito(
    session: Session, actor: Usuario, horta_id: int, datos: DatosTratamento
) -> TratamentoFito:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    horta = session.get(Horta, horta_id)
    assert horta is not None
    _validar(session, horta, datos)
    tratamento = TratamentoFito(horta_id=horta_id, data_inicio=datos.data_inicio,
                                data_fin=datos.data_fin, creado_por=actor.id)
    _aplicar(tratamento, datos)
    _ligar_produtos(session, actor, horta_id, tratamento)
```

### Paso 23 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
    _validar(session, horta, datos)
    _aplicar(tratamento, datos)
```

Despois:
```python
    _validar(session, horta, datos)
    _aplicar(tratamento, datos)
    _ligar_produtos(session, actor, tratamento.horta_id, tratamento)
```

### Paso 24 — `src/horta/services/coidados_animais.py`

Antes:
```python
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

Despois:
```python
from horta.models.produto import Produto
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen, persoa_co_papel
from horta.services.produtos import comprobar_entrada_do_produto, produto_ou_novo
```

### Paso 25 — `src/horta/services/coidados_animais.py`

Antes:
```python
    medicamento: str | None = None
    cantidade: float | None = None
    unidade: str | None = None
    provedor_id: int | None = None
    proba_compra: str | None = None
```

Despois:
```python
    # O medicamento: o produto (ou o seu nome, e créase) e de que compra saíu, se se sabe.
    # O provedor e a proba de compra van na compra (entrada do produto)
    medicamento: str | None = None
    produto_id: int | None = None
    entrada_id: int | None = None
    cantidade: float | None = None
    unidade: str | None = None
```

### Paso 26 — `src/horta/services/coidados_animais.py`

Antes:
```python
        if not datos.medicamento:
            raise OperacionNonPermitidaError("Indica o medicamento")
        if datos.tempo_espera_dias is None:
            raise OperacionNonPermitidaError(
                "Indica o tempo de espera (0 se o medicamento non ten)")
        if datos.cantidade is not None and datos.cantidade <= 0:
            raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
        if datos.unidade:
            validar_codigo(session, "unidade_medida", datos.unidade, datos.data_inicio)
        persoa_co_papel(session, animal.horta_id, datos.provedor_id, "provedor")
```

Despois:
```python
        if not datos.medicamento and datos.produto_id is None:
            raise OperacionNonPermitidaError("Indica o medicamento")
        if datos.tempo_espera_dias is None:
            raise OperacionNonPermitidaError(
                "Indica o tempo de espera (0 se o medicamento non ten)")
        if datos.cantidade is not None and datos.cantidade <= 0:
            raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
        if datos.unidade:
            validar_codigo(session, "unidade_medida", datos.unidade, datos.data_inicio)
```

### Paso 27 — `src/horta/services/coidados_animais.py`

Antes:
```python
    coidado.medicamento = datos.medicamento if medicamento else None
    coidado.cantidade = datos.cantidade if medicamento else None
    coidado.unidade = (datos.unidade or None) if medicamento else None
    coidado.provedor_id = datos.provedor_id if medicamento else None
    coidado.proba_compra = (datos.proba_compra or None) if medicamento else None
```

Despois:
```python
    coidado.produto_id = datos.produto_id if medicamento else None
    coidado.entrada_id = datos.entrada_id if medicamento else None
    coidado.cantidade = datos.cantidade if medicamento else None
    coidado.unidade = (datos.unidade or None) if medicamento else None
```

### Paso 28 — `src/horta/services/coidados_animais.py`

Antes:
```python
def crear_coidado(
    session: Session, actor: Usuario, datos: DatosCoidado, hoxe: date | None = None
) -> CoidadoAnimal:
    animal = _animal(session, datos.animal_id)
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, animal, hoxe or date.today())
```

Despois:
```python
def _medicamento(session: Session, actor: Usuario, datos: DatosCoidado, horta_id: int) -> None:
    """O medicamento é un produto da explotación: o escollido, ou o do nome (créase)."""
    if datos.tipo != "medicamento":
        return
    if datos.produto_id is None:
        datos.produto_id = produto_ou_novo(session, actor, horta_id, "medicamento",
                                           datos.medicamento or "").id
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
```

### Paso 29 — `src/horta/services/coidados_animais.py`

Antes:
```python
        raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")
    _validar(session, datos, animal, hoxe or date.today())
```

Despois:
```python
        raise OperacionNonPermitidaError("Ese grupo de animais non é desta explotación")
    _validar(session, datos, animal, hoxe or date.today())
    _medicamento(session, actor, datos, animal.horta_id)
```

### Paso 30 — `src/horta/services/cultivos.py`

Antes:
```python
from horta.models.rega import RegaCultivo
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

Despois:
```python
from horta.models.produto import Produto
from horta.models.rega import RegaCultivo
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
from horta.services.produtos import comprobar_entrada_do_produto
```

### Paso 31 — `src/horta/services/cultivos.py`

Antes:
```python
        "provedor_material_id",
        "lote_material",
        "pasaporte_fitosanitario",
```

Despois:
```python
        "entrada_semente_id",
```

### Paso 32 — `src/horta/services/cultivos.py`

Antes:
```python
        "semente_tratamento_num_rexistro",
        "material_adquirido",
        "data_adquisicion_material",
```

Despois:
```python
        "semente_tratamento_num_rexistro",
```

### Paso 33 — `src/horta/services/cultivos.py`

Antes:
```python
    "material_adquirido", "data_adquisicion_material", "lote_material", *_CATALOGOS_CULTIVO,
```

Despois:
```python
    *_CATALOGOS_CULTIVO,
```

### Paso 34 — `src/horta/services/cultivos.py`

Antes:
```python
        )
    if valores["material_adquirido"] and valores["data_adquisicion_material"] is None:
        raise OperacionNonPermitidaError("Indica a data en que se adquiriu a semente ou planta")
```

Despois:
```python
        )
```

### Paso 35 — `src/horta/services/cultivos.py`

Antes:
```python
            validar_codigo(session, catalogo, str(valores[campo]), na_data)


```

Despois:
```python
            validar_codigo(session, catalogo, str(valores[campo]), na_data)


def _comprobar_semente(session: Session, horta_id: int, entrada_id: int | None) -> None:
    """A compra da semente ou planta: unha entrada dun produto de tipo semente."""
    entrada = comprobar_entrada_do_produto(session, horta_id, entrada_id, None)
    if entrada is not None:
        produto = session.get(Produto, entrada.produto_id)
        if produto is None or produto.tipo != "semente":
            raise OperacionNonPermitidaError("Esa compra non é dunha semente ou planta")


```

### Paso 36 — `src/horta/services/cultivos.py`

Antes:
```python
    persoa_co_papel(session, horta_id, campos.get("provedor_material_id"), "provedor")
```

Despois:
```python
    _comprobar_semente(session, horta_id, campos.get("entrada_semente_id"))
```

### Paso 37 — `src/horta/services/cultivos.py`

Antes:
```python
    persoa_co_papel(session, horta_id, cambios.get("provedor_material_id"), "provedor")
```

Despois:
```python
    _comprobar_semente(session, horta_id, cambios.get("entrada_semente_id"))
```

### Paso 38 — `src/horta/services/caderno.py`

Antes:
```python
from horta.models.persoa import Persoa, TipoCarne
```

Despois:
```python
from horta.models.persoa import Persoa, TipoCarne
from horta.models.produto import EntradaProduto
```

### Paso 39 — `src/horta/services/caderno.py`

Antes:
```python
        provedor = persoas_por_id.get(fe.provedor_id or 0) if fe else None
```

Despois:
```python
        # O provedor e o albará saen da compra (entrada) do abono
        entrada = session.get(EntradaProduto, ab.entrada_id) if ab.entrada_id else None
        provedor = persoas_por_id.get(entrada.provedor_id or 0) if entrada else None
```

### Paso 40 — `src/horta/services/caderno.py`

Antes:
```python
                ab.albaran_factura or ""])
```

Despois:
```python
                (entrada.albaran_factura or "") if entrada else ""])
```

### Paso 41 — `src/horta/services/cue.py`

Antes:
```python
from horta.models.persoa import Persoa
```

Despois:
```python
from horta.models.persoa import Persoa
from horta.models.produto import EntradaProduto
```

### Paso 42 — `src/horta/services/cue.py`

Antes:
```python
        engadir("SiembraPlantacion", {
            "IdAjenaSiembraPlant": c.id, "SiembraPlantacion": 0 if plantacion else 1,
            "FechaInicio": _data(c.data_inicio),
            "FechaFin": _data(c.data_fin_sementeira or c.data_inicio),
            "SiembraDirecta": c.sementeira_directa,
            "DosisSiembra": c.dose_sementeira_kg_ha,
            "UnidadDosisSiembra": 17 if c.dose_sementeira_kg_ha else None,
            "MaterialTratado": c.material_tratado, "MaterialAdquirido": c.material_adquirido,
            "FechaAdquisicion": _data(c.data_adquisicion_material) if c.material_adquirido
            else _data(c.data_inicio),
            "NumLote": c.lote_material,
```

Despois:
```python
        # A compra da semente ou planta (paso 7): provedor, lote e data
        semente = session.get(EntradaProduto, c.entrada_semente_id) if c.entrada_semente_id \
            else None
        engadir("SiembraPlantacion", {
            "IdAjenaSiembraPlant": c.id, "SiembraPlantacion": 0 if plantacion else 1,
            "FechaInicio": _data(c.data_inicio),
            "FechaFin": _data(c.data_fin_sementeira or c.data_inicio),
            "SiembraDirecta": c.sementeira_directa,
            "DosisSiembra": c.dose_sementeira_kg_ha,
            "UnidadDosisSiembra": 17 if c.dose_sementeira_kg_ha else None,
            "MaterialTratado": c.material_tratado, "MaterialAdquirido": semente is not None,
            "FechaAdquisicion": _data(semente.data if semente else c.data_inicio),
            "NumLote": semente.lote_provedor if semente else None,
```

### Paso 43 — `src/horta/services/cue.py`

Antes:
```python
        provedor = persoas.get(fe.provedor_id or 0) if fe else None
```

Despois:
```python
        entrada = session.get(EntradaProduto, ab.entrada_id) if ab.entrada_id else None
        provedor = persoas.get(entrada.provedor_id or 0) if entrada else None
```

### Paso 44 — `src/horta/services/cue.py`

Antes:
```python
                    "Unidad": _num(ab.unidade), "AlbaranFactura": ab.albaran_factura,
```

Despois:
```python
                    "Unidad": _num(ab.unidade),
                    "AlbaranFactura": entrada.albaran_factura if entrada else None,
```

### Paso 45 — `src/horta/services/diario.py`

Antes:
```python
from horta.services.producions_animais import PRODUTOS, listar_producions
```

Despois:
```python
from horta.services.producions_animais import PRODUTOS, listar_producions
from horta.services.produtos import listar_entradas, listar_produtos
```

### Paso 46 — `src/horta/services/diario.py`

Antes:
```python
    "lote_saida": "Saída de produto (venda, casa...)",
```

Despois:
```python
    "lote_saida": "Saída de produto (venda, casa...)",
    "entrada_produto": "Entrada de produto (compra)",
```

### Paso 47 — `src/horta/services/diario.py`

Antes:
```python
    nomes = {p.id: p.nome for p in listar_persoas(session, actor, horta_id, so_activas=False)}
```

Despois:
```python
    nomes = {p.id: p.nome for p in listar_persoas(session, actor, horta_id, so_activas=False)}
    nomes_produtos = {p.id: p.nome
                      for p in listar_produtos(session, actor, horta_id, so_activos=False)}
```

### Paso 48 — `src/horta/services/diario.py`

Antes:
```python
        detalle = co.medicamento if co.tipo == "medicamento" else (
```

Despois:
```python
        detalle = nomes_produtos.get(co.produto_id or 0) if co.tipo == "medicamento" else (
```

### Paso 49 — `src/horta/services/diario.py`

Antes:
```python
                                  persoas=_quen(pa.persoa_id), sen_quen=pa.persoa_id is None))
```

Despois:
```python
                                  persoas=_quen(pa.persoa_id), sen_quen=pa.persoa_id is None))
    for en in listar_entradas(session, actor, horta_id):
        cantidade = f"{en.cantidade:g} {en.unidade} de " if en.cantidade else ""
        traballos.append(Traballo(
            "entrada_produto", en.id, en.data, True,
            f"Entrada: {cantidade}{nomes_produtos.get(en.produto_id, '')}",
            nomes.get(en.provedor_id or 0, ""), frozenset(), persoas=_quen(en.persoa_id),
            sen_quen=en.persoa_id is None))
```

### Paso 50 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.producion_animal import ProducionAnimal
```

Despois:
```python
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto
```

### Paso 51 — `src/horta/services/tarefas.py`

Antes:
```python
    "lote_saida": (LoteSaida, "data"),
```

Despois:
```python
    "lote_saida": (LoteSaida, "data"),
    "entrada_produto": (EntradaProduto, "data"),
```

### Paso 52 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.producion_animal import ProducionAnimal
```

Despois:
```python
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto, Produto
```

### Paso 53 — `src/horta/services/hortas.py`

Antes:
```python
            "Esta explotación ten pastoreos rexistrados e debe conservarse (obriga legal)."
        )
```

Despois:
```python
            "Esta explotación ten pastoreos rexistrados e debe conservarse (obriga legal)."
        )
    if session.query(EntradaProduto).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten compras de produtos rexistradas e debe conservarse "
            "(obriga legal).")
    session.query(Produto).filter_by(horta_id=horta.id).delete()
```

### Paso 54 — crear o ficheiro `src/horta/ui/campo_produto.py`

Contido completo:
```python
"""Escoller un produto (insumo) nun formulario de traballo e, se se sabe, de que compra saíu.
Se o produto aínda non está, o botón «Novo» créao alí mesmo co nome
(docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md)."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.services.produtos import (
    TIPOS_PRODUTO,
    UNIDADES_PRODUTO,
    crear_produto,
    listar_entradas,
    listar_produtos,
)
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual


def opcions_entradas(horta_id: int, produto_id: int | None = None, tipo: str | None = None
                     ) -> dict[int, str]:
    """As compras dun produto (ou dun tipo), da máis recente á máis antiga."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return {}
        produtos = {p.id: p.nome for p in listar_produtos(session, actor, horta_id,
                                                           so_activos=False)}
        entradas = listar_entradas(session, actor, horta_id, produto_id=produto_id, tipo=tipo)
    return {e.id: " · ".join(x for x in (
        f"{e.data:%d/%m/%Y}", produtos.get(e.produto_id, ""),
        f"lote {e.lote_provedor}" if e.lote_provedor else "") if x) for e in entradas}


class CampoProduto:
    """Selector dos produtos dun tipo e botón para crear un novo. `value` é o id do produto."""

    def __init__(self, horta_id: int, tipo: str, etiqueta: str) -> None:
        self.horta_id = horta_id
        self.tipo = tipo
        with ui.row().classes("w-full no-wrap items-center gap-1") as self.fila:
            self.select = ui.select({}, label=etiqueta, with_input=True,
                                    clearable=True).classes("col")
            ui.button(icon="add", on_click=self._abrir_novo).props(
                'flat round dense aria-label="Novo produto"').tooltip("Novo")
        self._cargar()
        with ui.dialog() as self.dialogo, ui.card().style("width: min(26rem, 94vw)"):
            ui.label(f"Novo: {TIPOS_PRODUTO[tipo].lower()}").classes("text-h6")
            self.nome = ui.input("Nome").classes("w-full")
            self.unidade = ui.select(list(UNIDADES_PRODUTO), label="Cóntase en",
                                     value="unidades").classes("w-full")
            with ui.row():
                ui.button("Gardar", icon="check", on_click=self._gardar)
                ui.button("Cancelar", on_click=self.dialogo.close).props("flat")

    def _cargar(self) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                return
            produtos = listar_produtos(session, actor, self.horta_id, tipo=self.tipo)
        self.select.set_options({p.id: p.nome for p in produtos})

    def _abrir_novo(self) -> None:
        self.nome.value = ""
        self.dialogo.open()

    def _gardar(self) -> None:
        creado: list[int] = []
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            ok = executar_accion(session, lambda: creado.append(crear_produto(
                session, actor, self.horta_id, self.tipo, self.nome.value or "",
                self.unidade.value).id))
        if ok and creado:
            self._cargar()
            self.select.value = creado[0]
            self.dialogo.close()

    @property
    def value(self) -> int | None:
        return self.select.value

    @value.setter
    def value(self, produto_id: int | None) -> None:
        self.select.value = produto_id if produto_id in self.select.options else None

    def set_visibility(self, visible: bool) -> None:
        self.fila.set_visibility(visible)
```

### Paso 55 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
```

Despois:
```python
from horta.ui.accions import executar_accion
```

### Paso 56 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
        # De onde vén (empresa subministradora, granxa ou casa): obrigatorio nos estercos e
        # residuos; os seus NIF, REGA ou NIMA van na súa ficha de Persoas
        provedor = CampoPersoa(horta_id, "provedor", "De onde vén (empresa, granxa ou casa)")
```

Despois:
```python
        # De onde vén (empresa, granxa ou casa) apúntase en cada compra (Produtos)
```

### Paso 57 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
                        setattr(datos, campo, parsear_decimal(entrada.value))
                datos.provedor_id = provedor.value
```

Despois:
```python
                        setattr(datos, campo, parsear_decimal(entrada.value))
```

### Paso 58 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from horta.ui.accions import executar_accion
```

Despois:
```python
from horta.services.produtos import listar_produtos
from horta.ui.accions import executar_accion
from horta.ui.campo_produto import opcions_entradas
```

### Paso 59 — `src/horta/ui/pages/abonados.py`

Antes:
```python
                    for c in listar_cultivos(session, actor, horta_id)}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
```

Despois:
```python
                    for c in listar_cultivos(session, actor, horta_id)}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
        produtos_abono = {p.fertilizante_id: p.id for p in listar_produtos(
            session, actor, horta_id, tipo="abono") if p.fertilizante_id}
```

### Paso 60 — `src/horta/ui/pages/abonados.py`

Antes:
```python
            albaran = ui.input("Albará ou factura").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")
```

Despois:
```python
            # A compra do abono: alí van o provedor e o albará
            compra = ui.select({}, label="De que compra (opcional)", clearable=True).classes(
                "w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def cambiar_compras() -> None:
            produto = produtos_abono.get(abono.value or 0)
            compra.set_options(opcions_entradas(horta_id, produto) if produto else {},
                               value=None)

        abono.on_value_change(cambiar_compras)
```

### Paso 61 — `src/horta/ui/pages/abonados.py`

Antes:
```python
                        albaran_factura=albaran.value or None, persoa_id=aplicador.value,
```

Despois:
```python
                        entrada_id=compra.value, persoa_id=aplicador.value,
```

### Paso 62 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        albaran.value = (a.albaran_factura or "") if a else ""
```

Despois:
```python
        cambiar_compras()
        compra.value = a.entrada_id if a and a.entrada_id in compra.options else None
```

### Paso 63 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
```

Despois:
```python
from horta.services.produtos import listar_produtos
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campo_produto import CampoProduto, opcions_entradas
```

### Paso 64 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python

    filas = []
    for co in coidados:
        fin = fin_tempo_espera(co)
        filas.append({
            "id": co.id,
            "data": f"{co.data_inicio:%d/%m/%Y}",
            "grupo": grupos.get(co.animal_id, ""),
            "que": TIPOS_COIDADO[co.tipo].split(" (")[0],
            "detalle": co.medicamento or persoas.get(co.visitante_id or 0) or co.descricion
```

Despois:
```python
        medicamentos = {p.id: p.nome for p in listar_produtos(
            session, actor, horta_id, tipo="medicamento", so_activos=False)}

    filas = []
    for co in coidados:
        fin = fin_tempo_espera(co)
        filas.append({
            "id": co.id,
            "data": f"{co.data_inicio:%d/%m/%Y}",
            "grupo": grupos.get(co.animal_id, ""),
            "que": TIPOS_COIDADO[co.tipo].split(" (")[0],
            "detalle": medicamentos.get(co.produto_id or 0) or persoas.get(co.visitante_id or 0)
            or co.descricion
```

### Paso 65 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
        medicamento = ui.input("Medicamento").classes("w-full")
```

Despois:
```python
        medicamento = CampoProduto(horta_id, "medicamento", "Medicamento")
```

### Paso 66 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
            provedor = CampoPersoa(horta_id, "provedor", "Onde se mercou")
            proba_compra = ui.input("Nº de factura ou albará").classes("w-full")
        matricula = ui.input("Matrícula do vehículo").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")
```

Despois:
```python
            # Onde se mercou e a proba de compra: na compra (entrada) do medicamento
            compra = ui.select({}, label="De que compra (onde se mercou)", clearable=True
                               ).classes("w-full")
        matricula = ui.input("Matrícula do vehículo").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def cambiar_compras() -> None:
            compra.set_options(opcions_entradas(horta_id, medicamento.value)
                               if medicamento.value else {}, value=None)

        medicamento.select.on_value_change(cambiar_compras)
```

### Paso 67 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
                        medicamento=medicamento.value or None,
                        cantidade=parsear_decimal(cantidade.value), unidade=unidade.value,
                        provedor_id=provedor.value,
                        proba_compra=proba_compra.value or None,
```

Despois:
```python
                        produto_id=medicamento.value, entrada_id=compra.value,
                        cantidade=parsear_decimal(cantidade.value), unidade=unidade.value,
```

### Paso 68 — `src/horta/ui/pages/coidados_animais.py`

Antes:
```python
        medicamento.value = (co.medicamento or "") if co else ""
        cantidade.value = f"{co.cantidade:g}" if co and co.cantidade else ""
        unidade.value = co.unidade if co and co.unidade in unidades else None
        tempo_espera.value = (str(co.tempo_espera_dias)
                              if co and co.tempo_espera_dias is not None else "")
        duracion.value = str(co.duracion_dias) if co and co.duracion_dias else ""
        num_animais.value = str(co.num_animais) if co and co.num_animais else ""
        identificacion.value = (co.identificacion or "") if co else ""
        veterinario.value = co.veterinario_id if co else None
        receita.value = (co.receita or "") if co else ""
        provedor.value = co.provedor_id if co else None
        proba_compra.value = (co.proba_compra or "") if co else ""
```

Despois:
```python
        medicamento.value = co.produto_id if co else None
        cambiar_compras()
        compra.value = co.entrada_id if co and co.entrada_id in compra.options else None
        cantidade.value = f"{co.cantidade:g}" if co and co.cantidade else ""
        unidade.value = co.unidade if co and co.unidade in unidades else None
        tempo_espera.value = (str(co.tempo_espera_dias)
                              if co and co.tempo_espera_dias is not None else "")
        duracion.value = str(co.duracion_dias) if co and co.duracion_dias else ""
        num_animais.value = str(co.num_animais) if co and co.num_animais else ""
        identificacion.value = (co.identificacion or "") if co else ""
        veterinario.value = co.veterinario_id if co else None
        receita.value = (co.receita or "") if co else ""
```

### Paso 69 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
from horta.ui.campo_persoa import CampoPersoa
```

Despois:
```python
from horta.ui.campo_produto import opcions_entradas
```

### Paso 70 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            material_adquirido = ui.checkbox("A semente ou planta comprouse")
            data_adquisicion = campo_data("Data de compra")

        with ui.expansion("Orixe da semente ou planta").classes("w-full"):
            procedencia = ui.select(opcions["procedencia_material"], label="Procedencia",
                                    clearable=True).classes("w-full")
            # O provedor e o seu ROPVEG: ficha en Persoas
            provedor = CampoPersoa(horta_id, "provedor", "Provedor")
            lote_material = ui.input("Lote da semente ou planta").classes("w-full")
            pasaporte = ui.input("Pasaporte fitosanitario").classes("w-full")
```

Despois:
```python

        with ui.expansion("Orixe da semente ou planta").classes("w-full"):
            procedencia = ui.select(opcions["procedencia_material"], label="Procedencia",
                                    clearable=True).classes("w-full")
            # A compra (provedor, lote, data e pasaporte): apúntase en Produtos → Nova entrada
            compra_semente = ui.select(opcions_entradas(horta_id, tipo="semente"),
                                       label="De que compra (se se mercou)", clearable=True
                                       ).classes("w-full")
```

### Paso 71 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                provedor_material_id=provedor.value,
                lote_material=lote_material.value or None,
                pasaporte_fitosanitario=pasaporte.value or None,
```

Despois:
```python
                entrada_semente_id=compra_semente.value,
```

### Paso 72 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                if material_tratado.value else None,
                material_adquirido=material_adquirido.value,
                data_adquisicion_material=parsear_data(data_adquisicion.value),
```

Despois:
```python
                if material_tratado.value else None,
```

### Paso 73 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                    lote_material, pasaporte, num_arbores, marco,
                    ano_plantacion, unidades, ciclos, duracion, obxectivo, notas,
                    necesidade_n, necesidade_p, necesidade_k, plan_data, auga_n, auga_p,
                    semente_produto, semente_rexistro,
                    data_fin_sementeira, cantidade_semente, dose_sementeira, densidade,
                    data_adquisicion, castineiros, abeleiras, nogueiras, amendoeiras, outros_casca,
                    horas_sementeira)
    campos_select = (variedade_oficial, secano, procedencia, anterior, causa_baixa, cobertura)
    casillas = (sementeira_directa, material_tratado, material_adquirido, ferramenta)
```

Despois:
```python
                    num_arbores, marco,
                    ano_plantacion, unidades, ciclos, duracion, obxectivo, notas,
                    necesidade_n, necesidade_p, necesidade_k, plan_data, auga_n, auga_p,
                    semente_produto, semente_rexistro,
                    data_fin_sementeira, cantidade_semente, dose_sementeira, densidade,
                    castineiros, abeleiras, nogueiras, amendoeiras, outros_casca,
                    horas_sementeira)
    campos_select = (variedade_oficial, secano, procedencia, anterior, causa_baixa, cobertura)
    casillas = (sementeira_directa, material_tratado, ferramenta)
```

### Paso 74 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            provedor.value = None
```

Despois:
```python
            compra_semente.value = None
```

### Paso 75 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        provedor.value = c.provedor_material_id
        lote_material.value = _texto(c.lote_material)
        pasaporte.value = _texto(c.pasaporte_fitosanitario)
```

Despois:
```python
        compra_semente.value = (c.entrada_semente_id if c.entrada_semente_id
                                in compra_semente.options else None)
```

### Paso 76 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        semente_rexistro.value = _texto(c.semente_tratamento_num_rexistro)
        material_adquirido.value = bool(c.material_adquirido)
        data_adquisicion.value = _texto(c.data_adquisicion_material)
```

Despois:
```python
        semente_rexistro.value = _texto(c.semente_tratamento_num_rexistro)
```

### Paso 77 — crear o ficheiro `tests/services/test_produtos.py`

Contido completo:
```python
"""Produtos e entradas (compras) e as existencias
(docs/superpowers/specs/2026-10-29-produtos-e-entradas-design.md)."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.animais import crear_animal
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.cue import xerar_cue
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
from horta.services.produtos import (
    DatosEntrada,
    crear_entrada,
    crear_produto,
    existencias,
    listar_produtos,
)

HOXE = date(2026, 10, 29)


def _escenario(session):
    version = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="f" * 64, filas=0)
    session.add(version)
    session.flush()
    session.add(CatalogoValor(catalogo="material_fertilizante", codigo="14", descricion="14",
                              version_id=version.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Millo")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.1)
    return ana, horta, quen, cultivo


def test_compra_e_uso_dun_abono(session):
    ana, horta, quen, cultivo = _escenario(session)
    npk = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK 15-15-15", material="14", n_pct=15))
    [produto] = listar_produtos(session, ana, horta.id, tipo="abono")
    coop = crear_contacto(session, ana, horta.id, "Coop. Ulla", "provedor", tipo="entidade")
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=produto.id, data=date(2026, 3, 1), persoa_id=quen.id, provedor_id=coop.id,
        cantidade=25, unidade="kg", albaran_factura="A-1", importe=30), hoxe=HOXE)
    # 200 kg/ha en 0,1 ha: 20 kg
    crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=date(2026, 3, 10), fertilizante_id=npk.id,
        dose=200, unidade="17", entrada_id=compra.id, persoa_id=quen.id), hoxe=HOXE)
    conta = existencias(session, produto)
    assert (conta.entrou, conta.usado, conta.queda, conta.sen_contar) == (25, 20, 5, 0)
    # O CUE colle o provedor e o albará da compra
    [ferti] = xerar_cue(session, ana, horta.id, date(2026, 1, 1),
                        date(2026, 12, 31)).datos["ActividadesExplotacion"]["Fertilizacion"]
    assert ferti["MaterialFertilizante"]["EmpresaSuministradora"] == "Coop. Ulla"
    assert ferti["AplicacionMaterialFertilizante"]["AlbaranFactura"] == "A-1"


def test_a_compra_ten_que_ser_do_mesmo_produto(session):
    ana, horta, quen, cultivo = _escenario(session)
    npk = crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="NPK", material="14"))
    penso = crear_produto(session, ana, horta.id, "penso", "Penso galiñas", "kg")
    compra = crear_entrada(session, ana, DatosEntrada(
        produto_id=penso.id, data=date(2026, 3, 1), persoa_id=quen.id, cantidade=10),
        hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="doutro produto"):
        crear_abonado(session, ana, DatosAbonado(
            cultivo_id=cultivo.id, data_inicio=date(2026, 3, 10), fertilizante_id=npk.id,
            dose=100, unidade="17", entrada_id=compra.id, persoa_id=quen.id), hoxe=HOXE)


def test_medicamento_e_uso_sen_cantidade(session):
    ana, horta, quen, _ = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=quen.id, medicamento="Oxitetraciclina", tempo_espera_dias=7), hoxe=HOXE)
    [medicamento] = listar_produtos(session, ana, horta.id, tipo="medicamento")
    assert medicamento.nome == "Oxitetraciclina"
    # Un uso sen cantidade non se conta: o que queda non é seguro
    assert existencias(session, medicamento).sen_contar == 1


def test_validacions_da_entrada(session):
    ana, horta, quen, _ = _escenario(session)
    penso = crear_produto(session, ana, horta.id, "penso", "Penso", "kg")
    for cambios, erro in (({"cantidade": -1}, "maior que 0"), ({"unidade": "unidades"}, "kg"),
                          ({"data": date(2026, 11, 1)}, "futura"), ({"persoa_id": None}, "quen")):
        datos = {"produto_id": penso.id, "data": date(2026, 3, 1), "persoa_id": quen.id,
                 "cantidade": 10, "unidade": "kg", **cambios}
        with pytest.raises(OperacionNonPermitidaError, match=erro):
            crear_entrada(session, ana, DatosEntrada(**datos), hoxe=HOXE)


def test_diario_e_explotacion_con_compras(session):
    ana, horta, quen, _ = _escenario(session)
    penso = crear_produto(session, ana, horta.id, "penso", "Penso", "kg")
    crear_entrada(session, ana, DatosEntrada(produto_id=penso.id, data=date(2026, 3, 1),
                                             persoa_id=quen.id, cantidade=50), hoxe=HOXE)
    [traballo] = [t for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)
                  if t.tipo == "entrada_produto"]
    assert traballo.que == "Entrada: 50 kg de Penso"
    with pytest.raises(OperacionNonPermitidaError, match="compras"):
        eliminar_horta(session, ana, horta)
```

### Paso 78 — `tests/services/test_fertilizantes.py`

Antes:
```python
from horta.services.persoas import crear_contacto
```

Despois:
```python
from horta.services.produtos import listar_produtos
```

### Paso 79 — `tests/services/test_fertilizantes.py`

Antes:
```python
def test_esterco_pide_provedor(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="de onde veñen"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="Esterco", material="5"))
    casa = crear_contacto(session, ana, horta.id, "Casa do Monte", "provedor",
                          rega="ES150000000009")
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco", material="5", provedor_id=casa.id, n_pct=0.6))
    assert abono.provedor_id == casa.id and casa.ten_papel("provedor")


def test_provedor_doutra_explotacion_non_vale(session):
    ana, horta = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    alleo = crear_contacto(session, ana, outra.id, "Granxa allea", "provedor")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(
            nome="E", material="5", provedor_id=alleo.id))
```

Despois:
```python
def test_o_abono_e_un_produto(session):
    """O abono é un produto da explotación: o provedor vai en cada compra (entrada)."""
    ana, horta = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco", material="5", n_pct=0.6, liquido=True))
    [produto] = listar_produtos(session, ana, horta.id, tipo="abono")
    assert (produto.fertilizante_id, produto.nome, produto.unidade) == (abono.id, "Esterco",
                                                                        "litros")
```

### Paso 80 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
```

Despois:
```python
from horta.services.parcelas import crear_parcela
```

### Paso 81 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
        nome="Compost de alperujo", material="20",
        provedor_id=crear_contacto(session, ana, horta.id, "Planta X", "provedor").id, n_pct=1.5,
```

Despois:
```python
        nome="Compost de alperujo", material="20", n_pct=1.5,
```

### Paso 82 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
            nome="X", material="20",
            provedor_id=crear_contacto(session, ana, horta.id, "Y", "provedor").id, zinc=-1))
```

Despois:
```python
            nome="X", material="20", zinc=-1))
```

### Paso 83 — `tests/services/test_coidados_animais.py`

Antes:
```python
    assert (co.visitante_id, co.matricula, co.medicamento, co.num_animais) == (
```

Despois:
```python
    assert (co.visitante_id, co.matricula, co.produto_id, co.num_animais) == (
```

### Paso 84 — `tests/services/test_cultivos.py`

Antes:
```python
        ({"dose_sementeira_kg_ha": 200, "densidade_plantas_ha": 40000}, "Indica só un"),
        ({"material_adquirido": True}, "data en que se adquiriu"),
```

Despois:
```python
        ({"dose_sementeira_kg_ha": 200, "densidade_plantas_ha": 40000}, "Indica só un"),
```

### Paso 85 — `tests/services/test_persoas_papeis.py`

Antes:
```python
def test_o_medicamento_garda_veterinario_e_provedor(session):
    ana, horta = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    marta = crear_contacto(session, ana, horta.id, "Marta Vázquez", None)
    agrovet = crear_contacto(session, ana, horta.id, "Agrovet Lalín", None)
    [quen] = listar_persoas(session, ana, horta.id, papel="traballador")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=quen.id, medicamento="Oxitetraciclina", tempo_espera_dias=7,
        veterinario_id=marta.id, provedor_id=agrovet.id), hoxe=date(2026, 10, 28))
    assert (co.veterinario_id, co.provedor_id) == (marta.id, agrovet.id)
    # Quedan co papel que fixeron, para atopalos despois en Contactos
    assert marta.papeis == {"veterinario"} and agrovet.papeis == {"provedor"}
```

Despois:
```python
def test_o_medicamento_garda_veterinario(session):
    ana, horta = _escenario(session)
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=10)
    marta = crear_contacto(session, ana, horta.id, "Marta Vázquez", None)
    [quen] = listar_persoas(session, ana, horta.id, papel="traballador")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=quen.id, medicamento="Oxitetraciclina", tempo_espera_dias=7,
        veterinario_id=marta.id), hoxe=date(2026, 10, 28))
    assert co.veterinario_id == marta.id
    # Queda co papel que fixo, para atopalo despois en Contactos
    assert marta.papeis == {"veterinario"}
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produtos (2/3): produtos e compras nos traballos: feito.

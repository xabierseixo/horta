# Tarefa 082e — Persoas (6/11): provedor dos abonos e empresa de servizos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082d. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O provedor do abono é unha persoa da lista; a empresa de servizos é quen fixo o abonado. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/a7d9f1b3c5e0_abonos_provedor_e_servizos.py` (**ficheiro novo**)
- `src/horta/models/abonado.py`
- `src/horta/services/fertilizantes.py`
- `src/horta/services/abonados.py`
- `src/horta/ui/dialogo_abono.py`
- `src/horta/ui/pages/abonados.py`
- `tests/services/test_fertilizantes.py`
- `tests/services/test_caderno_abonos_metais.py`
- `tests/services/test_quen.py`
- `src/horta/services/diario.py`
- `src/horta/services/caderno.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/a7d9f1b3c5e0_abonos_provedor_e_servizos.py`

Contido completo:
```python
"""abonos: o provedor é unha persoa; a empresa de servizos do abonado é quen o fixo

Revision ID: a7d9f1b3c5e0
Revises: f6c8e0a2b4d9
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, persoa_para, primeiro


# revision identifiers, used by Alembic.
revision: str = 'a7d9f1b3c5e0'
down_revision: Union[str, Sequence[str], None] = 'f6c8e0a2b4d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("fertilizante") as batch:
        batch.add_column(sa.Column("provedor_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_fertilizante_provedor_id", "persoa", ["provedor_id"], ["id"])
    conn = op.get_bind()
    pasar_a_persoas(
        conn, "fertilizante", "provedor_id", "provedor",
        "SELECT id, horta_id, provedor_nome, provedor_nif, provedor_rega, provedor_nima "
        "FROM fertilizante",
        nome=lambda f: primeiro(f["provedor_nome"], f["provedor_nif"], f["provedor_rega"],
                                f["provedor_nima"]),
        datos=lambda f: {"nif": f["provedor_nif"], "rega": f["provedor_rega"],
                         "nima": f["provedor_nima"]})
    # A empresa de servizos que fixo o abonado é quen o fixo; se xa había unha persoa,
    # a empresa vai ás notas para non perder o dato
    for f in conn.execute(sa.text(
            "SELECT id, horta_id, persoa_id, notas, empresa_servizos_regfer FROM abonado "
            "WHERE empresa_servizos_regfer IS NOT NULL AND empresa_servizos_regfer != ''")
            ).mappings().all():
        regfer = f["empresa_servizos_regfer"].strip()
        if f["persoa_id"] is None:
            empresa = persoa_para(conn, f["horta_id"], "servizos",
                                  f"Empresa de servizos (REGFER {regfer})", tipo="entidade",
                                  regfer_numero=regfer)
            conn.execute(sa.text("UPDATE abonado SET persoa_id = :p WHERE id = :i"),
                         {"p": empresa, "i": f["id"]})
        else:
            notas = " · ".join(x for x in (f["notas"], f"Empresa de servizos: REGFER {regfer}")
                               if x)
            conn.execute(sa.text("UPDATE abonado SET notas = :n WHERE id = :i"),
                         {"n": notas[:1000], "i": f["id"]})
    with op.batch_alter_table("fertilizante") as batch:
        for columna in ("provedor_nome", "provedor_nif", "provedor_rega", "provedor_nima"):
            batch.drop_column(columna)
    with op.batch_alter_table("abonado") as batch:
        batch.drop_column("empresa_servizos_regfer")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("abonado") as batch:
        batch.add_column(sa.Column("empresa_servizos_regfer", sa.String(50), nullable=True))
    with op.batch_alter_table("fertilizante") as batch:
        batch.add_column(sa.Column("provedor_nome", sa.String(150), nullable=True))
        batch.add_column(sa.Column("provedor_nif", sa.String(14), nullable=True))
        batch.add_column(sa.Column("provedor_rega", sa.String(14), nullable=True))
        batch.add_column(sa.Column("provedor_nima", sa.String(50), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE fertilizante SET (provedor_nome, provedor_nif, provedor_rega, provedor_nima) = "
        "(SELECT nome, nif, rega, nima FROM persoa WHERE persoa.id = fertilizante.provedor_id)"))
    conn.execute(sa.text(
        "UPDATE abonado SET empresa_servizos_regfer = (SELECT regfer_numero FROM persoa p "
        "JOIN persoa_papel pp ON pp.persoa_id = p.id WHERE p.id = abonado.persoa_id "
        "AND pp.papel = 'servizos')"))
    with op.batch_alter_table("fertilizante") as batch:
        batch.drop_constraint("fk_fertilizante_provedor_id", type_="foreignkey")
        batch.drop_column("provedor_id")
```

### Paso 2 — `src/horta/models/abonado.py`

Antes:
```python
    provedor_nome: Mapped[str | None] = mapped_column(String(150), default=None)
    provedor_nif: Mapped[str | None] = mapped_column(String(14), default=None)
    provedor_rega: Mapped[str | None] = mapped_column(String(14), default=None)
    provedor_nima: Mapped[str | None] = mapped_column(String(50), default=None)
```

Despois:
```python
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

### Paso 3 — `src/horta/models/abonado.py`

Antes:
```python
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
    empresa_servizos_regfer: Mapped[str | None] = mapped_column(String(50), default=None)
```

Despois:
```python
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
```

### Paso 4 — `src/horta/services/fertilizantes.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import persoa_co_papel
```

### Paso 5 — `src/horta/services/fertilizantes.py`

Antes:
```python
    provedor_nome: str | None = None
    provedor_nif: str | None = None
    provedor_rega: str | None = None
    provedor_nima: str | None = None


def _validar(session: Session, datos: DatosFertilizante) -> None:
```

Despois:
```python
    # De onde vén: persoa ou entidade co papel «provedor» (co seu NIF, REGA ou NIMA)
    provedor_id: int | None = None


def _validar(session: Session, horta_id: int, datos: DatosFertilizante) -> None:
```

### Paso 6 — `src/horta/services/fertilizantes.py`

Antes:
```python
    identificadores = [x for x in (datos.provedor_nif, datos.provedor_rega, datos.provedor_nima)
                       if x]
    if len(identificadores) > 1:
        raise OperacionNonPermitidaError("Do provedor indica só un: NIF, REGA ou NIMA")
    if datos.material in ESTERCOS | RESIDUOS and not (datos.provedor_nome or "").strip():
```

Despois:
```python
    persoa_co_papel(session, horta_id, datos.provedor_id, "provedor")
    if datos.material in ESTERCOS | RESIDUOS and datos.provedor_id is None:
```

### Paso 7 — `src/horta/services/fertilizantes.py`

Antes:
```python
    _validar(session, datos)
```

Despois:
```python
    _validar(session, horta_id, datos)
```

### Paso 8 — `src/horta/services/abonados.py`

Antes:
```python
    horas: float | None = None
    empresa_servizos_regfer: str | None = None
```

Despois:
```python
    horas: float | None = None
```

### Paso 9 — `src/horta/services/abonados.py`

Antes:
```python
    # Se o fixo unha empresa de servizos, a persoa pode non ser do equipo
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas,
                   obrigatoria=not datos.empresa_servizos_regfer)
```

Despois:
```python
    # Quen o fixo pode ser unha persoa do equipo ou a empresa de servizos (co seu REGFER)
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

### Paso 10 — `src/horta/services/abonados.py`

Antes:
```python
    abonado.horas = datos.horas
    abonado.empresa_servizos_regfer = datos.empresa_servizos_regfer or None
```

Despois:
```python
    abonado.horas = datos.horas
```

### Paso 11 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

_IDENTIFICADORES = {"provedor_nif": "NIF", "provedor_rega": "REGA", "provedor_nima": "NIMA"}
```

Despois:
```python
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

```

### Paso 12 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
        with ui.column().classes("w-full") as provedor:
            provedor_nome = ui.input("De onde vén (casa, granxa ou empresa)").classes("w-full")
            with ui.row().classes("w-full no-wrap"):
                tipo_id = ui.select(_IDENTIFICADORES, value="provedor_nif",
                                    label="Identificador").classes("col")
                ident = ui.input("Número (opcional)").classes("col")
            tratamento = ui.select(tratamentos, label="Tratamento do esterco (opcional)",
                                   clearable=True).classes("w-full")
        provedor.bind_visibility_from(material, "value",
                                      backward=lambda v: v in ESTERCOS | RESIDUOS)
```

Despois:
```python
        # De onde vén (empresa subministradora, granxa ou casa): obrigatorio nos estercos e
        # residuos; os seus NIF, REGA ou NIMA van na súa ficha de Persoas
        provedor = CampoPersoa(horta_id, "provedor", "De onde vén (empresa, granxa ou casa)")
        tratamento = ui.select(tratamentos, label="Tratamento do esterco (opcional)",
                               clearable=True).classes("w-full")
        tratamento.bind_visibility_from(material, "value", backward=lambda v: v in ESTERCOS)
```

### Paso 13 — `src/horta/ui/dialogo_abono.py`

Antes:
```python
                if datos.material in ESTERCOS | RESIDUOS:
                    datos.provedor_nome = provedor_nome.value or None
                    if ident.value:
                        setattr(datos, tipo_id.value, ident.value)
```

Despois:
```python
                datos.provedor_id = provedor.value
                if datos.material in ESTERCOS:
```

### Paso 14 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from horta.services.persoas import listar_persoas
```

Despois:
```python
from horta.services.persoas import listar_quen
```

### Paso 15 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 16 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        aplicador = ui.select(persoas, label="Quen o botou", clearable=True).classes("w-full")
```

Despois:
```python
        aplicador = ui.select(persoas, label="Quen o botou (persoa ou empresa de servizos)",
                              clearable=True).classes("w-full")
```

### Paso 17 — `src/horta/ui/pages/abonados.py`

Antes:
```python
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            empresa = ui.input("REGFER da empresa de servizos (se o fixo unha)").classes(
                "w-full")
```

Despois:
```python
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
```

### Paso 18 — `src/horta/ui/pages/abonados.py`

Antes:
```python
                        maquina_id=maquina.value, empresa_servizos_regfer=empresa.value or None,
```

Despois:
```python
                        maquina_id=maquina.value,
```

### Paso 19 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        maquina.value = a.maquina_id if a else None
        empresa.value = (a.empresa_servizos_regfer or "") if a else ""
```

Despois:
```python
        maquina.value = a.maquina_id if a else None
```

### Paso 20 — `tests/services/test_fertilizantes.py`

Antes:
```python
from horta.services.hortas import crear_horta
```

Despois:
```python
from horta.services.hortas import crear_horta
from horta.services.persoas import crear_contacto
```

### Paso 21 — `tests/services/test_fertilizantes.py`

Antes:
```python
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco", material="5", provedor_nome="Casa", n_pct=0.6))
    assert abono.provedor_nome == "Casa"


def test_so_un_identificador_do_provedor(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="só un"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(
            nome="E", material="5", provedor_nome="X", provedor_nif="1", provedor_rega="2"))
```

Despois:
```python
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

### Paso 22 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
```

### Paso 23 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
        nome="Compost de alperujo", material="20", provedor_nome="Planta X", n_pct=1.5,
```

Despois:
```python
        nome="Compost de alperujo", material="20",
        provedor_id=crear_contacto(session, ana, horta.id, "Planta X", "provedor").id, n_pct=1.5,
```

### Paso 24 — `tests/services/test_caderno_abonos_metais.py`

Antes:
```python
            nome="X", material="20", provedor_nome="Y", zinc=-1))
```

Despois:
```python
            nome="X", material="20",
            provedor_id=crear_contacto(session, ana, horta.id, "Y", "provedor").id, zinc=-1))
```

### Paso 25 — `tests/services/test_quen.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto, listar_quen
```

### Paso 26 — `tests/services/test_quen.py`

Antes:
```python
def test_abonado_dunha_empresa_de_servizos_sen_persoa(session):
    ana, horta, _, cultivo = _escenario(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id,
        empresa_servizos_regfer="ES1234"), hoxe=HOXE)
    assert abonado.persoa_id is None
```

Despois:
```python
def test_abonado_dunha_empresa_de_servizos(session):
    """Quen o fixo pode ser a empresa de servizos (co seu REGFER), e sae en «Quen o fixo»."""
    ana, horta, _, cultivo = _escenario(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost", material="13"))
    empresa = crear_contacto(session, ana, horta.id, "Abonos Ulla SL", "servizos",
                             tipo="entidade", regfer_numero="ES1234")
    abonado = crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id,
        persoa_id=empresa.id), hoxe=HOXE)
    assert abonado.persoa_id == empresa.id
    assert empresa in listar_quen(session, ana, horta.id)
```

### Paso 27 — `src/horta/services/diario.py`

Antes:
```python
            sen_quen=not quen and not a.empresa_servizos_regfer))
```

Despois:
```python
            sen_quen=not quen))
```

### Paso 28 — `src/horta/services/caderno.py`

Antes:
```python
    persoas = session.query(Persoa).filter_by(horta_id=horta_id).order_by(Persoa.id).all()
```

Despois:
```python
    persoas = session.query(Persoa).filter_by(horta_id=horta_id).order_by(Persoa.id).all()
    persoas_por_id = {p.id: p for p in persoas}
```

### Paso 29 — `src/horta/services/caderno.py`

Antes:
```python
        maquina = session.get(Maquina, ab.maquina_id) if ab.maquina_id else None
        filas_fert.append([
            _intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(ab.cultivo_id, ""),
            ({SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
                p.secano_regadio, "") if p and p.secano_regadio else ""),
            c.especie if c else "", _num(ab.superficie_ha),
            describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion)
            if ab.tipo_fertilizacion else "",
            describir(session, "material_fertilizante", fe.material) if fe else
            "Abonado en verde",
            fe.nome if fe else "", (fe.provedor_nome or "") if fe else "",
            (fe.provedor_rega or fe.provedor_nif or fe.provedor_nima or "") if fe else "",
            describir(session, "metodo_fertilizacion", ab.metodo) if ab.metodo else "",
            maquina.alias if maquina else "",
            ab.empresa_servizos_regfer or ((persoa.regfer_numero or "") if persoa else ""),
```

Despois:
```python
        provedor = persoas_por_id.get(fe.provedor_id or 0) if fe else None
        maquina = session.get(Maquina, ab.maquina_id) if ab.maquina_id else None
        filas_fert.append([
            _intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(ab.cultivo_id, ""),
            ({SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
                p.secano_regadio, "") if p and p.secano_regadio else ""),
            c.especie if c else "", _num(ab.superficie_ha),
            describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion)
            if ab.tipo_fertilizacion else "",
            describir(session, "material_fertilizante", fe.material) if fe else
            "Abonado en verde",
            fe.nome if fe else "", nome_completo(provedor),
            (provedor.rega or provedor.nif or provedor.nima or "") if provedor else "",
            describir(session, "metodo_fertilizacion", ab.metodo) if ab.metodo else "",
            maquina.alias if maquina else "",
            (persoa.regfer_numero or "") if persoa else "",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (6/11): provedor dos abonos e empresa de servizos: feito.

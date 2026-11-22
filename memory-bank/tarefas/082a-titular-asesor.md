# Tarefa 082a — Persoas (2/11): titular e asesor nun só sitio

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O titular, o representante e a entidade de asesoramento son persoas con ese papel; Datos da explotación nunha soa xanela. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/d4a6c8e0f2b7_titular_e_asesor_persoas.py` (**ficheiro novo**)
- `src/horta/models/horta.py`
- `src/horta/ui/pages/horta_detalle.py`
- `tests/services/test_hortas.py`
- `src/horta/services/en_regra.py`
- `tests/services/test_en_regra.py`
- `tests/services/test_caderno_datos.py`
- `src/horta/services/caderno.py`
- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/d4a6c8e0f2b7_titular_e_asesor_persoas.py`

Contido completo:
```python
"""o titular e a entidade de asesoramento da explotación pasan a ser persoas con ese papel

Revision ID: d4a6c8e0f2b7
Revises: c3f5a7b9d1e6
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import persoa_para


# revision identifiers, used by Alembic.
revision: str = 'd4a6c8e0f2b7'
down_revision: Union[str, Sequence[str], None] = 'c3f5a7b9d1e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNAS = (("titular_nome", sa.String(200)), ("titular_nif", sa.String(9)),
             ("asesoramento_nome", sa.String(200)), ("asesoramento_nif", sa.String(14)),
             ("asesoramento_num", sa.String(50)))


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for h in conn.execute(sa.text(
            "SELECT id, titular_nome, titular_nif, asesoramento_nome, asesoramento_nif, "
            "asesoramento_num FROM horta")).mappings().all():
        if h["titular_nome"] or h["titular_nif"]:
            titular = conn.execute(sa.text(
                "SELECT p.id, p.nif FROM persoa p JOIN persoa_papel pp ON pp.persoa_id = p.id "
                "WHERE p.horta_id = :h AND pp.papel = 'titular' AND p.activa"),
                {"h": h["id"]}).first()
            if titular is None:
                persoa_para(conn, h["id"], "titular", h["titular_nome"] or "Titular",
                            nif=h["titular_nif"])
            elif not titular.nif and h["titular_nif"]:
                conn.execute(sa.text("UPDATE persoa SET nif = :n WHERE id = :i"),
                             {"n": h["titular_nif"], "i": titular.id})
        if h["asesoramento_nome"] or h["asesoramento_nif"] or h["asesoramento_num"]:
            persoa_para(conn, h["id"], "asesor", h["asesoramento_nome"] or "Asesoramento",
                        nif=h["asesoramento_nif"], tipo="entidade",
                        num_asesoramento=h["asesoramento_num"])
    with op.batch_alter_table("horta") as batch:
        for columna, _ in _COLUMNAS:
            batch.drop_column(columna)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("horta") as batch:
        for columna, tipo in _COLUMNAS:
            batch.add_column(sa.Column(columna, tipo, nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE horta SET (titular_nome, titular_nif) = (SELECT p.nome, p.nif FROM persoa p "
        "JOIN persoa_papel pp ON pp.persoa_id = p.id WHERE p.horta_id = horta.id "
        "AND pp.papel = 'titular' LIMIT 1)"))
    conn.execute(sa.text(
        "UPDATE horta SET (asesoramento_nome, asesoramento_nif, asesoramento_num) = "
        "(SELECT p.nome, p.nif, p.num_asesoramento FROM persoa p JOIN persoa_papel pp "
        "ON pp.persoa_id = p.id WHERE p.horta_id = horta.id AND pp.papel = 'asesor' "
        "AND p.tipo = 'entidade' LIMIT 1)"))
```

### Paso 2 — `src/horta/models/horta.py`

Antes:
```python
    titular_nome: Mapped[str | None] = mapped_column(String(200), default=None)
    titular_nif: Mapped[str | None] = mapped_column(String(9), default=None)
```

Despois:
```python
    # O titular, o representante e o asesor son persoas con ese papel (services.persoas)
```

### Paso 3 — `src/horta/models/horta.py`

Antes:
```python
    tipo_representacion: Mapped[str | None] = mapped_column(String(100), default=None)
    asesoramento_nome: Mapped[str | None] = mapped_column(String(200), default=None)
    asesoramento_nif: Mapped[str | None] = mapped_column(String(14), default=None)
    asesoramento_num: Mapped[str | None] = mapped_column(String(50), default=None)
```

Despois:
```python
    tipo_representacion: Mapped[str | None] = mapped_column(String(100), default=None)
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    actualizar_horta,
    comprobar_rol_horta,
    eliminar_horta,
    estado_rexistro,
    listar_hortas_usuario,
)
from horta.services.parcelas import (
    listar_parcelas,
)
```

Despois:
```python
    TIPOS_XIP,
    actualizar_horta,
    comprobar_rol_horta,
    eliminar_horta,
    estado_rexistro,
    listar_hortas_usuario,
)
from horta.services.parcelas import (
    listar_parcelas,
)
from horta.services.persoas import nome_completo, titular_da_horta
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.dialogo_datos_caderno import boton_datos_caderno
```

Despois:
```python
from horta.ui.confirmacion import confirmar_eliminacion
```

### Paso 6 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
```

Despois:
```python
_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
# Datos da explotación para o caderno da Xunta (1.1)
_DATOS_CADERNO = (("enderezo", "Enderezo"), ("localidade", "Localidade"),
                  ("codigo_postal", "Código postal"), ("provincia", "Provincia"),
                  ("email", "Email"),
                  ("tipo_representacion", "Tipo de representación (se asina un representante)"))
```

### Paso 7 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        horta_titular_nome = horta.titular_nome or ""
        horta_titular_nif = horta.titular_nif or ""
        horta_codigo_reaga = horta.codigo_reaga or ""
        horta_codigo_rega = horta.codigo_rega or ""
        estado = estado_rexistro(horta)
```

Despois:
```python
        datos_horta = {campo: getattr(horta, campo) or "" for campo, _ in _DATOS_CADERNO}
        horta_tipo_xip = horta.tipo_xip
        horta_fertilizacion = horta.asesoramento_fertilizacion
        titular = titular_da_horta(session, horta_id)
        nome_titular = nome_completo(titular)
        horta_codigo_reaga = horta.codigo_reaga or ""
        horta_codigo_rega = horta.codigo_rega or ""
        estado = estado_rexistro(session, horta)
```

### Paso 8 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        with ui.dialog() as dialog_config_horta, ui.card():
            ui.label("Configurar explotación").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome).classes("w-full")
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "").classes(
                "w-full"
            )
            ui.label("Tipo de explotación").classes("text-caption texto-suave")
            tipo_radio = ui.radio(
                {True: "Profesional", False: "Non profesional"}, value=horta_uso_profesional
            ).props("inline")
            with ui.column().classes("w-full gap-1").bind_visibility_from(tipo_radio, "value"):
                titular_nome_input = ui.input(
                    "Titular (nome ou razón social)", value=horta_titular_nome
                ).classes("w-full")
                titular_nif_input = ui.input("NIF do titular", value=horta_titular_nif).classes(
                    "w-full"
                )
                reaga_input = ui.input(
                    "Nº REAGA (ES + 12 díxitos)", value=horta_codigo_reaga
                ).classes("w-full")
            rega_input = ui.input(
                "Nº REGA, se ten animais (ES + 12 díxitos)", value=horta_codigo_rega
            ).classes("w-full")
```

Despois:
```python
        with ui.dialog() as dialog_config_horta, ui.card().style("width: min(36rem, 94vw)"):
            ui.label("Datos da explotación").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome).classes("w-full")
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "").classes(
                "w-full"
            )
            ui.label("Tipo de explotación").classes("text-caption texto-suave")
            tipo_radio = ui.radio(
                {True: "Profesional", False: "Non profesional"}, value=horta_uso_profesional
            ).props("inline")
            with ui.column().classes("w-full gap-1").bind_visibility_from(tipo_radio, "value"):
                reaga_input = ui.input(
                    "Nº REAGA (ES + 12 díxitos)", value=horta_codigo_reaga
                ).classes("w-full")
            rega_input = ui.input(
                "Nº REGA, se ten animais (ES + 12 díxitos)", value=horta_codigo_rega
            ).classes("w-full")
            # Caderno da Xunta 1.1 e 1.4. O titular, o representante e o asesor son persoas
            with ui.expansion("Datos para o caderno").classes("w-full"):
                datos_inputs = {campo: ui.input(etiqueta, value=datos_horta[campo]).classes(
                    "w-full") for campo, etiqueta in _DATOS_CADERNO}
                tipo_xip_input = ui.select(
                    TIPOS_XIP, label="Xestión integrada de pragas (XIP)", clearable=True,
                    value=horta_tipo_xip).classes("w-full")
                fertilizacion_input = ui.checkbox("Recibe asesoramento en fertilización",
                                                  value=horta_fertilizacion)
            ui.label("O titular, o representante e o asesor indícanse en Persoas.").classes(
                "text-caption texto-suave")
```

### Paso 9 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                            titular_nome=titular_nome_input.value or None,
                            titular_nif=titular_nif_input.value or None,
```

Despois:
```python
                            tipo_xip=tipo_xip_input.value,
                            asesoramento_fertilizacion=fertilizacion_input.value,
                            **{c: (i.value or None) for c, i in datos_inputs.items()},
```

### Paso 10 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        with ui.row().classes("gap-2"):
            ui.button("Configurar explotación", icon="settings",
                      on_click=dialog_config_horta.open).props("outline")
            boton_datos_caderno(horta_id)
```

Despois:
```python
        ui.label(f"Titular: {nome_titular}" if nome_titular
                 else "Aínda non se indicou o titular").classes("q-mb-sm")
        with ui.row().classes("gap-2"):
            ui.button("Editar datos da explotación", icon="settings",
                      on_click=dialog_config_horta.open).props("outline")
            ui.button("Titular e asesor en Persoas", icon="groups", on_click=lambda: ui.navigate.to(
                url_seccion(horta_id, "equipo"))).props("outline")
```

### Paso 11 — `tests/services/test_hortas.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
```

### Paso 12 — `tests/services/test_hortas.py`

Antes:
```python
    assert estado_rexistro(horta) == "non_profesional"
    actualizar_horta(session, ana, horta, uso_profesional=True)
    assert estado_rexistro(horta) == "en_preparacion"
    actualizar_horta(
        session, ana, horta, titular_nif="12345678z", codigo_reaga="es 150010000001"
    )
    assert horta.titular_nif == "12345678Z"
    assert horta.codigo_reaga == "ES150010000001"
    assert estado_rexistro(horta) == "rexistrada"
```

Despois:
```python
    assert estado_rexistro(session, horta) == "non_profesional"
    actualizar_horta(session, ana, horta, uso_profesional=True)
    assert estado_rexistro(session, horta) == "en_preparacion"
    actualizar_horta(session, ana, horta, codigo_reaga="es 150010000001")
    assert horta.codigo_reaga == "ES150010000001"
    assert estado_rexistro(session, horta) == "en_preparacion"
    # O NIF do titular está na persoa co papel titular
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="12345678z")
    assert estado_rexistro(session, horta) == "rexistrada"
```

### Paso 13 — `tests/services/test_hortas.py`

Antes:
```python
    with pytest.raises(OperacionNonPermitidaError, match="NIF do titular"):
        actualizar_horta(session, ana, horta, titular_nif="ABC")
```

Despois:
```python
    with pytest.raises(OperacionNonPermitidaError, match="NIF"):
        crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="ABC")
```

### Paso 14 — `src/horta/services/en_regra.py`

Antes:
```python
from horta.services.persoas import con_papel, ropo_vixente
```

Despois:
```python
from horta.services.persoas import con_papel, ropo_vixente, titular_da_horta
```

### Paso 15 — `src/horta/services/en_regra.py`

Antes:
```python
    requisitos = [
        Requisito(
            "NIF do titular",
            bool(horta.titular_nif),
            "Indícao en «Configurar explotación».",
```

Despois:
```python
    titular = titular_da_horta(session, horta.id)
    requisitos = [
        Requisito(
            "NIF do titular",
            bool(titular and titular.nif),
            "Indica en «Persoas» quen é o titular e o seu NIF.",
```

### Paso 16 — `tests/services/test_en_regra.py`

Antes:
```python
    actualizar_horta(session, ana, horta, titular_nif="12345678Z", codigo_reaga="ES150010000001")
```

Despois:
```python
    actualizar_horta(session, ana, horta, codigo_reaga="ES150010000001")
    # O NIF do titular está na persoa co papel titular
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="12345678Z")
```

### Paso 17 — `tests/services/test_caderno_datos.py`

Antes:
```python
                     asesoramento_nome="ATRIA Ulloa", asesoramento_fertilizacion=True)
```

Despois:
```python
                     asesoramento_fertilizacion=True)
    # A entidade de asesoramento (caderno 1.4) é unha persoa co papel asesor
    crear_persoa(session, ana, horta.id, "ATRIA Ulloa", papeis={"asesor"}, tipo="entidade",
                 num_asesoramento="AT-7")
```

### Paso 18 — `tests/services/test_caderno_datos.py`

Antes:
```python
    assert ["ATRIA Ulloa", "AS"] in filas
```

Despois:
```python
    assert ["ATRIA Ulloa", "AT-7", "AS"] in filas
```

### Paso 19 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.labores import DESBROCE, PODAS, listar_labores
```

Despois:
```python
from horta.services.labores import DESBROCE, PODAS, listar_labores
from horta.services.persoas import nome_completo
```

### Paso 20 — `src/horta/services/caderno.py`

Antes:
```python
    cab = (f"Explotación/Titular da explotación: {horta.nome} / "
           f"{horta.titular_nome or (titular.nome if titular else '')}   "
```

Despois:
```python
    # Titular ou representante (1.1): se o titular é unha entidade, quen a representa
    representante = titular if titular is None or titular.tipo == "persoa" else next(
        (p for p in persoas if p.activa and p.ten_papel("representante")), None)
    asesoria = next((p for p in persoas if p.activa and p.ten_papel("asesor")
                     and (p.tipo == "entidade" or p.num_asesoramento)), None)
    cab = (f"Explotación/Titular da explotación: {horta.nome} / {nome_completo(titular)}   "
```

### Paso 21 — `src/horta/services/caderno.py`

Antes:
```python
        ["Nome e apelidos ou razón social", horta.titular_nome or horta.nome],
        ["NIF", horta.titular_nif or (titular.nif if titular else "")],
        ["CEA/Nº de Rexistro da Explotación", horta.codigo_reaga or ""],
        ["Código REGA", horta.codigo_rega or ""],
        ["Dirección", horta.enderezo or ""],
        ["Localidade", horta.localidade or ""],
        ["C. Postal", horta.codigo_postal or ""],
        ["Provincia", horta.provincia or ""],
        ["Teléfono", horta.telefono or ""],
        ["e-mail", horta.email or ""],
        [],
        ["TITULAR OU REPRESENTANTE DA EXPLOTACIÓN"],
        ["Nome e apelidos", " ".join(x for x in (titular.nome, titular.apelidos or "")
                                     if x) if titular else ""],
        ["NIF", (titular.nif or "") if titular else ""],
        ["Dirección", (titular.enderezo or "") if titular else ""],
        ["Localidade", (titular.localidade or "") if titular else ""],
        ["C. Postal", (titular.codigo_postal or "") if titular else ""],
        ["Provincia", (titular.provincia or "") if titular else ""],
        ["Tipo de representación", horta.tipo_representacion or ""],
        ["Teléfono", (titular.telefono or "") if titular else ""],
        ["e-mail", (titular.email or "") if titular else ""],
```

Despois:
```python
        ["Nome e apelidos ou razón social", nome_completo(titular) or horta.nome],
        ["NIF", (titular.nif or "") if titular else ""],
        ["CEA/Nº de Rexistro da Explotación", horta.codigo_reaga or ""],
        ["Código REGA", horta.codigo_rega or ""],
        ["Dirección", horta.enderezo or ""],
        ["Localidade", horta.localidade or ""],
        ["C. Postal", horta.codigo_postal or ""],
        ["Provincia", horta.provincia or ""],
        ["Teléfono", horta.telefono or ""],
        ["e-mail", horta.email or ""],
        [],
        ["TITULAR OU REPRESENTANTE DA EXPLOTACIÓN"],
        ["Nome e apelidos", nome_completo(representante)],
        ["NIF", (representante.nif or "") if representante else ""],
        ["Dirección", (representante.enderezo or "") if representante else ""],
        ["Localidade", (representante.localidade or "") if representante else ""],
        ["C. Postal", (representante.codigo_postal or "") if representante else ""],
        ["Provincia", (representante.provincia or "") if representante else ""],
        ["Tipo de representación", horta.tipo_representacion or ""],
        ["Teléfono", (representante.telefono or "") if representante else ""],
        ["e-mail", (representante.email or "") if representante else ""],
```

### Paso 22 — `src/horta/services/caderno.py`

Antes:
```python
        [horta.asesoramento_nome or "", horta.asesoramento_nif or "",
         horta.asesoramento_num or "", horta.tipo_xip or ""],
```

Despois:
```python
        [nome_completo(asesoria), (asesoria.nif or "") if asesoria else "",
         (asesoria.num_asesoramento or "") if asesoria else "", horta.tipo_xip or ""],
```

### Paso 23 — `src/horta/services/hortas.py`

Antes:
```python
        "titular_nome",
        "titular_nif",
        "codigo_reaga",
        "codigo_rega",
        "enderezo",
        "localidade",
        "codigo_postal",
        "provincia",
        "email",
        "tipo_representacion",
        "asesoramento_nome",
        "asesoramento_nif",
        "asesoramento_num",
        "tipo_xip",
        "asesoramento_fertilizacion",
    }
)
# Tipo de explotación en xestión integrada de pragas (modelo do caderno, 1.4)
TIPOS_XIP = {"AE": "Agricultura ecolóxica", "PI": "Produción integrada",
             "CP": "Certificación privada", "ATRIA": "Agrupación de tratamento integrado (ATRIA)",
             "AS": "Asistida por un asesor", "NO": "Sen obriga de asesor en XIP"}

# Patróns do descritor SIEX (Anexo VI): NIF/NIE de persoa física e CIF; código de
# explotación ES + 12 díxitos (codigoREA). O REGA segue o mesmo formato.
_PATRON_NIF = re.compile(
    r"^([KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]|[A-HJ-NP-SUVW]\d{7}[0-9A-J])$"
)
_PATRON_CODIGO = re.compile(r"^ES\d{12}$")


def _normalizar_e_validar_codigos(cambios: dict[str, Any]) -> None:
    for campo in ("titular_nif", "codigo_reaga", "codigo_rega"):
        if cambios.get(campo):
            cambios[campo] = cambios[campo].strip().upper().replace(" ", "")
        elif campo in cambios:
            cambios[campo] = None
    if cambios.get("tipo_xip") and cambios["tipo_xip"] not in TIPOS_XIP:
        raise OperacionNonPermitidaError("Tipo de explotación en XIP descoñecido")
    if cambios.get("titular_nif") and not _PATRON_NIF.match(cambios["titular_nif"]):
        raise OperacionNonPermitidaError("O NIF do titular non é válido")
    for campo, nome in (("codigo_reaga", "REAGA"), ("codigo_rega", "REGA")):
        if cambios.get(campo) and not _PATRON_CODIGO.match(cambios[campo]):
            raise OperacionNonPermitidaError(
                f"O código {nome} debe ter o formato ES seguido de 12 díxitos"
            )


def estado_rexistro(horta: Horta) -> str:
    """non_profesional | en_preparacion | rexistrada (calculado, non gardado)."""
    if not horta.uso_profesional:
        return "non_profesional"
    if horta.titular_nif and horta.codigo_reaga:
```

Despois:
```python
        "codigo_reaga",
        "codigo_rega",
        "enderezo",
        "localidade",
        "codigo_postal",
        "provincia",
        "email",
        "tipo_representacion",
        "tipo_xip",
        "asesoramento_fertilizacion",
    }
)
# Tipo de explotación en xestión integrada de pragas (modelo do caderno, 1.4)
TIPOS_XIP = {"AE": "Agricultura ecolóxica", "PI": "Produción integrada",
             "CP": "Certificación privada", "ATRIA": "Agrupación de tratamento integrado (ATRIA)",
             "AS": "Asistida por un asesor", "NO": "Sen obriga de asesor en XIP"}

# Patróns do descritor SIEX (Anexo VI): NIF/NIE de persoa física e CIF (aínda o usa o NIF do
# arrendador das parcelas); código de explotación ES + 12 díxitos (codigoREA).
_PATRON_NIF = re.compile(
    r"^([KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]|[A-HJ-NP-SUVW]\d{7}[0-9A-J])$"
)
_PATRON_CODIGO = re.compile(r"^ES\d{12}$")


def _normalizar_e_validar_codigos(cambios: dict[str, Any]) -> None:
    for campo in ("codigo_reaga", "codigo_rega"):
        if cambios.get(campo):
            cambios[campo] = cambios[campo].strip().upper().replace(" ", "")
        elif campo in cambios:
            cambios[campo] = None
    if cambios.get("tipo_xip") and cambios["tipo_xip"] not in TIPOS_XIP:
        raise OperacionNonPermitidaError("Tipo de explotación en XIP descoñecido")
    for campo, nome in (("codigo_reaga", "REAGA"), ("codigo_rega", "REGA")):
        if cambios.get(campo) and not _PATRON_CODIGO.match(cambios[campo]):
            raise OperacionNonPermitidaError(
                f"O código {nome} debe ter o formato ES seguido de 12 díxitos"
            )


def estado_rexistro(session: Session, horta: Horta) -> str:
    """non_profesional | en_preparacion | rexistrada (calculado, non gardado): rexistrada se
    ten REAGA e o titular (a persoa co papel titular) ten NIF."""
    if not horta.uso_profesional:
        return "non_profesional"
    nif_titular = (session.query(Persoa.nif).join(PersoaPapel)
                   .filter(Persoa.horta_id == horta.id, Persoa.activa.is_(True),
                           PersoaPapel.papel == "titular").scalar())
    if nif_titular and horta.codigo_reaga:
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (2/11): titular e asesor nun só sitio: feito.

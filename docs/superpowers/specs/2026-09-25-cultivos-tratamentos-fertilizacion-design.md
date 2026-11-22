# Deseño: Cultivos, Tratamentos e Fertilización

## Contexto

A app leva dúas iteracións de melloras (Robustez, Busca/filtros/paxinación) sobre entidades periféricas (usuarios, hortas, parcelas, animais), pero aínda non ten as entidades centrais que o README §23 ("primeira versión") define coma obxectivo: Cultivos e Tarefas. Sen elas, a app non cumpre o seu propósito — ser unha base de coñecemento estruturada do que se fixo, onde, cando e con que resultados (README §1).

Esta spec cobre **Cultivos**, decidido coma primeiro dos dous subproxectos que faltan (o segundo, Tarefas + Dashboard, depende de que Cultivos exista — unha tarefa pode ligarse a un cultivo concreto, §8).

Amplíase o alcance inicial de "Cultivos" para incluír **Tratamentos** e **Fertilización** na mesma spec: o README §22 xa indicaba que os tratamentos fitosanitarios "se modelan cando se implemente esa funcionalidade en Cultivos", e o usuario confirmou explicitamente que quere construír xa as tres entidades xuntas en vez de deixar tratamentos/fertilización para despois.

## Obxectivo

1. Rexistrar Cultivos ligados a unha Parcela (especie, variedade, datas do ciclo, cantidade/unidade, estado, notas).
2. Rexistrar Tratamentos fitosanitarios ligados a un Cultivo, cos campos esixidos polo Anexo III do RD 1311/2012 e a Orde APA/204/2023 (praga, produto, dose, eficacia, aplicador, equipo aplicador, persoas de asesoramento).
3. Rexistrar Fertilizacións ligadas a un Cultivo, cos campos do mesmo marco normativo (tipo, produto, N/P/K, carbono orgánico, micronutrientes, asesoramento recibido).
4. Tratamentos e Fertilizacións nunca se borran fisicamente — baixa lóxica, para poder cumprir a conservación mínima de 3 anos esixida pola normativa cando aplique.
5. Estas tres entidades seguen o mesmo patrón xa establecido (modelo SQLAlchemy, servizo con permisos, pestana na páxina da horta con busca/filtro/paxinación) que Parcelas/Animais/Membros.

## Fóra de alcance

- **Tarefas + Dashboard con datos reais**: segundo subproxecto, depende deste. Brainstorming propio despois.
- **Colleitas (§11)** coma entidade independente con múltiples rexistros de colleita por cultivo (varias datas + cantidades, coma no exemplo do README): Cultivo xa ten un campo `data_colleita_real` único, que cobre o caso simple. A entidade Colleitas completa (rexistro múltiple, estatísticas de produción) queda para unha fase posterior, tal e como xa indicaba o §23.
- **Xeración do caderno de explotación** (exportar PDF/Excel por horta e ano, README §22 "Xeración do caderno"): é o paso natural seguinte unha vez que existan datos reais de Cultivos/Tratamentos/Fertilización que exportar — **non se esquece, é o obxectivo final desta liña de traballo**, pero require estas tres entidades xa creadas e con datos, así que vai despois nunha spec propia.
- Decidir se a exportación do caderno inclúe ou non os rexistros dados de baixa: cuestión a resolver cando se deseñe esa exportación, non agora.
- A nota de deseño farmOS (unificar Tarefas/Sementeiras/Colleitas/Tratamentos coma un só concepto de "evento"): non se aplica aquí. Tratamentos e Fertilizacións módanse coma rexistros ligados a Cultivo, non coma estados do seu ciclo de vida — a decisión sobre Tarefas faise no seu propio subproxecto.
- Activar/desactivar Tratamentos/Fertilización segundo `horta.uso_profesional`: dispoñibles sempre, para simplificar — a obriga legal de rexistralos só aplica cando a horta é profesional, pero a funcionalidade non se oculta.

## Arquitectura

```
Horta
  └── Parcela
         └── Cultivo (especie, variedade, datas, cantidade, unidade, estado)
                ├── Tratamento (fitosanitario, baixa lóxica)
                └── Fertilización (baixa lóxica)
```

- `Cultivo.parcela_id` → `Parcela.id`. Os permisos de Cultivo resólvense vía `parcela.horta_id` (igual que Parcela resolve vía `horta_id` directamente).
- `Tratamento.cultivo_id` e `Fertilizacion.cultivo_id` → `Cultivo.id`. **Este proxecto non usa `relationship()` de SQLAlchemy en ningún modelo** (só columnas FK soltas — decisión xa establecida; é por iso que `eliminar_horta`/`eliminar_parcela` cascadean a man en vez de depender do ORM). Os permisos de Tratamento/Fertilización resólvense con dúas consultas explícitas: `parcela_id = session.get(Cultivo, cultivo_id).parcela_id` e despois `horta_id = session.get(Parcela, parcela_id).horta_id` (ou un `session.query(Parcela.horta_id).join(Cultivo, Cultivo.parcela_id == Parcela.id).filter(Cultivo.id == cultivo_id).scalar()` nunha soa consulta — usar esta segunda forma, por ser un só round-trip á BD).
- `eliminar_parcela` amplíase para borrar en cascada os seus Cultivos (e, por extensión, os Tratamentos/Fertilizacións dese cultivo — ver "Baixa lóxica vs. cascada" abaixo). `eliminar_horta` xa cascadea a Parcela, así que herda a cadea completa.
- **Baixa lóxica vs. cascada**: a baixa lóxica aplícase só cando se elimina UN tratamento/fertilización individual dende a UI (acción explícita do usuario). Se se elimina o Cultivo enteiro (ou a Parcela, ou a Horta), os seus Tratamentos/Fertilizacións bórranse fisicamente coma parte da cascada — non ten sentido conservar un tratamento "por baixa lóxica" cando o cultivo ao que pertence xa non existe. Esta distinción é importante: non facer baixa lóxica en cascada, só cando se borra o rexistro individual.

## Compoñentes

### Modelos (`src/horta/models/cultivo.py`, novo)

```python
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Cultivo(Base):
    __tablename__ = "cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("parcela.id"))
    especie: Mapped[str] = mapped_column(String(120))
    variedade: Mapped[str | None] = mapped_column(String(120), default=None)
    data_sementeira: Mapped[date | None] = mapped_column(Date, default=None)
    data_plantacion: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_prevista: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_real: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(30), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Tratamento(Base):
    __tablename__ = "tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    praga: Mapped[str] = mapped_column(String(200))
    superficie_tratada: Mapped[float | None] = mapped_column(Float, default=None)
    produto: Mapped[str] = mapped_column(String(200))
    numero_rexistro_produto: Mapped[str | None] = mapped_column(String(50), default=None)
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(200), default=None)
    aplicador: Mapped[str] = mapped_column(String(200))
    equipo_aplicador: Mapped[str | None] = mapped_column(String(200), default=None)
    persoas_asesoramento: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Fertilizacion(Base):
    __tablename__ = "fertilizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
    tipo: Mapped[str] = mapped_column(String(50))
    produto: Mapped[str] = mapped_column(String(200))
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    n: Mapped[float | None] = mapped_column(Float, default=None)
    p: Mapped[float | None] = mapped_column(Float, default=None)
    k: Mapped[float | None] = mapped_column(Float, default=None)
    carbono_organico: Mapped[float | None] = mapped_column(Float, default=None)
    micronutrientes: Mapped[str | None] = mapped_column(String(300), default=None)
    asesoramento_recibido: Mapped[str | None] = mapped_column(String(300), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Valores fixos para selectores (mesmo patrón que `_ESTADOS_PARCELA` etc. en `horta_detalle.py`):
- `Cultivo.estado`: `planificado`, `sementado`, `plantado`, `colleitado`, `finalizado`.
- `Cultivo.unidade`: `kg`, `unidades`, `ducias`, `mazos`.
- `Fertilizacion.tipo`: `emenda`, `abonado_fondo`, `cobertoira`.

### Migración Alembic

Unha soa revisión nova (`uv run alembic revision --autogenerate -m "engadir cultivo, tratamento e fertilizacion"`) que crea as tres táboas. Revisar o ficheiro xerado antes de aplicalo (comprobar as FK e os tipos, coma se fixo nas migracións anteriores).

### Servizos

`src/horta/services/cultivos.py`, `src/horta/services/tratamentos.py`, `src/horta/services/fertilizacions.py` — mesmo patrón que `services/parcelas.py`:

- `_ROLES_ESCRITURA`/`_ROLES_LECTURA` (reutilizar de `hortas.py` ou redefinir localmente, seguindo o que xa fai `parcelas.py`).
- `CAMPOS_EDITABLES_CULTIVO`/`CAMPOS_EDITABLES_TRATAMENTO`/`CAMPOS_EDITABLES_FERTILIZACION` (frozensets, excluíndo `id`, as FK, `created_at`, e — para Tratamento/Fertilización — `baixa`, que só se cambia dende a acción de eliminar, non dende actualizar).
- `crear_cultivo(session, actor, parcela_id, especie, **campos)`: carga a `Parcela` (`session.get(Parcela, parcela_id)`) para obter `horta_id`, e chama a `comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)`. Se a parcela non existe, levantar `ValueError("Esa parcela non existe")` antes de comprobar permisos.
- `crear_tratamento`/`crear_fertilizacion`: resolven a `horta_id` coa consulta dun só salto descrita na sección de Arquitectura (`session.query(Parcela.horta_id).join(Cultivo, Cultivo.parcela_id == Parcela.id).filter(Cultivo.id == cultivo_id).scalar()`), e chaman a `comprobar_rol_horta` con ese resultado. Se a consulta devolve `None` (cultivo inexistente), levantar `ValueError("Ese cultivo non existe")`.
- `actualizar_cultivo`/`eliminar_cultivo`, `actualizar_tratamento`/`eliminar_tratamento`, `actualizar_fertilizacion`/`eliminar_fertilizacion`: reciben xa o obxecto (`Cultivo`/`Tratamento`/`Fertilizacion`) coma parámetro (mesmo patrón que `actualizar_parcela(session, actor, parcela, **cambios)`), e resolven a `horta_id` coa mesma consulta dun salto a partir do `parcela_id`/`cultivo_id` do obxecto recibido.
- `actualizar_*`: mesmo patrón que `actualizar_parcela` (rexeitar campos non editables, comprobar permisos, `setattr`, commit).
- `eliminar_cultivo`: `session.delete(cultivo)` tal cual (cascada física, xa que ao borrar un cultivo enteiro tamén se borran fisicamente os seus tratamentos/fertilizacións — ver nota de arquitectura). Require borrar primeiro os `Tratamento`/`Fertilizacion` dese cultivo explicitamente (mesmo patrón que `eliminar_horta` fixo coas súas parcelas: iterar e `session.delete()` cada un, despois `session.flush()`, antes de borrar o Cultivo).
- `eliminar_tratamento`/`eliminar_fertilizacion`: **NON fan `session.delete()`** — fan `tratamento.baixa = True; session.commit()` (baixa lóxica).
- `listar_cultivos(session, actor, horta_id)`: a UI amosa unha soa pestana "Cultivos" para toda a horta (coma Parcelas/Animais, non anidada dentro de cada parcela), así que a función lista por `horta_id`, non por `parcela_id`: `session.query(Cultivo).join(Parcela, Cultivo.parcela_id == Parcela.id).filter(Parcela.horta_id == horta_id).order_by(Cultivo.especie).all()`.
- `listar_tratamentos(session, actor, horta_id)`/`listar_fertilizacions(session, actor, horta_id)`: mesmo motivo, tamén por `horta_id` (pestana plana para toda a horta): `session.query(Tratamento).join(Cultivo, Tratamento.cultivo_id == Cultivo.id).join(Parcela, Cultivo.parcela_id == Parcela.id).filter(Parcela.horta_id == horta_id, Tratamento.baixa.is_(False)).all()` (substituír `Tratamento` por `Fertilizacion` na segunda función). `.is_(False)` en vez de `== False` para evitar o aviso de ruff (`E712`).

### UI

Tres pestanas novas en `src/horta/ui/pages/horta_detalle.py`, mesmo patrón que Parcelas/Animais/Membros (diálogo crear, táboa con busca/filtro/paxinación coma nas últimas dúas iteracións, diálogo editar, eliminar con confirmación):

- **Cultivos**: táboa con columnas Parcela/Especie/Variedade/Estado (máis unha columna Estado editable coma selector). O formulario de crear/editar leva un `ui.select` de Parcela (as parcelas da horta actual) e os campos de datas coma `ui.date` (xa dispoñible en NiceGUI, sen dependencia nova).
- **Tratamentos**: táboa con columnas Cultivo (mostrando especie+variedade)/Data/Praga/Produto/Aplicador. O formulario leva un `ui.select` de Cultivo.
- **Fertilización**: táboa con columnas Cultivo/Data/Tipo/Produto. Mesmo patrón.

As tres pestanas engádense despois de Membros na páxina da horta, visibles para calquera membro (lectura para lectores, escritura para admin/editor — mesmos roles que Parcelas/Animais).

## Probas

- Un ficheiro de test por servizo (`tests/services/test_cultivos.py`, `test_tratamentos.py`, `test_fertilizacions.py`), seguindo o patrón xa establecido en `test_parcelas.py`: crear/actualizar/eliminar con éxito, rexeitar campos non editables, rexeitar sen permiso (lector), rexeitar dende outra horta.
- Test específico para a baixa lóxica: `eliminar_tratamento` non borra a fila da BD (segue existindo con `baixa=True`), e `listar_tratamentos` non a devolve.
- Test específico para a cascada: eliminar un Cultivo borra fisicamente os seus Tratamentos/Fertilizacións (non quedan filas orfas, nin sequera con `baixa=True`).
- Sen tests novos de UI para as tres pestanas (precedente xa establecido: as páxinas NiceGUI non se testean unitariamente).
- Suite completa, ruff e mypy en verde ao final.

## Lembrete para a seguinte spec

Unha vez esta spec estea implementada e haxa datos reais de Cultivos/Tratamentos/Fertilización, a seguinte peza natural é a **xeración do caderno de explotación** (README §22 "Xeración do caderno"): un botón "Exportar caderno de explotación" por horta e ano, que xere un PDF/Excel coa estrutura dos modelos oficiais (datos da explotación, táboa de parcelas, táboa de tratamentos, táboa de fertilización), usando WeasyPrint/openpyxl coma xa estaba previsto no CLAUDE.md. Non esquecer isto ao rematar Tarefas+Dashboard.

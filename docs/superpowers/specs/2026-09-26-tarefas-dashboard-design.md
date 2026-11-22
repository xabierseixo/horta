# Deseño: Tarefas e Dashboard

## Contexto

Segundo e último subproxecto que faltaba para completar o alcance da "primeira versión" (README §23): Usuarios, Hortas, Parcelas, Cultivos xa existen; falta Tarefas e un Dashboard básico. Sen isto, a app aínda non cumpre o obxectivo da primeira iteración (crear tarefas, ver o que hai pendente).

Esta spec tamén resolve unha nota de deseño que quedara aberta dende a iteración anterior (CLAUDE.md, inspirada en farmOS): se Tarefas debía modelarse coma unha entidade propia ou coma un concepto xenérico de "evento" compartido co Histórico (§10). Xa se decidiu con Tratamentos/Fertilización usar entidades propias en vez dun modelo xenérico — esta spec segue o mesmo criterio.

## Obxectivo

1. Rexistrar Tarefas: descrición, datas (prevista/límite/feita), ligazón opcional a Parcela e/ou Cultivo, prioridade, estado (pendente/feito), notas.
2. Marcar unha tarefa coma feita rexistra a data real de finalización — isto substitúe a necesidade dunha entidade Histórico separada: consultar "tarefas feitas nesta parcela, ordenadas por data" xa cobre o §10.
3. Unha nova pestana "Dashboard" en `/hortas/{id}`, coma pestana por defecto, cos contadores e listaxes do mockup do §17 (agás o plano da horta).

## Fóra de alcance

- **Plano da horta** (`ui.leaflet`): require §5/§15, fase posterior propia.
- **Calendario** (§9, vistas mensual/semanal/lista): fase posterior propia; esta spec só amosa listaxes simples de tarefas de hoxe/próximas/atrasadas.
- **Entidade Histórico separada**: resolta coma consulta sobre Tarefas feitas (ver Obxectivo 2), non coma táboa nova.
- **Notificacións/lembretes** (push, email): non mencionados en ningures do README para esta fase, non se engaden.
- Mellorar o dashboard xeral (`/`, lista de hortas): queda como está; esta spec só toca o dashboard POR horta.

## Arquitectura

```
Horta
  └── Tarefa (horta_id obrigatorio; parcela_id e cultivo_id opcionais)
```

- `Tarefa.horta_id` → `Horta.id` (coma Parcela/Animal — permisos resólvense directamente, sen salto).
- `Tarefa.parcela_id` → `Parcela.id`, opcional (nullable) — hai tarefas sen parcela concreta (p.ex. "mercar sementes").
- `Tarefa.cultivo_id` → `Cultivo.id`, opcional (nullable) — independente de `parcela_id`; non se esixe consistencia entre ambos os dous (se se indica cultivo, non fai falla tamén indicar a súa parcela — simplicidade sobre validación exhaustiva dun caso raro).
- Sen `relationship()` de SQLAlchemy, coma sempre neste proxecto.
- `eliminar_parcela`/`eliminar_horta` amplíanse para tamén desligar/eliminar as Tarefas dependentes (ver "Cascada" abaixo).

### Cascada ao eliminar Parcela/Cultivo/Horta

- Eliminar unha **Horta**: bórranse fisicamente todas as súas Tarefas (igual criterio que Parcela/Animal/Membro — non hai obriga legal de conservar tarefas, a diferenza de Tratamentos/Fertilización).
- Eliminar unha **Parcela**: as Tarefas ligadas a ela **non se eliminan** — pasan a ter `parcela_id = NULL` (a tarefa segue existindo, só perde a ligazón a unha parcela que xa non existe). Mesmo criterio para `cultivo_id` ao eliminar un Cultivo.
  - Razón: unha tarefa é un rexistro de traballo real (p.ex. "regar", xa marcada coma feita hai meses); eliminar unha parcela non debería borrar ese historial de traballo, só a súa ligazón a algo que xa non existe.

## Compoñentes

### Modelo (`src/horta/models/tarefa.py`, novo)

```python
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Tarefa(Base):
    __tablename__ = "tarefa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("parcela.id"), default=None)
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
    descricion: Mapped[str] = mapped_column(String(300))
    data: Mapped[date | None] = mapped_column(Date, default=None)
    data_limite: Mapped[date | None] = mapped_column(Date, default=None)
    data_feita: Mapped[date | None] = mapped_column(Date, default=None)
    prioridade: Mapped[str] = mapped_column(String(20), default="media")
    estado: Mapped[str] = mapped_column(String(20), default="pendente")
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Valores fixos para selectores: `prioridade` = `baixa`/`media`/`alta`; `estado` = `pendente`/`feito`.

### Servizo (`src/horta/services/tarefas.py`, novo)

Mesmo patrón que `services/parcelas.py` (permisos directos vía `horta_id`, sen salto):

- `crear_tarefa(session, actor, horta_id, descricion, **campos) -> Tarefa`
- `actualizar_tarefa(session, actor, tarefa, **cambios) -> Tarefa` (`CAMPOS_EDITABLES_TAREFA` exclúe `id`, `horta_id`, `created_at` — inclúe `parcela_id`/`cultivo_id`, xa que cambiar a que parcela/cultivo pertence unha tarefa é lexítimo e non afecta os permisos, que xa se resolven por `horta_id`).
- `marcar_feita(session, actor, tarefa) -> Tarefa`: pon `estado="feito"` e `data_feita=date.today()`. Función dedicada (non parte de `actualizar_tarefa`), mesmo patrón que `activar_usuario`/`desactivar_usuario`.
- `marcar_pendente(session, actor, tarefa) -> Tarefa`: reverte (`estado="pendente"`, `data_feita=None`) — por se alguén marca por erro.
- `eliminar_tarefa(session, actor, tarefa) -> None`: borrado físico (sen baixa lóxica — Tarefas non teñen obriga legal de conservación, a diferenza de Tratamentos/Fertilización).
- `listar_tarefas(session, actor, horta_id) -> list[Tarefa]`
- `listar_tarefas_pendentes_hoxe(session, actor, horta_id) -> list[Tarefa]`: `estado="pendente"` e `data == date.today()`.
- `listar_tarefas_proximas(session, actor, horta_id, limite=5) -> list[Tarefa]`: `estado="pendente"` e `data > date.today()`, ordenadas por `data`, limitadas a `limite`.
- `listar_tarefas_atrasadas(session, actor, horta_id) -> list[Tarefa]`: `estado="pendente"` e `data_limite < date.today()`.
- `contar_tarefas_pendentes(session, actor, horta_id) -> int`.

### Cascada en `eliminar_parcela`/`eliminar_horta`

- `eliminar_parcela` (en `services/parcelas.py`): xusto despois da comprobación de permiso, e ANTES do bloque xa existente que borra Cultivo/Tratamento/Fertilización, engadir `session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})`. Non fai falla un `session.flush()` propio para isto (é un `UPDATE`, non un `DELETE`; queda incluído no `session.flush()` xa existente da función, que sae antes de `session.delete(parcela)`) — pero colocar o `.update(...)` ANTES dese flush existente, non despois.
- `eliminar_cultivo` (en `services/cultivos.py`): mesmo criterio — `session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})` xusto despois da comprobación de permiso, ANTES do bloque que borra Tratamento/Fertilización, e ANTES do `session.flush()` xa existente dese función.
- `eliminar_horta` (en `services/hortas.py`): a Tarefa pode referenciar Parcela e/ou Cultivo (FK opcionais), así que **hai que borrar e facer flush das Tarefas ANTES de calquera outro borrado desta función** (antes de resolver `parcelas`/`cultivos`, non despois). Orde exacta a engadir en `eliminar_horta`, coma PRIMEIRO bloque despois da comprobación de permiso e antes do bloque xa existente de `parcelas = session.query(Parcela)...`:
  ```python
  for tarefa in session.query(Tarefa).filter_by(horta_id=horta.id).all():
      session.delete(tarefa)
  session.flush()
  ```
  Razón da orde: se se borrase despois de Cultivo/Parcela (coma os outros bloques), unha Tarefa que aínda apunte a un Cultivo/Parcela xa borrado violaría a FK ao intentar borrar esa Tarefa. Borrándoas primeiro (e facendo flush) elimínase esa dependencia antes de tocar Parcela/Cultivo. Isto é exactamente a lección dos dous fallos xa atopados e corrixidos na iteración anterior (`eliminar_horta`/`eliminar_parcela`): cando hai varios niveis de dependencia sen `relationship()`, cada nivel necesita o seu propio `flush()`, na orde correcta (fillos antes ca pais).

### UI

**Pestana "Tarefas"** en `/hortas/{id}` (mesmo patrón de busca/filtro/paxinación xa establecido): táboa con Descrición/Data/Data límite/Prioridade/Estado. Diálogo de crear: descrición (obrigatoria) + parcela (opcional, selector) + cultivo (opcional, selector) + data + prioridade. Editar: tamén data_límite e notas. Un botón "Marcar feita"/"Marcar pendente" (alterna segundo o estado actual, mesmo patrón que "Activar"/"Desactivar" en Usuarios) ademais de Editar/Eliminar.

**Pestana "Dashboard"** en `/hortas/{id}`, posta coma primeira pestana (antes de Parcelas), pestana por defecto ao abrir a horta:
- Catro contadores: parcelas, cultivos, animais, tarefas pendentes.
- Sección "Tarefas de hoxe" (lista simple, `listar_tarefas_pendentes_hoxe`).
- Sección "Próximas actividades" (lista simple, `listar_tarefas_proximas`, límite 5).
- Se hai tarefas atrasadas (`listar_tarefas_atrasadas`), un aviso destacado (`ui.notify` persistente ou simplemente un `ui.label` en cor negativa) indicando cantas hai.
- Sen busca/filtro/paxinación nesta pestana (é un resumo, non unha táboa de xestión).

## Probas

- `tests/models/test_tarefa.py`: crear cunha tarefa mínima (só descrición), comprobar valores por defecto (`estado="pendente"`, `prioridade="media"`, datas `None`).
- `tests/services/test_tarefas.py`: patrón estándar (admin/editor poden crear, lector non; listar filtra por horta; actualizar rexeita campos non editables; eliminar require permiso), máis:
  - `marcar_feita` pon `estado="feito"` e `data_feita=date.today()`.
  - `marcar_pendente` reverte.
  - `listar_tarefas_pendentes_hoxe`/`_proximas`/`_atrasadas` devolven exactamente o esperado con datos de proba en varias datas.
  - `eliminar_parcela` non borra as tarefas ligadas, só pon `parcela_id=None` (test específico, xa que este comportamento é distinto ao de Cultivo/Tratamento/Fertilización).
  - `eliminar_horta` si borra fisicamente as tarefas da horta.
- Sen tests novos de UI (precedente xa establecido).
- Suite completa, ruff, mypy en verde ao final.

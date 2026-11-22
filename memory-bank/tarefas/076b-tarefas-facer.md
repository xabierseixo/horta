# Tarefa 076b — Tarefas por facer (3/16): facela liga o traballo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Facer unha tarefa con tipo déixaa feita e ligada ao traballo apuntado (do seu tipo e da explotación); unha tarefa sen tipo garda quen a fixo e as horas; o Diario non a repite. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/services/tarefas.py`
- `src/horta/services/diario.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.horta import RolHorta
from horta.models.labor import Labor
```

Despois:
```python
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.parcela import Parcela
```

### Paso 2 — `src/horta/services/tarefas.py`

Antes:
```python
def marcar_feita(session: Session, actor: Usuario, tarefa: Tarefa) -> Tarefa:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    tarefa.estado = "feito"
    tarefa.data_feita = date.today()
    session.commit()
    return tarefa


def marcar_pendente(session: Session, actor: Usuario, tarefa: Tarefa) -> Tarefa:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
```

Despois:
```python
def marcar_feita(
    session: Session, actor: Usuario, tarefa: Tarefa, persoa_id: int | None = None,
    data: date | None = None, horas: float | None = None,
) -> Tarefa:
    """Unha tarefa sen tipo (outro traballo) feita: quen a fixo, cando e cantas horas."""
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    if tarefa.tipo is not None:
        raise OperacionNonPermitidaError("Esta tarefa apúntase no formulario do seu tipo")
    comprobar_quen(session, tarefa.horta_id, persoa_id, horas, obrigatoria=False)
    tarefa.estado = "feito"
    tarefa.data_feita = data or date.today()
    tarefa.persoa_id = persoa_id
    tarefa.horas = horas
    session.commit()
    return tarefa


def facer_tarefa(session: Session, actor: Usuario, tarefa: Tarefa, rexistro: Base) -> Tarefa:
    """A tarefa fíxose: queda feita e ligada ao traballo apuntado no formulario do seu tipo."""
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    taboa, campo_data = _TABOA_E_DATA.get(tarefa.tipo or "", (None, ""))
    if taboa is None or not isinstance(rexistro, taboa):
        raise OperacionNonPermitidaError("O traballo apuntado non é do tipo da tarefa")
    if isinstance(rexistro, Colleita):
        cultivo = session.get(Cultivo, rexistro.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        horta_id = parcela.horta_id if parcela else None
    else:
        horta_id = getattr(rexistro, "horta_id", None)
    if horta_id != tarefa.horta_id:
        raise OperacionNonPermitidaError("O traballo apuntado non é desta explotación")
    tarefa.estado = "feito"
    tarefa.data_feita = getattr(rexistro, campo_data)
    tarefa.traballo_id = getattr(rexistro, "id")
    session.commit()
    return tarefa


def marcar_pendente(session: Session, actor: Usuario, tarefa: Tarefa) -> Tarefa:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    if tarefa.traballo_id is not None:
        raise OperacionNonPermitidaError(
            "Esta tarefa xa ten o traballo apuntado: para cambiala, edita ese traballo")
```

### Paso 3 — `src/horta/services/diario.py`

Antes:
```python
        feita = ta.estado == "feito"
        sitio = onde(ta.cultivo_id) or parcelas.get(ta.parcela_id or 0, "")
        traballos.append(Traballo(
            "tarefa", ta.id, ta.data_feita or ta.data if feita else ta.data or ta.data_limite,
            feita, ta.descricion, sitio,
            parcela_de(ta.cultivo_id) or (frozenset({ta.parcela_id}) if ta.parcela_id
                                          else frozenset()),
            atrasado=not feita and ta.data_limite is not None and ta.data_limite < hoxe))
```

Despois:
```python
        if ta.traballo_id is not None:
            continue  # xa feita: sae o traballo apuntado no seu tipo
        feita = ta.estado == "feito"
        sitio = onde(ta.cultivo_id) or parcelas.get(ta.parcela_id or 0, "")
        traballos.append(Traballo(
            "tarefa", ta.id, ta.data_feita or ta.data if feita else ta.data or ta.data_limite,
            feita, ta.descricion, sitio,
            parcela_de(ta.cultivo_id) or (frozenset({ta.parcela_id}) if ta.parcela_id
                                          else frozenset()),
            atrasado=not feita and ta.data_limite is not None and ta.data_limite < hoxe,
            persoas=_quen(ta.persoa_id), sen_quen=feita and ta.persoa_id is None))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (3/16): facela liga o traballo: feito.

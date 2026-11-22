# Tarefa 076n — Tarefas por facer (15/16): marcar feita abre o formulario

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

En Tarefas, «Marcar feita» fai a tarefa como no Diario; volver a por facer unha xa apuntada avisa. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    listar_tarefas_proximas,
    marcar_feita,
```

Despois:
```python
    listar_tarefas_proximas,
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        abrir_nova_tarefa = dialogo_nova_tarefa(horta_id)
```

Despois:
```python
        abrir_nova_tarefa = dialogo_nova_tarefa(horta_id)
        formularios = Formularios(horta_id)
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        accion = marcar_pendente if tarefa_completa.estado == "feito" else marcar_feita
```

Despois:
```python
        if tarefa_completa.estado != "feito":
            formularios.facer(tarefa_completa)
            return
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
            feito = executar_accion(session, lambda: accion(session, actor_actual, obxectivo))
```

Despois:
```python
            feito = executar_accion(
                session, lambda: marcar_pendente(session, actor_actual, obxectivo))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (15/16): marcar feita abre o formulario: feito.

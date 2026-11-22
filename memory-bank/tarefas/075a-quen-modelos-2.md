# Tarefa 075a — Quen e horas (2/2 datos): labor, abonado, sementeira e comprobación común

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Labor e abonado gardan as horas; o cultivo, quen fixo a sementeira e as súas horas. Nova comprobación común: quen é obrigatorio e ten que ser da explotación; as horas, se se poñen, máis de 0. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/models/labor.py`
- `src/horta/models/abonado.py`
- `src/horta/models/cultivo.py`
- `src/horta/services/persoas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/labor.py`

Antes:
```python
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

Despois:
```python
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 2 — `src/horta/models/abonado.py`

Antes:
```python
    aplicador_persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

Despois:
```python
    aplicador_persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 3 — `src/horta/models/cultivo.py`

Antes:
```python
    data_adquisicion_material: Mapped[date | None] = mapped_column(Date, default=None)
```

Despois:
```python
    data_adquisicion_material: Mapped[date | None] = mapped_column(Date, default=None)
    # Quen fixo a sementeira ou plantación e cantas horas
    sementeira_persoa_id: Mapped[int | None] = mapped_column(
        ForeignKey("persoa.id"), default=None
    )
    sementeira_horas: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 4 — `src/horta/services/persoas.py`

Antes:
```python
    return persoa.ropo_caducidade is not None and persoa.ropo_caducidade >= na_data
```

Despois:
```python
    return persoa.ropo_caducidade is not None and persoa.ropo_caducidade >= na_data


def comprobar_quen(
    session: Session, horta_id: int, persoa_id: int | None, horas: float | None,
    obrigatoria: bool = True,
) -> None:
    """Todo traballo o fai unha persoa: tense que indicar e ten que ser desta explotación.
    As horas son opcionais."""
    if persoa_id is None:
        if obrigatoria:
            raise OperacionNonPermitidaError("Indica quen o fixo")
    else:
        persoa = session.get(Persoa, persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("A persoa indicada non é desta explotación")
    if horas is not None and horas <= 0:
        raise OperacionNonPermitidaError("As horas teñen que ser máis de 0")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas (2/2 datos): labor, abonado, sementeira e comprobación común: feito.

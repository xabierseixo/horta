# Tarefa 072b — Rexistro do MAPA: produto repetido

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072a3. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O rexistro actual do MAPA trae o produto 16192 (OVIPRON) dúas veces con distinto IdProducto e os mesmos usos, e a importación fallaba. Impórtase só a primeira aparición. Visto na descarga real do 2026-10-25. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/fito_importar.py`
- `tests/services/test_fito_importar.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/fito_importar.py`

Antes:
```python
        num = texto(d["Num_Registro"]) or ""
```

Despois:
```python
        num = texto(d["Num_Registro"]) or ""
        if num in vistos:
            continue  # o MAPA repite ás veces un produto con outro IdProducto e os mesmos usos
```

### Paso 2 — `tests/services/test_fito_importar.py`

Antes:
```python
    assert session.query(FitoUso).count() == 1


```

Despois:
```python
    assert session.query(FitoUso).count() == 1


def test_produto_repetido_no_mapa_importase_unha_vez(session, tmp_path):
    _escribir(tmp_path, [_produto("ES-001", "A", [_USO]), _produto("ES-001", "A", [_USO])])
    assert importar_fitosanitarios(session, tmp_path).altas == 1
    assert session.query(FitoUso).count() == 1


```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Rexistro do MAPA: produto repetido: feito.

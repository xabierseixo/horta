# Tarefa 037b — Parcela completa: datos e regras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 037.

## Obxectivo

Campos obrigatorios do REA bloque 12 para a parcela (= DGC) que faltan segundo `docs/campos-oficiais-anexo-v.md`: agregado e zona SIGPAC, referencia catastral, réxime de tenencia e NIF do arrendador, pequena superficie, datas e causa de alta/baixa; e a orixe da auga (CUE rega). Regras: NIF válido, baixa ≥ alta, códigos de catálogo vixentes. Pantalla noutra tarefa.

## Ficheiros a tocar

- `src/horta/models/parcela.py`
- `alembic/versions/b8e3f6a9d4c2_parcela_completa.py` (**ficheiro novo**)
- `src/horta/services/parcelas.py`
- `tests/services/test_parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/parcelas.py`: validación nova

Antes:
```python
def crear_parcela(
```

Despois:
```python
_CATALOGOS_PARCELA = {
    "rexime_tenencia": "rexime_tenencia",
    "causa_baixa": "causa_baixa",
    "orixe_auga": "orixe_auga",
}


def _validar_rea(session: Session, valores: dict[str, Any]) -> None:
    nif = valores.get("nif_arrendador")
    if nif and not _PATRON_NIF.match(nif):
        raise OperacionNonPermitidaError("O NIF do arrendador non é válido")
    alta, baixa = valores.get("data_alta"), valores.get("data_baixa")
    if alta is not None and baixa is not None and baixa < alta:
        raise OperacionNonPermitidaError("A data de baixa non pode ser anterior á de alta")
    for campo, catalogo in _CATALOGOS_PARCELA.items():
        if valores.get(campo):
            validar_codigo(session, catalogo, str(valores[campo]), alta or date.today())


def crear_parcela(
```

### Paso 2 — mesmo ficheiro: validar ao crear

Antes:
```python
    _validar_superficie(campos)
    estado = campos.pop("estado", "activa")
```

Despois:
```python
    _validar_superficie(campos)
    _validar_rea(session, campos)
    estado = campos.pop("estado", "activa")
```

### Paso 3 — mesmo ficheiro: validar ao actualizar

Antes:
```python
    _validar_superficie(cambios)
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
```

Despois:
```python
    _validar_superficie(cambios)
    _validar_rea(session, {c: cambios.get(c, getattr(parcela, c)) for c in
                           ("nif_arrendador", "data_alta", "data_baixa", *_CATALOGOS_PARCELA)})
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
```

### Paso 4 — `tests/services/test_parcelas.py`: engadir ao final do ficheiro

```python
@pytest.mark.parametrize(
    ("campos", "mensaxe"),
    [
        ({"nif_arrendador": "123"}, "NIF do arrendador"),
        ({"data_alta": date(2026, 5, 1), "data_baixa": date(2026, 4, 1)}, "anterior á de alta"),
        ({"rexime_tenencia": "99"}, "non existe"),
    ],
)
def test_validacions_rea_da_parcela(session, campos, mensaxe):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_parcela(session, ana, horta.id, "P1", **campos)


def test_parcela_garda_sigpac_completo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", sigpac_agregado="0",
                            sigpac_zona="0", referencia_catastral="15078A00100023")
    actualizar_parcela(session, ana, parcela, nif_arrendador="12345678Z")
    assert (parcela.sigpac_zona, parcela.nif_arrendador) == ("0", "12345678Z")
```

### Paso 5 — mesmo ficheiro de tests: importar

Antes:
```python
from horta.services.errors import PermisoDenegadoError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

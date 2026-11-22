# Tarefa 001 — Campos xeográficos editables en Parcela

**Estado**: feita

## Obxectivo

O modelo `Parcela` xa ten os campos `lat`, `lon`, `geometria` e `imaxe` (migración `9ceefdfded77`), pero o servizo non permite editalos. Hai que permitilo e validar as coordenadas. **Sen tocar a UI** (iso é outra tarefa).

## Ficheiros a tocar

- `src/horta/services/parcelas.py`
- `tests/services/test_parcelas.py`

Ningún outro.

## Pasos

1. En `src/horta/services/parcelas.py`, engadir `"lat"`, `"lon"`, `"geometria"` e `"imaxe"` ao conxunto `CAMPOS_EDITABLES_PARCELA`.
2. No mesmo ficheiro, crear unha función privada `_validar_coordenadas(campos: dict[str, Any]) -> None` que:
   - se `campos` ten `lat` e non é `None`, levante `ValueError("A latitude debe estar entre -90 e 90")` cando non estea entre -90 e 90 (incluídos);
   - se `campos` ten `lon` e non é `None`, levante `ValueError("A lonxitude debe estar entre -180 e 180")` cando non estea entre -180 e 180 (incluídos).
3. Chamar a `_validar_coordenadas(campos)` en `crear_parcela` e `_validar_coordenadas(cambios)` en `actualizar_parcela`, **despois** da comprobación de permisos (`comprobar_rol_horta`) e antes de modificar nada.
4. En `tests/services/test_parcelas.py`, engadir estes tests (reutilizar o helper `_crear_usuario` e `crear_horta` como nos tests existentes):
   - `test_crear_parcela_con_coordenadas`: crear unha parcela con `lat=42.88`, `lon=-8.54` e comprobar que se gardan.
   - `test_actualizar_campos_xeograficos`: actualizar `lat`, `lon`, `geometria='{"type": "Polygon", "coordinates": []}'` e `imaxe="parcelas/norte.jpg"` e comprobar os catro valores.
   - `test_latitude_fora_de_rango`: `crear_parcela(..., lat=91)` levanta `ValueError`.
   - `test_lonxitude_fora_de_rango`: `actualizar_parcela(..., lon=-181)` levanta `ValueError` e a parcela segue co valor anterior de `lon`.

## Criterios de aceptación

- Os catro campos pódense crear e actualizar polo servizo.
- As coordenadas fóra de rango levantan `ValueError` coa mensaxe indicada.
- Todos os tests existentes seguen pasando.

## Resultado

- `CAMPOS_EDITABLES_PARCELA` actualizado con `lat`, `lon`, `geometria`, `imaxe`.
- Función `_validar_coordenadas` creada: rexeita lat fóra de [-90, 90] e lon fóra de [-180, 180].
- Validación chamada en `crear_parcela` e `actualizar_parcela` despois de `comprobar_rol_horta`.
- 4 tests engadidos en `tests/services/test_parcelas.py`.
- Commits: `d95027b`.
- `uv run ruff check src tests`: All checks passed.
- `uv run mypy src`: Success.
- `uv run pytest -q`: 148 passed.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

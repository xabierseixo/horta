# Tarefa 026 — Importar 21 catálogos oficiais máis

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha.

## Obxectivo

Temos descargados 108 catálogos do FEGA pero só se importan 13. Engádense os 21 que necesitan cultivos, parcelas, colleitas, fertilización, análises, rega, labores e animais. Todos teñen o código na columna "Código SIEX" (agás `RAZAS`, que usa "Código") e a descrición na segunda columna, así que abonda con engadilos ao dicionario `CATALOGOS_XERAIS`; o importador e o comando `horta-catalogos importar` xa os collen.

Quedan fóra, para máis adiante, os que teñen códigos repetidos ou compostos: `REGIMENES_CALIDAD`, `MATERIAL_VEGETAL_REPRODUCCION` e `DETALLE_MATERIAL_FERT`.

## Ficheiros a tocar

- `src/horta/services/catalogos_importar.py`
- `tests/services/test_catalogos_importar.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/catalogos_importar.py`: engadir os catálogos

Antes:
```python
    "boas_practicas": ("BUENAS_PRACTICAS_AMBITOS", "Código SIEX", None),
}
```

Despois:
```python
    "boas_practicas": ("BUENAS_PRACTICAS_AMBITOS", "Código SIEX", None),
    # Cultivos e parcelas (REA)
    "sistema_cultivo": ("SIST_CULTIVO", "Código SIEX", None),
    "destino_cultivo": ("DESTINO_CULTIVO", "Código SIEX", None),
    "certificacion_ecoloxica": ("TIPO_CERTIFICACION_ECOLOGICA", "Código SIEX", None),
    "sistema_explotacion": ("SIST_EXPLOTACION", "Código SIEX", None),
    "actividade_agraria": ("ACTIVIDAD_AGRARIA", "Código SIEX", None),
    "causa_baixa": ("CAUSA_BAJA", "Código SIEX", None),
    "procedencia_material_vexetal": ("PROC_VEGETAL", "Código SIEX", None),
    "tipo_cobertura_solo": ("TIPO_COBERTURA_SUELO", "Código SIEX", None),
    "rexime_tenencia": ("REGIMEN_TENENCIA", "Código SIEX", None),
    # Colleita
    "destino_colleita": ("DEST_COSECHA", "Código SIEX", None),
    "destino_restos": ("DEST_RES_VEG", "Código SIEX", None),
    # Fertilización, análises e rega
    "material_fertilizante": ("MAT_FERTI", "Código SIEX", None),
    "tipo_fertilizacion": ("TIPO_FERITILIZACION", "Código SIEX", None),
    "metodo_fertilizacion": ("METODO_APLICACION_FERTILIZANTE", "Código SIEX", None),
    "tratamento_estercos": ("TRAT_ESTIERCOLES", "Código SIEX", None),
    "material_analizado": ("MATERIAL_ANALIZADO", "Código SIEX", None),
    "tipo_analise": ("TIPO_ANALISIS", "Código SIEX", None),
    "orixe_auga": ("ORIGEN_AGUA_RIEGO", "Código SIEX", None),
    "sistema_rega": ("SIST_RIEGO", "Código SIEX", None),
    # Labores e animais
    "tipo_labor": ("TIPO_LABOR", "Código SIEX", None),
    "especie_animal": ("ESPECIE_ANIMAL", "Código SIEX", None),
    "raza": ("RAZAS", "Código", None),
}
```

### Paso 2 — `tests/services/test_catalogos_importar.py`: engadir ao final do ficheiro

```python


def test_importa_sistema_de_cultivo(session, tmp_path):
    f = _xlsx(tmp_path / "SIST_CULTIVO.xlsx",
              ["Código SIEX", "Sistema de cultivo", "Observaciones", "Fecha de alta",
               "Fecha de modificación", "Fecha de baja"],
              [["1", "Aire libre", None, "30/06/2023", None, None],
               ["9", "Bodega Sacos", "Setas/champiñones", "30/06/2023", None, None]])
    importar_catalogo(session, "sistema_cultivo", f)
    valores = {v.codigo: v.descricion for v in session.query(CatalogoValor)}
    assert valores == {"1": "Aire libre", "9": "Bodega Sacos"}


def test_importa_razas_coa_columna_codigo(session, tmp_path):
    f = _xlsx(tmp_path / "RAZAS.xlsx",
              ["Código", "Raza", "Especie", "Clasificación", "Grado de amenaza"],
              [["1", "Galiña de Mos", "Gallinas", "Autóctona", "En peligro"]])
    importar_catalogo(session, "raza", f)
    assert session.query(CatalogoValor).one().descricion == "Galiña de Mos"
```

## Criterios de aceptación

- `CATALOGOS_XERAIS` ten 34 catálogos (13 de antes + 21 novos).
- Os 2 tests novos pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- `src/horta/services/catalogos_importar.py`: engadíronse 21 catálogos ao dicionario `CATALOGOS_XERAIS` (sistema_cultivo, destino_cultivo, certificacion_ecoloxica, sistema_explotacion, actividade_agraria, causa_baixa, procedencia_material_vexetal, tipo_cobertura_solo, rexime_tenencia, destino_colleita, destino_restos, material_fertilizante, tipo_fertilizacion, metodo_fertilizacion, tratamento_estercos, material_analizado, tipo_analise, orixe_auga, sistema_rega, tipo_labor, especie_animal, raza).
- `tests/services/test_catalogos_importar.py`: engadíronse 2 tests (`test_importa_sistema_de_cultivo` e `test_importa_razas_coa_columna_codigo`).
- Comprobacións: `ruff check` (passed), `mypy` (no issues), `pytest` (248 passed).
- Commit: `smoth/026-importar-mais-catalogos`.

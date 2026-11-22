# Tarefa 031 — Regras do cultivo completo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 030.

## Obxectivo

Regras do deseño `2026-10-23-cultivo-e-colleitas-design.md` §1: superficie > 0 e non maior ca da parcela, datas coherentes, árbores ou marco (non os dous), data de conversión só en conversión, códigos de catálogo vixentes; e o estado calcúlase coas datas (planificado / en_curso / rematado).

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `tests/services/test_cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: importar date e validar_codigo

Antes:
```python
from typing import Any
```

Despois:
```python
from datetime import date
from typing import Any
```

### Paso 2 — mesmo ficheiro

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
```

### Paso 3 — mesmo ficheiro: funcións novas antes de crear_cultivo

Antes:
```python
def crear_cultivo(
```

Despois:
```python
_CATALOGOS_CULTIVO = {
    "sistema_cultivo": "sistema_cultivo",
    "sistema_explotacion": "sistema_explotacion",
    "destino": "destino_cultivo",
    "actividade_agraria": "actividade_agraria",
    "certificacion_ecoloxica": "certificacion_ecoloxica",
    "causa_baixa": "causa_baixa",
    "procedencia_material": "procedencia_material_vexetal",
    "tipo_cobertura_solo": "tipo_cobertura_solo",
}
_EN_CONVERSION = "3"
_CAMPOS_REA = (
    "superficie_ha", "tipo_inicio", "data_inicio", "data_fin", "data_colleita_prevista",
    "num_arbores", "marco_plantacion", "data_inicio_conversion", "data_fin_sementeira",
    "cantidade_semente_kg", "dose_sementeira_kg_ha", "densidade_plantas_ha",
    "material_adquirido", "data_adquisicion_material", "lote_material", *_CATALOGOS_CULTIVO,
)


def calcular_estado(cultivo: Cultivo, hoxe: date | None = None) -> str:
    """planificado / en_curso / rematado segundo as datas de inicio e fin."""
    hoxe = hoxe or date.today()
    if cultivo.data_fin is not None and cultivo.data_fin <= hoxe:
        return "rematado"
    if cultivo.data_inicio is not None and cultivo.data_inicio <= hoxe:
        return "en_curso"
    return "planificado"


def _valores_rea(cultivo: Cultivo | None, cambios: dict[str, Any]) -> dict[str, Any]:
    return {c: cambios.get(c, getattr(cultivo, c, None)) for c in _CAMPOS_REA}


def _validar_rea(session: Session, valores: dict[str, Any], parcela: Parcela | None) -> None:
    superficie = valores["superficie_ha"]
    if superficie is not None:
        if superficie <= 0:
            raise OperacionNonPermitidaError("A superficie do cultivo ten que ser maior que 0")
        if parcela is not None and parcela.superficie and superficie > parcela.superficie:
            raise OperacionNonPermitidaError("A superficie do cultivo é maior ca da parcela")
    if valores["tipo_inicio"] not in (None, "sementeira", "plantacion"):
        raise OperacionNonPermitidaError("Tipo de inicio non válido")
    inicio = valores["data_inicio"]
    for campo, texto in (("data_fin", "de fin"), ("data_colleita_prevista", "de colleita")):
        if inicio is not None and valores[campo] is not None and valores[campo] < inicio:
            raise OperacionNonPermitidaError(f"A data {texto} non pode ser anterior á de inicio")
    if inicio is not None and valores["data_fin_sementeira"] is not None:
        if valores["data_fin_sementeira"] < inicio:
            raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    # CUE 6: cantidade, dose, densidade e marco exclúense entre si
    medidas = [c for c in ("cantidade_semente_kg", "dose_sementeira_kg_ha",
                           "densidade_plantas_ha", "marco_plantacion") if valores[c]]
    if len(medidas) > 1:
        raise OperacionNonPermitidaError(
            "Indica só un: cantidade de semente, dose por hectárea, plantas por hectárea "
            "ou marco de plantación"
        )
    if valores["material_adquirido"] and valores["data_adquisicion_material"] is None:
        raise OperacionNonPermitidaError("Indica a data en que se adquiriu a semente ou planta")
    if valores["num_arbores"] is not None and valores["marco_plantacion"]:
        raise OperacionNonPermitidaError(
            "Indica o número de árbores ou o marco de plantación, non os dous"
        )
    if (
        valores["data_inicio_conversion"] is not None
        and valores["certificacion_ecoloxica"] != _EN_CONVERSION
    ):
        raise OperacionNonPermitidaError(
            "A data de conversión só se indica se o cultivo está en conversión a ecolóxico"
        )
    na_data = inicio or date.today()
    for campo, catalogo in _CATALOGOS_CULTIVO.items():
        if valores[campo]:
            validar_codigo(session, catalogo, str(valores[campo]), na_data)


def crear_cultivo(
```

### Paso 4 — mesmo ficheiro: validar e calcular o estado ao crear

Antes:
```python
    _validar_datas(campos.get("data_sementeira"), campos.get("data_colleita_real"))
    estado = campos.pop("estado", "planificado")
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, estado=estado, **campos)
```

Despois:
```python
    _validar_datas(campos.get("data_sementeira"), campos.get("data_colleita_real"))
    _validar_rea(session, _valores_rea(None, campos), session.get(Parcela, parcela_id))
    estado = campos.pop("estado", None)
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, **campos)
    cultivo.estado = estado or calcular_estado(cultivo)
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)

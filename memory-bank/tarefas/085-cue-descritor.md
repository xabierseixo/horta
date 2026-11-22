# Tarefa 085 — CUE (1/3): o descritor oficial e o comprobador

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

A app le o descritor oficial do CUE (FEGA, Anexo VI v3.11.4) e comproba os datos contra el: obrigatorios, ocorrencias, tipos, lonxitudes, datas e números. Deseño: `docs/superpowers/specs/2026-10-29-cue-design.md` (paso 6 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/services/cue_descritor.py` (**ficheiro novo**)
- `tests/services/test_cue_descritor.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/cue_descritor.py`

Contido completo:
```python
"""O descritor oficial do CUE (FEGA, Anexo VI v3.11.4, folla «EstructuraCuadernoWS») lido tal
cal do CSV, e un comprobador dos datos contra el: obrigatorios, ocorrencias, tipos,
lonxitudes, datas e números (docs/superpowers/specs/2026-10-29-cue-design.md).

O descritor non se copia a man: se o FEGA publica outra versión, cámbiase o CSV."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

VERSION = "3.11.4"
_CSV = Path(__file__).resolve().parents[1] / "data" / f"cue-descriptor-ws-v{VERSION}.csv"
_OCORRENCIA = re.compile(r"^(\d+)(?:\.\.(\d+|n))?$")
_TIPO = re.compile(r"^(string|number|date|boolean)(?:\((\d+)(?:,(\d+))?\))?$")


@dataclass
class Nodo:
    """Un bloque (con fillos) ou un campo do descritor."""

    nome: str
    obrigatorio: bool = False
    minimo: int = 0
    maximo: int | None = 1  # None: sen límite (n)
    tipo: str | None = None  # string, number, date, boolean; None nos bloques
    lonxitude: int | None = None
    decimais: int | None = None
    descricion: str = ""
    observacions: str = ""
    fillos: list[Nodo] = field(default_factory=list)

    @property
    def e_bloque(self) -> bool:
        return self.tipo is None

    def fillo(self, nome: str) -> Nodo | None:
        return next((f for f in self.fillos if f.nome == nome), None)


@dataclass(frozen=True)
class Erro:
    ruta: str  # p.ex. CUADERNO/ActividadesExplotacion/Riego[2]/FechaInicio
    mensaxe: str


def _nivel_e_nome(fila: list[str]) -> tuple[int, str] | None:
    for nivel, celda in enumerate(fila[:7]):
        if celda.strip():
            return nivel, celda.strip()
    return None


def _ocorrencia(texto: str) -> tuple[int, int | None] | None:
    m = _OCORRENCIA.match(texto.strip())
    if not m:
        return None
    minimo = int(m.group(1))
    if m.group(2) is None:
        return minimo, minimo
    return minimo, None if m.group(2) == "n" else int(m.group(2))


@cache
def descritor() -> Nodo:
    """A árbore do descritor oficial (CUADERNO e todos os seus bloques e campos)."""
    filas = list(csv.reader(_CSV.open(encoding="utf-8")))[1:]
    raiz = Nodo("raiz", maximo=None)
    pila: list[tuple[int, Nodo]] = [(-1, raiz)]
    for i, fila in enumerate(filas):
        lido = _nivel_e_nome(fila)
        if lido is None:
            continue
        nivel, nome = lido
        # Os nomes do descritor non levan espazos: unha fila con espazos é unha nota de edición
        # do documento oficial (p.ex. «Se quita cantidad y unidad»), non un campo
        if nome == "}" or " " in nome.rstrip("{").strip():
            continue
        while pila[-1][0] >= nivel:
            pila.pop()
        pai = pila[-1][1]
        seguinte = next((_nivel_e_nome(f) for f in filas[i + 1:] if _nivel_e_nome(f)), None)
        tipo = _TIPO.match(fila[8].replace(" ", "")) if len(fila) > 8 else None
        e_bloque = nome.endswith("{") or (
            tipo is None and seguinte is not None and seguinte[0] > nivel)
        nodo = Nodo(nome.rstrip("{").strip(), descricion=fila[10].strip() if len(fila) > 10 else "",
                    observacions=fila[11].strip() if len(fila) > 11 else "")
        if e_bloque:
            ocorrencia = _ocorrencia(fila[7]) or (0, 1)
            nodo.minimo, nodo.maximo = ocorrencia
            nodo.obrigatorio = nodo.minimo > 0
            pila.append((nivel, nodo))
        else:
            nodo.obrigatorio = fila[7].strip() == "*"
            nodo.minimo = 1 if nodo.obrigatorio else 0
            if tipo:
                nodo.tipo = tipo.group(1)
                nodo.lonxitude = int(tipo.group(2)) if tipo.group(2) else None
                nodo.decimais = int(tipo.group(3)) if tipo.group(3) else None
            else:
                nodo.tipo = "string"
        pai.fillos.append(nodo)
    cuaderno = raiz.fillo("CUADERNO")
    assert cuaderno is not None
    return cuaderno


def _erro_valor(nodo: Nodo, valor: Any) -> str | None:
    if nodo.tipo == "boolean":
        return None if isinstance(valor, bool) else "ten que ser true ou false"
    if nodo.tipo == "date":
        if not isinstance(valor, str):
            return "ten que ser unha data dd/mm/aaaa"
        try:
            datetime.strptime(valor, "%d/%m/%Y")
        except ValueError:
            return f"«{valor}» non é unha data dd/mm/aaaa"
        return None
    if nodo.tipo == "number":
        if isinstance(valor, bool) or not isinstance(valor, int | float):
            return "ten que ser un número"
        if nodo.decimais is None and not float(valor).is_integer():
            return "ten que ser un número enteiro"
        texto = f"{abs(valor):.{nodo.decimais or 0}f}"
        enteiros = texto.split(".")[0].lstrip("0")
        if nodo.decimais and round(valor, nodo.decimais) != valor:
            return f"máis de {nodo.decimais} decimais"
        if nodo.lonxitude and len(enteiros) > nodo.lonxitude - (nodo.decimais or 0):
            return f"ten demasiadas cifras (máximo {nodo.lonxitude})"
        return None
    if not isinstance(valor, str):
        return "ten que ser texto"
    if nodo.lonxitude and len(valor) > nodo.lonxitude:
        return f"máis de {nodo.lonxitude} caracteres"
    return None


def validar(datos: dict[str, Any], nodo: Nodo | None = None, ruta: str = "CUADERNO"
            ) -> list[Erro]:
    """Os erros dun bloque (por defecto, un CUADERNO) fronte ao descritor."""
    nodo = nodo or descritor()
    erros: list[Erro] = []
    for clave in datos:
        if nodo.fillo(clave) is None:
            erros.append(Erro(f"{ruta}/{clave}", "non existe no descritor do CUE"))
    for fillo in nodo.fillos:
        valor = datos.get(fillo.nome)
        ruta_fillo = f"{ruta}/{fillo.nome}"
        if valor is None or valor == [] or valor == "":
            if fillo.obrigatorio:
                erros.append(Erro(ruta_fillo, "é obrigatorio"))
            continue
        if not fillo.e_bloque:
            mensaxe = _erro_valor(fillo, valor)
            if mensaxe:
                erros.append(Erro(ruta_fillo, mensaxe))
            continue
        lista = valor if isinstance(valor, list) else [valor]
        if fillo.maximo is not None and len(lista) > fillo.maximo:
            erros.append(Erro(ruta_fillo, f"como moito {fillo.maximo}"))
        if len(lista) < fillo.minimo:
            erros.append(Erro(ruta_fillo, f"polo menos {fillo.minimo}"))
        for n, elemento in enumerate(lista, 1):
            sufixo = f"[{n}]" if fillo.maximo != 1 else ""
            if not isinstance(elemento, dict):
                erros.append(Erro(f"{ruta_fillo}{sufixo}", "ten que ser un bloque"))
                continue
            erros += validar(elemento, fillo, f"{ruta_fillo}{sufixo}")
    return erros
```

### Paso 2 — crear o ficheiro `tests/services/test_cue_descritor.py`

Contido completo:
```python
"""O descritor oficial do CUE (FEGA, Anexo VI v3.11.4) e o comprobador."""

from horta.services.cue_descritor import descritor, validar

ACTIVIDADES = ["EnergiaUtilizada", "ActividadAgraria", "TratamientosPostCosecha",
               "TratamientosEdifInstalaciones", "SiembraPlantacion", "UsoSemillaTratada",
               "Cosecha", "TratamFito", "Fertilizacion", "PlanAbonado", "ComercializacionVD",
               "Analitica", "Pastoreo", "DatosCubierta", "LaboresCulturales", "Riego"]


def test_le_todos_os_bloques():
    cuaderno = descritor()
    assert [f.nome for f in cuaderno.fillo("ActividadesExplotacion").fillos] == ACTIVIDADES
    riego = cuaderno.fillo("ActividadesExplotacion").fillo("Riego")
    cantidade = riego.fillo("Cantidad")
    assert (cantidade.obrigatorio, cantidade.tipo, cantidade.lonxitude, cantidade.decimais) == (
        True, "number", 8, 2)
    assert riego.fillo("DGCs").minimo == 1 and riego.fillo("DGCs").maximo is None


def _cuaderno(**riego):
    base = {"IdAjenaRiego": 1, "FechaInicio": "01/06/2026", "FechaFin": "01/06/2026",
            "SistemaRiego": 6, "Cantidad": 12.5, "UnidadMedida": 3,
            "DGCs": [{"CodigoDGCAjena": 7, "Superficie": 0.1}]}
    base.update(riego)
    return {"CAExplotacion": "12", "IdTitular": "12345678Z", "UnidadGestora": "12345678Z",
            "CodigoRea": "ES150010000001", "ActividadesExplotacion": {"Riego": [base]}}


def test_un_rexistro_correcto_non_ten_erros():
    assert validar(_cuaderno()) == []


def test_detecta_os_erros():
    erros = {e.ruta.rsplit("/", 1)[-1]: e.mensaxe for e in validar(_cuaderno(
        FechaInicio="2026-06-01", Cantidad=1.234, SistemaRiego=None, NumContador="X" * 20,
        Inventado=1, DGCs=[]))}
    assert "data" in erros["FechaInicio"]
    assert "decimais" in erros["Cantidad"]
    assert erros["SistemaRiego"] == "é obrigatorio"
    assert "caracteres" in erros["NumContador"]
    assert "non existe" in erros["Inventado"]
    assert erros["DGCs"] == "é obrigatorio"
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

CUE (1/3): o descritor oficial e o comprobador: feito.

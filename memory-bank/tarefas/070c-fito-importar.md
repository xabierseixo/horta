# Tarefa 070c — Rexistro de fitosanitarios: importador e comando

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 070b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Importar ProductosAutorizados.json e Cultivos.json do MAPA co comando 'horta-catalogos fitosanitarios DIRECTORIO', calculando as pontes cos cultivos (EPPO) e pragas (nome científico) do SIEX. Probado en seco co rexistro real (2.080 produtos, 62.616 usos, 5 s). Deseño: `docs/superpowers/specs/2026-10-25-tratamentos-completos-design.md` §1.

## Ficheiros a tocar

- `src/horta/services/fito_importar.py` (**ficheiro novo**)
- `src/horta/cli_catalogos.py`
- `tests/services/test_fito_importar.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/fito_importar.py`

Contido completo:
```python
"""Importa o rexistro de fitosanitarios do MAPA (ProductosAutorizados.json e Cultivos.json).

Os usos e as pontes cos códigos SIEX substitúense enteiros en cada importación. Os produtos
consérvanse aínda que deixen de figurar, para poder describir os tratamentos antigos.
Importar despois dos catálogos do FEGA: as pontes cruzan cos cultivos e pragas do SIEX.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CultivoSiex
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.services.catalogos_importar import InformeImportacion, _nova_version
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_normalizar import (
    aplicacions_max,
    clave,
    data,
    intervalo_min_dias,
    nome_cientifico,
    numero,
    prazo_seguridade,
    texto,
    unidade_dose,
)

NON_FIGURA = "Non figura"


def _ler(ruta: Path) -> Any:
    if not ruta.exists():
        raise OperacionNonPermitidaError(f"Falta o ficheiro {ruta.name}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _uso(num_rexistro: str, u: dict[str, Any]) -> dict[str, Any]:
    dose_min, dose_max = numero(u.get("Dosis_Min")), numero(u.get("Dosis_Max"))
    ps_tipo, ps_dias = prazo_seguridade(u.get("Plazo Seguridad"))
    return {
        "num_rexistro": num_rexistro,
        "codigo_cultivo": str(u["CodigoCultivo"]),
        "cultivo": texto(u.get("Cultivo")) or "",
        "codigo_agente": str(u["CodigoAgente"]),
        "agente": texto(u.get("Agente")) or "",
        "tipo_usuario": texto(u.get("TipoUsuario")),
        "sistema_cultivo": texto(u.get("SistemaCultivo")),
        "dose_min": dose_min,
        "dose_max": dose_max if dose_max is not None else dose_min,
        "unidade_dose": unidade_dose(u.get("Unidad Medida dosis")),
        "ps_tipo": ps_tipo,
        "ps_dias": ps_dias,
        "aplicacions_max": aplicacions_max(u.get("Aplicaciones")),
        "intervalo_min_dias": intervalo_min_dias(u.get("IntervaloAplicaciones")),
        "condicionamento": (texto(u.get("CondicionamientoEspecifico")) or "")[:2000] or None,
    }


def _pontes(session: Session, cultivos_mapa: list[dict[str, Any]],
            axentes: dict[str, str]) -> None:
    session.query(FitoPonteCultivo).delete()
    session.query(FitoPonteAxente).delete()
    por_eppo: dict[str, list[str]] = {}
    for c in cultivos_mapa:
        for eppo in (c.get("CodigoEppo") or "").split(","):
            if eppo.strip():
                por_eppo.setdefault(eppo.strip().upper(), []).append(str(c["CodigoCultivo"]))
    for siex in session.query(CultivoSiex).filter(CultivoSiex.codigo_eppo.is_not(None)):
        for codigo in por_eppo.get((siex.codigo_eppo or "").upper(), []):
            session.add(FitoPonteCultivo(cultivo_siex_codigo=siex.codigo, codigo_cultivo=codigo))
    por_nome: dict[str, list[str]] = {}
    for codigo_agente, agente in axentes.items():
        por_nome.setdefault(nome_cientifico(agente), []).append(codigo_agente)
    for valor in session.query(CatalogoValor).filter(CatalogoValor.catalogo.in_(TIPOS_PROBLEMA)):
        for codigo_agente in por_nome.get(clave(valor.descricion), []):
            session.add(FitoPonteAxente(catalogo=valor.catalogo, codigo=valor.codigo,
                                        codigo_agente=codigo_agente))


def importar_fitosanitarios(session: Session, directorio: Path) -> InformeImportacion:
    ruta = directorio / "ProductosAutorizados.json"
    produtos = _ler(ruta)["Productos"]
    cultivos_mapa = _ler(directorio / "Cultivos.json")
    informe = InformeImportacion(catalogo="fitosanitarios")
    version = _nova_version(session, "fitosanitarios", ruta, len(produtos))
    if version is None:
        informe.xa_importado = True
        return informe
    existentes = {p.num_rexistro: p for p in session.query(FitoProduto)}
    session.query(FitoUso).delete()
    session.query(FitoMateria).delete()
    vistos: set[str] = set()
    todos_usos: list[dict[str, Any]] = []
    materias: list[FitoMateria] = []
    for p in produtos:
        d = p["DATOSPRODUCTO"]
        num = texto(d["Num_Registro"]) or ""
        vistos.add(num)
        datos = {
            "nome": texto(d.get("Nombre")) or num,
            "titular": texto(d.get("Titular")),
            "estado": texto(d.get("Estado")),
            "data_caducidade": data(d.get("Fecha_Caducidad")),
            "data_cancelacion": data(d.get("Fecha_Cancelacion")),
            "data_limite_venda": data(d.get("Fecha_LimiteVenta")),
        }
        actual = existentes.get(num)
        if actual is None:
            session.add(FitoProduto(num_rexistro=num, version_id=version.id, **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
        for c in p.get("COMPOSICION") or []:
            if texto(c.get("Nombre Sustancia")):
                materias.append(FitoMateria(num_rexistro=num,
                                            sustancia=texto(c.get("Nombre Sustancia")),
                                            concentracion=numero(c.get("Concentracion")),
                                            unidade=texto(c.get("DescripcionNota"))))
        todos_usos += [_uso(num, u) for u in p.get("USOS") or []]
    for num, produto in existentes.items():
        if num not in vistos and produto.estado != NON_FIGURA:
            produto.estado = NON_FIGURA
            informe.baixas += 1
    session.flush()
    session.add_all(materias)
    session.bulk_insert_mappings(FitoUso, todos_usos)  # type: ignore[arg-type]
    axentes = {u["codigo_agente"]: u["agente"] for u in todos_usos}
    _pontes(session, cultivos_mapa, axentes)
    session.commit()
    return informe
```

### Paso 2 — `src/horta/cli_catalogos.py`

Antes:
```python
from horta.services.fertilizantes_importar import importar_fertilizantes
```

Despois:
```python
from horta.services.fertilizantes_importar import importar_fertilizantes
from horta.services.fito_importar import importar_fitosanitarios
```

### Paso 3 — `src/horta/cli_catalogos.py`

Antes:
```python
    p_imp.add_argument("directorio", type=Path)
```

Despois:
```python
    p_imp.add_argument("directorio", type=Path)
    p_fito = sub.add_parser("fitosanitarios", help="importa o rexistro de fitosanitarios do MAPA")
    p_fito.add_argument("directorio", type=Path)
```

### Paso 4 — `src/horta/cli_catalogos.py`

Antes:
```python
        return _importar(args.directorio)
```

Despois:
```python
        return _importar(args.directorio)
    if args.orde == "fitosanitarios":
        with get_session() as session:
            try:
                _imprimir(importar_fitosanitarios(session, args.directorio))
            except OperacionNonPermitidaError as erro:
                print(f"fitosanitarios: {erro}")
                return 1
        return 0
```

### Paso 5 — crear o ficheiro `tests/services/test_fito_importar.py`

Contido completo:
```python
import json

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_importar import NON_FIGURA, importar_fitosanitarios
from horta.services.fito_normalizar import (
    aplicacions_max,
    intervalo_min_dias,
    nome_cientifico,
    prazo_seguridade,
    unidade_dose,
)


def _produto(num, nome, usos, estado="Vigente"):
    return {
        "DATOSPRODUCTO": {"IdProducto": 1, "Num_Registro": num, "Nombre": nome,
                          "Titular": "Empresa", "Estado": estado,
                          "Fecha_Caducidad": "2030-07-31T00:00:00"},
        "COMPOSICION": [{"Nombre Sustancia": "AZUFRE", "Concentracion": 80,
                         "DescripcionNota": "% p/p"}],
        "USOS": usos,
    }


_USO = {"CodigoCultivo": "0102090000000000", "Cultivo": "Patata",
        "CodigoAgente": "8.48.4.5",
        "Agente": "Mildiu de la patata y el tomate, Phytophthora infestans",
        "TipoUsuario": "Profesional", "Dosis_Min": 0.38, "Dosis_Max": 1.25,
        "Unidad Medida dosis": "%", "Plazo Seguridad": "14", "Aplicaciones": "Máx. 5",
        "IntervaloAplicaciones": "7-10 días"}


def _escribir(directorio, produtos):
    (directorio / "ProductosAutorizados.json").write_text(
        json.dumps({"Productos": produtos}), encoding="utf-8")
    (directorio / "Cultivos.json").write_text(json.dumps([
        {"NombreComun": "Patata", "CodigoEppo": "SOLTU", "CodigoCultivo": "0102090000000000"},
    ]), encoding="utf-8")


def _catalogos_siex(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CultivoSiex(codigo=99, nome_oficial="PATATA", codigo_eppo="SOLTU",
                            version_id=v.id))
    session.add(CatalogoValor(catalogo="enfermidade", codigo="77",
                              descricion="Phytophthora infestans", version_id=v.id))
    session.commit()


def test_importa_produtos_usos_e_pontes(session, tmp_path):
    _catalogos_siex(session)
    _escribir(tmp_path, [_produto("ES-001", "FUNXICIDA", [_USO])])
    informe = importar_fitosanitarios(session, tmp_path)
    assert informe.altas == 1
    produto = session.get(FitoProduto, "ES-001")
    assert produto.nome == "FUNXICIDA" and produto.data_caducidade.year == 2030
    assert session.query(FitoMateria).one().sustancia == "AZUFRE"
    uso = session.query(FitoUso).one()
    assert (uso.dose_max, uso.unidade_dose, uso.ps_dias, uso.aplicacions_max,
            uso.intervalo_min_dias) == (1.25, "%", 14, 5, 7)
    ponte = session.query(FitoPonteCultivo).one()
    assert (ponte.cultivo_siex_codigo, ponte.codigo_cultivo) == (99, "0102090000000000")
    axente = session.query(FitoPonteAxente).one()
    assert (axente.catalogo, axente.codigo, axente.codigo_agente) == (
        "enfermidade", "77", "8.48.4.5")


def test_reimportar_igual_non_fai_nada(session, tmp_path):
    _escribir(tmp_path, [_produto("ES-001", "FUNXICIDA", [_USO])])
    importar_fitosanitarios(session, tmp_path)
    assert importar_fitosanitarios(session, tmp_path).xa_importado


def test_produto_que_desaparece_queda_como_non_figura(session, tmp_path):
    _escribir(tmp_path, [_produto("ES-001", "A", [_USO]), _produto("ES-002", "B", [])])
    importar_fitosanitarios(session, tmp_path)
    _escribir(tmp_path, [_produto("ES-001", "A", [_USO])])
    informe = importar_fitosanitarios(session, tmp_path)
    assert informe.baixas == 1
    assert session.get(FitoProduto, "ES-002").estado == NON_FIGURA
    assert session.query(FitoUso).count() == 1


def test_falta_un_ficheiro(session, tmp_path):
    with pytest.raises(OperacionNonPermitidaError):
        importar_fitosanitarios(session, tmp_path)


@pytest.mark.parametrize(("texto", "esperado"), [
    ("14", ("dias", 14)), ("No procede", ("non_procede", 0)), ("NP", ("non_procede", 0)),
    ("10 aire libre, 3 invernadero", ("condicional", 10)), ("", ("sen_dato", None)),
])
def test_prazo_seguridade(texto, esperado):
    assert prazo_seguridade(texto) == esperado


def test_outros_campos():
    assert aplicacions_max("1-3") == 3
    assert intervalo_min_dias("3-4 semanas") == 21
    assert unidade_dose("Kg/Ha") == "kg/ha"
    assert nome_cientifico("Bledos, Amaranthus spp.") == "AMARANTHUS SPP."
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O comando importa o rexistro e as probas pasan.

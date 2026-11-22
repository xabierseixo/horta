# Tarefa 081h — Parte común (9/9): probas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Probas de que todos os traballos levan a parte común e de que a máquina ten que ser da explotación. Probado no navegador o 2026-10-28. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `tests/services/test_parte_comun.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `tests/services/test_parte_comun.py`

Contido completo:
```python
"""A parte común dos traballos (docs/como-e-a-app.md §2.4) é igual en todos."""

from datetime import date

import pytest

from horta.models.traballo import ConMaquina, FeitoPor, ParteComun
from horta.models.tratamento_fito import TratamentoFito
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega
from horta.services.tarefas import _TABOA_E_DATA
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    crear_tratamento_instalacion,
)

HOXE = date(2026, 10, 28)
# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1


def _usuario(session, email):
    usuario = Usuario(nome=email.split("@")[0], email=email, password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


@pytest.mark.parametrize("tipo", sorted(_TABOA_E_DATA))
def test_todos_os_traballos_levan_a_parte_comun(tipo):
    modelo = _TABOA_E_DATA[tipo][0]
    assert issubclass(modelo, ParteComun)
    # No tratamento, quen e as horas van en cada aplicador
    assert issubclass(modelo, FeitoPor) or modelo is TratamentoFito
    for campo in ("notas", "baixa", "uuid", "creado_por", "created_at"):
        assert campo in modelo.__table__.c


@pytest.mark.parametrize("tipo", ["rega", "tratamento_instalacion", "movemento_animal",
                                  "producion_animal", "labor", "abonado", "colleita",
                                  "coidado_animal"])
def test_traballos_con_maquina(tipo):
    assert issubclass(_TABOA_E_DATA[tipo][0], ConMaquina)


def test_rega_garda_a_maquina_da_explotacion(session):
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    cultivo = crear_cultivo(session, ana, crear_parcela(session, ana, horta.id, "P").id,
                            "Millo")
    bomba = crear_maquina(session, ana, horta.id, "Bomba")
    rega = crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE,
                                              persoa_id=QUEN, maquina_id=bomba.id), hoxe=HOXE)
    assert rega.maquina_id == bomba.id and rega.creado_por == ana.id


def test_maquina_doutra_explotacion_non_vale(session):
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    allea = crear_maquina(session, ana, crear_horta(session, ana, "Outra").id, "Remolque")
    with pytest.raises(OperacionNonPermitidaError, match="máquina"):
        crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
            tipo="local", data=HOXE, obxecto="Almacén", nome_comercial="X",
            persoa_id=QUEN, maquina_id=allea.id), hoxe=HOXE)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (9/9): probas: feito.

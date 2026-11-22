# Tarefa 062c — Caderno: tratamentos asesorados (3.1 bis) e semente tratada (3.2)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 062. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O Excel do caderno leva as táboas 3.1 bis (con xustificación, medidas, asesor e validación) e 3.2 (semente tratada, con «Aplica tratamento SI/NON»). Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `tests/services/test_caderno_tratamentos.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
            "Observacións"], filas_trat)
```

Despois:
```python
            "Observacións"], filas_trat)
    ws3 = wb["3 Tratamentos"]
    ws3.append([])
    ws3.append(["3.1 bis REXISTRO DE TRATAMENTOS FITOSANITARIOS DA PARCELA (soamente para "
                "cultivos e superficies obxecto de asesoramento)"])
    ws3.append(["Especie", "Variedade", "Id. parcelas", "Superficie cultivada (ha)",
                "Superficie tratada (ha)", "Praga", "Xustificación da actuación",
                "Alternativas non químicas: tipo de medida", "Intensidade da medida",
                "Data de actuación", "Alternativas químicas: nome comercial",
                "Número de rexistro", "Dose utilizada", "Data de actuación",
                "Eficacia da intervención", "Observacións", "Asesor", "Nº inscrición ROPO",
                "Data de validación"])
    for t in listar_tratamentos_fito(session, actor, horta_id):
        if t.baixa or not no_periodo(t.data_inicio, t.data_fin) or t.asesor is None:
            continue
        asesor = session.get(Persoa, t.asesor.persoa_id)
        praga = ", ".join(describir(session, p.tipo, p.codigo) for p in t.problemas)
        xust = ", ".join(describir(session, "xustificacion", x.codigo) for x in t.xustificacions)
        medidas = ", ".join(describir(session, "tipo_medida_fito", m.tipo_medida)
                            for m in t.medidas)
        intensidade = ", ".join(f"{m.cantidade:g} {describir(session, 'unidade_medida', m.unidade)}"
                                for m in t.medidas if m.cantidade is not None and m.unidade)
        pr = t.produtos[0] if t.produtos else None
        for tc in t.cultivos:
            cv = cultivo_de(tc.cultivo_id)
            ws3.append([
                cv.especie if cv else "", (cv.variedade or "") if cv else "",
                orde_cultivo.get(tc.cultivo_id, ""), _num(cv.superficie_ha) if cv else "",
                _num(tc.superficie_ha), praga, xust, medidas, intensidade,
                _intervalo(t.data_inicio, t.data_fin) if t.medidas else "",
                (pr.nome_comercial or pr.materia_activa or "") if pr else "",
                (pr.num_rexistro or "") if pr else "",
                f"{_num(pr.dose)} {describir(session, 'unidade_medida', pr.unidade)}"
                if pr and pr.dose is not None else "",
                _intervalo(t.data_inicio, t.data_fin) if pr else "",
                describir(session, "eficacia", t.eficacia) if t.eficacia else "",
                t.observacions or "",
                " ".join(x for x in (asesor.nome, asesor.apelidos or "") if x) if asesor else "",
                (asesor.ropo_numero or "") if asesor else "", _data(t.asesor.data)])
    tratadas = [c for c in cultivos if c.material_tratado
                and c.data_inicio and no_periodo(c.data_inicio)]
    ws3.append([])
    ws3.append(["3.2 REXISTRO DE USO DE SEMENTE TRATADA"])
    ws3.append(["Aplica tratamento", "SI" if tratadas else "NON"])
    ws3.append(["Data de sementeira", "Id. parcelas", "Especie", "Variedade",
                "Superficie sementada (ha)", "Cantidade de semente (kg)",
                "Materia activa / Nome comercial", "Nº rexistro"])
    for cu in tratadas:
        ws3.append([_data(cu.data_inicio), orde_cultivo[cu.id], cu.especie, cu.variedade or "",
                    _num(cu.superficie_ha), _num(cu.cantidade_semente_kg),
                    cu.semente_tratamento_produto or "", cu.semente_tratamento_num_rexistro or ""])
```

### Paso 2 — crear o ficheiro `tests/services/test_caderno_tratamentos.py`

Contido completo:
```python
from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from horta.models.tratamento_fito import (
    TratamentoAsesor,
    TratamentoCultivo,
    TratamentoFito,
    TratamentoProduto,
)
from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa


def _filas(session, ana, horta):
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    return [[x for x in f if x not in (None, "")]
            for f in libro["3 Tratamentos"].iter_rows(values_only=True)]


def test_asesorados_e_semente_tratada(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Leira")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2, data_inicio=date(2026, 3, 1),
                       material_tratado=True, cantidade_semente_kg=50,
                       semente_tratamento_produto="Monceren", semente_tratamento_num_rexistro="123")
    asesora = crear_persoa(session, ana, horta.id, "Lúa", e_asesor=True, ropo_numero="R-9")
    t = TratamentoFito(horta_id=horta.id, data_inicio=date(2026, 5, 2),
                       data_fin=date(2026, 5, 2))
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id, superficie_ha=0.2)]
    t.produtos = [TratamentoProduto(tipo_produto="1", nome_comercial="Cobre 50",
                                    num_rexistro="ES-1", dose=2, unidade="5")]
    t.asesor = TratamentoAsesor(persoa_id=asesora.id, data=date(2026, 5, 1))
    session.add(t)
    session.commit()

    filas = _filas(session, ana, horta)
    i = next(n for n, f in enumerate(filas) if f and str(f[0]).startswith("3.1 bis"))
    assert filas[i + 2][:3] == ["Pataca", 1, 0.2]
    assert "Cobre 50" in filas[i + 2] and "Lúa" in filas[i + 2] and "R-9" in filas[i + 2]
    j = next(n for n, f in enumerate(filas) if f == ["3.2 REXISTRO DE USO DE SEMENTE TRATADA"])
    assert filas[j + 1] == ["Aplica tratamento", "SI"]
    assert filas[j + 3] == ["01/03/2026", 1, "Pataca", 0.2, 50, "Monceren", "123"]
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

A folla de tratamentos leva 3.1 bis e 3.2.

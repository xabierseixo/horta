# Tarefa 084a — Varias leiras (2/5): caderno, Diario e plan de abonado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 084. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O caderno pon unha fila por leira (na rega, a auga repartida pola superficie); o Diario di «N leiras»; o plan de abonado conta a superficie de cada cultivo. Deseño: `docs/superpowers/specs/2026-10-28-varias-leiras-design.md` (paso 5 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `src/horta/services/caderno.py`
- `src/horta/services/diario.py`
- `src/horta/services/faltas_caderno.py`
- `src/horta/services/plan_abonado.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/caderno.py`

Antes:
```python
from horta.services.labores import DESBROCE, PODAS, listar_labores
```

Despois:
```python
from horta.services.labores import DESBROCE, PODAS, listar_labores
from horta.services.leiras import superficie_total
```

### Paso 2 — `src/horta/services/caderno.py`

Antes:
```python
        c = cultivo_de(ab.cultivo_id)
        p = parcelas.get(c.parcela_id) if c else None
        fe = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
        npk = nutrientes_do_abonado(session, ab)
        kg_ha = dose_kg_ha(ab.dose, ab.unidade, fe.densidade if fe else None) \
            if ab.dose is not None and ab.unidade else None
        persoa = session.get(Persoa, ab.persoa_id) if ab.persoa_id else None
        provedor = persoas_por_id.get(fe.provedor_id or 0) if fe else None
        maquina = session.get(Maquina, ab.maquina_id) if ab.maquina_id else None
        filas_fert.append([
            _intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(ab.cultivo_id, ""),
            ({SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
                p.secano_regadio, "") if p and p.secano_regadio else ""),
            c.especie if c else "", _num(ab.superficie_ha),
            describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion)
            if ab.tipo_fertilizacion else "",
            describir(session, "material_fertilizante", fe.material) if fe else
            "Abonado en verde",
            fe.nome if fe else "", nome_completo(provedor),
            (provedor.rega or provedor.nif or provedor.nima or "") if provedor else "",
            describir(session, "metodo_fertilizacion", ab.metodo) if ab.metodo else "",
            maquina.alias if maquina else "",
            (persoa.regfer_numero or "") if persoa else "",
            _num(fe.n_pct) if fe else "", _num(fe.p2o5_pct) if fe else "",
            _num(fe.k2o_pct) if fe else "",
            *((_num(getattr(fe, c)) for c in FORMAS_N_P) if fe else ("",) * 5),
            _num(fe.materia_organica_pct) if fe else "",
            _num(kg_ha / 1000) if kg_ha is not None else "",
            *(npk if npk else ("", "", "")),
            ab.albaran_factura or ""])
```

Despois:
```python
        fe = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
        npk = nutrientes_do_abonado(session, ab)
        kg_ha = dose_kg_ha(ab.dose, ab.unidade, fe.densidade if fe else None) \
            if ab.dose is not None and ab.unidade else None
        persoa = session.get(Persoa, ab.persoa_id) if ab.persoa_id else None
        provedor = persoas_por_id.get(fe.provedor_id or 0) if fe else None
        maquina = session.get(Maquina, ab.maquina_id) if ab.maquina_id else None
        # Unha fila por leira, coa súa superficie
        for le in ab.leiras:
            c = cultivo_de(le.cultivo_id)
            p = parcelas.get(c.parcela_id) if c else None
            filas_fert.append([
                _intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(le.cultivo_id, ""),
                ({SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
                    p.secano_regadio, "") if p and p.secano_regadio else ""),
                c.especie if c else "", _num(le.superficie_ha),
                describir(session, "tipo_fertilizacion", ab.tipo_fertilizacion)
                if ab.tipo_fertilizacion else "",
                describir(session, "material_fertilizante", fe.material) if fe else
                "Abonado en verde",
                fe.nome if fe else "", nome_completo(provedor),
                (provedor.rega or provedor.nif or provedor.nima or "") if provedor else "",
                describir(session, "metodo_fertilizacion", ab.metodo) if ab.metodo else "",
                maquina.alias if maquina else "",
                (persoa.regfer_numero or "") if persoa else "",
                _num(fe.n_pct) if fe else "", _num(fe.p2o5_pct) if fe else "",
                _num(fe.k2o_pct) if fe else "",
                *((_num(getattr(fe, c)) for c in FORMAS_N_P) if fe else ("",) * 5),
                _num(fe.materia_organica_pct) if fe else "",
                _num(kg_ha / 1000) if kg_ha is not None else "",
                *(npk if npk else ("", "", "")),
                ab.albaran_factura or ""])
```

### Paso 3 — `src/horta/services/caderno.py`

Antes:
```python
        ws7.append([_intervalo(ab.data_inicio, ab.data_fin), orde_cultivo.get(ab.cultivo_id, ""),
                    describir(session, "material_fertilizante", fr.material), _num(dose),
                    *(_num(getattr(fr, m)) for m in METAIS_RESIDUO)])
```

Despois:
```python
        for le in ab.leiras:
            ws7.append([_intervalo(ab.data_inicio, ab.data_fin),
                        orde_cultivo.get(le.cultivo_id, ""),
                        describir(session, "material_fertilizante", fr.material), _num(dose),
                        *(_num(getattr(fr, m)) for m in METAIS_RESIDUO)])
```

### Paso 4 — `src/horta/services/caderno.py`

Antes:
```python
        c = cultivo_de(r.cultivo_id)
        m3_ha = (r.cantidade * _A_M3.get(r.unidade, 0) / r.superficie_ha
                 if r.superficie_ha and r.cantidade else None)
        if m3_ha is not None:
            acumulado[r.cultivo_id] = acumulado.get(r.cultivo_id, 0) + m3_ha
        filas_rega.append([
            orde_cultivo.get(r.cultivo_id, ""), _num(r.superficie_ha),
            describir(session, "sistema_rega", r.sistema_rega) if r.sistema_rega else "",
            _intervalo(r.data_inicio, r.data_fin), _num(m3_ha),
            _num(acumulado.get(r.cultivo_id)),
            _num(c.plan_auga_n_nitrico) if c else "", _num(c.plan_auga_p2o5) if c else ""])
```

Despois:
```python
        # A auga é a total da rega: repártese entre as leiras pola súa superficie, así que os
        # m³/ha son os mesmos en todas
        superficie = superficie_total([leira_rega.superficie_ha for leira_rega in r.leiras])
        m3_ha = (r.cantidade * _A_M3.get(r.unidade, 0) / superficie
                 if superficie and r.cantidade else None)
        for leira_rega in r.leiras:
            c = cultivo_de(leira_rega.cultivo_id)
            if m3_ha is not None:
                acumulado[leira_rega.cultivo_id] = acumulado.get(leira_rega.cultivo_id, 0) + m3_ha
            filas_rega.append([
                orde_cultivo.get(leira_rega.cultivo_id, ""), _num(leira_rega.superficie_ha),
                describir(session, "sistema_rega", r.sistema_rega) if r.sistema_rega else "",
                _intervalo(r.data_inicio, r.data_fin), _num(m3_ha),
                _num(acumulado.get(leira_rega.cultivo_id)),
                _num(c.plan_auga_n_nitrico) if c else "", _num(c.plan_auga_p2o5) if c else ""])
```

### Paso 5 — `src/horta/services/caderno.py`

Antes:
```python
        filas_labor.append([
            orde_cultivo.get(lab.cultivo_id, ""), _num(lab.superficie_ha),
            describir(session, "tipo_labor", lab.tipo_labor),
            _intervalo(lab.data_inicio, lab.data_fin),
            ("SI" if lab.restos_desbroce_no_solo else "NON") if lab.tipo_labor == DESBROCE
            else "",
            ("SI" if lab.restos_poda_no_solo else "NON") if lab.tipo_labor in PODAS else "",
            describir(session, "tipo_cobertura_solo", lab.tipo_cobertura)
            if lab.tipo_cobertura else "",
            (m.tipo_une or "") if m else "", _num(m.potencia) if m else "",
            describir(session, "tipo_enerxia", m.tipo_enerxia) if m and m.tipo_enerxia else "",
            lab.num_repeticions or "", _num(lab.duracion_h)])
```

Despois:
```python
        for leira_labor in lab.leiras:
            filas_labor.append([
                orde_cultivo.get(leira_labor.cultivo_id, ""), _num(leira_labor.superficie_ha),
                describir(session, "tipo_labor", lab.tipo_labor),
                _intervalo(lab.data_inicio, lab.data_fin),
                ("SI" if lab.restos_desbroce_no_solo else "NON") if lab.tipo_labor == DESBROCE
                else "",
                ("SI" if lab.restos_poda_no_solo else "NON") if lab.tipo_labor in PODAS else "",
                describir(session, "tipo_cobertura_solo", lab.tipo_cobertura)
                if lab.tipo_cobertura else "",
                (m.tipo_une or "") if m else "", _num(m.potencia) if m else "",
                describir(session, "tipo_enerxia", m.tipo_enerxia) if m and m.tipo_enerxia else "",
                lab.num_repeticions or "", _num(lab.duracion_h)])
```

### Paso 6 — `src/horta/services/diario.py`

Antes:
```python
        return frozenset({c.parcela_id}) if c else frozenset()

```

Despois:
```python
        return frozenset({c.parcela_id}) if c else frozenset()

    def onde_leiras(ids: list[int]) -> str:
        return onde(ids[0]) if len(ids) == 1 else f"{len(ids)} leiras"

    def parcelas_de(ids: list[int]) -> frozenset[int]:
        return frozenset().union(*(parcela_de(i) for i in ids))

```

### Paso 7 — `src/horta/services/diario.py`

Antes:
```python
            onde(a.cultivo_id), parcela_de(a.cultivo_id), persoas=quen,
            sen_quen=not quen))
    for r in listar_regas(session, actor, horta_id):
        traballos.append(Traballo("rega", r.id, r.data_inicio, True,
                                  texto("sistema_rega", r.sistema_rega),
                                  onde(r.cultivo_id), parcela_de(r.cultivo_id),
                                  persoas=_quen(r.persoa_id), sen_quen=r.persoa_id is None))
    for lab in listar_labores(session, actor, horta_id):
        traballos.append(Traballo("labor", lab.id, lab.data_inicio, True,
                                  texto("tipo_labor", lab.tipo_labor),
                                  onde(lab.cultivo_id), parcela_de(lab.cultivo_id),
```

Despois:
```python
            onde_leiras([le.cultivo_id for le in a.leiras]),
            parcelas_de([le.cultivo_id for le in a.leiras]), persoas=quen,
            sen_quen=not quen))
    for r in listar_regas(session, actor, horta_id):
        traballos.append(Traballo("rega", r.id, r.data_inicio, True,
                                  texto("sistema_rega", r.sistema_rega),
                                  onde_leiras([le.cultivo_id for le in r.leiras]),
                                  parcelas_de([le.cultivo_id for le in r.leiras]),
                                  persoas=_quen(r.persoa_id), sen_quen=r.persoa_id is None))
    for lab in listar_labores(session, actor, horta_id):
        traballos.append(Traballo("labor", lab.id, lab.data_inicio, True,
                                  texto("tipo_labor", lab.tipo_labor),
                                  onde_leiras([le.cultivo_id for le in lab.leiras]),
                                  parcelas_de([le.cultivo_id for le in lab.leiras]),
```

### Paso 8 — `src/horta/services/faltas_caderno.py`

Antes:
```python
            ("superficie", lambda a: not a.superficie_ha),
            ("tipo de fertilización", lambda a: not a.tipo_fertilizacion),
            ("método de aplicación", lambda a: not a.metodo),
            ("boas prácticas", lambda a: not a.boas_practicas),
            ("dose", lambda a: a.fertilizante_id is not None and a.dose is None)]),
        *_contar("Regas", regas, [
            ("superficie", lambda r: not r.superficie_ha),
            ("sistema de rega", lambda r: not r.sistema_rega),
            ("cantidade de auga", lambda r: r.cantidade is None)]),
        *_contar("Labores", labores, [("superficie", lambda lab: not lab.superficie_ha)]),
```

Despois:
```python
            ("superficie", lambda a: any(not le.superficie_ha for le in a.leiras)),
            ("tipo de fertilización", lambda a: not a.tipo_fertilizacion),
            ("método de aplicación", lambda a: not a.metodo),
            ("boas prácticas", lambda a: not a.boas_practicas),
            ("dose", lambda a: a.fertilizante_id is not None and a.dose is None)]),
        *_contar("Regas", regas, [
            ("superficie", lambda r: any(not le.superficie_ha for le in r.leiras)),
            ("sistema de rega", lambda r: not r.sistema_rega),
            ("cantidade de auga", lambda r: r.cantidade is None)]),
        *_contar("Labores", labores, [
            ("superficie", lambda lab: any(not le.superficie_ha for le in lab.leiras))]),
```

### Paso 9 — `src/horta/services/plan_abonado.py`

Antes:
```python
        parte = (abonado.superficie_ha / cultivo.superficie_ha
                 if cultivo.superficie_ha and abonado.superficie_ha else 1.0)
```

Despois:
```python
        # A parte do cultivo que se abonou nesa leira
        superficie = next((le.superficie_ha for le in abonado.leiras
                           if le.cultivo_id == cultivo.id), None)
        parte = (superficie / cultivo.superficie_ha
                 if cultivo.superficie_ha and superficie else 1.0)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Varias leiras (2/5): caderno, Diario e plan de abonado: feito.

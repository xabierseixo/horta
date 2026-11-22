# Diario de traballos, «Apuntar traballo» e apuntar só o mínimo (deseño)

Data: 2026-10-26 · Estado: **aprobado polo usuario** («si», 2026-10-26) · Tarefas 074–074q

Parte de `docs/como-e-a-app.md` §5, paso 1. Sector: farmOS (rexistros con estado), xFarm e Agroptima (partes de traballo e caderno como informe); ver §6 dese documento.

## Principio (acordado co usuario o 2026-10-26)

1. **Apúntase o que se fai.** Os formularios teñen todos os campos, pero só obrigan ao mínimo para saber *que, onde e cando*. O resto énchese se se sabe.
2. **Os informes saen do apuntado** (caderno, CUE, máis adiante o xemelgo).
3. **Se a un informe lle falta algo, avisa e non bloquea**, e pódese completar despois.

Así unha explotación non profesional nunca queda bloqueada polo caderno, e a profesional ve o que lle falta antes de entregalo.

## Mínimo de cada tipo de traballo

| Tipo | Obrigatorio | Antes tamén esixía (agora opcional) |
|---|---|---|
| Rega | cultivo, data | superficie, sistema de rega, cantidade de auga |
| Labor | cultivo, data, tipo de labor | superficie |
| Abonado | cultivo, data, abono (ou abonado en verde) | superficie, tipo, método, boas prácticas, dose |
| Colleita | cultivo, data, cantidade | lote (ponse só: AAAA-CULTIVO-NNN) |
| Tratamento fitosanitario | sen cambios: a quen non é profesional xa non lle pide xustificación, nº de rexistro nin aplicador | — |
| Mostras, tratamento de instalacións, cultivo | sen cambios | — |

Datos: `rega.superficie_ha/sistema_rega/cantidade`, `labor.superficie_ha` e `abonado.superficie_ha/tipo_fertilizacion/metodo` pasan a admitir baleiro (migración `c9e1a3b5d7f0`). O xa gardado non cambia.

Se faltan os catálogos oficiais, os formularios ábrense igual e avisan.

## Que lle falta ao caderno

`services/faltas_caderno.py`: por tipo de traballo, cantos rexistros do período non teñen cada dato que pide o caderno (regas sen sistema, abonados sen método…; tratamentos coa súa comprobación CUE existente). Móstrase en **Informes** só nas explotacións profesionais, cunha ligazón á táboa de cada tipo. Nunca impide descargar o caderno.

## Diario

`services/diario.py` (`listar_traballos`) xunta todos os rexistros coa parte común: tipo, data, feito ou por facer, que, onde e as parcelas. Non hai táboas novas: cada tipo segue na súa.
- **Por facer** (tarefas pendentes; sementeiras con data futura): sempre, sexa cal sexa o período; as sen data primeiro; as atrasadas (data límite pasada) marcadas.
- **Feito**: no período, do máis recente ao máis antigo. Por defecto, os últimos 90 días.
- Filtros: tipo, parcela, estado e período. Filtrar por persoa queda para o paso 4 (rega e colleita aínda non gardan quen o fixo).
- Ao premer un traballo ábrese o seu formulario para corrixilo; unha tarefa leva á sección Tarefas. Quen só pode ler vai á táboa do tipo.
- Con un tipo escollido, ligazón á táboa dese tipo (as súas columnas propias, p.ex. «non colleitar antes do»).

## «Apuntar traballo»

No Diario e no Inicio; no móbil, botón redondo sempre á vista. Primeiro «Que fixeches?» (tratamento, abonado, rega, labor, colleita, sementeira ou plantación, toma de mostras, tratamento en almacén ou instalación, tarefa por facer) e despois o formulario dese tipo, o mesmo de sempre. Os formularios sepáranse das súas páxinas (`dialogo_rega`, `dialogo_labor`… e `ui/dialogo_tarefa.py`) e constrúense a primeira vez que se usan.

## Menú

Inicio (o antigo Resumo) · Diario · Informes · grupo **Explotación**: parcelas, cultivos, animais, equipo, maquinaria e datos da explotación (configurar e datos do caderno; só administración da explotación). As táboas de cada tipo de traballo saen do menú; seguen nas mesmas direccións e chégase desde o Diario.

## Fases futuras comprobadas

- **Paso 3 (tarefas = traballos por facer):** o Diario xa as mostra xuntas; falta que a tarefa leve o tipo e, ao facela, abra o formulario dese tipo.
- **Paso 4 (parte común):** quen e cantas horas en todos os tipos; entón, filtro por persoa.
- **Paso 6 (historial por recurso):** `listar_traballos` filtrado por cultivo ou parcela.
- **Plan de empresa e xemelgo:** len os mesmos rexistros; os datos opcionais que falten avísanse igual ca no caderno.

## Probado

412 probas, ruff e mypy. No navegador (escritorio e móbil, copia da BD): apuntar unha rega só co cultivo, velo no Diario, abrilo para corrixir, os nove formularios desde «Apuntar traballo», Informes co aviso do que falta e o caderno xerado con datos baleiros.

# Análise dos campos da aplicación (2026-10-23)

Revisión de todos os modelos e formularios de horta comparados con:
- o **REA** (Rexistro de Explotacións Agrarias) e o **CUE** (Caderno Dixital) do SIEX, descritores v3.11 / v3.11.4 en `docs/referencia/siex/`;
- o RD 1311/2012 (fitosanitarios), o **RD 1051/2022** (nutrición sostible: plan de abonado, análises, rega), o Reg. UE 2018/848 (ecolóxico), o Reg. UE 2023/564 (rexistro de tratamentos);
- oSIGris e Agroptima (ver `docs/estado-e-evolucion.md`, sección de competidores).

Lenda de prioridade: **P1** = imprescindible (lei/CUE ou a pantalla non serve), **P2** = moi útil, **P3** = mellora.

---

## 0. Problemas comúns a toda a app

| # | Problema | Onde | Prioridade |
|---|---|---|---|
| C1 | As datas escríbense a man como texto `AAAA-MM-DD`; non hai calendario | cultivos, fertilización, tarefas, persoas, maquinaria, tratamentos | P1 |
| C2 | Selectores e campos sen ancho: a etiqueta non se ve (p.ex. "Parcela" en Novo cultivo) | diálogos de crear | P1 |
| C3 | Superficies en unidades distintas: parcelas e fertilización en **m²**, tratamentos en **ha**; o CUE pide ha | parcela, fertilización | P1 |
| C4 | Texto libre onde hai catálogo oficial (especie, variedade, produto, tipo de fertilizante, uso da parcela) | cultivos, fertilización, parcelas | P1 |
| C5 | Os diálogos "Novo X" piden menos campos que os de editar: hai que crear e despois editar | parcelas, cultivos, animais, tarefas | P2 |
| C6 | "Estado" é texto libre con valores fixos no código; non hai historial de cambios | parcelas, cultivos, animais, tarefas | P3 |
| C7 | Sen fotos nin documentos adxuntos (albarás, análises, certificados) | todo | P2 |
| C8 | Sen exportación do caderno (PDF/Excel oficial, ficheiro para o CUE) | todo | P1 (antes do 1/1/2027) |

---

## 1. Explotación (`Horta`)

**Ten**: nome, descrición, profesional si/non, titular, NIF, REAGA, REGA, lat/lon, teléfono.

| Falta | Por que | Prioridade |
|---|---|---|
| Concello e provincia (códigos INE) | REA, informes, filtros por zona | P2 |
| Enderezo | REA, documentos | P3 |
| Tipo de titular e tipo de entidade (catálogos SIEX) | REA | P3 |
| Réxime: ecolóxico (nº operador CRAEGA), produción integrada, outros selos | réximes especiais | P2 |
| Ano de campaña activo | o caderno vai por campañas | P2 |

---

## 2. Parcela

**Modelo**: nome, descrición, superficie, posición, lat/lon, uso/aproveitamento, secano/regadío, SIGPAC (provincia, concello, polígono, parcela, subparcela), xeometría, imaxe, notas, estado.

**Formulario**: só nome, superficie (m²), lat/lon e estado. **Os campos SIGPAC, secano/regadío e uso existen no modelo pero non se poden encher.**

| Falta / fallo | Por que | Prioridade |
|---|---|---|
| Amosar e editar SIGPAC, secano/regadío e uso | xa están no modelo; Anexo III e CUE | P1 |
| SIGPAC completo: falta **agregado, zona e recinto** (a referencia oficial ten 7 partes) | o CUE identifica cada actividade pola **DGC** (delimitación gráfica do cultivo, da solicitude xeoespacial da PAC), que vai sobre recintos SIGPAC | P1 |
| Superficie en **ha** (con 4 decimais) | CUE; C3 | P1 |
| Varios recintos por parcela (unha leira pode ser 2-3 recintos) | CUE; oSIGris o fai | P2 |
| Réxime de tenencia (propiedade, arrendamento...) | REA | P3 |
| Debuxar no mapa e traer a xeometría de SIGPAC | `ui.leaflet` + SIGPAC OGC API | P2 |
| Parcela ecolóxica / en conversión con data de inicio | ecolóxico | P2 |
| Orixe da auga (pozo, rede, comunidade de regantes) | CUE `OrigenAgua`, RD 1051/2022 | P2 |

---

## 3. Cultivo — o máis atrasado

**Modelo**: parcela, especie e variedade (texto), códigos SIEX (sen usar no formulario), 4 datas, cantidade + unidade, notas, estado.

**Formulario "Novo cultivo"**: parcela (sen etiqueta visible), especie e variedade a man. Nada máis.

| Falta / fallo | Por que | Prioridade |
|---|---|---|
| **Superficie (ha)**, por defecto a da parcela | dose/ha dos tratamentos, CUE, rendemento | P1 |
| **Cultivo e variedade do catálogo oficial** (buscador en galego) | CUE; xa temos 1.121 cultivos e 89.154 variedades cargados | P1 |
| Data de inicio e de fin (as 4 datas actuais confunden) | REA `fechaInicio/fechaFin` | P1 |
| Sistema de cultivo (aire libre, invernadoiro, túnel...) | REA, catálogo SIEX | P1 |
| Secano / regadío | REA | P1 |
| Destino (autoconsumo, venda, transformación, gando) | REA, catálogo SIEX | P1 |
| Actividade agraria | REA, catálogo SIEX | P2 |
| Ecolóxico (non / en conversión / certificado) e produción integrada | réximes; catálogo "Certificación ecolóxica" | P1 |
| Selos de calidade (DOP/IGP: Pemento de Herbón, Pataca de Galicia, Grelos de Galicia...) | REA `regimenesDeCalidad` | P2 |
| Orixe do material vexetal: tipo (certificado/propio), provedor, ROPVEG, **lote**, pasaporte fitosanitario | REA; trazabilidade | P2 |
| Leñosos: nº de árbores **ou** marco de plantación, ano de plantación | REA (castiñeiros, viña, kiwi, froitais) | P2 |
| Cogomelos: unidades produtivas, módulos, ciclos/ano, duración do ciclo (non van en ha) | REA "datos adicionais de fungos" | P2 |
| Cultivo anterior e obxectivo de colleita (kg/ha) | plan de abonado, RD 1051/2022 | P2 |
| Causa e data de baixa | REA | P3 |
| **Colleitas como rexistros propios** (ver 4) en vez de "cantidade" única | varias colleitas por cultivo | P1 |

---

## 4. Entidades que non existen e fan falta

| Entidade | Campos principais (do CUE salvo indicación) | Por que | Prioridade |
|---|---|---|---|
| **Colleita** | cultivo, datas inicio/fin, cantidade + unidade, superficie, produto colleitado, finalidade, destino dos restos, maquinaria (CUE `Cosecha`) + **lote** (non o pide o CUE na colleita, si na venda; trazabilidade do Reg. CE 178/2002) | CUE; trazabilidade; balance ecolóxico | P1 |
| **Plan de abonado** | cultivo, necesidades N / P₂O₅ / K₂O (UF), obxectivo de produción, cultivo precedente, ferramenta, asesor e data | RD 1051/2022: obrigatorio dende o **1/9/2026** (data fixada polo RD 934/2025); exentas as unidades de secano ≤ 10 ha e os pastos sen fertilizar (confirmar no BOE consolidado o caso do regadío); CUE `PlanAbonado` | P1 |
| **Análise** (solo, auga, esterco, foliar) | material, data, laboratorio, nº boletín, MO, textura, pH, P, K, N, condutividade | RD 1051/2022, CUE `Analitica` | P2 |
| **Rega** | data, cultivo/parcela, sistema de rega, cantidade + unidade, dose, orixe da auga, **nº de contador**, N e P achegados na fertirrega, enerxía (CUE `Fertirrigacion`) | RD 1051/2022 (rexistro da auga), CUE `BuenasPracticasRiego` | P2 |
| **Venda directa** | data, produto, cantidade, nº factura, lote, comprador | CUE `ComercializacionVD`; lei da cadea alimentaria; plan de empresa | P2 |
| **Labores** (arar, sementar, rozar...) | data, parcela/cultivo, tipo, maquinaria, horas | CUE `ActividadAgraria`; custos | P3 |
| **Almacén de produtos** (fitos e fertilizantes: entradas, saídas, stock) | produto, lote, cantidade, albará | RETO; control de stock como oSIGris | P3 |
| **Gastos e ingresos** | data, concepto, importe, parcela/cultivo | custos por cultivo (Agroptima); plan de empresa AGADER | P2 |

---

## 5. Fertilización — modelo antigo

**Ten**: cultivo, data, superficie (m²), tipo (emenda/fertilizante...), produto e **dose como texto**, N/P/K/C en %, micronutrientes e asesoramento (texto).

Hai que refacela como se fixo cos tratamentos (bloque `Fertilizacion` do CUE):

| Falta / fallo | Prioridade |
|---|---|
| Dose **numérica** + unidade (kg/ha, t/ha, m³/ha) | P1 |
| Tipo de material do catálogo (mineral, esterco, xurro, compost, lodos...) e detalle | P1 |
| Datas inicio/fin, superficie en ha, varios cultivos/recintos | P1 |
| Método de aplicación (catálogo) e enterrado | P1 |
| Estercos: orixe (REGA da granxa provedora, NIMA), tratamento | P2 |
| Provedor (empresa, NIF), albará/factura | P2 |
| Aplicador (persoa, REGFER) e equipo (ROMA) | P2 |
| Ligazón co plan de abonado: aviso se se pasa das necesidades | P2 |

---

## 6. Tratamentos fitosanitarios (fase 1 xa feita)

Modelo completo conforme ao CUE. Pendentes xa coñecidos: formulario con varias filas (varios cultivos/produtos), asesor e medidas non químicas na UI, editar/completar tratamentos antigos, aviso de inspección de maquinaria, tratamentos post-colleita e en instalacións, semente tratada (`UsoSemillaTratada`).

---

## 7. Animais

**Ten**: especie e raza (texto), cantidade, alta/baixa, estado, notas.

| Falta | Por que | Prioridade |
|---|---|---|
| Especie dun catálogo (galiñas, coellos, ovellas, cabras, porcos, abellas...) | consistencia | P2 |
| Finalidade (autoconsumo / produción) e ligazón ao REGA da explotación | o RD 637/2021 obriga a inscribir no REGA **tamén os galiñeiros de autoconsumo** (ata 30 aves sen vender) | P1 |
| Movementos (entradas, saídas, mortes) en vez de só "cantidade" | libro de rexistro gandeiro | P2 |
| Produción (ovos, leite, mel...) | rendemento, vendas | P3 |
| Pastoreo en parcelas | CUE `Pastoreo` | P3 |
| Tratamentos veterinarios | lei do medicamento veterinario | P3 |

---

## 8. Tarefas

**Ten**: descrición, parcela, cultivo, datas, prioridade, estado, notas.

| Falta | Prioridade |
|---|---|
| Persoa asignada | P2 |
| Horas e maquinaria usada (custos, partes de traballo) | P3 |
| Repetición (cada semana, cada ano) | P3 |
| Converter unha tarefa feita nun rexistro (p.ex. "tratar" → tratamento) | P3 |

---

## 9. Persoas e maquinaria

- **Persoas**: completas para o CUE. Falta teléfono/email e relación coa explotación (titular, traballador, familiar) — P3.
- **Maquinaria**: o modelo ten tipo UNE, tipo de enerxía e alugada, **pero o formulario non os amosa** — P2. Falta aviso de inspección vencida — P2.

---

## 10. Revisión 2 (mesmo día): comprobacións e achados novos

Comprobouse cada afirmación contra o código, os 108 catálogos descargados do FEGA (`.playwright-mcp/fega/`) e a normativa. Correccións xa aplicadas arriba (DGC, plan de abonado, REGA). Achados novos:

| # | Achado | Prioridade |
|---|---|---|
| R1 | **Fallo legal na app**: unha explotación *non profesional* con galiñas tamén ten que estar no REGA, pero `requisitos_en_regra` devolve lista baleira se non é profesional e o diálogo de configuración oculta o campo REGA. Hai que pedir o REGA sempre que haxa animais | P1 |
| R2 | Só se importan **13 dos 108 catálogos**. Para cultivos, parcelas e fertilización hai que importar polo menos: `SIST_CULTIVO` (33 valores, inclúe 8 sistemas de cogomelos: bodega/nave × sacos/bandexas/botellas/outros), `DESTINO_CULTIVO` (29), `TIPO_CERTIFICACION_ECOLOGICA` (non certificado / certificado / en conversión), `SIST_EXPLOTACION` (secano/regadío), `ACTIVIDAD_AGRARIA`, `REGIMENES_CALIDAD` (inclúe Pemento de Herbón, Grelos, Pataca, Castaña de Galicia, Faba de Lourenzá, Mel de Galicia...), `MATERIAL_VEGETAL_REPRODUCCION`, `CAUSA_BAJA`, `DEST_COSECHA`, `DEST_RES_VEG`, `MAT_FERTI`, `DETALLE_MATERIAL_FERT`, `TIPO_FERITILIZACION`, `METODO_APLICACION_FERTILIZANTE`, `TRAT_ESTIERCOLES`, `MATERIAL_ANALIZADO`, `TIPO_ANALISIS`, `ORIGEN_AGUA_RIEGO`, `SIST_RIEGO`, `TIPO_LABOR`, `REGIMEN_TENENCIA`, `ESPECIE_ANIMAL`, `RAZAS` | P1 |
| R3 | `requisitos_en_regra` conta como "ten animais" tamén os dados de baixa | P3 |
| R4 | Coa superficie do cultivo, o tratamento pode avisar se a superficie tratada é maior ca do cultivo | P2 |
| R5 | **Membros e Persoas confunden**: *Membros* = contas de usuario que poden entrar na app (admin/editor/lector); *Persoas* = xente que aparece nos rexistros (aplicadores, asesores), teña ou non conta. Propostas: renomear a "Acceso á app" e "Traballadores e asesores", e permitir ligar unha persoa ao seu usuario para non repetir datos | P2 |

## Proposta de orde de traballo

1. **Arranxos comúns** (C1 calendario, C2 anchos, C3 ha) e **R1** (REGA para todos os que teñen animais): tarefas pequenas para smoth.
1b. **Importar os catálogos de R2** (base para todo o que segue).
2. **Cultivo completo + Colleitas** (sección 3 e Colleita): deseño de Claude, implementación por smoth.
3. **Parcela completa** (SIGPAC enteiro, ha, campos ocultos).
4. **Fertilización nova + Plan de abonado + Análises + Rega** (fase 2 do caderno CUE).
5. **Ecolóxico e selos** transversal (explotación, parcela, cultivo, colleita).
6. Animais, vendas, gastos/ingresos, tarefas.
7. Exportación do caderno (PDF/Excel e CUE) — antes do 1/1/2027.

## Estado (2026-10-23): que tarefa resolve cada punto

| Punto | Tarefa |
|---|---|
| C1 calendario | 025 |
| C2 anchos e etiquetas | 024 (feita) |
| C3 hectáreas | 027 |
| C4 catálogos no cultivo | 026 (importar) + 032 (pantalla) |
| §3 cultivo completo | 029 (BD), 031 (regras), 032 (pantalla), 034 (ocos) |
| §4 Colleita | 029, 030, 033 |
| R1 REGA para todos | 023 (feita) |
| R2 catálogos | 026 |
| R4 tratamento ≤ cultivo | 034 |
| R5 Equipo (Persoas + Membros) | pendente de deseño |
| §2 parcela completa (SIGPAC, ha, campos ocultos) | 027 (ha); resto pendente |
| §5 fertilización, plan de abonado, análises, rega | pendente (fase 2 do caderno) |
| §1 explotación (concello, réxime...) | pendente |
| §7 animais, §8 tarefas, §9 maquinaria editable | pendente |
| C5 crear = editar | 032 (cultivos); resto pendente |
| C8 exportación do caderno | pendente (antes do 1/1/2027) |

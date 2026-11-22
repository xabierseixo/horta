# Caderno fase 2: fertilización, rega, plan de abonado e análises (deseño)

Data: 2026-10-25 · Estado: **aprobado e feito** (tarefas 046–053e, 2026-10-25)

Fontes:
- Anexo V CUE bloques 9 (fertilización), 10 (rega) e 13 (analíticas): `docs/campos-oficiais-anexo-v.md`.
- Descritor do servizo web CUE v3.11.4 (bloques `Fertilizacion`, `Riego`, `Analitica`): `docs/referencia/siex/cue-descriptor-ws-v3.11.4.csv`. É máis preciso ca o Anexo V e manda cando discrepan.
- Competencia (2026-10-25): Agroptima, xFarm, Agricolum e as notas de oSIGris en `docs/campos-oficiais-anexo-v.md`, Fonte 2.
- Fases futuras: trazabilidade e plan de empresa (Fonte 3 do mesmo documento).

## Decisións do usuario (2026-10-25)

1. **Un cultivo por rexistro** de abonado e de rega. O CUE tamén vai por cultivo e variedade.
2. **Auga: «non o sei».** A cantidade é obrigatoria no CUE, así que a app axuda a estimala (§3). Non se inventan valores por defecto.
3. **Abonos: sen preferencia.** Decide Claude: «Os meus abonos», creados dende o propio formulario (§1). Todas as apps analizadas gardan o produto unha vez, e é o que precisan o almacén e os custos do plan de empresa.

## O que fan as outras apps e que collemos

| Función | Quen | En horta |
|---|---|---|
| Produto gardado unha vez (riqueza, provedor) | xFarm, Agroptima (almacén), oSIGris | **si**: `fertilizante` |
| Apuntar en menos de medio minuto dende o móbil | Agroptima | **si**: catro campos á vista, o resto pregado |
| kg de N/ha por cultivo comparado cun límite | Agroptima, Agricolum | **si**: comparado coa necesidade do plan de abonado (§4); sen límites legais por zona ata ter a fonte oficial |
| Almacén con entradas e saídas | xFarm, Agroptima | non (fase futura; `fertilizante` xa o permite) |
| Libro de fertilizantes e declaración anual de N | Agricolum | non (exportación, fase futura) |

## Fóra deste deseño

Labores culturais (CUE 5), cuberta do solo (CUE 7), pastoreo (CUE 12), metais pesados e micronutrientes desagregados, almacén, límites legais de N por zona vulnerable, exportación ao CUE.

---

## 1. Os meus abonos — táboa `fertilizante`

Créase dende o diálogo de abonado («Novo abono…»). Non ten pantalla propia nesta fase.

| Campo | Tipo | Obrig. | Orixe |
|---|---|---|---|
| horta_id | FK | si | |
| nome | texto 250 | si | p.ex. «Esterco de vaca», «Nitrofoska 15-15-15»; único por horta |
| material | catálogo MAT_FERTI (23) | si | CUE `Material` |
| fertilizante_siex_codigo | FK `fertilizante_siex` | non | CUE `DetalleMaterial`; ao escollelo énchense material, nome e riqueza |
| n_pct, p2o5_pct, k2o_pct | número 0–100 | non | CUE `Macronutrientes`; son a base do cálculo de N |
| liquido | si/non | non | se si: densidade e unidade (CUE) |
| densidade | número | non | |
| tratamento_estercos | catálogo TRAT_ESTIERCOLES | non | só se o material é esterco (1–10) |
| provedor_nome | texto 150 | se é esterco ou residuo | CUE `EmpresaSuministradora` |
| provedor_nif / provedor_rega / provedor_nima | texto | só un dos tres | CUE: excluíntes entre si; REGA para estercos, NIMA para residuos (18–23), NIF para centro xestor |
| activo | si/non | | ocultalo da lista sen perder o histórico |

## 2. Abonado — táboa `abonado`

Substitúe a `fertilizacion` antiga (en `models/cultivo.py`, sen datos na BD de proba). Baixa lóxica, como tratamentos e colleitas.

**Á vista no formulario:** cultivo, data, abono (lista + «Novo abono…»), dose e unidade. Coa dose e a riqueza móstrase ao momento «= X kg de N/ha».

| Campo | Tipo | Obrig. | Orixe / regra |
|---|---|---|---|
| horta_id, cultivo_id | FK | si | un cultivo (decisión 1) |
| data_inicio, data_fin | data | si | fin ≥ inicio; fin por defecto = inicio |
| superficie_ha | número | si | por defecto a do cultivo; ≤ cultivo |
| fertilizante_id | FK | si salvo abonado en verde | CUE: material obrigatorio se non hai a boa práctica «abonado en verde» |
| dose, unidade | número + catálogo UNIDADES_MEDIDA | si | por hectárea (kg/ha, t/ha, l/ha, m³/ha) |
| tipo_fertilizacion | catálogo (fondo / cobertura / emenda) | si | |
| metodo | catálogo METODO_APLICACION (7) | si | 5 e 6 = fertirrega (§3) |
| boas_practicas | táboa filla `abonado_boa_practica` (catálogo BPF, a importar) | si (1..n) | CUE `BuenasPracticas`; `DeclaraBuenasPracticas` = hai algunha |
| xestion_sostible | si/non | non | CUE `GestionSostInsu` |
| aplicacion_lodos | si/non | si | por defecto non; só ten sentido co material 22 |
| albaran_factura | texto 50 | non | trazabilidade e custos |
| aplicador_persoa_id | FK persoa | non | NIF do aplicador e REGFER (`persoa.regfer_numero`) |
| empresa_servizos_regfer | texto 50 | non | se o abonado o fai unha empresa |
| maquina_id | FK maquina | non | ROMA, tipo UNE, potencia, enerxía e propia saen da máquina |
| num_repeticions, duracion_h_ha | número | non | como en colleitas |
| rega_id | FK rega | se é fertirrega | a fertirrega crea tamén o rexistro de rega (§3) |
| dose_n_auga, dose_p_auga | número (kg/ha) | se é fertirrega | CUE `DosisN` e `DosisP` |
| notas | texto | non | |
| baixa, creado_por, created_at | | | como `colleita` |

**Cálculo:** kg de N/ha = dose (pasada a kg/ha) × n_pct / 100; igual para P₂O₅ e K₂O. É unha función de servizo con probas e non se garda.

## 3. Rega — táboa `rega`

| Campo | Tipo | Obrig. | Orixe / regra |
|---|---|---|---|
| horta_id, cultivo_id | FK | si | un cultivo (decisión 1) |
| data_inicio, data_fin | data | si | |
| superficie_ha | número | si | por defecto a do cultivo |
| sistema_rega | catálogo SIST_RIEGO (8) | si | lembra o último usado nese cultivo |
| cantidade, unidade | número + catálogo UNIDADES_MEDIDA (l ou m³) | si | CUE |
| orixe_auga | catálogo ORIGEN_AGUA_RIEGO | non | por defecto o da parcela (`parcela.orixe_auga`) |
| tipo_enerxia | catálogo TIPENERGIA | non | |
| num_contador | texto 14 | non | |
| boas_practicas | táboa filla `rega_boa_practica` (catálogo BPR, a importar) | non | |
| notas, baixa, creado_por, created_at | | | |

**Axuda para quen non sabe a cantidade (decisión 2):** un botón «Non sei os litros» abre unha calculadora que **non se garda**: minutos × litros por minuto, ou número de regadeiras × litros de cada unha. O resultado enche `cantidade` e pódese corrixir. Non se propón ningún caudal por defecto.

## 4. Plan de abonado — campos en `cultivo`

Van no apartado «Plan de abonado» que xa existe no cultivo, onde están `cultivo_anterior_codigo` e `obxectivo_colleita_kg_ha`.

| Campo | Tipo | CUE |
|---|---|---|
| plan_necesidade_n, plan_necesidade_p2o5, plan_necesidade_k2o | número (UF/ha = kg/ha) | 43–45 |
| plan_ferramenta_sostibilidade | si/non | 48 |
| plan_data | data | 49 |
| plan_auga_n_nitrico, plan_auga_p2o5 | número (mg/l) | 41–42 |

**Comparación:** en Fertilización e no cultivo móstrase «N aplicado: 80 de 120 kg/ha». Sen cores de «ilegal»: a necesidade é do plan, non un límite legal.

## 5. Análises — táboa `analise`

| Campo | Tipo | Obrig. | Orixe |
|---|---|---|---|
| horta_id | FK | si | |
| material_analizado | catálogo (cultivo / produto colleitado / solo / auga) | si | CUE |
| data_mostraxe | data | si | CUE |
| laboratorio, laboratorio_nif, num_boletin | texto | non | CUE |
| tipos | táboa filla `analise_tipo` (catálogo TIPO_ANALISIS) | non | CUE 0..n |
| substancias_detectadas | táboa filla (catálogo de substancias activas, a importar) | non | CUE 0..n |
| parcela_id, cultivo_id | FK | non | CUE `DGCs` |
| colleita_id | FK | non | **trazabilidade**: análise do produto ligada ao lote |
| materia_organica, area, limo, arxila, ph, fosforo_ppm, potasio_ppm, n_total, conductividade | número | non | CUE `ParametrosSuelo`; só se o material é solo |
| notas, created_at, creado_por | | | |

O PDF do boletín irá cando haxa adxuntos (fase futura).

## 6. Catálogos (revisado 2026-10-25: xa estaban descargados)

- **Boas prácticas:** non hai catálogos BPF/BPR separados. `BUENAS_PRACTICAS_AMBITOS` (60, xa importado como `boas_practicas`) ten columnas de ámbito; gárdanse en `categoria` (`fito,fertilizacion,rega`) e cada formulario filtra as súas (tarefa 046c).
- **Detalle de material:** `DETALLE_MATERIAL_FERT` ten 1.243 produtos con material, nome, fabricante, N/P₂O₅/K₂O total, estado (líquido/sólido), densidade e inhibidores. Vai á táboa propia `fertilizante_siex`, como `cultivo_siex` (tarefas 046, 046b).
- **Substancias activas:** `SUST_ACTIVAS` (284) para as análises; importar cando se faga 2g.

## 7. Pantallas

- **Fertilización** (substitúe a sección antiga de `horta_detalle.py`): táboa (data, cultivo, abono, dose, kg N/ha) e diálogo en pasos como o de tratamentos: 1. Que e onde, 2. Como, 3. Máis datos.
- **Rega**: nova sección no menú, en CADERNO, despois de Fertilización.
- **Análises**: nova sección en CADERNO.
- O plan de abonado vai no diálogo do cultivo.

## 8. Orde e reparto

| Paso | Que | Quen |
|---|---|---|
| 2a | catálogo de abonos e ámbitos das boas prácticas (§6) | ornith-88 (046–046c) |
| 2b | `fertilizante` + `abonado`: modelo, migración, servizo con probas | ornith-88 (en tarefas pequenas) |
| 2c | pantalla Fertilización nova | ornith-88 |
| 2d | quitar `fertilizacion` antiga: modelo, servizo, sección e probas | **qwen-66** (limpeza) |
| 2e | `rega` + calculadora | ornith-88 |
| 2f | plan de abonado no cultivo + comparación de N | ornith-88 |
| 2g | `analise` | ornith-88 |
| — | textos de axuda dos campos novos | Claude |

Cada paso leva proba en seco antes de lanzalo, como sempre.

## 9. Fases futuras comprobadas

- **Trazabilidade:** abonados e regas por cultivo → lote (colleita), e análise ligada ao lote.
- **Plan de empresa:** `albaran_factura` e `fertilizante` permiten custos por produto; a rega dá o consumo de auga.
- **Almacén:** `fertilizante` é o produto do almacén.
- **Exportación CUE:** os nomes e catálogos seguen o descritor v3.11.4.

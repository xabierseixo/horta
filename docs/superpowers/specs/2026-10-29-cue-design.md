# CUE: os datos do caderno dixital co formato oficial (paso 6 do deseño global)

Data: 2026-10-29 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §8 (informes). Tarefas 085–.

## Fontes

- **RD 1311/2012, art. 16.1** (modificado polo RD 1039/2025): desde o 1/1/2027 o rexistro de tratamentos das explotacións profesionais é o caderno dixital (CUE) do SIEX.
- **Descritor oficial do FEGA**, Anexo VI v3.11.4 (`docs/referencia/siex/cue-descriptor-ws-v3.11.4.csv`): os campos de cada bloque, se son obrigatorios, o seu tipo, o seu formato e o catálogo.
- **Como se entrega en Galicia** (DOG do 8/5/2024, orde do CUE comercial; comprobado o 2026-10-29):
  - o caderno público da Xunta (XEAGA) **non importa ficheiros**: alí os datos métense a man;
  - **o envío automático** só o pode facer un **CUE comercial**: a empresa que fai o programa comunícao á Xunta (MR407B), e cada titular autorízao (MR407D, ou MR407C para unha entidade xestora); despois conéctase ao servizo REST/JSON da Xunta (Anexo VI: `comunicacionProductor`, `crear`, `comprobarEstado`).
  - Presentar o MR407B é unha decisión do usuario e un trámite oficial: a app non o fai.

## Que fai a app neste paso

1. **Os datos do CUE co formato oficial:** un `CUADERNO` en JSON tal como o pide o método `crear` do Anexo VI, para un período.
2. **Comprobación contra o descritor oficial:**
   - a app le o descritor do FEGA tal cal (o CSV), e non unha copia escrita a man;
   - comproba os obrigatorios, os tipos, as lonxitudes, as datas (dd/mm/aaaa), os números (enteiros e decimais) e os catálogos.
   - O que falla tradúcese a «que traballo e que dato falta», e enlaza co traballo para completalo.
3. **Informe «Para pasar ao XEAGA»:** un Excel cunha folla por bloque, na orde e cos nomes dos formularios do caderno público, para quen o teña que meter a man.
4. **Para despois do MR407B:** o mesmo JSON é o que se enviará. A conexión (autenticación do titular, `crear`, `comprobarEstado`) farase cando o usuario o decida.

## Como se monta cada bloque

**Leiras (DGC):**
- Sen conexión co REA, cada cultivo vai como **DGC allea** (`AltaDGC`, `CodigoDGCAjena` = id do cultivo na app).
- Leva a referencia SIGPAC da súa parcela (provincia, concello, agregado, zona, polígono, parcela, recinto), a superficie, as datas, o cultivo e a variedade oficiais, o secano ou regadío e o sistema de cultivo.
- Se falta a referencia SIGPAC, avísase: sen ela o CUE non acepta a leira.

**Actividades:** cada rexistro leva un `IdAjena…` (o id na app) para poder corrixilo ou borralo despois sen duplicar.

| Bloque do CUE | Sae de |
|---|---|
| `SiembraPlantacion` | o cultivo (sementeira ou plantación) |
| `TratamFito` | tratamento fitosanitario (as súas leiras, problemas, xustificacións, produtos, aplicadores, máquinas e asesor) |
| `TratamientosPostCosecha` e `TratamientosEdifInstalaciones` | tratamento en instalacións |
| `Fertilizacion` | abonado (unha DGC por leira) |
| `Riego` | rega (unha DGC por leira, coa auga repartida pola superficie) |
| `LaboresCulturales` | labor (unha DGC por leira) |
| `Cosecha` | colleita |
| `Pastoreo` | pastoreo |
| `ComercializacionVD` | saídas de venda dos lotes de colleitas (tipo 0 venda directa, 1 almacén ou cooperativa) |
| `Analitica` | análise |
| `PlanAbonado` | plan de abonado do cultivo |
| `EnergiaUtilizada` | (paso 7: entradas de enerxía) |

- **Unidades:** as unidades da app tradúcense ao catálogo oficial (kg → 5, t → 6, l → 4, m³ → 3…).
- **Booleanos:** `true` ou `false`.

## Onde aparece

En **Informes → CUE**:
- o período;
- «Descargar os datos do CUE (JSON)»;
- «Descargar para pasar ao XEAGA (Excel)»;
- a lista do que falta, por traballo, con ligazón para completalo.

O caderno da Xunta en Excel segue como está (vale en papel ata o 31/12/2026).

## Probas previstas

- O descritor lese enteiro: cada bloque, campos e obrigatorios.
- O validador detecta un obrigatorio que falta, un tipo mal, unha lonxitude longa e unha data mal escrita.
- Cada bloque cos datos dunha explotación de proba pasa a validación, e o que falta tradúcese ao traballo.
- Unidades e booleanos.
- Excel do XEAGA: unha folla por bloque.
- No navegador: descargar os dous ficheiros e ver o que falta.

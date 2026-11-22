# Análise dos lotes (2026-10-29)

O usuario non ve claro que representa o lote (paso 4, `docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md`) nin onde van cousas que fai todos os días: **clasificar por tamaños ou calidades** e **decidir como se agrupan os ovos** (por día, por semana…). Este documento ordena a parte antes de tocar código. **Feito o 2026-10-29** («adiante e codifica»): §6.2 e §6.3. Tamén a ficha de trazabilidade e simulacro de retirada (§6.4, §6bis): botón «Trazabilidade» en Lotes.

## 1. Que é un lote

Definición legal (Directiva 89/396/CEE, trasposta polo RD 1808/1991; texto por confirmar no BOE): **o conxunto de unidades dun alimento producidas ou envasadas en circunstancias practicamente idénticas.** Dito doutro xeito: o que comparte orixe e historia, de modo que, se hai un problema nunha parte, afecta a todo.

Para que serve (Reg. CE 178/2002, art. 18): **saber de onde veu e a onde foi** cada cousa que vendes (un paso atrás e un paso adiante). Se hai un problema, retírase só ese lote, non toda a produción.

Na app hoxe mestúranse tres ideas distintas que conveñen separar:

| Idea | Pregunta | Exemplo | Onde vai |
|---|---|---|---|
| **Orixe** | de onde vén? | leira do río, colleita do 10/9 | colleita ou produción dos animais (xa existe) |
| **Lote** | que vai xunto ao vender? | o número na caixa ou na factura | ficha de lote (xa existe) |
| **Clase** | como é? | grande, mediana, miúda; extra, primeira | **non existe** |

Regra: **a clase non cambia o lote**. As patacas grandes e as miúdas da mesma colleita son o mesmo lote, porque teñen a mesma orixe e a mesma historia. A clase é unha característica do que se vende.

## 2. Que se fai co produto entre a colleita e a venda

| Operación | Que pasa | Exemplo | Na app hoxe |
|---|---|---|---|
| **Entrar** | o colleitado ou producido entra nun lote | 300 kg de pataca → lote 001 | si |
| **Xuntar** | varias entradas van ao mesmo lote | ovos de luns a domingo → «ovos semana 44»; mel de varias colmeas | si, escribindo o mesmo código (pouco claro) |
| **Clasificar** | o lote repártese por clases e sae refugo | 001 → 150 G, 100 M, 40 P, 10 refugo | **non** |
| **Dividir (saír)** | sae unha parte: venda, casa, perda, animais | 100 kg á tenda de Lalín | si |
| **Mesturar lotes** | dous lotes xa feitos van xuntos | sobras de 001 e 002 nun saco | **non** |
| **Transformar** | un ou varios lotes (e ingredientes mercados) dan un produto novo | leite → queixo; froita → marmelada | **non** (paso 17) |

Xuntar, clasificar, mesturar e transformar son a mesma idea vista en GS1/EPCIS (agregar, desagregar, transformar). Se se modelan ben agora, o xemelgo e a transformación (paso 17) apóianse niso sen refacer.

## 3. Casos por produto

| Produto | Como se fai o lote habitualmente | Clasificación | Ollo |
|---|---|---|---|
| Hortalizas, pataca, froita | un lote por colleita (día e leira) | por calibre e categoría (Extra, I, II), segundo o produto | normas de comercialización: Reg. Delegado (UE) 2023/2429 (categorías e excepcións por confirmar para a venda directa) |
| Ovos | por día de posta ou por envasado (diario ou semanal) | por peso (S, M, L, XL) e calidade (A, B) | **na venda directa exenta (RD 226/2008: na explotación, mercado local ou a domicilio, máx. 50 galiñas no mercado) non se pode usar a clasificación por calidade e peso**. Normas de comercialización: Reg. Delegado (UE) 2023/2465 (aplícase desde o 28/11/2023, substitúe o 589/2008 e quita a data de consumo preferente obrigatoria); o límite de **28 días desde a posta** para vender ao consumidor está no Reg. 853/2004 (modificado polo Reg. Delegado 2022/2258) |
| Mel | por extracción ou por cata | por tipo (milflores, castiñeiro…) | o tipo é unha clase, non outro lote |
| Leite, queixo | leite: por día ou recollida; queixo: por elaboración | — | transformación (paso 17); Reg. 931/2011 (orixe animal) |
| Animais vivos e carne | por animal ou por partida (guía) | — | xa van polas entradas e saídas de animais (libro gandeiro) |
| Cogomelos | por colleita ou recolección | por especie (obrigatorio na etiqueta) | RD 30/2009: a especie é obrigatoria |

Conclusión: **cada explotación decide como agrupa**, pero a decisión adoita ser fixa por produto: «as patacas, un lote por colleita»; «os ovos, un lote por semana».

## 4. Que pide a lei (resumo)

- **Todo alimento que se vende:** poder dicir de quen veu e a quen foi (Reg. 178/2002, art. 18).
- **Orixe animal** (ovos, mel, leite, carne; Reg. de Execución 931/2011): descrición, cantidade, quen o envía, quen o recibe, identificación do lote e data.
- **Venda directa en Galicia** (Decreto 125/2014): rexistro de vendas (produto, cantidade, data, lugar) e etiqueta co titular e o nº REAGA.
- **Ovos:** ver a táboa. A exención da venda directa importa: o pequeno produtor pode non ter que clasificar, e mesmo non pode facelo con esas denominacións.

## 5. Como está a app hoxe

- `lote`: código, produto, unidade, data e categoría da venda directa. Nel entran colleitas e producións dos animais; del saen as saídas (`lote_saida`). O que queda calcúlase.
- O código proponse (AAAA-PRODUTO-NNN). Para xuntar varios días hai que escribir a man o mesmo código.
- Falta: **clases**, **clasificación**, **mesturar lotes**, **como agrupa cada produto** e (máis adiante) **transformación**.

## 6. Proposta, dentro do deseño global

Os lotes non son un módulo á parte: son a pregunta **«que sae?»** do deseño global (`docs/superpowers/specs/2026-10-28-deseno-global-design.md` §1), e todo o que se lles fai son **traballos** coa parte común (§5.1), igual que a colleita ou a venda. Así cada peza nova usa o que xa hai e non se apunta nada dúas veces.

### 6.1 Encaixe en cada pregunta

| Pregunta | Que hai xa | Que engade esta proposta |
|---|---|---|
| **Quen** | persoas, equipo, clientes | quen clasifica ou mestura (como en todo traballo) |
| **Onde e con que** | parcelas, animais, máquinas | — (a orixe do lote xa sae da colleita ou da produción) |
| **Que entra** | **ficha de produto** (insumos: abonos, sementes…) con entradas e **lote do provedor** | o mesmo patrón ao revés: **ficha do produto que sae** (§6.2) |
| **Que se fai** | traballos coa parte común; Diario; Tarefas | **Clasificación** e **Mestura de lotes** como dous tipos de traballo novos; máis adiante **Transformación** (paso 17) coa mesma forma |
| **Que sae** | lote, saídas (venda, casa, perda, animais, transformación) | a saída escolle a **clase**; existencias por clase |
| **Cartos** | importe e cobro de cada venda; horas × custo | as horas de clasificar e mesturar contan no custo, sen nada novo |
| **Tempo** | contexto dos traballos | — |

### 6.2 A ficha do produto que sae (simétrica á dos insumos)

Hoxe o lote garda en texto que produto é e a súa categoría da venda directa; cada lote repíteo. Igual que os insumos teñen a súa ficha (`produto`) e cada compra apunta a ela, os produtos que vendes terían a súa:

| Campo | Para que | Hoxe |
|---|---|---|
| nome, unidade | pataca (kg), ovos (ducias), mel (kg) | repetido en cada lote |
| cultivo oficial ou produto animal | CUE e avisos | repetido en cada lote |
| categoría da venda directa | máximos anuais (Decreto 125/2014) | en cada lote |
| **clases** | grande, mediana, miúda; milflores… | non existe |
| **como agrupa** | un lote por colleita (por defecto), por día, por semana, por mes ou a man | non existe |

- O lote apunta á ficha. Os datos que hoxe repite cada lote pásanse á ficha cunha migración, como se fixo coas persoas (paso 3).
- **Produtos** (Xestión) pasa a ter dúas pestanas, como Persoas: **o que mercas** e **o que vendes**.

### 6.3 Os traballos novos

Cada un ten a parte común (datas, quen, horas, máquina, notas, baixa lóxica, uuid do móbil, fotos, tempo) e por iso aparece só no Diario, en «Apuntar traballo», en Tarefas (tipo «Clasificar»), no historial da persoa, nas fotos e nos Cartos:

- **Clasificación:** lote, e por cada clase canto saíu; o refugo vai como saída (perda ou animais). Despois o lote sabe **canto queda de cada clase**.
- **Mestura de lotes:** de que lotes e canto de cada un → un lote novo que garda as súas orixes.
- **Transformación (paso 17):** a mesma forma que a mestura, pero entran tamén insumos (con lote do provedor) e sae outro produto. Por iso conven deixar a mestura feita con esa idea.

Para quen non clasifica nin mestura, nada cambia: colleita → lote → venda, coma agora.

### 6.4 O que le de aquí cada informe

| Informe | Que le |
|---|---|
| Caderno e CUE (colleita comercializada) | saídas de venda; a clase non cambia nada |
| Rexistro de venda directa (Decreto 125/2014) | vendas e máximos pola categoría da ficha do produto |
| Cartos | importe das vendas; horas de clasificar e mesturar |
| **Trazabilidade do lote / xemelgo** | orixe (colleitas, leira, tratamentos) → clasificación e mesturas → saídas, nunha ficha. É o que ve quen merca no QR |
| Estatísticas (paso 15) | produción por clase e porcentaxe de refugo |

```
QUE ENTRA                         QUE SE FAI                               QUE SAE
Produto que mercas ─ entrada ─┐   colleita / produción ──► LOTE (ficha do produto que vendes)
 (lote do provedor)           │                              │  clasificación ─► existencias por clase
                              └──► (paso 17) transformación ◄┤  mestura ─────► lote novo con orixes
                                                             └► saídas: venda (con clase), casa, perda…
```

## 6bis. Como agrupan os produtos a lexislación e outras apps (investigación do 2026-10-29)

Só co buscador (as páxinas non se puideron abrir desde a sesión); textos legais por confirmar no orixinal.

### Lexislación

| Norma | Que di sobre como se fai un lote |
|---|---|
| **Directiva 2011/91/UE** (substitúe a 89/396/CEE; en España RD 1808/1991) | Lote = **unidades de venda producidas, fabricadas ou envasadas en condicións practicamente idénticas**. **Determínao o produtor ou envasador** en cada caso. Vai precedido de «L». Excepción: produtos agrícolas que saen da explotación cara a un almacén ou centro de envasado |
| **Reg. CE 178/2002, art. 18** | non di como agrupar; si que hai que saber de quen veu e a quen foi |
| **Reg. 931/2011** (orixe animal) | por cada envío: descrición, cantidade, quen envía, quen recibe, **lote** e data |
| **FSMA 204** (EUA, referencia) | o código de lote ponse **ao envasar por primeira vez** e **ao transformar**. Se se mestura ou transforma, **o resultado leva un lote novo ligado aos de orixe**. A leira, a data de colleita e quen colleitou son datos ligados ao lote, non o lote en si |
| **GLOBALG.A.P.** | o lote colleitado ten que ligar coa **parcela** e co que se fixo nela; un **simulacro de retirada ao ano** |
| GS1 froitas e hortalizas / PTI | en cada caixa: produto, **lote** e **data de envasado ou colleita** |
| Ovos (RD 226/2008) | na venda directa exenta non se clasifica por peso nin calidade |

**A lei non fixa como agrupar: decide o produtor**, co criterio de «condicións practicamente idénticas». Na práctica do sector, iso é **mesmo produto + mesma orixe (parcela) + mesmo día** (de colleita ou de envasado).

### Outras apps

| App | Como fai os lotes |
|---|---|
| **farmOS** (libre) | campo de lote na plantación, na sementeira, na colleita e na venda; o inventario leva entradas e saídas |
| **Farmbrite** | **un lote por colleita**, que garda a leira, a cama e a data; o lote créase ao meter a colleita no almacén, e **cada venda escolle de que lote sae** |
| ERP hortofrutícolas (almacéns) | **lote de entrada** na recepción (parcela, variedade, **calibre**, envases) → confección → **lote de saída**, ligado aos de entrada |
| Agroptima, xFarm | rexistran a colleita pero non se atopou un lote ligado á venda |
| Documento do MAPA sobre centrais hortofrutícolas | o agricultor anota parcela, variedade, **calibre** e envases: **o calibre é un dato da partida, non outro lote** |

### O que se confirma para horta

1. **Por defecto, un lote por colleita** (produto + leira + día), que é o que xa fai a app e o que fan Farmbrite e o sector. Para os ovos e o mel, por día ou por envasado (ou o que decida o produtor).
2. **A clase (calibre, categoría) é un dato da partida, non un lote novo:** confírmao a práctica dos almacéns.
3. **Mesturar ou transformar crea un lote novo ligado aos de orixe:** é o que pide a FSMA e o que fan os ERP (entrada → saída). Isto dálle a razón ao traballo «Mestura de lotes» e prepara o paso 17.
4. **Cada venda escolle de que lote sae** (Farmbrite), como xa fai a app.
5. Novo, e encaixa en Informes: **simulacro de retirada** (GLOBALG.A.P.): escolles un lote e a app mostra de onde veu, que se lle fixo e a quen foi. É a mesma ficha de trazabilidade do §6.4.

Fontes: boe.gob.es/doue/2011/334/L00001-00005.pdf (Directiva 2011/91/UE) · arrsys.com/fsma-204-traceability-food-label-requirements-for-2026 · cals.cornell.edu (GAP, trazabilidade) · gs1.org/standards/fresh-fruit-and-vegetable-traceability-guideline/current-standard · globalgap.org/about/impact-areas-and-claims/supply-chain-traceability · help.farmbrite.com/help/traceability-from-harvest-to-sale · farmos.discourse.group/t/traceability-from-seed-to-product/345 · mapa.gob.es (Hort_1999_135_22_34.pdf)

## 7. Para decidir (usuario)

1. ¿Vale a **ficha do produto que vendes** (con clases e como agrupa), simétrica á dos insumos, e que Produtos teña dúas pestanas?
2. ¿Vale a definición do lote («o que vai xunto ao vender, coa mesma orixe») e que a clase non cambie o lote?
3. ¿Que produtos clasificas e con que clases? (Para saber se chega cunha lista libre por produto.)
4. ¿Precisas saber **canto queda de cada clase**, ou chega con apuntar a clase ao vender?
5. Ovos: ¿vendes en venda directa exenta (na casa, mercado local, a domicilio) ou a tendas? Isto decide se se clasifican por peso.
6. ¿Mesturas lotes xa feitos (sobras dunha colleita con outra)? Se non, quedaría para a transformación (paso 17).
7. Orde: ¿facemos isto agora (antes do paso 11b e do 12), ou despois?

## 8. Por verificar no texto oficial

- RD 1808/1991, art. 2: definición literal de lote.
- ~~Reg. Delegado (UE) 2023/2465 (ovos)~~: comprobado o 2026-10-29 (ver táboa).
- Reg. Delegado (UE) 2023/2429: categorías e excepcións para a venda directa ao consumidor.
- Reg. de Execución 931/2011, art. 3: lista exacta de datos.

## Fontes

- https://www.boe.es/eli/es/rd/1991/12/13/1808/con (RD 1808/1991)
- https://www.boe.es/eli/es/rd/2008/02/15/226/con (RD 226/2008) · https://agrinfo.eu/book-of-reports/revised-egg-marketing-standards/translate/es (Reg. 2023/2465)
- https://www.boe.es/doue/2008/163/L00006-00023.pdf (Reg. 589/2008)
- https://www.boe.es/doue/2011/242/L00002-00003.pdf (Reg. 931/2011) · https://www.aesan.gob.es/AECOSAN/web/seguridad_alimentaria/detalle/trazabilidad.htm
- https://boe.es/doue/2023/2429/L00001-00077.pdf (Reg. 2023/2429)

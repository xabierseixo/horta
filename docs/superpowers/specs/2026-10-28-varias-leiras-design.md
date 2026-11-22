# Varias leiras nun traballo (paso 5 do deseño global)

Data: 2026-10-28 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.2. Tarefas 084–.

## Por que

As explotacións galegas teñen moitas leiras pequenas. Rozar, regar ou abonar cinco leiras na mesma mañá é **un traballo**: unha persoa, unhas horas e unha máquina. Hoxe a app obriga a apuntar cinco traballos e a partir as horas a man.

O tratamento e o pastoreo xa admiten varias leiras. Labor, rega e abonado aínda non.

## Que garda

**Táboas fillas** `labor_cultivo`, `rega_cultivo` e `abonado_cultivo`, igual que `tratamento_cultivo`, con dous campos:
- `cultivo_id`;
- `superficie_ha`: por defecto, a do cultivo; non pode pasar da del.

**O traballo** (labor, rega, abonado) deixa de ter `cultivo_id` e `superficie_ha`. Os rexistros de agora pasan a unha fila filla cada un.

**A parte común vai unha vez por traballo:** data, quen, horas, máquina e notas.

**Detalles por tipo:**
- **Labor:** o tipo de labor e os restos son do traballo. A cuberta do chan propónse coa do primeiro cultivo.
- **Rega:** a cantidade de auga é a total. No caderno e no CUE repártese entre as leiras pola súa superficie, e o informe dío así.
- **Abonado:** a dose vai por hectárea e vale para todas as leiras. Os nutrientes de cada cultivo calcúlanse coa súa superficie.

**Normas:**
- polo menos unha leira;
- todas da explotación e sen repetir;
- a superficie de cada unha non pode ser maior que a do seu cultivo.

## Colleita

A colleita segue sendo dunha leira: a cantidade colleitada en cada leira é un dato real, e o CUE (bloque 11) pídea por cultivo.

O formulario permite **escoller varias leiras e poñer o que se colleu en cada unha**. Gárdase unha colleita por leira, todas co mesmo lote, a mesma data e a mesma persoa. As horas repártense entre as leiras pola cantidade colleitada.

## Onde aparece

- **Formularios de labor, rega e abonado:**
  - «Leiras», con escolla de varias, como no pastoreo;
  - a superficie, en «Máis datos», só se hai unha leira.
- **Táboas e Diario:** o nome da leira, ou «N leiras».
- **Caderno (follas de labores, rega e fertilización):** unha fila por leira, como pide o modelo. Na rega, o volume por hectárea de cada leira.

## Probas previstas

- cada traballo con dúas leiras e unha superficie maior ca a do cultivo, que falla;
- leira doutra explotación ou repetida, que falla;
- non se borra un cultivo ou unha parcela con eses traballos;
- o caderno, cunha fila por leira, e na rega o reparto do volume;
- o plan de abonado, cos nutrientes por cultivo;
- a colleita en varias leiras: unha colleita por leira, no mesmo lote;
- o paso dos datos de agora a filas fillas;
- no navegador: rozar tres leiras de vez e velas no Diario e no caderno.

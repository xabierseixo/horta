# Os cartos (paso 10 do deseño global)

Data: 2026-10-29 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §7 e §2bis (CRM).

## Por que

- Saber **o que che deben e o que debes**, por cliente e por provedor.
- Ter **ingresos, gastos e resultado de cada ano** sen apuntar dúas veces o que xa está na app.
- Saber **canto custa cada traballo** (horas × custo da hora da persoa e da máquina). É a base do plan de empresa (paso 16) e do custo efectivo de produción que pide a Lei 12/2013 da cadea alimentaria.

## Regra: non se apunta nada que saia doutro sitio

| Que | De onde sae |
|---|---|
| Ingresos por vendas | saídas de lote de tipo venda (`lote_saida.importe`) |
| Ingresos por venda de animais | saídas de animais (`movemento_animal.importe`, novo) |
| Gastos por compras | entradas de produto (`entrada_produto.importe`) e entradas de animais (`movemento_animal.importe`) |
| Man de obra | horas de cada traballo × `persoa.custo_hora` (novo) |
| Máquinas | horas de cada traballo con máquina × `maquina.custo_hora` (novo) |
| Outros gastos e ingresos | **á man**, táboa nova `apunte_cartos` |

## Que garda

**Cobros e pagos:** `data_pago` (data do cobro ou do pago; baleira = pendente) en:
- `lote_saida` (só nas vendas),
- `entrada_produto`,
- `movemento_animal` (só nas entradas e saídas),
- `apunte_cartos`.

Só conta como pendente o que ten importe. Ao aplicar a migración, o que xa tiña importe márcase cobrado ou pagado na súa data: antes non había onde dicir o contrario, e a venda directa adoita cobrarse ao momento. Pódese cambiar despois.

**`movemento_animal`:** `importe` e `data_pago`, só nas entradas e saídas (venda ou compra de animais).

**`persoa.custo_hora` e `maquina.custo_hora`** (€/hora, opcionais). Úsase o custo de agora para todos os anos: se cambia, cambian as contas dos anos pasados. Gardar o histórico de custos queda para cando se precise.

**`apunte_cartos`** (outros gastos e ingresos), baixa lóxica:

| Campo | Para que |
|---|---|
| `tipo` | gasto ou ingreso |
| `categoria` | seguro, aluguer, auga, luz, combustible, cota, axuda, impostos, reparación, servizos, outro |
| `concepto` | texto (obrigatorio) |
| `data`, `importe` | importe > 0 |
| `persoa_id` | a quen se paga ou quen paga (opcional, contacto) |
| `albaran_factura`, `data_pago`, `notas` | |

## Custo dun traballo

- Horas de quen o fixo (`FeitoPor`): `horas × custo_hora` da persoa.
- Máquina (`ConMaquina`): as mesmas horas × `custo_hora` da máquina.
- Tratamentos: cada aplicador coas súas `horas_utilizacion` e a súa máquina.
- Sementeira: `sementeira_horas` de quen a fixo.
- Tarefas feitas sen tipo («outro traballo» sen formulario): as súas horas. As tarefas feitas cun tipo xa están no seu traballo e non se contan dúas veces.
- Sen horas ou sen custo da hora, ese traballo non suma, e o resumo di cantos traballos quedan sen contar.

## Resumo por período

Por semana (de luns a domingo), mes, trimestre ou ano; escóllese o período entre os doce últimos.


- **Ingresos:** vendas, vendas de animais e outros ingresos (axudas incluídas).
- **Gastos:** compras de produtos, compras de animais, outros gastos, man de obra e máquinas.
- **Resultado:** ingresos − gastos.
- A man de obra do titular e da familia é un custo de oportunidade, non un pago. Móstrase separada para que se vexa o resultado con ela e sen ela.
- Pendente de cobrar e de pagar, por persoa (de calquera ano).

## Onde aparece

- **Cartos** (menú, área Xestión): resumo do ano (escoller o ano), pendente de cobrar e de pagar por persoa, e táboa de outros gastos e ingresos (engadir, editar, dar de baixa, marcar cobrado ou pagado).
- **Formulario de venda e de compra:** «Cobrada»/«Pagada» e a data.
- **Saídas e entradas de animais:** prezo e «Cobrada»/«Pagada».
- **Ficha do equipo e da máquina:** custo da hora.
- **Historial do contacto:** marca o pendente e mostra o total que debe ou se lle debe.

## Permisos

- Cobros e pagos dunha venda ou compra: quen pode apuntala (administrar ou editar).
- Cartos (resumo, outros gastos e ingresos): administrar ou editar. Quen só mira non ve os cartos.
- Custo da hora: quen pode editar a ficha.

## Probas previstas

- crear, editar e dar de baixa un apunte; importe > 0; categoría válida; persoa da mesma explotación;
- data de pago non anterior á data da venda ou compra, nin futura;
- pendente por persoa: vendas sen cobrar, compras e apuntes sen pagar; o pagado non sae;
- custo dun traballo: persoa, máquina, aplicadores do tratamento, sementeira, tarefa sen tipo; sen dobre conta das tarefas con tipo;
- resumo do ano: só ese ano, sen baixas; resultado;
- quen só mira non ve os cartos.

# Lotes e saídas (paso 4 do deseño global)

Data: 2026-10-28 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §6. Tarefas 083–.

## Fontes

- **Decreto 125/2014 (venda directa en Galicia, DOG 30/09/2014, comprobado o 2026-10-28):**
  - **art. 4, canles:** na explotación, en mercados e en tendas, estas últimas sen intermediarios. A domicilio conta como venda directa, igual ca no deseño das vendas.
  - **art. 6, rexistro:** produto, cantidade, data e lugar de cada venda; nas tendas, cal é a tenda. Consérvase 2 anos.
  - **art. 7.3:** os ovos non se venden a tendas.
  - **anexo II, máximos por explotación e ano:**

    | Produto | Máximo ao aire libre | Máximo en invernadoiro |
    |---|---|---|
    | mel | 3.000 kg | — |
    | pole | 450 kg | — |
    | propóleo | 30 kg | — |
    | xelea real | 10 kg | — |
    | ovos | 1.000 ducias | — |
    | amoras | 5.000 kg | 10.000 kg |
    | kiwi | 13.000 kg | — |
    | outras froitas | 20.000 kg | — |
    | hortalizas | 20.000 kg | 40.000 kg |
    | legumes | 10.000 kg | 24.000 kg |
    | patacas | 20.000 kg | — |
    | cogomelos | 500 kg | 2.500 kg |
    | cereais | 5.000 kg | — |

- **CUE 3 (`ComercializacionVD`):**
  - datas, produto, cantidade e unidade;
  - tipo: venda directa ou colleita comercializada;
  - nº de factura ou albará e nº de lote;
  - quen merca (§ persoas).
- **Caderno da Xunta, folla 5 «Colleita comercializada»:** data, produto, kg, parcelas de orixe, albará, lote e cliente.
- **Trazabilidade (Reg. CE 178/2002, art. 18):** saber a quen se entregou cada lote.

## Que garda

**`lote`** (novo): a identidade do produto que sae da explotación.

| Campo | Para que |
|---|---|
| `horta_id`, `codigo` | único na explotación (`AAAA-PRODUTO-NNN`, proposto como agora) |
| `produto` | nome que se ve (Pataca, Ovos…) |
| `cultivo_siex_codigo` ou `produto_animal` | que produto é exactamente: un lote só recolle colleitas do mesmo cultivo oficial, ou producións do mesmo produto |
| `unidade` | a do lote; as entradas e as saídas convértense a ela (t↔kg, ducias↔unidades) |
| `categoria_venda_directa` | para os máximos do anexo II. Nos ovos e no mel ponse soa; nos cultivos escóllese no lote |
| `protexido` | se é de invernadoiro (sistema de cultivo protexido), para o máximo do anexo II |
| `data`, `baixa` | |

**Entradas:**
- a colleita e a produción gardan `lote_id` en vez do texto;
- ao apuntar escríbese o código; se xa existe e é o mesmo produto, a entrada súmase a ese lote (a semana de ovos, ou a pataca de tres leiras); se é outro produto, dá erro;
- o retirado da produción (rotos, tempo de espera) **non entra no lote**: entra o producido menos o retirado.

**`lote_saida`** (novo traballo, coa parte común):

| Campo | Para que |
|---|---|
| `lote_id`, `data`, `data_fin` | de que lote e cando |
| `tipo` | venda, casa, transformación, perda, animais |
| `cantidade`, `unidade` | canto |
| `canle` (só venda) | na explotación, mercado, a domicilio, tenda, almacén ou cooperativa (esta última é «colleita comercializada» no CUE) |
| `lugar` (só venda) | onde (art. 6) |
| `comprador_id` (só venda) | persoa ou entidade co papel cliente |
| `albaran_factura`, `importe` (só venda) | documento e prezo, en euros |

**Normas:**
- non sae máis do que queda no lote;
- non antes da primeira entrada nin no futuro;
- a venda leva canle;
- a tenda leva quen merca;
- os ovos non van a tendas.

**Unha entrada non se pode baixar por debaixo do que xa saíu do seu lote.**

**Avisos (non bloquean):**
- **máximos do anexo II:** suma das vendas directas do ano (todas as canles menos almacén ou cooperativa) da mesma categoría;
- **tempo de espera:** o lote ten produción dun grupo en tempo de espera;
- **prazo de seguridade:** o lote ten unha colleita feita antes de rematar o prazo dun tratamento.

**Os datos de agora:**
- os textos de lote pasan a fichas de lote;
- o cliente e o albará da colleita pasan a unha saída «venda», co cliente como persoa.

## Onde aparece

- **Explotación → Lotes** (no menú):
  - cada lote, co que entrou, saíu e queda, e a súa categoría;
  - botóns «Vender» e «Outra saída»;
  - debaixo, a táboa das saídas.
- **Colleitas e Produción:** columna «Queda» e botón «Vender», co lote xa posto.
- **Diario e «Apuntar traballo»:** tipo «Saída de produto», por exemplo «Venda: 5 kg de Pataca · lote 2026-PATACA-001 · Bar Central».
- **Tarefas:** tipo «Saída de produto».
- **Caderno, folla 5:** sae das vendas dos lotes de colleitas.

## Fases futuras

- **CUE 3:** de aquí. A unidade tradúcese ao catálogo oficial.
- **Rexistro de venda directa (art. 6):** informe.
- **Ingresos (paso 10):** os prezos das vendas.
- **Transformación (paso 17):** unha saída «transformación» crea a entrada dun lote novo.
- **Xemelgo:** historial do lote.

## Probas previstas

**Servizo:**
- lote por código, e unha segunda colleita ou produción que se suma;
- outro produto co mesmo código, que falla;
- queda e conversión de unidades;
- non saír máis do que queda;
- cada tipo de saída garda só os seus datos;
- tenda sen cliente e ovos a tenda, que fallan;
- aviso de máximo anual e de tempo de espera;
- non baixar unha entrada por debaixo do saído;
- Diario e tarefa;
- caderno 5;
- paso dos datos (lotes e clientes da colleita).

**Navegador:** apuntar ovos dúas veces no mesmo lote, vendelos nun mercado e ver o que queda; vender unha colleita a unha tenda.

# Produtos e entradas (paso 7 do deseño global)

Data: 2026-10-29 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §4. Tarefas 086–.

## Por que

Hoxe a compra vai metida dentro de cada uso:
- o albará do abono, en cada abonado;
- o provedor e a proba de compra do medicamento, en cada coidado;
- o provedor, o lote e o pasaporte da semente, en cada cultivo;
- os fitosanitarios non teñen compra.

Na realidade **mércase unha vez e úsase moitas**. Hai que saber de quen se recibiu cada cousa (Reg. CE 178/2002, art. 18), canto queda e canto custou (plan de empresa e paso 10).

## Fontes

- **Reg. (UE) 2019/6, art. 108, e RD 666/2023, art. 41 (rexistro de medicamentos):**
  - a **entrada**: data, medicamento, cantidade recibida, provedor (nome e enderezo) e proba de compra;
  - a **administración**: a que xa garda o coidado.
- **CUE 9 (fertilización):** empresa subministradora (nome, NIF, REGA ou NIMA) e albará ou factura.
- **CUE 6 (sementeira) e pasaporte fitosanitario (Reg. UE 2016/2031):** provedor, lote, data de adquisición e pasaporte da semente ou planta.
- **CUE 2 (enerxía utilizada):** tipo de enerxía, cantidade e unidade, que sae das entradas de enerxía (gasóleo, electricidade).
- **RD 1311/2012:** conservar as facturas dos fitosanitarios.

## Que garda

**`produto`:** cada insumo da explotación.

| Campo | Para que |
|---|---|
| `tipo` | fitosanitario, abono, semente, medicamento, penso, enerxía, outro |
| `nome`, `unidade` | a unidade das existencias: kg, l ou unidades |
| `num_rexistro` | fitosanitario: nº do rexistro do MAPA; medicamento: nº de autorización, se se sabe |
| `fertilizante_id` | abono: a súa composición (a táboa `fertilizante` de agora, que segue igual) |
| `tipo_enerxia` | enerxía: catálogo oficial |
| `activo` | |

**`entrada_produto`:** cada compra ou recepción. É un traballo coa parte común (quen o recibiu).

| Campo | Para que |
|---|---|
| `produto_id`, `data` | |
| `provedor_id` | persoa ou entidade co papel provedor (paso 3) |
| `cantidade`, `unidade` | pode quedar baleira se non se sabe (datos de antes) |
| `lote_provedor`, `albaran_factura`, `importe`, `data_caducidade` | |
| `pasaporte_fitosanitario` | sementes e plantas |

**Os usos apuntan ao produto e, se se sabe, á entrada:**

| Uso | Antes | Despois |
|---|---|---|
| Abonado | `fertilizante_id`, `albaran_factura` | `produto_id` (abono) e `entrada_id`; o albará vai na entrada |
| Tratamento (cada produto) | `num_rexistro`, `nome_comercial` | ademais `produto_id` e `entrada_id`. O nº de rexistro segue: é o que pide o CUE |
| Coidado con medicamento | `medicamento`, `provedor_id`, `proba_compra` | `produto_id` (medicamento) e `entrada_id`; o provedor e a proba de compra van na entrada |
| Cultivo (semente ou planta) | `provedor_material_id`, `lote_material`, `pasaporte_fitosanitario`, `data_adquisicion_material` | `entrada_semente_id`; todo iso vai na entrada |

**Existencias:** o que queda de cada produto é o que entrou menos o que se usou, na unidade do produto.
- **Abonado:** dose × superficie.
- **Tratamento:** a cantidade, ou dose × superficie.
- **Coidado:** a cantidade.
- **Sementeira:** a cantidade de semente.
- Se algún uso non se pode contar (sen cantidade ou noutra unidade), a app avisa en vez de dar un número falso.

**Paso dos datos de agora:**
- Cada `fertilizante` pasa a ser un produto de tipo abono.
- Cada medicamento distinto dos coidados pasa a ser un produto de tipo medicamento.
- Cada semente con provedor ou lote pasa a ser un produto de tipo semente.
- Onde había provedor, albará, proba de compra, lote ou pasaporte, créase unha entrada sen cantidade coa data do uso, e o uso apunta a ela.

## Onde aparece

- **Explotación → Produtos** (no menú, xunto a Lotes):
  - cada produto, co que entrou, o que se usou e o que queda;
  - botón «Nova entrada» (compra) e o historial de entradas.
- **Nos formularios de abonado, tratamento, coidado e cultivo:**
  - escóllese o produto, ou créase un dende o formulario, como coas persoas;
  - opcionalmente, de que entrada sae (proponse a última con existencias).
- **«Apuntar traballo» e Diario:** «Entrada de produto», por exemplo «Entrada: 25 kg de NPK 15-15-15 · Agro Ulla SL».
- **Tarefas:** tipo «Entrada de produto».

## Informes

- **CUE 9:** a empresa subministradora e o albará saen da entrada do abonado.
- **CUE 6:** o provedor, o lote, a data de adquisición e o pasaporte saen da entrada da semente.
- **CUE 2:** as entradas de enerxía.
- **Caderno 3.2 e 7:** os mesmos datos.
- **Rexistro de medicamentos (paso 14):** entradas e coidados.
- **Cartos (paso 10):** o gasto de cada entrada.
- **Xemelgo:** a orixe dos insumos de cada lote.

## Probas previstas

- produto e entrada;
- existencias con usos de cada tipo e conversión de unidades;
- uso sen cantidade, que avisa;
- cada uso garda o produto e a entrada;
- non se borra un produto con entradas ou usos;
- caderno e CUE dende a entrada;
- paso dos datos de agora (abonos, medicamentos, sementes);
- Diario e tarefa;
- no navegador: mercar abono, usalo en dous abonados e ver o que queda.

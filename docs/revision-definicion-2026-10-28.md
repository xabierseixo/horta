# Revisión da definición da app (2026-10-28)

Estado: **aprobada** (2026-10-28); decisións levadas ao deseño global (`docs/superpowers/specs/2026-10-28-deseno-global-design.md`). Feita antes das vendas, porque o usuario notou que a app perde definición ao crecer. O usuario pediu revisala a fondo, pensando como quen fai apps para o sector e non copiando outras apps.

**Base:**
- `docs/como-e-a-app.md` e `docs/modelo-datos.md`.
- As columnas de cada táboa de traballo, comparadas cun script.
- Un percorrido polas pantallas nunha copia da BD: Inicio, Diario, Apuntar traballo, Informes, Parcelas, Cultivos, Animais, Equipo, Maquinaria e Datos da explotación.
- Outras apps (AgriWebb, Farmbrite), só como contraste.

## 1. Como se mira

Unha explotación galega pequena e mixta (horta, froita, galiñas, algunhas vacas ou ovellas, colmeas, venda directa) móvese arredor de seis preguntas. A app ten que responder cada unha nun só sitio:

| Pregunta | Que é | Hoxe na app |
|---|---|---|
| **Quen?** | a xente da casa e a de fóra | Equipo (dentro); a xente de fóra, escrita a man en 12 sitios |
| **Onde e con que?** | terra, animais, instalacións, máquinas | parcelas, cultivos, grupos e máquinas; non hai instalacións |
| **Que entra?** | sementes, abonos, fitosanitarios, medicamentos, pensos | non existe: a compra vai metida dentro de cada uso |
| **Que se fai?** | os traballos | ben resolto (Diario, quen, tarefas), con fallos na parte común |
| **Que sae?** | o produto (lotes) e a onde vai: venda, casa, transformación, perda | o lote é só un texto; non se sabe canto queda nin a onde foi |
| **Canto custa e canto dá?** | gastos e ingresos | aínda non: dependerá de «que entra» e de «que sae» |

**Conclusión principal:** a app fixo moi ben «que se fai», pero non ten «que entra» nin «que sae» como cousas propias. Por iso os provedores, os albarás, os clientes e os lotes acaban escritos dentro dos traballos. O problema dos clientes é só o primeiro síntoma.

## 2. O que se atopou

### 2.1 Quen: catro ideas de persoa mesturadas

Hoxe hai catro sitios con datos de persoas:
- **usuario:** a conta para entrar na app;
- **persoa (Equipo):** quen traballa, co ROPO, as horas e os datos para a UTA;
- **titular** nos datos da explotación (nome e NIF), repetido na persoa coa función «Titular»;
- **xente de fóra** escrita a man en 12 sitios.

**Os 12 sitios con xente de fóra:**
- cliente da colleita;
- titular e REGA nas entradas e saídas;
- REGA no pastoreo de terceiros;
- provedor do abono;
- empresa de servizos no abonado;
- provedor da planta e empresa da semente;
- provedor do medicamento, veterinario e visitante;
- laboratorio;
- asesoramento;
- arrendador da parcela;
- (en deseño) quen merca;
- e os aplicadores e asesores de fóra, que están en Equipo.

**Na realidade a mesma persoa fai varios papeis:**
- o veciño que axuda na vendima e merca ovos;
- o técnico da ADSG que é asesor e veterinario;
- o fillo que traballa e é cotitular.

Unha lista de «clientes» á parte (como fan AgriWebb e Farmbrite) crearía outro silo máis e volvería repetir xente que xa está en Equipo.

O titular e o asesor xa se apuntan en dous sitios (Datos da explotación e Equipo), e o caderno colle un ou outro. Inicio pide o NIF do titular en Datos da explotación aínda que xa estea na persoa titular.

### 2.2 Que entra: a compra metida dentro do uso

| Insumo | Onde se apunta a compra hoxe |
|---|---|
| Abono | provedor no abono; o albará vai en cada **abonado** |
| Medicamento | provedor, proba de compra e receita en cada **coidado** |
| Semente ou planta | provedor, lote e pasaporte fitosanitario en cada **cultivo** |
| Fitosanitario | non se apunta a compra (só o produto do rexistro do MAPA) |
| Penso | non existe |

**Na realidade compras unha vez e úsalo moitas:**
- un saco de abono serve para cinco abonados;
- un frasco de antiparasitario, para tres grupos.

**Hoxe pasa isto:**
- o provedor e o albará escríbense en cada uso;
- non se sabe canto queda;
- non hai custo do que se usou, que é a base do plan de empresa.

**A normativa tamén o separa:**
- o rexistro de medicamentos pide a entrada (data, provedor, cantidade recibida) á parte da administración;
- a trazabilidade (Reg. CE 178/2002, art. 18) pide saber de quen se recibiu cada cousa.

### 2.3 Que sae: o lote é só un texto

- Colleita e produción gardan o lote como texto único. Non hai ficha do lote, nin canto queda, nin a onde foi.
- O produto sae por varios camiños, e só un é a venda:
  - **venda** (directa, a tenda, a almacén ou cooperativa);
  - **casa** (autoconsumo);
  - **transformación** (mermelada, queixo, embutido);
  - **perda** (rotos, podre, o retirado polo tempo de espera);
  - **para os animais** (patacas pequenas ou verdura ás galiñas).
- Os ovos retirados ou as patacas podres xa se apuntan (retirada, destino), pero cada un no seu sitio.
- O primeiro deseño das vendas só restaba o vendido, polo que «queda» sería falso.
- A transformación (paso 17) xunta e divide lotes. Se o lote segue sendo un texto, haberá que refacer as vendas.
- O límite de venda directa (Decreto 125/2014) é por tipo de produto: ovos, mel, hortalizas, froita… Hoxe o produto da colleita é o cultivo, e o da produción é outra lista.

### 2.4 Que se fai: os traballos

**Está ben:**
- todos van ao Diario e a «Apuntar traballo»;
- levan quen os fixo;
- poden saír dunha tarefa;
- o caderno sae deles.

**Fallos:**
- **Un traballo, unha leira.** Labor, rega, abonado e colleita refírense a un só cultivo; o tratamento e o pastoreo, a varios. En Galicia unha explotación ten moitas leiras pequenas: rozar cinco leiras na mesma mañá obriga a apuntar cinco traballos e partir as horas a man. Isto vai contra a regra de apuntar en medio minuto.
- **A parte común non é igual:**
  - máquina: falta en rega, tratamento en instalacións, análise, entradas e saídas, produción e pastoreo (a muxidora ou o remolque non se poden poñer);
  - o tratamento non ten notas nin quen o apuntou;
  - o identificador para o móbil só está en colleita, produción e pastoreo; o deseño da app do móbil pedíao tamén no tratamento, na tarefa e na sementeira;
  - as datas chámanse distinto («data» ou «data_inicio/data_fin»).
- **O tratamento en instalacións** escribe o lugar a man (obxecto e referencia catastral), porque non existen as instalacións.

### 2.5 Onde e con que

- **Estado do cultivo:** non mira os traballos. Na copia da BD, un cultivo con 120 kg colleitados segue «Planificado». O estado sae só das datas; nos animais, en cambio, os cantos saen dos movementos.
- **Animais só por grupos:**
  - vale para galiñas, ovellas, cabras e colmeas;
  - no vacún cada animal leva o seu crotal e o seu documento, e as entradas, saídas e saneamentos van un a un;
  - hoxe o crotal só se pode escribir como texto na entrada ou na saída.
  - Non é para facer xa, pero hai que decidilo antes de que os traballos de animais medren máis.
- **Datos da explotación en dúas xanelas,** con dous campos co mesmo nome «Tipo de explotación»: un é profesional ou non; o outro, o tipo para o asesoramento en pragas.

### 2.6 O documento de como é a app quedou atrás

- A táboa de traballos de §2:
  - non ten entradas e saídas, produción nin pastoreo;
  - aínda pon a venda en «outro traballo» e o cliente na colleita.
- Fala de «animais e lotes»: na app son grupos, e «lote» é o lote do produto.
- Non di nada de «que entra» nin de «que sae».

## 3. Proposta

A idea: completar os dous lados que faltan (**entra** e **sae**) e ter **unha soa lista de xente**. Os traballos quedan no medio, como agora, e collen de aí os datos en vez de escribilos.

### 3.1 Unha soa lista de persoas e entidades

- A táboa de persoas pasa a ser para **toda a xente coa que se trata**, de dentro e de fóra, persoas ou empresas.
- **Cada ficha garda:**
  - nome ou razón social, NIF, enderezo, teléfono e email;
  - se os ten: REGA, REAGA, NIMA, ROPO e REGFER.
- **Papeis** (pode ter varios): titular, traballador, aplicador, asesor, veterinario, cliente, provedor, laboratorio, empresa de servizos e outra explotación.
- **Dúas pantallas sobre a mesma lista:**
  - **Equipo:** quen traballa, coas horas e a UTA, como agora;
  - **Contactos:** a xente de fóra.
- O titular e o asesor gárdanse só aquí. Datos da explotación queda nunha soa xanela.
- **Nos traballos:** escóllese a persoa; se non está, escríbese o nome e créase ao gardar.
- Os textos de agora pásanse sós, xuntando os que teñen o mesmo NIF, ou o mesmo nome se non teñen NIF.
- Non é un programa de clientes: non hai pedidos, nin facturas, nin seguimento.

### 3.2 Que sae: o lote como ficha, coas súas saídas

- **Ficha do lote:**
  - colleita e produción crean un **lote** con código, produto, cantidade e unidade, e de onde vén (o cultivo ou o grupo);
  - máis adiante, a transformación creará lotes a partir doutros.
- **Saídas do lote**, cada unha cun tipo:
  - venda (con quen merca, a canle, o lugar, a factura ou albará e o prezo);
  - casa;
  - transformación;
  - perda ou retirada;
  - para os animais.
- **Canto queda** = o que entrou no lote − as saídas.
- **As vendas son o primeiro tipo de saída.** Fanse con este deseño e non co anterior.
- Os datos do cliente da colleita pasan á venda. O retirado da produción pasa a ser unha saída «perda».
- O **produto do lote** leva a súa categoría da venda directa (ovos, mel, hortalizas, froita…) para os máximos do Decreto 125/2014.
- A pantalla de lotes, co seu historial, segue no módulo do xemelgo. Este é o seu cimento.

### 3.3 Que entra: as compras (despois das vendas)

- **Compra ou entrada dun insumo:** data, provedor (da lista de 3.1), produto, cantidade, lote do provedor, albará ou factura e prezo.
- **Os traballos que o usan** (abonado, coidado, sementeira, tratamento) escollen de que compra sae, ou só o produto se non se sabe.
- Con iso:
  - o provedor e o albará escríbense unha vez;
  - sábese canto queda;
  - sae o custo de cada traballo para o plan de empresa.
- **É o paso que xa estaba na folla de ruta como «almacén»**, pero adiantado:
  - os gastos (paso 9) e o plan de empresa (paso 16) dependen del;
  - o rexistro de medicamentos tamén.

### 3.4 Que se fai: a parte común igual en todos

- **Varias leiras nun traballo:** labor, rega, abonado e colleita poderán ter varios cultivos, como xa fan o tratamento e o pastoreo. O caderno e o CUE seguen saíndo leira por leira.
- **Mesma parte común en todos:** data ou datas, quen, horas, máquina, notas, quen o apuntou e identificador para o móbil.
- **Estado do cultivo segundo os traballos:**
  - a primeira sementeira ou colleita pásao a «en curso»;
  - a baixa ou o fin, a «rematado».

### 3.5 Para decidir, pero non para facer agora

- **Vacún un a un:** o grupo segue valendo para o resto. Para o vacún, cada animal tería o seu crotal dentro do grupo. Hai que mirar antes o libro de rexistro bovino e o SITRAN.
- **Instalacións** (paso 14): o tratamento en instalacións escollerá a instalación en vez de escribila.

### 3.6 Poñer ao día `como-e-a-app.md`

- As seis preguntas (§1 desta revisión) como forma da app.
- Os recursos: persoas e entidades (Equipo e Contactos), lotes e insumos.
- A táboa de traballos completa.
- **Regra nova:**
  - antes de engadir un campo cunha persoa, empresa, produto ou lote, mirar se xa existe;
  - ao rematar cada paso da folla de ruta, revisar a app enteira coas seis preguntas.

### 3.7 Orde proposta

1. Poñer ao día `como-e-a-app.md` (3.6).
2. Persoas e entidades: Equipo e Contactos, co titular e o asesor nun só sitio (3.1).
3. Lotes e saídas, coas vendas como primeira saída (3.2).
4. Varias leiras nun traballo, a parte común igual e o estado do cultivo (3.4). Vai antes do CUE porque o CUE le todo isto.
5. Outro traballo.
6. CUE.
7. Compras e existencias (3.3), antes de gastos e ingresos.

## 4. Decisións do usuario

1. **Unha soa lista de persoas e entidades**, con dúas pantallas (Equipo e Contactos), en vez dunha lista de clientes á parte? (Recomendado: si.)
2. **O lote como ficha, coas súas saídas** (venda, casa, transformación, perda, animais), e as vendas como a primeira saída? (Recomendado: si; cambia o deseño de vendas presentado antes.)
3. **Compras e existencias** antes de gastos e ingresos, en lugar de deixalas para o almacén? (Recomendado: si.)
4. **Varias leiras nun mesmo traballo** e a parte común igual en todos, antes do CUE? (Recomendado: si.)
5. **Vacún un a un:** mirámolo cando toque o libro de rexistro gandeiro (paso 14), ou antes? (Recomendado: no paso 14, pero sen facer nada nos animais que o impida.)

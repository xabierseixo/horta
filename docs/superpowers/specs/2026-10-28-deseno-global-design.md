# Deseño global da app (a app como un todo)

Data: 2026-10-28 · Estado: **aprobado polo usuario** («Codifica», 2026-10-28; recomendacións das decisións 2 e 3 aceptadas) · Substitúe a folla de ruta por partes de `docs/como-e-a-app.md` §5.

**Orixe:**
- `docs/revision-definicion-2026-10-28.md`, que o usuario aprobou («Estou de acordo»);
- a condición do usuario: «a app é un todo, non podemos seguir facendo por partes».

**Como se usa este documento:**
- Cando estea aprobado, `como-e-a-app.md` reescríbese a partir del.
- Cada paso de construción (§7) é unha parte deste deseño e non un deseño novo. Antes de cada paso compróbase que segue encaixando aquí. Se non encaixa, cámbiase primeiro este documento.

## 1. A forma da app: seis preguntas

| Pregunta | Na app | Que hai |
|---|---|---|
| **Quen?** | Persoas e entidades | unha soa lista, con papeis |
| **Onde e con que?** | Recursos | parcelas e cultivos, animais, instalacións e máquinas |
| **Que entra?** | Produtos e entradas | insumos e as súas entradas (compras) |
| **Que se fai?** | Traballos | todos coa mesma parte común |
| **Que sae?** | Lotes e saídas | o produto e a onde vai |
| **Canto custa e canto dá?** | Cartos | sae de entradas, saídas e horas; só se escribe o que non sae doutro sitio |

E por riba de todo, os **informes**, que só len (caderno, CUE, libros, plan de empresa e xemelgo).

**Regras que fan que sexa un todo:**
1. **Cada cousa existe nun só sitio.** Os traballos escollen (persoa, cultivo, máquina, produto ou lote) e non escriben. Se non existe, créase dende o propio formulario cun nome, e complétase despois.
2. **Todo o que sae dunha conta calcúlase e non se escribe:**
   - os animais dun grupo;
   - o que queda nun lote ou dun produto;
   - o estado dun cultivo;
   - os gastos que veñen das compras;
   - os ingresos que veñen das vendas.
3. **Todos os traballos teñen a mesma parte común.** Está escrita unha vez no código, así que un traballo novo non pode quedar sen ela.
4. **Os informes só len.** Se lles falta algo, avisan, e nunca bloquean ao apuntar.
5. **Antes de engadir un campo cunha persoa, empresa, produto, lugar ou lote, mírase se xa existe.**
6. **Ao rematar cada paso, revísase a app enteira coas seis preguntas.**

## 2. Quen: persoas e entidades

**Táboa `persoa`, ampliada:** pasa a ser toda a xente e as empresas coas que se trata a explotación.

| Que | Campos |
|---|---|
| Identidade | tipo (persoa ou entidade), nome ou razón social, apelidos, NIF |
| Contacto | enderezo, localidade, código postal, provincia, concello (código INE, que o pide o CUE para quen merca), país, teléfono, email |
| Rexistros, se os ten | REGA, REAGA, NIMA, ROPO (número, tipo e caducidade), REGFER, nº de rexistro dixital de alimentos (CUE 3) |
| Traballo, só para o equipo | vínculo, horas ao ano, formación, xénero, nacemento, discapacidade |
| Conta na app | `usuario_id`, como agora |

**Papeis:** táboa `persoa_papel`, porque unha mesma persoa pode ter varios.
- Os papeis son:
  - titular, traballador, aplicador, asesor;
  - veterinario, cliente, provedor, laboratorio, empresa de servizos e outra explotación.
- Os papeis de agora (`e_titular`, `e_traballador`, `e_aplicador`, `e_asesor`) pásanse a esta táboa.

**Pantalla «Persoas»** (en Explotación), con dúas pestanas sobre a mesma lista:
- **Equipo:** titular, traballador, aplicador e asesor, coas horas e a UTA, como agora;
- **Contactos:** o resto.
- Unha persoa con papeis das dúas pestanas sae nas dúas.

**Titular e asesor nun só sitio:**
- Desaparecen da explotación `titular_nome`, `titular_nif` e `asesoramento_nome/nif/num`.
- O titular é a persoa ou entidade co papel «titular», e o asesor a que ten o papel «asesor».
- Na explotación quedan os seus datos propios: REAGA, REGA, tipo de explotación, tipo de XIP e se recibe asesoramento en fertilización. Todo nunha soa xanela, e o campo «Tipo de explotación» só aparece unha vez.

**Os 12 sitios con texto pasan a escoller unha persoa:**

| Sitio | Campo novo | Papel que se propón |
|---|---|---|
| venda (lote_saida) | `comprador_id` | cliente |
| entrada e saída de animais | `outra_parte_id` (en vez de titular e REGA) | outra explotación ou cliente |
| pastoreo de terceiros | `propietario_id` (en vez do REGA) | outra explotación |
| entrada de produto (compra) | `provedor_id` | provedor |
| abonado | `empresa_servizos_id` | empresa de servizos |
| análise | `laboratorio_id` | laboratorio |
| coidado (medicamento) | `veterinario_id` | veterinario |
| coidado (visita) | `visitante_id` | calquera |
| parcela | `arrendador_id` | calquera |
| explotación | o papel «asesor» | asesor |

- **Os textos de agora pásanse sós.** Por cada texto créase unha persoa ou entidade co seu papel. Os que teñen o mesmo NIF, ou o mesmo nome se non teñen NIF, quedan nun só contacto.
- Ningún texto se perde: se non se pode pasar, vai ás notas do rexistro.
- O provedor dos abonos, das sementes e dos medicamentos pasa á entrada de produto (§4).

## 2bis. Usuarios, Equipo e Contactos: un pequeno CRM (revisión do 2026-10-29)

A pantalla de Persoas mesturaba os datos da xente coas contas da app. Ademais, o titular quedou duplicado: unha ficha ligada á conta e outra co papel de titular. Quedan tres cousas separadas:

| Que | Quen o xestiona | Que é |
|---|---|---|
| **Administración da app** | quen administra a plataforma (unha ou varias persoas) | configuración, catálogos oficiais, fontes, contas |
| **Equipo** | quen administra a explotación | quen traballa nela: ficha, horas, carné. Se ten que apuntar datos, na súa ficha dáselle **acceso á app**, cun permiso (administrar, editar, só mirar) e por convite: unha ligazón que se lle manda e na que pon o seu contrasinal. Sen escribir correos de contas alleas |
| **Contactos (CRM)** | quen ten permiso para editar | clientes, provedores, empresas e traballadores de fóra que fan traballos, veterinario, asesor, laboratorio, outras explotacións. Cada ficha mostra **o seu historial**, sacado do que xa se apunta: compras, vendas, traballos feitos e o pendente de cobrar ou pagar (paso 10) |

- Unha conta pode estar en varias explotacións (p.ex. un asesor).
- **A mesma persoa nunca se dá de alta dúas veces:** ao gardar, a app avisa se xa hai outra co mesmo NIF, email ou nome e apelidos.
- O titular é unha soa ficha: co papel de titular, no Equipo e, se ten conta, ligada a ela.

## 2ter. O pequeno ERP: onde está cada parte

| Área | Onde |
|---|---|
| Compras e almacén | produtos, compras e existencias (§4, paso 7) |
| Vendas | lotes, saídas e clientes (§6, paso 4) |
| Produción | traballos, colleitas e animais (§5) |
| Equipo | §2bis |
| Maquinaria e instalacións | máquinas; instalacións no paso 14 |
| Cartos | §7: gastos, ingresos, cobros e pagos pendentes, custo da hora (paso 10) |
| Facturas | **gárdanse** (número, data, importe, cobrada ou pagada) nas compras e nas vendas. **Emitilas cumprindo VERI\*FACTU (RD 1007/2023)** quere facerse, pero non é prioridade: vai ao final da orde (decisión do usuario, 2026-10-29) |

## 3. Onde e con que: recursos

| Recurso | Cambio |
|---|---|
| Parcela | o arrendador pasa a ser unha persoa (§2) |
| Cultivo | **o estado calcúlase dos traballos**: *planificado* se non ten sementeira nin colleita, *en curso* desde a primeira, e *rematado* ou *de baixa* coa data de fin ou a causa. Os datos da semente pasan á entrada de produto (§4) e o cultivo só sinala de que entrada saíu |
| Animais (grupos) | sen cambios. **Decisión para o paso 14:** o vacún un a un (crotal dentro do grupo). Ata entón non se fai nada que o impida |
| Instalacións | novo no paso 14: almacéns, cortes, obradoiros, cámaras. Despois o tratamento en instalacións escolle a instalación, e os lotes e os produtos poden ter un sitio |
| Máquinas | sen cambios |

## 4. Que entra: produtos e entradas

**`produto`** (novo, por explotación): os insumos.
- **Tipo:** fitosanitario, abono, semente ou planta, medicamento, penso, enerxía ou outro.
- **Datos:** nome, unidade e a ligazón oficial:
  - nº de rexistro do MAPA nos fitosanitarios;
  - o catálogo de fertilizantes nos abonos;
  - a variedade e o ROPVEG nas sementes.
- O `fertilizante` de agora pasa a ser un produto de tipo abono, coa súa composición, que segue igual.

**`entrada_produto`** (novo): cada compra ou recepción.
- Data, produto, provedor (§2), cantidade e unidade, lote do provedor, albará ou factura, prezo e caducidade.
- Nas sementes, tamén o pasaporte fitosanitario.

**Os traballos usan o produto:**
- o abonado, o tratamento, o coidado (medicamento) e a sementeira escollen o produto;
- se se sabe, tamén a entrada de onde sae;
- se non se sabe, avísase no informe e non se bloquea.

**Existencias:** o que queda é o que entrou menos o que se usou, na unidade do produto. Se non se pode converter, avísase.

**Informes que saen de aquí:**
- rexistro de medicamentos (entradas + coidados);
- CUE 2 (enerxía);
- custos do plan de empresa;
- a orixe dos insumos no xemelgo.

## 5. Que se fai: traballos

### 5.1 Parte común (unha mixin no código, `TraballoComun`)

Todos os traballos levan:

| Campo | Para que |
|---|---|
| `horta_id` | a explotación |
| `data_inicio` e `data_fin` | cando; nos traballos dun día, as dúas iguais |
| `persoa_id` e `horas` | quen o fixo; no tratamento, cada aplicador |
| `maquina_id` | con que máquina, onde poida haber unha. Non vai na análise nin no pastoreo |
| `notas` | |
| `baixa` | baixa lóxica |
| `uuid` | identificador para o móbil |
| `creado_por` e `created_at` | quen o apuntou e cando |

- **Hoxe faltan:**
  - a máquina en rega, tratamento en instalacións, entradas e saídas e produción;
  - as notas e quen o apuntou no tratamento;
  - o `uuid` en todos agás colleita, produción e pastoreo.
- As columnas que se chaman `data` quedan como están na BD. A mixin dálles o nome común.

### 5.2 A que se refire: varias leiras

- **Labor, rega e abonado** poden ter **varias leiras**, cunha táboa filla con cultivo e superficie, como xa fan o tratamento e o pastoreo.
- **As horas** son do traballo enteiro.
- **No CUE** sae un rexistro por leira, porque así o pide. A cantidade de auga da rega repártese por superficie, e avísase disto no informe.
- **A colleita** segue sendo dunha leira, porque o que se colle en cada leira é un dato real e o CUE o pide así. Pero o formulario deixa apuntar varias leiras dunha vez: unha cantidade por leira, todas no mesmo lote e coa mesma persoa e data.

### 5.3 Tipos de traballo

**Xa feitos:**
- labor, sementeira (dentro do cultivo), tratamento, tratamento en instalacións, abonado, rega, colleita, toma de mostras;
- coidado de animais, entrada ou saída de animais, produción dos animais, pastoreo.

**Novos:**
- **saída de produto** (§6: venda, casa, transformación, perda, animais);
- **entrada de produto** (§4);
- **outro traballo** (mantemento, limpeza…: descrición + parte común).

Todos van ao Diario e a «Apuntar traballo», e poden ser tarefas.

## 6. Que sae: lotes e saídas

**`lote`** (novo): a identidade do produto que sae da explotación.

| Campo | Para que |
|---|---|
| `codigo` | único na explotación (`AAAA-PRODUTO-NNN`, como agora) |
| `produto` | que é: o cultivo (código SIEX) ou o produto animal (ovos, leite, mel…) |
| `categoria_venda_directa` | ovos, mel, hortalizas, froita, patacas, legumes, cereais, cogomelos…, para os máximos do Decreto 125/2014. Proposta automática a partir do produto |
| `unidade` | a unidade do lote |
| `data` | cando se creou |
| `baixa` | |

**Entradas no lote:**
- as colleitas e as producións apuntan ao lote (`lote_id` en vez do texto);
- un lote pode recoller varias colleitas ou producións (a semana de ovos, ou a pataca de tres leiras);
- máis adiante, as transformacións.

**`lote_saida`** (novo; é un traballo coa parte común):
- **Tipo:** venda, casa, transformación, perda ou animais.
- **Cantidade e unidade.**
- **Se é venda:**
  - canle: na explotación, mercado, a domicilio, tenda, ou almacén ou cooperativa;
  - lugar;
  - quen merca (§2);
  - albará ou factura e prezo.

**O que queda nun lote** = entradas − saídas.
- **Non deixa sacar máis do que hai.**
- **Avisos que non bloquean:**
  - os máximos anuais da venda directa por categoría;
  - o lote saíu dun grupo en tempo de espera;
  - o lote ten un tratamento co prazo de seguridade sen cumprir.
- **Bloquea:** os ovos non se venden a tendas, e unha venda a tenda leva quen merca (Decreto 125/2014, arts. 6 e 7).

**Os datos de agora:**
- os textos de lote pasan a fichas de lote;
- o retirado da produción pasa a saída «perda»;
- o cliente e o albará da colleita pasan a unha saída «venda».

**Pantalla «Lotes»** (en Explotación, xunto a Produtos):
- código, produto, de onde vén, canto entrou, canto saíu e canto queda;
- botóns «Vender» e «Saída».
- O módulo do xemelgo amplíaa despois co historial selado.

## 7. Cartos

Non se apunta nada que saia doutro sitio:

| Que | De onde sae |
|---|---|
| **Ingresos** | vendas (`lote_saida`) e vendas de animais (prezo nas saídas de animais) |
| **Gastos** | entradas de produto (prezo) |
| **Man de obra** | horas × custo da hora de cada persoa |
| **Máquinas** | horas × custo da hora da máquina |

- Á man só se apuntan os **outros gastos e ingresos**: seguros, aluguer, auga, luz, cotas e axudas.
- **Cobros e pagos:** cada venda e cada compra di se está cobrada ou pagada e cando. Así sae o pendente de cada cliente e provedor (CRM, §2bis).

## 7bis. O tempo (MeteoGalicia e AEMET): contexto de todo o anterior

O tempo non é unha sección á parte nin un traballo. É o **contexto** do onde, do que se fai e do que se vai facer, e cólgase dese sitio (investigación en `docs/estado-e-evolucion.md` §8decies; decisión do usuario do 2026-10-28: MeteoGalicia e AEMET, non Open-Meteo).

**Recursos (onde):**
- **Parcela:** as coordenadas (xa as ten, ou as do mapa ou do GPS) e o **concello** (código INE).
- **Estación:** a app propón a estación de MeteoGalicia máis próxima (distancia e altitude) e pódese cambiar a man. Avisa se está lonxe (máis de ~10 km) ou con moita diferenza de altitude.
- **Explotación:** o concello e a zona de aviso de AEMET, para o que non ten parcela.

**Datos:**

| Que | De onde | Onde se garda |
|---|---|---|
| **Tempo dun día nunha estación** | MeteoGalicia | táboa `tempo_dia` (estación, data, temperaturas mínima e máxima, choiva, vento medio e refacho, humidade). Gárdase **unha vez** e compárteo todo o que pasou ese día alí |
| **Predición por concello** | MeteoGalicia (e AEMET) | non se garda: consúltase ao abrir |
| **Avisos** (vento, choiva, xeadas…) | AEMET, zona de aviso | non se gardan: consúltanse ao abrir |

**Que se fai (traballos):**
- A parte común gaña `tempo_id`: o tempo dese día na estación da primeira leira.
- **Ao apuntar** un tratamento, unha rega ou un abonado, a app busca o tempo dese día, gárdao e móstrao. Avisa, sen bloquear:
  - tratamento con vento forte ou choiva;
  - rega despois de chover;
  - abonado antes dunha choiva forte (lixiviación de nitratos).
- Se non hai conexión, apúntase igual e o tempo énchese despois.

**O que se vai facer (tarefas e Inicio):**
- **Inicio:** a predición dos próximos días e os avisos da zona, por concello.
- **Tarefas:** aviso se unha tarefa de tratamento cae nun día con vento ou choiva prevista.

**Informes:**
- **Xemelgo:** o tempo gardado de cada traballo é unha evidencia, coa fonte e a data da consulta.
- **CUE e caderno:** se o modelo o pide, sae do dato gardado e non dunha consulta nova.
- **Estatísticas:** choiva e auga de rega por cultivo.

**Sen servizos neste ordenador** (decisión do usuario):
- non hai tarefas programadas;
- consúltase ao abrir unha pantalla ou ao gardar un traballo;
- gárdase só o que usa un traballo.
- A clave de AEMET pídea e gárdaa o titular.

**Confirmado o 2026-10-29** (`2026-10-29-tempo-design.md`):
- o código de municipio do SIGPAC é o do Catastro, non o INE: o concello escóllese da lista do INE;
- MeteoSIX pide clave, pero as estacións, os datos diarios e a predición por concello de MeteoGalicia non.

## 8. Informes: que le cada un

Serve para comprobar que o modelo enteiro ten todo o que fai falta:

| Informe | Le |
|---|---|
| Caderno da Xunta (Excel) | explotación, titular e asesor (§2), parcelas, cultivos e todos os traballos; a folla 5 sae das saídas de venda |
| CUE 1–13 | traballos (un rexistro por leira); CUE 2 das entradas de enerxía; CUE 3 das vendas; CUE 12 do pastoreo |
| Libro de rexistro gandeiro | grupos, entradas e saídas (coa outra parte, §2), coidados e visitas |
| Rexistro de medicamentos | entradas de medicamentos e coidados |
| Rexistro de venda directa (Decreto 125/2014, art. 6) | saídas de venda: produto, cantidade, data, lugar e tenda |
| Trazabilidade e xemelgo | o lote, as súas entradas (colleitas e producións), os traballos dos seus cultivos ou grupos, os insumos usados (coas entradas e os provedores) e as súas saídas |
| Balance de masas | o que entrou e o que saíu de cada lote, fronte á superficie e ao rendemento |
| Plan de empresa | produción (lotes), ingresos, gastos, horas, persoas (UTA), máquinas e superficies |

## 9. Pantallas

| Sitio | Que ten |
|---|---|
| Inicio | o de hoxe, o atrasado e os avisos |
| Diario | todos os traballos; «Apuntar traballo» |
| Informes | caderno, CUE, libros, rexistros e o que lles falta |
| **Explotación** | Parcelas · Cultivos · Animais · Instalacións (paso 14) · Máquinas · **Persoas** (Equipo e Contactos) · **Produtos** (o que entra) · **Lotes** (o que sae) · Datos da explotación |
| Módulos | plan de empresa e xemelgo |

## 10. Orde de construción

Cada paso fai unha peza enteira en toda a app, non nunha soa pantalla.

| Paso | Que | Por que nesta orde |
|---|---|---|
| 1 | Reescribir `como-e-a-app.md` e `modelo-datos` co modelo de destino | todo o demais apóiase nel |
| 2 | **Parte común:** a mixin, os campos que faltan e o estado do cultivo calculado | cimento de todos os traballos e do móbil |
| 3 | **Persoas e entidades:** papeis, Equipo e Contactos, titular e asesor nun só sitio; os 12 textos pasan a persoas en toda a app á vez | todo o que segue escolle persoas |
| 4 | **Lotes e saídas:** ficha de lote, saídas (venda, casa, transformación, perda, animais) e pantalla Lotes; pásanse os lotes, o retirado e os clientes | as vendas, o CUE 3 e o xemelgo len de aquí |
| 5 | **Varias leiras nun traballo** (labor, rega e abonado) e varias colleitas dunha vez | o CUE debe ler o modelo final |
| 6 | **CUE** (obrigatorio desde o 1/1/2027) | xa co modelo estable |
| 7 | **Produtos e entradas:** compras, existencias e provedores; pásanse os abonos, as sementes e os medicamentos | base de gastos e do plan de empresa |
| 8 | Outro traballo | xa coa parte común |
| 9 | Meteoroloxía (MeteoGalicia e AEMET) | dentro dos traballos. 9a feito; 9b (Inicio e tarefas) e 9c (AEMET, coa clave) despois do 9bis |
| 9bis | **Usuarios, Equipo e Contactos (CRM)** (§2bis): acceso á app por convite na ficha do equipo, historial de cada contacto, aviso de duplicados; xuntar o titular duplicado | o usuario atopouno confuso ao usar a app (2026-10-29) |
| 10 | Cartos: outros gastos e ingresos, custo da hora, cobros e pagos | le os pasos 4 e 7; completa o CRM |
| 11 | Fotos, app do móbil sen cobertura | o `uuid` xa está desde o paso 2 |
| 12–17 | historial e rotación, calendario e mapa, instalacións e libros gandeiros (con decisión do vacún), estatísticas, plan de empresa, transformación e xemelgo | como na folla de ruta |
| 18 | Emitir facturas cumprindo VERI\*FACTU | quérese, pero non é prioridade (2026-10-29) |

**Sobre o prazo do CUE (1/1/2027):**
- Quedan dous meses.
- Os pasos 2–5 cambian o que o CUE le. Se o CUE se fixese antes, habería que refacelo.
- Mentres tanto, o caderno en Excel xa sae.
- Se o tempo aperta, o CUE pode adiantarse ao paso 5, porque ese paso só cambia como se reparten as leiras.

## 11. Cada paso, sempre igual

1. Comprobar que encaixa neste documento.
2. Mirar a normativa dese paso.
3. Escribir a versión de proba.
4. Facer as tarefas.
5. Revisar a app enteira coas seis preguntas: buscar repetidos, textos que deberían ser fichas e contas que se escriben a man.
6. Probar no navegador, en escritorio e en móbil.
7. Poñer os documentos ao día.

## 12. Decisións pendentes do usuario

1. Aprobar este deseño global.
2. **Unha pantalla «Persoas»** con dúas pestanas (Equipo e Contactos), en vez de dúas entradas no menú? (Recomendado: si; é unha soa lista.)
3. **Orde co prazo do CUE:** os pasos 2–5 antes do CUE (recomendado), ou o CUE antes do paso 5?

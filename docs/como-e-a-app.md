# Como é horta (documento de referencia)

Data: 2026-10-28 (reescrito a partir do deseño global, `docs/superpowers/specs/2026-10-28-deseno-global-design.md`, aprobado polo usuario: «Codifica»). **Ler antes de deseñar calquera cousa.** Se un deseño non encaixa aquí, primeiro cámbiase este documento co usuario. **A app é un todo:** non se deseña por partes soltas (decisión do usuario, 2026-10-28).

## 1. Que é

Unha app para as explotacións de Galicia: produtores primarios, gandaría e transformación. Nela apúntase **o traballo que se fai** na explotación, **o que entra** e **o que sae**. Todo o que hai que entregar, consultar ou demostrar sae de aí como **informe**:
- o caderno de explotación e o CUE;
- os libros e rexistros (gandeiro, medicamentos, venda directa);
- a trazabilidade dun lote;
- o plan de empresa e os custos.

**Nunca se mete o mesmo dato dúas veces e nunca se «enche un caderno»:** o caderno é un resultado.

**Apuntar só obriga ao mínimo** (que, onde, cando e quen). Un traballo sempre o fai unha persoa: nunca se supón que non hai quen o fixo. O resto énchese se se sabe. Se a un informe lle falta algo, **avisa e non bloquea**, e complétase cando se poida.

Quen a usa:
- xente que non é experta en informática, desde o móbil e no campo;
- a persoa titular, quen traballa e o asesor.

En galego sempre (o castelán é unha tradución). Os campos saen da normativa e dos catálogos oficiais (`docs/campos-oficiais-anexo-v.md`). As outras apps (§6) só serven de contraste: as decisións tómanse pensando no traballo real dunha explotación galega.

## 2. A forma da app: seis preguntas

| Pregunta | Na app | Que hai |
|---|---|---|
| **Quen?** | Persoas e entidades | unha soa lista de xente e empresas, de dentro e de fóra, con papeis |
| **Onde e con que?** | Recursos | parcelas e cultivos, animais (grupos), instalacións, máquinas |
| **Que entra?** | Produtos e entradas | insumos (sementes, abonos, fitosanitarios, medicamentos, pensos, enerxía) e cada compra ou recepción |
| **Que se fai?** | Traballos | todos coa mesma parte común |
| **Que sae?** | Lotes e saídas | o produto e a onde vai: venda, casa, transformación, perda, animais |
| **Canto custa e canto dá?** | Cartos | calculado das entradas, das saídas e das horas; á man só o que non sae doutro sitio |

Por riba, os **informes**, que só len, e dous **módulos** con datos propios: plan de empresa e xemelgo.

### 2.1 Quen: persoas e entidades

- Unha soa táboa de persoas e entidades (persoa ou empresa): identidade, contacto, rexistros (REGA, REAGA, NIMA, ROPO, REGFER, rexistro dixital de alimentos) e, só para o equipo, os datos de traballo (UTA).
- **Papeis** (varios por persoa): titular, traballador, aplicador, asesor, veterinario, cliente, provedor, laboratorio, empresa de servizos, outra explotación.
- Pantalla **Persoas**, con dúas pestanas sobre a mesma lista: **Equipo** e **Contactos**.
- O titular e o asesor da explotación son as persoas con ese papel: non se escriben noutro sitio.
- Nos traballos escóllese a persoa; se non está, créase dende o formulario co nome.

### 2.2 Onde e con que: recursos

- **A explotación:** REAGA, REGA, tipo e datos de asesoramento (o titular e o asesor son persoas).
- **Parcelas** e os seus **cultivos** (cada plantación ou sementeira). O estado do cultivo calcúlase dos seus traballos.
- **Animais**, en **grupos**. (Decisión pendente para o paso 14: o vacún un a un, co crotal dentro do grupo.)
- **Instalacións:** almacéns, cortes, obradoiros, cámaras (paso 14).
- **Máquinas.**

### 2.3 Que entra: produtos e entradas

- **Produto:** cada insumo da explotación (tipo, nome, unidade e ligazón oficial: rexistro do MAPA, catálogo de fertilizantes, variedade e ROPVEG).
- **Entrada de produto:** cada compra ou recepción, co provedor, a cantidade, o lote do provedor, o albará ou a factura, o prezo e a caducidade.
- Os traballos (abonado, tratamento, coidado, sementeira) escollen o produto e, se se sabe, a entrada. O que queda calcúlase.

### 2.4 Que se fai: traballos

**Parte común (igual en todos, escrita unha vez no código):**
- explotación;
- data ou datas de inicio e fin;
- quen o fixo e cantas horas;
- con que máquina, onde poida haber unha;
- notas;
- baixa lóxica;
- identificador para o móbil;
- quen o apuntou e cando.

**A que se refire:** unha ou varias leiras (cultivos), animais, unha instalación ou a explotación enteira.

| Tipo de traballo | Detalles | Táboa |
|---|---|---|
| Labor no campo (arar, rozar, podar…) | tipo oficial, restos no chan, cobertura | `labor` |
| Sementeira / plantación | material vexetal, dose | hoxe dentro de `cultivo` |
| Tratamento fitosanitario | problema, produtos, xustificación, asesor | `tratamento_fito` |
| Tratamento en instalacións / postcolleita / transporte | produto, que se tratou | `tratamento_instalacion` |
| Abonado | abono, dose, método | `abonado` |
| Rega | sistema, auga | `rega` |
| Colleita | cantidade, lote | `colleita` |
| Toma de mostras / análise | laboratorio, resultados | `analise` |
| Coidado de animais | coidado, enfermidade, cambio na produción, medicamento, visita | `coidado_animal` |
| Entrada ou saída de animais | nacemento, entrada, saída, morte; a outra parte | `movemento_animal` |
| Produción dos animais | ovos, leite, mel, cera, la; lote | `producion_animal` |
| Pastoreo | leiras, animais propios ou doutra persoa | `pastoreo` |
| Saída de produto | venda, casa, transformación, perda, animais | `lote_saida` (paso 4) |
| Entrada de produto | compra ou recepción dun insumo | `entrada_produto` (paso 7) |
| Outro traballo (mantemento, limpeza…) | descrición | paso 8 |

Cada tipo ten a súa propia táboa, porque cada un corresponde a un bloque do CUE ou dun libro oficial. **As tarefas son traballos *por facer*:** cando se fan, quedan ligadas ao traballo apuntado.

### 2.5 Que sae: lotes e saídas

- **Lote:** a identidade do produto (código único na explotación, produto, categoría da venda directa, unidade). Nel entran colleitas e producións (e, máis adiante, transformacións).
- **Saída do lote:** venda (canle, lugar, quen merca, albará ou factura, prezo), casa, transformación, perda ou animais.
- **O que queda** = entradas − saídas. Non se saca máis do que hai.

### 2.6 Cartos

- **Ingresos:** vendas e vendas de animais.
- **Gastos:** entradas de produto.
- **Man de obra e máquinas:** horas × custo da hora.
- Á man, só os outros gastos e ingresos (seguros, aluguer, auga, luz, cotas, axudas).

### 2.6bis O tempo: contexto de todo

O tempo (MeteoGalicia e AEMET) non é unha sección á parte:
- **onde:** cada parcela ten o seu concello e a estación máis próxima;
- **o que se fai:** cada traballo garda o tempo dese día (unha táboa compartida por estación e día) e avisa de vento, choiva ou xeadas;
- **o que se vai facer:** Inicio mostra a predición e os avisos, e as tarefas avisan do tempo previsto;
- **informes:** o xemelgo usa o tempo gardado como evidencia.

Detalle en `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §7bis.

### 2.7 Informes: o que sae de todo o anterior

| Informe | Le |
|---|---|
| Caderno da Xunta (Excel) | explotación, titular e asesor, parcelas, cultivos, traballos; folla 5 das vendas |
| CUE (obrigatorio desde o 1/1/2027) | traballos (un rexistro por leira), enerxía das entradas, vendas, pastoreo |
| Libro de rexistro gandeiro | grupos, entradas e saídas, coidados, visitas |
| Rexistro de medicamentos | entradas de medicamentos e coidados |
| Rexistro de venda directa (Decreto 125/2014) | vendas |
| Trazabilidade / xemelgo / balance de masas | lote, as súas entradas, os traballos e insumos dos seus cultivos ou grupos, as súas saídas |
| Plan de empresa | produción, ingresos, gastos, horas, persoas, máquinas, superficies |
| Avisos | «para estar en regra», prazo de seguridade, tempo de espera, máximos da venda directa, catálogos sen revisar, tarefas atrasadas |

### 2.8 Módulos

**Plan de empresa (AGADER e liñas da Consellería)** — análise en `docs/estado-e-evolucion.md` §3. Datos propios: liña de axuda, investimentos (Anexo V, con IVE e sen el, tres ofertas por gasto), financiamento, previsións a 5 anos, VAN/TIR/pay-back, emprego (UTA). Os datos reais énchense sós desde o resto da app.

**Xemelgo dixital do produto** — análise en `docs/trazabilidade-analise.md`. Cada lote ten un historial de eventos aos que só se pode engadir, asinados e encadeados por hash; os eventos saen dos traballos, das entradas e das saídas, con evidencias (foto, data, lugar, fonte oficial comprobada). Non substitúe o caderno.

Decisión pendente: módulos en paquetes propios (`horta.plan_empresa`, `horta.xemelgo`) que só usan os servizos de horta (recomendación de Claude, 2026-10-25).

## 3. Pantallas

| Sitio | Para que |
|---|---|
| **Inicio** | que toca hoxe, o atrasado e os avisos |
| **Diario** | todos os traballos (feitos e por facer) por data, con filtros. Botón **«Apuntar traballo»**: primeiro *que fixeches*, despois o formulario dese tipo |
| **Informes** | caderno, CUE, libros, rexistros e o que lles falta |
| **Explotación** | Parcelas · Cultivos · Animais · Instalacións · Máquinas · **Persoas** (Equipo e Contactos) · **Produtos** (o que entra) · **Lotes** (o que sae) · Datos da explotación |
| **Plan de empresa** e **Xemelgo** (módulos) | os seus datos propios e os seus informes |
| **Administración** | usuarios e catálogos oficiais (só administración global) |

Dentro de cada recurso vese o seu historial: na ficha dun cultivo, todos os seus traballos.

## 4. Regras de deseño

1. Antes de deseñar, situalo nas **seis preguntas** (§2). Os bloques da normativa son informes sobre o apuntado, non pantallas novas.
2. **Cada cousa existe nun só sitio.** Antes de engadir un campo cunha persoa, empresa, produto, lugar ou lote, mirar se xa existe. Nos traballos escóllese, non se escribe.
3. **O que sae dunha conta calcúlase:** animais dun grupo, o que queda nun lote ou dun produto, estado do cultivo, gastos e ingresos derivados.
4. **A parte común dos traballos é igual en todos** (§2.4).
5. Un formulario só esixe o mínimo para saber que se fixo, onde, cando e quen. O que pide un informe avísase no informe, nunca bloquea ao apuntar.
6. Apuntar desde o móbil en menos de medio minuto: o imprescindible á vista e o resto pregado. Propoñer o último valor usado. Poder apuntar varias leiras dunha vez.
7. Avisar, non bloquear, cando a referencia legal é outra (etiquetas, catálogos con lagoas).
8. Conservar o histórico: os traballos danse de baixa, non se borran (3 anos; medicamentos, 5).
9. Non copiar un patrón (doutra app ou da propia) sen cuestionalo.
10. **Ao rematar cada paso, revisar a app enteira coas seis preguntas** e comprobar os fluxos reais no navegador (escritorio e móbil).

## 5. Onde estamos e orde de construción

**Feito ata o lote 080:**
- Recursos: parcelas, cultivos, animais, máquinas, equipo.
- Traballos: tratamento, tratamento en instalacións, abonado, rega, labor, colleita, sementeira, análise, coidado de animais, entradas e saídas, produción dos animais, pastoreo; tarefas como traballos por facer; quen e horas en todos.
- Diario, «Apuntar traballo» e Informes; caderno da Xunta en Excel; catálogos oficiais e rexistro do MAPA.
- Deseños de cada parte en `docs/superpowers/specs/` (lotes 074–080).

**Feito co deseño global (2026-10-28 e 29):**
- **Paso 1:** este documento co deseño global.
- **Paso 2 (lote 081):** a parte común está escrita unha vez (`models/traballo.py`) e todos os traballos a levan (máquina, notas, quen o apuntou, identificador do móbil). O estado do cultivo sae dos seus traballos.
- **Paso 3 (lote 082):** unha soa lista de persoas e entidades con papeis. A pantalla Persoas ten dúas pestanas, Equipo e Contactos. O titular, o representante e o asesor son persoas. Os 12 textos con xente de fóra pasan a escoller unha persoa ou crear unha nova dende o formulario.
- **Paso 4 (lote 083):** o lote é unha ficha onde entran colleitas e produción.
  - Saídas do lote: venda (canle, lugar, quen merca, albará, prezo), casa, transformación, perda e animais.
  - Pantalla Lotes, «Vender» nas colleitas e na produción, e caderno 5 dende as vendas.
  - Avisos dos máximos da venda directa, do tempo de espera e do prazo de seguridade.

**Paso 10, cartos (2026-10-29, `docs/superpowers/specs/2026-10-29-cartos-design.md`):** cobrada/pagada e cando nas vendas, compras e entradas e saídas de animais (con prezo); outros gastos e ingresos (`apunte_cartos`); custo da hora da persoa e da máquina; pantalla Cartos co resumo do ano e o pendente por persoa; o pendente sae no historial do contacto.

**Paso 11a, fotos (2026-10-29):** táboa `foto` (a que vai: tipo do Diario, parcela, animal ou lote); ficheiros en `HORTA_FOTOS_DIR` (por defecto `~/.local/share/horta/fotos`), un cartafol por explotación; só JPEG, PNG ou WEBP de ata 10 MB; ruta `/fotos/{id}` só para quen ve a explotación; baixa lóxica. Icona de cámara en cada traballo do Diario e botón «Fotos» en Parcelas, Animais e Lotes. O 11b (app do móbil sen cobertura) agarda decisión.

**Lotes ordenados (2026-10-29, `docs/analise-lotes-2026-10-29.md`):** ficha do produto que vendes (`produto_venda`: categoría da venda directa, clases e como se fan os lotes: por colleita, día, semana, mes ou a man), en Produtos → «O que vendes»; traballos **Clasificación** (o lote repártese por clases, o refugo conta como perda) e **Mestura de lotes** (lote novo que garda as orixes), no Diario, Tarefas, fotos e cartos; a venda escolle a clase; Lotes mostra o que queda de cada clase.

**Paso 12, historial e rotación (2026-10-29):** `services/historial.py` (xenérico: todo o que apunta a unha persoa, grupo de animais ou máquina; a parcela, polos traballos do Diario) e botón «Historial» en Parcelas, Animais e Maquinaria; rotación por parcela con aviso se o mesmo cultivo volve antes de 3 anos (tamén ao gardar un cultivo; nunca bloquea).

**Paso 13, calendario e mapa (2026-10-29):** `ui/pages/calendario.py`. Calendario (`ui.date`) cos días que teñen traballos marcados; ao escoller un día, os seus traballos e tarefas (como no Diario). Mapa (`ui.leaflet`) coas parcelas que teñen coordenadas; quen edita escolle unha parcela e preme no mapa para situala. O debuxo das parcelas (polígonos, SIGPAC) queda para máis adiante.

**Paso 14 (2026-10-29):** libro de rexistro gandeiro e rexistro de medicamentos en Excel (Informes; `services/libros_gandeiros.py`); instalacións (`instalacion`, pantalla en Xestión, historial; os grupos de animais e o outro traballo poden ir a unha); animais identificados opcionais en calquera especie (`animal_identificado`: crotal, microchip ou anela; aviso se non coinciden co grupo). O vacún, ovino, caprino e équidos deben identificarse un a un (Reg. UE 2016/429, Reg. Delegado 2019/2035; detalle por especie por confirmar no texto oficial).

**Paso 15, estatísticas (2026-10-29):** `services/estatisticas.py`, pantalla Estatísticas (`ui.echart`): produción por produto nos últimos 5 anos, clases e refugo do ano, choiva (a gardada da estación da explotación) e auga de rega por mes, e ingresos e gastos por mes (só quen edita).

**Paso 16, plan de empresa (2026-10-29, `docs/superpowers/specs/2026-10-29-plan-empresa-design.md`):** AGADER Anexo III e V. Conta a 5 anos proposta desde Cartos e editable; amortizacións do investimento, xuros dos préstamos (cota constante); VAN, TIR e pay-back; avisos (menos de 3 ofertas, financiamento que non cadra); métricas (rendemento, prezo medio por canle, refugo, horas e UTA, punto morto); seguimento previsto fronte a real; descarga en Excel. Só quen edita.

**Paso 17, transformación e xemelgo (2026-10-29):** traballo **Transformación** (`transformacion`, con lotes propios e ingredientes mercados que se descontan; sae un lote novo doutro produto), no Diario, Tarefas, fotos e cartos; a trazabilidade segue ata as colleitas e os lotes dos provedores. **Páxina pública do lote** (`/lote/{token}`, sen sesión, enderezo secreto que se pode retirar): de onde vén e que se lle fixo, nunca a quen se vendeu. Pendente: QR (precisa dependencia nova), selado (hash e selo de tempo, `estado-e-evolucion.md` §5) e EPCIS.

**Peches (2026-10-29):** QR da páxina pública do lote (dependencia `segno`) e descarga en PNG; rotación tamén pola familia botánica (`data/familias_cultivos.csv`); no Mapa debúxase o contorno da parcela (gárdase en `geometria` como GeoJSON, coa superficie e o centro). Aprazados: selado do xemelgo (escoller selo de tempo externo), MR404A (falta o anexo oficial), RECAN/ECREA (sen acceso desde a sesión), marxe por cultivo (reparto de custos), VERI\*FACTU, AEMET e app do móbil.

**Mapa con cartografía oficial e zonas (2026-10-29):** capas PNOA, SIGPAC e Catastro (`services/xeo_oficial.py`); premendo no mapa tráese o recinto SIGPAC (crea ou completa a parcela: referencia, uso, contorno, superficie) ou a referencia catastral. **Zonas da parcela** (`parcela_zona`: bancal, sector, invernadoiro, camiño): debuxalas a man ou **dividir a parcela en bancais iguais** (orientación e paso entre bancais), superficie automática, aviso se suman máis ca a parcela; o cultivo pode ir nunha zona. **Caché das capas** (`services/teselas.py`, ruta `/teselas/{capa}/{z}/{x}/{y}`): cada tesela descárgase unha vez e gárdase en `~/.local/share/horta/teselas` (ou `HORTA_TESELAS_DIR`); o botón «Gardar a zona para usar sen conexión» descarga de antemán os arredores das parcelas (zoom 14–19). A ortofoto vai debaixo e SIGPAC/Catastro por riba, visibles dende zoom 15. Por comprobar no ordenador do usuario as consultas ao premer (desde a sesión na nube non hai acceso).

**Orde de construción** (deseño global, §10). Cada paso fai unha peza enteira en toda a app:

1. Este documento e `modelo-datos` co modelo de destino.
2. **Parte común** igual en todos os traballos (máquina, notas, quen o apuntou, identificador do móbil) e **estado do cultivo** calculado.
3. **Persoas e entidades:** papeis, Equipo e Contactos, titular e asesor nun só sitio; os 12 textos de xente de fóra pasan a persoas en toda a app á vez.
4. **Lotes e saídas:** ficha de lote, saídas (venda, casa, transformación, perda, animais), pantalla Lotes; pásanse os lotes, o retirado e os clientes.
5. **Varias leiras nun traballo** (labor, rega, abonado) e varias colleitas dunha vez.
6. **CUE** (obrigatorio desde o 1/1/2027).
7. **Produtos e entradas:** compras, existencias e provedores.
8. **Outro traballo.**
9. **Meteoroloxía** con MeteoGalicia e AEMET (decisión do usuario, 2026-10-28), dentro dos traballos.
10. **Cartos:** outros gastos e ingresos, custo da hora.
11. **Fotos** e **app do móbil** sen cobertura.
12. **Historial** na ficha de cada recurso e **rotación** de cultivos.
13. **Calendario** e **mapa** da explotación.
14. **Instalacións**, **libro de rexistro gandeiro** e **rexistro de medicamentos** (con decisión do vacún un a un).
15. **Estatísticas** de produción.
16. **Módulo de plan de empresa.**
17. **Transformación** e **módulo de xemelgo dixital.**

Máis adiante: comprobacións contra fontes oficiais (SIGPAC, prezos do MAPA), outros formularios de axudas (MR404A/MR405F, SEPE, banca), novidades normativas, receitas fitosanitarias, ecolóxico e cogomelos, castelán, asistente de IA, API e sensores.

## 6. Como o fai o sector (análise do 2026-10-25)

| App | Como se organiza |
|---|---|
| farmOS (libre) | **Recursos** (*assets*: parcelas, plantacións, animais, equipos, materiais) e **rexistros** (*logs*: actividade, entrada de insumos, colleita, sementeira, transplante, observación, análise, mantemento, tratamento veterinario). Todos levan data, estado *pendente/feito/abandonado*, recursos, lugar, responsables, cantidades e notas. Planificar = rexistro pendente. |
| xFarm | Rexistro de actividades: parcelas, tipo, produtos, persoal e horas. Planificadas, feitas e atrasadas na mesma pantalla. O almacén descóntase ao apuntar. O caderno descárgase en Excel/PDF cando se queira. |
| Agroptima | Os traballadores apuntan **partes de traballo** desde o campo, mesmo sen cobertura. As **ordes de traballo** son o planificado. O caderno créase cun clic. Custos por parcela e cultivo. |
| Agricolum | Rexistra operacións, entradas e saídas por parcela; xera o caderno cun clic; valida doses. |

Conclusión: **todas rexistran traballos e sacan o caderno como informe.** Ningunha ten unha sección «caderno» onde se enchen datos.

Fontes:
- https://farmos.org/model/type/log/
- https://www.xfarm.ag/en/activity-management
- https://blog.agroptima.com/es/blog/partes-de-trabajo-app-modernizar-gestion-agricola/
- https://www.agroptima.com/en/digital-field-journal
- https://play.google.com/store/apps/details?id=com.agricolum

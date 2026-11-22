# Trazabilidade e control de calidade — análise e estratexia

Data: 2026-10-22 · Estado: **só análise** (sen implementación). Parte da idea de `documentos/modelo_negocio_app_trazabilidade.md` (blockchain, token, NFT como DNI do lote, xemelgo dixital, QR).

## 1. Que queremos conseguir

Que calquera persoa que compre o produto (consumidor final, tenda, restaurante, distribuidor ou inspector) poida comprobar **a vida real do lote** (orixe, cultivo ou cría, tratamentos, colleita, transformación, envasado e venda) **sen ter que fiarse do produtor nin da nosa plataforma**.

Clientes da app: pequenos produtores e transformadores galegos (horta, cogomelos, ovos, mel, queixo, conservas), con pouco tempo, pouco orzamento e venda en canles curtas (directa, mercados, tendas, restauración, cooperativas).

## 2. Diagnóstico da idea orixinal

| Peza do documento | Valoración |
|---|---|
| **Blockchain** como rexistro que non se pode borrar | Correcto como obxectivo. Non fai falta unha blockchain propia nin pagar transaccións: basta un **rexistro encadeado por hash** e **ancorar** periodicamente a súa "pegada" nunha cadea pública (ver §4.3). Mesma garantía, custo case cero. |
| **Token** para contabilizar lotes e tarifas | Non achega nada ao cliente e engade risco (regulación cripto, imaxe de "especulación"). A facturación faise con subscrición ou prezo por lote, sen token. |
| **NFT** como DNI fixo do lote | O concepto é bo (identificador único e inmutable); a tecnoloxía NFT non fai falta. Un identificador de lote estándar (GS1) asinado e ancorado dá o mesmo sen carteiras cripto. |
| **Xemelgo dixital** (estados engadidos ao lote) | Moi bo: é o núcleo. Modélase como **eventos só de engadir** ligados ao lote. |
| **QR** con ligazón ao lote | Necesario pero insuficiente: un QR impreso cópiase. Hai que combinalo con detección de clonados e, para produto premium, NFC criptográfico (§4.4). |

**O fallo de fondo de case todos os sistemas "blockchain alimentaria"**: garanten que o dato non se cambia *despois*, pero non que fose verdade *ao rexistralo* (o "problema do oráculo"). Se o produtor escribe "sen tratamentos" e é mentira, a blockchain fai a mentira inmutable. Ese é o oco que imos cubrir.

## 3. A proposta: "proba, non promesa"

Tres ideas que, xuntas, non ofrece ningunha solución pensada para pequenos produtores:

1. **A trazabilidade sae soa do caderno de explotación.** Dende o 1/1/2027 o rexistro electrónico de tratamentos é obrigatorio para as explotacións profesionais (CUE). O produtor que xa rexistra en horta para cumprir a lei obtén o pasaporte do lote **sen traballo extra**. Cumprir a lei = ter trazabilidade.
2. **Cada afirmación compróbase contra fontes oficiais e datos independentes**, e o consumidor ve que se comprobou, contra que fonte e cando.
3. **Calquera pode verificar a integridade sen fiarse de nós**: as probas están ancoradas nunha cadea pública e poden comprobarse con ferramentas independentes.

## 4. Arquitectura en capas

### 4.1 Captura con evidencias (sen fricción)

- **Eventos** xerados pola actividade normal en horta: sementeira, plantación, tratamento, fertilización, colleita, creación do lote, transformación (mestura ou división de lotes), envasado, expedición e venda.
- **Evidencias automáticas** en cada evento:
  - foto feita dende a app, co seu hash, data, GPS e a sinatura do dispositivo (patrón tipo C2PA de "autenticidade na captura");
  - meteoroloxía do día e lugar (Open-Meteo/MeteoGalicia);
  - xeometría da parcela (SIGPAC);
  - copia da versión do rexistro de fitosanitarios vixente ese día (snapshots semanais de `fitosanitarios/`).
- Opcional: sensores (temperatura de cámara, humidade), albarás e facturas de compra de insumos.

### 4.2 Verificación automática (o diferencial)

Cada lote leva **selos de verificación**, cada un coa súa fonte e data:

| Comprobación | Fonte |
|---|---|
| A parcela existe e o seu uso é compatible co cultivo | SIGPAC (OGC API) |
| O fitosanitario estaba **autorizado para ese cultivo e praga na data do tratamento**, e coa dose máxima | Rexistro MAPA (snapshot da semana) |
| Respectouse o **prazo de seguridade** ata a colleita | Cálculo propio sobre os anteriores |
| **Balance de masas**: os kg vendidos non superan o que é posible colleitar nesa superficie (rendemento medio ESYRCE/RECAN) nin o que entrou na transformación | Datos propios + MAPA |
| Rexistro sanitario / REGA / REAGA vixente | Rexistros oficiais (manual ao principio) |
| Certificación ecolóxica, DOP ou IXP | Certificado subido ou credencial verificable do organismo (CRAEGA, consellos reguladores) |
| Meteoroloxía coherente (p. ex. tratamento con choiva forte) | Open-Meteo/MeteoGalicia |
| Fotos tomadas no lugar e na data declarados | Metadatos asinados da captura |

O **balance de masas** é a peza antifraude máis potente e simple: impide "lavar" produto alleo baixo a etiqueta propia. A transformación (art. 12 Leader: ≥85 % de materia prima agraria) tamén se pode demostrar así.

### 4.3 Integridade inalterable e verificable por terceiros

- Cada explotación ten un **rexistro só de engadir**: cada evento leva o hash do anterior e vai **asinado** pola persoa que o rexistra (clave por usuario; no futuro, a carteira europea de identidade dixital EUDI/eIDAS 2.0).
- As correccións non borran nada: son **eventos novos** que anulan ou rectifican (como na contabilidade). Isto encaixa coa baixa lóxica que xa usa horta.
- Cada día calcúlase unha **raíz Merkle** de todos os eventos e **ánclase**:
  - **OpenTimestamps** (sobre Bitcoin): gratuíto, estándar aberto e verificable sen nós;
  - opcionalmente, un **selo de tempo cualificado eIDAS** (valor legal na UE) para clientes que o precisen.
- Calquera evento pódese demostrar cunha **proba Merkle** curta. A páxina do lote permite descargala e comprobala con ferramentas independentes.
- No futuro: aliñamento con **EBSI / TRACE4EU** (piloto europeo de trazabilidade sobre a infraestrutura de blockchain da UE, que inclúe agroalimentación).

### 4.4 Vínculo físico (antíclonado por niveis)

| Nivel | Soporte | Para | Protección |
|---|---|---|---|
| Básico | QR impreso en formato **GS1 Digital Link** cun código curto asinado | Todo produto | **Detección de clonados**: alerta se o mesmo QR se escanea en lugares ou tempos incompatibles, ou máis veces das unidades do lote |
| Premium | Etiqueta **NFC NTAG 424 DNA** (cada lectura xera unha URL única cifrada, AES-128; variante TagTamper para precintos) | Queixo, mel, viño, conservas, produto de alto valor | Non se pode clonar; detecta apertura do envase. Sen app: o móbil le o NFC directamente |
| B2B | Eventos **EPCIS 2.0** | Tendas, restauración, distribución | Intercambio estándar entre empresas, e retirada rápida dun lote (art. 18 do Regulamento 178/2002) |

Prezo das etiquetas NFC: pendente de pedir orzamento (o fabricante só di que están pensadas para despregamento masivo).

### 4.5 Experiencias por público

- **Consumidor** (sen app, multilingüe, 10 segundos): a "vida do produto" en liña de tempo; quen o produciu (cara e nome); onde (mapa a nivel de concello ou parroquia); cando se colleitou (frescura en horas ou días); tratamentos en linguaxe clara ("0 tratamentos de síntese", verificado); selos coa súa fonte. Botón para volver mercar ou contactar co produtor: **a trazabilidade convértese en canle de venda directa**.
- **Revendedor/restaurante**: portal do lote con documentos (albarás, certificados), exportación EPCIS e alertas se se retira un lote. O restaurante pode mostrar na carta o pasaporte do produto.
- **Inspector**: historial completo coas probas, exportación no formato do CUE e caderno PDF.
- **Produtor**: o lote xérase só a partir do que xa rexistra; estatísticas de escaneos (onde e cando se consome); o prezo extra conseguido aliméntase no plan de empresa.

## 5. Por que é disruptivo para este mercado

- As solucións de trazabilidade con blockchain apuntaron a grandes cadeas (o exemplo clásico é Walmart obrigando os seus provedores), con custos e esforzo que expulsan o pequeno produtor. Aquí o custo marxinal é case cero porque **reutiliza o rexistro legal obrigatorio**.
- **Verificación contra fontes oficiais** e **balance de masas**: van alén do "o produtor di".
- **Verificable sen confiar na plataforma** (ancoraxe pública e probas descargables).
- **Antíclonado progresivo**: do QR barato ao NFC criptográfico.
- **Estándares abertos** (GS1 Digital Link, EPCIS 2.0, credenciais verificables W3C, eIDAS e EBSI): nada de sistema pechado.
- Puntúa nos baremos Leader (dixitalización, innovación) e reforza o plan de empresa.

## 6. Riscos e límites (sinceros)

- **Disposición a pagar do consumidor**: os estudos son de preferencias declaradas, non de comportamento real. En Italia, unha media de 0,98 € máis por produto con trazabilidade blockchain/QR (2024). Nos EUA, uns 1,45 $ pola información trazable e uns 0,35 $ máis se está verificada con blockchain (2025). Un estudo máis antigo atopou que os consumidores españois e portugueses eran os menos dispostos a pagar un extra. **Non hai datos fiables de taxas reais de escaneo.** Conclusión: o valor non pode depender só do consumidor. Ten que estar tamén no cumprimento legal, no B2B (restauración e tendas), na venda directa e na diferenciación.
- **Lixo de entrada**: as verificacións reducen o fraude, pero non o eliminan. Hai que comunicar con exactitude que se verificou e que non.
- **Declaracións legais**: a información voluntaria (p. ex. "sen tratamentos") non pode inducir a erro (Regulamento 1169/2011). Os textos ao consumidor deben xerarse dos datos verificados, non de texto libre.
- **Protección de datos**: datos persoais e xeolocalización do produtor; consentimento e precisión do mapa limitada (concello ou parroquia).
- **Xestión de claves** para usuarios pouco técnicos: claves custodiadas pola app ao principio; carteira EUDI cando estea dispoñible.
- **Dependencia de servizos externos** (SIGPAC, MAPA): snapshots propios e degradación controlada se fallan.

## 7. Implicacións para o modelo de datos (fase 1)

Hai que deseñalas xa, aínda que se implementen despois:

- `Lote` (identificador GS1 ou propio, produto, cantidade, unidade, orixe: parcelas e cultivos ou lotes de entrada).
- `Evento` (tipo, data, referencias, contido, hash, hash anterior, sinatura, autor) **só de engadir**.
- `Evidencia` (foto, documento ou lectura, co seu hash e metadatos).
- `Verificacion` (tipo, resultado, fonte, versión da fonte, data).
- `Selado` (raíz Merkle, proba OpenTimestamps/eIDAS, data).
- `Etiqueta` (QR/NFC, lote, contador e rexistro de escaneos).
- As entidades que hoxe se borran fisicamente (cultivos, tarefas…) deberían pasar a baixa lóxica cando formen parte da historia dun lote.

## 8. Fases propostas

1. **T1**: lotes e eventos derivados dos rexistros actuais, rexistro encadeado e páxina pública do lote con QR.
2. **T2**: verificacións (SIGPAC, fitosanitarios na data, prazo de seguridade, meteoroloxía, balance de masas).
3. **T3**: ancoraxe con OpenTimestamps e verificador público descargable.
4. **T4**: fotos asinadas na captura, nivel NFC, detección de clonados por escaneos.
5. **T5**: credenciais verificables de terceiros (certificadoras), EPCIS B2B, selo eIDAS e piloto con EBSI/TRACE4EU.

## 9. Fontes

- NXP NTAG 424 DNA: https://community.Freescale.com/docs/en/brochure/NTAG424_BROCHURE.pdf · etiquetas Identiv: https://identiv.com/wp-content/uploads/2026/04/ID-Safe-A572-NTAG®424DNATT_04_26.pdf
- EBSI: https://ebsi.eu/ · TRACE4EU: https://www.intesigroup.com/en/news/trace4eu/
- C2PA, captura asinada: https://truepic.com/c2pa/capture · https://www.digicert.com/blog/why-content-authenticity-has-to-begin-at-the-point-of-capture
- IBM Food Trust e custos para pequenos: https://www.ledgerinsights.com/ibm-food-trust-blockchain-cost-food-traceability/
- Disposición a pagar: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12507238/ · https://ricerca.uniba.it/handle/11586/467024 · https://archimer.ifremer.fr/doc/00349/46017/47021.pdf
- GS1 EPCIS: https://www.gs1.org/epcis
- Lei 1/2024 de calidade alimentaria de Galicia: https://www.xunta.gal/gl/notas-de-prensa/-/nova/86903/dog-publica-hoxe-lei-calidade-alimentaria-que-reforza-aposta-pola-excelencia

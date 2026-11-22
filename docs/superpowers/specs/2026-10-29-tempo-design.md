# O tempo: MeteoGalicia e AEMET (paso 9 do deseño global)

Data: 2026-10-29 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §7bis. Tarefas 088–.

## Por que

O tempo é o contexto de cada traballo:
- un tratamento con vento ou choiva pode non servir e pode levar o produto fóra da leira;
- unha rega despois de chover gasta auga sen falta;
- abonar con aviso vermello de choiva está prohibido (RD 1051/2022, art. 4.4).

Ademais, o tempo gardado de cada traballo é unha evidencia para o xemelgo e para as estatísticas.

## O que se confirmou o 2026-10-29

Probouse cada servizo antes de deseñar. Quedan resoltas as dúas dúbidas do deseño global (§7bis):

- **MeteoGalicia non pide clave** para estes tres servizos (JSON):
  - **lista de estacións:** `servizos.meteogalicia.gal/mgrss/observacion/listaEstacionsMeteo.action`. Hai 155 estacións, con identificador, nome, concello, latitude, lonxitude e altitude.
  - **datos diarios dunha estación:** `.../observacion/datosDiariosEstacionsMeteo.action?idEst=…&dataIni=dd/mm/aaaa&dataFin=dd/mm/aaaa`. Cada medida trae código e validación. Usaranse:
    - `TA_MIN_1.5m`, `TA_MAX_1.5m`, `TA_AVG_1.5m`: temperaturas;
    - `PP_SUM_1.5m`: choiva en l/m²;
    - `VV_AVG_10m`: vento medio en m/s;
    - `VV_MAX_10m`: refacho en m/s;
    - `HR_AVG_1.5m`: humidade;
    - `ET0_SUM_1.5m`: evapotranspiración, para a rega.
  - **predición por concello:** `.../predicion/jsonPredConcellos.action?idConc=…`. Trae varios días con ceo, temperaturas, probabilidade de choiva por franxas, vento e **nivel de aviso**.
  - **MeteoSIX** (predición nun punto) si pide clave. Non se usa.
- **Código do concello:**
  - MeteoGalicia usa o **código INE** (p.ex. 15078, Santiago).
  - O código de municipio do SIGPAC é o do **Catastro**, que non sempre coincide co INE. Por iso **non se tira da referencia SIGPAC**.
  - A lista oficial de concellos é a do **INE** (`ine.es/daco/daco42/codmun/diccionario26.xlsx`): 313 concellos en Galicia. Vai na app como `data/concellos_galicia.csv`.
- **RD 1051/2022, art. 4.4:** prohibe aplicar fertilizantes:
  - a) en terreos xeados, cubertos de neve, hidromorfos ou inundados;
  - b) con **avisos meteorolóxicos vermellos por precipitacións** da **AEMET** (ou de Protección Civil).
- **O CUE non pide datos do tempo.**

## Que garda

| Onde | Campo | Para que |
|---|---|---|
| `horta` | `concello_ine` | concello da explotación: predición e avisos |
| `horta` | `estacion_meteo_id` | estación para o que non ten parcela (animais, compras…) |
| `parcela` | `concello_ine`, `estacion_meteo_id` | baleiros = os da explotación |
| **`estacion_meteo`** (nova) | `id` (o de MeteoGalicia), `nome`, `concello`, `lat`, `lon`, `altitude` | gárdase ao escollela, para mostrala e medir distancias sen conexión |
| **`tempo_dia`** (nova) | `estacion_id`, `data`, `t_min`, `t_max`, `t_media`, `choiva`, `vento_medio`, `refacho`, `humidade`, `et0`, `fonte`, `consultado` | o tempo dun día nunha estación. Única por estación e data: gárdase **unha vez** e compárteo todo o que pasou alí ese día |
| parte común de todos os traballos | `tempo_id` | o tempo dese día na estación da primeira leira, ou na da explotación |

**Estación de cada parcela:**
- Coas coordenadas da parcela, a app **propón a estación máis próxima**, coa distancia e a altitude.
- Pódese cambiar a man.
- Avisa se está a máis de 10 km (guías de extensión agraria, §8decies de `docs/estado-e-evolucion.md`).
- Mostra a altitude da estación, para comparala coa da leira. A parcela non garda altitude e non hai fonte para un límite, así que non hai aviso de altitude.

## Cando se consulta (sen servizos neste ordenador)

- **Ao escoller a data e a leira nun formulario** de tratamento, rega ou abonado, a app consulta o tempo dese día e móstrao no formulario:
  - Por exemplo: «Mabegondo, 1/10: 9–20 ºC, 0 l/m², vento 1,1 m/s (refacho 8,5)».
- **Ao gardar calquera traballo**, enlázase co tempo dese día se xa está gardado ou se se pode consultar.
- **Se non hai conexión, ou se o día aínda non rematou**, apúntase igual. O tempo énchese despois, ao abrir o Diario: unha consulta por estación cubre todos os días que faltan.
- **Ao abrir Inicio:** a predición do concello. Non se garda.

## Avisos (nunca bloquean)

| Traballo | Aviso | Fonte |
|---|---|---|
| Abonado | choiva nese día: comprobar que o terreo non estea encharcado | RD 1051/2022 art. 4.4 a) |
| Abonado | xeada (mínima ≤ 0 ºC) | RD 1051/2022 art. 4.4 a) |
| Abonado | aviso vermello de choiva da AEMET | RD 1051/2022 art. 4.4 b). Só coa clave de AEMET (paso 9c) |
| Tratamento | choiva ese día: o produto pode lavarse | etiqueta do produto |
| Tratamento | vento medio > 3 m/s: risco de deriva | boas prácticas (Junta de Andalucía, guía de contaminación difusa 2021). Lembra que é a media do día |
| Rega | choiva nos dous días anteriores, en l/m² | información, sen limiar |
| Tarefa de tratamento | choiva prevista (probabilidade ≥ 70 %) nese día | predición de MeteoGalicia |

- Os datos diarios son o **contexto do día, non a medida da hora exacta** do traballo. Os avisos dino así.

## Pasos

- **9a.** Concellos e estacións na explotación e nas parcelas, `tempo_dia`, `tempo_id` na parte común, o tempo nos formularios e os avisos dos traballos, e o enchido ao abrir o Diario.
- **9b.** Inicio, coa predición e o nivel de aviso do concello (MeteoGalicia). Avisos nas tarefas.
- **9c. AEMET**, cando o titular teña a clave (pídea el e gárdaa no ficheiro de contorno; a app nunca a manexa):
  - avisos oficiais por zona (CAP);
  - aviso vermello de choiva no abonado (RD 1051/2022).

## Informes

- **Xemelgo:** o tempo de cada traballo, coa fonte (MeteoGalicia, estación) e cando se consultou.
- **Estatísticas (paso 15):** choiva, ET0 e auga de rega por cultivo.
- **CUE e caderno:** non o piden.

## Probas previstas

- A estación máis próxima, a distancia, a altitude e o aviso de distancia.
- `tempo_dia`:
  - lese a resposta de MeteoGalicia, cun exemplo gardado nas probas: **as probas nunca usan a rede**;
  - non se duplica por estación e día;
  - as medidas sen validar quedan baleiras.
- Un traballo enlázase co tempo da estación da súa leira, ou da explotación.
- Sen conexión gárdase igual, e despois énchese ao abrir o Diario.
- Cada aviso da táboa.
- A predición do concello, lida dun exemplo gardado.
- No navegador:
  - escoller o concello e a estación;
  - apuntar un tratamento e ver o tempo e o aviso;
  - ver a predición en Inicio.

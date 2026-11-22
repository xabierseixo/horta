# Horta — Aplicación de xestión dunha horta

## 1. Obxectivo

Desenvolver unha aplicación web para a **xestión integral dunha ou varias hortas**, orientada inicialmente a uso persoal pero deseñada desde o principio para soportar varios usuarios e, eventualmente, hortas compartidas.

A aplicación debe permitir rexistrar e consultar de maneira sinxela a estrutura da horta, os cultivos, as tarefas, as sementeiras, plantacións, colleitas e o histórico das parcelas.

O obxectivo non é crear simplemente un calendario agrícola, senón unha **base de coñecemento e xestión da propia horta**, onde os datos históricos permitan saber que se fixo, onde, cando e con que resultados.

---

## 2. Tecnoloxía inicial

O proxecto estará desenvolvido en Python.

Tecnoloxías previstas:

* **uv** para xestión do proxecto e dependencias Python.
* **NiceGUI** como framework da interface web.
* **SQLAlchemy** como ORM.
* **SQLite** inicialmente como base de datos, deixando a arquitectura preparada para PostgreSQL.
* **Alembic** para migracións da base de datos.
* **Pydantic** para validación e modelos de datos.
* **httpx** para comunicación con APIs externas.
* **pytest** para probas.
* **Ruff** para linting e formato.
* **mypy** para comprobación de tipos.

A arquitectura debe evitar dependencias innecesarias e manterse sinxela, modular e fácil de manter.

**Preferir sempre compoñentes nativos de NiceGUI antes ca librarías externas soltas.** En particular, para funcionalidades xa previstas neste documento:

* `ui.leaflet` para o plano da horta (§5): parcelas coma polígonos debuxables, galiñeiros/instalacións coma marcadores, sen depender de ningunha libraría JS de mapas á parte.
* `ui.echart` para gráficas (produción, gastos/ingresos, §12).
* `ui.date` / `ui.timeline` para calendario e liñas de tempo (§9).
* **WeasyPrint** (HTML→PDF) e **openpyxl** (Excel) coma as únicas dependencias novas necesarias para xerar o caderno de explotación exportable (§22) — non hai equivalente nativo en NiceGUI para isto.

---

# 3. Concepto principal

A entidade central da aplicación é a **Horta**.

Un usuario pode ter unha ou varias hortas e unha horta pode, no futuro, ser compartida por varios usuarios con diferentes permisos.

Modelo conceptual:

```text
Usuario
   │
   ├── Horta
   │      │
   │      ├── Parcelas
   │      │      └── Cultivos
   │      │
   │      ├── Animais
   │      │      └── (galiñas, coellos, ...)
   │      │
   │      ├── Tarefas
   │      │
   │      ├── Sementeiras
   │      ├── Plantacións
   │      ├── Colleitas
   │      └── Histórico
   │
   └── outras Hortas
```

Non debe asumirse que unha conta de usuario equivale necesariamente a unha única horta.

Cada horta debe poder almacenar, como mínimo:

* nome;
* descrición;
* **uso profesional** (booleano: autoconsumo / con actividade comercial). Determina se se activan os campos e obrigas do caderno de explotación (ver §22).

---

# 4. Usuarios

A aplicación debe contemplar autenticación e xestión de usuarios.

Non se debe implementar manualmente un sistema de contrasinais se existe unha solución madura e adecuada para o ecosistema FastAPI/NiceGUI.

Debe estudarse a mellor opción entre:

* sistema de autenticación integrado;
* libraría especializada para FastAPI;
* OAuth/OIDC;
* ou outro mecanismo apropiado.

A decisión debe priorizar:

* seguridade;
* mantemento;
* madurez;
* compatibilidade co stack;
* facilidade de evolución.

Nunha fase posterior debería ser posible que varios usuarios compartan unha horta.

Exemplo:

```text
Horta "A miña horta"

Xabier     → administrador
Ana        → editor
Pepe       → lectura
```

---

# 5. Parcelas

A horta está dividida en parcelas.

Cada parcela debe poder almacenar, como mínimo:

* nome;
* descrición;
* superficie;
* posición (campo simple, preparando o terreo para a futura representación gráfica);
* uso/aproveitamento (cultivo, secano ou regadío) — dato esixido polo caderno de explotación cando a horta é de uso profesional (ver §22);
* referencia SIGPAC (provincia, concello, polígono, parcela, subparcela) — opcional, só relevante se a horta é de uso profesional;
* notas;
* estado;
* histórico de cultivos.

Debe ser posible crear, modificar e eliminar parcelas.

A interface debería permitir visualizar as parcelas dunha forma intuitiva.

Idealmente debería existir unha representación gráfica/plano da horta:

```text
┌─────────────────────┬────────────────────┐
│                     │                    │
│      PARCELA 1      │      PARCELA 2     │
│                     │                    │
├─────────────────────┼────────────────────┤
│                     │                    │
│      PARCELA 3      │      PARCELA 4     │
│                     │                    │
└─────────────────────┴────────────────────┘
```

Non é necesario implementar inicialmente un GIS complexo. Pode comezarse cun plano sinxelo.

Cando se implemente, usar o compoñente nativo `ui.leaflet` de NiceGUI (ver §2): permite debuxar as parcelas coma polígonos editables e gardar as súas coordenadas, sen engadir ningunha dependencia de mapas á parte.

---

# 6. Cultivos

Un cultivo representa algo plantado ou sementado nunha parcela.

Debe poder rexistrarse:

* especie;
* variedade;
* parcela;
* data de sementeira;
* data de plantación;
* data prevista de colleita;
* data real de colleita;
* cantidade;
* unidade;
* estado;
* notas;
* fotografías, se se considera apropiado.

Exemplos:

```text
Tomate
Variedade: Negro de Santiago
Parcela: Norte
Sementeira: 15/03/2026
Plantación: 02/05/2026
```

---

# 7. Animais

Ademais dos cultivos, unha horta pode ter animais (galiñas, coellos, etc.) como unha entidade independente das parcelas — un galiñeiro ou unha coellería non é unha parcela de cultivo.

Debe poder rexistrarse, por especie/lote:

* especie (galiñas, coellos, etc.);
* raza ou variedade, se procede;
* cantidade;
* data de alta;
* data de baixa, se procede;
* estado;
* notas;
* fotografías, se se considera apropiado.

Exemplo:

```text
Galiñas
Raza: Rubia Galega
Cantidade: 6
Alta: 10/02/2026
```

Isto permitirá posteriormente rexistrar producións asociadas (ovos, carne, etc.), de forma similar ás colleitas dos cultivos.

---

# 8. Tarefas

A aplicación debe permitir crear tarefas relacionadas coa horta.

Exemplos:

* sementar;
* plantar;
* regar;
* fertilizar;
* podar;
* tratar;
* revisar;
* colleitar;
* preparar parcela;
* retirar cultivo.

Unha tarefa debería poder ter:

* descrición;
* data;
* data límite;
* parcela;
* cultivo relacionado;
* prioridade;
* estado;
* notas.

A pantalla principal debería mostrar as tarefas pendentes e as tarefas próximas.

---

# 9. Calendario

Debe existir un calendario da actividade da horta.

Debe poder visualizar:

* sementeiras;
* plantacións;
* tarefas;
* colleitas;
* tratamentos;
* outros eventos.

Sería interesante dispoñer de vistas:

* mensual;
* semanal;
* lista.

---

# 10. Histórico

O histórico é unha parte importante da aplicación.

Debe ser posible saber que se fixo anteriormente nunha parcela.

Por exemplo:

```text
PARCELA 1

2024 → fabas
2025 → tomate
2026 → repolo
```

Isto permitirá posteriormente implementar funcionalidades relacionadas coa **rotación de cultivos**.

Tamén debe ser posible consultar o histórico dun cultivo ou variedade.

**Nota de deseño (inspirada en farmOS, software agrícola de código aberto)**: en lugar de modelar Tarefas, Sementeiras, Plantacións, Colleitas e Tratamentos coma entidades independentes que despois hai que enlazar co Histórico, considerar un único concepto de **evento/rexistro** ligado a unha parcela/cultivo/animal, cun estado `pendente` ou `feito`. Un evento pendente É a tarefa (aparece en "tarefas pendentes", §8); ao marcalo `feito` (con data real, cantidades, etc.) pasa a formar parte automaticamente do histórico, sen duplicar datos nin lóxica entre dous sistemas distintos. Isto simplifica o modelo e encaixa coa filosofía de complexidade mínima (§21). A decidir en detalle cando se implementen estas fases.

---

# 11. Colleitas

As colleitas deben poder rexistrarse.

Por exemplo:

```text
Tomate — Negro de Santiago

02/08/2026 → 2,4 kg
08/08/2026 → 3,1 kg
15/08/2026 → 2,7 kg

Total → 8,2 kg
```

Isto permitirá posteriormente obter estatísticas:

* produción por cultivo;
* produción por parcela;
* produción por variedade;
* produción anual;
* evolución ao longo dos anos.

---

# 12. Xestión económica

A aplicación debe permitir controlar, de forma sinxela, o que se gasta e o que se ingresa pola horta — sen ser un programa de contabilidade nin de facturación.

Un **gasto** ou un **ingreso** debe poder rexistrarse con:

* data;
* categoría (sementes, fertilizantes, ferramentas, veterinario/pensos, venda de excedentes, etc.);
* importe;
* descrición;
* ligazón opcional a un cultivo, parcela ou animal concreto.

A aplicación debe poder amosar totais agregados (por categoría, por cultivo, por parcela, por ano) e unha vista simple de balance (gastos vs. ingresos), sen necesidade de partida dobre nin de xerar facturas.

**Aviso legal informativo**: existe normativa de venda directa/proximidade (estatal e Decreto 125/2014 en Galicia) que permite vender excedentes agrícolas sen darse de alta como autónomo, sempre que non se superen certos límites anuais por produto (p.ex. 30.000 kg de froita) e se empreguen canles permitidas (venda na propia explotación, mercados locais, entrega a domicilio). Para ovos, hai exención de marcado individual se hai menos de 50 galiñas poñedoras e a venda é en mercado público local. A aplicación debería poder amosar un aviso informativo destes límites cando a horta é de uso profesional e ten ingresos rexistrados, sen bloquear nada automaticamente.

---

# 13. Meteoroloxía

Nunha fase posterior a aplicación debería poder consultar datos meteorolóxicos mediante unha API externa.

Información potencial:

* temperatura;
* precipitación;
* previsión;
* humidade;
* vento.

A meteoroloxía debería integrarse coa información da horta e non ser simplemente unha pantalla independente.

Por exemplo, podería permitir posteriormente relacionar precipitacións e tarefas de rega.

**Fontes elixidas (decisión do 2026-10-28, substitúe a anterior de Open-Meteo)**: **MeteoGalicia** (datos reais das estacións galegas, sen clave; citar MeteoGalicia e a Consellería) e **AEMET OpenData** (previsión e avisos oficiais; clave gratuíta que solicita o titular). Fontes oficiais, galega e estatal.

---

# 14. Sensores IoT

A aplicación debe ofrecer a opción de conectar sensores físicos (IoT) ás parcelas ou instalacións, para complementar os datos introducidos a man. É unha funcionalidade opcional: quen non teña sensores segue usando a app con introdución manual de datos.

**Sensores de baixo custo, só software (sen hardware novo)**:

* **Xeolocalización do navegador** (`ui.run_javascript` + Geolocation API do móbil/PC): permite marcar automaticamente a posición GPS dunha parcela ao crearla, en vez de introducila a man (complementa o plano da horta, §5).
* **Cámara do dispositivo** (compoñentes nativos de NiceGUI): capturar fotos de cultivos/animais/colleitas directamente dende o navegador, sen ter que subir un ficheiro a man (§6, §7, §15).

**Sensores IoT físicos** (opcional, requiren hardware adicional — microcontrolador tipo ESP32 ou Raspberry Pi con sensores conectados):

* Humidade e temperatura do solo, por parcela — para suxerir ou automatizar tarefas de rega (§8/§9).
* Temperatura/humidade ambiental, pluviómetro — como complemento ou alternativa local aos datos de MeteoGalicia e AEMET (§13).
* Sensores en instalacións de animais (temperatura de galiñeiro, etc.).

Os sensores publicarían os seus datos por **MQTT** (patrón estándar en proxectos IoT/domótica, e xa usado en proxectos de robótica construídos sobre NiceGUI), e a aplicación subscribiríase para gardar as lecturas e amosalas en gráficas (`ui.echart`, §2). Isto require mercar e configurar hardware físico e engade unha dependencia nova (cliente MQTT); non é un requisito do produto, senón unha vía de ampliación para quen queira ir máis alá do rexistro manual. A decidir en detalle se e cando se aborda esta fase.

---

# 15. Fotografías

Sería interesante permitir fotografías asociadas a:

* parcelas;
* cultivos;
* tarefas;
* colleitas.

Por exemplo, poder visualizar a evolución dunha parcela:

```text
Marzo       Abril       Maio        Xuño
  📷          📷          📷          📷
```

Esta funcionalidade pode implementarse nunha fase posterior.

---

# 16. Rotación de cultivos

A aplicación debe estar deseñada para poder incorporar posteriormente un sistema de rotación.

Debe ser posible consultar:

```text
              2024       2025       2026       2027

Parcela 1    Fabas      Tomate     Repolo     Fabas
Parcela 2    Repolo     Fabas      Tomate     Repolo
Parcela 3    Tomate     Repolo     Fabas      Tomate
```

Inicialmente non é necesario implementar recomendacións automáticas.

---

# 17. Dashboard

A pantalla principal debería proporcionar unha visión rápida do estado actual da horta.

Exemplo conceptual:

```text
┌─────────────────────────────────────────────────────┐
│ 🌱 A MIÑA HORTA                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  4 parcelas     12 cultivos     7 tarefas pendentes│
│                                                     │
├───────────────────────┬─────────────────────────────┤
│ TAREFAS DE HOXE       │ PRÓXIMAS ACTIVIDADES       │
│                       │                             │
│ ☐ Regar tomates       │ 25/09 — Plantar repolo    │
│ ☐ Revisar fabas       │ 28/09 — Sementar fabas    │
│                       │ 02/10 — Plantar allos     │
├───────────────────────┴─────────────────────────────┤
│                                                     │
│                 PLANO DA HORTA                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

Debe ser unha interface clara e usable tanto en ordenador como en tablet/móbil.

---

# 18. Asistente de IA

A IA non debe ser o núcleo da aplicación.

Primeiro debe existir unha base de datos estruturada e fiable.

Nunha fase posterior podería incorporarse un asistente capaz de responder preguntas utilizando os datos reais da horta.

Exemplos:

> Que teño que facer esta semana?

> Que plantei na parcela Norte o ano pasado?

> Cantos quilos de tomate collín en 2026?

> Cando sementei as fabas?

> Que parcelas están libres?

O asistente debe consultar os datos da aplicación e non inventalos.

Se posteriormente se engade información externa (calendarios agrícolas, documentación, etc.), podería incorporarse un sistema RAG.

---

# 19. API e arquitectura

A aplicación debe manter unha separación razoable entre:

```text
Interface
    ↓
Lóxica da aplicación
    ↓
Modelos / servizos
    ↓
Base de datos
```

NiceGUI será inicialmente a interface principal, pero a lóxica da aplicación non debe quedar completamente mesturada co código da interface.

A arquitectura debería permitir no futuro:

* API REST;
* aplicación móbil ou outro frontend;
* integración con servizos externos;
* PostgreSQL;
* diferentes clientes.

Non se pretende construír inicialmente unha arquitectura excesivamente complexa. Debe aplicarse o principio de **complexidade mínima necesaria**.

---

# 20. Deseño da interface

A interface debe ser:

* limpa;
* clara;
* rápida;
* responsive;
* usable en móbil;
* usable en tablet;
* usable en escritorio.

Debe priorizar a información útil sobre decoración.

A navegación podería organizarse aproximadamente como:

```text
🏠 Inicio

🌱 Horta
   ├── Parcelas
   ├── Cultivos
   └── Plano

📅 Calendario

✓ Tarefas

🥕 Colleitas

📊 Estatísticas

🌦 Meteo

⚙ Configuración
```

---

# 21. Filosofía do proxecto

A aplicación debe ser **data-centric**.

A información estruturada da horta é a fonte de verdade.

As funcionalidades futuras, incluída a IA, deben construírse sobre esa información.

O deseño debe evitar:

* complexidade innecesaria;
* dependencias excesivas;
* duplicación de datos;
* lóxica empresarial mesturada coa interface;
* dependencias fortes dun provedor externo.

A aplicación debe poder funcionar inicialmente de forma local e posteriormente poder ser despregada nun servidor.

---

# 22. Caderno de explotación (cumprimento normativo)

> **Actualización 2026-10-22 (substitúe o dito máis abaixo sobre SIEX e sobre a data de 2026).** Verificado no texto consolidado do BOE: o RD 1039/2025 (BOE-A-2025-23421) modificou o art. 16.1 do RD 1311/2012. O rexistro de tratamentos das explotacións agrarias é o **Caderno Dixital de Explotación Agrícola integrado no SIEX**, rexistrado electronicamente na aplicación que habilite a autoridade competente; o papel vale **ata o 31/12/2026** e a obriga empeza o **1/1/2027**. Decisión: o obxectivo a longo prazo é que horta sexa unha **aplicación CUE comercial autorizada**; mentres tanto, exportación PDF/Excel e nun formato que acepte a ferramenta pública do CUE. Ver `docs/estado-e-evolucion.md` §2.2.

A aplicación debe poder servir tanto para uso doméstico coma para unha pequena explotación profesional, cumprindo a normativa de rexistro cando corresponda.

**Cando aplica**: a obriga legal de levar un caderno de explotación só existe quen supera o limiar de autoconsumo — hai venda de produto, e/ou úsanse fitosanitarios de uso profesional, e/ou é gandaría non exenta por especie/cantidade (regulado por normativa europea, estatal e galega — ver detalle abaixo). Unha horta de autoconsumo sen fitosanitarios profesionais **non ten obriga legal ningunha**.

Cada horta ten un campo **uso profesional** (§3) que activa ou oculta os campos e obrigas descritos nesta sección.

## Normativa de referencia

* **UE** — Regulamento (CE) 1107/2009 (art. 67.1): obriga de rexistro de tratamentos fitosanitarios para usuarios profesionais. Directiva 2009/128/CE: define "operador profesional".
* **Estado** — RD 1311/2012 (marco de uso sostible de fitosanitarios), Anexo III: é a norma central, detalla os campos esixidos (ver abaixo). Orde APA/204/2023: amplía os campos do Anexo III (equipo aplicador, asesoramento recibido en tratamentos e fertilización, micronutrientes e carbono orgánico na fertilización). RD 34/2025 (que modifica o RD 1311/2012 e o RD 1054/2022): dende o 1 de xaneiro de 2026 o rexistro de tratamentos fitosanitarios ten que ser **electrónico** (xa non vale papel) para calquera usuario profesional, independentemente do tamaño da explotación — **verificado contra o texto oficial (BOE-A-2025-998) o 2026-09-26: esta obriga é só "electrónico" fronte a papel, NON esixe conexión a SIEX nin software homologado**; iso é distinto do Caderno Dixital de Explotación (CUE) completo, que segue sendo voluntario agás para explotacións >30 ha (ou >5 ha de regadío). Conservación de rexistros: mínimo 3 anos.
* **Estado (gandaría)** — obriga xeral de Libro de Explotación Gandeira (altas/baixas, alimentación, medicamentos, saídas de produto); RD 1547/2004 (cunícola) e RD 637/2021 (avícola) para os anexos mínimos específicos. Exención expresa para autoconsumo (p.ex. coellos: exento ata 5 femias reprodutoras sen venda).
* **Galicia** — a Consellería do Medio Rural segue o marco estatal (ferramenta XEAGA); o REAGA (Decreto 253/2008) exime as explotacións de autoconsumo do rexistro estándar.

## Campos mínimos esixidos (cando a horta é de uso profesional)

Por **parcela** (xa recollido en §5): referencia SIGPAC, superficie, uso/aproveitamento, secano/regadío.

Por **tratamento fitosanitario** (a modelar quando se implemente esa funcionalidade en Cultivos): data, parcela, praga a controlar, cultivo (especie+variedade), superficie tratada, produto (nome + nº de rexistro), dose/cantidade empregada, valoración da eficacia, identificación do aplicador, equipo aplicador, persoas que interveñen no asesoramento (esixido pola Orde APA/204/2023, que amplía o Anexo III do RD 1311/2012).

Por **fertilización**: data, superficie, tipo (emenda/abonado de fondo/cobertoira), produto e dose, valores de N/P/K, composición en carbono orgánico, micronutrientes, asesoramento recibido (tamén esixido pola Orde APA/204/2023).

Por **animais** (se a horta é comercial e non está exenta por especie/cantidade): altas/baixas, alimentación, medicamentos, saídas de produto (ovos, carne...).

**Regra transversal**: os rexistros regulados non deben poder borrarse fisicamente (só baixa lóxica), para poder cumprir os 3 anos de conservación esixidos cando aplique.

Estes campos regulados intégranse dentro das funcionalidades xa previstas (Cultivos §6, Animais §7, Histórico §10) — non son un módulo separado. O que non é obrigatorio por lei (custo/tempo por operación, maquinaria, provedores/facturas, trazabilidade por lote, condicións meteorolóxicas) queda como boa práctica opcional, non como requisito.

## Xeración do caderno

Existe un sistema oficial de intercambio (FEGA/SIEX, anexos técnicos V/VI/VII) que permite a un software homologarse coma "CUE comercial" e conectarse en tempo real coa administración (en Galicia require rexistro formal, formularios MR407B/C/D). **Iso non é necesario** para que a aplicación sexa útil e legalmente defendible: é un compromiso técnico e de mantemento moi grande que contradí a filosofía de complexidade mínima e de non depender fortemente dun provedor externo (§21). Confirmado contra o texto oficial (RD 34/2025, BOE-A-2025-998): a obriga de rexistro electrónico de fitosanitarios (dende 2026-01-01) non esixe explicitamente esta homologación nin conexión SIEX para o rexistro propio do agricultor — só para outras obrigas distintas (trazabilidade produto-distribuidor vía RETO). Se algún día se precisa conectar cun sistema oficial, iso faise noutra aplicación distinta, non dentro de horta.

O que realmente esixe a normativa é poder **presentar os rexistros** cos campos do Anexo III nunha inspección — en papel ou en calquera formato lexible. É tamén o patrón que usan as apps comerciais existentes deste sector (FieldPad, Agricolum, CxTierra): un botón único que xera un PDF/Excel co formato oficial, sen integración en tempo real con ningún sistema externo.

**Decisión de deseño**: cando se implementen Cultivos e Tratamentos, engadir unha función de **exportar/xerar PDF do caderno de explotación** (por horta e por ano), coa estrutura dos modelos oficiais de referencia (datos da explotación, táboa de parcelas, táboa de tratamentos, táboa de fertilización). A integración directa co sistema oficial FEGA/SIEX queda como posibilidade opcional para unha fase moi posterior — non é un requisito.

---

# 23. Primeira versión

Non intentar implementar todo de golpe.

A primeira versión funcional debería limitarse a:

1. Usuarios/autenticación.
2. Crear unha horta.
3. Crear parcelas.
4. Crear cultivos.
5. Crear tarefas.
6. Dashboard básico.
7. Persistencia en SQLite.
8. CRUD completo.
9. Tests básicos.

Despois poderanse engadir:

* calendario;
* plano da horta;
* colleitas;
* produción animal (galiñas, coellos, ...);
* caderno de explotación completo (tratamentos fitosanitarios, fertilización, rexistro gandeiro — ver §22; os campos base xa se inclúen en horta/parcelas desde a v1);
* xestión económica (gastos e ingresos, ver §12);
* fotografías;
* meteoroloxía;
* sensores IoT (xeolocalización e cámara son sinxelas de engadir; sensores físicos de humidade/temperatura son opcionais e requiren hardware, ver §14);
* rotación;
* estatísticas;
* API;
* asistente de IA.

## Obxectivo da primeira iteración

Conseguir unha aplicación na que sexa posible:

```text
crear usuario
      ↓
crear horta
      ↓
crear parcelas
      ↓
crear cultivos
      ↓
crear tarefas
      ↓
consultar/modificar/eliminar datos
      ↓
pechar aplicación
      ↓
volver entrar
      ↓
os datos seguen aí
```

A prioridade inicial é ter unha **base sólida e funcional**, non unha gran cantidade de funcionalidades.

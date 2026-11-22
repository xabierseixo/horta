# Horta unificada — estado actual e evolución

Data: 2026-10-22 · Documento vivo: actualizar cada vez que cambie o estado ou unha decisión.

## 1. Obxectivo

Construír unha única aplicación, **horta**, para produtores primarios, transformadores ou ambas cousas, que integre:

1. Xestión da explotación (hortas, parcelas, cultivos, animais, tarefas, caderno de explotación).
2. Plan de empresa que cumpra o modelo oficial de **AGADER** (e que poida presentarse a outras administracións).
3. Fitosanitarios: catálogo oficial do MAPA e validación dos tratamentos.
4. Conexión ás fontes oficiais do Estado (MAPA/FEGA) e da Xunta de Galicia.
5. **Trazabilidade e control de calidade "inhackeable"** para o consumidor final ou revendedor: o elemento diferencial.

Ámbito: **toda Galicia**. Nada se deseña para unha comarca ou GDR concreto; as regras que varían por zona (p. ex. baremos dos GDR) son datos configurables.

## 2. Inventario e estado actual (verificado o 2026-10-22)

Cartafol `/home/xabier/dev/agrogandeiria/`:

| Cartafol | Que é | Estado |
|---|---|---|
| `horta/` | App Python 3.11 + NiceGUI + SQLAlchemy + Alembic + SQLite. Repo git. **Base da app unificada.** | 144 tests pasan, mypy OK. BD na migración `9ceefdfded77`. |
| `axe360_compat_release/` | AXE 360 v2.0, plan de empresa (SPA JavaScript, castelán, sen rede). **Versión base** para portar (só o "Modo compatible (navegador local)"; a versión Windows/Electron descártase). | Ver auditoría AGADER §3.4: non cumpre o modelo oficial. |
| `axe360_compat_release-modificado/` | O mesmo con melloras feitas antes (prezos MAPA dinámicos, VAN/TIR, impostos, tesourería, informe de 13 seccións, correccións). | **Só referencia**. Ver `INFORME_MELLORAS_PARA_CLAUDE.md`. |
| `fitosanitarios/` | Descarga semanal do rexistro de fitosanitarios do MAPA (regfiweb), snapshots, normalización a SQLite (2.080 produtos, 62.616 usos), API FastAPI. | Funcional. Pendente: ponte de códigos SIEX↔MAPA. |
| `documentos/` | `modelo_negocio_app_trazabilidade.md`: idea da trazabilidade (blockchain, token, NFT como DNI do lote, xemelgo dixital, QR). | Idea xenérica; solución técnica por definir (ver §5). |

### 2.1 horta en detalle

- Feito: autenticación, usuarios e roles, hortas compartidas, parcelas (con SIGPAC), animais, cultivos, tratamentos e fertilización con campos do Anexo III do RD 1311/2012 e baixa lóxica, tarefas, dashboard, busca/filtros/paxinación.
- Campos xeográficos (commits `1b8a70c`, `a1f0d6f`): `lat`, `lon`, `geometria`, `imaxe` en Parcela editables polo servizo, con validación de coordenadas e tests (tarefa 001, feita polo modelo local). Pendente: UI destes campos; decidir se `ultima_conexion`/`foto_perfil` (hoxe en Horta) van en Usuario.
- Contorno: o `.venv` foi copiado de `/home/xabier/dev/horta` e ten rutas vellas → `uv run pytest`/`alembic` fallan. Resolto o 2026-10-22: `.venv` recreado e `horta-venv/` (contorno antigo sobrante) eliminado.

### 2.2 Contradicións detectadas a resolver

1. **Normativa do caderno — verificado no BOE o 2026-10-22**: o texto consolidado do RD 1311/2012, art. 16.1, di que o rexistro de tratamentos da explotación é o **"Cuaderno Digital de Explotación Agrícola", integrado no sistema do RD 1054/2022 (SIEX)**; que a información "deberá registrarse de manera electrónica en la aplicación que se habilite al efecto por la autoridad competente", cun mes de prazo; e que os operadores profesionais agrarios poden seguir en **papel ata o 31/12/2026**. Ese parágrafo modificouno por última vez o **RD 1039/2025, do 19 de novembro** (BOE-A-2025-23421, disp. final 1.ª), que aprazou a obriga do 2026 ao **1/1/2027** (o RD 34/2025 a fixara en 2026). Polo tanto `ANALISE.md` está ao día e a afirmación de `CLAUDE.md` ("non esixe SIEX") **xa non se sostén** para explotacións profesionais a partir de 2027. Consecuencia: para os usuarios profesionais, horta terá que exportar a un formato que acepte a ferramenta pública ou unha app CUE autorizada, ou rexistrarse como CUE comercial. **Decidido (2026-10-22): o obxectivo é chegar a ser aplicación CUE comercial autorizada; mentres tanto, exportación PDF/Excel e nun formato que acepte a ferramenta pública do CUE.** Actualizados `CLAUDE.md` e `README.md` §22.
2. **SIEX**: resolto co punto anterior — integración co SIEX como obxectivo (CUE comercial), por fases.
3. **Idioma**: AXE en castelán, horta en galego. O formulario de AGADER existe nas dúas linguas oficiais.

## 3. Plan de empresa

### 3.1 Que esixe AGADER (verificado contra o texto oficial)

Fonte: convocatoria Leader MR701L, DOG nº 21 do 2/2/2026 (Resolución do 30/12/2025), PDF completo descargado e lido. A súa única modificación (DOG nº 157, 20/8/2026) **só cambia o art. 5 (orzamento)**; os anexos non cambian. Non existe unha "guía de plan de empresa" pública de AGADER: o que se presenta é o **formulario normalizado**.

**Anexo III — "Resumo do proxecto – plan de empresa (proxectos produtivos)"**:

- Datos da persoa solicitante e representante (tipo/número de identificación, país emisor, nome ou razón social, apelidos).
- Datos do proxecto: título; nº de expediente, anualidade, submedida, GDR.
- Datos da empresa: nova/existente; actividade principal (CNAE); participa ou está participada ≥25 % (si/non); nº de traballadores, facturación (€) e balance (€) — da empresa ou do grupo, criterios do anexo I do Regulamento (UE) 651/2014.
- 1. Descrición do proxecto, obxectivos e finalidade.
- 2. Breve descrición do proceso de elaboración do produto ou servizo (medios humanos e materiais).
- 3. Incidencia sobre o emprego en UTA: empregos mantidos; total creados; creados en colectivos (emprego feminino, persoas mozas, persoas maiores, persoas con discapacidade, outros).
- 4. Formación específica do promotor vinculada ao proxecto.
- 5. Plan de financiamento (importe € e %): capital social; recursos propios (fondos da actividade); créditos ou préstamos; subvencións concedidas; outros; total investimentos.
- 6. Previsión da conta de explotación, **anos 1 a 5**: A) Vendas; B) Custos variables; C) Custos fixos; D) Amortizacións; E) Marxe de explotación = A−(B+C+D); F) Ingresos financeiros − custos financeiros; G) Beneficio antes de imposto = E+F.
- Indicadores económicos: **VAN, TIR, PAY-BACK**.
- Sinatura, lugar e data.

**Anexo V — "Orzamento de gastos desagregados por partidas"**: partidas 1) adquisición de terreos ou inmobles, 2) obra civil e instalacións, 3) maquinaria e equipamento, 4) (verificar no PDF; non saíu na extracción de texto), 5) estudos, proxectos e honorarios, 6) gastos de constitución / outros; cada concepto con importe **sen IVE e con IVE**.

**Documentación complementaria (art. 18)** que a app pode preparar ou comprobar: (c) datos de pequena empresa; (h) **tres ofertas por gasto** (anexos VI-A/VI-B); (i) IVE recuperable ou non; (j) código de explotación agraria se hai produción primaria; (k) **plano SIXPAC con coordenadas**; (m) memoria valorada asinada se hai obra civil; (n) declaración de maquinaria nova ou mellora de capacidade >25 %; (p) calquera outra documentación (aquí encaixa a memoria completa tipo AXE).

**Requisitos xerais**: viable técnica, económica e financeiramente (art. 4.3.b); non iniciado antes da solicitude (art. 4.3.d); finalista (art. 4.3.e); só pequenas empresas (art. 4.1); informe técnico de viabilidade do GDR sobre solvencia técnica, financeira e económica (art. 26); mantemento do emprego 3 anos tras o pago final (art. 31).

### 3.2 Tipoloxía do proxecto (decide se é Leader/AGADER ou non)

| Tipo | Artigo | Condicións |
|---|---|---|
| Produción agraria primaria | 11 | **Excluída como regra xeral.** Excepcións: eficiencia enerxética/renovables na explotación; pequenos proxectos ≤30.000 € complementarios dunha actividade principal **non agraria**; mobilización de terras. 15–50 %. |
| Transformación e comercialización de produtos agrarios | 12 | Orzamento subvencionable ≤60.000 €; ≥85 % de materia prima do anexo I do Tratado; rexistro sanitario; 15–50 %. |
| Transformación de produtos forestais | 13 | Pequena escala; 15–40 %, máx. 200.000 €. |
| Actividades non agrarias | 14 | Creación/ampliación/modernización; 15–50 %, máx. 200.000 €. |
| Bono Activa Rural | 15 | Ata 18.000 €, autónomos novos, plan empresarial de 5 anos. |

Usuarios que son **produtores e transformadores**: a transformación vai por Leader (AGADER); a produción primaria vai polas liñas da Consellería do Medio Rural (MR404A mozos agricultores, MR405F investimentos), con outro plan empresarial (ver §3.5). A app debe ter un **paso previo de clasificación** que indique liña, límites e documentos.

### 3.3 Puntuación común a toda Galicia

Resolución do 27/4/2023 (DOG 10/5/2023), marco Leader 2023-2027:

- Art. 17 — criterios que poden puntuar (máx. 100): a) lugar do investimento (densidade, evolución da poboación 10 anos, paro, habitantes, envellecemento, natalidade, poboación feminina, distancia a servizos); b) emprego creado/mantido, colectivos desfavorecidos, ratio investimento/emprego; c) sustentabilidade ambiental (renovables, eficiencia, economía circular); d) innovación; e) capacidade de arrastre (transformación de produtos da zona, % de recursos endóxenos, novas iniciativas).
- Art. 19 — baremos públicos e obxectivos; nota de corte; % de axuda proporcional aos puntos entre a nota de corte e a puntuación da axuda máxima; mínimo 15 % (produtivos).

Na app: recoller unha vez os datos que cobren a–e; os **baremos dos 24 GDR como datos configurables** (todos), co GDR detectado polo concello. Pendente: recompilar os 24 baremos oficiais.

### 3.4 Auditoría do AXE orixinal fronte a AGADER

O informe do AXE é un plan de negocio xeral (resumo, xestión, plan de empresa con DAFO, mercado, marketing, referencias). Cita "AGADER · Guía del plan de empresa" como "documento local do proxecto", que non está no cartafol. **Non segue o Anexo III nin o Anexo V.**

| Bloque oficial | AXE orixinal |
|---|---|
| Solicitante/representante | ❌ só texto "promotores"; `meta.holder` existe pero non se pode editar |
| Título do proxecto | ✅ |
| Expediente/anualidade/submedida/GDR | ❌ |
| Nova/existente, CNAE, participación ≥25 % | ❌ |
| Traballadores, facturación, balance | ⚠️ horas (non persoas), balance parcial |
| 1. Descrición, obxectivos | ✅ |
| 2. Proceso e medios humanos/materiais | ⚠️ textos e activos, sen separar |
| 3. Emprego en UTA e colectivos | ❌ |
| 4. Formación do promotor | ❌ |
| 5. Plan de financiamento | ⚠️ préstamos e patrimonio; sen capital social, subvencións nin % |
| 6. Conta a 5 anos | ❌ 3 anos; o informe só mostra vendas, resultado e caixa |
| E) Marxe = A−(B+C+D) | ❌ o resultado inclúe xuros e custo de oportunidade |
| F) Resultado financeiro | ❌ xuros mesturados; calcúlanse cos anos do 1.º préstamo para todos |
| G) Beneficio antes de impostos | ❌ |
| VAN / TIR | ❌ |
| Payback | ⚠️ calculado, non mostrado |
| Anexo V (6 partidas, sen/con IVE, só investimento novo) | ❌ os activos son os existentes; 3 tipos; sen IVE |
| Ofertas (anexo VI) | ❌ |

Resultado: de 20 bloques, 3 cumpren, 6 parcialmente, 11 non. O Anexo V non se cumpre.

O que se aproveita: estudo de mercado, marketing, DAFO, xestión mensual, referencias MAPA → como **memoria complementaria** (art. 18.1.p) e para defender a viabilidade ante o GDR. Da versión modificada aprovéitanse como referencia: VAN/TIR (`irr`), calendario real de préstamos (`loanYear`), impostos, tesourería mensual, UTA, ditame.

### 3.5 Outras administracións onde presentar un plan de empresa (Estado e UE)

Galicia (para completar): Consellería do Medio Rural — **MR404A** (mozos agricultores; plan empresarial con situación inicial e final, superficie/cabezas/rendementos, maquinaria, man de obra, produción bruta e gastos por actividade, análise económica, impacto climático/auga/enerxía/Rede Natura, formación e asesoramento; RUT ≥35 % da renda de referencia) e **MR405F** (investimentos en explotacións). DOG 9/3/2026.

Estado:

| Organismo | Instrumento | Plan esixido | Verificación |
|---|---|---|---|
| **SEPE** | Capitalización da prestación por desemprego (pago único) | Memoria do proxecto (capital propio e alleo, préstamos, importe solicitado) | Fontes secundarias e folla informativa; confirmar en sepe.es |
| **ENISA** (Ministerio de Industria) | Préstamos participativos (aprox. 25.000–1.500.000 €), sen avais | Plan de negocio viable técnica e economicamente, carácter innovador | Fontes secundarias; a web oficial non respondeu |
| **SAECA** (vinculada ao MAPA) | Avais para préstamos agrarios; liñas para mozos | Vía entidade financeira; plan de viabilidade a confirmar na convocatoria (BOE) | Nota do MAPA (xuño 2026); requisitos documentais non confirmados |
| **CDTI** | Proxectos de innovación (p. ex. NEOTEC para empresas tecnolóxicas novas) | Plan de empresa + memoria técnica | De coñecemento previo; pertinente sobre todo para a propia app/empresa tecnolóxica |
| **Banca / ICO** | Préstamos (canalizan tamén garantías InvestEU) | Plan de viabilidade e tesourería | Xeral |

Unión Europea: non hai axudas directas da UE para un pequeno proxecto agrario; os fondos europeos (**FEADER**) chegan a través da Xunta (AGADER e Medio Rural). Opcións europeas directas, máis para innovación: **EIT Food** (aceleradoras, 2026 confirmado), **Erasmus para Mozos Emprendedores** (intercambio; o requisito de plan de negocio está por confirmar), **Horizon Europe / EIC** (innovación, escala grande), **InvestEU** (garantías vía banca).

Consecuencia para o deseño: **un único modelo de datos e varios formatos de saída**. Prioridade: 1) AGADER Anexo III+V; 2) Medio Rural MR404A/MR405F; 3) memoria completa (base AXE); 4) SEPE pago único; 5) ENISA/banca.

## 4. Fontes oficiais de datos

| Fonte | Datos | Acceso | Estado |
|---|---|---|---|
| **CKAN do MAPA** `servicio.mapa.gob.es/ckan/api/3/action/` | Prezos e índices percibidos/pagados (78.973 rexistros), **RECAN** (740.016 rexistros, con Galicia por OTE e dimensión económica) | API CKAN sen clave, CSV e `datastore_search`; actualización diaria | Probado. Substitúe o script PowerShell do AXE modificado. RECAN permite comparar o plan coa media real galega |
| **SIGPAC OGC API** `sigpac-hubcloud.es/ogcapi` | Recintos, cultivo declarado, elementos da paisaxe (GeoJSON) | OGC API Features; tamén WMS e ATOM | Probado. Revisar condicións de uso (unha resposta do MAPA de 2023 en datos.gob.es dicía que non se permitía acceso por código) |
| **regfiweb** (MAPA) | Fitosanitarios | Exportacións masivas JSON | Xa en `fitosanitarios/` |
| **FEGA/SIEX** | Catálogos de cultivos, pragas, etc. (Anexo V v3.11) | Descarga manual (captcha) | Parcial en `fitosanitarios/exploracion/siex/` |
| Estatística dixital MAPA | Superficies, rendementos | PowerBI | Sen API |
| Xunta: Xeaga, REAGA, MeteoGalicia, abertos.xunta.gal | Explotacións, meteoroloxía | Por investigar | Pendente |
| INE / IGE | Indicadores municipais (criterio a do art. 17) | APIs públicas | Pendente |
| Open-Meteo | Meteoroloxía | API sen clave | Xa decidido no README |

## 5. Trazabilidade "inhackeable"

Unha blockchain garante que o rexistrado non se cambia despois, pero **non que fose verdade ao rexistralo**. Proposta en tres capas:

1. **Rexistro inalterable**: lote con identificador fixo (o "NFT" do documento, sen token); eventos do lote (sementeira, tratamento, colleita, transformación, envasado, venda) nun historial só de engadir, cada evento co hash do anterior e asinado (Ed25519) por quen o rexistra; cada día publícase un hash raíz cun selo de tempo externo (**OpenTimestamps** sobre Bitcoin, gratuíto, ou **selo de tempo cualificado eIDAS**, con valor legal na UE). Blockchain completa (p. ex. EBSI) opcional máis adiante.
2. **Validación contra fontes oficiais (o diferencial)**: a parcela existe en SIGPAC; o produto fitosanitario estaba autorizado para ese cultivo e praga **na data** (snapshots semanais); respectouse o prazo de seguridade; meteoroloxía coherente; foto con GPS e data; validación opcional por terceiros (técnico, CRAEGA, consello regulador). O consumidor ve que se comprobou e contra que fonte.
3. **QR asinado** en formato **GS1 Digital Link** (compatible con EPCIS 2.0), páxina pública do lote con vistas para consumidor, revendedor e inspector. Base legal mínima: art. 18 do Regulamento (CE) 178/2002 (unha etapa atrás, unha adiante). O pasaporte dixital de produto (Regulamento (UE) 2024/1781) exclúe os alimentos (por verificar), polo que isto é valor engadido voluntario.

Encaixa coa baixa lóxica xa usada en horta. Tamén pode puntuar nos baremos Leader (dixitalización, innovación).

## 6. Arquitectura obxectivo

- **Base: horta** (Python/NiceGUI). Os cálculos do AXE pásanse a servizos Python; o catálogo de fitosanitarios intégrase como módulo de datos de referencia; os conectores oficiais son un módulo con snapshots programados (patrón de `fitosanitarios/snapshot_mapa.py` + timer systemd).
- Modelo de datos común: explotación/empresa → actividades (primaria, transformación) → parcelas, cultivos, animais → lotes → eventos; economía (gastos, ingresos, investimentos, ofertas, financiamento); emprego (persoas, UTA, colectivos); proxectos de axuda (liña, tipoloxía, GDR, baremo).
- Saídas: caderno de explotación, Anexo III/V AGADER, MR404A/MR405F, memoria completa, informe para banca/ENISA/SEPE, páxina pública do lote.

## 7. Plan de evolución (orde proposta)

1. **Estabilizar horta**: recrear `.venv`, revisar e completar os cambios do modelo local (ruff, conectar campos ou movelos), commit; mecanismo de coordinación entre axentes.
2. **Fitosanitarios en horta**: validación de tratamentos (autorizado, dose, prazo de seguridade).
3. **Economía**: colleitas, gastos, ingresos, investimentos, ofertas.
4. **Plan de empresa**: clasificación da tipoloxía → datos → Anexo III + Anexo V + control de completitude; cálculos (conta a 5 anos coas fórmulas oficiais, VAN, TIR, payback); memoria complementaria; baremos dos 24 GDR; comparativa RECAN.
5. **Conectores**: CKAN MAPA, SIGPAC, INE/IGE, meteoroloxía, Xunta.
6. **Trazabilidade**: lotes, eventos encadeados, selado, validacións, QR e páxina pública.
7. Outros formatos (MR404A/MR405F, SEPE, ENISA/banca).
8. **Novidades (lector RSS)**: módulo de novidades dentro de horta. Lista inicial de fontes proposta por Claude (BOE, DOG, MAPA, FEGA, AGADER, EUR-Lex, GS1...); as fontes pódense engadir, editar e eliminar. Novidades clasificadas por nivel (técnico, normativo, axudas). Comprobado o 2026-10-22: o BOE ten RSS; o resto hai que buscalo fonte por fonte, e decidir que facer coas que non teñan RSS.

**Fase 1 do caderno de tratamentos CUE — feita (2026-10-22, rama `fase1-caderno`)**: catálogos oficiais do FEGA versionados (1.121 cultivos con EPPO, 89.154 variedades, pragas, enfermidades, xustificacións, unidades, estados fenolóxicos, maquinaria UNE…) con importador idempotente e comando `horta-catalogos`; capa galega (51 nomes galegos); persoas con ROPO e aviso de caducidade; maquinaria con ROMA/REGANIP; tratamento fitosanitario conforme ao bloque `TratamFito` do CUE: **o modelo e os servizos** admiten varios cultivos e produtos, medidas non químicas, asesor, problemas e xustificacións codificados e aplicador con ROPO vixente obrigatorio en hortas profesionais; migración dos tratamentos antigos; non se poden borrar hortas, parcelas nin cultivos con tratamentos; **formulario en 5 pasos** (un cultivo, un problema, un produto, aplicador e máquina, eficacia), baixa de tratamentos e edición de persoas (renovar carné). Spec e plan en `docs/superpowers/`.
Pendentes desta fase: aviso de inspección de maquinaria vencida (periodicidade legal por confirmar, RD 1702/2011); variedades locais galegas (táboa `variedade_local` sen datos); selector de cultivo oficial no formulario de cultivos; no formulario: varias filas (varios cultivos/produtos), asesor e medidas non químicas; editar/completar tratamentos (incluídos os migrados, amosando os datos `orixinal_*`); editar e desactivar máquinas dende a UI; retirar o servizo antigo `tratamentos.py`; pedir ao FEGA unha vía estable para os catálogos (Lei 37/2007).

## 8. Decisións pendentes

- Idioma dos informes (galego/castelán/ambos).
- Conseguir a "Guía del plan de empresa de AGADER" usada polo AXE (se existe) e contrastala co Anexo III.
- Confirmar a partida 4 do Anexo V no PDF oficial.
- Confirmar requisitos de ENISA, SAECA, SEPE e Erasmus para Mozos Emprendedores nas fontes oficiais.
- Condicións de uso do SIGPAC por código.
- Lector RSS: fontes comúns para todos, por usuario ou mixto.

## 8bis. Comparativa con outras apps (oSIGris) — 2026-10-22

Referencia: oSIGris (cuaderno de campo SIEX, privado, orientado a técnicos e cooperativas). Fontes: web osigris.com, notas de versión da App Store (v1.71–2.0), titorías e FAQ de exploraosigris.com, comparativa de agro4data. Só se copia a **funcionalidade** que nós non temos, mellorándoa; nada de marca nin código.

Horta xa ten: hortas con membros e roles, parcelas (SIGPAC, coordenadas), cultivos (sementeira, plantación, colleita, cantidade), tratamentos e fertilizacións cos campos do Anexo III (baixa lóxica), animais, tarefas, dashboard.

| # | Funcionalidade de oSIGris que nos falta | Notas / como mellorala |
|---|---|---|
| 1 | Asistente fitosanitario: produto autorizado para o cultivo e a praga, dose, caldo, prazo de seguridade, aviso se non cumpre | Xa previsto (fase 2) co proxecto `fitosanitarios` e regfiweb |
| 2 | Stock de fitosanitarios e fertilizantes (entradas, saídas, consumo nos tratamentos) | Engadir lote do produto: serve tamén ao xemelgo (insumos con lote, guía GS1 FFV) |
| 3 | Maquinaria e equipos (ROMA, inspección ITEAF) e instalacións (almacéns) | Ligar o equipo usado en cada tratamento |
| 4 | Carné de aplicador e asesor (ROPO) por persoa | Hoxe `aplicador` é texto libre |
| 5 | Plan de abonado e calculadoras (fitosanitarios e fertilizantes) | Catálogo de fertilizantes SATIVUM (MAPA) — verificar acceso |
| 6 | Campañas por ano e duplicar unha campaña ao ano seguinte | |
| 7 | Rexistros masivos: unha mesma operación en varias parcelas dunha vez | Moi útil para pequenas explotacións con moitas parcelas |
| 8 | Seguimento de pragas e enfermidades, visitas técnicas, fenoloxía (estados BBCH) | Eventos naturais para o xemelgo |
| 9 | Rega, labores e produción como rexistros propios | Rega e labores son parte do caderno SIEX |
| 10 | Pastoreo (gando nunha parcela durante un período) | Encaixa con produtor+gandeiro |
| 11 | Mapa de datos e incidencias por parcela | `ui.leaflet` xa decidido |
| 12 | Exportación Excel con logo propio; compartir un rexistro (correo, WhatsApp) | Xa previsto: PDF/Excel do caderno |
| 13 | Estado de envío ao CUE/SIEX por rexistro | Cando sexamos app CUE comercial |
| 14 | Multiorganización (un técnico leva moitas explotacións) | Temos multihorta con roles; falta vista de técnico |
| 15 | App móbil e traballo sen conexión con sincronización | Valorar PWA; o campo galego ten mala cobertura |
| 16 | Avisos de cambios nas autorizacións de produtos | Encaixa co lector RSS e co catálogo de fitosanitarios |

Non se copia: o asistente de IA por WhatsApp (decisión: sen axentes de IA).

Onde xa somos mellores ou seremos: plan de empresa AGADER, xemelgo dixital con EPCIS para quen merca, fontes oficiais MAPA/Xunta, cero custo, transformadores ademais de produtores.

### Campos vistos dentro de oSIGris (conta de proba, 2026-10-22)

Revisión só de lectura dos formularios (sen gardar nada). O seu aviso legal prohibe copiar textos, deseño e código: só anotamos que datos piden.

- **Explotación**: nome, alias, ano de campaña, data de inicio, comunidade autónoma, NIF. Asistente en pasos: parcelas → cultivos → unidades de xestión → maquinaria → instalacións → equipo → resumo.
- **Parcelas**: debuxar no mapa, importar Excel (provincia, municipio, agregado, zona, polígono, parcela, recinto, superficie declarada, cultivo principal e de rotación con data, variedade, sistema de cultivo, certificado ecolóxico, ecorréxime, secano/regadío, produción integrada) ou shapefile (UTM 29N/30N/31N). **Unidades de xestión**: grupos de parcelas cun alias.
- **Maquinaria**: tipo (catálogo de ~700 tipos), alias, marca e modelo, nº ROMA, nº REGANIP, matrícula, enerxía, potencia, data de compra, última inspección, caducidade ITV, alugada.
- **Instalacións**: tipo, nome, enderezo, referencia catastral.
- **Equipo**: rol (administrador, técnico asesor, técnico, dono, agricultor, servizo externo), NIF, teléfono, carné ROPO (básico, cualificado, fumigador, piloto…), nº ROPO e caducidade, nº REGFER, aplicador si/non.
- **Gando**: grupos por tipo, nº REGA, cantidade; importación por Excel.
- **Fertilizantes (catálogo propio)**: tipo, nº rexistro, nome, casa comercial, provedor (nome, NIF, REGA, NIMA), inhibidor de nitrificación/ureasa.
- **Vademécum fitosanitario**: busca por nº rexistro, nome, cultivo, praga, formulado, titular, sistema de cultivo e data; marca os produtos fóra de uso; histórico de cambios.
- **Incidencias (rexistros), tamén masivas**:
  - Labor: tipo, data inicio/fin, notas.
  - Rega: tipo, cantidade, máquina, técnica.
  - Tratamento fitosanitario: produto, praga, modo de aplicación, dose e unidade, caldo, prazo de seguridade, prazo de reentrada, **nº de lote**, nº de factura, eficacia, velocidade do vento, preventivo, pre-plantación. Calculadora (produto total, caldo total e sobrante).
  - Loita non química: tipo, cantidade, nº de MDF, eficacia.
  - Fertilización: tipo, data, dose, caldo, nº de albarán/factura, tipo e modo de aplicación, xestión sostible de insumos, documento de aplicación de lodos, provedor, inhibidores. Calculadora.
  - Confirmación escribindo "VERIFICADO" antes de gardar un rexistro masivo.
- **Tarefas en segundo plano**: exportar cultivo/incidencia ao CUE, gardar campaña REA, creación de campañas, cargas masivas; **mensaxes da Estación Fitopatolóxica do Areeiro** (avisos de pragas).
- **Perfil**: asesor ROPO (nº e caducidade), carné aplicador, nº REGFER; notificacións, rexistro de actividade, integracións.

Dentro dunha explotación de proba (creada co usuario de proba, datos inventados, sen exportar nada):

- **Alta de parcela debuxando no mapa**: calcula a superficie, **detecta automaticamente o recinto SIGPAC** e ofrece axustar o debuxo ao SIGPAC. A ficha da explotación amosa zona vulnerable a nitratos, pendente media, N kg/ha aplicado, receitas pendentes e se está conectada ao SIEX.
- **Cultivo** (táboa editable): datas inicio/fin, parcela e recinto (con superficie por recinto), cultivo e variedade (catálogo), código, superficie, sistema de cultivo, nº de árbores, SAGIP, certificado ecolóxico, ecorréxime, finalidade, regadío, produción integrada.
- **Tipos de incidencia (rexistro)**: infección/praga (foto, superficie, porcentaxe, localización no mapa, **aviso anónimo aos agricultores da zona**), estado fenolóxico (foto, data de detección), visita/nota (asunto e contido), rega (superficie, cantidade, **nº de contador**, fertirrega), sementeira (superficie, kg, **lote da semente**, tratamento da semente con fitosanitario, sementeira directa, resementeira), plantación (nº plantas, marco), colleita (foto, superficie, tipo/subtipo, produto, cantidade, **albarán/factura**, semente ou planta obtida, non colleitado, enterrado), pastoreo (tipo de gando, cabezas, ubicación), cuberta vexetal (anchuras, actuación), fertilización (con **plan de abonado** e consumo de stock), tratamento fitosanitario, loita non química, analítica, comercial, labor.
- **Plan de abonado** (cultivo previo, obxectivo de colleita kg/ha, CIC, MO/C, C/N) e **calculadora SATIVUM** (estratexia, obxectivo de colleita).
- **Stock fitosanitario**: entrada con produto, data de compra, **nº de lote**, nº e capacidade de envases, prezo, factura, provedor.
- **Receita fitosanitaria** (asesor → agricultor): infección, tipo de tratamento, modo, datas, lote, factura, dose, caldo, superficie, prazos, risco, eficacia, preventivo.
- **Estación meteorolóxica** propia por API (identificador e claves).
- **Descargas**: caderno de campo (por datas, cultivos, parcelas e tipo de rexistro; só rexistros revisados), **RETO** (rexistro de transaccións de fitosanitarios) e **exportación masiva ao CUE**.

Outras apps a revisar nas seguintes roldas: FieldPad (sinxeleza e sen conexión), xFarm, Agrónic (rega), aGROSlab, Efemis/Hispatec (custos), CUE público do MAPA.

## 8ter. Segunda rolda de investigación (2026-10-22)

**Normativa verificada no BOE — fertilización (RD 1051/2022, texto consolidado, última modificación RD 934/2025, BOE-A-2025-21211):**
- Art. 5: o caderno de explotación debe rexistrar **os aportes de nutrientes e materia orgánica e a auga de rega**: datos do plan de abonado (rendemento esperado, cultivo precedente, necesidades de N, P₂O₅ e K₂O, data), datos do solo dos recintos, análise dos estercos (N, P, MO), doses e datas de cada aporte. Efectos dende o 1/1/2026 (disp. final 9ª).
- Art. 4.2: **plan de abonado obrigatorio dende o 1/9/2026** en cada unidade de produción (regadío sementado/plantado entre 1/3 e 30/6/2026: dende o 1/1/2026). Exentas: só pastos sen fertilizar; ≤10 ha de secano ou só pastos/forraxeiras para autoconsumo.
- Prohibido fertilizar en solo xeado/encharcado ou con **aviso vermello de AEMET por chuvia** (art. 4.4): posible aviso na app.
- Anexo, parte III: o asesoramento dáse por cumprido se o agricultor leva **caderno dixital** e usa unha app de recomendación de abonado **recoñecida pola comunidade autónoma** (lista publicada polo MAPA). Oportunidade: que horta sexa recoñecida pola Xunta.
- Consecuencia para horta: rega e plan de abonado pasan a ser obrigatorios (non opcionais) para explotacións profesionais. Prioridade alta.

**Outras apps:**
- **xFarm**: caderno dixital 99 €/ano; rexistros por app, WhatsApp ou voz (IA: non o copiamos); comprobación de doses e produtos antes de aplicar; almacén; conexión con +50 marcas de maquinaria (rexistro automático); exportación a portais oficiais.
- **Agroptima**: funciona **sen conexión** e sincroniza despois; partes de traballo (persoas, horas, maquinaria); **custos, beneficio e marxe por parcela, cultivo e explotación** → enlaza co plan de empresa.
- **FieldPad**: sen conexión, fotos con GPS e hora, ligazóns públicas para enviar informes sen conta.
- **farmOS** (software libre): modelo xenérico de activos (parcelas, plantacións, sementes, materiais), rexistros (logs) e cantidades con inventario; **nº de lote en sementeira, colleita e venda**; QR que abre a ficha de cada activo. Referencia de deseño para o xemelgo.

**Fontes galegas:**
- **Estación Fitopatolóxica do Areeiro** (Deputación de Pontevedra): avisos fitosanitarios en https://areeiro.depo.gal/avisos-fitosanitarios (unha páxina por aviso). Sen RSS visible: para o lector de novidades fará falta ler a páxina.

Pendente de verificar: CUE público do MAPA (funcións concretas), avisos fitosanitarios da Xunta, lista de apps de abonado recoñecidas.

## 8quater. Terceira rolda de investigación (2026-10-22)

**Contido mínimo do CUE (Orde APA/204/2023, anexo II, BOE-A-2023-5699)** — referencia para o modelo de datos de horta:
- *Por explotación*: medidas preventivas/culturais e valoración da xestión integrada de pragas; tratamentos **postcolleita** (produto tratado e cantidade); tratamentos en **edificacións/instalacións**.
- *Por unidade de cultivo*: datos xerais do cultivo (do REA) + detalle da actividade.
- *Tratamento*: data, superficie, cultivo; problema e **xustificación**; medios de defensa non químicos (tipo, cantidade, unidade, nº MDF); produto (nome comercial, **materia activa**, nº rexistro, **cantidade e unidade**); **aplicador** (nome, NIF, nº ROPO) e **equipo** (nº ROMA ou REGANIP); **asesor** (data de validación, nome, NIF, ROPO); avaliación e eficacia.
- *Semente tratada*: superficie, tipo de tratamento, data, **lote da semente**, cantidade, produto.
- *Fertilización*: o do RD 1051/2022 e **plan de abonado adxunto**; documento de lodos se procede.
- Falta en horta hoxe: materia activa, cantidade+unidade estruturadas (agora `dose` é texto), NIF/ROPO do aplicador, ROMA/REGANIP do equipo, asesor con data de validación, xustificación, semente tratada, postcolleita, tratamentos en instalacións.

**Venda directa en Galicia (Decreto 125/2014, DOG 30/9/2014)** — moi relevante para pequenos produtores:
- Inscrición no REAGA, sección **SEVEDI** (comunicación previa; non precisa rexistro sanitario).
- **Rexistro básico de vendas obrigatorio**: produto, cantidade, data e lugar de venda (e establecemento se se vende a comercio); conservar 2 anos.
- Etiqueta: nome do titular, **nº REAGA** e enderezo da explotación.
- **Cantidades máximas por produtor e ano** (anexo II): mel 3.000 kg, ovos 1.000 ducias, hortalizas 20.000 kg exterior / 40.000 invernadoiro, pataca 20.000 kg, outras froitas 20.000 kg, cereais 5.000 kg, etc. → a app pode levar a conta e avisar.
- Funcionalidade nova clara: **rexistro de vendas + etiqueta con QR** (que enlace co xemelgo).

**Lei da cadea alimentaria (Lei 12/2013, mod. Lei 16/2021)**: contratos por escrito antes da entrega (agás pago ao contado contra entrega, con factura); para o produtor primario o prezo debe cubrir o **custo efectivo de produción** → o cálculo de custos por cultivo (como Agroptima) axuda a cumprir e a negociar.

**Galiñas de autoconsumo**: RD 637/2021 obriga a inscribilas no rexistro de explotacións gandeiras (en Galicia ~139.000 inscritas).

**Técnico:**
- NiceGUI depende dunha conexión viva co servidor: **non funciona sen conexión** tal cal. Para traballo sen cobertura faría falta outra peza (app lixeira ou PWA con caché e sincronización). Decisión pendente.
- SIGPAC: hai WMS público (imaxes); os datos de recintos son "conxuntos de alto valor" (Regulamento UE 2023/138), o que favorece a reutilización. Condicións de uso por confirmar.

**Avisos fitosanitarios da Xunta**: o Servizo de Sanidade e Produción Vexetal publica avisos (p.ex. flavescencia dourada 1/2026) en mediorural.xunta.gal; falta localizar o listado oficial.

## 8quinquies. Cuarta rolda: gandaría, transformación e cogomelos (2026-10-22)

**Gandaría — libro de rexistro da explotación (RD 787/2023, art. 23 e anexo V; BOE consolidado)**:
- Obrigatorio, papel ou informático, conservar **3 anos**. Contido mínimo: código REGA, nome/coordenadas/enderezo, titular (e titular dos animais se é outro), especie, clasificación e capacidade, **enfermidades** (data e animais afectados), **cambios nos parámetros de produción** sospeitosos (enfermidade ou benestar), identificación individual e tipo de dispositivo, **entradas e saídas** (explotación de orixe/destino, código de movemento, data, nº e identificación dos animais), **visitas e vehículos** (incluído o veterinario).
- Exento de parte dos datos se o titular os mete directamente nas bases de datos oficiais.
- Formato concreto: o que aprobe cada comunidade autónoma por especie (pendente: modelo galego).

**Medicamentos veterinarios (RD 666/2023, art. 41; Regulamento UE 2019/6, art. 108)**:
- Rexistro de tratamentos en toda explotación de animais de produción (papel ou electrónico), co **nº de receita veterinaria**; apartado de **visitas veterinarias** asinadas; conservar **5 anos**.
- Campos do art. 108 (pendente de cotexar co texto oficial): data da primeira administración, medicamento, cantidade, provedor, animais tratados, veterinario, **tempo de espera**, duración.
- Para o xemelgo e a seguridade: a app pode bloquear/avisar se se vende un produto (ovos, leite, carne) dentro do tempo de espera.

**Transformación**:
- **Artesanía alimentaria de Galicia** (Decreto 174/2019; normas técnicas por produto, última orde 11/4/2025): Rexistro da Artesanía Alimentaria e distintivo oficial; microempresas <10 persoas e <2 M€.
- **Flexibilidade hixiénica** para pequenos establecementos (RD 1086/2020), p.ex. queixo tradicional (art. 8.2).
- Proxecto INNOQUESAR (Asturias): a quesería artesá precisa ferramenta **sen ordenador fixo nin Internet**, fácil durante a elaboración. Rexistros típicos: lotes, leite de orixe, temperaturas, limpeza, incidencias (APPCC).

**Cogomelos**:
- **RD 30/2009** (condicións sanitarias): só se poden vender as **especies do anexo** (A silvestres, B cultivadas, C con tratamento, D prohibidas = infracción moi grave); a etiqueta debe indicar **xénero e especie e se é silvestre ou cultivado**; identificación correcta da especie por provedor e empresa; a venda directa do produtor/recolector suxeita ao Reg. 852/2004 e ás condicións da comunidade autónoma.
- **Galicia**: venda directa permitida (Decreto 125/2014) ata **500 kg/ano ao exterior e 2.500 kg en invernadoiro**; a recolección silvestre en monte regúlaa o **Decreto 50/2014** (aproveitamento micolóxico: consumo propio, comercial, científico) baixo a Lei 7/2012 de montes.
- Funcionalidade: catálogo de especies comercializables con validación (non deixar vender unha especie non permitida), etiqueta con xénero/especie/orixe, rexistro de recolección (monte, data, cantidade, permiso).

## 8sexies. Quinta rolda: formato europeo dos rexistros e ecolóxico (2026-10-22)

**Rexistros de fitosanitarios — Regulamento de Execución (UE) 2023/564 (anexo, verificado en BOE DOUE-L-2023-80367)** — define o formato electrónico lexible por máquina que esixirá o CUE:
- *Tratamento de superficies*: nome do produto e **nº de autorización**; **data e, se procede, hora de inicio**; dose en **kg ou L de produto por hectárea**; localización = **unidade de terreo da solicitude xeoespacial da PAC (SIXC)** ou método de determinación; **hectáreas tratadas** (e fracción da unidade); cultivo con **código EPPO** e **estado fenolóxico BBCH**.
- *Espazos pechados* (almacéns, invernadoiros permanentes): kg/L por m³ ou m², nº de almacén/invernadoiro, volume ou superficie.
- *Semente / material de reprodución* (p.ex. pataca de sementeira): kg/L por kg, t ou cantidade de semente; cantidade tratada; cultivo EPPO e **nº de lote**.
- Prazo: rexistrar sen demora; se non se fai en electrónico, pasalo nun máximo de 30 días. Reg. 2025/2203 permite aos Estados non pasar a electrónico os usos anteriores ao 1/1/2027 (España: RD 1039/2025).
- **Consecuencias para o modelo de datos de horta**: catálogo de cultivos con **códigos EPPO** (gd.eppo.int), catálogo **BBCH** por cultivo, dose numérica con unidade normalizada (non texto), hora de inicio, vínculo parcela↔recinto SIGPAC, tipos de tratamento (superficie / espazo pechado / semente).
- Novo **Regulamento (UE) 2026/1123** (26/5/2026) de etiquetado de fitosanitarios (substitúe o 547/2011): revisar cando se integre o asistente.

**Medicamentos veterinarios — art. 108 do Regulamento (UE) 2019/6 (verificado no texto do BOE DOUE-L-2019-80010)**: data da primeira administración, denominación do medicamento, cantidade administrada, provedor (nome e enderezo), **proba de compra**, identificación do animal ou grupo, veterinario prescritor, **tempo de espera (aínda que sexa cero)**, duración do tratamento; 5 anos. Non hai que duplicar o que xa estea na receita.

**Galiñas de autoconsumo (Galicia)**: ata 30 poedeiras ou 50 de carne (ou equivalente); non se pode vender nada; só hai que inscribirse (formulario en liña).

**Agricultura ecolóxica**: rexistros do operador no anexo II do Reg. 2018/848 (modificado polo Delegado 2021/1691) e Reg. de Execución 2021/2119; certificación en Galicia: CRAEGA. Pendente de detallar campos.

**Indicacións xeográficas hortícolas galegas** (control Agacal): IXP **Grelos de Galicia** (todo Galicia), IXP **Pataca de Galicia** (variedades Kennebec, Agria, Fina de Carballo; ~3.400 ha). Os produtores inscritos precisan trazabilidade dende a parcela: oportunidade de rexistros compatibles co consello regulador.

**Rexistro sanitario de transformadores en Galicia**: REGASA (Decreto 204/2012), comunicación de inicio de actividade (procedemento SA550A); a venda directa de produtos primarios non o precisa.

**Fontes de datos novas (sen custo):**
- **EPPO** (códigos de cultivos e pragas): rexistro gratuíto en data.eppo.int para obter token da API; tamén base SQLite descargable a man. Condicións de reutilización por confirmar.
- **AEMET OpenData**: API key gratuíta; avisos en formato CAP (tar.gz de XML) → para o aviso "non abonar con aviso vermello". Citar AEMET.
- **MeteoGalicia**: datos das estacións automáticas galegas (últimas medidas, diarios, mensuais) aparentemente sen clave; uso libre citando MeteoGalicia e a Consellería. Complementa Open-Meteo con datos reais galegos.

## 8septies. Réximes de produción especiais (2026-10-22)

Ademais da produción "convencional", horta debe soportar os réximes que obrigan a rexistros extra. Cada explotación/cultivo/lote pode estar nun ou varios.

**1. Agricultura ecolóxica — Reg. (UE) 2018/848, anexo II modificado polo Delegado 2021/1691 (texto verificado no DOUE, BOE L 334 22/9/2021)**. Rexistros obrigatorios:
- *Vexetal*: uso de fertilizantes/correctores permitidos (data, produto, cantidade, cultivo e parcela); fitosanitarios permitidos **demostrando a necesidade** (data, produto, substancias activas, cantidade, cultivo, parcela, **praga a controlar**); produtos de limpeza/desinfección (data, produto, substancias activas, lugar); **todo outro insumo externo por parcela** e documentos de calquera excepción (p.ex. semente non ecolóxica); **recolección silvestre** (período, lugar, especies, cantidade).
- *Gandaría*: orixe dos animais (individual ou por lote/rabaño/colmea), rexistros veterinarios dos que entran, data de chegada e **período de conversión**; **réxime de alimentación** (nome dos pensos, proporcións, % de pensos propios ou da rexión, períodos de pasto e transhumancia); tratamentos veterinarios (animais, data, diagnóstico, posoloxía, produto, receita e **tempo de espera antes de vender como ecolóxico**); saídas (idade, número, peso, identificación, data, destino); baleirado de galiñeiros entre lotes.
- *Apicultura*: mapa ou coordenadas das colmeas; alimentación (produto, datas, cantidades, colmeas); zona e período de desprazamento; retirada de alzas, extracción, **cantidade e datas de colleita de mel**.
- *Conversión*: 2 anos antes da sementeira (anuais e pastos), 3 anos antes da primeira colleita (perennes); durante a conversión non se pode vender como ecolóxico; non hai recoñecemento retroactivo salvo excepcións (art. 10).
- *Grupos de operadores* (art. 36; Delegado 2021/715): pequenos agricultores poden certificarse en grupo con personalidade xurídica e **sistema de control interno** (informes de inspección interna, trazabilidade e balance de masas). Oportunidade: horta como ferramenta do SCI dunha cooperativa/agrupación. (Limiares de tamaño por verificar.)
- Galicia: control por **CRAEGA**; certificados en TRACES (xa anotado).
- **Funcionalidades derivadas**: marcar parcela/cultivo/lote como ecolóxico ou en conversión (con datas e cálculo automático do fin de conversión); validar que o fitosanitario/fertilizante estea permitido en ecolóxico (anexos do Reg. 2021/1165) e pedir a praga e a xustificación; **balance de masas** (o vendido como eco ≤ o colleitado eco); informe para a inspección de CRAEGA.

**2. Produción integrada — RD 1201/2002 (estatal) e Decreto 108/2001 (Galicia)**: normas técnicas por cultivo (material vexetal, técnicas culturais, fertilización, protección fitosanitaria, colleita e postcolleita, **anotacións e rexistros**); Rexistro Oficial de Produción Integrada de Galicia; agrupacións APRIA. Pendente: que normas técnicas están vixentes en Galicia.

**3. Indicacións xeográficas e calidade diferenciada**: IXP Grelos de Galicia, IXP Pataca de Galicia (Kennebec, Agria, Fina de Carballo), outras DOP/IXP (mel, carne, viño…); control Agacal / consellos reguladores. Reg. 2024/1143 (xa anotado).
- Termo facultativo **"produto de montaña"** (Reg. 1151/2012 e Delegado 665/2014): materias primas e pensos principalmente de zona de montaña; p.ex. animais criados alí polo menos 2/3 da súa vida. Moitas zonas de Galicia son de montaña → a app pode comprobar se un lote cumpre.
- **Artesanía Alimentaria de Galicia** (xa anotado) e **Galicia Calidade** (marca da Xunta) — pendente.

**4. Esquemas privados**: GLOBALG.A.P. IFA v6 (Smart/GFS; trazabilidade, balance de masas, retirada, reclamacións; certificación individual ou de grupo); Demeter (biodinámica) — sen datos aínda. Sistemas Participativos de Garantía (SPG) — non dan dereito ao selo ecolóxico oficial, pero hai iniciativas en España (p.ex. Mercado da Terra); o xemelgo pode servirlles de evidencia.

## 8octies. Catálogos oficiais SIEX: como se obteñen e actualizan (2026-10-22)

- **Son oficiais**: Anexo VII da Documentación Técnica Agrícola SIEX (FEGA). Documento técnico vixente **v3.11 (nov. 2025)**, interface común (Anexo VI) **v3.11.4**. O FEGA anuncia que coa **versión SIEX 5.9.0 (set. 2027)** esta documentación substitúese pola "Documentación Técnica Horizontal" → cambios seguros.
- **Consulta**: portal público https://www3.sede.fega.gob.es/bdcsixpor/catalogos (aplicación web con **reCAPTCHA**; sen API pública documentada — non se debe automatizar saltando o captcha).
- **Descarga directa sen captcha**: ZIP "Fichero de los catálogos SIEX… Circular PAC 4/2025" (17/2/2025) en fega.gob.es. Contén 18 follas Excel: **Catálogo Variedade/Especie/Tipo** (459 cultivos, 19.737 variedades, columnas: código cultivo, cultivo, código variedade, variedade, código UPOV, admisible axudas asociadas, **data de baixa**), Cultivo, Actividade agraria, Actividade sobre a cuberta, Aproveitamento, Certificación ecolóxica, Destino do cultivo, Edificacións e instalacións, Material vexetal de reprodución, Réxime de tenencia, **Réximes de calidade**, Sistema de condución, Sistema de cultivo, Sistema de explotación, SENP, Tipo de cobertura do solo, Tipo de entidade, Tipo de titular.
- Inclúe GRELOS (484), PATATA (99), BERZA, NABO, KIWI, CASTAÑO, PIMIENTO… pero **non variedades locais galegas** como pataca "Fina de Carballo" → complemento propio.
- **As apps CUE comerciais autorizadas** conéctanse por servizos web (Anexo VI); cando horta sexa autorizada, comprobar se dan acceso aos catálogos por API.

**APIs e servizos para consultas (investigación 2026-10-22, continuación)**:
- **Catálogos SIEX**: sen API pública. Publícanse como ZIP de Excel coa circular PAC de cada campaña: `20250217_…4-2025.zip` e **`20260610_Catalogos_SIEX_Circular_PAC_2026.zip` (10/6/2026)** → cadencia aproximada **anual** (máis cambios puntuais). A páxina "fichero-de-los-catalogos-siex…" da circular vixente é o punto que vixiar.
- **Interface Único Común (IUWS) do CUE/REA — Anexo VI v3.11.4**: servizo **REST/JSON** de cada comunidade autónoma. Métodos: `comunicacion/{app}` (certificado cualificado de persoa xurídica → JWT), **`comunicacionProductor/{app}/{peticion}`** (o propio agricultor autentícase na CA e o token volve á URL de callback da app, **sen certificado da empresa**), `exportarREA/{NIF}_{CIF xestora}` (datos do REA: recintos, cultivos con códigos SIEX), `exportar/{nº explotación}_{CIF}` (cuaderno), `crear/` (cargar actividades; JSON ≤ 2 MB), `comprobarEstado/{id}`, `version` (sen seguridade). Require que a CA rexistre a Entidade, a Empresa SW, o CUE-comercial, dominio e URL de callback, e a autorización expresa de cada titular. **Non ten método de catálogos.**
- O **descritor oficial do cuaderno** (estrutura JSON exacta: DatosExplotacion, AltaDGC, ActividadAgraria, TratamientosPostCosecha, TratamientosEdifInstalaciones, UsoSemillaTratada, Cosecha, Fertilizacion con BuenasPracticas, ProblematicaFito, Justificaciones, ProductosFito/MateriaActivaFormulado, IdentificadorAplicador/AplicadorEmpresa/EquipoAplicador, AsesorValidacion, Maquinaria, EnergiaUtilizada…) e o do REA gardáronse en `docs/referencia/siex/`. **É a referencia para o modelo de datos de horta.**
- Outras APIs con consulta sinxela xa identificadas: **SIGPAC OGC API** (`sigpac-hubcloud.es/ogcapi`, recintos por coordenadas, aberta), **CKAN do MAPA**, **EPPO** (token gratuíto), **AEMET OpenData** (clave gratuíta), **MeteoGalicia**.

**Deseño decidido para non quedar obsoletos**:
1. Os catálogos gárdanse na BD **con versión** (fonte, URL, data da versión, data de importación).
2. **Nunca se borra un código**: se o FEGA o dá de baixa, márcase coa data de baixa; os rexistros antigos seguen apuntando ao código válido no seu momento (requisito legal de conservación).
3. **Script de importación** idempotente (`importar-catalogos`) que compara a versión nova coa actual e informa de altas, baixas e cambios.
4. **Vixilancia automática**: tarefa periódica que comproba se a páxina do FEGA publicou un ficheiro novo (cambio de URL/data/hash) e avisa ao administrador (encaixa co lector de novidades).
5. Capa galega por riba: nome galego, variedades locais, orde de busca galega — en táboas propias, sen tocar os códigos oficiais.

### 8octies. Deseño visual — textos visibles (tarefa 022)

- **Tarefa 022 (textos visibles horta→explotación)**: **feita** o 2026-10-23 polo modelo local.
  - Todos os textos visibles entre comiñas que mencionaban "horta" foron cambiados a "explotación" nos 5 ficheiros indicados.
  - Nomes de variables, funcións e enderezos (`horta_id`, `Horta`, `/hortas/...`) non se tocaron.
  - Comprobacións: ruff/mypy/pytest pasaron (244 tests).
  - Commit `smoth/022-textos-horta-a-explotacion`.

## 8nonies. App do móbil para o campo (investigación do 2026-10-28)

**Por que:** a app actual (NiceGUI) precisa conexión continua co servidor; no campo moitas veces non hai cobertura. As apps do sector (Agroptima, SKYFLD, CropSights) traballan sen conexión e sincronizan despois.

**Decisión (usuario, 2026-10-28):** app web instalable (**PWA**) só para o campo, que garda no móbil e envía á app grande ao volver a cobertura. Sen tendas nin custos, Android e iPhone. A app nativa só se a PWA queda curta (a tenda de Apple custa ~99 €/ano; dúas apps que manter). Precisa a API da app grande (README §19).

**Que pode facer un navegador no móbil (2026):** cámara, GPS, micrófono e gardar datos no propio móbil, en Android e iPhone. Avisos (*push*) no iPhone só se a PWA está instalada na pantalla de inicio. No iPhone **non** hai sincronización en segundo plano, Bluetooth nin NFC (envíase ao abrila); en Android Chrome si.

**Funcionalidades posibles (todas saen de traballos que xa ten a app ou do plan):**
- Apuntar traballos e facer as tarefas do día sen cobertura.
- **Fotos con data e lugar** de cultivos, pragas, animais e colleitas, ligadas ao traballo (evidencias do xemelgo; seguimento dun cultivo).
- **Parcela automática polo GPS**: propón a parcela onde está a persoa.
- **Identificar plantas e malas herbas cunha foto** (Pl@ntNet: de balde ata 500 consultas/día, citando Pl@ntNet). Axuda a encher «problema: mala herba» do tratamento. Para **enfermidades** non hai servizo de balde (Plantix é de pago e sen prezos públicos): non se propón.
- **Ditar en galego** en vez de escribir (recoñecedor de voz do Proxecto Nós, libre, con API; o teclado do móbil tamén dita).
- **Ler QR e códigos de barras** coa cámara: o QR dun lote (xemelgo), a etiqueta dun produto.
- **Foto da factura ou receita** como proba de compra (medicamentos veterinarios, fitosanitarios).
- **Avisos**: tarefas do día, tempo de espera, avisos de AEMET.
- **Crotais electrónicos** de ovellas e cabras: o NFC do móbil non os le (134,2 kHz); fai falta un lector externo por Bluetooth, e no iPhone a PWA non pode usalo. Para máis adiante.
- **PAC**: as fotos xeorreferenciadas oficiais vanse pola app do FEGA (SgaFot); horta non a substitúe, pero as súas fotos quedan como proba propia.

Fontes: Pl@ntNet API (my.plantnet.org/terms_of_use), Plantix Vision API (plantix.net/en/business), FOGGA manual SgaFot, Xunta (Proxecto Nós), fichas de xFarm e Agroptima, guías PWA 2026 (magicbell.com).

## 8decies. Meteoroloxía: onde están as leiras e que estación usar (investigación do 2026-10-28)

**Pedido do usuario (2026-10-28):** buscar onde están as leiras e configurar as estacións máis próximas, ou facelo por concellos; analizar como o fan outros.

**Fontes (decisión do usuario: MeteoGalicia e AEMET):**
- **MeteoGalicia**, servizos web abertos en JSON:
  - lista de estacións activas con identificador (`servizos.meteogalicia.gal/mgrss/observacion/listaEstacionsMeteo.action`);
  - datos de cada estación: ao momento, últimos 10 minutos, diarios e mensuais;
  - **predición por concello**, co código do concello (lista oficial en PDF «JSON_Pred_Concello»).
  - Hai que confirmar na documentación oficial se MeteoSIX pide clave.
- **AEMET OpenData** (clave gratuíta):
  - **predición por municipio**, co código INE de 5 cifras; é a da capital do concello, non de cada leira;
  - observación por estación, co seu identificador;
  - **avisos** por zona de aviso, en CAP (XML comprimido).
  - As chamadas van en dous pasos e os textos en ISO-8859-1.

**Como o fan outros:**
- xFarm: o tempo de cada leira; enche só o tempo real en cada traballo apuntado; a predición por leira é de pago.
- METOS/Lindsay: predición para cada leira sen estación propia.
- Farmers Edge: estación propia cada ~1.000 ha.
- As guías de extensión agraria din que, para decisións locais, a estación debe estar a menos de ~10 km. A ~25 km xa dá outra humidade. En Galicia tamén conta moito a altitude.

**Proposta para o paso 8:**
1. **Onde está cada leira:** coas coordenadas da parcela (xa as ten), co punto do mapa ou do GPS do móbil, ou, se non as ten, coas da explotación.
2. **Concello:** tirado da parcela (código SIGPAC; hai que confirmar a correspondencia co código INE) ou das coordenadas → **predición** de MeteoGalicia e AEMET para ese concello e **zona de aviso** de AEMET.
3. **Estación de medida:** a app propón a **estación de MeteoGalicia máis próxima** (distancia e altitude) a cada parcela, e permite cambiala a man. Se está lonxe (máis de ~10 km) ou a moita diferenza de altitude, avisa.
4. **Nos traballos:** ao apuntar un tratamento, gárdase o tempo real dese día da estación da parcela (vento, choiva). O xemelgo e o CUE usan ese dato gardado, non unha consulta nova.
5. Sen servizos nin programadores neste ordenador: consulta ao momento e garda o que se usa.

Fontes: pypi.org/project/meteoGalicia-api; meteo-estaticos.xunta.gal JSON_estado_actual_es.pdf; CRAN meteospain (MeteoGalicia); exemplos da API AEMET (rdrr.io meteoForecast; aemet-mcp); xfarm.ag/en/environment-and-climate; extension.arizona.edu (AZ2135); lindsay.com (METOS).

## 8undecies. Apps de horta e ferramentas de plan de empresa (investigación do 2026-10-29)

Detalle e fontes: `docs/analise-apps-horta-e-plans-empresa-2026-10-29.md` (só co buscador; varias páxinas oficiais quedan por verificar).

- Apps de horta comercial pequena (Tend, Farmbrite, Qrop/Brinjel) **planifican primeiro**: o plan de cultivos xera tarefas, sementes a mercar, colleita e ingresos previstos. As españolas rexistran o feito e sacan o caderno, como horta. LiteFarm (libre) dá beneficio por cultivo e acceso ao inspector de ecolóxico.
- Ferramentas de plan de empresa (Ministerio/ENISA, IGAPE, AgPlan, LivePlan, Enloop): **ningunha enche un formulario oficial de axuda nin usa os datos reais da explotación**. Ideas útiles: escenarios, ratios con puntuación, revisor dentro da ferramenta, plan fronte ao real.
- Nova fonte de comparación: **ECREA** (MAPA), custos e resultados **por cultivo ou actividade**, complemento da RECAN.
- Propostas para decidir: plan de cultivos antes do módulo de plan de empresa; plan fronte ao real (seguimento de MR404A e AGADER); escenarios; acceso de lectura limitado para técnico/GDR/banco.

## 8duodecies. Comprobacións legais (2026-10-29, co buscador)

- **Identificación dos animais: RD 787/2023** (modificado polo RD 1307/2024), sobre o Reg. (UE) 2016/429 e o Reg. Delegado 2019/2035. Identificación na explotación de nacemento e sempre antes de saír dela (art. 16). **Vacún:** individual, agora tamén electrónica. **Ovino e caprino:** individual; os que van ao matadoiro antes dos 12 meses poden levar crotal convencional co código da explotación. **Porcino:** marca (crotal ou tatuaxe) da explotación de nacemento. **Aves:** precinto ao saír da explotación. **Coellos (lepóridos):** dentro do RD, método por confirmar no texto consolidado.
- **Ovos:** Reg. Delegado (UE) 2023/2465 aplícase desde o 28/11/2023 e substitúe o 589/2008; quita a data de consumo preferente obrigatoria. O límite de 28 días desde a posta para vender ao consumidor está no Reg. 853/2004 (Reg. Delegado 2022/2258).
- **Reg. 931/2011** (orixe animal): descrición, cantidade, operador de orixe e destino (e propietario se é outro), lote; aplícase desde o 1/7/2012. A data de expedición, por confirmar no art. 3.
- **AGADER Anexo V, partida 4:** segue sen confirmar (o buscador non dá o anexo; hai que lelo no DOG).

Fontes: boe.es/eli/es/rd/2023/10/17/787 · boe.es BOE-A-2024-26927 · mapa.gob.es (trazabilidade ovino-caprino e outras especies) · agrinfo.eu (normas dos ovos) · boe.gob.es/doue/2023/2465 · aesan.gob.es (trazabilidade).

## 9. Fontes

- DOG nº 21, 2/2/2026 — Leader MR701L (bases, anexos III e V): https://www.xunta.gal/dog/Publicados/2026/20260202/AnuncioO90-020126-0004_gl.html
- DOG nº 157, 20/8/2026 — modificación: https://www.xunta.gal/dog/Publicados/2026/20260820/AnuncioO90-140826-0001_gl.html
- DOG 10/5/2023 — marco Leader 2023-2027: https://www.xunta.gal/dog/Publicados/2023/20230510/AnuncioO90-280423-0001_gl.html
- DOG 9/3/2026 — MR404A/MR405F: https://www.xunta.gal/dog/Publicados/2026/20260309/AnuncioG0426-260226-0003_es.html
- Exemplo de baremo GDR (só como exemplo de formato): https://gdrsalnesullaumia.com/wp-content/uploads/2025/09/NORMAS-DE-XESTION-E-BAREMOS-FINAL.pdf
- CKAN MAPA: https://servicio.mapa.gob.es/ckan/
- SIGPAC: https://sigpac-hubcloud.es/ · https://sigpac-hubcloud.es/ogcapi?f=html
- SAECA (nota MAPA): https://www.mapa.gob.es/es/prensa/ultimas-noticias/detalle_noticias/bego-a-garc-a-bernal---las-mujeres-rurales-convierten-el-talento-individual-en-oportunidades-colectivas-/d53dbd49-1e45-4393-89a5-02a37a9cfada
- EIT Food Accelerator Network 2026: https://www.eit.europa.eu/our-activities/opportunities/eit-food-accelerator-network-2026
- GS1 EPCIS: https://www.gs1.org/epcis

## Accións futuras acordadas (2026-10-23)

Decididas co usuario para facer máis adiante (agora a prioridade son as funcionalidades en curso):

1. **Datos persoais (RGPD)**: revisar antes de usar con datos reais os campos de colectivo do Equipo (discapacidade = dato de saúde, categoría especial; xénero, data de nacemento). Proposta: gardar só totais no plan de empresa ou con consentimento explícito.
2. **Copias de seguridade e aloxamento**: servidor, PostgreSQL (revisar migracións con `lastrowid`), copias diarias automáticas, conservación ≥ 3 anos.
3. **Seguridade antes de abrila a usuarios reais**: HTTPS, rexistro e recuperación de contrasinal cunha solución madura, límite de intentos, rexistro de actividade (quen cambiou que).
4. **Probas automáticas de pantallas** (escritorio e móbil) para as seccións principais.
5. **Pasar a rama `deseno-visual` a master** ao rematar a cola actual e a revisión da app.
6. **Idioma**: a base é sempre o galego (deseño, textos, vocabulario); o castelán será unha opción de tradución. Preparar a app para traducións sen cambiar a base.
7. Limpeza de código morto despois de cada cola (ver memoria).

# Análise de aplicacións de horta e de plans de empresa (2026-10-29)

Que fan outras aplicacións de xestión de hortas e as ferramentas de plan de empresa, e que lle serve a horta. Complementa o xa analizado en `docs/estado-e-evolucion.md` §8bis–8ter (oSIGris, xFarm, Agroptima, FieldPad, farmOS) e `docs/como-e-a-app.md` §6 (Agricolum), que aquí non se repiten.

**Como se fixo:** só co buscador web; desde esta sesión non se puideron abrir as páxinas das apps nin as oficiais (ipyme.org, igape, xunta.gal, tend.com...). Os datos saen dos resumos do buscador, dos repositorios públicos e de comparadores (Capterra, GetApp). Os prezos e as funcións que só dá un comparador márcanse **(sen confirmar)**. Nada se copia: só se anotan ideas de funcionalidade.

## 1. Aplicacións de xestión de horta

### 1.1 Que hai

| App | Que é | Prezo | O que fai ben | Que lle falta para unha explotación galega |
|---|---|---|---|---|
| **Tend** (EUA) | Horta comercial pequena: *o plan manda* — o plan de cultivos xera o calendario de produción e este alimenta as canles de venda | dende 39 $/mes (sen confirmar) | Biblioteca de cultivos con modelos (marco, días ata colleita, rendemento); tarefas recorrentes (rega, abonado, pragas); mapa de leiras e camas | Nada do caderno español, SIEX nin fitosanitarios do MAPA; en inglés |
| **Farmbrite** (EUA) | Horta + gando + almacén + contabilidade + vendas nun só sitio | 29 $/mes cultivos ou gando, 59 $/mes todo; só contabilidade 119 $/ano (Capterra 2026, sen confirmar) | Plan de cultivos coas xanelas de sementeira, crecemento e colleita; **sucesións repetidas** ao colleitar; **previsión de colleita e de ingresos**; vista do que haberá dispoñible para vender; apunta sen conexión; contabilidade con P&G, orzamento e tesourería | Contabilidade de EUA (Schedule F); sen normativa europea |
| **LiteFarm** (Univ. British Columbia, libre GPLv3) | Xestión para pequenas explotacións sostibles | gratuíta | Vendas e gastos con **beneficio por cultivo ao momento**; comparar prezos por data e lugar; **documentación ecolóxica cun clic** e **convidar ao inspector** á explotación; quendas de traballo; informe de fin de tempada | Sen caderno español; sen plan de empresa |
| **Qrop** e **Brinjel** (Francia, con L'Atelier Paysan; libres, Brinjel AGPL-3.0 tamén de pago) | Planificación para hortelás de venda (*maraîchage*) | Qrop gratuíta (alfa); Brinjel por subscrición ou instalado no propio servidor | Plan por camas (lonxitude, marco, rendemento esperado) → **xera as tarefas de sementeira e transplante, a semente necesaria e as bandexas**; **lista de sementes e plantas a mercar**; mapa onde se arrastran as plantacións; **historial de cada cama para a rotación**; custo da man de obra por tarefa | Sen caderno, fitosanitarios nin custos completos |
| **Agrivi** (Croacia) | Xestión para explotacións medianas e grandes, cooperativas e agroindustria | baixo pedido, sen versión gratuíta | Facturas de compra e venda, préstamos e activos; tesourería; **rendibilidade por leira, cultivo e explotación**; orzamento; comparar leiras, tempadas e prácticas | Caro e pensado para máis tamaño; contabilidade incompleta segundo as revisións |
| iCultor, Planifica tu Huerto, Garden Planner, farming.software | Planificadores de horta doméstica ou de permacultura | gratuítos ou baratos | Calendario de sementeira e colleita, asociacións boas e malas, avisos antes das xeadas | Non son de xestión profesional |

En España as apps profesionais (Agroptima, Isagri, Agricolum, ERP agrícolas) céntranse no caderno e na trazabilidade para certificación. **Non se atopou ningunha que xunte planificación de sucesións, venda directa en cestas e caderno oficial.**

### 1.2 O que se repite

1. **Dúas familias.** As españolas *rexistran o feito* e sacan o caderno (é o que fai horta hoxe). As de horta comercial pequena (Tend, Qrop, Farmbrite) *planifican primeiro*: o plan de cultivos xera as tarefas, a semente que mercar, a colleita prevista e o que haberá para vender.
2. **O plan de cultivos é o que une a horta e os cartos.** Rendemento esperado × superficie × prezo = ingresos previstos; o mesmo dato que pide a conta a 5 anos dun plan de empresa.
3. **Custo e beneficio por cultivo** (LiteFarm, Agrivi, Agroptima, Farmbrite) a partir das horas, entradas e vendas.
4. **Historial por cama ou leira** para a rotación (Qrop, Brinjel).
5. **Acceso para quen revisa** (inspector de ecolóxico en LiteFarm).

### 1.3 Onde está horta

| Idea | En horta hoxe |
|---|---|
| Rexistrar o feito e sacar o caderno | **Feito**, e máis completo ca as estranxeiras (caderno da Xunta, CUE, fitosanitarios do MAPA, catálogos do FEGA) |
| Tarefas planificadas que, ao facelas, quedan apuntadas | **Feito** (tarefas 076: «Facela agora») |
| Lotes e vendas | **Feito** (paso 4) |
| Horas por traballo e quen o fixo | **Feito** (tarefas 075) |
| Plan de cultivos con sucesións, colleita prevista e sementes a mercar | **Falta** |
| Custo e beneficio por cultivo | **Falta** (paso 10 «Cartos» e módulo de plan de empresa) |
| Historial de rotación por leira | **Falta** (rotación é fase posterior no README) |
| Acceso para un inspector ou técnico | **Case:** existe o rol `lector` na horta; falta limitar o que ve (só caderno, só plan) |

## 2. Ferramentas de plan de empresa

### 2.1 Que hai

| Ferramenta | Quen | Prezo e lingua | Como funciona | Que serve para horta |
|---|---|---|---|---|
| **Plan de Empresa** (planempresa.ipyme.org) | Ministerio (DGEIPYME) con ENISA | gratuíta, castelán, con rexistro | Seccións: datos básicos, promotores, produtos, produción, mercado, marketing, organización e persoal, investimentos; despois **escenarios económicos** (ingresos, gastos, investimentos, financiamento, balance, conta de resultados, tesourería), segundo o Plan Xeral de Contabilidade; varios escenarios por plan | Os **escenarios** (probar investimento, persoas, prezo de venda). Horizonte de anos sen confirmar |
| **Viable 2020 / simulador de viabilidade** | IGAPE | gratuíto, descarga (sen confirmar se segue vixente) | Plan económico e financeiro a **5 anos** para quen non sabe de finanzas | Mesmo horizonte ca o Anexo III de AGADER |
| **Folla de viabilidade** da submedida 6961.1 (Andalucía, mozos agricultores) | Xunta de Andalucía | gratuíta, folla de LibreOffice | Táboa de cálculo da viabilidade e hitos por fases do plan | Modelo do que pide unha liña de incorporación; en Galicia o equivalente é MR404A |
| **MR404A** (Galicia, persoas agricultoras mozas) | Consellería do Medio Rural | formulario da sede | Plan empresarial obrigatorio; manter a actividade **5 anos** desde o último pago; ser agricultor profesional en **18 meses**; titoría da Consellería. Orde do 26/2/2026, DOG nº 45 | O **seguimento** (previsto fronte ao real durante anos). Anexo do plan en 2026 sen confirmar (en 2023 era o IV) |
| **AgPlan** (Univ. de Minnesota) | Centro de xestión financeira agraria | gratuíta, inglés | Modelos por tipo (agrario de materias primas, **valor engadido** = transformación, transición a ecolóxico, pequena empresa, agroturismo); preguntas guía e exemplos en cada sección; **compartir co revisor** escollido e falar con el na ferramenta; folla aparte de balance, resultados e tesourería | Separar produtor e transformador; o fluxo co técnico ou co GDR |
| **LivePlan** | Palo Alto Software | ~12–20 $/mes | Fórmulas incorporadas; **trae os datos reais da contabilidade** (QuickBooks, Xero) para comparar | A idea de **plan fronte ao real**, que horta pode facer cos seus propios datos |
| **Enloop** | — | de pago | Estados financeiros automáticos, **16 ratios** e unha **puntuación** do plan; texto escrito automaticamente | Ratios e puntuación; o texto automático non (decisión: sen IA) |
| **ProjectionHub** | — | baixo pedido | Proxeccións financeiras sen saber de follas de cálculo | Pouca información |
| **ECREA** (MAPA) | Ministerio | gratuíto, informe interactivo | **Custos e resultados por cultivo ou actividade gandeira**, evolución e territorio; microdatos anónimos baixo petición. Avance 2025 a finais de 2026 | Referencia **por cultivo** para comparar o plan; complementa a RECAN (que é por explotación, OTE e tamaño) |
| AXE 360 | — | — | Xa auditado (`estado-e-evolucion.md` §3.4): non segue o Anexo III nin o V | Memoria complementaria |

### 2.2 O que se repite

1. **Ningunha ferramenta enche un formulario oficial de axuda.** Nin a do Ministerio, nin a do IGAPE, nin as comerciais xeran o Anexo III/V de AGADER nin o plan de MR404A: dan un plan xeral e a persoa pásao á man. É o oco que xa viu `estado-e-evolucion.md` §3, agora confirmado tamén fóra de Galicia.
2. **Todas parten de cero.** A persoa escribe as cifras. Só LivePlan (contabilidade) e as apps de granxa (Farmbrite, Agrivi: orzamento) usan datos reais. **Ningunha xunta caderno da explotación e plan de empresa.**
3. **Escenarios** (Ministerio) e **ratios con puntuación** (Enloop) para ver se o plan se sostén.
4. **Revisor dentro da ferramenta** (AgPlan): o técnico de emprego, o GDR ou o banco len e comentan.
5. **Seguimento despois da axuda**: as liñas de incorporación esixen anos de compromiso, pero as ferramentas acaban no documento.

## 3. Conclusións para horta

**O diferencial confírmase:** ningunha app consultada xunta (1) caderno oficial español e SIEX, (2) plan de cultivos e custos, e (3) plan de empresa no formato das axudas galegas, cos datos reais da propia explotación. Cada peza existe por separado; xuntas, non.

Propostas, por orde. **Son ideas para decidir, non traballo para facer agora** (CLAUDE.md: non adiantar fases sen que se pida):

1. **Plan de cultivos** (familia Tend/Qrop): cultivo, leira, superficie ou camas, datas previstas e rendemento esperado. Encaixa co que xa hai: o planificado son tarefas pendentes e o feito son traballos. Del saen a colleita prevista, as sementes a mercar e os **ingresos previstos do plan de empresa**.
2. **Plan fronte ao real** no módulo de plan de empresa: cada ano, o previsto na conta a 5 anos ao lado do real (vendas, entradas, horas). Serve para o seguimento de MR404A e AGADER, e ningunha ferramenta o fai cos datos da explotación.
3. **Escenarios** (base, malo, bo) sobre o mesmo plan, cambiando prezos, rendementos e investimento.
4. **Ratios e control de completitude** xunto ao VAN/TIR/pay-back xa previstos: o que lle falta ao plan para presentalo e se os números se sosteñen, igual que Informes avisa do que lle falta ao caderno.
5. **Comparar con ECREA (por cultivo) e RECAN (por explotación)**: «o teu custo por hectárea de pataca fronte á media». ECREA é nova para nós; mirar se ten Galicia e acceso aberto.
6. **Acceso de lectura limitado** para técnico, GDR, banco ou inspector de ecolóxico, reutilizando o rol `lector`, limitado ao plan ou ao caderno.
7. **Historial de rotación por leira**, cando toque a fase de rotación.

Non se copia: o texto escrito por IA (Enloop) nin a contabilidade fiscal completa (Farmbrite, Agrivi): horta leva os gastos e ingresos que o plan e o caderno precisan e non substitúe a asesoría.

## 4. Para decidir (usuario)

1. ¿Engadimos o **plan de cultivos** antes do módulo de plan de empresa, para que este teña ingresos previstos de onde saír?
2. ¿O **plan fronte ao real** forma parte do primeiro módulo de plan de empresa ou vai despois?
3. ¿Ábrese acceso a persoas de fóra (técnico, GDR, banco) ou de momento só membros da horta?

## 5. Pendente de verificar (as páxinas non se puideron abrir)

- Plan de Empresa do Ministerio: anos que proxecta e se segue activo (manual: planempresa.ipyme.org/Content/docs/GuiaManualPdE.pdf).
- IGAPE: nome e descarga actual do simulador de viabilidade.
- MR404A 2026: anexo e contido do plan empresarial na Orde do 26/2/2026 (DOG nº 45, 9/3/2026).
- ECREA: se dá datos de Galicia e por cultivos hortícolas.
- Prezos de Tend, Farmbrite e Brinjel na web de cada un.

## 6. Fontes

Apps de horta:
- https://tend.com/solutions/crop-management-software · https://tend.com/page/how-it-works.html
- https://farmbrite.com/crop-management-software · https://help.farmbrite.com/help/planning · https://www.capterra.com/p/136765/Farmbrite/pricing/
- https://ubcfarm.ubc.ca/litefarm/ · https://youngagrarians.org/resources/guides-toolkits/software-tools-for-small-farms/ · https://github.com/GOATech/LiteFarm
- https://github.com/andreh11/qrop · https://wiki.p2pfoundation.net/Crop_Planning_Software
- https://www2.agrivi.com/blog/finance-management-with-agrivi-software · https://softwareconnect.com/reviews/agrivi-360-fms/
- https://www.softwaredoit.es/software-sector-primario/software-agricultores.html · https://farming.software/es/inicio/ · https://icultor.com/

Plans de empresa:
- https://planempresa.ipyme.org/ · https://planempresa.ipyme.org/Content/docs/EjemploPlan.pdf · https://femz.es/desarrolla-tu-plan-de-empresa-con-dgipyme/
- https://emprendedores.es/gestion/crear-una-empresa/herramientas-sumulador-para-tu-plan-economico (Viable 2020, IGAPE)
- https://www.juntadeandalucia.es/organismos/agriculturapescaaguaydesarrollorural/areas/infraestructuras-agrarias/modernizacion/paginas/establecimiento-jovenes-agricultores-2024-2027.html
- https://sede.xunta.gal/detalle-procedemento?codtram=MR404A · https://www.xunta.gal/dog/Publicados/2026/20260309/AnuncioG0426-260226-0003_gl.html
- https://agrisk.umn.edu/Library/Record/agplan1 · https://extension.okstate.edu/programs/farm-management-and-finance/e-farm-management-training/developing-a-farm-business-plan/site-files/docs/using-the-online-ag-business-planning-tool-agplan.pdf
- https://upmetrics.co/compare/liveplan-vs-enloop · https://startupsavant.com/enloop-vs-liveplan · https://www.getapp.sg/compare/20501/91056/liveplan/vs/projectionhub
- https://www.mapa.gob.es/es/ministerio/servicios/analisis-y-prospectiva/financiacion-fiscalidad-costes-energia/ecrea (ECREA)

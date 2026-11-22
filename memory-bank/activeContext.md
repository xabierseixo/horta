# Estado actual do proxecto

Mantéñeo Claude (ver `AGENTS.md`). Os modelos locais só o len; o que fan anótano no apartado **Resultado** de cada tarefa.

## Obxectivo

App única **horta** para produtores primarios e/ou transformadores de toda Galicia: xestión da explotación, caderno de explotación oficial (modelo da Xunta e CUE do SIEX), plan de empresa conforme a AGADER, fitosanitarios do MAPA e trazabilidade verificable. Detalle: `docs/estado-e-evolucion.md`.

## Estado verificado (2026-10-27)

Forma da app: `docs/como-e-a-app.md` (recursos, traballos, informes; ler antes de deseñar).

- Rama de traballo `deseno-visual`; `master` actualizada con ela o 2026-10-25 (sen remoto: só no ordenador).
- Comprobacións: `uv run pytest -q` → 437 passed; `ruff` e `mypy` sen erros.
- Caderno de explotación completo: todos os campos do modelo oficial da Xunta (follas 1–8), exportable a Excel para calquera período (tarefas 055–066d).
- Fertilización, rega, plan de abonado e análises (tarefas 046–053e).
- Tratamentos completos (tarefas 070–071e, deseño `docs/superpowers/specs/2026-10-25-tratamentos-completos-design.md`):
  - rexistro de fitosanitarios do MAPA dentro de horta (`horta-catalogos fitosanitarios DIR`), con pontes aos códigos SIEX;
  - buscador de produtos e enchido automático do nº de rexistro e materia activa;
  - avisos (non bloqueos): uso non autorizado no cultivo ou contra o problema, dose máxima, nº de aplicacións, produto só profesional, cancelado ou caducado;
  - prazo de seguridade na lista («Non colleitar antes do») e aviso ao apuntar unha colleita;
  - diálogo con varios cultivos, problemas, xustificacións, produtos e medidas non químicas, e asesor; edítase calquera tratamento.

- Catálogos oficiais (tarefas 072–072j, deseño `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`):
  - os 39 catálogos do FEGA que usa a app van en `src/horta/data/catalogos_fega/`; a app impórtaos soa se a BD non ten;
  - importación segura: comprobación de columnas, revisión sen gardar e aviso se un ficheiro daría de baixa moitos códigos;
  - Administración → Catálogos oficiais: estado, portal do FEGA (captcha: descarga unha persoa), subida revisada de .xlsx ou .zip; aviso no Resumo aos 60 días;
  - rexistro de fitosanitarios do MAPA automático dentro da app (ao arrancar e cada 6 h, descarga se pasaron 7 días; `HORTA_ACTUALIZAR=0` desactívao; `horta-catalogos fitosanitarios --descargar` para despregar).
- Labores culturais (CUE bloque 5, tarefas 073–073e, deseño `docs/superpowers/specs/2026-10-25-labores-culturais-design.md`): táboa Labores (desde o Diario); folla «9 Labores (CUE)» no caderno descargable.
- Diario de traballos (tarefas 074–074q, deseño `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`):
  - menú Inicio, Diario, Informes e grupo Explotación; as táboas de cada tipo de traballo ábrense desde o Diario;
  - «Apuntar traballo» (que fixeches → formulario dese tipo), tamén no Inicio; no móbil, botón sempre á vista;
  - apuntar só obriga ao mínimo (rega: cultivo e data; labor: + tipo; abonado: + abono; colleita: + cantidade, lote automático); Informes avisa do que lle falta ao caderno (só profesionais) e nunca bloquea.
- Quen e horas (tarefas 075–075v, deseño `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`):
  - todo traballo leva quen o fixo (rega, labor, abonado salvo empresa de servizos, colleita, toma de mostras, tratamento en instalacións; sementeira cando xa pasou); horas opcionais;
  - o formulario propón quen fixo o último traballo; Diario con filtro «Quen»; Informes conta os traballos de antes sen quen.
- Tarefas = traballos por facer (tarefas 076–076p, deseño `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`):
  - a tarefa leva o tipo de traballo e quen o vai facer; «Facela agora» (Diario ou Tarefas) abre o formulario dese tipo xa enchido e, ao gardar, queda feita e ligada ao traballo (o Diario non a repite);
  - sen tipo («outro traballo»): quen a fixo (obrigatorio), data e horas.
- Coidado e saúde dos animais (tarefas 077–077j, deseño `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`): táboa `coidado_animal` (coidado, enfermidade, cambio na produción, medicamento con tempo de espera obrigatorio, visita) por grupo de animais; aviso de tempo de espera en Animais; a tarefa pode referirse a un grupo; un grupo con coidados non se borra. 447 probas.
- Entradas e saídas de animais (tarefas 078–078j, deseño `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`): táboa `movemento_animal`; a cantidade, baixa e estado do grupo saen dos movementos; especie oficial (`especie_codigo`) e razas oficiais; pantalla de Animais en `ui/pages/animais.py`. 455 probas (un fallo intermitente sen reproducir o 2026-10-28, 8 repeticións limpas).
- Meteoroloxía: o usuario decidiu (2026-10-28) usar **MeteoGalicia e AEMET** (non Open-Meteo). AEMET precisa clave que pide o usuario.
- BD de proba en `~/.local/share/horta/horta.db`; configuración en `~/.config/horta/entorno` (HORTA_DATABASE_URL, HORTA_STORAGE_SECRET).

- Produción dos animais (tarefas 079–079j, deseño `docs/superpowers/specs/2026-10-28-producion-animais-design.md`): táboa `producion_animal` (produto da especie, cantidade, retirado, lote compartido coas colleitas vía `producions_animais.lotes_da_horta`); aviso de tempo de espera; botón «Produción» en Animais. 470 probas. Primeiro lote coas dúas colas á vez (88 e 66): o 66 non arrancou (GPU do .66 sen memoria, 2026-10-28) e as súas tarefas completáronse coa versión esperada; o 88 moveu `sync/claude` (`git update-ref`), e o orquestador volve poñelo no HEAD antes de cada tarefa.
- Pastoreo (tarefas 080–080j, deseño `docs/superpowers/specs/2026-10-28-pastoreo-design.md`, CUE 12): táboas `pastoreo`, `pastoreo_leira`, `pastoreo_animal` (propios → animal; terceiros con REGA e especie); `data_fin` baleira = aínda no pasto («Saíron do pasto»); número ≤ animais do grupo ese día, sumando os pastoreos que coinciden; aviso de prazo de seguridade (`pastoreos.aviso_prazo_pastoreo`). 487 probas. O 66 volveu fallar pola GPU sen memoria; o 88 integrou 080, 080a, 080e, 080j e 080i ao seu xeito igual ao esperado.
- **Deseño global** (`docs/superpowers/specs/2026-10-28-deseno-global-design.md`, aprobado «Codifica»; revisión en `docs/revision-definicion-2026-10-28.md`): a app como un todo, seis preguntas (quen, onde, entra, faise, sae, cartos) e o tempo como contexto (§7bis).
  - Paso 2, parte común (tarefas 081–081h): `models/traballo.py` (ParteComun, FeitoPor, ConMaquina); `abonado.aplicador_persoa_id` → `persoa_id`; `tratamento_fito.observacions` → `notas`; `cultivo.estado` desaparece (`cultivos.estado_cultivo`). 509 probas.
  - Paso 3, persoas e entidades (tarefas 082–082j, `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md`): `persoa_papel`; Persoas (Equipo/Contactos); `ui/campo_persoa.py`; os textos de xente de fóra pásanse con `horta/migracion_persoas.py`. 521 probas.
  - Paso 4, lotes e saídas (tarefas 083–083d, `docs/superpowers/specs/2026-10-28-lotes-e-saidas-design.md`): `lote`, `lote_saida`, `services/lotes.py`, pantalla Lotes. O retirado da produción non entra no lote. 538 probas.
  - Paso 5, varias leiras (tarefas 084–084d, `docs/superpowers/specs/2026-10-28-varias-leiras-design.md`): `labor_cultivo`, `rega_cultivo`, `abonado_cultivo`; `services/leiras.py`; colleita en varias leiras (`colleitas.crear_colleitas`).
  - CUE: o caderno público da Xunta (XEAGA) non importa ficheiros; o envío automático require ser CUE comercial (MR407B/C/D). Pendente de decisión do usuario.

  - Paso 10, cartos (`docs/superpowers/specs/2026-10-29-cartos-design.md`): `apunte_cartos`; `data_pago` en `lote_saida`, `entrada_produto` e `movemento_animal` (+ `importe`); `custo_hora` en `persoa` e `maquina`; `services/cartos.py` (pendentes, custo dos traballos, resumo do ano); pantalla Cartos (`ui/pages/cartos.py`, `ui/campo_pago.py`). Migración `b1f3d5e7a9c2`: o que xa tiña prezo queda cobrado/pagado na súa data. 590 probas. Probado no navegador.

  - Paso 10bis: resumo de Cartos por semana, mes, trimestre ou ano (`cartos.periodo`, `resumo_periodo`).
  - Paso 11a, fotos: `models/foto.py`, `services/fotos.py`, `ui/fotos.py`, ruta `/fotos/{id}` en `main.py`; migración `c2a4e6b8d0f1`. Diario, Parcelas, Animais e Lotes. Probado no navegador.

  - Paso 12, historial e rotación: `services/historial.py` (`por_referencia`, `rotacion`, `aviso_rotacion`), `ui/historial.py`; `equipo.historial` usa o xenérico. 609 probas.

  - Paso 13, calendario e mapa: `ui/pages/calendario.py` (Calendario no menú tras Diario; Mapa en Produción). 609 probas.

  - Paso 14: `services/libros_gandeiros.py`, `services/instalacions.py`, `ui/pages/instalacions.py`, `ui/identificados.py`; migración `e4c6a8b0d2f3`. 612 probas.

  - Paso 15, estatísticas: `services/estatisticas.py`, `ui/pages/estatisticas.py`. 613 probas.

  - Paso 16, plan de empresa: `models/plan_empresa.py`, `services/plan_empresa.py`, `ui/pages/plan_empresa.py`; migración `0d3b48bb5d29`. 617 probas. Fóra: plan de cultivos, MR404A, marxe por cultivo, RECAN/ECREA.

  - Paso 17: transformación (`services/clasificacions.py`, `dialogo_transformacion`) e páxina pública do lote (`services/trazabilidade.py`, `ui/pages/lote_publico.py`, excepción en `AuthMiddleware`); migración `23edab3c731f`. 619 probas. Pendente: QR, selado, EPCIS.

  - Peches: QR (`segno`), rotación por familia, debuxo das parcelas no Mapa; comprobacións legais en `estado-e-evolucion.md` §8duodecies. 621 probas.
  - Mapa: capas oficiais e recinto SIGPAC/Catastro (`services/xeo_oficial.py`); zonas da parcela (`models/zona.py`, `services/zonas.py`, `cultivo.zona_id`), migración `ee20f21b4ca4`. 626 probas. Pendente de probar no ordenador do usuario: SIGPAC e Catastro reais.

## Pendente

- Mapa (2026-10-29): capas PNOA/SIGPAC/Catastro servidas pola caché `services/teselas.py` (ruta `/teselas/...`, botón «Gardar a zona para usar sen conexión»); capa SIGPAC correcta `AU.Sigpac:recinto`. Pendente: o usuario comproba no seu ordenador as descargas de recinto e Catastro (dixo que non baixan ben; agardando o erro exacto).

- Aprazados (2026-10-29): selado do xemelgo, MR404A, RECAN/ECREA, marxe por cultivo, lista de «máis adiante»; e polo usuario: 9c AEMET, 11b app do móbil, 18 VERI*FACTU, CUE comercial, tratamentos sen xustificación.

- Lotes feitos (`docs/analise-lotes-2026-10-29.md` §6): `produto_venda`, `clasificacion`(+`_clase`), `mestura`(+`_orixe`), `lote_saida.clase`; `lote.categoria_venda_directa` pasa á ficha (migración `d3b5f7a9c1e2`). Servizos `lotes.py` (ficha_para, codigo_por_agrupacion, queda_por_clase) e `clasificacions.py`; UI `ui/pages/clasificacions.py`. 606 probas. Trazabilidade e simulacro de retirada: `services/trazabilidade.py`, botón en Lotes.

- Orde do deseño global completada ata o 17. Quedan: QR e selado do xemelgo, 18 (VERI*FACTU), 9c (AEMET, aprazado), 11b (app do móbil, decisión). 11b (app do móbil sen cobertura) precisa decisión do usuario. 9c (AEMET) aprazado polo usuario (2026-10-29), non urxente.
- Usuario: confirmar a folla de ruta revisada co plan orixinal (2026-10-28: produción animal, gastos e ingresos, fotos, CUE, meteoroloxía, calendario, mapa, rotación, estatísticas, transformación…).
- Usuario (2026-10-29): decidir as tres preguntas de `docs/analise-apps-horta-e-plans-empresa-2026-10-29.md` §4 (plan de cultivos antes do plan de empresa; plan fronte ao real; acceso de persoas de fóra). Verificar ao abrir as webs oficiais o §5 dese documento (ipyme, IGAPE, anexo MR404A 2026, ECREA).
- Usuario: decidir se os tratamentos dunha explotación profesional deben poder gardarse sen xustificación, aplicador ou co ROPO caducado (hoxe bloquean); e módulos separados ou todo nunha peza para plan de empresa e xemelgo.

- Usuario: revisar as propostas de textos en galego (`docs/propostas/`).
- Vía oficial para os catálogos do FEGA: alta MR470B na Xunta («punto de descarga» para cadernos comerciais) ou petición ao FEGA (cau-fega@fega.es). O portal do FEGA respondía 404 o 2026-10-25.
- Histórico de versións das etiquetas (períodos de graza): integrar os snapshots semanais de `../fitosanitarios`.
- Fases seguintes posibles: trazabilidade do lote, cuberta do solo (CUE 7) e pastoreo (CUE 12), envío ao CUE oficial vía XEAGA (trámite MR470B, require o usuario).
- Accións futuras acordadas (RGPD, copias, seguridade, probas de pantallas): `docs/estado-e-evolucion.md`.

# Tratamentos completos: rexistro do MAPA, comprobación do uso e formulario con varias filas (deseño)

Data: 2026-10-25 · Estado: **aprobado e feito** (tarefas 070–071e, 2026-10-25)

Decisión do usuario (2026-10-25): seguinte bloque = «Completar tratamentos».

Fontes:
- RD 1311/2012: Anexo III (rexistro de tratamentos) e art. 41 (usos autorizados na etiqueta).
- Descritor CUE v3.11.4, bloque `TratamFito`: varios cultivos, problemas, xustificacións, produtos e medidas por tratamento.
- Rexistro de produtos fitosanitarios do MAPA, JSON de regfiweb. O FEGA dío nas súas preguntas frecuentes: é a fonte oficial de produtos para os cadernos comerciais.
- Análise propia: `fitosanitarios/exploracion/ANALISE.md` §5 (o SIEX non comproba usos, cada caderno ten que facelo).
- Competencia: PlantCare, GPISoft e Agroptima comproban produto–cultivo–praga ao apuntar.

## O que hai e o que falta

O modelo e o servizo (`tratamento_fito`) xa admiten varias filas de todo, editar e o asesor. O formulario só ten unha fila de cada cousa. Non deixa editar nada que teña máis (`cabe_no_formulario`), e o produto escríbese a man sen ningunha comprobación.

| Falta | Por que importa |
|---|---|
| Escoller o produto do rexistro oficial | Evita erros no nº de rexistro (o CUE pídeo) e enche nome e materia activa |
| Avisar se o produto non está autorizado no cultivo e para a praga, ou se se pasa a dose | É o que mira unha inspección; o SIEX non o comproba |
| Prazo de seguridade → «non colleitar antes do…» | Seguridade alimentaria; enlaza coas colleitas (trazabilidade) |
| Varios produtos no mesmo caldo, varios problemas, medidas non químicas, asesor | Mesturas no tanque son habituais; GIP (medidas non químicas) e asesor pídeos o CUE |
| Editar calquera tratamento, tamén os migrados | Hoxe hai que dalo de baixa e repetilo |

## 1. Rexistro do MAPA dentro de horta

Táboas novas, versionadas con `catalogo_version` como os catálogos do FEGA. Impórtanse co comando `horta-catalogos fitosanitarios RUTA.json`, que le o JSON oficial do MAPA. A lóxica de normalización trasládase de `fitosanitarios/normalizar.py`, só cos campos que se usan. Así horta non depende do outro proxecto.

| Táboa | Campos |
|---|---|
| `fito_produto` | num_rexistro (clave), nome, titular, estado (Vigente/Cancelado), data_caducidade, data_cancelacion, data_limite_venda, version_id |
| `fito_materia` | num_rexistro, sustancia, concentracion, unidade |
| `fito_uso` | num_rexistro, codigo_cultivo, cultivo, codigo_agente, agente, tipo_usuario, sistema_cultivo, dose_min, dose_max, unidade_dose, ps_tipo, ps_dias, aplicacions_max, intervalo_min_dias, condicionamento |
| `fito_ponte_cultivo` | cultivo_siex_codigo → codigo_cultivo (MAPA), polo código EPPO |
| `fito_ponte_axente` | catálogo e código SIEX (enfermidade/praga/mala_herba/regulador) → codigo_agente (MAPA), polo nome científico |

As pontes calcúlanse ao importar, porque non hai táboa oficial de correspondencia. Cobertura medida o 2026-10-25:
- pragas: 608 de 709 axentes do MAPA;
- cultivos: 69 de 116 cultivos hortícolas do SIEX directamente por EPPO; máis ao contar as categorías superiores do MAPA (p.ex. «Hortalizas»), con `xerarquia.py`.

## 2. Escoller o produto

- No paso «Con que», un buscador por nome comercial ou nº de rexistro (entre os 2.080 produtos).
- Ao escoller un produto énchense o nº de rexistro, o nome e a materia activa (substancia e concentración). Pódense corrixir.
- Segue sendo posible escribilo a man, para produtos que non están no rexistro: substancias básicas, medios de defensa fitosanitaria e outros tipos do catálogo `tipo_produto`.
- Se o produto está cancelado ou caducado na data do tratamento, sae un aviso co día da cancelación e o límite de venda. O rexistro non publica o límite de uso, así que o texto di «comproba o prazo de uso».

## 3. Comprobación do uso: avisos, non bloqueos

Función de servizo `comprobar_tratamento(session, horta, datos) -> list[Aviso]`, con probas. Usa o cultivo (ponte + categorías superiores), os problemas (ponte + categorías superiores do axente) e cada produto. Mostra os avisos antes de gardar e na ficha do tratamento. Non se gardan.

| Caso | Aviso |
|---|---|
| Uso atopado | «Autorizado en Patata contra Mildiu: 0,38–1,25 %, prazo de seguridade 14 días, máx. 5 aplicacións» (informativo) |
| O produto non ten ningún uso no cultivo | «Este produto non está autorizado en Patata segundo o rexistro do MAPA» (forte) |
| Autorizado no cultivo pero non para o problema | «Autorizado en Patata, pero non atopamos o uso contra X», coa lista de problemas autorizados |
| Sen ponte para o cultivo ou o problema | «Non podemos comprobalo automaticamente: mira a etiqueta» |
| Explotación de autoconsumo e produto só para uso profesional | «Produto só para usuarios profesionais (carné ROPO)» |
| Dose por riba da máxima | só cando as unidades coinciden (l/ha, kg/ha). Con % ou ml/hl amósase a dose da etiqueta, sen comparar, porque faría falta o volume de caldo |
| Máis aplicacións ca o máximo | conta os tratamentos dese produto no mesmo cultivo |

**Por que non bloquea:**
- A etiqueta é a única referencia legal.
- As pontes non cobren todo.
- Cando cambia unha etiqueta hai 3 meses de graza para vender e 3 para usar a versión anterior, e o histórico de etiquetas aínda non o temos.

Bloquear deixaría sen poder apuntar tratamentos legais.

**Prazo de seguridade:** data do tratamento + ps_dias (o máis longo dos produtos usados). Amósase como «Non colleitar antes do dd/mm/aaaa»:
- na lista de tratamentos;
- ao apuntar unha colleita dese cultivo antes desa data, como aviso.

## 4. Formulario con varias filas

Mantense o diálogo en 5 pasos; cada lista leva «+ Engadir» e unha papeleira por fila.

1. **Que e onde:** un ou máis cultivos (mesma especie e variedade, outras parcelas), cada un coa súa superficie e estado fenolóxico.
2. **Por que:** un ou máis problemas; xustificacións con selección múltiple.
3. **Con que:** un ou máis produtos (buscador §2) e medidas non químicas: tipo (catálogo `tipo_medida_fito`), cantidade, unidade e nº de rexistro do MDF.
4. **Quen:** aplicador e máquina. Asesor opcional (persoa, data, validación), só se a explotación ten asesores.
5. **Resultado:** eficacia, observacións e avisos (§3).

- Edítase calquera tratamento, porque o formulario carga todas as filas. Desaparecen `cabe_no_formulario` e o aviso de «dáo de baixa e apúntao de novo».
- Nos tratamentos migrados amósanse os textos orixinais (`orixinal_*`) como axuda mentres se completan.

## Fóra deste deseño

- Histórico de versións das etiquetas: xa existe o snapshot semanal en `fitosanitarios`; integralo despois.
- Conversión de doses con volume de caldo.
- Almacén de produtos.
- Envío ao CUE (XEAGA).
- Descarga automática do JSON do MAPA: de momento faise a man, igual ca os catálogos do FEGA.

## Orde e reparto

Para cada paso, Claude escribe a versión esperada e próbaa en seco; ornith-88 implementa en tarefas de ≤6 edicións.

| Paso | Que | Quen |
|---|---|---|
| a | táboas, migración e importador do JSON con pontes; probas cun JSON pequeno de proba | ornith-88 |
| b | buscador de produto e enchido automático | ornith-88 |
| c | `comprobar_tratamento` con probas; avisos no formulario | ornith-88 |
| d | prazo de seguridade na lista e aviso en colleitas | ornith-88 |
| e | formulario con varias filas, medidas e asesor; editar todo | ornith-88 |
| f | quitar `cabe_no_formulario` e as súas probas | qwen-66 (limpeza) |
| — | textos dos avisos | Claude |

## Fases futuras comprobadas

- **Trazabilidade:** o prazo de seguridade e os produtos ligan tratamento → colleita (lote).
- **Plan de empresa:** produto escollido do rexistro = clave para custos e almacén.
- **CUE:** o nº de rexistro e os códigos SIEX van como pide `TratamFito`; nada cambia no modelo do tratamento.

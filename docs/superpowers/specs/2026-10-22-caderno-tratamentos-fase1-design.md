# Caderno de tratamentos conforme ao CUE — Fase 1 (deseño)

Data: 2026-10-22 · Estado: **aprobado (2026-10-22)** · Autor: Claude (con Xabier)

## 1. Obxectivo

Que o rexistro de tratamentos fitosanitarios de horta garde **exactamente** a información que esixen:

- o **Regulamento de Execución (UE) 2023/564** (formato electrónico dos rexistros de fitosanitarios: produto e nº de autorización, data e hora, dose en kg ou L/ha, superficie e unidade de terreo PAC, cultivo con código EPPO e estado BBCH);
- a **Orde APA/204/2023, anexo II** (contido mínimo do CUE: problema e xustificación, materia activa, aplicador con ROPO, equipo con ROMA/REGANIP, asesor, eficacia);
- o **descritor oficial do CUE do FEGA** (Anexo VI v3.11.4, bloque `TratamFito`, gardado en `docs/referencia/siex/cue-descriptor-ws-v3.11.4.csv`),

de forma que a futura exportación ao CUE sexa unha tradución directa, sen pedirlle datos novos ao usuario.

Contexto: dende o 1/1/2027 o rexistro electrónico é obrigatorio para explotacións profesionais (RD 1311/2012 art. 16.1, mod. RD 1039/2025). Ver `docs/estado-e-evolucion.md` §2.2, §8quater, §8sexies, §8octies.

## 2. Alcance

**Dentro**
1. Catálogos oficiais SIEX con versión (cultivos, variedades e listas de valores) + capa galega.
2. Persoas da explotación (aplicadores e asesores) con ROPO e caducidade.
3. Maquinaria/equipos aplicadores con ROMA/REGANIP e inspección.
4. Novo modelo de tratamento fitosanitario (sobre superficie) conforme ao bloque `TratamFito`.
5. Migración dos tratamentos existentes sen perder datos.
6. Formularios novos en ficheiros propios.

**Fóra (fases seguintes, cada unha co seu deseño)**: fertilización e plan de abonado; semente tratada; tratamentos postcolleita e en instalacións; rega; colleita; stock e lotes; vendas; ecolóxico; importación do REA e exportación ao CUE (IUWS); vixilancia automática de novas versións dos catálogos (irá co lector de novidades).

## 3. Decisións

| # | Decisión | Motivo |
|---|---|---|
| D1 | A fonte dos códigos é o **SIEX** (FEGA), non listas propias | É o que valida o CUE; evita traducións |
| D2 | Os catálogos **nunca se borran**: cada código ten `data_baixa` e cada importación rexistra unha versión | Conservación legal 3 anos; os rexistros antigos seguen sendo válidos |
| D3 | A **capa galega** (nome galego, orde de busca, variedades locais) vai en táboas propias | Unha importación nova do FEGA non a pisa |
| D4 | Un tratamento pode cubrir **varios cultivos/parcelas** e levar **varios produtos** | Así é a realidade e así o define `TratamFito` (DGCs 1..n, ProductosFito 0..n) |
| D5 | Dose **numérica + unidade do catálogo**; dose **ou** cantidade total, nunca ambas | Descritor oficial e Reg. 2023/564 |
| D6 | Aplicadores, asesores e equipos son **entidades da horta**, non texto | Reutilización, validación de carné e inspección |
| D7 | O carné ROPO do aplicador debe estar **vixente na data do tratamento**; se non, non se garda | Requisito legal; mensaxe clara |
| D8 | Os campos antigos de texto consérvanse como "orixinais" de só lectura | Non perder información histórica |

## 4. Modelo de datos

### 4.1 Catálogos

```
CatalogoVersion      id, fonte ("FEGA-SIEX"), nome_ficheiro, url, data_version,
                     data_importacion, sha256
CatalogoValor        id, catalogo (p.ex. "unidade_medida", "praga", "enfermidade",
                     "mala_herba", "regulador", "xustificacion", "eficacia",
                     "estado_fenoloxico", "tipo_produto", "tipo_medida_fito",
                     "boas_practicas", "tipo_maquinaria_une", "tipo_enerxia",
                     "sistema_cultivo", ...), codigo, descricion, data_baixa,
                     version_id → CatalogoVersion
                     UNIQUE(catalogo, codigo)
CultivoSiex          codigo (PK, nº SIEX), nome_oficial, nome_latin, codigo_eppo,
                     codigo_upov, horticola (bool), leñoso (bool), integrado (bool),
                     data_alta, data_modificacion, data_baixa, version_id
VariedadeSiex        id, cultivo_codigo → CultivoSiex, codigo, nome_oficial,
                     codigo_upov, data_baixa, version_id
                     UNIQUE(cultivo_codigo, codigo)
```

Capa galega:

```
NomeGalego           catalogo ("cultivo" | "variedade" | outro catálogo), codigo,
                     nome_gl, prioridade_galicia (int; maior = sae antes)
VariedadeLocal       id, cultivo_codigo → CultivoSiex, nome, fonte (p.ex. "Misión
                     Biolóxica de Galicia"), notas
                     (ao exportar ao CUE usa a variedade SIEX 0 "SIN VARIEDAD" e o nome
                      local vai nas observacións)
```

### 4.2 Persoas e equipos (por horta)

```
Persoa               id, horta_id, nome, apelidos, nif, e_aplicador, e_asesor,
                     ropo_numero, ropo_tipo_carne (básico | cualificado | fumigador |
                     piloto | sector_suministrador | sector_tratamentos),
                     ropo_caducidade (date), regfer_numero, activa
Maquina              id, horta_id, alias, tipo_une (CatalogoValor "tipo_maquinaria_une"),
                     marca_modelo, num_roma, num_reganip, id_equipo_non_inscribible,
                     propia (bool), potencia, unidade_potencia, tipo_enerxia,
                     data_ultima_inspeccion, alugada, activa
                     REGRA: como moito un de num_roma / num_reganip / id_equipo_non_inscribible
```

### 4.3 Tratamento fitosanitario (substitúe o modelo actual)

```
Tratamento           id, horta_id, data_inicio, data_fin, hora (time, opcional),
                     actividade_cuberta (NULL | mantemento | eliminacion),
                     eficacia (CatalogoValor "eficacia"), observacions,
                     baixa (bool, baixa lóxica), created_at,
                     -- conservados da versión anterior, só lectura:
                     orixinal_produto, orixinal_dose, orixinal_aplicador,
                     orixinal_equipo, orixinal_asesoramento

TratamentoCultivo    tratamento_id, cultivo_id → Cultivo, superficie_ha,
                     estado_fenoloxico (CatalogoValor "estado_fenoloxico")
                     REGRA: todos os cultivos dun tratamento teñen o mesmo cultivo
                            SIEX e a mesma variedade

TratamentoProblema   tratamento_id, tipo (enfermidade | praga | mala_herba | regulador),
                     codigo (CatalogoValor do tipo correspondente)
                     REGRA: polo menos 1

TratamentoXustificacion  tratamento_id, codigo (CatalogoValor "xustificacion")
                         REGRA: polo menos 1

TratamentoProduto    tratamento_id, tipo_produto (CatalogoValor), num_rexistro,
                     nome_comercial, materia_activa (texto; código só para
                     autorizacións excepcionais), dose, cantidade, unidade
                     (CatalogoValor "unidade_medida")
                     REGRA: dose XOR cantidade; num_rexistro obrigatorio para
                            fitosanitarios rexistrados

TratamentoMedida     tratamento_id, tipo_medida (CatalogoValor "tipo_medida_fito"),
                     cantidade, unidade, num_rexistro_mdf, boas_practicas
                     REGRA: o tratamento ten polo menos 1 TratamentoProduto ou
                            1 TratamentoMedida

TratamentoAplicador  tratamento_id, persoa_id → Persoa (e_aplicador), maquina_id →
                     Maquina (NULL se aplicacion_manual), aplicacion_manual,
                     horas_utilizacion, num_repeticions, duracion
                     REGRA: polo menos 1; ROPO da persoa vixente na data_inicio

TratamentoAsesor     tratamento_id (1:1, opcional), persoa_id → Persoa (e_asesor),
                     data, validacion (bool), observacions (≤200), confirmacion
                     (bool), contrato (bool)
```

A superficie total e a dose por hectárea calcúlanse; non se gardan dúas veces.

### 4.4 Cultivo (cambios mínimos)

`Cultivo` engade `cultivo_siex` (→ CultivoSiex, NULL permitido para cultivos antigos), `variedade_siex_id` (→ VariedadeSiex, NULL), `variedade_local_id` (→ VariedadeLocal, NULL). Mantéñense `especie` e `variedade` (texto) para compatibilidade e para hortas de autoconsumo que non queiran códigos.

## 5. Regras e validación (nos servizos)

Todas no servizo `tratamentos` (fronteira de seguridade), con `OperacionNonPermitidaError` e mensaxes en galego:

1. Permisos: `comprobar_rol_horta` (editor/admin) para crear, editar e dar de baixa; lector só le.
2. `data_fin ≥ data_inicio`.
3. Cultivos do mesmo cultivo SIEX e variedade; superficie > 0 e ≤ superficie da parcela (se se coñece).
4. ≥1 problema, ≥1 xustificación, ≥1 produto ou medida.
5. Produto: dose XOR cantidade; valores > 0; unidade obrigatoria.
6. Aplicador: persoa marcada como aplicadora; ROPO con caducidade ≥ `data_inicio` → se non: "O carné ROPO de X caducou o dd/mm/aaaa".
7. Máquina: como moito un identificador; se a inspección está vencida segundo a periodicidade legal (pendente de confirmar, ver §11.2) amósase **aviso**, non bloqueo.
8. Códigos de catálogo: deben existir e non estar de baixa na `data_inicio` (os xa gardados seguen válidos aínda que despois se dean de baixa).
9. Horta sen `uso_profesional`: os campos CUE son opcionais (autoconsumo); só se esixen 1–3 e un produto.

## 6. Importación dos catálogos

**Fonte confirmada (2026-10-22)**: o portal público do FEGA (https://www3.sede.fega.gob.es/bdcsixpor/catalogos) ofrece **107 catálogos** agrícolas, gandeiros e comúns, cada un descargable en CSV/XLSX dende o navegador (reCAPTCHA invisible: a descarga faise nunha sesión de navegador normal, sen saltar ningunha protección). O índice (METACATALOGO) inclúe para cada catálogo a data de publicación e a **expresión cron de actualización** (a maioría `0 0 0 1 * *` = o día 1 de cada mes; "Detalle material fertilizante" diario). O catálogo **Cultivo (PRODUCTOS)** ten 1.121 cultivos con **nome latino, código EPPO e UPOV**, e datas de alta, modificación e baixa por fila → o EPPO xa non é unha fase posterior.


- Comando: `uv run horta-catalogos importar <ficheiro.zip | ficheiro.xlsx> [--catalogo nome]`.
- Le o ZIP oficial do FEGA (circular PAC: cultivos e variedades) e os Excel dos catálogos do CUE descargados do portal.
- Idempotente: compara co existente e informa de **altas, baixas (marca `data_baixa`) e cambios de descrición**; nunca borra.
- Garda unha `CatalogoVersion` con sha256 (non reimporta o mesmo ficheiro).
- Os ficheiros orixinais non se versionan en git (tamaño); gárdase a URL e o hash.

**Descarga**: feita o 2026-10-22 por Claude no navegador (107 catálogos). Actualización mensual: repetir a descarga no navegador (procedemento documentado no plan); a importación compara e informa dos cambios. Non se automatiza contra o servidor saltando o captcha. En paralelo, pedirlle ao FEGA un acceso estable (correo a cau-fega@fega.es, Lei 37/2007).

## 7. Interface

- Ficheiros novos en `src/horta/ui/pages/`: `tratamentos.py` (lista e formulario), `persoas.py`, `maquinaria.py`. `horta_detalle.py` só os enlaza (pestanas), sen engadir máis código nel.
- Formulario de tratamento en pasos curtos: **1) Que e onde** (data, hora, cultivos/parcelas con superficie e estado) → **2) Por que** (problemas e xustificación) → **3) Con que** (produtos ou medidas) → **4) Quen** (aplicador, máquina, asesor) → **5) Resultado** (eficacia, observacións).
- Selectores con busca escribindo; resultados en galego primeiro e por `prioridade_galicia`; os usados recentemente na horta, arriba.
- Avisos visibles: ROPO a punto de caducar (30 días), inspección de máquina vencida.
- Tratamentos migrados amosan os datos "orixinais" nunha caixa de só lectura e un aviso "completa os datos para o CUE".

## 8. Migración

Unha migración Alembic:
1. Crea as táboas novas.
2. Para cada tratamento antigo: crea `TratamentoCultivo` co seu `cultivo_id` e `superficie_tratada`; copia `produto`, `dose`, `aplicador`, `equipo_aplicador`, `persoas_asesoramento` aos campos `orixinal_*`; `praga` pasa a `observacions` (non hai código fiable); `eficacia` a `observacions`.
3. Non inventa códigos. Os migrados quedan marcados como "incompletos para o CUE" (calculado: faltan problema/xustificación/produto codificado/aplicador).
4. Proba de migración sobre unha copia da BD con datos reais antes de aplicar.

## 9. Probas

- Servizos: un test por regra da §5 (permisos, cada validación, caducidade ROPO na data, dose XOR cantidade, mesmo cultivo, códigos de baixa).
- Importador: ficheiro pequeno de exemplo en `tests/fixtures/` → altas; segundo ficheiro → baixas e cambios; mesmo ficheiro dúas veces → sen cambios.
- Migración: BD con tratamentos antigos → datos en `orixinal_*` e relacións creadas.
- UI: proba manual no navegador do formulario en pasos (fluxo completo e erros).

## 10. División en tarefas (orientativa, para o plan)

Claude: modelos e migración, regras complexas, importador, deseño de UI. Smoth: tarefas literais pequenas (servizos CRUD de Persoa e Maquina, validacións simples con tests, columnas de táboas, textos), sempre con "Antes/Despois" e proba en seco previa.

## 11. Cuestións abertas

1. Descarga dos catálogos: resolto (§6); queda pedir ao FEGA unha vía estable.
2. Periodicidade legal da inspección de equipos (RD 1702/2011) para o aviso da §5.7.
3. Fonte das variedades locais galegas (Misión Biolóxica, CIAM Mabegondo): pendente de investigar.
4. Códigos EPPO: resolto, veñen no catálogo Cultivo do FEGA.

# Pastoreo (deseño)

Data: 2026-10-28 · Estado: **aprobado polo usuario** («Si», 2026-10-28) · Tarefas 080–080j · Paso 6, parte 4 (`docs/como-e-a-app.md` §5)

## Fontes

- **Caderno dixital, CUE bloque 12 «Pastoreo»** (RD 1054/2022; `docs/campos-oficiais-anexo-v.md`; descritor SIEX v3.11.4, comprobado o 2026-10-28). Os 10 campos son obrigatorios:
  - data de inicio e data de fin;
  - leiras (DGC) co seu cultivo, a superficie pastada e o tipo de cobertura do solo (catálogo `TIPO_COBERTURA_SUELO`, xa importado);
  - animais: REGA, especie e número de animais de cada especie;
  - animais da explotación (S/N) e de terceiros (S/N); non poden ser os dous «non».
  - Os detalles de actividade agraria 3, 29 e 30 do cultivo levan un pastoreo coas mesmas datas.
- **PAC, ecorréxime de pastoreo extensivo** (RD 1048/2022, art. 30, e cambios posteriores; hai que cotexar o texto vixente antes do informe):
  - pastoreo con animais propios un mínimo de días ao ano (120 no texto orixinal), co REGA activo;
  - carga gandeira mínima e máxima en UGM/ha (táboa do anexo V);
  - as leiras a máis de 10 km da instalación gandeira teñen que levar no caderno as datas de inicio e fin do pastoreo.
- **Prazo de seguridade dos fitosanitarios** (etiqueta do produto, rexistro do MAPA): o gando non debe comer un cultivo tratado antes de que remate o prazo. A app xa avisa disto nas colleitas.
- **Análise de campos** (`docs/analise-campos-2026-10-23.md` §7): «Pastoreo en parcelas · CUE Pastoreo».
- **Outras apps:**
  - farmOS: rexistros de movemento (o grupo entra nun lugar; sae cun movemento posterior) e un plan de pastoreo con tempo de recuperación de cada leira.
  - AgriWebb e apps de pastoreo rotativo: días pastados e días de descanso de cada leira, sacados dos movementos.

## Para que serve (obxectivo)

- Encher o **bloque 12 do caderno oficial** (paso 7) sen escribir nada dúas veces.
- Ter os datos do **ecorréxime de pastoreo** da PAC: días pastados con animais propios e animais por hectárea.
- **Seguridade:** avisar se o gando entra nunha leira antes de que remate o prazo de seguridade dun tratamento.
- Base do **historial da leira** (días de pastoreo e de descanso) e do **xemelgo** (leite ou carne de animais a pasto).

## Relacións (`docs/modelo-datos.md`)

- `pastoreo → horta`, `→ persoa` (quen levou o gando, obrigatorio) e `→ usuario` (`creado_por`).
- `pastoreo_leira → pastoreo`, `→ cultivo`: unha ou máis leiras. En Galicia o gando adoita andar en varias leiras pequenas á vez.
- `pastoreo_animal → pastoreo`: unha ou máis liñas de animais.
  - **Propios:** `→ animal` (grupo da mesma explotación). O REGA é o da explotación.
  - **De terceiros:** REGA e especie (catálogo oficial), sen grupo.
- Baixa lóxica, como os outros traballos.

## Que garda

**`pastoreo`**

| Campo | Para que | Fonte |
|---|---|---|
| `data_inicio` | cando entrou o gando | CUE 12.1 |
| `data_fin` (opcional mentres o gando segue alí) | cando saíu | CUE 12.2 |
| `persoa_id`, `horas`, `notas`, `baixa`, `creado_por`, `created_at` | como nos outros traballos | — |

**`pastoreo_leira`**

| Campo | Para que | Fonte |
|---|---|---|
| `cultivo_id` | a leira e o seu cultivo | CUE 12.3 |
| `superficie_ha` (opcional; ≤ a do cultivo; por defecto, a do cultivo) | superficie pastada | CUE 12.4 |
| `tipo_cobertura` (opcional; por defecto, a do cultivo) | tipo de cobertura do solo | CUE 12.10 |

**`pastoreo_animal`**

| Campo | Para que | Fonte |
|---|---|---|
| `animal_id` (propios) | o grupo | CUE 12.8 |
| `rega`, `especie_codigo` (de terceiros) | de quen son e que son | CUE 12.5, 12.7, 12.9 |
| `numero` (> 0) | cantos animais | CUE 12.6 |

**Normas:**
- Polo menos unha leira e unha liña de animais.
- Datas: inicio non futuro; fin ≥ inicio e non futura. O cultivo ten que estar na leira nesas datas.
- Grupo propio:
  - dado de alta antes do inicio e sen baixa antes do inicio;
  - o número non pode pasar dos animais que ten o grupo ese día;
  - se o grupo está noutro pastoreo nas mesmas datas, a suma das dúas liñas tampouco pode pasar dese número.
- As abellas non se ofrecen.
- De terceiros: REGA obrigatorio e especie do catálogo oficial.
- **Aviso, sen bloquear:** se algunha leira ten un tratamento co prazo de seguridade sen rematar na data de inicio, a app avisa: «Ollo: o tratamento do dd/mm/aaaa (produto) ten prazo de seguridade: non se debería meter o gando antes do dd/mm/aaaa». Usa o mesmo cálculo ca a colleita.

## Onde aparece

- **Animais:**
  - botón «Ao pasto» no grupo, que abre o formulario co grupo e o seu número xa postos;
  - se o grupo está no pasto, sae «No pasto: Leira de abaixo desde o dd/mm» e un botón «Saíron do pasto», que só pide a data de fin.
- **Leiras/cultivos:** nada novo nesta parte; o historial vai no paso 12.
- **Apuntar traballo** e **Diario:** tipo «Pastoreo», por exemplo «Pastoreo: 12 vacas (Vacas do monte) · Leira de abaixo, 0,8 ha · ata o 15/11 · Ana». Se o gando segue alí, «aínda no pasto».
- **Táboa «Pastoreo»** (fóra do menú, como «Entradas e saídas»): inicio, fin, leiras, animais e quen; editar e dar de baixa.
- **Tarefas:** novo tipo «Pastoreo», co grupo ou a leira. «Facela agora» como nos outros tipos.

## Fases futuras

- **Paso 7 (CUE):**
  - bloque 12 coas leiras (DGC), o REGA da explotación para os propios e as marcas propios/terceiros;
  - aviso se queda algún pastoreo sen data de fin, ou se un cultivo co detalle de actividade 3, 29 ou 30 non ten pastoreo coas mesmas datas;
  - comprobar se a especie do CUE (número dunha cifra) usa o mesmo catálogo ca o REGA.
- **Informe do ecorréxime:** días de pastoreo con animais propios en cada leira e no ano, e carga en UGM/ha (táboa do RD 1048/2022). As leiras a máis de 10 km precisan as coordenadas (mapa, paso 13).
- **Paso 12:** días pastados e días de descanso de cada leira no seu historial.
- **Xemelgo:** o lote de leite ou de carne mostra que os animais estiveron a pasto e onde.

## Probas previstas

Servizo:
- crear cunha leira e un grupo propio; crear con varias leiras e animais de terceiros;
- sen leiras ou sen animais, que falla;
- terceiros sen REGA ou cunha especie que non está no catálogo, que falla;
- máis animais dos que ten o grupo, tamén sumando outro pastoreo nas mesmas datas, que falla;
- datas: futuras, fin antes do inicio, grupo aínda sen alta, que fallan;
- superficie maior ca a do cultivo, que falla;
- «Saíron do pasto» pon a data de fin;
- aviso de prazo de seguridade;
- quen é obrigatorio;
- Diario e tarefa;
- non se borra un grupo, un cultivo nin unha explotación con pastoreo.

Navegador (escritorio e móbil, copia da BD):
- levar un grupo a dúas leiras, ver «No pasto» en Animais e no Diario;
- marcar «Saíron do pasto».

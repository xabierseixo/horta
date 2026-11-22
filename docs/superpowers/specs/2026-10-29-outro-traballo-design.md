# Outro traballo (paso 8 do deseño global)

Data: 2026-10-29 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.3. Tarefas 087–.

## Por que

Na explotación fanse traballos que non son de ningún libro oficial:
- arranxar un peche;
- limpar o galiñeiro;
- mantemento da máquina;
- levar papeis á cooperativa.

Hoxe non hai onde apuntalos, e esas horas tamén son traballo. O plan de empresa (paso 16) e os cartos (paso 10) precisan saber **cantas horas leva a explotación**, non só as dos traballos do CUE.

## Fontes

- **Plan de empresa AGADER:** as UTA (unidades de traballo) da explotación. Saen das horas de todos os traballos.
- **Deseño global §5.1 (parte común) e §5.3 (tipos de traballo).**
- Non hai libro oficial para estes traballos: por iso non levan campos de ningún catálogo.

## Que garda

**`outro_traballo`:** é un traballo coa parte común (§5.1): datas, quen, horas, máquina, notas, baixa, uuid e quen o apuntou.

| Campo | Para que |
|---|---|
| `descricion` | que se fixo (obrigatorio) |
| `parcela_id` | se foi nunha parcela (opcional) |
| `animal_id` | se foi cuns animais (opcional) |

- Sen parcela nin animais, o traballo é da explotación enteira.
- As instalacións chegan no paso 14; daquela engádese `instalacion_id`.

## Onde aparece

- **«Apuntar traballo» e Diario:** «Outro traballo», co texto da descrición. Por exemplo, «Outro traballo: arranxar o peche · Leira do río».
- **Tarefas:** tipo «Outro traballo»: ao facela ábrese o formulario coa descrición da tarefa.
- **Non ten táboa propia:** a súa lista é o Diario filtrado por «Outro traballo».
- **Ficha da parcela e dos animais (paso 12):** no seu historial.

## Informes

- **Non vai ao caderno nin ao CUE:** non son traballos rexistrados.
- **Plan de empresa e cartos:** as horas, coma as de calquera outro traballo.

## Probas previstas

- crear, editar e dar de baixa (baixa lóxica);
- sen descrición non se garda;
- a parcela e os animais teñen que ser da mesma explotación;
- quen o fixo nunha explotación profesional (coma no resto de traballos);
- Diario e tarefa;
- no navegador: apuntalo dende «Apuntar traballo» e velo no Diario.

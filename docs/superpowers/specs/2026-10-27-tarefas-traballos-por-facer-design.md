# Tarefas = traballos por facer (deseño)

Data: 2026-10-27 · Estado: **aprobado polo usuario** («pois adiante, se non tes o plan deseñado, deseñao», 2026-10-27) · Tarefas 076–

Parte de `docs/como-e-a-app.md` §5, paso 5: «a tarefa leva o tipo; ao marcala feita ábrese o formulario dese tipo xa enchido». Fontes: §2 («As tarefas son traballos *por facer*. Cando se fan, pasan a *feito* e complétanse os detalles do seu tipo. Non hai dúas listas distintas para o mesmo traballo»; parte común con quen e horas) e o deseño de quen e horas (`2026-10-27-quen-e-horas-design.md`). Nada inventado a maiores.

## Para que serve (obxectivo)

A app rexistra o traballo real e del saen os informes (caderno, CUE), o plan de empresa (horas, persoas, produción) e o xemelgo (eventos do lote). Planificar non pode crear unha segunda lista: o planificado convértese no rexistro do seu tipo, que é o que len os informes. A tarefa só garda o que aínda non se fixo (e, se é «outro traballo», quen e cantas horas).

## Relacións (`docs/modelo-datos.md`)

- `tarefa → horta` (xa); `tarefa → parcela`, `tarefa → cultivo` (xa, opcionais; ao borrar a parcela ou o cultivo quedan baleiros).
- `tarefa → persoa` (novo, FK): ten que ser da mesma explotación (`comprobar_quen`). As persoas non se borran (só ao borrar a explotación, e as tarefas bórranse antes).
- `tarefa → traballo apuntado` (novo: `tipo` + `traballo_id`, sen FK porque pode ser de sete táboas, igual que `Traballo(tipo, id)` no Diario). O servizo recibe o propio rexistro: deduce o tipo da súa clase, comproba que é o tipo da tarefa e que é da mesma explotación (a colleita, pola parcela do seu cultivo). Os traballos non se borran (só baixa), así que a ligazón non queda solta.

## Que garda a tarefa (migración `e1b3d5f7a9c2`)

| Campo | Para que |
|---|---|
| `tipo` | o tipo de traballo que se vai facer (tratamento, abonado, rega, labor, colleita, toma de mostras, tratamento en instalacións); baleiro = outro traballo |
| `persoa_id` | quen o vai facer (opcional ao planificar); cando se fai, quen o fixo |
| `horas` | horas de traballo, se se fixo sen tipo (opcional) |
| `traballo_id` | o rexistro que se apuntou ao facela, na táboa do seu tipo |

A sementeira non vai como tipo de tarefa: un cultivo con data de sementeira futura xa é a sementeira por facer (non hai dúas listas).

## Facer unha tarefa

- Desde o Diario (tocar unha tarefa por facer) ou desde Tarefas («Marcar feita»): **«Facela agora»**.
- **Con tipo:** ábrese o formulario dese tipo xa enchido co que se sabe (cultivo ou parcela, quen a ía facer, data de hoxe). Ao gardar, a tarefa pasa a *feito* coa data do traballo e queda ligada ao rexistro (`services/tarefas.facer_tarefa(session, actor, tarefa, rexistro)`).
- **Sen tipo:** pídese quen o fixo (obrigatorio, como todo traballo), a data e as horas (opcionais).
- **Diario:** unha tarefa feita e ligada non sae dúas veces: sae o traballo apuntado. Unha tarefa feita sen tipo sae con quen a fixo; as de antes sen persoa cóntanse en Informes («Traballos sen quen o fixo»).
- **Volver a por facer:** non se pode se xa ten o traballo apuntado («edita ese traballo»). Tampouco se pode cambiar o tipo.

## Nova tarefa e editar

O diálogo leva «Que traballo é» (baleiro = outro) e «Quen o vai facer» (opcional).

## Fases futuras

- Paso 6 (outro traballo e coidado de animais): as tarefas sen tipo poderán converterse nese tipo.
- Plan de empresa: as horas e as persoas das tarefas feitas sen tipo xa quedan gardadas.

## Tamén neste lote

- «Quen o fixo» só propón persoas activas no equipo (antes podía propoñer unha dada de baixa e o formulario fallaba).

## Probado

437 probas, ruff e mypy; migración arriba, abaixo e arriba nunha copia da BD. Navegador (escritorio e móbil, copia da BD): tarefa de rega con cultivo e Ana → «Facela agora» abre a rega xa enchida → gárdase, a tarefa queda feita e ligada e o Diario mostra só a rega; tarefa sen tipo → quen, data e horas; en Tarefas, volver a por facer unha xa apuntada avisa «edita ese traballo».

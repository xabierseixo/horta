# Entradas e saídas de animais (deseño)

Data: 2026-10-28 · Estado: **aprobado polo usuario** («Continuamos?», 2026-10-28) · Tarefas 078–078j · Paso 6, parte 2 (`docs/como-e-a-app.md` §5)

## Fontes

- **Libro de rexistro da explotación gandeira**, RD 787/2023 art. 23 e anexo V (BOE-A-2023-22499, comprobado o 2026-10-27), 3 anos:
  - **4** especie;
  - **8** identificación individual e tipo de dispositivo, se procede;
  - **9** entradas: nome e enderezo do titular anterior, código da explotación de orixe, código do movemento, data, número de animais e identificación, se procede;
  - **10** saídas: nome e enderezo do novo titular, código da explotación de destino, código do movemento, data, número e identificación.
- **README §7** (plan orixinal): grupos por especie con data de alta e de baixa. **README §22**: libro gandeiro con altas e baixas.
- **Análise de campos** (`docs/analise-campos-2026-10-23.md` §7):
  - «movementos (entradas, saídas, mortes) en vez de só cantidade»;
  - «especie dun catálogo».
- **Deseño da parte 1**: a especie pasa ao catálogo oficial nesta parte, e a data de alta pódese cambiar.
- **Outras apps:**
  - farmOS: rexistros de nacemento (coa nai) e de movemento; o número de animais sae dos rexistros, non se escribe a man.
  - Farmbrite: rexistros de vendas e mortes por animal ou grupo.

## Para que serve (obxectivo)

- Completa o **libro de rexistro gandeiro**: as entradas e saídas (puntos 9–10), xunto cos coidados da parte 1 (6, 7, 11) e o REGA da explotación (1–3). O informe sae no paso 14.
- O número de animais de cada grupo **sae dos apuntamentos**: non hai que cambialo a man e non pode quedar mal.
- Prepara as **vendas** (parte 4): unha venda de animais é unha saída.
- Prepara o **xemelgo**: a orixe dos animais dun lote.

## Relacións (`docs/modelo-datos.md`)

- `movemento_animal → horta`, `→ animal` (o grupo, obrigatorio, da mesma explotación), `→ persoa` (quen o fixo, obrigatorio; non no movemento inicial) e `→ usuario` (`creado_por`).
- `animal.especie_codigo` (novo): código do catálogo oficial `especie_animal`, xa importado. Só se ofrecen as especies de granxa, en galego (galiñas, porcos, ovellas, cabras, coellos, abellas…). `animal.especie` pasa a ser **o nome do grupo** (p. ex. «Galiñas do galiñeiro de abaixo»).
- **A cantidade do grupo** = suma dos movementos. Cada vez que se apunta, edita ou dá de baixa un movemento, recalcúlase.
  - Non se pode deixar o grupo en negativo en ningunha data.
  - Se queda a 0, o grupo pasa a *baixa* coa data dese movemento. Se despois entra algún animal, volve a *activo*.
- **Data de alta** = data do movemento inicial. Pódese cambiar.
- **Borrar un grupo:** só se non ten coidados nin máis movementos ca o inicial (obriga de 3 anos). Se non, bórranse ese grupo e o seu movemento inicial.
- Os movementos non se borran: **baixa lóxica**.

## Que garda (táboa nova `movemento_animal`)

Parte común: `horta_id`, `animal_id`, `data`, `tipo`, `cantidade` (> 0), `identificacion` (crotais, anelas…, se os teñen), `persoa_id`, `horas`, `notas`, `baixa`, `creado_por`, `created_at`.

| Tipo | Etiqueta | Datos propios | Fonte |
|---|---|---|---|
| `inicial` | Animais ao dar de alta o grupo | — (créase só, ao crear o grupo) | README §7 |
| `nacemento` | Nacemento | — | farmOS; libro (altas) |
| `entrada` | Entrada (compra, cesión) | `titular` (nome e enderezo do anterior), `rega` da orixe, `codigo_movemento` (nº de guía) | an. V.9 |
| `saida` | Saída (venda, cesión, matadoiro) | `titular` (nome e enderezo do novo), `rega` do destino, `codigo_movemento` | an. V.10 |
| `morte` | Morte ou sacrificio na casa | `causa` (texto) | libro (baixas); análise §7 |

- **Aviso, sen bloquear:** unha saída ou un sacrificio dun grupo en tempo de espera avisa «Este grupo está en tempo de espera ata dd/mm/aaaa». Usa `fin_tempo_espera`, da parte 1.
- Os grupos que existen agora reciben un movemento `inicial` coa súa cantidade e data de alta (migración).

## Onde aparece

- **Animais:**
  - «Novo grupo»: nome do grupo, especie (lista oficial en galego), raza (opcional; propón as razas oficiais desa especie, como a Galiña de Mos, ou texto libre), cantidade e data de alta.
  - Editar: nome, especie, raza e data de alta. A cantidade móstrase pero non se escribe.
  - Botón «Entrada ou saída» e ligazón «Ver entradas e saídas».
- **Apuntar traballo** e **Diario**: tipo «Entrada ou saída de animais», por exemplo «Saída: 4 · Galiñas · Ana». O inicial non sae.
- **Táboa «Entradas e saídas»** (fóra do menú): data, grupo, tipo, cantidade, orixe ou destino, quen; editar e dar de baixa.
- **Tarefas:** novo tipo «Entrada ou saída de animais», co grupo. «Facela agora» como nos outros tipos.

## Fases futuras

- **Paso 14:** informe «Libro de rexistro da explotación», por especie, cos puntos 1–11. A clasificación e a capacidade (punto 5) engadiranse alí, coa explotación.
- **Parte 4 (vendas):** unha venda de animais vivos crea a súa saída. Os produtos (ovos, mel) van na parte de produción.
- **Xemelgo:** a orixe dos animais (REGA de orixe) vai no historial do lote.
- **Lector de crotais por Bluetooth** (app do móbil, máis adiante): enche `identificacion`.

## Probas previstas

Servizo:
- crear un grupo crea o movemento inicial;
- nacemento, entrada e saída cambian a cantidade;
- unha saída maior ca o que hai, ou que deixa un día en negativo, falla;
- a 0 o grupo pasa a baixa, e unha entrada posterior volve a activalo;
- editar e dar de baixa recalcula a cantidade;
- especie fóra do catálogo falla;
- non se borra un grupo con movementos ou coidados;
- quen o fixo é obrigatorio;
- aviso de tempo de espera na saída;
- Diario e tarefa.

Navegador (escritorio e móbil, copia da BD): crear un grupo, apuntar unha entrada e unha saída, e ver a cantidade e o Diario.

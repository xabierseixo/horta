# Coidado e saúde dos animais (deseño)

Data: 2026-10-27 · Estado: **aprobado polo usuario** («Continua», 2026-10-28) · Tarefas 077–077j · Paso 6, parte 1 de 5 (`docs/como-e-a-app.md` §5)

Partes do paso 6, na orde acordada co usuario (2026-10-27): 1) coidado e saúde dos animais; 2) entradas e saídas de animais; 3) pastoreo (CUE 12); 4) vendas (Decreto 125/2014, CUE 3); 5) outro traballo (mantemento, envasado…).

## Fontes

- `docs/como-e-a-app.md` §2: tipo «Coidado de animais (máis adiante: medicamentos)»; parte común de todo traballo (datas, estado, a que se refire, quen e horas, máquina, notas).
- **Libro de rexistro da explotación gandeira**, RD 787/2023 art. 23 e anexo V (BOE-A-2023-22499, comprobado o 2026-10-27): consérvase 3 anos, en papel ou informático, por especie. Do anexo V tocan a esta parte: **6** incidencias de enfermidades infecciosas ou parasitarias (data e animais afectados); **7** cambios na produción que fagan sospeitar de enfermidade ou de problemas de benestar (data e animais afectados); **11** visitas e vehículos, incluídas as do veterinario. Os puntos 6, 7 e 11 poden levarse en rexistros á parte (art. 23.5). Os puntos 9 e 10 (entradas e saídas) van na parte 2.
- **Medicamentos veterinarios**, Regulamento (UE) 2019/6 art. 108 e RD 666/2023 art. 41 (`docs/estado-e-evolucion.md` §8quinquies e §8sexies): data da primeira administración, medicamento, cantidade, provedor (nome e enderezo), proba de compra, animal ou grupo, veterinario que o receitou e nº de receita, **tempo de espera (aínda que sexa cero)**, duración do tratamento; consérvase **5 anos**.
- Outras apps (2026-10-27): farmOS (rexistros de actividade, observación e médicos sobre animais ou grupos), Farmbrite (coidados e tratamentos por animal ou grupo, aviso do tempo de espera). De aí: apuntar por **grupo** (non só animal a animal) e o **aviso do tempo de espera**.

Non hai modelo galego do libro (pendente de atopar). Non se confirmou se as galiñas de autoconsumo (RD 637/2021) teñen que levar o libro: a app déixao apuntar a todos.

## Para que serve (obxectivo)

É traballo real (un *traballo*, non unha sección que encher). Del saen: o **libro de rexistro gandeiro** e o **rexistro de medicamentos** (informes, despois da parte 2), as horas e as persoas do **plan de empresa**, e o **xemelgo** (os ovos, o mel ou o leite dun lote levarán o historial sanitario e o tempo de espera cumprido).

## Relacións (`docs/modelo-datos.md`)

- `coidado_animal → horta` (novo).
- `coidado_animal → animal` (novo, obrigatorio): o grupo de animais da mesma explotación, de alta: só se ofrecen os grupos activos e a data do coidado non pode ser posterior á de baixa. A data de alta non se comproba porque hoxe a app pon a do día en que se crea o grupo e non deixa cambiala (chegará coas entradas e saídas, parte 2).
- `coidado_animal → persoa` (quen o fixo, obrigatorio como todo traballo; `comprobar_quen`, mesma explotación).
- `coidado_animal → maquina` (opcional; mesma explotación).
- `coidado_animal → usuario` (`creado_por`).
- `tarefa → animal` (novo, opcional): unha tarefa pode referirse a un grupo de animais, igual ca a unha parcela ou cultivo. Novo tipo de tarefa `coidado_animal`.
- **Borrar animais (cambio):** hoxe `eliminar_animal` borra de todo. Desde agora, se o grupo ten coidados apuntados **non se pode borrar**: dáselle de baixa (data de baixa), porque eses rexistros hai que gardalos 3 e 5 anos. Se non ten nada apuntado, bórrase coma ata agora. Ao borrar un grupo sen coidados, as tarefas que o nomean quedan sen animal (como coa parcela).
- Os coidados non se borran: **baixa lóxica**, como o resto dos traballos.

## Que garda (táboa nova `coidado_animal`)

**Parte común:** `horta_id`, `animal_id`, `data_inicio`, `data_fin` (baleiro = o mesmo día), `tipo`, `persoa_id`, `horas`, `maquina_id`, `notas`, `baixa`, `creado_por`, `created_at`.

**Que se fixo** (`tipo`), cos seus datos:

| Tipo | Etiqueta | Datos | Fonte |
|---|---|---|---|
| `coidado` | Coidado (comida, auga, limpeza…) | `descricion` (obrigatoria) | como-e-a-app §2 |
| `enfermidade` | Enfermidade | `descricion` (que se viu, obrigatoria), `num_animais` afectados, `identificacion` dos animais (se a teñen) | RD 787/2023 an. V.6 |
| `producion` | Cambio na produción | `descricion` (p.ex. «poñen a metade»), `num_animais`, `identificacion` | an. V.7 |
| `medicamento` | Medicamento | `medicamento` (obrigatorio), `cantidade` + `unidade` (do catálogo de unidades), `num_animais`, `identificacion`, `provedor` (nome e enderezo), `proba_compra` (nº de factura ou albará), `veterinario`, `receita`, `tempo_espera_dias` (**obrigatorio, pode ser 0**), `duracion_dias` | Reg. 2019/6 art. 108; RD 666/2023 |
| `visita` | Visita ou vehículo | `visitante` (quen veu, obrigatorio), `descricion` (motivo), `matricula` do vehículo | an. V.11 |

`num_animais` non pode ser maior ca a cantidade do grupo. `tempo_espera_dias` e `duracion_dias` ≥ 0.

**Tempo de espera:** un medicamento marca «non usar os produtos ata» = (data de fin, ou data de inicio + duración − 1 día) + tempo de espera. Calcúlao o servizo (`fin_tempo_espera(coidado)`), non se garda.

## Onde aparece

- **Apuntar traballo** e **Diario:** novo tipo «Coidado de animais» (icona `pets`). No Diario: «Coidado de animais: Medicamento — Oxitetraciclina» · grupo · quen.
- **Formulario** (curto no móbil): grupo de animais (só os de alta), que se fixo, data, quen o fixo, e os datos do tipo escollido. En «Máis datos»: data de fin, horas, máquina, notas.
- **Táboa «Coidados dos animais»** (fóra do menú, desde o Diario e desde Animais): data, grupo, que, quen; editar e dar de baixa.
- **Animais:** o grupo que está en tempo de espera mostra «En tempo de espera ata dd/mm/aaaa»; e ligazón «Ver os coidados».
- **Tarefas:** tipo «Coidado de animais» e, opcional, o grupo de animais. «Facela agora» abre o formulario co grupo e a persoa xa postos (paso 5).

## Fases futuras

- **Parte 2 (entradas e saídas):** xunto con estes rexistros e o REGA da explotación completan o libro (puntos 1–11) → informe «Libro de rexistro da explotación» e «Rexistro de medicamentos». A especie pasará ao catálogo oficial `especie_animal` (xa importado) cando se toquen os grupos na parte 2; aquí non se cambia.
- **Parte 4 (vendas):** avisará se se vende un produto dun grupo en tempo de espera (usa `fin_tempo_espera`).
- **Xemelgo:** os eventos sanitarios do grupo de orixe entran no historial do lote.
- **Plan de empresa:** horas e persoas xa quedan na parte común.
- **Fotos e adxuntos** (receita, factura): cando existan os adxuntos.

## Probas previstas

Servizo: crear cada tipo coas súas obrigas (medicamento sen tempo de espera falla; 0 vale); grupo doutra explotación ou xa de baixa nesa data falla; `num_animais` maior ca o grupo falla; quen obrigatorio; editar e baixa; `fin_tempo_espera`; borrar un grupo con coidados falla e sen coidados vai; Diario mostra o coidado; tarefa de coidado → «Facela agora» → queda ligada. Navegador (escritorio e móbil, copia da BD): apuntar un medicamento, ver o aviso en Animais e no Diario.

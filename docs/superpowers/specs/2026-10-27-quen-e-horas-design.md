# Quen fixo cada traballo e cantas horas (deseño)

Data: 2026-10-27 · Estado: **aprobado polo usuario** («A partir diso tes que continuar codificando», 2026-10-27) · Tarefas 075–075k

Parte de `docs/como-e-a-app.md` §5, paso 4. Só o que xa está acordado nese documento; nada inventado a maiores.

## Principio (usuario, 2026-10-27)

«Os traballos sempre os fai a xente»: todo traballo leva **quen o fixo**. O mínimo para apuntar pasa a ser *que, onde, cando e quen*. As **horas** son opcionais.

## Que garda cada tipo

| Tipo | Quen | Horas |
|---|---|---|
| Rega, colleita, toma de mostras, tratamento en instalacións | `persoa_id` (novo) | `horas` (novo) |
| Labor | `persoa_id` (xa existía, agora obrigatorio) | `horas` (novo; `duracion_h` segue sendo o das pasadas da máquina, CUE) |
| Abonado | `aplicador_persoa_id` (xa existía, agora obrigatorio salvo que o fixese unha empresa de servizos con REGFER, campo do CUE) | `horas` (novo) |
| Sementeira ou plantación (no cultivo) | `sementeira_persoa_id` (novo) | `sementeira_horas` (novo) |
| Tratamento fitosanitario | sen cambios: os aplicadores e as súas horas de máquina, como pide o CUE | — |
| Tarefa (por facer) | sen cambios: queda para o paso 5 | — |

Migración `d0a2c4e6f8b1` (columnas que admiten baleiro: os rexistros de antes non se tocan).

## Regras

- O servizo de cada tipo esixe a persoa («Indica quen o fixo») e que sexa da explotación (`services/persoas.comprobar_quen`). As horas, se se poñen, teñen que ser máis de 0.
- Sementeira: o cultivo tamén pode estar planificado (por facer), así que o servizo só comproba que a persoa sexa da explotación; o formulario esixe quen cando a data de sementeira xa pasou.
- **Os rexistros de antes sen persoa non se inventan**: o Diario sabe cales son (`Traballo.sen_quen`) e **Informes** mostra cantos hai de cada tipo, a todas as explotacións, cunha ligazón para completalos. Ao editalos pídese quen o fixo.
- No formulario, «Quen o fixo» vai á vista, despois da data, e propón quen fixo o último traballo (regra 5: «propoñer o último valor usado»). As horas van en «Máis datos».

## Diario

`Traballo.persoas` (quen o fixo). Filtro **Quen** e o nome na tarxeta.

## Probado

429 probas, ruff e mypy. Navegador (escritorio e móbil, copia da BD): apuntar unha rega sen persoa (avisa), con persoa e horas, filtrar o Diario por persoa e ver en Informes os traballos de antes sen quen.

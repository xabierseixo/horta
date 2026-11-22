# Labores culturais (CUE bloque 5) (deseño)

Data: 2026-10-25 · Estado: **aprobado e feito** (tarefas 073–073e, 2026-10-25)

Fontes:
- Anexo V do CUE, bloque 5 (`docs/campos-oficiais-anexo-v.md`).
- Descritor do servizo web CUE v3.11.4, bloque `LaboresCulturales` (`docs/referencia/siex/cue-descriptor-ws-v3.11.4.csv`). Manda cando discrepa do Anexo V.
- Catálogos FEGA `TIPO_LABOR` (14), `TIPO_COBERTURA_SUELO` (6), `TIPO_MAQUINA_UNE`, `TIPENERGIA` (xa importados).

Obriga: o CUE electrónico é obrigatorio desde o 1/1/2027 (RD 1311/2012 modificado polo RD 1039/2025). O modelo en papel da Xunta non ten folla de labores.

## Campos — táboa `labor`

Un cultivo por rexistro, igual ca abonados e regas (decisión do usuario do 2026-10-25). Baixa lóxica.

| Campo | Tipo | Obrig. | CUE / regra |
|---|---|---|---|
| horta_id, cultivo_id | FK | si | `DGCs`: cultivo da parcela |
| data_inicio, data_fin | data | si | `FechaInicio`, `FechaFin`. Fin ≥ inicio; fin por defecto = inicio; non futura |
| superficie_ha | número | si | `Superficie`. Por defecto a do cultivo; ≤ cultivo |
| tipo_labor | catálogo TIPO_LABOR | si | `TipoLabor` |
| restos_desbroce_no_solo | si/non | si | `DepositadoSueloDesb`. Só se pregunta en «Desbroce e sega» (5) |
| restos_poda_no_solo | si/non | si | `DepositadoSueloPoda`. Só se pregunta nas podas (7, 11, 12) |
| tipo_cobertura | catálogo TIPO_COBERTURA_SUELO | non | `Cubiertas` (0..n no descritor). Por defecto, a do cultivo (`cultivo.tipo_cobertura_solo`) |
| maquina_id | FK maquina | non | `Maquinaria`: tipo UNE, potencia, unidade e enerxía saen da máquina, como no abonado |
| num_repeticions, duracion_h | número | non | `NumRepeticiones`, `Duracion` (horas de cada repetición) |
| persoa_id | FK persoa | non | non é do CUE: quen o fixo. Serve para as horas de traballo do plan de empresa |
| notas, baixa, creado_por, created_at | | | como as regas |

## Pantalla «Labores» (CADERNO, despois de Rega)

- **Táboa:** data, cultivo, labor, máquina.
- **Diálogo á vista:** cultivo, data, labor e, se procede, o «quedaron os restos no chan?».
- **«Máis datos»:**
  - data de fin;
  - superficie;
  - cobertura do solo;
  - máquina, repeticións e horas;
  - quen o fixo;
  - notas.
- Proponse o último labor apuntado nese cultivo.

## Outros

- **Borrar cultivos, parcelas ou explotacións con labores:** non se pode, como coas regas (conservación de 3 anos).
- **Caderno descargable:** folla nova «9 Labores (CUE)» co período escollido. Non está no modelo da Xunta, pero si no CUE.

## Fases futuras comprobadas

- **Plan de empresa:** horas de máquina e de persoa por cultivo → custos.
- **Trazabilidade:** labores por cultivo → lote.
- **Tarefas:** marcar unha tarefa feita podería crear o labor (non neste deseño).
- **Envío ao CUE:** os campos seguen `LaboresCulturales`.

## Reparto

Claude escribe e proba a versión esperada; ornith-88 implementa en tarefas de ≤6 pasos.

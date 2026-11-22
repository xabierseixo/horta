# Tipo de explotación e "en regra" (deseño)

Data: 2026-10-22 · Estado: **aprobado** (Xabier, conversa do 2026-10-22)

## Obxectivo

O público principal son pequenas e medianas explotacións profesionais, sen excluír o uso non profesional. Na interface dise **"explotación"** (o modelo interno segue chamándose `Horta`).

## Tres estados (calculados, non gardados)

| Estado | Condición | Regras |
|---|---|---|
| `non_profesional` | `uso_profesional = False` | sen obrigas legais; caderno opcional; sen exportar ao CUE |
| `en_preparacion` | profesional e falta NIF do titular ou nº REAGA | regras profesionais; lista "en regra"; sen exportar ao CUE |
| `rexistrada` | profesional con NIF do titular e nº REAGA | regras profesionais; exporta ao CUE |

Calcúlase cunha función (`estado_rexistro(horta)`) para que nunca haxa un estado incoherente cos datos.

## Datos novos da explotación

`titular_nome`, `titular_nif` (NIF, NIE ou CIF; patróns do descritor SIEX), `codigo_reaga` e `codigo_rega` (formato `ES` + 12 díxitos, como `codigoREA` do descritor CUE). Todos opcionais.

## "En regra" (só profesionais)

Función `requisitos_en_regra(session, horta) -> list[Requisito]` (texto, cumprido, axuda). Primeira versión:
1. NIF do titular.
2. Inscrición no REAGA.
3. Polo menos un aplicador co carné ROPO en vigor.
4. Se hai animais: código REGA.

Amósase no Resumo. Medrará con cada fase (plan de abonado, SEVEDI, ecolóxico…).

## Interface

- Crear/configurar explotación: pregunta "Tipo de explotación" (Profesional / Non profesional); se é profesional, campos do titular e códigos.
- Resumo: etiqueta co estado e a lista "Para estar en regra".
- Textos visibles: "horta" → "explotación".

## Reparto

Todo en tarefas literais para smoth (018 en diante), con proba en seco previa.

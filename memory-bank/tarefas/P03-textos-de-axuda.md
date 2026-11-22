# Tarefa P03 (qwen-66) — Textos de axuda dos campos

**Estado**: feita (Claude, 2026-10-24)

## Obxectivo

Escribir unha axuda curta para cada campo dos formularios, para un agricultor que non é experto. Son **propostas**: revisaraas unha persoa.

## Ficheiros

- Ler: `memory-bank/entrada/campos-para-axuda.csv` (columnas `pantalla;campo`).
- Crear: `docs/propostas/axuda-campos.csv`

Ningún outro. Non crees scripts.

## Formato

Cabeceira e unha liña por cada liña da entrada, na mesma orde:

```
pantalla;campo;axuda
parcelas;Recinto;O último número da referencia SIGPAC da parcela. Está na solicitude da PAC ou no visor SIGPAC.
cultivos;Sementeira directa;Marca se sementaches sen arar antes a terra.
```

- Galego normativo, frases curtas (máximo 25 palabras), sen tecnicismos.
- Se non sabes que significa un campo, escribe só `?` na axuda. Non inventes.
- Non uses punto e coma dentro do texto.

## Ao rematar

Enche o Resultado, marca Estado: feita e fai un só commit co rodapé 'Axente: qwen-66'.

## Resultado

Propostas feitas por Claude, pendentes de revisión humana. Columna `seguridade`: revisar primeiro as `baixa` e `media`.

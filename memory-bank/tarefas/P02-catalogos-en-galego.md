# Tarefa P02 (qwen-66) — Traducir ao galego os textos dos catálogos oficiais

**Estado**: feita (Claude, 2026-10-24)

## Obxectivo

Os catálogos oficiais do FEGA veñen en castelán. Propor a tradución ao galego de cada texto. Son **propostas**: revisaraas unha persoa antes de usalas.

## Ficheiros

- Ler: `memory-bank/entrada/catalogos-para-galego.csv` (columnas `catalogo;codigo;descricion_oficial`).
- Crear: `docs/propostas/catalogos-en-galego.csv`

Ningún outro. Non crees scripts.

## Formato do ficheiro que creas

Cabeceira e unha liña por cada liña da entrada, na mesma orde, separadas por punto e coma:

```
catalogo;codigo;descricion_oficial;descricion_gl;seguridade
sistema_cultivo;1;Aire libre;Aire libre;alta
sistema_cultivo;4;Invernadero (cubierta accesible);Invernadoiro (cuberta accesible);alta
```

- `descricion_gl`: galego normativo (RAG), mesma maiúscula inicial que o orixinal. Vocabulario: invernadero → invernadoiro, riego → rega, regadío → regadío, secano → secano, siembra → sementeira, cosecha → colleita, abono → abono, estiércol → esterco, purín → xurro, suelo → solo/chan, semilla → semente, plantón → plantón, cubierta → cuberta, arrendamiento → arrendamento, propiedad → propiedade, seta → cogomelo, champiñón → champiñón.
- `seguridade`: `alta`, `media` ou `baixa`. Non inventes: se dubidas, `baixa`.

## Ao rematar

Enche o Resultado, marca Estado: feita e fai un só commit co rodapé 'Axente: qwen-66'.

## Resultado

Propostas feitas por Claude, pendentes de revisión humana. Columna `seguridade`: revisar primeiro as `baixa` e `media`.

# Tarefa P01 (penélope) — Propor nomes galegos de cultivos hortícolas

**Estado**: feita (Claude, 2026-10-24)

## Obxectivo

Propor o nome galego de cada cultivo hortícola da lista oficial que aínda non o ten. Son só **propostas**: revisaraas unha persoa antes de usalas.

## Ficheiros

- Ler: `memory-bank/entrada/cultivos-horticolas-sen-galego.csv` (columnas `codigo;nome_oficial;nome_latin`, nome oficial en castelán).
- Crear: `docs/propostas/nomes-galegos-horticolas.csv`

Ningún outro. Non crees scripts.

## Formato do ficheiro que creas

Unha liña de cabeceira e unha liña por cada cultivo da entrada, na mesma orde, separadas por punto e coma:

```
codigo;nome_oficial;nome_gl;seguridade
99;PATATA;Pataca;alta
```

- `nome_gl`: nome común en galego normativo (RAG), con maiúscula inicial e sen artigo. Exemplos correctos: Pataca, Cebola, Allo, Leituga, Pemento, Tomate, Cenoria, Nabiza, Grelos, Faba, Fabón, Repolo, Cabaza, Berenxena, Allo porro, Remolacha, Rabanete, Espinaca, Acelga.
- `seguridade`: `alta` se estás seguro, `media` se é probable, `baixa` se non o sabes. Se non o sabes, pon o nome traducido literalmente e `baixa`. Non inventes.

## Ao rematar

Enche o Resultado, marca Estado: feita e fai un só commit co rodapé 'Axente: penelope'.

## Resultado

Propostas feitas por Claude, pendentes de revisión humana. Columna `seguridade`: revisar primeiro as `baixa` e `media`.

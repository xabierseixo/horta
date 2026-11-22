# Revisión da app tras a cola 029–038 (2026-10-24)

Probado no navegador coa conta de proba: abren sen erros Parcelas, Cultivos, Colleitas, Tratamentos, Fertilización, Tarefas, Animais, Equipo e Maquinaria, e os formularios novos (parcela, cultivo, colleita, persoa). Apuntar unha colleita funciona de principio a fin (lote proposto, gardado, aparece na lista).

## Ocos atopados

| # | Onde | Que pasa | Por que importa |
|---|---|---|---|
| 1 | Tratamentos | Non se pode editar un tratamento: `actualizar_tratamento_fito` existe pero ningunha pantalla o usa. | Un erro ao apuntar obriga a dar de baixa e volver crear; no CUE queda rastro de baixas innecesarias. |
| 2 | Maquinaria | Non hai botón de editar (`actualizar_maquina` sen usar). | A data de inspección cambia cada poucos anos (ROMA/ITEAF). |
| 3 | Colleitas | "Superficie colleitada" pide hectáreas en texto; o resto da app usa `CampoSuperficie` (m² ou ha). | Incoherencia; quen traballa en m² ten que converter. |
| 4 | Colleitas | O lote proposto usa o código SIEX do cultivo (`2026-99-001`). | Para quen merca, un número sen significado; a trazabilidade (fase futura) pedirá un lote lexible. Decidir o formato antes de que haxa moitos lotes. |
| 5 | Cultivos | Os cultivos antigos teñen superficie baleira e estado "Faltan datos". | Normal en datos de proba; a pantalla xa avisa. |
| 6 | Equipo | `uta_equipo` móstrase (0 horas = 0 UTA) pero `rendemento_kg_ha` aínda non se ve en ningures. | Rendemento serve para o plan de empresa; mostralo na colleita ou no resumo. |
| 7 | Código vello | O modelo `Tratamento` antigo e `services/tratamentos.py` seguen (só os usan probas e o borrado de parcelas). | **Feito** (tarefas 042–042e): modelo, servizo e táboa quitados. |

## Feito hoxe

- Limpeza: fóra `_seccion_parcelas`, `_seccion_cultivos`, `_seccion_membros` e `ui/pages/persoas.py` (−627 liñas).
- Rexenerados `modelo-datos.md` e `campos-oficiais-anexo-v.md` (campos sen cubrir: 426 → 408, en REA 2 e 12).

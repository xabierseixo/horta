# Análise da app tal como está (2026-10-23)

Percorrido pantalla a pantalla na rama `deseno-visual` (escritorio 1360 px e móbil 390 px), máis revisión do código. Complementa `analise-campos-2026-10-23.md` (campos fronte a REA/CUE e normativa). Capturas en `.playwright-mcp/an-*.png` (fóra do repo).

Lenda: **P1** = falla ou confunde a calquera usuario; **P2** = incómodo ou incoherente; **P3** = mellora.

---

## A. Problemas transversais (afectan a todas as pantallas)

| # | Problema | Onde se ve | P |
|---|---|---|---|
| A1 | **No móbil o menú lateral ábrese tapando a pantalla** ao entrar en calquera sección (`left_drawer(value=True)` en `ui/layout.py`). Hai que pechalo cada vez | móbil, todas | P1 |
| A2 | **Os botóns Editar / Eliminar non se ven ata marcar a caixa dunha fila.** Non hai pista de que hai que marcala; non se pode premer a fila para abrila | parcelas, cultivos, fertilización, tarefas, animais, membros, persoas | P1 |
| A3 | **Cada sección fai as cousas dun xeito distinto**: botón "Novo" arriba á dereita (parcelas, cultivos...) ou debaixo da táboa (tratamentos, persoas, maquinaria); "Editar" / "Editar seleccionada" / "Cambiar rol"; maquinaria sen editar nin dar de baixa; tratamentos sen editar nin ver o detalle; buscador e filtro só nalgunhas | todas | P1 |
| A4 | **Textos en inglés** na paxinación das táboas: "Records per page", "1-1 of 1", "1 record selected". NiceGUI/Quasar non ten paquete de galego (só `es`), así que hai que poñer os textos con props da táboa (`rows-per-page-label`, `:pagination-label`, `:selected-rows-label`) nun único sitio común | todas as táboas | P2 |
| A5 | **Valores internos á vista** en vez de texto para persoas: "activa", "planificado", "admin", "lector", "abonado_fondo", "si" | táboas e selectores | P2 |
| A6 | **Datas en formato AAAA-MM-DD** escritas a man e amosadas así no Resumo (tarefa 025 arranxa a entrada; falta amosalas como 23/10/2026) | formularios, Resumo | P1 (025) / P2 |
| A7 | **Campos estreitos e sen nome** nos diálogos (tarefa 024) | diálogos | P1 (024) |
| A8 | **Superficie sen unidade** ("3000") e en unidades distintas (tarefa 027) | parcelas, fertilización | P1 (027) |
| A9 | Aviso de táboa baleira cun **triángulo de perigo** (icona por defecto de Quasar): parece un erro | táboas baleiras | P3 |
| A10 | As táboas no móbil precisan desprazamento horizontal; mellor tarxetas (xa previsto na maqueta) | móbil | P2 |
| A11 | Diálogos longos (editar cultivo, fertilización) son unha columna moi alta con desprazamento; non hai seccións | editar | P2 |
| A12 | Crear e editar piden campos distintos: créase con 3 campos e hai que volver a abrir para completar (tarefas, cultivos, fertilización, animais, parcelas) | diálogos | P2 |

## B. Conceptos duplicados ou confusos

| # | Problema | P |
|---|---|---|
| B1 | **Persoas e Membros son dúas listas para a mesma xente** (ver §D). O usuario non ve a diferenza | P1 |
| B2 | **Dúas "administracións"**: "Administración" (contas da app, só admin global, pantalla co deseño antigo e unha icona rota antes de "Horta") e a xestión de membros de cada explotación | P2 |
| B3 | **Dous modelos de tratamento**: o antigo (`Tratamento`, `services/tratamentos.py`, aínda con tests) e o novo CUE (`TratamentoFito`). A UI só usa o novo; o antigo confunde no código | P3 |
| B4 | **Tarefas: "Data" e "Data límite"** sen explicar a diferenza; e o estado "feita" fai de histórico, pero non se ve en ningún sitio como historial | P2 |
| B5 | **Cultivo: catro datas** (sementeira, plantación, colleita prevista, colleita real) e unha "cantidade" única; non encaixa con varias colleitas (ver análise de campos §3–4) | P1 |
| B6 | Fertilización vai sempre a **un só cultivo** e co modelo antigo (dose en texto) | P1 |

## C. Pantalla a pantalla

**Entrada (login)**: só email e contrasinal. **Non hai rexistro de usuarios novos** (as contas só as crea un administrador) nin **recuperación de contrasinal**. Para unha app pensada para "todo o mundo" isto é un bloqueo — P1. O email distingue maiúsculas e espazos (tarefa 028) — P1.

**Resumo**: etiqueta do tipo de explotación e "Para estar en regra" ben. As catro cifras (parcelas, cultivos, animais, tarefas) teñen o estilo antigo (sombra) e non se poden premer para ir á sección — P3. "Tarefas de hoxe" e "Próximas actividades" amosan datas AAAA-MM-DD — P2. Non hai avisos útiles (ROPO a caducar, tratamentos sen completar para o CUE, colleitas previstas) — P2.

**Parcelas**: táboa con nome, superficie (sen unidade) e estado. O formulario non deixa encher SIGPAC, secano/regadío nin uso, que xa están no modelo. Non hai mapa. Dende unha parcela non se ven os seus cultivos — P2.

**Cultivos**: "Novo cultivo" só parcela/especie/variedade a man; editar ten 12 campos nunha columna; non usa o catálogo oficial nin pide superficie (ver análise de campos §3) — P1.

**Tratamentos**: asistente en 5 pasos correcto e conforme ao CUE. Faltan: ver o detalle dun tratamento, editalo ou completalo, buscador/filtro por cultivo e data — P2.

**Fertilización**: modelo antigo; "Nova fertilización" con selectores sen nome — P1 (refacer na fase 2 do caderno).

**Tarefas**: correcta pero básica; sen persoa asignada; "Marcar feita/pendente" só despois de marcar a fila — P2.

**Animais**: especie e raza en texto libre; só "cantidade" (sen entradas/saídas) — P2.

**Persoas / Membros**: ver §D.

**Maquinaria**: só "Nova máquina"; **non se pode editar nin dar de baixa** dende a UI — P1.

**Administración**: deseño antigo, icona rota, sen volver á explotación; só para o admin global — P2.

**Móbil**: menú aberto tapando todo (A1); táboas con desprazamento (A10) — P1.

## D. Equipo (substitúe Persoas e Membros) — decidido o nome "Equipo"

Situación: `Persoa` (nome, NIF, aplicador/asesor, ROPO, REGFER) e `HortaMembro` (usuario + rol admin/editor/lector) non teñen relación. Quen aplica tratamentos e usa a app ten que estar nas dúas listas.

Proposta (pendente de aprobar o deseño detallado):
- Unha sección **Equipo** cunha soa táboa: nome, funcións (titular, traballador, aplicador, asesor), carné ROPO, **acceso á app** (sen acceso / só mirar / editar / administrador).
- `Persoa` gaña un `usuario_id` opcional; o acceso segue gardándose en `HortaMembro` (fronteira de seguridade intacta), pero na UI vese e xestiónase dende a persoa.
- Migración: cada membro actual pasa a ser unha persoa ligada á súa conta; as persoas actuais quedan sen acceso.
- Unha persoa sen funcións pero con acceso (p.ex. xestora) tamén vai no Equipo.

## F. Xornadas reais (probadas no móbil, 390 px)

**1. "Sementei leitugas e quero apuntalo"** — unhas 10 accións:
menú → Cultivos (o menú segue aberto tapando, hai que pechalo) → Novo cultivo → parcela, "leituga" a man → Crear → **a páxina recárgase e o menú volve abrirse tapando a táboa** → pechar menú → marcar a caixa da fila → Editar → buscar a data de sementeira entre 10 campos → Gardar (e outra vez o menú).
Achados: F1 o menú reábrese despois de **cada** gardado no móbil (P1, mesma causa ca A1); F2 o texto escrito queda tal cal ("leituga" en minúscula, sen catálogo); F3 non se pode apuntar a data ao crear.

**2. "Acabo de sulfatar e apúntoo dende o campo"**:
**O formulario de tratamentos sae cortado pola esquerda no móbil** (`ui.card().style("min-width: 40rem")` en `tratamentos_fito.py`: 640 px nunha pantalla de 390). Non se ven as etiquetas nin o botón enteiro: **non se pode usar no campo** (P1). Ademais: non hai "repetir o último tratamento" (no campo repítense moito), e cada vez hai que escoller cultivo, problema, produto, aplicador e máquina.

**3. "Collín 20 kg de patacas"**: non hai onde apuntalo agás o campo "cantidade" do cultivo (unha soa vez). Sen colleitas non hai lotes, nin vendas, nin rendemento (P1, ver análise de campos §4).

**4. "Vendín na feira"** e **"Chega unha inspección e pídenme o caderno"**: non hai vendas nin exportación do caderno (P1 antes do 1/1/2027).

**5. "Son traballador, non administrador"**: queda por probar co rol editor/lector que ve e que non (pendente).

## G. Administración (petición do usuario: "hai que poder xestionar máis cousas que só os usuarios")

Hoxe só ten a lista de contas, co deseño antigo. O administrador da plataforma debería poder:
- **Contas**: crear, desactivar, restablecer contrasinal; ver as altas novas cando haxa rexistro aberto.
- **Explotacións**: ver todas (nome, tipo, membros, última actividade) para dar soporte; nunca editar os seus datos sen permiso.
- **Catálogos oficiais**: ver que versión de cada catálogo do FEGA está cargada e de que data, importar os novos ficheiros dende a web (hoxe só por consola) e ver o informe de altas/baixas/cambios.
- **Capa galega**: nomes galegos dos cultivos e variedades locais (hoxe só por CSV).
- **Fontes de datos**: estado das descargas do MAPA (fitosanitarios, prezos) e avisos da Estación Fitopatolóxica do Areeiro, cando estean.
- **Copias de seguridade** e **rexistro de actividade** (quen cambiou que), útil para soporte e auditoría.
- Mesmo menú lateral e mesmo deseño ca o resto da app.

## Revisión 2 (mesmo día)

Comprobado no código: menú `left_drawer(value=True)` (A1); as cifras do Resumo son `ui.card` sen ligazón (C); `persoas.py` e `maquinaria.py` poñen o botón "Novo" despois da táboa e o resto de seccións antes (A3); Quasar sen galego (A4, corrixido arriba); o servizo antigo `tratamentos.py` só se usa xa nos tests (B3).

## E. Orde proposta

1. **Xa en cola** (smoth): 024 anchos, 025 calendario, 026 catálogos, 027 hectáreas, 028 email.
2. **Arranxos transversais P1 pequenos**: A1/F1 menú móbil, **F-2 formulario de tratamentos no móbil**, A4 idioma das táboas, A5 textos en vez de valores internos, maquinaria editable.
3. **Patrón único de listas** (A2, A3, A12): premer a fila abre o detalle/edición; botón "Novo" sempre no mesmo sitio; mesmo diálogo para crear e editar. Primeiro deseño (Claude) e despois tarefas para smoth sección a sección.
4. **Equipo** (§D).
5. **Cultivo completo + Colleitas** (análise de campos §3–4).
6. **Rexistro de usuarios e recuperación de contrasinal** (C, entrada) — require escoller unha solución madura (CLAUDE.md: non facelo a man).
7. **Administración ampliada** (§G).
8. Resto da análise de campos (parcela, fertilización, animais...).

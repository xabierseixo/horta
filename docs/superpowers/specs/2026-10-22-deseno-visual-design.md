# Deseño visual «Caderno de campo» e menú lateral (deseño)

Data: 2026-10-22 · Estado: **aprobado** (maqueta aprobada por Xabier: https://claude.ai/artifact/8NSVYkyc3fgAiBooZWxcUf)

## Obxectivo

Substituír as 10 pestanas en fila por un **menú lateral** con seccións agrupadas e dar á app un estilo propio, sobrio e lexible no campo, implementado con compoñentes nativos de NiceGUI/Quasar (sen librarías JS novas, CLAUDE.md).

## Navegación

- Menú lateral (`ui.left_drawer`, 248 px, `show-if-above`): fixo no ordenador; no móbil pregase e ábrese co botón ☰ da cabeceira.
- Contido do menú, de arriba abaixo: marca «Horta» (ligazón a `/`), selector de explotación (cambia de horta mantendo a sección), **Resumo**, grupos **Terra** (Parcelas, Cultivos), **Caderno** (Tratamentos, Fertilización, Tarefas), **Gandaría** (Animais), **Equipo** (Persoas, Maquinaria, Membros — só admin da horta), e ao pé o usuario con «Administración» (só admin global) e «Pechar sesión».
- **Cada sección ten a súa URL**: `/hortas/{id}/{seccion}` con `seccion` ∈ `resumo, parcelas, cultivos, tratamentos, fertilizacion, tarefas, animais, persoas, maquinaria, membros`. `/hortas/{id}` redirixe a `/hortas/{id}/resumo`. Sección descoñecida → resumo. A sección actual queda marcada no menú.
- «Configurar horta» pasa a un botón na cabeceira da sección Resumo (só admin da horta).

## Tokens de estilo

| Token | Valor | Uso |
|---|---|---|
| `--cor-primaria` | `#2F7D4F` | accións principais, elemento activo do menú |
| `--cor-primaria-escura` | `#1F5C38` | hover, texto sobre fondo verde claro |
| `--cor-menu` | `#1F3A2B` | fondo do menú lateral e da cabeceira móbil |
| `--cor-menu-texto` | `#DCE8DF` | texto do menú |
| `--cor-menu-suave` | `#A9C2B1` | títulos de grupo do menú |
| `--cor-fondo` | `#F4F6F3` | fondo da páxina |
| `--cor-superficie` | `#FFFFFF` | tarxetas, táboas, paneis |
| `--cor-bordo` | `#E1E7E2` | bordos de tarxetas e táboas |
| `--cor-texto` | `#1C2B22` | texto principal |
| `--cor-texto-suave` | `#5B6B60` | texto secundario |
| `--cor-ok-fondo` / `--cor-ok-texto` | `#E3F2E7` / `#1F5C38` | etiqueta «Completo» |
| `--cor-aviso-fondo` / `--cor-aviso-texto` / `--cor-aviso-bordo` | `#FFF4E0` / `#6B4300` / `#F0C98A` | avisos e «Faltan datos» |
| `--cor-erro` | `#B3261E` | accións destrutivas |

Tipografía: **Inter** (Google Fonts) 400/500/600/700; títulos de sección 28 px/700; texto 14–15 px. Raio 8 px (controis) e 12 px (tarxetas). Obxectivos táctiles ≥ 44 px.

## Compoñentes (clases CSS globais en `ui/tema.py`)

- `.tarxeta`: fondo branco, bordo, raio 12, padding 16–18.
- `.cifra` (tarxeta de cifra rápida): etiqueta suave + número 28 px/700.
- `.etiqueta-ok`, `.etiqueta-aviso`: pílulas de estado.
- `.aviso`: banda de aviso (fondo aviso, bordo, raio 10).
- Táboas: `ui.table(...).classes("w-full taboa")` con props `flat bordered` e `no-data-label` en galego.
- Botón principal: `color=primary` (unelevated); secundario: `outline`.
- Cabeceira de sección: función `cabeceira_seccion(titulo, migas)` → devolve unha fila onde van os botóns de acción.
- Formularios longos: diálogo á dereita (`ui.dialog().props("position=right maximized")` con tarxeta de 560 px) e pasos.

## Reparto

- **Claude** (base): `ui/tema.py`, `ui/layout.py` (menú, cabeceira móbil, `cabeceira_seccion`), rutas por sección en `horta_detalle.py`, tests das funcións puras (lista de seccións, URLs).
- **smoth** (tarefas literais, unha por pantalla): aplicar `cabeceira_seccion`, clases de táboa e `no-data-label`, tarxetas e etiquetas en cada sección; páxinas de lista de hortas, login e administración co tema novo.

## Fóra

Modo escuro; iconas propias (úsanse as Material Icons de Quasar); cifras do Resumo novas (só se reestiliza o que hai).

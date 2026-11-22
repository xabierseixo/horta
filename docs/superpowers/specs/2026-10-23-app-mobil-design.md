# App do móbil para o campo, sen conexión (deseño inicial)

Data: 2026-10-23 · Estado: proposta; o usuario pediu tela en conta xa.

## Problema

Na leira moitas veces non hai cobertura. A app actual (NiceGUI) debúxase no servidor: sen conexión non funciona. A competencia (Agroptima) traballa sen conexión e sincroniza despois; xFarm e oSIGris teñen app móbil.

## Decisión recomendada: app web instalable (PWA) só para o campo

- Unha **segunda interface, pequena**, feita para o móbil: apuntar en segundos o que se fai na leira — **tratamento, colleita, sementeira, tarefa feita, foto/incidencia** — e consultar o básico (que cultivo hai en cada parcela, carné ROPO, prazo de seguridade).
- **Funciona sen conexión**: garda os rexistros no propio móbil e envíaos cando volve a cobertura.
- Instálase dende o navegador (sen tendas de apps, sen custos). Faise con HTML/JS lixeiro servido pola mesma app; os catálogos que precisa descárganse ao móbil.
- A xestión completa (parcelas, equipo, informes, plan de empresa) segue na app web actual.
- Alternativas descartadas por agora: app nativa (Android/iOS: dúas apps, tendas, custo); Flutter (outra linguaxe e equipo).

## Pezas necesarias

1. **API REST** na app actual que use os mesmos servizos (os permisos seguen nos servizos): autenticación por token, ler catálogos e cultivos da explotación, enviar rexistros.
2. **Sincronización segura**: cada rexistro creado no móbil leva un **identificador propio (UUID)**; se se envía dúas veces, gárdase unha soa (idempotente). Os rexistros regulados nunca se borran (baixa lóxica) e cada un garda **quen** o fixo: encaixa coa trazabilidade (eventos só de engadir).
3. **Conflitos**: o móbil só **engade** rexistros; as modificacións fanse na web. Así non hai conflitos de edición.

## Que implica xa (para non refacer)

- Os rexistros que se poderán crear dende o móbil (colleita, tratamento, sementeira/cultivo, tarefa) deben aceptar un **`uuid` xerado no cliente**, único. Engádese agora á colleita (tarefa 029, aínda sen facer); ao tratamento e á tarefa cando se toquen.
- `creado_por` (xa na colleita) e baixa lóxica: xa previstos.
- Os servizos reciben datos simples (dataclasses), que é o que precisará a API: xa é así nas colleitas e tratamentos.

## Fases

1. API REST + token (lectura e envío de colleitas e tarefas).
2. PWA sen conexión: colleita e tarefa feita.
3. Tratamento dende o campo (o máis valioso; require catálogos no móbil).
4. Fotos e localización como evidencias (trazabilidade).

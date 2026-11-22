# Coordinación entre axentes (Claude Code e o modelo local "ornith-88" (e "qwen-66" para tarefas independentes))

Neste repositorio traballan dous axentes de IA: **Claude Code** e un **modelo local (ornith-88: Cline + Ollama ornith en 192.168.0.88) a través de Cline**. Este ficheiro é o protocolo común. Os dous axentes o len ao comezar cada tarefa.

## Fonte de verdade

1. **git** é a única fonte de verdade do código. O que non está en commit non existe para o outro axente.
2. **`docs/estado-e-evolucion.md`**: estado do proxecto, decisións e plan de evolución.
3. **`memory-bank/activeContext.md`**: o relevo entre sesións. Di que se fixo por última vez, que quedou a medias e cal é o seguinte paso.
4. **`CLAUDE.md`**: convencións de código (as dúas ferramentas deben seguilas).

## Ao comezar unha tarefa

1. `git status` e `git log --oneline -15`. Se hai cambios sen commit doutro axente, **non os sobrescribir nin descartar**: avisar ao usuario.
2. Ler `memory-bank/activeContext.md` e contrastalo co repositorio.
3. Ler a sección relevante de `docs/estado-e-evolucion.md`.

## Ao rematar unha tarefa

1. Pasar as comprobacións: `uv run ruff check src tests`, `uv run mypy src`, `uv run pytest`. O hook `.githooks/pre-commit` faino automaticamente se está activado (ver máis abaixo).
2. **Facer commit** do traballo (pequeno e cun só propósito), con este rodapé:
   ```
   Axente: claude        (ou: Axente: ornith-88)
   ```
3. Claude actualiza `memory-bank/activeContext.md`: obxectivo, estado, ficheiros cambiados, resultado verificado das probas, problemas abertos e seguinte paso concreto.
4. `docs/estado-e-evolucion.md` e `memory-bank/activeContext.md` mantéñeos Claude. Os modelos locais non os modifican: anotan o que fixeron no apartado **Resultado** da tarefa. O orquestador desfai calquera cambio fóra dos ficheiros da tarefa.

Nunca deixar traballo sen commit ao pechar a sesión. Se está incompleto, facer commit nunha rama (`ornith/<tarefa>` ou `claude/<tarefa>`) e anotalo en `activeContext.md`.

## Ramas

- Por defecto, un axente de cada vez sobre `main`.
- Se traballan en paralelo, cada un na súa rama: `claude/<tarefa>`, `ornith/<tarefa>`. Só se fusiona en `main` cando pasan as comprobacións.

## Revisión e sincronización

- A etiqueta git **`sync/claude`** marca o último commit revisado por Claude.
- Ao comezar, Claude revisa `git log sync/claude..HEAD` (o que fixo ornith-88 dende a última vez), comproba ruff/mypy/pytest e as convencións de `CLAUDE.md`, informa dos problemas e move a etiqueta. Isto faise coa skill `/sincronizar`.
- Os cambios de esquema (modelos ou migracións) explícanse antes ao usuario, e cada migración vai no mesmo commit que o modelo que a orixina.

## Activar o hook de calidade (unha vez por clon)

```bash
uv sync                               # se o .venv está roto: rm -rf .venv && uv sync
git config core.hooksPath .githooks
```

## Cola de tarefas

As tarefas para o modelo local están en `memory-bank/tarefas/NNN-nome.md`. Claude escríbeas e lánzaas co Cline CLI nun worktree illado, ou o usuario pídellas a Cline en VS Code. Cada ficheiro ten:

- **Estado**: `pendente` → `en curso` → `feita` (ou `bloqueada`, co motivo).
- **Obxectivo**, **Ficheiros a tocar** (non tocar ningún outro), **Pasos**, **Criterios de aceptación** e **Comprobacións**.

Quen executa a tarefa:

1. Le a tarefa enteira e este ficheiro antes de empezar.
2. Fai só o que pide a tarefa e toca só os ficheiros que indica (a propia tarefa sempre se pode actualizar; calquera outro ficheiro desfaise ao integrar). Se algo non está claro ou non se pode facer, marca `bloqueada`, explica o motivo no propio ficheiro e para.
3. Pasa as comprobacións, cambia o estado a `feita`, engade un apartado **Resultado** (que se fixo e saída resumida das probas) e fai un único commit co rodapé `Axente: ornith-88`.

---
name: sincronizar
description: Sincronizarse co traballo feito polo modelo local (smoth/Cline) dende a última revisión de Claude. Usar ao comezar unha sesión ou cando o usuario diga que o modelo local fixo cambios.
---

# Sincronizar co modelo local

Segue o protocolo de `AGENTS.md`.

1. **Estado**: `git status --short` e `git log --oneline -20`. Se hai cambios sen commit, lístaos e pregunta ao usuario antes de tocalos. Nunca os descartes.
2. **Que cambiou**: se existe a etiqueta `sync/claude`, `git log --stat sync/claude..HEAD` e `git diff sync/claude..HEAD`. Se non existe, revisa os últimos commits con rodapé `Axente: smoth` ou os non feitos por Claude.
3. **Relevo**: le `memory-bank/activeContext.md` e contrasta cada afirmación co repositorio (marca o que non sexa certo).
4. **Comprobacións**: `uv run ruff check src tests`, `uv run mypy src` e `uv run pytest -q`. Se o `.venv` está roto (rutas vellas), dío; a solución é `rm -rf .venv && uv sync`, pero pide permiso antes.
5. **Revisión**: comproba os cambios contra as convencións de `CLAUDE.md` (servizos como fronteira de seguridade, `CAMPOS_EDITABLES_*`, migración no mesmo commit que o modelo, textos en galego, tests de servizo para cada regra nova) e contra `docs/estado-e-evolucion.md`.
6. **Informe** ao usuario: que fixo o modelo local, que está ben, que problemas hai (ficheiro:liña) e que propós.
7. Se o usuario confirma a revisión: `git tag -f sync/claude HEAD` e actualiza `memory-bank/activeContext.md` e, se cambia o estado, `docs/estado-e-evolucion.md`.

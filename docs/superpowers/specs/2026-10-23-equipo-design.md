# Equipo (substitúe Persoas e Membros) — deseño

Data: 2026-10-23 · Estado: nome "Equipo" e idea aprobados polo usuario; detalle segundo as fontes.

Fontes: `docs/analise-app-2026-10-23.md` §D (dúas listas para a mesma xente); `docs/campos-oficiais-anexo-v.md` Fonte 2 (oSIGris: rol, teléfono, tipo de carné, REGFER, aplicador) e Fonte 3 (plan de empresa AGADER: emprego en UTA e colectivos, formación do promotor; trazabilidade: autor dos rexistros); REA bloque 5 xerente (formación agraria, UTA, ano de inicio). `docs/modelo-datos.md`: `persoa` (← tratamento_aplicador, tratamento_asesor) e `horta_membro` (usuario ↔ horta, rol).

## Decisión

- **Unha soa lista: Equipo.** Cada fila é unha `persoa` da explotación.
- O **acceso á app** segue gardándose en `horta_membro` (fronteira de seguridade: `comprobar_rol_horta` non cambia). A persoa liga coa súa conta por `persoa.usuario_id`. Dar ou quitar acceso dende o Equipo chama a `engadir_membro` / `cambiar_rol_membro` / `quitar_membro` (mantense a regra "polo menos un administrador").
- No menú, "Persoas" e "Membros" substitúense por **Equipo** (grupo Equipo, xunto a Maquinaria).

## Campos novos de `persoa`

| Campo | Para que (fonte) |
|---|---|
| usuario_id → usuario (opcional) | ligar coa conta; acceso á app (análise §D) |
| e_titular, e_traballador (si/non) | funcións (oSIGris: dono, agricultor) |
| telefono, email | contacto (oSIGris, REA xerente) |
| vinculo: titular / familiar / asalariado / socio / externo | emprego AGADER (UTA asalariadas e familiares) |
| horas_ano | UTA = horas / 1.920 (AXE mellorado `UTA_HOURS`, AGADER Anexo III punto 3) |
| formacion_agraria | formación do promotor (AGADER punto 4; REA xerente) |
| xenero, data_nacemento, discapacidade (opcionais) | emprego en colectivos (muller, mozo, maior, discapacidade) — AGADER Anexo III punto 3 |

## Servizos (`services/equipo.py`)

- `conceder_acceso(persoa, email, rol)` (só admin): busca a conta polo email normalizado; erro se non existe ou se xa está ligada a outra persoa do equipo; crea ou cambia o `horta_membro` e liga a persoa.
- `retirar_acceso(persoa)` (só admin): quita o `horta_membro` (non se pode quitar o último admin) e desliga.
- `acceso_da_persoa(persoa) -> rol | None`.
- `uta_equipo(horta_id) -> float`: suma de horas das persoas activas / 1.920.
- Ao **crear unha explotación**, o creador entra no Equipo ligado á súa conta.

## Migración

Cada `horta_membro` existente sen persoa ligada → nova `persoa` (nome do usuario, `usuario_id`, activa). As persoas actuais quedan sen acceso.

## Pantalla

Táboa: nome, funcións, carné ROPO (caducidade), acceso. Formulario único (crear/editar): datos persoais, funcións, carné e REGFER, traballo (vínculo, horas/ano, formación), colectivo (pregable, opcional), e **acceso á app** (email + permiso; só o ven os administradores). Avisos de ROPO a caducar como agora.

## Fases futuras

- Trazabilidade: `creado_por` (usuario) nos rexistros → con `persoa.usuario_id` sábese que persoa do equipo foi.
- Plan de empresa: `uta_equipo`, vínculo e colectivos alimentan o Anexo III punto 3; formación o punto 4.
- Partes de traballo (Agroptima): horas por tarefa irán contra a persoa.
- Colleita/tarefas: "quen o fixo" poderá apuntar a unha persoa (columna opcional, sen romper nada).

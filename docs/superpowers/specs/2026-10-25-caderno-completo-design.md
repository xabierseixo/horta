# Caderno completo: todos os campos do modelo oficial (deseño)

Data: 2026-10-25 · Estado: **feito** (tarefas 055–066d, 2026-10-25). Decisión do usuario: «o caderno ten que ter todos os campos»

Fontes: modelo oficial da Xunta (7/8/2026, `docs/referencia/caderno/`), Anexo III do RD 1311/2012 (BOE consolidado), Anexo V do CUE e RD 1051/2022. A exportación (tarefas 054–054b) xa ten as 8 follas; aquí está o que a app aínda non garda e onde se vai gardar. Os campos son opcionais na app salvo onde a norma os fai obrigatorios; o Excel leva sempre todas as columnas.

## O que falta, por sección do modelo

| Sección | Campo(s) | Onde se garda | Obriga |
|---|---|---|---|
| 1.1 Explotación | enderezo, localidade, código postal, provincia, email | `horta` | modelo |
| 1.1 Titular | enderezo, localidade, código postal, provincia; tipo de representación | `persoa` (titular); `horta.tipo_representacion` | modelo |
| 1.3 Equipos | data de adquisición | `maquina.data_adquisicion` | Anexo III A.1 |
| 1.4 Asesoramento | entidade (nome, NIF, nº de identificación) e tipo de explotación en XIP (AE, PI, CP, ATRIA, AS, NO) | `horta` | Anexo III A.1 «en su caso» |
| 2.1 Parcelas | sistema de asesoramento en XIP | sae de `horta.tipo_xip` | modelo |
| 2.2 Datos ambientais | punto de captación de auga para consumo humano (na parcela si/non, distancia m, coordenadas UTM, denominación); zona específica (total/parcial, ha) | `parcela` | Anexo III A.1 f–g, art. 33–35 |
| 3.1 bis Asesorados | xustificación, medidas non químicas, asesor | xa están en `tratamento_fito` (medidas, xustificacións, asesor) | — (só falta exportalo) |
| 3.2 Semente tratada | produto (nome comercial ou materia activa) e nº de rexistro | `cultivo` | Anexo III B, CUE 1.4 |
| 3.3 Postcolleita, 3.4 Locais, 3.5 Transporte | data, que se trata (produto vexetal / local e enderezo ou ref. catastral / vehículo e matrícula), problema, cantidade tratada (t) ou volume (m³), produto (nome, nº rexistro, materia activa, tipo), cantidade usada e unidade, xustificación | táboa nova `tratamento_instalacion` (tipo: postcolleita, local, transporte) | Anexo III B «en su caso», CUE 1.2–1.3 |
| 5 Colleita comercializada | cliente: nome, NIF, enderezo, nº REAGA | `colleita` | modelo; trazabilidade (Reg. CE 178/2002 art. 18) |
| 6 Solos | metais pesados: cadmio, cobre, níquel, chumbo, cinc, mercurio, cromo (mg/kg) | `analise` | só con lodos/residuos (modelo Xunta) |
| 7 Fertilización | valor agronómico: N orgánico, ureico, nítrico, amoniacal; P₂O₅ soluble; materia orgánica (estercos); metais pesados do residuo (Cd, Cu, Ni, Pb, Zn, Hg, Cr VI, As, Cr) | `fertilizante` (o N e P detallados impórtanse do catálogo oficial cando existen) | Anexo III C; metais só con residuos do anexo VIII RD 1051/2022 |
| 7 Fertilización | asesoramento (si/non) | `horta.asesoramento_fertilizacion` | modelo |

## Orde (cada bloque: modelo + migración + formulario + columnas do Excel)

1. Explotación, titular, máquinas e asesoramento (1.1, 1.3, 1.4, 2.1).
2. Parcelas: auga e zonas (2.2).
3. Semente tratada (3.2) e 3.1 bis no Excel.
4. Tratamentos de postcolleita, locais e transporte (3.3–3.5): entidade, servizo, sección na pantalla de Tratamentos.
5. Cliente nas colleitas (5).
6. Metais pesados nas análises de solo (6).
7. Valor agronómico e metais nos abonos (7), con importación do catálogo oficial.

Cada bloque probado no navegador e en seco antes de lanzalo; ornith-88 implementa.

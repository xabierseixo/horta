# Persoas e entidades (paso 3 do deseño global)

Data: 2026-10-28 · Estado: **dentro do deseño global aprobado** («Codifica», 2026-10-28) · Desenvolve `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §2. Tarefas 082–.

## Fontes

Os campos de cada papel saen da normativa que xa usa a app:

| Papel | Campos que pide a normativa | Fonte |
|---|---|---|
| Titular (persoa ou entidade) | nome ou razón social, NIF, enderezo, teléfono, email | caderno da Xunta 1.1; REA |
| Representante (cando o titular é unha entidade) | nome e apelidos, NIF, enderezo; tipo de representación | caderno 1.1 «Titular ou representante» |
| Aplicador e asesor | NIF, ROPO (número, tipo, caducidade), REGFER | caderno 1.2; RD 1311/2012 |
| Empresa de servizos | razón social, NIF, ROPO ou REGFER | caderno 1.2; CUE 9 (fertilización) |
| Entidade de asesoramento | nome, NIF, nº de identificación | caderno 1.4 |
| Cliente (quen merca) | NIF, nome e apelidos ou razón social, enderezo, provincia, concello (INE), CP, país, nº de rexistro dixital | CUE 3 (`ComercializacionVD`); Decreto 125/2014, art. 6 |
| Provedor de abono | nome, e un de NIF, REGA ou NIMA | CUE 9 |
| Provedor de medicamento | nome e enderezo | Reg. (UE) 2019/6, art. 108 |
| Veterinario | nome (receita) | Reg. (UE) 2019/6; RD 666/2023 |
| Outra explotación (gando) | titular e REGA | RD 787/2023, anexo V; CUE 12 |
| Laboratorio | nome e NIF | CUE 13 |
| Arrendador | NIF | REA (réxime de tenencia) |

**Na vida real** a mesma persoa fai varios papeis:
- o veciño que axuda e merca ovos;
- a ADSG, que é asesoría e veterinaria;
- a cooperativa, que vende o abono e merca a colleita.

Por iso hai unha soa lista con papeis, e non unha lista por papel.

## Que garda

**`persoa`** (ampliada):

| Campo | Novo | Para que |
|---|---|---|
| `tipo` | si | `persoa` ou `entidade` |
| `nome`, `apelidos`, `nif` | | o NIF valídase como persoa (DNI/NIE) ou como entidade (CIF) segundo o tipo |
| `enderezo`, `localidade`, `codigo_postal`, `provincia`, `telefono`, `email` | | |
| `concello_codigo` | si | código INE do concello (CUE 3) |
| `pais` | si | país, se non é España (CUE 3) |
| `rega`, `reaga`, `nima`, `rexistro_dixital`, `num_asesoramento` | si | rexistros, segundo o papel |
| `ropo_*`, `regfer_numero` | | como agora |
| datos de traballo (vínculo, horas ao ano, formación, xénero, nacemento, discapacidade) | | só para o equipo, como agora |
| `usuario_id`, `activa` | | como agora |

**`persoa_papel`** (nova): `persoa_id` e `papel`, únicos xuntos.
- **Papeis do equipo:** titular, representante, traballador, aplicador, asesor.
- **Papeis de contacto:** cliente, provedor, veterinario, laboratorio, servizos (empresa de servizos), explotacion (outra explotación).
- Os booleanos `e_titular`, `e_traballador`, `e_aplicador` e `e_asesor` pasan a esta táboa.

**Regras:**
- O aplicador precisa ROPO e caducidade.
- O asesor que é persoa precisa ROPO. A entidade de asesoramento non o precisa, pero leva o seu número.
- Só pode haber un titular activo por explotación.

**Desaparecen da explotación** os campos `titular_nome`, `titular_nif`, `asesoramento_nome`, `asesoramento_nif` e `asesoramento_num`. Quedan na explotación os datos propios: códigos, enderezo, tipo de representación, tipo de XIP e asesoramento en fertilización.

## Os sitios con texto pasan a escoller unha persoa

| Sitio | Antes | Despois |
|---|---|---|
| Explotación | titular e asesoramento | persoas cos papeis titular, representante e asesor |
| Entradas e saídas de animais | `titular`, `rega` | `outra_parte_id` (papel explotacion) |
| Pastoreo de terceiros | `rega` | `propietario_id` (papel explotacion, co REGA na súa ficha) |
| Abono (`fertilizante`) | `provedor_nome/nif/rega/nima` | `provedor_id` (papel provedor) |
| Abonado | `empresa_servizos_regfer` | **quen o fixo** (`persoa_id`) pode ser a empresa de servizos, co seu REGFER. Desaparece o campo á parte |
| Cultivo (semente ou planta) | `provedor_material` | `provedor_material_id` (papel provedor) |
| Coidado (medicamento) | `provedor`, `veterinario` | `provedor_id`, `veterinario_id` |
| Coidado (visita) | `visitante` | `visitante_id` (sen papel fixo) |
| Análise | `laboratorio`, `laboratorio_nif` | `laboratorio_id` |
| Parcela | `nif_arrendador` | `arrendador_id` |
| Colleita | `cliente_*` | **non se toca:** pasa á venda no paso 4 |

- **Paso dos datos de agora:** por cada texto créase unha persoa ou entidade nesa explotación, co seu papel e cos datos que había (NIF, REGA, NIMA, REGFER).
- **Sen duplicados:** se xa hai unha co mesmo NIF, ou co mesmo nome se non hai NIF, úsase esa e engádeselle o papel.
- O titular e o asesoramento da explotación pásanse do mesmo xeito. Se xa había unha persoa titular, complétase co NIF se lle faltaba.

## Pantallas

- **Persoas** (en Explotación, no sitio de Equipo), con dúas pestanas:
  - **Equipo:** quen ten un papel do equipo, coas horas e a UTA, como agora;
  - **Contactos:** o resto, co nome, os papeis, o NIF e o teléfono.
- **Ficha:**
  - tipo (persoa ou entidade), nome, papeis (varios) e NIF;
  - contacto e rexistros, pregados;
  - ROPO e REGFER só para aplicador, asesor e servizos;
  - os datos de traballo só para o equipo.
- **Nos formularios** (unha peza común, `ui/campo_persoa.py`):
  - un selector coas persoas que teñen ese papel, e as outras debaixo;
  - un botón «Nova», que abre unha ficha curta co nome e os datos que pide ese papel (por exemplo, o REGA para outra explotación);
  - ao gardar, a persoa queda co papel.
- **Datos da explotación:** nunha soa xanela, sen titular nin asesor. Ten unha ligazón a Persoas para indicar o titular e o asesor.
- **Inicio («para estar en regra»):** o NIF do titular sae da persoa titular, e o aviso leva a Persoas.

## Informes

- **Caderno 1.1:**
  - os datos da explotación saen do titular;
  - «Titular ou representante» é o representante se o titular é unha entidade, ou o propio titular se é unha persoa.
- **Caderno 1.2:** aplicadores, asesores e empresas de servizos.
- **Caderno 1.4:** a persoa ou entidade co papel asesor e co número de asesoramento.
- **Fertilizantes, análises e libro gandeiro:** os datos len a ficha da persoa.

## Fases futuras

- **Paso 4:** a venda escolle quen merca (cliente), e o cliente da colleita pásase alí.
- **Paso 7:** o provedor pasa á entrada de produto (compra). O provedor do abono e da semente vai alí.
- **CUE:** os datos do cliente e do provedor saen das súas fichas.

## Probas previstas

**Servizo:**
- papeis;
- NIF de persoa e de entidade;
- un só titular;
- o asesor-persoa precisa ROPO e a entidade non;
- cada sitio garda a persoa e rexeita unha doutra explotación;
- crear dende o formulario engade o papel;
- o paso de datos: textos, duplicados por NIF e por nome, titular e asesoramento;
- o caderno, as fichas 1.1, 1.2 e 1.4.

**Navegador (escritorio e móbil, copia da BD):**
- Persoas, coas pestanas Equipo e Contactos;
- crear un contacto dende unha saída de animais e dende unha análise;
- Datos da explotación;
- Inicio.

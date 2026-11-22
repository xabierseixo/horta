# Modelo de datos de horta

Xerado automaticamente das clases SQLAlchemy (`horta.db.Base.metadata`) o 2026-10-28 (tarefas ata 080j, pastoreo). Rexenerar despois de cada cambio de modelo (ver o final). Consultar **antes** de deseñar calquera tarefa que toque datos.

**Modelo de destino:** `docs/superpowers/specs/2026-10-28-deseno-global-design.md` (persoas e papeis, produtos e entradas, lotes e saídas, parte común dos traballos). Este ficheiro describe o modelo **actual**; o de destino vaise construíndo na orde de `docs/como-e-a-app.md` §5.

## Árbore principal

```
usuario ──< horta_membro >── horta  (rol na explotación: admin / editor / lector)
horta
 ├── parcela ──< cultivo ──< colleita
 │                  ├──< tratamento_cultivo >── tratamento_fito
 │                  ├──< abonado ──< abonado_boa_practica
 │                  └──< rega ──< rega_boa_practica
 ├── fertilizante ──< abonado        (os meus abonos; ← fertilizante_siex, catálogo oficial)
 ├── analise ──< analise_tipo, analise_substancia  (opcional: → parcela, cultivo, colleita/lote)
 ├── tratamento_fito ──< produto / problema / xustificacion / medida / aplicador / asesor
 ├── persoa   (aplicadores e asesores; ← tratamento_aplicador, tratamento_asesor)
 ├── maquina  (← tratamento_aplicador)
 ├── animal ──< coidado_animal  (coidados, enfermidades, produción, medicamentos, visitas; → persoa, → maquina)
 │      ├──< movemento_animal (inicial, nacemento, entrada, saída, morte; a cantidade do grupo é a súa suma)
 │      └──< producion_animal (ovos, leite, mel…; lote único xunto cos das colleitas)
 ├── pastoreo ──< pastoreo_leira (→ cultivo), pastoreo_animal (→ animal, ou REGA e especie de terceiros)
 └── tarefa   (opcional: → parcela, → cultivo, → animal, → persoa; tipo + traballo_id → o rexistro apuntado ao facela)
catalogo_version ──< catalogo_valor, cultivo_siex ──< variedade_siex, variedade_local
nome_galego (capa galega dos códigos de catálogo)
```

## Relacións lóxicas por código de catálogo (sen clave foránea)

Gárdanse como texto e valídanse con `services.catalogos.validar_codigo(catalogo, codigo, data)` contra `catalogo_valor` (catalogo, codigo), respectando data_alta/data_baixa:

| Táboa.campo | catálogo |
|---|---|
| cultivo.sistema_cultivo | sistema_cultivo |
| cultivo.sistema_explotacion | sistema_explotacion |
| cultivo.destino | destino_cultivo |
| cultivo.actividade_agraria | actividade_agraria |
| cultivo.certificacion_ecoloxica | certificacion_ecoloxica |
| cultivo.causa_baixa | causa_baixa |
| cultivo.procedencia_material | procedencia_material_vexetal |
| cultivo.tipo_cobertura_solo | tipo_cobertura_solo |
| parcela.rexime_tenencia / causa_baixa / orixe_auga | rexime_tenencia / causa_baixa / orixe_auga |
| cultivo.cultivo_anterior_codigo | cultivo_siex.codigo (sen FK) |
| colleita.destino_colleita / destino_restos | destino_colleita / destino_restos |
| tratamento_cultivo.estado_fenoloxico | estado_fenoloxico |
| tratamento_problema.codigo | praga / enfermidade / mala_herba / regulador (segundo `tipo`) |
| tratamento_xustificacion.codigo | xustificacion |
| tratamento_produto.tipo_produto / unidade | tipo_produto / unidade_medida |
| tratamento_medida.tipo_medida / boas_practicas | tipo_medida_fito / boas_practicas |
| tratamento_fito.eficacia | eficacia |
| maquina.tipo_une / tipo_enerxia | tipo_maquinaria_une / tipo_enerxia |
| fertilizante.material / tratamento_estercos | material_fertilizante / tratamento_estercos |
| fertilizante_siex.material | material_fertilizante |
| abonado.unidade | unidade_medida (só as de dose: `services.fertilizantes.UNIDADES_DOSE`) |
| abonado.tipo_fertilizacion / metodo | tipo_fertilizacion / metodo_fertilizacion |
| rega.sistema_rega / orixe_auga / tipo_enerxia / unidade | sistema_rega / orixe_auga / tipo_enerxia / unidade_medida (l ou m³) |
| rega_boa_practica.codigo | boas_practicas con «rega» en `categoria` |
| analise.material_analizado | material_analizado |
| analise_tipo.codigo / analise_substancia.codigo | tipo_analise / substancia_activa |
| abonado_boa_practica.codigo | boas_practicas con «fertilizacion» en `categoria` (ámbitos, tarefa 046c) |

## Regras que dependen das relacións

- Os permisos van sempre pola explotación: `comprobar_rol_horta(horta_id)`. Para cultivo e colleita, a explotación sácase de `parcela.horta_id`.
- Non se borran (obriga legal, baixa lóxica): tratamento_fito, colleita, abonado, rega, analise, coidado_animal. Un grupo de `animal` con coidados non se pode borrar (dáselle de baixa), nin a súa explotación; ao borrar un grupo sen coidados, as tarefas que o nomean quedan sen animal (lote 077). Tampouco se borra un grupo con entradas ou saídas (movemento_animal distinto do inicial), produción ou pastoreo; nin un cultivo, parcela ou explotación con pastoreo (lote 080). `animal.cantidade`, `data_baixa` e `estado` calcúlanse dos movementos (`services.movementos_animais.recalcular`); `animal.especie` é o nome do grupo e `especie_codigo` a especie oficial (lote 078). Non se pode borrar unha explotación, parcela ou cultivo con tratamentos CUE, abonados, regas ou colleitas; as análises (voluntarias) só perden a ligazón (os abonados: tarefas 049–049b). Ao borrar unha explotación sen abonados bórranse os seus `fertilizante`.
- Superficies en **hectáreas** (parcela.superficie, cultivo.superficie_ha, colleita.superficie_ha, tratamento_cultivo.superficie_ha, abonado.superficie_ha): cultivo ≤ parcela; colleita, tratamento e abonado ≤ cultivo.
- Lote da colleita: único dentro da explotación.

## Relacións (quen apunta a quen)

```
abonado: aplicador_persoa_id → persoa, creado_por → usuario, cultivo_id → cultivo, fertilizante_id → fertilizante, horta_id → horta, maquina_id → maquina
abonado_boa_practica: abonado_id → abonado
analise: colleita_id → colleita, creado_por → usuario, cultivo_id → cultivo, horta_id → horta, parcela_id → parcela, persoa_id → persoa
analise_substancia: analise_id → analise
analise_tipo: analise_id → analise
animal: horta_id → horta
catalogo_valor: version_id → catalogo_version
coidado_animal: animal_id → animal, creado_por → usuario, horta_id → horta, maquina_id → maquina, persoa_id → persoa
colleita: creado_por → usuario, cultivo_id → cultivo, maquina_id → maquina, persoa_id → persoa
cultivo: cultivo_siex_codigo → cultivo_siex, parcela_id → parcela, sementeira_persoa_id → persoa, variedade_local_id → variedade_local, variedade_siex_id → variedade_siex
cultivo_siex: version_id → catalogo_version
fertilizante: fertilizante_siex_codigo → fertilizante_siex, horta_id → horta
fertilizante_siex: version_id → catalogo_version
fito_materia: num_rexistro → fito_produto
fito_produto: version_id → catalogo_version
fito_uso: num_rexistro → fito_produto
horta_membro: horta_id → horta, usuario_id → usuario
labor: creado_por → usuario, cultivo_id → cultivo, horta_id → horta, maquina_id → maquina, persoa_id → persoa
maquina: horta_id → horta
movemento_animal: animal_id → animal, creado_por → usuario, horta_id → horta, persoa_id → persoa
parcela: horta_id → horta
pastoreo: creado_por → usuario, horta_id → horta, persoa_id → persoa
pastoreo_animal: animal_id → animal, pastoreo_id → pastoreo
pastoreo_leira: cultivo_id → cultivo, pastoreo_id → pastoreo
persoa: horta_id → horta, usuario_id → usuario
producion_animal: animal_id → animal, creado_por → usuario, horta_id → horta, persoa_id → persoa
rega: creado_por → usuario, cultivo_id → cultivo, horta_id → horta, persoa_id → persoa
rega_boa_practica: rega_id → rega
tarefa: animal_id → animal, cultivo_id → cultivo, horta_id → horta, parcela_id → parcela, persoa_id → persoa
tratamento_aplicador: maquina_id → maquina, persoa_id → persoa, tratamento_id → tratamento_fito
tratamento_asesor: persoa_id → persoa, tratamento_id → tratamento_fito
tratamento_cultivo: cultivo_id → cultivo, tratamento_id → tratamento_fito
tratamento_fito: horta_id → horta
tratamento_instalacion: creado_por → usuario, horta_id → horta, persoa_id → persoa
tratamento_medida: tratamento_id → tratamento_fito
tratamento_problema: tratamento_id → tratamento_fito
tratamento_produto: tratamento_id → tratamento_fito
tratamento_xustificacion: tratamento_id → tratamento_fito
variedade_local: cultivo_codigo → cultivo_siex
variedade_siex: cultivo_codigo → cultivo_siex, version_id → catalogo_version
```

## Táboas e campos

### abonado

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| cultivo_id | INTEGER | non | → cultivo.id |
| data_inicio | DATE | non |  |
| data_fin | DATE | non |  |
| superficie_ha | FLOAT | si |  |
| fertilizante_id | INTEGER | si | → fertilizante.id |
| dose | FLOAT | si |  |
| unidade | VARCHAR(20) | si |  |
| tipo_fertilizacion | VARCHAR(20) | si |  |
| metodo | VARCHAR(20) | si |  |
| xestion_sostible | BOOLEAN | non |  |
| aplicacion_lodos | BOOLEAN | non |  |
| albaran_factura | VARCHAR(50) | si |  |
| aplicador_persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| empresa_servizos_regfer | VARCHAR(50) | si |  |
| maquina_id | INTEGER | si | → maquina.id |
| num_repeticions | INTEGER | si |  |
| duracion_h_ha | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

Apuntan aquí: abonado_boa_practica.abonado_id

### abonado_boa_practica

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| abonado_id | INTEGER | non | → abonado.id |
| codigo | VARCHAR(20) | non |  |

### analise

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| material_analizado | VARCHAR(20) | non |  |
| data_mostraxe | DATE | non |  |
| laboratorio | VARCHAR(150) | si |  |
| laboratorio_nif | VARCHAR(9) | si |  |
| num_boletin | VARCHAR(50) | si |  |
| parcela_id | INTEGER | si | → parcela.id |
| cultivo_id | INTEGER | si | → cultivo.id |
| colleita_id | INTEGER | si | → colleita.id |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| materia_organica | FLOAT | si |  |
| area | FLOAT | si |  |
| limo | FLOAT | si |  |
| arxila | FLOAT | si |  |
| ph | FLOAT | si |  |
| fosforo_ppm | FLOAT | si |  |
| potasio_ppm | FLOAT | si |  |
| n_total | FLOAT | si |  |
| conductividade | FLOAT | si |  |
| cadmio | FLOAT | si |  |
| cobre | FLOAT | si |  |
| niquel | FLOAT | si |  |
| chumbo | FLOAT | si |  |
| zinc | FLOAT | si |  |
| mercurio | FLOAT | si |  |
| cromo | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

Apuntan aquí: analise_substancia.analise_id, analise_tipo.analise_id

### analise_substancia

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| analise_id | INTEGER | non | → analise.id |
| codigo | VARCHAR(20) | non |  |

### analise_tipo

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| analise_id | INTEGER | non | → analise.id |
| codigo | VARCHAR(20) | non |  |

### animal

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| especie | VARCHAR(80) | non |  |
| especie_codigo | VARCHAR(20) | si |  |
| raza | VARCHAR(120) | si |  |
| cantidade | INTEGER | non |  |
| data_alta | DATE | non |  |
| data_baixa | DATE | si |  |
| estado | VARCHAR(50) | non |  |
| notas | VARCHAR(1000) | si |  |
| created_at | DATETIME | non |  |

Apuntan aquí: coidado_animal.animal_id, movemento_animal.animal_id, pastoreo_animal.animal_id, producion_animal.animal_id, tarefa.animal_id

### catalogo_valor

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| catalogo | VARCHAR(60) | non |  |
| codigo | VARCHAR(20) | non |  |
| descricion | VARCHAR(500) | non |  |
| codigo_eppo | VARCHAR(12) | si |  |
| categoria | VARCHAR(120) | si |  |
| data_alta | DATE | si |  |
| data_baixa | DATE | si |  |
| version_id | INTEGER | non | → catalogo_version.id |

### catalogo_version

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| catalogo | VARCHAR(60) | non |  |
| nome_ficheiro | VARCHAR(255) | non |  |
| sha256 | VARCHAR(64) | non |  |
| filas | INTEGER | non |  |
| data_importacion | DATETIME | non |  |

Apuntan aquí: catalogo_valor.version_id, cultivo_siex.version_id, fertilizante_siex.version_id, fito_produto.version_id, variedade_siex.version_id

### coidado_animal

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| animal_id | INTEGER | non | → animal.id |
| data_inicio | DATE | non |  |
| data_fin | DATE | non |  |
| tipo | VARCHAR(20) | non |  |
| descricion | VARCHAR(500) | si |  |
| num_animais | INTEGER | si |  |
| identificacion | VARCHAR(500) | si |  |
| medicamento | VARCHAR(250) | si |  |
| cantidade | FLOAT | si |  |
| unidade | VARCHAR(20) | si |  |
| provedor | VARCHAR(300) | si |  |
| proba_compra | VARCHAR(100) | si |  |
| veterinario | VARCHAR(200) | si |  |
| receita | VARCHAR(50) | si |  |
| tempo_espera_dias | INTEGER | si |  |
| duracion_dias | INTEGER | si |  |
| visitante | VARCHAR(200) | si |  |
| matricula | VARCHAR(20) | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| maquina_id | INTEGER | si | → maquina.id |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

### colleita

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| cultivo_id | INTEGER | non | → cultivo.id |
| data | DATE | non |  |
| data_fin | DATE | si |  |
| cantidade | FLOAT | non |  |
| unidade | VARCHAR(20) | non |  |
| superficie_ha | FLOAT | si |  |
| lote | VARCHAR(40) | non |  |
| albaran_factura | VARCHAR(60) | si |  |
| cliente_nome | VARCHAR(200) | si |  |
| cliente_nif | VARCHAR(14) | si |  |
| cliente_enderezo | VARCHAR(250) | si |  |
| cliente_reaga | VARCHAR(20) | si |  |
| destino_colleita | VARCHAR(20) | si |  |
| destino_restos | VARCHAR(20) | si |  |
| obten_sementes | BOOLEAN | non |  |
| obten_plantas | BOOLEAN | non |  |
| sen_colleita_ambiental | BOOLEAN | non |  |
| restos_no_solo | BOOLEAN | non |  |
| maquina_id | INTEGER | si | → maquina.id |
| num_repeticions | INTEGER | si |  |
| duracion_h_ha | FLOAT | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| uuid | VARCHAR(36) | si |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

Apuntan aquí: analise.colleita_id

### comprobacion_catalogo

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| catalogo (clave) | VARCHAR(60) | non |  |
| data | DATETIME | non |  |
| erro | VARCHAR(500) | si |  |

### cultivo

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| parcela_id | INTEGER | non | → parcela.id |
| especie | VARCHAR(120) | non |  |
| variedade | VARCHAR(120) | si |  |
| cultivo_siex_codigo | INTEGER | si | → cultivo_siex.codigo |
| variedade_siex_id | INTEGER | si | → variedade_siex.id |
| variedade_local_id | INTEGER | si | → variedade_local.id |
| data_colleita_prevista | DATE | si |  |
| notas | VARCHAR(1000) | si |  |
| estado | VARCHAR(50) | non |  |
| superficie_ha | FLOAT | si |  |
| tipo_inicio | VARCHAR(12) | si |  |
| data_inicio | DATE | si |  |
| data_fin | DATE | si |  |
| causa_baixa | VARCHAR(20) | si |  |
| sistema_cultivo | VARCHAR(20) | si |  |
| sistema_explotacion | VARCHAR(20) | si |  |
| destino | VARCHAR(20) | si |  |
| actividade_agraria | VARCHAR(20) | si |  |
| certificacion_ecoloxica | VARCHAR(20) | si |  |
| data_inicio_conversion | DATE | si |  |
| producion_integrada | BOOLEAN | non |  |
| procedencia_material | VARCHAR(20) | si |  |
| provedor_material | VARCHAR(200) | si |  |
| lote_material | VARCHAR(40) | si |  |
| pasaporte_fitosanitario | VARCHAR(40) | si |  |
| ropveg | VARCHAR(20) | si |  |
| num_arbores | INTEGER | si |  |
| marco_plantacion | VARCHAR(20) | si |  |
| ano_plantacion | INTEGER | si |  |
| unidades_produtivas | INTEGER | si |  |
| ciclos_ano | INTEGER | si |  |
| duracion_ciclo_dias | INTEGER | si |  |
| cultivo_anterior_codigo | INTEGER | si |  |
| obxectivo_colleita_kg_ha | FLOAT | si |  |
| plan_necesidade_n | FLOAT | si |  |
| plan_necesidade_p2o5 | FLOAT | si |  |
| plan_necesidade_k2o | FLOAT | si |  |
| plan_ferramenta_sostibilidade | BOOLEAN | non |  |
| plan_data | DATE | si |  |
| plan_auga_n_nitrico | FLOAT | si |  |
| plan_auga_p2o5 | FLOAT | si |  |
| tipo_mvr | VARCHAR(20) | si |  |
| detalle_mvr | VARCHAR(20) | si |  |
| empresa_semente | VARCHAR(20) | si |  |
| sementeira_directa | BOOLEAN | non |  |
| tipo_cobertura_solo | VARCHAR(20) | si |  |
| num_castineiros | INTEGER | si |  |
| num_abeleiras | INTEGER | si |  |
| num_nogueiras | INTEGER | si |  |
| num_amendoeiras | INTEGER | si |  |
| num_outros_froitos_casca | INTEGER | si |  |
| data_fin_sementeira | DATE | si |  |
| cantidade_semente_kg | FLOAT | si |  |
| dose_sementeira_kg_ha | FLOAT | si |  |
| densidade_plantas_ha | FLOAT | si |  |
| material_tratado | BOOLEAN | non |  |
| semente_tratamento_produto | VARCHAR(250) | si |  |
| semente_tratamento_num_rexistro | VARCHAR(50) | si |  |
| material_adquirido | BOOLEAN | non |  |
| data_adquisicion_material | DATE | si |  |
| sementeira_persoa_id | INTEGER | si | → persoa.id |
| sementeira_horas | FLOAT | si |  |
| created_at | DATETIME | non |  |

Apuntan aquí: abonado.cultivo_id, analise.cultivo_id, colleita.cultivo_id, labor.cultivo_id, pastoreo_leira.cultivo_id, rega.cultivo_id, tarefa.cultivo_id, tratamento_cultivo.cultivo_id

### cultivo_siex

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| codigo (clave) | INTEGER | non |  |
| nome_oficial | VARCHAR(200) | non |  |
| nome_latin | VARCHAR(200) | si |  |
| codigo_eppo | VARCHAR(12) | si |  |
| codigo_upov | VARCHAR(40) | si |  |
| horticola | BOOLEAN | non |  |
| integrado | BOOLEAN | non |  |
| data_alta | DATE | si |  |
| data_baixa | DATE | si |  |
| version_id | INTEGER | non | → catalogo_version.id |

Apuntan aquí: cultivo.cultivo_siex_codigo, variedade_local.cultivo_codigo, variedade_siex.cultivo_codigo

### fertilizante

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| nome | VARCHAR(250) | non |  |
| material | VARCHAR(20) | non |  |
| fertilizante_siex_codigo | INTEGER | si | → fertilizante_siex.codigo |
| n_pct | FLOAT | si |  |
| p2o5_pct | FLOAT | si |  |
| k2o_pct | FLOAT | si |  |
| n_organico_pct | FLOAT | si |  |
| n_ureico_pct | FLOAT | si |  |
| n_nitrico_pct | FLOAT | si |  |
| n_amoniacal_pct | FLOAT | si |  |
| p2o5_soluble_pct | FLOAT | si |  |
| materia_organica_pct | FLOAT | si |  |
| cadmio | FLOAT | si |  |
| cobre | FLOAT | si |  |
| niquel | FLOAT | si |  |
| chumbo | FLOAT | si |  |
| zinc | FLOAT | si |  |
| mercurio | FLOAT | si |  |
| cromo_vi | FLOAT | si |  |
| arsenico | FLOAT | si |  |
| cromo | FLOAT | si |  |
| liquido | BOOLEAN | non |  |
| densidade | FLOAT | si |  |
| tratamento_estercos | VARCHAR(20) | si |  |
| provedor_nome | VARCHAR(150) | si |  |
| provedor_nif | VARCHAR(14) | si |  |
| provedor_rega | VARCHAR(14) | si |  |
| provedor_nima | VARCHAR(50) | si |  |
| activo | BOOLEAN | non |  |
| created_at | DATETIME | non |  |

Apuntan aquí: abonado.fertilizante_id

### fertilizante_siex

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| codigo (clave) | INTEGER | non |  |
| material | VARCHAR(20) | non |  |
| clase | VARCHAR(60) | si |  |
| subclase | VARCHAR(60) | si |  |
| nome | VARCHAR(300) | non |  |
| fabricante | VARCHAR(200) | si |  |
| n_pct | FLOAT | non |  |
| p2o5_pct | FLOAT | non |  |
| k2o_pct | FLOAT | non |  |
| n_organico_pct | FLOAT | non |  |
| n_ureico_pct | FLOAT | non |  |
| n_nitrico_pct | FLOAT | non |  |
| n_amoniacal_pct | FLOAT | non |  |
| p2o5_soluble_pct | FLOAT | non |  |
| liquido | BOOLEAN | non |  |
| densidade | FLOAT | si |  |
| inhibidor_nitrificacion | BOOLEAN | non |  |
| inhibidor_ureasa | BOOLEAN | non |  |
| data_baixa | DATE | si |  |
| version_id | INTEGER | non | → catalogo_version.id |

Apuntan aquí: fertilizante.fertilizante_siex_codigo

### fito_materia

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| num_rexistro | VARCHAR(20) | non | → fito_produto.num_rexistro |
| sustancia | VARCHAR(200) | non |  |
| concentracion | FLOAT | si |  |
| unidade | VARCHAR(40) | si |  |

### fito_ponte_axente

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| catalogo | VARCHAR(20) | non |  |
| codigo | VARCHAR(20) | non |  |
| codigo_agente | VARCHAR(30) | non |  |

### fito_ponte_cultivo

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| cultivo_siex_codigo | INTEGER | non |  |
| codigo_cultivo | VARCHAR(16) | non |  |

### fito_produto

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| num_rexistro (clave) | VARCHAR(20) | non |  |
| nome | VARCHAR(200) | non |  |
| titular | VARCHAR(200) | si |  |
| estado | VARCHAR(20) | si |  |
| data_caducidade | DATE | si |  |
| data_cancelacion | DATE | si |  |
| data_limite_venda | DATE | si |  |
| version_id | INTEGER | non | → catalogo_version.id |

Apuntan aquí: fito_materia.num_rexistro, fito_uso.num_rexistro

### fito_uso

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| num_rexistro | VARCHAR(20) | non | → fito_produto.num_rexistro |
| codigo_cultivo | VARCHAR(16) | non |  |
| cultivo | VARCHAR(200) | non |  |
| codigo_agente | VARCHAR(30) | non |  |
| agente | VARCHAR(300) | non |  |
| tipo_usuario | VARCHAR(20) | si |  |
| sistema_cultivo | VARCHAR(40) | si |  |
| dose_min | FLOAT | si |  |
| dose_max | FLOAT | si |  |
| unidade_dose | VARCHAR(60) | si |  |
| ps_tipo | VARCHAR(20) | non |  |
| ps_dias | INTEGER | si |  |
| aplicacions_max | INTEGER | si |  |
| intervalo_min_dias | INTEGER | si |  |
| condicionamento | VARCHAR(2000) | si |  |

### horta

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| nome | VARCHAR(120) | non |  |
| descricion | VARCHAR(500) | si |  |
| uso_profesional | BOOLEAN | non |  |
| titular_nome | VARCHAR(200) | si |  |
| titular_nif | VARCHAR(9) | si |  |
| codigo_reaga | VARCHAR(14) | si |  |
| codigo_rega | VARCHAR(14) | si |  |
| lat | FLOAT | si |  |
| lon | FLOAT | si |  |
| telefono | VARCHAR(30) | si |  |
| enderezo | VARCHAR(200) | si |  |
| localidade | VARCHAR(100) | si |  |
| codigo_postal | VARCHAR(10) | si |  |
| provincia | VARCHAR(50) | si |  |
| email | VARCHAR(200) | si |  |
| tipo_representacion | VARCHAR(100) | si |  |
| asesoramento_nome | VARCHAR(200) | si |  |
| asesoramento_nif | VARCHAR(14) | si |  |
| asesoramento_num | VARCHAR(50) | si |  |
| tipo_xip | VARCHAR(10) | si |  |
| asesoramento_fertilizacion | BOOLEAN | non |  |
| foto_perfil | VARCHAR(500) | si |  |
| ultima_conexion | DATETIME | si |  |
| created_at | DATETIME | non |  |

Apuntan aquí: abonado.horta_id, analise.horta_id, animal.horta_id, coidado_animal.horta_id, fertilizante.horta_id, horta_membro.horta_id, labor.horta_id, maquina.horta_id, movemento_animal.horta_id, parcela.horta_id, pastoreo.horta_id, persoa.horta_id, producion_animal.horta_id, rega.horta_id, tarefa.horta_id, tratamento_fito.horta_id, tratamento_instalacion.horta_id

### horta_membro

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| horta_id (clave) | INTEGER | non | → horta.id |
| usuario_id (clave) | INTEGER | non | → usuario.id |
| rol | VARCHAR(6) | non |  |

### labor

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| cultivo_id | INTEGER | non | → cultivo.id |
| data_inicio | DATE | non |  |
| data_fin | DATE | non |  |
| superficie_ha | FLOAT | si |  |
| tipo_labor | VARCHAR(20) | non |  |
| restos_desbroce_no_solo | BOOLEAN | non |  |
| restos_poda_no_solo | BOOLEAN | non |  |
| tipo_cobertura | VARCHAR(20) | si |  |
| maquina_id | INTEGER | si | → maquina.id |
| num_repeticions | INTEGER | si |  |
| duracion_h | FLOAT | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

### maquina

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| alias | VARCHAR(120) | non |  |
| tipo_une | VARCHAR(20) | si |  |
| marca_modelo | VARCHAR(200) | si |  |
| num_roma | VARCHAR(12) | si |  |
| num_reganip | VARCHAR(12) | si |  |
| id_equipo_non_inscribible | VARCHAR(50) | si |  |
| propia | BOOLEAN | non |  |
| potencia | FLOAT | si |  |
| unidade_potencia | VARCHAR(20) | si |  |
| tipo_enerxia | VARCHAR(20) | si |  |
| data_ultima_inspeccion | DATE | si |  |
| data_adquisicion | DATE | si |  |
| alugada | BOOLEAN | non |  |
| activa | BOOLEAN | non |  |

Apuntan aquí: abonado.maquina_id, coidado_animal.maquina_id, colleita.maquina_id, labor.maquina_id, tratamento_aplicador.maquina_id

### movemento_animal

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| animal_id | INTEGER | non | → animal.id |
| data | DATE | non |  |
| tipo | VARCHAR(20) | non |  |
| cantidade | INTEGER | non |  |
| identificacion | VARCHAR(500) | si |  |
| titular | VARCHAR(300) | si |  |
| rega | VARCHAR(20) | si |  |
| codigo_movemento | VARCHAR(50) | si |  |
| causa | VARCHAR(300) | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

### nome_galego

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| catalogo | VARCHAR(60) | non |  |
| codigo | VARCHAR(20) | non |  |
| nome_gl | VARCHAR(200) | non |  |
| prioridade | INTEGER | non |  |

### parcela

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| nome | VARCHAR(120) | non |  |
| descricion | VARCHAR(500) | si |  |
| superficie | FLOAT | si |  |
| posicion | VARCHAR(120) | si |  |
| lat | FLOAT | si |  |
| lon | FLOAT | si |  |
| uso_aproveitamento | VARCHAR(120) | si |  |
| secano_regadio | VARCHAR(7) | si |  |
| sigpac_provincia | VARCHAR(10) | si |  |
| sigpac_concello | VARCHAR(10) | si |  |
| sigpac_poligono | VARCHAR(10) | si |  |
| sigpac_parcela | VARCHAR(10) | si |  |
| sigpac_subparcela | VARCHAR(10) | si |  |
| sigpac_agregado | VARCHAR(10) | si |  |
| sigpac_zona | VARCHAR(10) | si |  |
| referencia_catastral | VARCHAR(20) | si |  |
| rexime_tenencia | VARCHAR(20) | si |  |
| nif_arrendador | VARCHAR(9) | si |  |
| pequena_superficie | BOOLEAN | non |  |
| data_alta | DATE | si |  |
| data_baixa | DATE | si |  |
| causa_baixa | VARCHAR(20) | si |  |
| orixe_auga | VARCHAR(20) | si |  |
| auga_consumo | BOOLEAN | non |  |
| auga_consumo_na_parcela | BOOLEAN | non |  |
| auga_consumo_distancia_m | FLOAT | si |  |
| auga_consumo_utm | VARCHAR(50) | si |  |
| auga_consumo_denominacion | VARCHAR(150) | si |  |
| zona_especifica | VARCHAR(10) | si |  |
| zona_especifica_ha | FLOAT | si |  |
| geometria | TEXT | si |  |
| imaxe | VARCHAR(500) | si |  |
| notas | VARCHAR(1000) | si |  |
| estado | VARCHAR(50) | non |  |
| created_at | DATETIME | non |  |

Apuntan aquí: analise.parcela_id, cultivo.parcela_id, tarefa.parcela_id

### pastoreo

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| data_inicio | DATE | non |  |
| data_fin | DATE | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| uuid | VARCHAR(36) | si |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

Apuntan aquí: pastoreo_animal.pastoreo_id, pastoreo_leira.pastoreo_id

### pastoreo_animal

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| pastoreo_id | INTEGER | non | → pastoreo.id |
| animal_id | INTEGER | si | → animal.id |
| rega | VARCHAR(14) | si |  |
| especie_codigo | VARCHAR(20) | si |  |
| numero | INTEGER | non |  |

### pastoreo_leira

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| pastoreo_id | INTEGER | non | → pastoreo.id |
| cultivo_id | INTEGER | non | → cultivo.id |
| superficie_ha | FLOAT | si |  |
| tipo_cobertura | VARCHAR(20) | si |  |

### persoa

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| nome | VARCHAR(120) | non |  |
| apelidos | VARCHAR(200) | si |  |
| nif | VARCHAR(9) | si |  |
| e_aplicador | BOOLEAN | non |  |
| e_asesor | BOOLEAN | non |  |
| ropo_numero | VARCHAR(14) | si |  |
| ropo_tipo_carne | VARCHAR(20) | si |  |
| ropo_caducidade | DATE | si |  |
| regfer_numero | VARCHAR(20) | si |  |
| enderezo | VARCHAR(200) | si |  |
| localidade | VARCHAR(100) | si |  |
| codigo_postal | VARCHAR(10) | si |  |
| provincia | VARCHAR(50) | si |  |
| activa | BOOLEAN | non |  |
| usuario_id | INTEGER | si | → usuario.id |
| e_titular | BOOLEAN | non |  |
| e_traballador | BOOLEAN | non |  |
| telefono | VARCHAR(30) | si |  |
| email | VARCHAR(255) | si |  |
| vinculo | VARCHAR(20) | si |  |
| horas_ano | FLOAT | si |  |
| formacion_agraria | VARCHAR(200) | si |  |
| xenero | VARCHAR(10) | si |  |
| data_nacemento | DATE | si |  |
| discapacidade | BOOLEAN | non |  |

Apuntan aquí: abonado.aplicador_persoa_id, analise.persoa_id, coidado_animal.persoa_id, colleita.persoa_id, cultivo.sementeira_persoa_id, labor.persoa_id, movemento_animal.persoa_id, pastoreo.persoa_id, producion_animal.persoa_id, rega.persoa_id, tarefa.persoa_id, tratamento_aplicador.persoa_id, tratamento_asesor.persoa_id, tratamento_instalacion.persoa_id

### producion_animal

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| animal_id | INTEGER | non | → animal.id |
| data | DATE | non |  |
| data_fin | DATE | non |  |
| produto | VARCHAR(20) | non |  |
| cantidade | FLOAT | non |  |
| unidade | VARCHAR(20) | non |  |
| retirada | FLOAT | si |  |
| lote | VARCHAR(40) | non |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| uuid | VARCHAR(36) | si |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

### rega

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| cultivo_id | INTEGER | non | → cultivo.id |
| data_inicio | DATE | non |  |
| data_fin | DATE | non |  |
| superficie_ha | FLOAT | si |  |
| sistema_rega | VARCHAR(20) | si |  |
| cantidade | FLOAT | si |  |
| unidade | VARCHAR(20) | non |  |
| orixe_auga | VARCHAR(20) | si |  |
| tipo_enerxia | VARCHAR(20) | si |  |
| num_contador | VARCHAR(14) | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

Apuntan aquí: rega_boa_practica.rega_id

### rega_boa_practica

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| rega_id | INTEGER | non | → rega.id |
| codigo | VARCHAR(20) | non |  |

### tarefa

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| parcela_id | INTEGER | si | → parcela.id |
| cultivo_id | INTEGER | si | → cultivo.id |
| animal_id | INTEGER | si | → animal.id |
| descricion | VARCHAR(300) | non |  |
| data | DATE | si |  |
| data_limite | DATE | si |  |
| data_feita | DATE | si |  |
| prioridade | VARCHAR(20) | non |  |
| estado | VARCHAR(20) | non |  |
| notas | VARCHAR(1000) | si |  |
| tipo | VARCHAR(30) | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| traballo_id | INTEGER | si |  |
| created_at | DATETIME | non |  |

### tratamento_aplicador

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| persoa_id | INTEGER | non | → persoa.id |
| maquina_id | INTEGER | si | → maquina.id |
| aplicacion_manual | BOOLEAN | non |  |
| horas_utilizacion | FLOAT | si |  |
| num_repeticions | INTEGER | si |  |
| duracion | FLOAT | si |  |

### tratamento_asesor

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| persoa_id | INTEGER | non | → persoa.id |
| data | DATE | si |  |
| validacion | BOOLEAN | non |  |
| observacions | VARCHAR(200) | si |  |
| confirmacion | BOOLEAN | non |  |
| contrato | BOOLEAN | non |  |

### tratamento_cultivo

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| cultivo_id | INTEGER | non | → cultivo.id |
| superficie_ha | FLOAT | si |  |
| estado_fenoloxico | VARCHAR(20) | si |  |

### tratamento_fito

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| data_inicio | DATE | non |  |
| data_fin | DATE | non |  |
| hora | TIME | si |  |
| actividade_cuberta | VARCHAR(20) | si |  |
| eficacia | VARCHAR(20) | si |  |
| observacions | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| created_at | DATETIME | non |  |
| orixinal_produto | VARCHAR(200) | si |  |
| orixinal_dose | VARCHAR(100) | si |  |
| orixinal_aplicador | VARCHAR(200) | si |  |
| orixinal_equipo | VARCHAR(200) | si |  |
| orixinal_asesoramento | VARCHAR(200) | si |  |
| tratamento_antigo_id | INTEGER | si |  |

Apuntan aquí: tratamento_aplicador.tratamento_id, tratamento_asesor.tratamento_id, tratamento_cultivo.tratamento_id, tratamento_medida.tratamento_id, tratamento_problema.tratamento_id, tratamento_produto.tratamento_id, tratamento_xustificacion.tratamento_id

### tratamento_instalacion

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| horta_id | INTEGER | non | → horta.id |
| tipo | VARCHAR(20) | non |  |
| data | DATE | non |  |
| obxecto | VARCHAR(250) | non |  |
| referencia_catastral | VARCHAR(30) | si |  |
| problema_tipo | VARCHAR(20) | si |  |
| problema_codigo | VARCHAR(20) | si |  |
| xustificacion | VARCHAR(20) | si |  |
| cantidade_tratada | FLOAT | si |  |
| tipo_produto | VARCHAR(20) | si |  |
| nome_comercial | VARCHAR(250) | si |  |
| num_rexistro | VARCHAR(50) | si |  |
| materia_activa | VARCHAR(250) | si |  |
| cantidade_utilizada | FLOAT | si |  |
| unidade | VARCHAR(20) | si |  |
| persoa_id | INTEGER | si | → persoa.id |
| horas | FLOAT | si |  |
| notas | VARCHAR(1000) | si |  |
| baixa | BOOLEAN | non |  |
| creado_por | INTEGER | si | → usuario.id |
| created_at | DATETIME | non |  |

### tratamento_medida

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| tipo_medida | VARCHAR(20) | non |  |
| cantidade | FLOAT | si |  |
| unidade | VARCHAR(20) | si |  |
| num_rexistro_mdf | VARCHAR(10) | si |  |
| boas_practicas | VARCHAR(20) | si |  |

### tratamento_problema

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| tipo | VARCHAR(20) | non |  |
| codigo | VARCHAR(20) | non |  |

### tratamento_produto

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| tipo_produto | VARCHAR(20) | non |  |
| num_rexistro | VARCHAR(20) | si |  |
| nome_comercial | VARCHAR(200) | si |  |
| materia_activa | VARCHAR(200) | si |  |
| dose | FLOAT | si |  |
| cantidade | FLOAT | si |  |
| unidade | VARCHAR(20) | non |  |

### tratamento_xustificacion

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| tratamento_id | INTEGER | non | → tratamento_fito.id |
| codigo | VARCHAR(20) | non |  |

### usuario

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| nome | VARCHAR(120) | non |  |
| email | VARCHAR(255) | non |  |
| password_hash | VARCHAR(255) | non |  |
| rol | VARCHAR(7) | non |  |
| activo | BOOLEAN | non |  |
| created_at | DATETIME | non |  |

Apuntan aquí: abonado.creado_por, analise.creado_por, coidado_animal.creado_por, colleita.creado_por, horta_membro.usuario_id, labor.creado_por, movemento_animal.creado_por, pastoreo.creado_por, persoa.usuario_id, producion_animal.creado_por, rega.creado_por, tratamento_instalacion.creado_por

### variedade_local

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| cultivo_codigo | INTEGER | non | → cultivo_siex.codigo |
| nome | VARCHAR(200) | non |  |
| fonte | VARCHAR(200) | si |  |
| notas | VARCHAR(1000) | si |  |

Apuntan aquí: cultivo.variedade_local_id

### variedade_siex

| Campo | Tipo | Nulo | Ligazón |
|---|---|---|---|
| id (clave) | INTEGER | non |  |
| cultivo_codigo | INTEGER | non | → cultivo_siex.codigo |
| codigo | INTEGER | non |  |
| nome_oficial | VARCHAR(300) | non |  |
| data_baixa | DATE | si |  |
| version_id | INTEGER | non | → catalogo_version.id |

Apuntan aquí: cultivo.variedade_siex_id

## Como rexenerar

```bash
uv run python -c "import horta.models; from horta.db import Base; [print(t.name, [c.name for c in t.columns]) for t in Base.metadata.sorted_tables]"
```
(o script completo que xera as táboas deste documento está en `memory-bank/xerar_modelo.md`).

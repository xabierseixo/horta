# Cultivo completo e colleitas (deseño)

Data: 2026-10-23 · Estado: **borrador, pendente de revisión do usuario**

Fontes: `docs/analise-campos-2026-10-23.md` §3–4 e revisións; `docs/analise-app-2026-10-23.md` §F (xornadas 1 e 3); descritor REA v3.11 (bloque `cultivos`) e CUE v3.11.4 (bloque `Cosecha`) en `docs/referencia/siex/`.

## Obxectivo

Que un cultivo garde o que pide o REA/CUE e o que o agricultor necesita (superficie, cultivo oficial, como se cultiva, orixe da semente), e que **cada colleita sexa un rexistro propio** con data, cantidade e lote. É a base de: dose por hectárea dos tratamentos, plan de abonado, rendemento, vendas, trazabilidade e plan de empresa (fases posteriores).

## Fóra deste deseño

Vendas; selos de calidade DOP/IGP (catálogo con códigos repetidos); recintos SIGPAC/DGC por cultivo; mapa; plan de abonado; deseño visual (decisión do usuario: funcionalidades primeiro).

---

## 1. Cultivo — campos

Os catálogos xa están importados (tarefa 026) salvo onde se indica.

| Campo | Tipo | Obrigatorio | Orixe / regra |
|---|---|---|---|
| parcela | FK | si | xa existe |
| **cultivo_siex_codigo** | catálogo PRODUCTOS (1.121) | si nos novos | buscador en galego (`buscar_cultivos`); `especie` gárdase co nome galego para amosar |
| variedade | VARIEDAD oficial **ou** variedade local **ou** texto libre | non | xa existen os tres campos |
| **superficie_ha** | número > 0 | si nos novos | por defecto a superficie libre da parcela; non pode superar a da parcela (se a parcela a ten) |
| **tipo_inicio** | sementeira / plantación | si | substitúe as dúas datas actuais |
| **data_inicio** | data | si | sementeira ou plantación |
| data_colleita_prevista | data | non | xa existe |
| **data_fin** | data | non | ≥ data_inicio; ao pórse, o cultivo queda rematado |
| causa_baixa | catálogo CAUSA_BAJA | non | só se hai data_fin antes do previsto |
| **sistema_cultivo** | catálogo SIST_CULTIVO (33) | si | por defecto "Aire libre" (1) |
| **sistema_explotacion** | catálogo SIST_EXPLOTACION (S/R) | si | por defecto o da parcela, se o ten |
| **destino** | catálogo DESTINO_CULTIVO (29) | si | por defecto "Consumo humano en fresco" (1) |
| actividade_agraria | catálogo ACTIVIDAD_AGRARIA | si | por defecto 1 (produción); oculto salvo que se cambie |
| **certificacion_ecoloxica** | catálogo (1 non / 2 certificado / 3 en conversión) | si | por defecto 1 |
| data_inicio_conversion | data | se é 3 | para calcular o fin da conversión (fase ecolóxica) |
| producion_integrada | si/non | non | REA |
| procedencia_material | catálogo PROC_VEGETAL | non | orixe da semente/planta |
| provedor_material, lote_material, pasaporte_fitosanitario, ropveg | texto | non | trazabilidade da semente |
| num_arbores **ou** marco_plantacion, ano_plantacion | número / texto / ano | non | só leñosos; excluíntes entre si (REA) |
| unidades_produtivas, ciclos_ano, duracion_ciclo_dias | números | non | só se sistema_cultivo é de cogomelos (9–16) |
| cultivo_anterior_codigo | catálogo PRODUCTOS | non | para o plan de abonado |
| obxectivo_colleita_kg_ha | número | non | para o plan de abonado |
| notas | texto | non | xa existe |

**Estado** deixa de escribirse a man e calcúlase: *planificado* (sen data_inicio ou no futuro), *en curso*, *rematado* (con data_fin). A columna `estado` mantense por compatibilidade e actualízase dende o servizo.

**Desaparecen do formulario**: data_sementeira, data_plantacion, data_colleita_real, cantidade, unidade (pasan a data_inicio/tipo_inicio e a Colleitas; ver migración).

### Regras de validación (servizo)

- Códigos de catálogo vixentes na data_inicio (`validar_codigo`).
- superficie_ha > 0 e ≤ superficie da parcela.
- data_fin ≥ data_inicio; data_colleita_prevista ≥ data_inicio.
- num_arbores e marco_plantacion non xuntos.
- data_inicio_conversion só se certificacion_ecoloxica = 3.
- Os tratamentos xa rexistrados non poden ter superficie tratada maior ca do cultivo (nova validación en `tratamentos_fito`, análise R4).

## 2. Colleita (entidade nova)

| Campo | Tipo | Obrigatorio | Regra |
|---|---|---|---|
| cultivo | FK | si | da mesma explotación |
| data | data | si | ≥ data_inicio do cultivo; ≤ hoxe |
| cantidade | número > 0 | si | |
| unidade | kg, t, unidades, ducias, mazos, litros | si | |
| superficie_ha | número | non | ≤ superficie do cultivo |
| **lote** | texto | si | proposto automaticamente `AAAA-<código cultivo>-NNN`, editable; único na explotación |
| destino_colleita | catálogo DEST_COSECHA | non | |
| destino_restos | catálogo DEST_RES_VEG | non | |
| notas | texto | non | |
| baixa | si/non | — | baixa lóxica, como tratamentos (conservación 3 anos) |

Funcións de servizo: `crear_colleita`, `actualizar_colleita`, `dar_de_baixa_colleita`, `listar_colleitas(horta, cultivo=None, ano=None)`, `propor_lote(cultivo, data)`, `rendemento(cultivo) -> kg/ha` (só se todas as colleitas van en kg ou t).

Permisos: ler = admin/editor/lector; escribir = admin/editor (como o resto).

## 3. Pantallas (funcionais; o estilo vén despois)

- **Cultivos**: "Novo cultivo" e "Editar" usan **o mesmo formulario** por bloques: *Que e onde* (parcela, cultivo, variedade, superficie, tipo e data de inicio, colleita prevista) · *Como se cultiva* (sistema, secano/regadío, destino, ecolóxico, integrada) · *Orixe da semente/planta* (pregable) · *Datos específicos* (só leñosos ou só cogomelos) · *Plan de abonado* (pregable). A táboa amosa cultivo, parcela, superficie, inicio, estado e total colleitado.
- **Colleitas**: sección nova no menú (grupo Caderno) e botón "Apuntar colleita" dende o cultivo. Táboa: data, cultivo, cantidade, lote, destino.
- **Resumo**: total colleitado no ano.

## 4. Migración dos datos existentes

- `data_inicio = data_plantacion` se existe (tipo plantación); se non, `data_sementeira` (tipo sementeira).
- Se había `cantidade` e `data_colleita_real` → créase unha Colleita con esa data, cantidade e unidade, e lote `MIGRADO-<id>`.
- `data_fin = data_colleita_real` se o estado era colleitado/finalizado.
- `superficie_ha`, sistema, destino... quedan baleiros nos cultivos antigos; a app avisa "Faltan datos para o caderno" (como os tratamentos migrados).
- As columnas antigas non se borran nesta fase (por seguridade); deixan de usarse.

## 5. Probas

Servizo: cada regra de validación (unha proba por regra), permisos, proposta de lote única, rendemento, migración (cultivo con e sen colleita antiga). UI: proba no navegador de crear un cultivo con catálogo e apuntar dúas colleitas (escritorio e móbil, criterio do usuario).

## 6. Reparto

- **Claude**: modelo, migración, servizos e probas (lóxica con regras).
- **smoth**: formulario por bloques, sección Colleitas, columnas da táboa, Resumo — tarefas literais.

## 7. Fases futuras (comprobación)

| Fase | Que necesitará deste deseño | Cuberto |
|---|---|---|
| Vendas | vender **por lote**; dispoñible = colleitado − vendido | lote único por explotación; cantidade + unidade normalizables a kg |
| Trazabilidade / xemelgo | historia do lote: semente (lote_material, provedor, pasaporte) → tratamentos do cultivo → colleita → venda | lote_material no cultivo; colleita ligada ao cultivo e este aos tratamentos (`TratamentoCultivo`) |
| Exportación CUE (`Cosecha`) | FechaInicio/FechaFin, Cantidad/Unidad, CodigoCultivo, Superficie, IdFinalidad, IdDestinoRest | data (inicio = fin), cantidade/unidade, cultivo_siex_codigo, superficie_ha, destino_colleita, destino_restos. **Unidade**: ao exportar traducir ao catálogo UNIDADES_MEDIDA |
| Exportación REA | campos do bloque `cultivos` | todos os do §1 cos mesmos catálogos |
| Plan de abonado | cultivo_anterior, obxectivo kg/ha, superficie | si |
| Ecolóxico (balance de masas, fin de conversión) | certificación por cultivo, data de conversión, colleitas por lote | si |
| Plan de empresa | produción anual por cultivo e rendemento kg/ha | `listar_colleitas` + `rendemento_kg_ha` |
| Equipo | quen colleitou (opcional) | **non**: engadir `persoa_id` opcional á colleita cando exista Equipo (columna nullable, sen romper nada) |

## 8. Revisión cruzada deseño ↔ código (2026-10-23, tarefas 029–034)

Comprobado con script: os campos do §1 e do §2 existen no modelo e a pantalla usa todos (agás os antigos que se manteñen por compatibilidade). Decisións tomadas onde o deseño e o código non coincidían:

| Punto do deseño | No código | Decisión |
|---|---|---|
| cultivo oficial obrigatorio nos novos | só o esixe a pantalla; o servizo admite cultivos sen código (os antigos e os tests) | aceptado: a táboa marca "Faltan datos" |
| variedade local galega | o campo existe pero a táboa `variedade_local` está baleira e a pantalla non a ofrece | pendente ata ter datos de variedades locais |
| actividade agraria oculta, por defecto 1 | tarefa 034 | feito |
| superficie por defecto = libre da parcela; secano/regadío da parcela | tarefa 034 | feito |
| tratamento ≤ superficie do cultivo | tarefa 034 | feito |
| Resumo: total colleitado no ano | sen tarefa | pasa á fase de Resumo/informes |
| nome galego duplicado ("Pataca" para o código 416) | dato: falta recargar `horta-catalogos nomes-galegos` na BD | lembrar ao actualizar catálogos |

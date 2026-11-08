# Horta

Aplicación web para a xestión integral de explotacións agrarias e gandeiras de Galicia.

## Descrición

Horta centraliza nun único rexistro a actividade da explotación: as parcelas e os cultivos, os animais, os traballos realizados, os insumos adquiridos, a produción e a súa comercialización.

A partir dese rexistro, a aplicación xera a documentación esixida pola normativa: o caderno de explotación, os libros de rexistro gandeiro e a trazabilidade dos lotes. Ademais, achega a información económica necesaria para a planificación da explotación. Cada dato introdúcese unha soa vez e utilízase en todos os documentos nos que é necesario.

Está deseñada para explotacións profesionais suxeitas a obrigas de rexistro e tamén para producións de autoconsumo. A interface está en galego e adaptada ao uso desde dispositivos móbiles.

## Funcionalidades

### Base territorial e produtiva
- Rexistro de parcelas con referencia SIGPAC e catastral, réxime de tenencia e sistema de explotación.
- Visualización das parcelas sobre cartografía.
- Xestión de cultivos por parcela: especie, variedade, superficie, datas e sistema de cultivo.
- Ficha de cada parcela e de cada cultivo co seu historial completo.

### Rexistro da actividade
- Sementeiras e plantacións, labores, regas, fertilización, tratamentos fitosanitarios, colleitas e toma de mostras.
- Rexistro mínimo obrigatorio (actividade, lugar, data e responsable), con datos complementarios opcionais.
- Planificación de tarefas e calendario de actividade.
- Información meteorolóxica de MeteoGalicia asociada á explotación.

### Produtos fitosanitarios
- Integración dos catálogos oficiais do SIEX (FEGA) e do Rexistro de Produtos Fitosanitarios do MAPA.
- Comprobación da autorización do produto para o cultivo e a praga indicados.
- Rexistro do aplicador, co seu carné ROPO, e da maquinaria de aplicación, con número ROMA e REGANIP.

### Gandaría
- Xestión de animais por grupos, con altas, baixas e movementos.
- Rexistro da produción (ovos, leite, mel e outros), dos coidados e tratamentos veterinarios e do pastoreo.

### Insumos, produción e comercialización
- Catálogo de insumos e rexistro de entradas: provedor, lote, cantidade e prezo.
- Xestión de lotes de produto e das súas saídas: venda, autoconsumo, transformación e perdas.
- Trazabilidade completa de cada lote, cunha páxina pública opcional para o consumidor.

### Xestión
- Directorio único de persoas e entidades: equipo de traballo, clientes, provedores, asesores e veterinarios.
- Xestión económica de gastos, ingresos e custos de man de obra.
- Plan de empresa para solicitudes de axudas.
- Acceso multiusuario con permisos de administración, edición ou consulta.

## Documentación xerada

| Documento | Formato |
|---|---|
| Caderno de explotación (modelo da Xunta de Galicia) | Excel |
| Caderno Dixital de Explotación Agrícola (CUE) | Excel e JSON |
| Libro de rexistro gandeiro | Excel |
| Rexistro de medicamentos veterinarios | Excel |
| Plan de empresa (Anexos III e V) | Excel |

A aplicación indica en cada momento os datos que faltan para completar o caderno, sen impedir a súa descarga.

## Marco normativo

- Real Decreto 1311/2012, sobre o uso sostible de produtos fitosanitarios.
- Caderno Dixital de Explotación Agrícola integrado no SIEX, obrigatorio para as explotacións profesionais desde o 1 de xaneiro de 2027 (Real Decreto 1039/2025).
- Catálogos e codificacións do SIEX (Anexo V).
- Rexistros autonómicos de explotacións agrarias e gandeiras (REAGA e REGA).

Os rexistros sometidos a obriga legal de conservación non se eliminan: dánse de baixa e mantéñense no histórico.

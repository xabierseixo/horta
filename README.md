# AgroXest360

Aplicación web para a xestión integral de explotacións agrarias e gandeiras de Galiza.

## Descrición

AgroXest360 centraliza nun único rexistro a actividade da explotación: as parcelas e os cultivos, os animais, os traballos realizados, os insumos adquiridos, a produción e a súa comercialización.

A partir dese rexistro, a aplicación xera a documentación esixida pola normativa: o caderno de explotación, os libros de rexistro gandeiro e a trazabilidade dos lotes. Ademais, achega a información económica necesaria para a planificación da explotación. Cada dato introdúcese unha soa vez e utilízase en todos os documentos nos que é necesario.

Diríxese tanto a explotacións profesionais suxeitas a obrigas de rexistro como a producións de autoconsumo. Está optimizada para o seu uso en dispositivos móbiles, o que permite rexistrar a actividade directamente no campo.

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
- Cálculo das necesidades de rega de cada cultivo coa evapotranspiración de MeteoGalicia e os coeficientes de cultivo da FAO (método FAO-56, o mesmo do SiAR do Ministerio).

### Produtos fitosanitarios
- Integración dos catálogos oficiais do SIEX (FEGA) e do Rexistro de Produtos Fitosanitarios do MAPA.
- Comprobación da autorización do produto para o cultivo e a praga indicados.
- Rexistro do aplicador, co seu carné ROPO, e da maquinaria de aplicación, con número ROMA e REGANIP.
- Recomendacións do asesor: o técnico deixa a recomendación e o agricultor aplícaa sen volver a apuntar os datos; o tratamento queda validado polo asesor.

### Sensores e internet das cousas
- Conexión de sensores de campo e de instalacións: humidade do chan, temperatura e humidade do aire, choiva, mollado de folla, contadores de auga, nivel de depósitos e de fosas de purín, e temperatura de cámaras e almacéns.
- Recepción das lecturas por internet desde dispositivos propios (ESP32, Arduino), redes LoRaWAN, MQTT ou estacións meteorolóxicas comerciais, sen depender dun fabricante concreto.
- Gráficas en tempo real e avisos configurables: humidade do chan baixa, risco de xeada, nivel da fosa ou temperatura fóra de rango.
- Uso dos datos noutras partes da aplicación: confirmar as necesidades de rega coa humidade real do chan, propor o rexistro dunha rega a partir do contador de auga e acompañar a trazabilidade dos lotes coa temperatura de conservación.

### Gandaría
- Xestión de animais por grupos, con altas, baixas e movementos.
- Rexistro da produción (ovos, leite, mel e outros), dos coidados e tratamentos veterinarios e do pastoreo.

### Insumos, produción e comercialización
- Catálogo de insumos e rexistro de entradas: provedor, lote, cantidade e prezo.
- Xestión de lotes de produto e das súas saídas: venda, autoconsumo, transformación e perdas.
- Trazabilidade completa de cada lote, cunha páxina pública opcional para o consumidor.

### Xestión
- Directorio único de persoas e entidades: equipo de traballo, clientes, provedores, asesores e veterinarios.
- Xestión económica de gastos, ingresos e custos de man de obra, e seguimento do consumo de enerxía.
- Plan de empresa para solicitudes de axudas.
- Arquivo de documentos e certificacións (certificado ecolóxico, GlobalG.A.P., seguros, inspeccións, carnés…), con aviso antes da súa caducidade.
- Acceso multiusuario con permisos de administración, edición ou consulta.
- Panel con todas as explotacións dunha persoa usuaria e os seus avisos, pensado para técnicos asesores e cooperativas.
- Cumprimento do RGPD: aviso legal, política de privacidade, aceptación expresa, descarga dos datos persoais e borrado da conta.

## Documentación xerada

- Caderno de explotación (modelo da Xunta de Galicia).
- Caderno Dixital de Explotación Agrícola (CUE).
- Libro de rexistro gandeiro.
- Rexistro de medicamentos veterinarios.
- Plan de empresa (Anexos III e V).

Todos eles poden descargarse en Excel, PDF, ODS (LibreOffice), CSV, XML e JSON.

## Marco normativo

- Real Decreto 1311/2012, sobre o uso sostible de produtos fitosanitarios.
- Caderno Dixital de Explotación Agrícola integrado no SIEX (Real Decreto 1054/2022): obrigatorio para rexistrar os tratamentos fitosanitarios desde o 1 de xaneiro de 2027 (Real Decreto 1039/2025); o caderno dixital completo, a partir do próximo marco da PAC.
- Catálogos e codificacións do SIEX (Anexo V).
- Rexistros autonómicos de explotacións agrarias e gandeiras (REAGA e REGA).

## Licenza

AgroXest360 é software libre, publicado baixo a licenza [GNU Affero General Public License v3.0 ou posterior](LICENSE) (AGPL-3.0-or-later). Calquera persoa pode usala, estudala, modificala e redistribuíla. Se se ofrece como servizo web, o código fonte, incluídas as modificacións, ten que estar dispoñible para as persoas que a usan.

## Despregamento

As instrucións para instalar a aplicación nun servidor están en [DESPREGAMENTO.md](DESPREGAMENTO.md).

# Caderno de explotación: fontes (revisado 2026-10-25)

## Modelo oficial de Galicia (base da exportación)

- `20260807_Modelo_de_caderno_de_explotacion_Xunta.docx` (e o seu texto en `.txt`): modelo da Consellería do Medio Rural, en galego, con data 7/8/2026. Descargado de https://mediorural.xunta.gal/es/temas/agricultura/sanidad-vegetal/fitosanitarios
- Seccións: 1 Información xeral (1.1 explotación e titular, 1.2 aplicadores, 1.3 equipos de fitosanitarios **e fertilizantes**, 1.4 asesoramento); 2 Parcelas (2.1 SIXPAC e datos agronómicos, 2.2 datos ambientais); 3 Tratamentos (3.1, 3.1 bis asesorados, 3.2 semente tratada, 3.3 postcolleita, 3.4 locais, 3.5 transporte); 4 Análises de fitosanitarios; 5 Colleita comercializada; **6 Caracterización de solos** (pH, MO, N, P₂O₅, K₂O, metais pesados); **7 Fertilización** (táboa principal, valor agronómico do material e metais pesados para residuos; plan de abonado e asesoramento SI/NON); **8 Rega** (con N nítrico e fósforo da auga).

## Outros modelos consultados

- Andalucía v6 (2023): mesma base estatal, máis ecorréximes (P1–P7) e unha fertilización máis simple. https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/MODELO_DE_CUADERNO_DE_EXPLOTACION_v.6.pdf (hai v8 de 2025).
- MAPA: modelo aprobado polo Comité Fitosanitario Nacional (18/12/2013), base dos autonómicos.

## Obrigas (BOE, texto consolidado)

- Tratamentos (RD 1311/2012 art. 16): rexistrar nun mes; papel ata o 31/12/2026; dende o 1/1/2027, electrónico no CUE (SIEX).
- Fertilización (RD 1051/2022 art. 4–5): rexistrar nun mes; pór o caderno á disposición da autoridade nun mes cando o pida; exentas as explotacións ≤5 ha con ≤1 ha de regadío (salvo invernadoiros >0,1 ha). Plan de abonado obrigatorio dende o 1/9/2026 (exentas unidades de secano ≤10 ha).
- Conservar 3 anos co caderno: facturas, contratos, certificados de inspección, envases, boletíns de análise, asesoramento, albarás de venda, plan de abonado, documentos dos estercos e residuos.
- Non hai unha data de presentación periódica: o caderno lévase ao día e amósase cando o pide a Administración (inspección, controis PAC).

## CUE comercial en Galicia (XEAGA)

https://mediorural.xunta.gal/es/temas/explotaciones/xeaga/cuadernos-comerciales
- Procedementos: MR470B (empresa desenvolvedora de software), MR407C (entidade xestora), MR407D (titular que usa un CUE comercial).
- Interface Única v3.11: integración `https://api-lab.xeaga.xunta.gal`, produción `https://api.xeaga.xunta.gal` (comunicación/token, exportarREA, exportar, crear, comprobarEstado). A v3.3 retirouse en 2026.

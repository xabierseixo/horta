# Plan de empresa (paso 16 do deseño global)

Data: 2026-10-29 · Decisións do usuario: sen plan de cultivos polo de agora; previsto fronte a real si; primeiro só AGADER (Anexo III + V). Base legal: `docs/estado-e-evolucion.md` §3.1 (convocatoria MR701L, DOG 2/2/2026).

## Que garda

- **`plan_empresa`**: título, liña (`agader`), ano 1, empresa nova ou existente, CNAE, textos do Anexo III (descrición, proceso, formación), emprego en UTA (mantidas, creadas e por colectivos), taxa de desconto do VAN.
- **`plan_investimento`** (Anexo V): partida, concepto, importe sen IVE, % IVE, vida útil (amortización lineal; os terreos non se amortizan) e cantas ofertas hai (avisa se son menos de 3).
- **`plan_financiamento`**: capital, recursos propios, préstamo (con xuro e anos: cota constante), subvención, outros.
- **`plan_ano`** (anos 1–5): vendas, custos variables e custos fixos. **Ao crear o plan propóñense desde Cartos** (o último ano completo): vendas = vendas de produto e de animais; variables = compras, man de obra allea e máquinas; fixos = outros gastos. Edítanse.

## Que calcula

- Conta de explotación: A vendas, B variables, C fixos, D amortizacións (do investimento), E = A−(B+C+D), F = − xuros dos préstamos, G = E+F.
- Fluxo de caixa de cada ano = G + D; ano 0 = − investimento sen IVE (o IVE recuperable non conta).
- **VAN** coa taxa do plan, **TIR** (bisección) e **pay-back** (primeiro ano en que o acumulado é ≥ 0).
- Métricas da explotación (ano real): rendemento kg/ha por cultivo, prezo medio por produto e canle, % de refugo, horas e UTA, punto morto.
- **Seguimento**: cada ano do plan, o previsto ao lado do real (Cartos).

## Saídas

Excel co Anexo III (datos, emprego, financiamento, conta a 5 anos, indicadores) e o Anexo V (partidas sen e con IVE).

## Fóra deste paso

Plan de cultivos; MR404A/MR405F; marxe por cultivo (precisa repartir custos por cultivo); comparación con RECAN/ECREA; memoria complementaria.

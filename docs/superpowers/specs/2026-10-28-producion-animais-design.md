# Produción dos animais (deseño)

Data: 2026-10-28 · Estado: **aprobado polo usuario** («Si, continua», 2026-10-28) · Tarefas 079–079j · Paso 6, parte 3 (`docs/como-e-a-app.md` §5)

## Fontes

- **README §7** (plan orixinal): «rexistrar producións asociadas (ovos, carne, etc.), de forma similar ás colleitas dos cultivos».
- **Análise de campos** (`docs/analise-campos-2026-10-23.md` §7): «Produción (ovos, leite, mel...): rendemento, vendas».
- **Ovos:**
  - RD 1027/2024 (BOE-A-2024-20403, comprobado o 2026-10-28):
    - non se aplica á venda directa ao consumidor na explotación nin a domicilio (art. 1.2);
    - no mercado local, sen marcar os ovos se hai ≤ 50 galiñas poñedoras e o nome e enderezo están á vista (arts. 1.3 e 5.2).
  - Reg. de Execución (UE) 2023/2466: rexistros dos produtores rexistrados (número de galiñas, ovos producidos e vendidos por día). Hai que cotexar o texto do artigo antes do paso 14.
- **Mel:** RD 209/2002, anexo substituído polo RD 448/2005 (comprobado o 2026-10-28). O libro apícola pide colmeas, enfermidades, tratamentos, análises e traslados, **non a produción**. A produción serve para as vendas e o plan de empresa.
- **Leite:** o RD 989/2022 (que substitúe o RD 1728/2007) obriga a quen merca o leite, non ao gandeiro. Non se pode vender o leite dun animal en tempo de espera (Reg. UE 2019/6, xa usado na parte 1).
- **Venda directa (Decreto 125/2014, anexo II):** máximo 1.000 ducias de ovos e 3.000 kg de mel por ano. A conta faise na parte 4 (vendas), a partir desta produción.
- **Trazabilidade (Reg. CE 178/2002, art. 18):** un lote por produción, como nas colleitas.
- **Outras apps:**
  - farmOS: a produción dos animais (p. ex. ovos) é un rexistro de colleita sobre o animal, con cantidade e unidade.
  - Farmbrite: rexistros de produción por animal ou grupo (ovos, leite, la, mel), con data, cantidade e unidade.
  - Apps de galiñas: conta diaria ou semanal de ovos, e os rotos ou que non valen.
  - Apps de colmeas (Apiary Book, HiveTracks): mel recollido por colmea ou apiario, en kg.
  - Apps de leite: litros por muxidura, e o leite que se tira polo tempo de espera.

## Para que serve (obxectivo)

- Saber canto produce cada grupo. Serve para as **estatísticas** (paso 15) e o **plan de empresa** (produción bruta).
- Prepara as **vendas** (parte 4): cada venda sae dun lote de produción, e conta para os límites da venda directa.
- **Seguridade alimentaria:** se o grupo está en tempo de espera, a app avisa de que o produto non se pode vender nin comer.
- **Xemelgo:** o lote do ovo ou do mel enlaza coa vida do grupo (coidados, medicamentos, orixe).

## Relacións (`docs/modelo-datos.md`)

- `producion_animal → horta`, `→ animal` (o grupo, obrigatorio, da mesma explotación), `→ persoa` (quen, obrigatorio) e `→ usuario` (`creado_por`).
- O **lote** é obrigatorio e único na explotación, xunto cos lotes das colleitas, para que as vendas os collan dun só sitio. A app propón `AAAA-PRODUTO-NNN` (p. ex. `2026-OVOS-001`).
- Non se pode apuntar antes da data de alta do grupo, despois da súa baixa nin no futuro.
- Baixa lóxica.

## Que garda (táboa nova `producion_animal`)

| Campo | Para que | Fonte |
|---|---|---|
| `data`, `data_fin` (opcional) | un día ou un período (p. ex. os ovos da semana) | apps de galiñas; colleita |
| `produto` | ovos, leite, mel, cera, la, outro | README §7; análise §7 |
| `cantidade` (> 0) e `unidade` | unidades, ducias, litros, kg | Decreto 125/2014 (ducias, kg) |
| `retirada` (opcional, ≤ cantidade) | o que non vale: rotos, ou o que se tira polo tempo de espera | apps de galiñas e de leite; Reg. UE 2019/6 |
| `lote` | trazabilidade e vendas | Reg. CE 178/2002 |
| `persoa_id`, `horas`, `notas`, `baixa`, `creado_por`, `uuid`, `created_at` | como nos outros traballos | — |

- **Produtos por especie:**
  - ovos: galiñas, pavos, pintadas, patos, gansos, paspallás, avestruces;
  - leite: vacas, ovellas, cabras e cabalos e burros (leite de burra);
  - mel e cera: abellas;
  - la: ovellas;
  - «outro»: calquera especie.
- **Unidade por defecto:** ovos en unidades (ou ducias), leite en litros, mel, cera e la en kg.
- **Carne:** non vai aquí. Sae da **saída** (venda ou matadoiro) ou do **sacrificio na casa** (parte 2).
- **Aviso, sen bloquear:** se o grupo está en tempo de espera nesa data, a app avisa «Este grupo está en tempo de espera ata o dd/mm/aaaa: este produto non se pode vender nin comer» e propón poñer todo como retirado. Usa `fin_tempo_espera` (parte 1).

## Onde aparece

- **Animais:** botón «Produción» no grupo, que abre o formulario co grupo xa escollido. Os produtos que se ofrecen son os da especie do grupo.
- **Apuntar traballo** e **Diario:** tipo «Produción dos animais», por exemplo «Produción: 24 ovos (2 rotos) · Galiñas · Ana».
- **Táboa «Produción»** (fóra do menú, como «Entradas e saídas»): data, grupo, produto, cantidade, retirada, lote e quen; editar e dar de baixa.
- **Tarefas:** novo tipo «Produción dos animais», co grupo. «Facela agora» como nos outros tipos.
- **Inicio:** nada novo nesta parte; as gráficas van no paso 15.

## Fases futuras

- **Parte 4 (vendas):**
  - a venda escolle un lote de produción ou de colleita;
  - aviso se o lote ten produto retirado;
  - conta anual para os límites do Decreto 125/2014.
- **Paso 14:** se a explotación de galiñas está rexistrada, informe cos datos do Reg. 2023/2466.
- **Paso 15:** estatísticas por grupo, produto e mes (p. ex. ovos por galiña).
- **Paso 16:** produción bruta no plan de empresa.
- **Xemelgo:** o lote enlaza coa vida do grupo.

## Probas previstas

Servizo:
- crear, editar e dar de baixa;
- lote proposto e lote repetido (tamén cun lote de colleita);
- produto que non é da especie do grupo, que falla;
- retirada maior ca a cantidade, que falla;
- datas: antes da alta, despois da baixa ou no futuro, que fallan;
- quen é obrigatorio;
- aviso de tempo de espera;
- Diario e tarefa;
- non se borra un grupo con produción.

Navegador (escritorio e móbil, copia da BD):
- apuntar os ovos dunha semana e ver o Diario;
- apuntar ovos dun grupo medicado e ver o aviso.

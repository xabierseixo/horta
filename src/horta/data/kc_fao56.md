# Coeficientes de cultivo (Kc) — fonte

`kc_fao56.csv` sae de:

Allen, R. G.; Pereira, L. S.; Raes, D.; Smith, M. (1998). *Crop evapotranspiration — Guidelines for computing crop water requirements*. FAO Irrigation and Drainage Paper 56. Roma: FAO. Capítulo 6, táboa 11 (duración das fases) e táboa 12 (Kc ini, Kc mid, Kc end). https://www.fao.org/4/x0490e/x0490e0b.htm

É o mesmo método que usa o Sistema de Información Agroclimática para el Regadío (SiAR) do MAPA. A ET0 diaria vén das estacións de MeteoGalicia.

Criterios:
- Cando a táboa 12 non dá un Kc ini propio para o cultivo, úsase o do seu grupo (hortalizas pequenas 0,7; solanáceas 0,6; cucurbitáceas 0,5; raíces e tubérculos 0,5; leguminosas 0,4).
- As fases (táboa 11) son a fila máis próxima ao clima e á época de Galicia (Europa ou Mediterráneo, primavera). Se a táboa 11 non ten o cultivo, as columnas `l_*` van baleiras e úsase o Kc mid todo o ciclo (cálculo aproximado).
- Pradeiras e alfalfa: Kc medio dos cortes (*averaged cutting effects*).
- Os cultivos que non están na táboa non teñen cálculo: a app avisa e non inventa valores.
- Para revisar con técnicos: o Kc end do tomate (0,70–0,90, tomouse 0,80), a cuberta vexetal dos froiteiros (tomouse «active ground cover, no frosts») e o millo forraxeiro (non está na táboa; úsase o de gran con colleita húmida).

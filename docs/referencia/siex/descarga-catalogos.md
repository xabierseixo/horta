# Descarga mensual dos catálogos do FEGA

Os catálogos actualízanse maioritariamente o día 1 de cada mes (índice METACATALOGO, campo cronExpre).

1. Abrir https://www3.sede.fega.gob.es/bdcsixpor/catalogos nun navegador normal.
2. Para cada catálogo da táboa de `CATALOGOS_XERAIS` (src/horta/services/catalogos_importar.py),
   máis "Cultivo" (PRODUCTOS) e "Variedad / Especie / Tipo" (VARIEDAD_ESPECIE_TIPO):
   filtrar polo nome, abrir o detalle e premer a icona de Excel.
3. Gardar cada ficheiro como `<CODIGO>.xlsx` (p.ex. `PLAGAS.xlsx`) nun directorio.
4. `uv run horta-catalogos importar <directorio>` e revisar o informe (altas, baixas, cambios).
5. Se hai baixas que afecten a tratamentos en curso, avisar ás persoas usuarias.

Non automatizar contra o servidor saltando o reCAPTCHA. Vía estable pendente: petición ao FEGA
(cau-fega@fega.es) ao abeiro da Lei 37/2007 de reutilización.

# Catálogos oficiais: dentro da app, aviso e actualización asistida; rexistro do MAPA automático (deseño)

Data: 2026-10-25 · Estado: **aprobado e feito** (tarefas 072–072j, 2026-10-25)

## Decisións do usuario (2026-10-25)

- Non se instala nada no ordenador. As descargas teñen que funcionar dentro da app, ou facerse cando se desprega.
- Os catálogos que teñen captcha descárgaos unha persoa co seu navegador. A app avisa de que toca e importa o que se sube.

## Fontes comprobadas o 2026-10-25

- **Rexistro de fitosanitarios do MAPA** (regfiweb): descarga directa JSON (`POST Exportaciones/ExportJsonProductosAutorizados` e `ExportJsonCultivos`), sen captcha.
  - O FEGA, nas súas preguntas frecuentes, dío fonte oficial para os cadernos comerciais.
  - Cambia cada semana.
- **Catálogos SIEX (FEGA)**:
  - O portal `www3.sede.fega.gob.es/bdcsixpor` ten reCAPTCHA en cada descarga e hoxe responde 404.
  - O ZIP anual da Circular PAC (`20260610_Catalogos_SIEX_Circular_PAC_2026.zip`) non ten captcha, pero só trae 10 dos 39 catálogos que usa a app.
  - Non hai API nin datos abertos.
  - Vía oficial futura: o «punto de descarga» para cadernos comerciais (preguntas frecuentes do FEGA), con alta MR470B na Xunta.
- **Formato:**
  - A app le cada ficheiro polos nomes das columnas.
  - O ZIP e o portal usan as mesmas columnas, pero nomes de ficheiro distintos; as follas do ZIP chámanse «Datos».
  - O FEGA substitúe a documentación técnica en set. 2027 (SIEX 5.9.0), así que é probable que cambie o formato.

## 1. Catálogos dentro da app

- Os 39 ficheiros que usa a app (5,2 MB) van en `src/horta/data/catalogos_fega/`. Reutilízanse citando a fonte (Lei 37/2007).
- `horta-catalogos importar` sen directorio importa os da app.
- Ao arrancar, se a BD non ten catálogos, a app impórtaos sola. Así unha instalación nova non precisa descargar nada.

## 2. Importación segura (todas as rutas: comando, arranque e pantalla)

- **Recoñecemento polo contido, non polo nome:**
  - código do portal (`PLAGAS.xlsx`);
  - ou nome do ficheiro do ZIP sen a data;
  - ou título da folla, comparando o comezo do texto porque Excel o corta aos 31 caracteres.
  - Se non se recoñece: «Non sei que catálogo é».
  - Se se recoñece pero a app non o usa: «A app non usa este catálogo».
- **Formato:** antes de tocar nada compróbanse as columnas obrigatorias de cada catálogo. Se falta algunha, sae este erro: «Ao ficheiro X fáltalle a columna «Y». O FEGA puido cambiar o formato: hai que adaptar a app». Non se importa nada.
- **Revisión sen gardar:** a importación pódese executar en modo previsualización: calcula altas, baixas e cambios e despois desfai.
- **Sospeitoso:** se un ficheiro daría de baixa máis de 5 códigos e máis do 20 % dos existentes, márcase e pide confirmación expresa. É o caso típico dun ficheiro equivocado.

## 3. Pantalla «Catálogos oficiais» (`/admin/catalogos`, só administración global)

- **Táboa:** catálogo (nome en galego), ficheiro do FEGA, nº de códigos, data da última importación e días que pasaron.
- **Botón «Abrir o portal do FEGA»** (nova lapela) e a lista dos ficheiros que hai que baixar.
- **Subida:** varios `.xlsx` ou un `.zip` → «Revisar» → táboa con ficheiro, catálogo, altas/baixas/cambios e avisos → «Aplicar».
- **Rexistro do MAPA:** data da copia, última comprobación e botón «Comprobar agora».
- No menú, xunto a «Administración».

## 4. Aviso

- Na sección Resumo, só para a administración global, sae un aviso cando o catálogo importado hai máis tempo ten máis de 60 días: «Os catálogos oficiais teñen N días: revísaos». Leva ligazón á pantalla.
- Tamén avisa se a última descarga do rexistro do MAPA fallou.

## 5. Rexistro do MAPA automático

- `services/fito_descargar.py` descarga os dous JSON (só biblioteca estándar) a un directorio temporal e importa.
- Se o JSON non cambiou, a importación non fai nada (sha256).
- **Táboa `comprobacion_catalogo`** (catálogo, data, resultado/erro): garda cando se comprobou por última vez, aínda que non houbese cambios.
- **Programación:** ao arrancar a app e despois cada 6 h, en segundo plano. Descarga se a última comprobación ten máis de 7 días.
  - `HORTA_ACTUALIZAR=0` desactívao (probas, sen internet).
  - Se falla, a app segue coa copia anterior, rexístrao e avisa (§4).
- **Despregamento:** `horta-catalogos fitosanitarios --descargar`.

## Fóra deste deseño

- Detectar automaticamente un ZIP novo do FEGA: a URL da páxina cambia cada ano. A pantalla acepta o ZIP cando alguén o baixe.
- Descargar automaticamente os catálogos con captcha.

## Orde e reparto

Claude escribe e proba a versión esperada; ornith-88 implementa en tarefas pequenas. Os ficheiros binarios (os .xlsx da app) cópiaos Claude.

| Paso | Que |
|---|---|
| a | importadores: comprobación de columnas, modo revisión e marca de sospeitoso |
| b | recoñecemento de ficheiros e revisión dun lote (servizo + probas) |
| c | catálogos dentro da app e importación ao arrancar se non hai |
| d | `comprobacion_catalogo`, descarga do MAPA, programación e `--descargar` |
| e | pantalla «Catálogos oficiais» e aviso no Resumo |

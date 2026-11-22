# Catálogos oficiais SIEX que leva a app

Fonte: Fondo Español de Garantía Agraria (FEGA), Anexo VII da Documentación Técnica Agrícola
SIEX, portal público https://www3.sede.fega.gob.es/bdcsixpor/catalogos. Reutilización ao
abeiro da Lei 37/2007, citando a fonte.

Descargados no navegador o 2026-10-22. Só os 39 que usa a app (ver `CATALOGOS_APP` en
`services/catalogos_ficheiros.py`).

- Instalación nova: a app impórtaos soa ao arrancar se a BD non ten catálogos; tamén
  `uv run horta-catalogos importar`.
- Actualizar: descargalos de novo no portal (ten captcha: faino unha persoa no navegador) e
  subilos en Administración → Catálogos oficiais, ou substituír estes ficheiros nunha versión
  nova da app.

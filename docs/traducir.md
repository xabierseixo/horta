# Tradución e soporte multilingüe en Horta

A aplicación ten soporte multilingüe baseado no estándar **gettext** e a libraría **Babel**.
O idioma base do código e da interface é o galego (`gl`). Pódense engadir novos idiomas
sen tocar o código fonte da aplicación, simplemente engadindo ficheiros de catálogo `.po`.

## Que é un ficheiro `.po`

Un ficheiro `.po` (Portable Object) é un ficheiro de texto plano que contén correspondencias
entre as mensaxes orixinais da aplicación (`msgid`, en galego) e as súas traducións a outro
idioma (`msgstr`).

En Horta, cada idioma adicional sitúase en:
`src/horta/locales/<código>/horta.po` (por exemplo: `src/horta/locales/es/horta.po`).

A aplicación compila estes ficheiros `.po` a formato binario `.mo` directamente en memoria ao
arrancar mediante Babel, polo que non se gardan ficheiros binarios `.mo` no repositorio git.

## Como extraer os textos do código

Para xerar o modelo de tradución inicial (`horta.pot`) a partir de todos os textos marcados:

```bash
uv run pybabel extract -F babel.cfg -k _ -k N_ -k ngettext:1,2 -o src/horta/locales/horta.pot .
```

`babel.cfg` usa o extractor `horta.extraer_textos`, que tamén colle os `_()` que van dentro
dunha f-string (o extractor normal de Babel non os ve en Python 3.11).

## Como crear un novo idioma

1. Inicializar o catálogo para o código de lingua desexado (por exemplo `es` para castelán):

```bash
uv run pybabel init -i src/horta/locales/horta.pot -d src/horta/locales -D horta -l es
```

2. Mover o ficheiro xerado á ruta esperada pola aplicación:

```bash
mv src/horta/locales/es/LC_MESSAGES/horta.po src/horta/locales/es/horta.po
rmdir src/horta/locales/es/LC_MESSAGES
```

(Ou indicar directamente a ruta de saída co parámetro `-o src/horta/locales/<código>/horta.po`).

3. **Engadir a cabeceira `Language-Name`**:
   No bloque de cabeceiras inicial do `.po` (`msgid ""`), engadir a liña co nome co que se
   amosará o idioma no selector da interface:

   ```po
   "Language-Name: Español\n"
   ```

## Traducir os textos

Os ficheiros `.po` pódense editar con calquera editor de texto plano ou con ferramentas
especializadas de tradución asistida como [Poedit](https://poedit.net/).

Se un texto non ten tradución definida (`msgstr ""` baleiro), a aplicación amosa
automaticamente o texto orixinal en galego.

## Como actualizar as traducións cando cambian os textos

Cando se engaden ou modifican textos no código Python:

1. Volver extraer o modelo actualizado:
   ```bash
   uv run pybabel extract -F babel.cfg -k _ -k N_ -k ngettext:1,2 -o src/horta/locales/horta.pot .
   ```

2. Actualizar os catálogos existentes sen perder as traducións actuais:
   ```bash
   uv run pybabel update -i src/horta/locales/horta.pot -d src/horta/locales -D horta
   ```

## Regras para marcar textos no código

- **Textos simples**:
  ```python
  from horta.idiomas import _

  ui.label(_("Gardar"))
  ```

- **Textos con variables e datos**:
  Usar sempre `.format(...)` e **nunca** f-strings dentro de `_()`, xa que `pybabel extract`
  require cadeas de texto literais estáticas para podelas extraer:
  ```python
  # Correcto:
  ui.notify(_("Gardáronse {n} lecturas").format(n=n))

  # INCORRECTO (non se pode extraer):
  # ui.notify(_(f"Gardáronse {n} lecturas"))
  ```

- **Plurais**:
  Usar `ngettext` indicando forma singular, plural e cantidade:
  ```python
  from horta.idiomas import ngettext

  texto = ngettext("{n} leira", "{n} leiras", total).format(n=total)
  ```

- **Constantes e dicionarios a nivel de módulo**:
  Marcar a cadea con `N_` para que pybabel a extraia sen tentar traducila no momento de
  definición do módulo, e traducila con `_()` onde se amose:
  ```python
  from horta.idiomas import N_, _

  ESTADOS = {
      "activa": N_("Activa"),
      "pausada": N_("Pausada"),
  }

  # Ao renderizar na interface:
  ui.label(_(ESTADOS[estado]))
  ```

- **Informes oficiais (caderno de campo, CUE, etc.)**:
  Os documentos que deban cumprir co idioma esixido pola administración usan o xestor de
  contexto `con_idioma(...)`, con independencia da lingua elixida pola persoa usuaria:
  ```python
  from horta.idiomas import con_idioma

  with con_idioma("es"):
      xerar_informe_cue(...)
  ```

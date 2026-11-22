# Deseño: Funcionalidades — busca, filtros e paxinación

## Contexto

Esta é a primeira das tres iteracións acordadas para "Funcionalidades" (a segunda das tres grandes iteracións de v1.1, tras "Robustez"): busca/filtros/paxinación, exportación e historial/actividade. Esta spec cobre só a primeira.

Motivación: as catro táboas actuais da app (Parcelas e Animais en `horta_detalle.py`, Membros en `horta_detalle.py`, Usuarios en `admin/usuarios.py`) amosan sempre todas as filas sen posibilidade de buscar, filtrar nin paxinar. Con hortas que crezan en número de parcelas/animais, ou paneis de admin con máis usuarios, isto deixa de ser usable.

## Obxectivo

1. Busca de texto libre en tempo real en todas as columnas visibles de cada táboa.
2. Filtro estruturado (selector, non texto libre) por campos de valores fixos: Estado en Parcelas e Animais, Rol en Membros, Rol e Activo en Usuarios.
3. Paxinación con 10 filas por páxina por defecto en todas as táboas.
4. Todo o anterior combinable á vez (busca + filtro(s) estruturado(s) + paxinación funcionan xuntos, non son alternativas).

## Fóra de alcance

Exportación (CSV/Excel) e historial/actividade son as seguintes dúas iteracións de "Funcionalidades", con spec propia cada unha. Busca/filtrado no servidor (consultas á BD con parámetros de busca) — non compensa cos volumes de datos actuais dunha horta persoal/pequena explotación; queda como posible traballo futuro se o volume de datos cambia. Persistencia do filtro activo tras recargar a páxina (`ui.navigate.reload()` tras crear/editar/eliminar reinicia sempre os filtros).

## Arquitectura

Filtrado 100% en Python sobre a lista de filas xa cargada, non co prop `filter` nativo de QTable — porque hai que combinar busca de texto libre CON selectores estruturados á vez, e QTable de fábrica só soporta un criterio simple.

```
Carga da páxina
    │
    └─ servizo (listar_parcelas/listar_animais/membros/usuarios) — sen cambios
           → lista completa de filas, gardada en Python (todas_as_filas)
           → taboa.rows = filtrar_filas(todas_as_filas, "", campos_busca, {})
           → ui.table(rows=..., pagination={"rowsPerPage": 10}, ...)

Usuario escribe no input de busca OU cambia un selector
    │
    └─ on_change → refrescar_taboa()
           → taboa.rows = filtrar_filas(todas_as_filas, texto_actual, campos_busca, filtros_actuais)
           → taboa.update()
           (QTable recalcula a paxinación sobre as filas filtradas)
```

- `todas_as_filas` nunca se muta, só se relee — evita volver consultar a BD en cada tecla.
- Crear/editar/eliminar segue facendo `ui.navigate.reload()` coma hoxe; isto recarga `todas_as_filas` e reinicia os filtros.
- `taboa.selected` (para Editar/Eliminar) segue operando sobre as filas actualmente visibles.
- Cero cambios na capa de servizos nin na BD. Cero dependencias novas.

## Compoñentes

### `src/horta/ui/filtros.py` (novo)

Función pura, sen NiceGUI nin BD:

```python
def filtrar_filas(
    filas: list[dict],
    texto: str,
    campos_busca: list[str],
    filtros_estruturados: dict[str, str] | None = None,
) -> list[dict]:
    """Filtra unha lista de filas por busca de texto (subcadea, sen distinguir
    maiúsculas/minúsculas) e por criterios estruturados de coincidencia exacta
    (p.ex. {"estado": "activa"}). Unha clave ausente ou con valor None/"" en
    filtros_estruturados non filtra por ese campo (sentinela "Todos")."""
```

Comportamento:
- `texto=""` → non filtra por texto.
- Busca por subcadea en `str(fila[campo]).casefold()` para cada campo en `campos_busca`; coincide se algún campo contén o texto buscado (tamén en casefold). Sen normalización de acentos (límite coñecido e aceptado: buscar "rio" non atopa "Río").
- Cada entrada de `filtros_estruturados` cuxo valor non sexa `None` nin `""` esixe coincidencia exacta (`str(fila[campo]) == valor`) — combínanse en AND entre si e coa busca de texto.

### Extracción DRY en ficheiros existentes

`src/horta/ui/pages/horta_detalle.py` ten hoxe as listas fixas de Estado/Rol escritas directamente dentro dos `ui.select(...)` de edición (liñas 242, 408, 512 na versión actual). Pásanse a constantes de módulo, reutilizadas tanto polo selector de edición coma polo novo selector de filtro:

```python
_ESTADOS_PARCELA = ("activa", "inactiva")
_ESTADOS_ANIMAL = ("activo", "baixa")
_ROLES_HORTA = ("admin", "editor", "lector")
```

### Por táboa

Catro sitios, mesmo patrón en cada un — unha fila nova enriba da táboa con:

| Táboa | Ficheiro | Busca (campos) | Selector(es) estruturado(s) |
|---|---|---|---|
| Parcelas | `horta_detalle.py` | nome, superficie, estado | Estado (`["Todos", *_ESTADOS_PARCELA]`) |
| Animais | `horta_detalle.py` | especie, raza, cantidade, estado | Estado (`["Todos", *_ESTADOS_ANIMAL]`) |
| Membros | `horta_detalle.py` | nome, email, rol | Rol (`["Todos", *_ROLES_HORTA]`) |
| Usuarios | `admin/usuarios.py` | nome, email, rol, activo | Rol (`["Todos", "admin", "usuario"]`) e Activo (`["Todos", "si", "non"]`) |

Cada `ui.select`/`ui.input` leva `on_change=refrescar_taboa` (ou equivalente `.on('update:model-value', refrescar_taboa)` se fai falla para o input de texto en cada tecla). `ui.table(...)` engade `.props('pagination={"rowsPerPage":10}')` xunto ao `_PROPS_TABOA` xa existente en cada ficheiro.

En `admin/usuarios.py`, `rows` xa garda `activo` coma texto (`"si"`/`"non"`, ver `admin/usuarios.py:41`), non coma booleano — o selector "Activo" filtra directamente por `{"activo": "si"}` ou `{"activo": "non"}`, sen necesidade de ningún campo derivado.

## Probas

- **`tests/ui/test_filtros.py`** (novo, tests unitarios puros para `filtrar_filas`):
  - Texto baleiro → devolve todas as filas.
  - Busca por subcadea en varios campos, sen distinguir maiúsculas/minúsculas.
  - Busca sen coincidencias → lista baleira.
  - Só filtro estruturado (texto="") → só as filas con coincidencia exacta.
  - Texto + filtro estruturado combinados (AND).
  - Sentinela "Todos" (valor `None`/`""`) → non filtra por esa clave.
  - Documentar coma test explícito o límite de acentos (busca "rio" non atopa "Río") — é o comportamento esperado, non un fallo.
- Sen tests novos de UI para o griding nas páxinas NiceGUI — segue o precedente xa establecido no proxecto (as páxinas non se testean unitariamente; verificación manual).
- Suite completa (`uv run pytest`), ruff e mypy deben seguir en verde.

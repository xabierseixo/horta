# Modelo: Animal

## Estado da revisión

- **Data de inicio**: 2026-10-12
- **Estado**: Completado
- **Resumo**: Revisión completa do modelo `Animal`, os seus campos, relacións, servizos e tests asociados.

## Ficheiros consultados

- `src/horta/models/animal.py`
- `src/horta/models/horta.py`
- `src/horta/services/animais.py`
- `tests/models/test_animal.py`

## Campos comprobados

| Campo | Tipo | Obrigatorio | Default | Observacións |
|-------|------|-------------|---------|--------------|
| `id` | `int` | Si (PK) | — | Primaria, auto-incremental |
| `horta_id` | `int` | Si (FK) | — | FK a `horta.id` |
| `especie` | `str` (80) | Si | — | Non ten default; crear animal sen especie fallará |
| `raza` | `str` (120) | Non | `None` | Opcional |
| `cantidade` | `int` | Non | `1` | Non validada: podería ser ≤ 0 (negativo ou cero) |
| `data_alta` | `date` | Si | — | Non ten default; crear animal sen data de alta fallará |
| `data_baixa` | `date` | Non | `None` | Opcional; podería ser igual a `data_alta` |
| `estado` | `str` (50) | Non | `"activo"` | Non validado contra un conxunto de valores permitidos |
| `notas` | `str` (1000) | Non | `None` | Opcional |
| `created_at` | `datetime` | Si | `now(utc)` | Auto; non é editable |

### Observacións de integridade

- **`data_alta` obrigatorio sen default**: Se se instancia `Animal()` sen pasar `data_alta`, a creación fallará con `IntegrityError`. Non parece existir unha ruta de fallo axeitada.
- **`especie` obrigatorio sen default**: Mesmo problema que `data_alta`.
- **FK `horta_id` sen `ondelete`**: Non se especifica o comportamento de borrado en cascada cando se elimina a horta.
- **`data_baixa` non validada**: Podería ser igual ou anterior a `data_alta`.
- **`estado` non enumera**: Podería admitir valores arbitrarios.

## Relacións comprobadas

### Animal ↔ Horta

- **Tipo**: Unha horta moiña moitos animais (N:1 de Animal a Horta, 1:N de Horta a Animal).
- **FK**: `animal.horta_id` → `horta.id`.
- **Relación ORM**: Non definida explicitamente en `animal.py` nin en `horta.py`. Non hai `relationship()` nin `back_populates`.
- **Impacto**: O código funciona porque SQLAlchemy detecta a relación pola FK, pero a documentación ORM é pobre; a navegación inversa (`horta.animais`) non existe.

### Horta ↔ HortaMembro ↔ Usuario

- **`HortaMembro`**: Tabla de unión (`horta_id`, `usuario_id` como PK compostos).
- **`RolHorta`**: Enum con `ADMIN`, `EDITOR`, `LECTOR`.
- **`RolHorta` non herdado**: Non está definido en `animal.py` nin en `horta.py`.

## Restricións e validacións comprobadas

### No modelo (`animal.py`)

- **Ninguna validación de negocio**: Non hai constraints de SQLAlchemy, `@validates`, nin `validator`.
- **FK sen `unique=True`**: `horta_id` podería ter moitas filas (é a relación N:1 esperada, pero non está documentado).
- **FK sen `nullable=True`**: Aínda que `horta_id` é obrigatorio, non se especifica explícitamente `nullable=False` (o default de SQLAlchemy é `False` para FKs).

### No servizo (`services/animais.py`)

- **`CAMPOS_EDITABLES_ANIMAL`**: Exclúe `id`, `horta_id`, `created_at` da actualización.
- **`crear_animal`**: Permite `estado` como campo opcional (default `"activo"`).
- **`actualizar_animal`**: Bloquea cambios en `id`, `horta_id`, `created_at` mediante `ValueError`.
- **`eliminar_animal`**: Borrado duro directo (`session.delete` + `session.commit`). Non hai soft delete.
- **`listar_animais`**: Filtra por `horta_id` e ordena por `especie`. Non verifica permisos do usuario actual (só `comprobar_rol_horta`).
- **Consistencia**: `listar_animais` usa `session.query(Animal).filter_by(horta_id=horta_id).order_by(Animal.especie).all()`. Funciona, pero é menos eficiente que usar a relación ORM se existise.

### Nos tests (`test_animal.py`)

- **`test_crear_animal_lote`**: Crea unha horta e un animal con lote.
- **Non valida**:
  - Que `data_alta` sexa obrigatorio.
  - Que `especie` sexa obrigatorio.
  - Que `cantidade` sexa > 0.
  - Que `estado` estea permitido.
- **Non testa** borrado, actualización nin permisos.

## Posibles carencias ou melloras

1. **Default para `data_alta`**: Considerar `default=lambda: date.today()` para evitar erro ao crear sen data.
2. **Default para `especie`**: Considerar un valor por defecto ou facer o campo realmente obrigatorio coa documentación adecuada.
3. **Validación de `cantidade`**: Engadir constraint `cantidade > 0`.
4. **Validación de `data_baixa`**: Engadir constraint `data_baixa >= data_alta` (se non é `None`).
5. **Validación de `estado`**: Usar un enum (`Enum`) en vez de `String(50)`. Valores recomendados: `activo`, `baixado`, `inactivo`.
6. **FK `horta_id` con `ondelete=SET NULL` ou `CASCADE`**: Decidir o comportamento esperado cando se elimina a horta.
7. **Definir relacións ORM**: Engadir `relationship()` en `animal.py` e `back_populates` en `horta.py` para mellorar a navegación e a eficiencia das queries.
8. **Soft delete**: Considerar engadir un campo `deleted_at` ou usar `data_baixa` como indicador de borrado lóxico.
9. **Tests**: Engadir tests para validacións de campos obrigatorios, valores permitidos de `estado`, e borrado.

## Cuestións pendentes

1. **Cascada de borrado**: ¿Que debería pasar cando se elimina unha horta? ¿Animais en baixo, ou erro?
2. **`data_alta` vs `created_at`**: `data_alta` é unha data de negocio (alta do animal), `created_at` é unha metadata de sistema. ¿Debería `data_alta` poder ser unha data no pasado?
3. **`cantidade` e `data_baixa`**: Se se baixa un animal, ¿debe actualizarse automaticamente a `cantidade` en cero?
4. **`listar_animais` e permisos**: O servizo comproba o rol do actor pero non verifica que o usuario sexa membro da horta (podería ser admin global).

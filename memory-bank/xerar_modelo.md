# Xerar docs/modelo-datos.md (táboas e relacións)

Executar dende `horta/` e substituír as seccións "Relacións" e "Táboas e campos":

```python
import horta.models  # noqa
from horta.db import Base
md = Base.metadata
fk_in = {}
for t in md.sorted_tables:
    for fk in t.foreign_keys:
        fk_in.setdefault(fk.column.table.name, []).append(f"{t.name}.{fk.parent.name}")
for t in md.sorted_tables:
    fks = [f"{fk.parent.name} → {fk.column.table.name}" for fk in t.foreign_keys]
    if fks:
        print(f"{t.name}: " + ", ".join(sorted(fks)))
for t in sorted(md.tables.values(), key=lambda x: x.name):
    print(f"### {t.name}")
    for c in t.columns:
        fk = ", ".join(f"→ {f.column.table.name}.{f.column.name}" for f in c.foreign_keys)
        print(f"| {c.name} | {c.type} | {'si' if c.nullable else 'non'} | {fk} |")
    if t.name in fk_in:
        print("Apuntan aquí:", ", ".join(sorted(fk_in[t.name])))
```

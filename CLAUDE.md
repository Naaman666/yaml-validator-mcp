# CLAUDE.md – yaml-validator-mcp

## Git munkafolyamat

### Ágak
- `main` – stabil kiadások, csak PR-on keresztül frissül `develop`-ból
- `develop` – aktív fejlesztés, ez az alapértelmezett célág

### Szabályok Claude számára

1. **Soha ne pusholj/commitelj közvetlenül `main`-re.**
2. Minden munkát egy **feature branch**-en végezz, ami `develop`-ból ágazik le.
   - Névminta: `claude/<rövid-leírás>-<id>` (pl. `claude/add-schema-validation-XYz1`)
3. PR-ok mindig **`develop`-ra** irányulnak, soha nem `main`-re.
4. A `develop` → `main` merge-t csak a maintainer végzi el, manuálisan.

### Workflow lépései

```
git checkout develop
git pull origin develop
git checkout -b claude/<feature-name>-<id>
# ... munka, commitok ...
git push -u origin claude/<feature-name>-<id>
# PR létrehozása develop-ra
```

## Projekt

- **Nyelv:** Python 3.11+
- **Tesztek:** `pytest` (58 teszt, 95% lefedettség)
- **Típusellenőrzés:** `mypy --strict`
- **Lint:** `yamllint`, `actionlint`

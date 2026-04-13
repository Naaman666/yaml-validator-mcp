# yaml-validator-mcp

*[English version](README.md)*

MCP szerver determinisztikus YAML validációhoz és automatikus javításhoz. Az AI modellek a YAML-t sima szövegként látják — nem tudják parse-olni és nem veszik észre a szerkezeti hibákat. Ez a szerver parser-alapú validációt és automatikus formázást biztosít, amit bármely MCP-kompatibilis kliens hívhat.

## Funkciók

- **3 rétegű validáció** (`yaml_validate`): szintaxis parse (ruamel.yaml, YAML 1.2), lint (yamllint), és opcionális JSON Schema validáció
- **Automatikus javítás** (`yaml_fix`): indentáció normalizálása, `---` marker hozzáadása, sor végi whitespace eltávolítása, kommentek megőrzése
- **Kommentek megőrzése**: a ruamel.yaml round-trip minden kommentet érintetlenül hagy
- **Strukturált kimenet**: JSON `valid`, `syntax_ok`, `errors[]`, `warnings[]` mezőkkel

## Telepítés

> **Megjegyzés:** Ez a csomag még nincs publikálva a PyPI-re. Telepítsd közvetlenül GitHub-ról az alábbi módszerek valamelyikével.

### Előfeltétel: `uv` telepítése (ez biztosítja az `uvx` parancsot)

Az `uvx` az [`uv`](https://docs.astral.sh/uv/) részeként érkezik. Ha ezt látod:
`A(z) uvx kifejezés nem ismerhető fel parancsmag...`, akkor először telepítsd az `uv`-t:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
vagy
```powershell
winget install --id=astral-sh.uv -e
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Bármelyik platform (pip-pel):**
```bash
pip install uv
```

Telepítés után indítsd újra a terminált, hogy az `uvx` bekerüljön a `PATH`-ba.

### Futtatás uvx-szel (ajánlott, GitHub-ról)

```bash
uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
```

### Telepítés pip-pel (GitHub-ról)

```bash
pip install git+https://github.com/Naaman666/yaml-validator-mcp.git
```

Majd futtasd:

```bash
yaml-validator-mcp
```

### Telepítés helyi klónból

```bash
git clone https://github.com/Naaman666/yaml-validator-mcp.git
cd yaml-validator-mcp
pip install .
```

## Konfiguráció

### Claude Code

Két módon tudod regisztrálni az MCP szervert.

**A lehetőség — CLI (ajánlott):** egyetlen parancs bármelyik shell-ben. Ez automatikusan a megfelelő config fájlt szerkeszti.

```bash
# Felhasználói szint (a gép minden projektjében elérhető)
claude mcp add yaml-validator -s user -- uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp

# vagy projekt szint (az aktuális repo .mcp.json-jába kerül — megosztható a csapattal)
claude mcp add yaml-validator -s project -- uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
```

Ellenőrzés:
```bash
claude mcp list
```

**B lehetőség — kézi szerkesztés:**

- **Felhasználói szintű config** (minden projektre érvényes): `~/.claude.json`
  - Windows: `C:\Users\<FelhasználóNév>\.claude.json` (nálad pl. `C:\Users\Naaman\.claude.json`)
  - macOS / Linux: `~/.claude.json`
- **Projekt szintű config** (repo-nként, git-be commit-olható): `.mcp.json` a projekt gyökerében.

Nyisd meg a fájlt (ha nem létezik, hozd létre) és add hozzá az alábbi `mcpServers` blokkot. Ha a fájlban már van más tartalom, **csak** az `mcpServers` kulcsot egyesítsd a meglévő JSON objektummal — ne írd felül az egész fájlt.

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Naaman666/yaml-validator-mcp.git",
        "yaml-validator-mcp"
      ]
    }
  }
}
```

Mentés után indítsd újra a Claude Code-ot.

### Antigravity

Nyisd meg a config-ot a UI-ból: **Agent panel → további opciók menü → MCP Servers → Manage MCP Servers → View raw config**.

Vagy szerkeszd közvetlenül a fájlt:

- **Windows:** `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
  (nálad pl. `C:\Users\Naaman\.gemini\antigravity\mcp_config.json`)
- **macOS / Linux:** `~/.gemini/antigravity/mcp_config.json`

Add hozzá (vagy egyesítsd) az `mcpServers` blokkot:

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Naaman666/yaml-validator-mcp.git",
        "yaml-validator-mcp"
      ],
      "transport": "stdio"
    }
  }
}
```

Mentés után indítsd újra az Antigravity-t.

## Használat

Miután regisztráltad az MCP szervert és újraindítottad a klienst, az LLM
**automatikusan** látja a `yaml_validate` és `yaml_fix` eszközöket — nem
kell manuálisan meghívnod őket. Egyszerűen természetes nyelven kérdezd
meg, és a modell magától felhasználja az eszközöket, amikor kell.

### Tipikus munkafolyamat

1. Nyisd meg a Claude Code-ot (vagy Antigravity-t) abban a repóban,
   amelyiknek a YAML fájljait ellenőrizni szeretnéd.
2. Írd le egyszerű szöveggel, hogy mit szeretnél.
3. Az első eszközhíváskor a kliens engedélyt kér az MCP tool
   futtatására — engedélyezd.
4. A modell beolvassa a fájlokat, átadja a tartalmat az MCP eszköznek,
   és a strukturált eredményt érthető formában jelenti vissza neked.

### Példa promptok

**Minden workflow fájl ellenőrzése egy repóban:**

```
Ellenőrizd a .github/workflows/ alatti minden YAML fájlt a yaml-validator
MCP-vel. Fájlonként sorold fel a hibákat sorszámokkal.
```

**Egy fájl automatikus javítása és visszamentése:**

```
Futtasd a yaml_fix-et a .github/workflows/deploy.yml-en, mutasd a diff-et,
és ha OK, írd vissza a javított tartalmat a fájlba.
```

**Összegző táblázat több fájlhoz:**

```
Listázd a .github/ alatti összes YAML fájlt, futtasd mindegyiken a
yaml_validate-et (default lint szint), és adj táblázatot:
fájl | valid | hibaszám | warning-ok száma.
```

**Relaxed lint szint (kevesebb stílus-panasz):**

```
Ellenőrizd a docker-compose.yml-t yaml-validator-ral "relaxed" lint
szinten.
```

**JSON Schema validáció (pl. GitHub Actions schema):**

```
Töltsd le a hivatalos GitHub Actions workflow JSON Schema-t, és futtasd
a yaml_validate-et a .github/workflows/ci.yml-re ezzel a schema-val.
Jelezd a szerkezeti hibákat.
```

### Tippek

- **Nem kell minden mondatban megnevezned az eszközt** — elég ennyi:
  *"nézd át a workflow YAML-jaimat hibákért"* —, a modell magától
  rájön, hogy a `yaml_validate`-et kell használnia.
- **Megnevezheted explicit módon** (`"használd a yaml-validator MCP-t"`),
  ha több hasonló eszköz is be van regisztrálva — ez egyértelművé teszi.
- Az első hívásnál engedély-promptot kapsz. Ha sokat használod,
  előre is engedélyezheted a szervert a Claude Code beállításokban.
- **Tömeges műveletnél** kérd meg a modellt, hogy **először listázza a
  fájlokat**, majd fusson rajtuk végig és adjon táblázatot — így
  átláthatóbb az interakció.

## Eszközök

### `yaml_validate`

Három rétegű determinisztikus validáció.

| Paraméter | Típus | Kötelező | Leírás |
|-----------|-------|----------|--------|
| `content` | str | Igen | Nyers YAML sztring |
| `lint_level` | str | Nem | `"default"` / `"relaxed"` / nyers yamllint config sztring |
| `schema` | dict | Nem | JSON Schema a szerkezet validációjához |

**Példa kimenet:**

```json
{
  "valid": false,
  "syntax_ok": true,
  "errors": [
    {"line": 3, "column": 5, "message": "wrong indentation: expected 2 but found 4", "rule": "indentation"}
  ],
  "warnings": []
}
```

### `yaml_fix`

YAML automatikus javítása kommentek megőrzésével. A javítás után automatikusan lefut a validáció.

| Paraméter | Típus | Kötelező | Leírás |
|-----------|-------|----------|--------|
| `content` | str | Igen | Nyers YAML sztring |
| `lint_level` | str | Nem | Javítás utáni lint szint |
| `schema` | dict | Nem | Javítás utáni schema validáció |

**Példa kimenet:**

```json
{
  "fixed_content": "---\nname: test\nvalue: 1\n",
  "fix_error": null,
  "validation": {
    "valid": true,
    "syntax_ok": true,
    "errors": [],
    "warnings": []
  }
}
```

Ha a bemenet nem parse-olható, a `fix_error` tartalmazza a hibaüzenetet, a `fixed_content` pedig az eredeti bemenetet adja vissza változatlanul.

## Fejlesztés

```bash
# Telepítés fejlesztői függőségekkel
pip install -e ".[dev]"

# Tesztek futtatása
pytest --cov=server --cov-report=term-missing -v

# Típusellenőrzés
mypy --strict server.py

# YAML fixture-ök lintelése
yamllint tests/fixtures/valid/
```

## Licenc

MIT

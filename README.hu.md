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

**Kötegelt auto-fix (összes workflow fájl javítása, diff-ek, csak regresszió-mentesen ment):**

```
Futtasd a yaml_fix-et a .github/workflows/ alatti összes YAML fájlra.
Mindegyikhez mutasd a unified diff-et és a fix utáni validation eredményt.
Csak akkor írd vissza a fájlt, ha validation.valid == true ÉS a diff nem üres.
```

**Dry-run fix (csak előnézet, nem mentés):**

```
Futtasd a yaml_fix-et a docker-compose.yml-re, de SEMMIT ne írj vissza.
Csak mutasd a fixed_content-et és a validation blokkot.
```

**Fix majd újra-validáció szigorúbb lint szinttel:**

```
Futtasd a yaml_fix-et a .github/workflows/ci.yml-re, majd a javított
tartalmon futtasd a yaml_validate-et lint_level="default" szinten.
Sorold fel a maradék warning-okat, hogy lássam, mit nem tud az auto-fix
javítani (pl. truthy kulcsokat).
```

**Kombinált ellenőrző-és-javító workflow (a mindennapi prompt):**

```
A .github/ alatti minden YAML fájlra (rekurzívan):

  1. Futtasd a yaml_validate-et default lint szinten. Jegyezd fel:
     előtte:hibák, előtte:warningok.

  2. Ha valid == false VAGY van bármelyik warning:

     a) Futtasd rajta a yaml_fix-et (automatikusan kezeli a `---`
        document markert, indentációt, sor végi whitespace-t).

     b) Aztán alkalmazd ezeket a GitHub-Actions-konvenciónak megfelelő
        kézi transzformokat (Edit-tel, NE hívd újra a yaml_fix-et):

        - Ha bare `on:` kulcs van a 0. oszlopban, idézd: `"on":`
          (különben YAML 1.1 szerint boolean `true`-ként parse-olódik
          — yamllint `truthy` warning).

        - Minden `uses: <owner>/<repo>@<40-char-sha> # vX.Y.Z`
          sornál: mozgasd a verziókommentet AZ ELŐZŐ SORRA mint
          `# <owner>/<repo> vX.Y.Z`, a `uses:` sor legyen tiszta.
          Ez egyszerre javítja a yamllint `comments` (1 space)
          warningokat és a `line-length` hibákat amik a SHA + inline
          komment kombóból jönnek; a renovate.json customManagers
          regex-e ezt a formátumot is felismeri.

        - Minden 80+ karakteres sornál egy `run: |` shell blokkban:
          bontsd szét backslash continuation-nel (`\`) természetes
          határ előtt (`&&`, `||`, `|`, `>`). A folytatás sort
          indeld +2 space-szel. Szemantikai változás nincs.

        - Minden megmaradt inline `# komment`-nél, ahol csak 1 space
          van a `#` előtt (kivéve `uses:` sorokon — azokat már
          hoist-oltad): adj egy második space-t — de CSAK ha ettől
          nem lesz 80+ karakter. Ha igen, mozgasd ezt is felfelé.

  3. Futtasd újra a yaml_validate-et a módosított tartalmon.

  4. Adj táblázatot:
       fájl | előtte:hibák | előtte:warningok |
              utána:hibák  | utána:warningok  | akció

     Akció lehet: `nincs` (eleve tiszta volt),
     `javítva` (hibák ÉS warningok 0-ra, fájl visszaírva),
     `részben-javítva` (csökkent, de maradt — fájl visszaírva),
     `még-hibás` (nem javult vagy syntax error maradt — fájl
     ÉRINTETLEN).

  5. `javítva` és `részben-javítva` esetén írd vissza a módosított
     tartalmat a fájlba.

  6. `még-hibás` és `részben-javítva` esetén sorold fel a maradék
     hibákat és warningokat sorszámmal és szabálynévvel, hogy el
     tudjam dönteni, kézzel javítom-e.
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

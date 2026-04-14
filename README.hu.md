# yaml-validator-mcp

*[English version](README.md)*

MCP szerver determinisztikus YAML validációhoz és automatikus javításhoz. Az AI modellek a YAML-t sima szövegként látják — nem tudják parse-olni és nem veszik észre a szerkezeti hibákat. Ez a szerver parser-alapú validációt és automatikus formázást biztosít, amit bármely MCP-kompatibilis kliens hívhat.

## Funkciók

- **3 rétegű validáció** (`yaml_validate`): szintaxis parse (ruamel.yaml, YAML 1.2), lint (yamllint), és opcionális JSON Schema validáció
- **Automatikus javítás** (`yaml_fix`): indentáció normalizálása, `---` marker hozzáadása, sor végi whitespace eltávolítása, kommentek megőrzése
- **GitHub Actions lintelés** (`gha_validate`, opcionális): [`actionlint`](https://github.com/rhysd/actionlint)-et wrap-eli workflow-specifikus ellenőrzésekhez (expression-ök, matrix hivatkozások, shellcheck a `run:` blokkokban) — olyan hibákat fog, amiket a YAML-szintű validáció nem lát
- **Kommentek megőrzése**: a ruamel.yaml round-trip minden kommentet érintetlenül hagy
- **Strukturált kimenet**: JSON `valid`, `syntax_ok`, `errors[]`, `warnings[]` mezőkkel

### Amit a YAML eszközök **nem** ellenőriznek

A `yaml_validate` és `yaml_fix` determinisztikus, offline, csak-YAML eszközök. Szándékosan **nem**:

- ellenőrzik, hogy egy érték létezik-e a külvilágban — pl. GitHub Action SHA (`uses: actions/checkout@<40-hex>`), `python-version`, `runs-on` runner címke, Docker image tag vagy URL. Egy 40 karakteres hex string szintaktikailag érvényes YAML scalar, így a parser elfogadja, függetlenül attól, hogy a commit ténylegesen létezik-e a GitHub-on.
- nem csinálnak semmilyen hálózati I/O-t (nincs GitHub API, nincs DNS, nincs registry lookup). Ez teszi az eszközöket gyorssá, reprodukálhatóvá és offline / air-gapped CI-ben is használhatóvá.
- nem értik a workflow/alkalmazás szemantikáját — pl. "ez a `needs:` hivatkozás valódi job-ra mutat?", "ez a `${{ expression }}` jól formázott?", "ebben a shell parancsban jók az idézőjelek?".

GitHub Actions workflow fájlokhoz használd a kiegészítő **`gha_validate`** tool-t (lásd lent), ami `actionlint`-et wrap-el és ezeket az Actions-specifikus problémákat elfogja. Annak ellenőrzésére, hogy egy pinnelt action SHA vagy tag ténylegesen létezik-e, használj **Renovate**-et vagy **Dependabot**-ot — azok a GitHub API-val beszélnek és erre a feladatra készültek.

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

A `gha_validate` (GitHub Actions linter) eléréséhez húzd be az
`actionlint-py`-t is ugyanabba az uvx hívásba:

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": [
        "--with", "actionlint-py",
        "--from", "git+https://github.com/Naaman666/yaml-validator-mcp.git",
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

A `gha_validate` támogatáshoz add hozzá az `"--with", "actionlint-py"`
párt az `args` tömbhöz (ugyanaz a minta, mint fent a Claude Code
példánál).

Mentés után indítsd újra az Antigravity-t.

## Használat

Miután regisztráltad az MCP szervert és újraindítottad a klienst, az LLM
**automatikusan** látja a `yaml_validate`, `yaml_fix` és (ha az
`actionlint` elérhető) `gha_validate` eszközöket — nem kell manuálisan
meghívnod őket. Egyszerűen természetes nyelven kérdezd meg, és a modell
magától felhasználja az eszközöket, amikor kell.

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

**GitHub Actions workflow lint (`gha_validate`):**

```
Futtasd a gha_validate-et a .github/workflows/ alatti minden fájlra.
Sorold fel a hibákat fájl, sor, oszlop, rule és üzenet szerint. Ha az
actionlint nem elérhető (available=false), mondd el egyszer és állj
meg — ne próbálkozz minden fájlra újra.
```

**Kombinált ellenőrző-és-javító workflow (a mindennapi prompt):**

```
A .github/ alatti minden YAML fájlra (rekurzívan):

  1. Futtasd a yaml_validate-et default lint szinten. Jegyezd fel:
     előtte:hibák, előtte:warningok. Ha a fájl a .github/workflows/
     alatt van, FUTTASD a gha_validate-et is, és jegyezd fel:
     előtte:gha_hibák. Ha az első gha_validate hívás available=false-t
     ad vissza, jelezd egyszer és a többi fájlnál hagyd ki a gha
     ellenőrzést (nincs telepítve actionlint — csak YAML-szintű
     ellenőrzések futnak).

  2. Ha yaml_validate.valid == false, van bármilyen yaml warning,
     VAGY a gha_validate hibát jelez:

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
          komment kombóból jönnek. Lásd lent: "Renovate
          kompatibilitás" — a hoist-olt formához custom regex
          manager kell, hogy a Renovate továbbra is együtt tudja
          bumpolni a SHA-t és a verziót.

        - Minden 80+ karakteres sornál egy `run: |` shell blokkban:
          bontsd szét backslash continuation-nel (`\`) természetes
          határ előtt (`&&`, `||`, `|`, `>`). A folytatás sort
          indeld +2 space-szel. Szemantikai változás nincs.

        - Minden megmaradt inline `# komment`-nél, ahol csak 1 space
          van a `#` előtt (kivéve `uses:` sorokon — azokat már
          hoist-oltad): adj egy második space-t — de CSAK ha ettől
          nem lesz 80+ karakter. Ha igen, mozgasd ezt is felfelé.

     c) FONTOS: a yaml_fix és a kézi transzformok NEM tudják
        automatikusan javítani a gha_validate hibákat (definiálatlan
        `${{ expression }}`-ök, shellcheck findings a `run:`
        blokkokban, ismeretlen step kulcsok, matrix elgépelések).
        Ezekhez emberi döntés kell — a 6. lépésben listázod őket.

  3. Futtasd újra a yaml_validate-et a módosított tartalmon. Workflow
     fájloknál a gha_validate-et is futtasd újra.

  4. Adj táblázatot:
       fájl | előtte e/w/g | utána e/w/g | akció

     ahol e = yaml hibák, w = yaml warningok, g = gha hibák (nem
     workflow fájloknál, vagy ha az actionlint nem elérhető, használj
     `—` jelet).

     Akció lehet:
       - `nincs`: eleve tiszta volt (minden számláló 0 előtte ÉS utána)
       - `javítva`: yaml hibák=0, yaml warningok=0, gha hibák=0 utána
         — fájl visszaírva
       - `részben-javítva`: yaml hibák=0 és yaml warningok=0 utána,
         de gha hibák maradtak VAGY yaml-szinten csak részben javult
         — fájl visszaírva (yaml_fix megtette a dolgát); a maradék
         hibákat a 6. lépésben listázod
       - `még-hibás`: yaml syntax error maradt, vagy yaml-szinten
         egyáltalán nem javult — fájl ÉRINTETLEN

  5. `javítva` és `részben-javítva` esetén írd vissza a módosított
     tartalmat a fájlba.

  6. `még-hibás` és `részben-javítva` esetén sorold fel a maradék
     hibákat sorszámmal és szabálynévvel:
       - yaml hibák és warningok (yaml_validate-ből)
       - gha_validate hibák (actionlint-ből) — ezeket mindig kézzel
         kell javítani, mert a yaml_fix nem tud workflow szemantikát
         módosítani
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

### Renovate kompatibilitás

A kombinált prompt kézi cleanup-ja **felmozgatja a `# vX.Y.Z`
verziókommentet** a `uses:` sor mögül az előző sorba:

```yaml
# Előtte — Renovate alap action-pin updater-e érti:
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Utána — Renovate alap updater-e már NEM látja a verziókommentet:
# actions/checkout v4.2.2
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

Ha Renovate-et használsz, adj hozzá egy `customManagers` blokkot a
`renovate.json`-odhoz, hogy a hoist-olt formát is felismerje és
együtt tudja bumpolni a SHA-t és a verziót:

```json
{
  "customManagers": [
    {
      "customType": "regex",
      "fileMatch": ["^\\.github/workflows/[^/]+\\.ya?ml$"],
      "matchStrings": [
        "#\\s+(?<depName>[\\w.-]+/[\\w.-]+)\\s+(?<currentValue>v[\\d.]+[\\w.+-]*)\\s*\\n\\s*(?:-\\s+)?uses:\\s+(?<packageName>[\\w.-]+/[\\w.-]+)@(?<currentDigest>[a-f0-9]{40})"
      ],
      "datasourceTemplate": "github-tags",
      "versioningTemplate": "semver-coerced"
    }
  ]
}
```

A pattern multiline: a komment sort és a következő `uses:` sort
egy match-ként fogja össze.

**Dependabot-felhasználóknak** hasonló opt-in kell: a Dependabot csak
az inline `# vX.Y.Z`-t ismeri, és jelenleg **nincs** ekvivalens
custom-regex hook-ja. Két opció: (a) a hoist-transzformot kihagyod
azokban a repókban, ahol Dependabot van, és helyette `.yamllint`
configgal lazítasz, vagy (b) elfogadod a kézi SHA-bumpolást a
hoist-olt entry-knél.

Ha jövőbeli cleanup-transzformok más automatizáló eszközöket törnek
el, ide kerüljenek az eszköz-specifikus fixek.

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

### `gha_validate`

GitHub Actions workflow linter ([`actionlint`](https://github.com/rhysd/actionlint)-et wrap-el). Olyan Actions-specifikus hibákat fog el, amiket a `yaml_validate` nem lát — érvénytelen `${{ expression }}` szintaxis, definiálatlan `matrix.*` / `needs.*` hivatkozások, shellcheck findings a `run:` blokkokban, ismeretlen step kulcsok, rosszul formázott step ID-k, `workflow_call` input típusok, stb.

Mint a többi eszköz, ez is **determinisztikus és offline** — nem hívja a GitHub API-t, így nem tudja megmondani, hogy egy pinnelt action SHA ténylegesen létezik-e a GitHub-on. Arra a Renovate/Dependabot való.

| Paraméter | Típus | Kötelező | Leírás |
|-----------|-------|----------|--------|
| `content` | str | Igen | Nyers workflow YAML (egy `.github/workflows/` alatti fájl tartalma) |

**Szükséges** az `actionlint` bináris a `PATH`-on. Telepítés az alábbiak egyikével:

```bash
pip install actionlint-py        # bundleli a binárist, cross-platform
# vagy
brew install actionlint           # macOS
# vagy
go install github.com/rhysd/actionlint/cmd/actionlint@latest
```

Vagy telepítsd ezt a csomagot a `gha` extrával, ami behúzza az `actionlint-py`-t:

```bash
pip install "yaml-validator-mcp[gha] @ git+https://github.com/Naaman666/yaml-validator-mcp.git"
# vagy uvx-szel — bármelyik szintaxis működik:
uvx --with actionlint-py --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
uvx --from "yaml-validator-mcp[gha] @ git+https://github.com/Naaman666/yaml-validator-mcp.git" yaml-validator-mcp
```

**Példa kimenet (tiszta workflow):**

```json
{
  "valid": true,
  "syntax_ok": true,
  "available": true,
  "errors": [],
  "tool_error": null
}
```

**Példa kimenet (definiálatlan matrix hivatkozás):**

```json
{
  "valid": false,
  "syntax_ok": true,
  "available": true,
  "errors": [
    {"line": 10, "column": 23, "message": "property \"does-not-exist\" is not defined in object type {}", "rule": "expression"}
  ],
  "tool_error": null
}
```

Ha az `actionlint` nincs telepítve, az `available` `false`, a `tool_error` tartalmazza a telepítési útmutatót, a `valid` pedig `true` marad (a hiányzó linter képesség-hiány, nem lint-hiba — a kliensben az `available`/`tool_error` mezőkre ágazz el).

## Fejlesztés

```bash
# Telepítés fejlesztői függőségekkel (magában foglalja az actionlint-py-t a gha_validate tesztekhez)
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

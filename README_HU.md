# yaml-validator-mcp

MCP szerver determinisztikus YAML-validáláshoz – vagyis szabályalapú, nem véletlenszerű ellenőrzéshez – és automatikus javításhoz. Az AI modellek a YAML-t egyszerű szövegként látják — nem tudják szintaktikailag elemezni, és nem észlelik a strukturális hibákat. Ez a szerver parser-alapú validálást és automatikus formázást nyújt, amelyet bármely MCP-kompatibilis kliens meg tud hívni.

## Funkciók

- **3 rétegű validálás** (`yaml_validate`): szintaktikai elemzés (ruamel.yaml, YAML 1.2), lint – vagyis stílusellenőrzés – (yamllint), és opcionális JSON Schema validálás
- **Automatikus javítás** (`yaml_fix`): behúzás normalizálása, `---` marker hozzáadása, trailing whitespace – vagyis sorvégi szóközök – eltávolítása, kommentek megőrzése
- **GitHub Actions lint** (`gha_validate`, opcionális): az [`actionlint`](https://github.com/rhysd/actionlint) köré épített wrapper – vagyis burkoló réteg – workflow-specifikus ellenőrzésekhez (kifejezések, matrix referenciák, shellcheck a `run:` blokkokban) — olyan hibákat is kiszűr, amelyeket a YAML-szintű validálás nem lát
- **Komment-megőrzés**: a ruamel.yaml round-trip – vagyis beolvasás-visszaírás – módban minden kommentet érintetlenül hagy
- **Strukturált kimenet**: JSON `valid`, `syntax_ok`, `errors[]`, `warnings[]` mezőkkel

### Mit **nem** ellenőriznek a YAML-eszközök

A `yaml_validate` és a `yaml_fix` determinisztikus, offline, csak YAML-szintű eszközök. Tervezetten **nem** végzik az alábbiakat:

- nem ellenőrzik, hogy egy érték létezik-e a külvilágban — pl. egy GitHub Action SHA (`uses: actions/checkout@<40-hex>`), `python-version`, `runs-on` runner label, Docker image tag vagy URL. Egy 40 karakteres hex-string szintaktikailag érvényes YAML skaláris, ezért a parser elfogadja, függetlenül attól, hogy a commit ténylegesen létezik-e a GitHubon.
- nem hajtanak végre hálózati I/O-t – vagyis nem kommunikálnak külső szerverekkel (nincs GitHub API, DNS, registry lookup). Ez gyorssá, reprodukálhatóvá és offline / air-gapped CI-ban is használhatóvá teszi az eszközöket.
- nem értik a workflow/alkalmazás szemantikáját – vagyis nem tudják megmondani, hogy "a `needs:` referencia valós jobot mutat-e?", "jól formázott-e ez a `${{ kifejezés }}`?", "helyes-e a shell parancs idézőjelezése?".

GitHub Actions workflow fájlokhoz használd a kiegészítő **`gha_validate`** eszközt (lásd lentebb), amely az `actionlint`-et burkolja be, és valóban elkapja ezeket az Actions-specifikus problémákat. A pinned action SHA-k vagy tagek tényleges létezésének ellenőrzéséhez használj **Renovate**-et vagy **Dependabot**-ot — ezek kommunikálnak a GitHub API-val, és erre a feladatra tervezték őket.

## Telepítés

> **Megjegyzés:** Ez a csomag még nincs publikálva a PyPI-ra. Telepítsd közvetlenül GitHubról az alábbi módszerek egyikével.

### Előfeltétel: az `uv` telepítése (ez biztosítja az `uvx` parancsot)

Az `uvx` az [`uv`](https://docs.astral.sh/uv/) csomag része. Ha `'uvx' is not recognized...` hibaüzenetet kapsz, először telepítsd az `uv`-t:

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

**Bármely platformon (pip-pel):**
```bash
pip install uv
```

Telepítés után indítsd újra a terminált, hogy az `uvx` elérhető legyen a PATH-ban.

### Futtatás uvx-szel (ajánlott, GitHubról)

```bash
uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
```

### Telepítés pip-pel (GitHubról)

```bash
pip install git+https://github.com/Naaman666/yaml-validator-mcp.git
```

Majd futtatás:

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

Az MCP szerver regisztrálásához két lehetőség áll rendelkezésre.

**A lehetőség — CLI (ajánlott):** egy parancs bármely shellből. Ez automatikusan szerkeszti a megfelelő konfigfájlt.

```bash
# User scope (minden projekten elérhető a gépen)
claude mcp add yaml-validator -s user -- uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp

# vagy project scope (a .mcp.json fájlba kerül az aktuális repóban — megosztható a csapattal)
claude mcp add yaml-validator -s project -- uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
```

Ellenőrzés:
```bash
claude mcp list
```

**B lehetőség — kézzel szerkeszd a konfigfájlt:**

- **User-scoped konfig** (minden projektre érvényes): `~/.claude.json`
  - Windows: `C:\Users\<NevedHere>\.claude.json`
  - macOS / Linux: `~/.claude.json`
- **Project-scoped konfig** (repo-specifikus, commitolható): `.mcp.json` a projekt gyökerében.

Nyisd meg a fájlt (ha nem létezik, hozd létre), és add hozzá az `mcpServers` blokkot. Ha a fájl már tartalmaz egyéb tartalmat, csak az `mcpServers` kulcsot merge-eld – vagyis illeszd bele – a meglévő JSON objektumba, ne írd felül az egész fájlt.

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

A `gha_validate` engedélyezéséhez (GitHub Actions linter) add hozzá az `actionlint-py`-t ugyanabban az uvx hívásban:

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

Szerkesztés után indítsd újra a Claude Code-ot.

### Antigravity

Nyisd meg a konfigot a UI-on keresztül: **Agent panel → további beállítások menü → MCP Servers → Manage MCP Servers → View raw config**.

Vagy szerkeszd közvetlenül a fájlt:

- **Windows:** `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
- **macOS / Linux:** `~/.gemini/antigravity/mcp_config.json`

Add hozzá (vagy merge-eld) az `mcpServers` blokkot:

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

A `gha_validate` támogatáshoz add hozzá a `"--with", "actionlint-py"` argumentumokat az `args` tömbhöz (ugyanúgy, mint a Claude Code példában).

Szerkesztés után indítsd újra az Antigravity-t.

## Használat

Miután az MCP szerver regisztrálva van és a klienst újraindítottad, az LLM automatikusan látja a `yaml_validate`, `yaml_fix`, és (ha az `actionlint` elérhető) a `gha_validate` eszközöket — nem kell manuálisan hívni őket. Csak írj természetes nyelven, és a modell szükség esetén meghívja az eszközöket.

### Tipikus munkafolyamat

1. Nyisd meg a Claude Code-ot (vagy Antigravity-t) abban a repóban, amelynek YAML fájljait ellenőrizni szeretnéd.
2. Írd le természetes nyelven, mit szeretnél.
3. Az első eszközhívásnál a kliens engedélyt kér az MCP eszköz futtatásához — hagyd jóvá.
4. A modell beolvassa a fájl(oka)t, átadja a tartalmat az MCP eszköznek, és visszajelzi a strukturált eredményt.

### Példa promptok

**Összes workflow fájl validálása egy repóban:**

```
Ellenőrizz minden YAML fájlt a .github/workflows/ könyvtárban a yaml-validator MCP-vel.
Sorold fel a hibákat fájlonként, sorszámmal.
```

**Egyetlen fájl automatikus javítása és visszamentése:**

```
Futtasd a yaml_fix-et a .github/workflows/deploy.yml fájlon, mutasd meg a diffet,
és ha rendben van, írd vissza a javított tartalmat a fájlba.
```

**Tömeges automatikus javítás (összes workflow fájl javítása, diffek megjelenítése, csak regresszió nélküli mentés):**

```
Minden YAML fájlra a .github/workflows/ alatt, futtasd a yaml_fix-et. Minden fájlnál
mutass egy unified diffet és a javítás utáni validálási eredményt. Csak akkor írd
vissza a fájlt, ha validation.valid igaz és a diff nem üres.
```

**Száraz futás – vagyis csak előnézet, soha nem ment:**

```
Futtasd a yaml_fix-et a docker-compose.yml-en, de NE írj semmit. Csak mutasd meg
a fixed_content-et és a validation blokkot.
```

**Javítás, majd újravalidálás szigorúbb lint szinttel:**

```
Futtasd a yaml_fix-et a .github/workflows/ci.yml-en, majd futtasd a yaml_validate-et
a javított tartalmon lint_level="default" beállítással. Jelezd a maradék figyelmeztetéseket,
hogy tudjam, mit nem tudott automatikusan javítani (pl. truthy kulcsok).
```

**GitHub Actions workflow lint (`gha_validate`):**

```
Futtasd a gha_validate-et minden fájlra a .github/workflows/ alatt. Jelezd a hibákat
fájl, sor, oszlop, szabály és üzenet adatokkal. Ha az actionlint nem elérhető
(available=false), jelezd egyszer és állj meg — ne próbálkozz újra fájlonként.
```

**Kombinált validálás-és-javítás munkafolyamat (a mindennapi prompt):**

```
Minden YAML fájlra a .github/ alatt (rekurzívan):

  1. Futtasd a yaml_validate-et alapértelmezett lint szinttel. Rögzítsd: before:errors,
     before:warnings. Ha a fájl a .github/workflows/ alatt van, futtasd a gha_validate-et
     is, és rögzítsd: before:gha_errors. Ha az első gha_validate hívás available=false-t
     jelez, jegyezd meg egyszer, és hagyd ki a gha ellenőrzéseket a többi fájlnál
     (az actionlint nincs telepítve — csak yaml-szintű ellenőrzések futnak).

  2. Ha yaml_validate.valid hamis, vannak yaml figyelmeztetések, VAGY a gha_validate
     hibákat jelez:

     a) Futtasd a yaml_fix-et a fájlon (ez automatikusan kezeli a `---` document
        markert, a behúzás normalizálását, a trailing whitespace-t).

     b) Ezután alkalmazd ezeket a GitHub-Actions-barát manuális átalakításokat
        (használj Edit-et, NE hívd meg újra a yaml_fix-et):

        - Ha egy csupasz `on:` kulcs a 0. oszlopban van, idézőjelezd `"on":`-ra
          a YAML 1.1 truthy kétértelműség elhallgattatásához (`on` boolean true-ként
          értelmezhető egyébként).

        - Minden `uses: <owner>/<repo>@<40-char-sha> # vX.Y.Z` sorban: emeld fel
          a verziókommentet az ELŐZŐ sorba `# <owner>/<repo> vX.Y.Z` formátumban,
          a `uses:` sort hagyd meg komment nélkül. Ez javítja a yamllint `comments`
          (1-szóköz) figyelmeztetéseket és a SHA + inline komment kombó miatt
          keletkező `line-length` hibákat.
          Lásd "Renovate kompatibilitás" lentebb — az emelt formátumhoz egyéni
          regex manager szükséges, hogy a Renovate képes legyen együtt frissíteni
          a SHA-t és a verziót.

        - Ha bármely sor 80 karakternél hosszabb egy `run: |` shell blokkban:
          törd meg backslash folytatással (`\`) egy természetes határon (`&&`, `||`,
          `|`, `>`). A folytatást 2 szóközzel beljebb indentáld. Szemantikai
          változás nincs.

        - Ha bármely fennmaradó inline `# komment`nél csak 1 szóköz van a `#` előtt
          (nem `uses:` sorokon, azok már fel vannak emelve): adj hozzá egy második
          szóközt — de csak akkor, ha ez NEM tolja a sort 80 karakter fölé.
          Ha igen, emeld fel azt a kommentet is.

     c) MEGJEGYZÉS: a yaml_fix és a manuális átalakítások NEM tudják automatikusan
        javítani a gha_validate hibákat (nem definiált `${{ kifejezések }}`,
        shellcheck megállapítások `run:` blokkokban, ismeretlen step kulcsok,
        matrix elírások). Ezek emberi felülvizsgálatot igényelnek — a 6. lépésben
        jelennek meg.

  3. Futtasd újra a yaml_validate-et a módosított tartalmon. Workflow fájloknál
     futtasd újra a gha_validate-et is.

  4. Mutass egy táblázatot:
       fájl | before e/w/g | after e/w/g | művelet

     ahol e = yaml hibák, w = yaml figyelmeztetések, g = gha hibák (használj
     `—`-t nem-workflow fájloknál vagy ha az actionlint nem elérhető).

     A művelet értékei:
       - `none`: minden számláló nulla volt before ÉS after (már tiszta volt)
       - `fixed`: yaml errors=0, yaml warnings=0, gha errors=0 after
         — fájl visszamentve
       - `partially-fixed`: yaml errors=0 és yaml warnings=0 after, de gha hibák
         maradtak VAGY a yaml problémák csak részben javultak — fájl visszamentve
         (a yaml_fix elvégezte a feladatát); maradék problémák a 6. lépésben
       - `still-broken`: yaml szintaktikai hiba maradt, vagy yaml-szinten
         egyáltalán nem javult — fájl NEM módosítva

  5. `fixed` és `partially-fixed` esetén írd vissza a módosított tartalmat a lemezre.

  6. `still-broken` és `partially-fixed` esetén sorold fel a maradék problémákat
     sorszámmal és szabálynévvel:
       - yaml hibák és figyelmeztetések (a yaml_validate-ből)
       - gha_validate hibák (az actionlint-ből) — ezek mindig manuális javítást
         igényelnek, mivel a yaml_fix nem tudja módosítani a workflow szemantikáját
```

**Összesítő táblázat sok fájlra:**

```
Sorold fel az összes YAML fájlt a .github/ alatt, futtasd mindegyiken a yaml_validate-et
(alapértelmezett lint szint), és adj egy táblázatot: fájl | valid | errors | warnings.
```

**Lazított lint szint (kevesebb stílushibázás):**

```
Validáld a docker-compose.yml-t a yaml-validátorral, lint_level="relaxed" beállítással.
```

**JSON Schema validálás (pl. GitHub Actions schema):**

```
Töltsd le a hivatalos GitHub Actions workflow JSON Schemát, és futtasd a yaml_validate-et
a .github/workflows/ci.yml-en azzal a sémával. Jelezd a strukturális hibákat.
```

### Tippek

- Nem kell minden mondatban megnevezni az eszközt — *"ellenőrizd a workflow YAML-jaimat hibák szempontjából"* is elég; a modell rájön, hogy `yaml_validate` kell.
- Megnevezheted explicit módon (`"használd a yaml-validator MCP-t"`), ha több hasonló eszköz van regisztrálva — ez eltávolítja a kétértelműséget.
- Az első híváskor megjelenik egy engedélykérő ablak. A Claude Code beállításokban előre jóvá hagyhatod a szervert, ha sokat használod.
- Tömeges műveleteknél kérd a modellt, hogy **először listázza a fájlokat**, majd futtassa az eszközt ciklusban és mutasson egy táblázatot — ez áttekhetőbbé teszi az interakciót.

### Renovate kompatibilitás

A kombinált prompt manuális tisztítása a `# vX.Y.Z` verziókommenteket a `uses:` sorról az előző sorba emeli:

```yaml
# Előtte — a Renovate alapértelmezett action-pin updater-e érti ezt:
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Utána a tisztítás után — a Renovate alapértelmezett updater-e már nem látja
# a verziókommentet:
# actions/checkout v4.2.2
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

Ha Renovate-et használsz, adj hozzá egy `customManagers` bejegyzést a `renovate.json`-odhoz, hogy a Renovate képes legyen együtt frissíteni a SHA-t és a verziót az emelt formátumban:

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

A minta többsoros: egyszerre fogja meg a komment sort és az azt követő `uses:` sort.

**Dependabot felhasználóknak** hasonló opt-in szükséges: a Dependabot csak az inline `# vX.Y.Z`-t ismeri fel, és jelenleg nincs egyenértékű custom-regex hook. Két megoldás: (a) hagyd el az emelési transzformációt Dependabot-ot használó repókban, és inkább egy `.yamllint` konfiggal lazítsd a szabályokat, vagy (b) fogadd el a manuális SHA frissítéseket az emelt bejegyzéseknél.

Ha jövőbeli tisztítási transzformációk más automatizálási eszközt törnek meg, ezt a szakaszt bővítsd az eszközspecifikus megoldással.

## Eszközök

### `yaml_validate`

Háromrétegű determinisztikus validálás.

| Paraméter | Típus | Kötelező | Leírás |
|-----------|-------|----------|--------|
| `content` | str | Igen | Nyers YAML string |
| `lint_level` | str | Nem | `"default"` / `"relaxed"` / nyers yamllint konfig string |
| `schema` | dict | Nem | JSON Schema strukturális validáláshoz |

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

YAML automatikus javítása komment-megőrzéssel. A javítás utáni validálás automatikusan fut.

| Paraméter | Típus | Kötelező | Leírás |
|-----------|-------|----------|--------|
| `content` | str | Igen | Nyers YAML string |
| `lint_level` | str | Nem | Javítás utáni lint szint |
| `schema` | dict | Nem | Javítás utáni schema validálás |

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

Ha a bemenet nem értelmezhető, a `fix_error` tartalmazza a hibaüzenetet, és a `fixed_content` az eredeti bemenetet változatlanul adja vissza.

### `gha_validate`

GitHub Actions workflow linter (az [`actionlint`](https://github.com/rhysd/actionlint) köré épített wrapper). Actions-specifikus problémákat kap el, amelyeket a `yaml_validate` nem lát — érvénytelen `${{ kifejezés }}` szintaxis, nem definiált `matrix.*` / `needs.*` referenciák, shellcheck megállapítások `run:` blokkokban, ismeretlen step kulcsok, rosszul formázott step ID-k, `workflow_call` input típusozás, stb.

A többi eszközhöz hasonlóan ez is **determinisztikus és offline** — nem kommunikál a GitHub API-val, tehát nem tudja megmondani, hogy egy pinned action SHA ténylegesen létezik-e a GitHubon. Erre Renovate-et/Dependabot-ot használj.

| Paraméter | Típus | Kötelező | Leírás |
|-----------|-------|----------|--------|
| `content` | str | Igen | Nyers workflow YAML (egy `.github/workflows/` alatti fájl tartalma) |

**Szükséges** az `actionlint` bináris a PATH-ban. Telepítési lehetőségek:

```bash
pip install actionlint-py        # magában hordozza a binárist, cross-platform
# vagy
brew install actionlint           # macOS
# vagy
go install github.com/rhysd/actionlint/cmd/actionlint@latest
```

Vagy telepítsd ezt a csomagot a `gha` extra-val, ami behúzza az `actionlint-py`-t:

```bash
pip install "yaml-validator-mcp[gha] @ git+https://github.com/Naaman666/yaml-validator-mcp.git"
# vagy uvx-szel — mindkét szintaxis működik:
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

**Példa kimenet (nem definiált matrix referencia):**

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

Ha az `actionlint` nincs telepítve, az `available` értéke `false`, a `tool_error` tartalmazza a telepítési útmutatót, és a `valid` `true` marad (egy hiányzó linter képességbeli hiány, nem lint hiba — a kliensben az `available`/`tool_error` alapján ágazz el).

## Fejlesztés

```bash
# Telepítés dev függőségekkel (tartalmazza az actionlint-py-t a gha_validate tesztekhez)
pip install -e ".[dev]"

# Tesztek futtatása
pytest --cov=server --cov-report=term-missing -v

# Típusellenőrzés
mypy --strict server.py

# YAML fixture-ök lint-elése
yamllint tests/fixtures/valid/
```

## Megbízhatóság és hatókör

Ezek az eszközök **determinisztikus parserek és linterek**, nem valószínűségi detektorok – vagyis nem találgatnak, hanem szabályok alapján döntenek. Nincs bennük heurisztika, ML, LLM reasoning. Ez meghatározza, hogyan gondolj a megbízhatóságra:

- **A konfigurált hatókörön belül a téves negatív / téves pozitív arány – vagyis az elmulasztott vagy téves hibák aránya – lényegében nulla.** Az alapul szolgáló motorok — ruamel.yaml (YAML 1.2 parser), yamllint (szabályalapú linter), jsonschema (Draft 7), actionlint — érett, széles körben alkalmazott projektek. Ha valódi hatóköri hiányt vagy téves egyezést tapasztalsz, az szinte mindig egy upstream hiba, amely egy egysoros YAML példával reprodukálható; azt a megfelelő projektnek jelezd (yamllint, actionlint, jsonschema), nem ide.

- **"Átment" ≠ "helyes".** A tiszta `valid: true` eredmény azt jelenti: *"az alkalmazott szabálykészletben egyetlen szabály sem illeszkedett semmire ebben a fájlban"*. **Nem** jelenti azt, hogy "ez a YAML azt csinálja, amit szándékozol", vagy hogy "ez a workflow biztonságosan futtatható". Az alkalmazásszintű helyesség (jó-e a `needs:` gráf? az `if:` feltétel egyezik-e a szándékoddal? a shell parancs a helyes dolgot csinálja-e az adataiddal?) hatókörön kívül esik — nincs itt olyan modell, amely értené a szándékodat.

- **Detekciós lefedettség ≠ javítási lefedettség.** A `yaml_fix` automatikusan csak a `yaml_validate` által detektáltak *szigorú részhalmazát* javítja. A kombinált prompt dokumentálja a fennmaradó manuális transzformációkat (`on:` idézőjelezés, `uses:` emelés, shell sortörések, komment szóközök). A leggyakoribb problémák összefoglalója:

  | Probléma | `yaml_validate` detektálja? | `yaml_fix` automatikusan javítja? |
  |---|:---:|:---:|
  | Tab behúzás | ✅ | ✅ (ruamel round-trip) |
  | Hiányzó `---` marker | ✅ | ✅ |
  | Trailing whitespace – sorvégi szóköz | ✅ | ✅ |
  | Rossz behúzásszélesség | ✅ | ✅ |
  | `on:` truthy figyelmeztetés | ✅ | ❌ (manuális) |
  | `line-length` > 80 | ✅ | ❌ (manuális) |
  | Inline komment 1-szóköz | ✅ | ❌ (manuális) |
  | Nem definiált `${{ matrix.x }}` | ❌ (`gha_validate`) | ❌ |
  | Shellcheck megállapítás `run:`-ban | ❌ (`gha_validate`) | ❌ |
  | Nem létező action SHA | ❌ (Renovate / Dependabot) | ❌ |
  | Hiányzó kötelező kulcs | csak JSON Schema-val | ❌ |

- **A hatókörön kívüli hiányok előre dokumentálva vannak** a fent lévő [*Mit nem ellenőriznek a YAML-eszközök*](#mit-nem-ellenőriznek-a-yaml-eszközök) szakaszban. Ha valami fontos a workflow-od számára abban a listában szerepel, párosítsd ezt az MCP-t az ott megnevezett eszközzel (`gha_validate`, Renovate, Dependabot, JSON Schema).

**Lényeg:** úgy gondolj erre az MCP-re, mint egy precíz vonalzóra, nem egy okos reviewer-re – vagyis ellenőrző eszközre, nem értelmező kollégára. Megbízhatóan megméri, amire tervezték, és tisztességesen nem mond semmit arról, amire nem tervezték.

## Licenc

MIT

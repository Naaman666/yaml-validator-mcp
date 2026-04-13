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

Add hozzá a Claude Code MCP konfigurációhoz:

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

### Antigravity

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

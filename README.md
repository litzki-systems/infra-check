# infra-check

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**infra-check** is a single-file command-line tool that inspects any domain for
machine-readable infrastructure signals — the kind of things that determine how
well a site can be understood by crawlers, AI agents, and automated clients.
It runs five checks per domain and produces a binary **PASS / FAIL** verdict,
with optional CSV or JSON export for batch runs.

## What it checks

| # | Check | What it looks for |
|---|-------|-------------------|
| 1 | **JSON-LD** | Presence of valid `application/ld+json` structured data on the homepage, and the `@type`s it declares. |
| 2 | **llms.txt** | Whether the domain serves a non-trivial `/llms.txt` file at the root. |
| 3 | **robots.txt** | Whether `/robots.txt` exists, whether generic bots are allowed, and which known AI crawlers (GPTBot, ClaudeBot, Google-Extended, CCBot, …) are blocked. |
| 4 | **Headers** | HTTP status, a valid `text/html` content type, and the presence of common security headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP). |
| 5 | **SSL/TLS** | That the domain responds over HTTPS without certificate errors. |

A domain **passes** when at least **3 of the 5** checks pass.

## Installation

infra-check needs Python 3 and a single dependency:

```bash
pip install requests
```

Then grab the script and run it directly — no packaging or install step required:

```bash
python infra-check.py --help
```

## Usage

### Single domain

```bash
python infra-check.py example.com
```

### Multiple domains

```bash
python infra-check.py example.com another.com third.org
```

### Batch from a file

Provide a text file with one domain per line (blank lines and `#` comments are
ignored):

```bash
python infra-check.py --file domains.txt
```

### Export to CSV

```bash
python infra-check.py --file domains.txt --csv results.csv
```

### Export to JSON

```bash
python infra-check.py --file domains.txt --json-out results.json
```

### Quiet mode (verdict lines only)

```bash
python infra-check.py --file domains.txt --quiet
```

### All options

| Option | Description |
|--------|-------------|
| `domains` | One or more domains to check (e.g. `example.com`). |
| `--file`, `-f` | Path to a text file with one domain per line. |
| `--csv` | Write full results to a CSV file. |
| `--json-out` | Write full results to a JSON file. |
| `--quiet`, `-q` | Only print the verdict lines. |

## Sample output

```
Checking 2 domain(s)...

✅  example.com  [PASS]  (4/5 checks passed)
   JSON-LD:     valid (Organization, WebSite)
   llms.txt:    missing
   robots.txt:  open
   Headers:     HTTP 200, security headers: yes
   SSL/TLS:     valid

❌  broken.example  [FAIL]  (1/5 checks passed)
   JSON-LD:     missing
   llms.txt:    missing
   robots.txt:  missing
   Headers:     unreachable
   SSL/TLS:     SSL error: certificate verify failed

==================================================
Total: 2 | Passed: 1 | Failed: 1
```

## License

Released under the [MIT License](LICENSE).

## Author

**Thorsten Litzki** — [Litzki Systems LLC](https://litzki-systems.com)

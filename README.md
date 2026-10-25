# infra-check

**English** · [Deutsch](#deutsch)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**infra-check** is a single-file command-line tool that inspects any domain for
machine-readable infrastructure signals: the things that decide how well a site
can be understood by crawlers, AI agents and automated clients. It runs five
checks per domain and produces a binary **PASS / FAIL** verdict, with optional
CSV or JSON export for batch runs.

## Measured, not estimated

Every result comes from a live request to the domain at the moment you run the
tool. There is no score model, no weighting and no estimate: each check either
finds the signal or it does not, and the raw findings are in the CSV or JSON
export. Requests identify themselves as
`InfraCheck/1.0 (+https://litzki-systems.com/infra-check)` and time out after
15 seconds.

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

Then run the script directly, no packaging or install step required:

```bash
python infra-check.py --help
```

## Usage

```bash
# Single domain
python infra-check.py example.com

# Multiple domains
python infra-check.py example.com another.com third.org

# Batch from a file (one domain per line, blank lines and # comments are ignored)
python infra-check.py --file domains.txt

# Export
python infra-check.py --file domains.txt --csv results.csv
python infra-check.py --file domains.txt --json-out results.json

# Verdict lines only
python infra-check.py --file domains.txt --quiet
```

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

## Limits

- The checks look at the homepage and the root files only. Deep pages are not inspected.
- PASS / FAIL is a technical presence check. It says nothing about rankings, citations or visibility in AI answers.
- Some sites block automated requests. A failed request is reported as such, not guessed around.

## License

Released under the [MIT License](LICENSE).

## Author

Thorsten Litzki · [Litzki Systems](https://litzki-systems.com)

---

<a id="deutsch"></a>

# infra-check (Deutsch)

[English](#infra-check) · **Deutsch**

**infra-check** ist ein Kommandozeilen-Werkzeug in einer einzigen Datei. Es prüft
beliebige Domains auf maschinenlesbare Infrastruktur-Signale, also auf das, was
bestimmt, wie gut Crawler, KI-Agenten und automatisierte Clients eine Website
verstehen. Pro Domain laufen fünf Prüfungen, das Ergebnis ist ein klares
**PASS / FAIL**, auf Wunsch mit CSV- oder JSON-Export für Massenprüfungen.

## Gemessen statt geschätzt

Jedes Ergebnis stammt aus einer echten Anfrage an die Domain im Moment der
Prüfung. Es gibt kein Score-Modell, keine Gewichtung und keine Schätzung: Jede
Prüfung findet das Signal oder nicht, die Rohdaten stehen im CSV- oder
JSON-Export. Anfragen geben sich als
`InfraCheck/1.0 (+https://litzki-systems.com/infra-check)` zu erkennen und
brechen nach 15 Sekunden ab.

## Was geprüft wird

| # | Prüfung | Worauf sie achtet |
|---|-------|-------------------|
| 1 | **JSON-LD** | Gültige strukturierte Daten (`application/ld+json`) auf der Startseite und die angegebenen `@type`s. |
| 2 | **llms.txt** | Ob unter `/llms.txt` eine Datei mit Inhalt liegt. |
| 3 | **robots.txt** | Ob `/robots.txt` existiert, ob allgemeine Bots zugelassen sind und welche bekannten KI-Crawler (GPTBot, ClaudeBot, Google-Extended, CCBot, …) gesperrt sind. |
| 4 | **Header** | HTTP-Status, Content-Type `text/html` und gängige Sicherheits-Header (HSTS, X-Content-Type-Options, X-Frame-Options, CSP). |
| 5 | **SSL/TLS** | Ob die Domain über HTTPS ohne Zertifikatsfehler antwortet. |

Eine Domain besteht, wenn mindestens **3 von 5** Prüfungen bestanden sind.

## Installation und Nutzung

```bash
pip install requests
python infra-check.py example.com
python infra-check.py --file domains.txt --csv ergebnisse.csv
```

Alle Optionen stehen in der Tabelle im englischen Teil.

## Grenzen

- Geprüft werden nur die Startseite und die Dateien im Stammverzeichnis.
- PASS / FAIL ist eine technische Vorhandensein-Prüfung, keine Aussage über Rankings, Zitierungen oder Sichtbarkeit in KI-Antworten.
- Manche Websites blockieren automatisierte Anfragen. Eine gescheiterte Anfrage wird als solche gemeldet, nicht geschätzt.

## Lizenz

[MIT-Lizenz](LICENSE).

## Autor

Thorsten Litzki · [Litzki Systems](https://litzki-systems.com)

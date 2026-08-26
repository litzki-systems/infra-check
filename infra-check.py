#!/usr/bin/env python3
"""
infra-check.py — Check any domain for machine-readable infrastructure signals.

Checks JSON-LD, llms.txt, robots.txt bot directives, and HTTP response headers.
Outputs a binary PASS/FAIL per domain, with optional CSV or JSON export.

Usage:
    python infra-check.py example.com
    python infra-check.py example.com another.com --json
    python infra-check.py --file domains.txt --csv results.csv
    python infra-check.py --file domains.txt --json-out results.json

Author: Thorsten Litzki (Litzki Systems LLC)
License: MIT
"""

import argparse
import csv
import json
import re
import sys
import time
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("This tool requires the 'requests' library.")
    print("Install it with: pip install requests")
    sys.exit(1)

TIMEOUT = 15
USER_AGENT = "InfraCheck/1.0 (+https://litzki-systems.com/infra-check)"
PASS_THRESHOLD = 3  # minimum checks that must pass


def check_json_ld(domain: str, session: requests.Session) -> dict:
    """Fetch the homepage and look for valid JSON-LD blocks."""
    url = f"https://{domain}"
    result = {"signal": "json_ld", "found": False, "valid": False, "types": [], "error": None}

    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        result["error"] = str(e)[:120]
        return result

    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        re.DOTALL | re.IGNORECASE,
    )
    matches = pattern.findall(resp.text)

    if not matches:
        return result

    result["found"] = True
    types_found = []

    for raw in matches:
        try:
            data = json.loads(raw.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                t = item.get("@type", "")
                if t:
                    types_found.append(t if isinstance(t, str) else str(t))
        except (json.JSONDecodeError, AttributeError):
            continue

    if types_found:
        result["valid"] = True
        result["types"] = types_found

    return result


def check_llms_txt(domain: str, session: requests.Session) -> dict:
    """Check whether the domain serves an llms.txt file at the root."""
    url = f"https://{domain}/llms.txt"
    result = {"signal": "llms_txt", "found": False, "size_bytes": 0, "error": None}

    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 200 and "text" in resp.headers.get("content-type", ""):
            body = resp.text.strip()
            if len(body) > 20 and not body.startswith("<!"):
                result["found"] = True
                result["size_bytes"] = len(body.encode("utf-8"))
    except requests.RequestException as e:
        result["error"] = str(e)[:120]

    return result


def check_robots_txt(domain: str, session: requests.Session) -> dict:
    """Parse robots.txt for bot-related directives."""
    url = f"https://{domain}/robots.txt"
    result = {
        "signal": "robots_txt",
        "found": False,
        "allows_generic_bots": True,
        "blocks_ai_bots": False,
        "ai_bot_rules": [],
        "error": None,
    }

    known_ai_bots = [
        "gptbot", "chatgpt-user", "claudebot", "anthropic",
        "google-extended", "ccbot", "bytespider", "cohere-ai",
        "perplexitybot", "amazonbot",
    ]

    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            return result
        if "text" not in resp.headers.get("content-type", ""):
            return result
    except requests.RequestException as e:
        result["error"] = str(e)[:120]
        return result

    result["found"] = True
    lines = resp.text.lower().splitlines()
    current_agent = None

    for line in lines:
        line = line.split("#")[0].strip()
        if line.startswith("user-agent:"):
            current_agent = line.split(":", 1)[1].strip()
        elif line.startswith("disallow:") and current_agent:
            path = line.split(":", 1)[1].strip()
            if path == "/" and current_agent == "*":
                result["allows_generic_bots"] = False
            if path == "/" and current_agent in known_ai_bots:
                result["blocks_ai_bots"] = True
                result["ai_bot_rules"].append(current_agent)

    return result


def check_headers(domain: str, session: requests.Session) -> dict:
    """Inspect HTTP response headers for machine-readability signals."""
    url = f"https://{domain}"
    result = {
        "signal": "headers",
        "status_code": None,
        "has_security_headers": False,
        "content_type_valid": False,
        "server": None,
        "error": None,
    }

    security_headers = [
        "strict-transport-security",
        "x-content-type-options",
        "x-frame-options",
        "content-security-policy",
    ]

    try:
        resp = session.head(url, timeout=TIMEOUT, allow_redirects=True)
        result["status_code"] = resp.status_code

        ct = resp.headers.get("content-type", "")
        result["content_type_valid"] = "text/html" in ct

        present = sum(1 for h in security_headers if h in resp.headers)
        result["has_security_headers"] = present >= 2

        result["server"] = resp.headers.get("server", "")[:60]

    except requests.RequestException as e:
        result["error"] = str(e)[:120]

    return result


def check_ssl(domain: str, session: requests.Session) -> dict:
    """Verify that the domain responds over HTTPS without certificate errors."""
    url = f"https://{domain}"
    result = {"signal": "ssl", "valid": False, "error": None}

    try:
        resp = session.head(url, timeout=TIMEOUT, allow_redirects=True)
        result["valid"] = True
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error: {str(e)[:100]}"
    except requests.RequestException as e:
        result["error"] = str(e)[:100]

    return result


def evaluate_domain(domain: str) -> dict:
    """Run all checks against a single domain and produce a verdict."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    checks = {
        "json_ld": check_json_ld(domain, session),
        "llms_txt": check_llms_txt(domain, session),
        "robots_txt": check_robots_txt(domain, session),
        "headers": check_headers(domain, session),
        "ssl": check_ssl(domain, session),
    }

    passing = 0
    if checks["json_ld"]["found"] and checks["json_ld"]["valid"]:
        passing += 1
    if checks["llms_txt"]["found"]:
        passing += 1
    if checks["robots_txt"]["found"] and checks["robots_txt"]["allows_generic_bots"]:
        passing += 1
    if checks["headers"]["content_type_valid"] and checks["headers"]["has_security_headers"]:
        passing += 1
    if checks["ssl"]["valid"]:
        passing += 1

    verdict = "PASS" if passing >= PASS_THRESHOLD else "FAIL"

    return {
        "domain": domain,
        "verdict": verdict,
        "passing": passing,
        "total": 5,
        "checks": checks,
    }


def print_result(result: dict) -> None:
    """Print a human-readable summary for one domain."""
    icon = "✅" if result["verdict"] == "PASS" else "❌"
    print(f"\n{icon}  {result['domain']}  [{result['verdict']}]  "
          f"({result['passing']}/{result['total']} checks passed)")

    checks = result["checks"]

    jl = checks["json_ld"]
    status = "valid" if jl["valid"] else ("present, invalid" if jl["found"] else "missing")
    types_str = f" ({', '.join(jl['types'][:3])})" if jl["types"] else ""
    print(f"   JSON-LD:     {status}{types_str}")

    lt = checks["llms_txt"]
    status = f"found ({lt['size_bytes']} bytes)" if lt["found"] else "missing"
    print(f"   llms.txt:    {status}")

    rt = checks["robots_txt"]
    if rt["found"]:
        bot_info = f", blocks {len(rt['ai_bot_rules'])} AI bots" if rt["blocks_ai_bots"] else ""
        access = "open" if rt["allows_generic_bots"] else "blocks all bots"
        print(f"   robots.txt:  {access}{bot_info}")
    else:
        print(f"   robots.txt:  missing")

    hd = checks["headers"]
    if hd["status_code"]:
        sec = "yes" if hd["has_security_headers"] else "incomplete"
        print(f"   Headers:     HTTP {hd['status_code']}, security headers: {sec}")
    else:
        print(f"   Headers:     unreachable")

    sl = checks["ssl"]
    print(f"   SSL/TLS:     {'valid' if sl['valid'] else sl.get('error', 'failed')}")


def write_csv(results: list, filepath: str) -> None:
    """Export results to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "domain", "verdict", "passing", "total",
            "json_ld_found", "json_ld_valid", "json_ld_types",
            "llms_txt_found", "llms_txt_size",
            "robots_found", "allows_bots", "blocks_ai_bots", "ai_bot_rules",
            "http_status", "security_headers", "content_type_valid",
            "ssl_valid",
        ])
        for r in results:
            c = r["checks"]
            writer.writerow([
                r["domain"], r["verdict"], r["passing"], r["total"],
                c["json_ld"]["found"], c["json_ld"]["valid"],
                "|".join(c["json_ld"]["types"][:5]),
                c["llms_txt"]["found"], c["llms_txt"]["size_bytes"],
                c["robots_txt"]["found"], c["robots_txt"]["allows_generic_bots"],
                c["robots_txt"]["blocks_ai_bots"],
                "|".join(c["robots_txt"]["ai_bot_rules"]),
                c["headers"]["status_code"],
                c["headers"]["has_security_headers"],
                c["headers"]["content_type_valid"],
                c["ssl"]["valid"],
            ])
    print(f"\nCSV written to {filepath}")


def write_json(results: list, filepath: str) -> None:
    """Export results to JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON written to {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Check domains for machine-readable infrastructure signals.",
        epilog="Example: python infra-check.py example.com --csv results.csv",
    )
    parser.add_argument(
        "domains", nargs="*", help="One or more domains to check (e.g. example.com)"
    )
    parser.add_argument(
        "--file", "-f", help="Path to a text file with one domain per line"
    )
    parser.add_argument(
        "--csv", dest="csv_out", help="Write results to a CSV file"
    )
    parser.add_argument(
        "--json-out", dest="json_out", help="Write results to a JSON file"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Only print verdict lines"
    )

    args = parser.parse_args()

    domains = list(args.domains) if args.domains else []

    if args.file:
        try:
            with open(args.file, "r") as f:
                for line in f:
                    d = line.strip()
                    if d and not d.startswith("#"):
                        domains.append(d)
        except FileNotFoundError:
            print(f"File not found: {args.file}")
            sys.exit(1)

    if not domains:
        parser.print_help()
        sys.exit(1)

    # deduplicate, preserve order
    seen = set()
    unique = []
    for d in domains:
        d = d.lower().strip().rstrip("/")
        d = re.sub(r"^https?://", "", d)
        if d not in seen:
            seen.add(d)
            unique.append(d)

    print(f"Checking {len(unique)} domain(s)...\n")

    results = []
    for i, domain in enumerate(unique):
        result = evaluate_domain(domain)
        results.append(result)

        if not args.quiet:
            print_result(result)
        else:
            icon = "✅" if result["verdict"] == "PASS" else "❌"
            print(f"{icon}  {domain}  [{result['verdict']}]")

        if i < len(unique) - 1:
            time.sleep(1)  # polite crawl delay

    # summary
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    failed = len(results) - passed
    print(f"\n{'='*50}")
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if args.csv_out:
        write_csv(results, args.csv_out)

    if args.json_out:
        write_json(results, args.json_out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""External link check for the Markdown documents.

Extracts every http(s) URL from the Markdown files (archive excluded), requests each one
once (HEAD, then GET when HEAD is refused) and reports:

  OK      2xx or 3xx
  LOGIN   401 or 403, or a redirect to a login page: the source exists but needs a WALLIX
          login; listed in KNOWN_LOGIN so it is a warning, not an error
  BLOCKED 403 or 429 from a host that refuses scripted clients but serves browsers
  DOWN    a host the documents already record as unreachable (KNOWN_DOWN)
  ERROR   404, 410, 5xx, DNS failure or timeout after retries

URLs inside fenced code blocks and code spans are not checked, nor are placeholder hosts
(acme, mydomain, .example, .local and similar).

Exit code 1 when any ERROR remains. Run: python3 tools/check_links.py [--verbose]
"""
import re
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL_RE = re.compile(r"https?://[^\s<>()\[\]\"'`|]+")
TRAILING = ".,;:!?*"
TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) docs-link-check/1.0", "Accept": "*/*"}
# Hosts that answer 401/403 or redirect to SSO for anonymous readers.
KNOWN_LOGIN = ("doc.wallix.com", "support.wallix.com")
# Hosts that block scripted clients with 403 or 429 while serving browsers.
KNOWN_BOT_BLOCK = ("nvd.nist.gov", "attack.mitre.org", "www.wallix.com", "www.iso.org", "apps.apple.com")
# Hosts the documents already describe as unreachable (gaps register B4).
KNOWN_DOWN = ("scim.wallix.com",)
# Placeholder hosts used in examples and quoted vendor text; never fetched.
PLACEHOLDER = re.compile(
    r"acme|mydomain|myapp|example|proxy|wam\.com|_ip|_port|^admin-?$|^admin\.trustelem\.com$|^[^.]+$",
    re.IGNORECASE,
)
CODE_SPAN = re.compile(r"`[^`]*`")
RETRIES = 2


def md_files():
    return [
        p for p in ROOT.rglob("*.md")
        if not {".scratch", ".git", "node_modules", "archive"} & set(p.parts)
    ]


def urls_by_file():
    """URLs outside fenced blocks and code spans, minus placeholder hosts."""
    found = {}
    for path in md_files():
        in_fence = False
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for url in URL_RE.findall(CODE_SPAN.sub("", line)):
                url = url.rstrip(TRAILING)
                host = url.split("/")[2].split("@")[-1].split(":")[0] if url.count("/") >= 2 else ""
                if PLACEHOLDER.search(host) or host.endswith((".local", ".example", ".test", ".invalid")):
                    continue
                found.setdefault(url, []).append(f"{path.relative_to(ROOT)}:{line_no}")
    return found


def fetch_once(url):
    ctx = ssl.create_default_context()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
                return resp.status, resp.geturl()
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 404, 405, 501):
                continue
            return e.code, url
        except Exception as e:  # DNS, timeout, TLS
            if method == "HEAD":
                continue
            return None, f"{type(e).__name__}: {e}"
    return None, "no response"


def fetch(url):
    """Retry timeouts: rfc-editor.org and similar hosts throttle bursts."""
    import time
    status, final = None, "no response"
    for attempt in range(RETRIES + 1):
        status, final = fetch_once(url)
        if status is not None or "resolution" in final or "not known" in final:
            break
        time.sleep(5 * (attempt + 1))
    return status, final


def classify(url, status, final):
    host = url.split("/")[2]
    if host.endswith(KNOWN_DOWN):
        return "DOWN" if status is None or status >= 400 else "OK"
    if status is None:
        return "ERROR"
    if 200 <= status < 400:
        if "login" in final.lower() or "sso" in final.lower():
            return "LOGIN"
        return "OK"
    if status in (401, 403, 429) and (host.endswith(KNOWN_LOGIN) or host.endswith(KNOWN_BOT_BLOCK)):
        return "LOGIN" if host.endswith(KNOWN_LOGIN) else "BLOCKED"
    return "ERROR"


def main():
    verbose = "--verbose" in sys.argv
    found = urls_by_file()
    urls = sorted(found)
    by_host = {}
    for url in urls:
        by_host.setdefault(url.split("/")[2], []).append(url)

    def fetch_host(host_urls):
        return [(u, fetch(u)) for u in host_urls]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = dict(pair for batch in pool.map(fetch_host, by_host.values()) for pair in batch)
    counts = {}
    errors = 0
    for url in urls:
        status, final = results[url]
        kind = classify(url, status, final)
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "ERROR":
            errors += 1
        if kind != "OK" or verbose:
            where = ", ".join(found[url][:3])
            print(f"{kind:7} {status or '-':>4} {url}  [{where}]" + (f" -> {final}" if kind == "ERROR" and status is None else ""))
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    print(f"{len(urls)} URLs checked: {summary}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

"""Shared logic for the 0N_* checks: GET one path on a host and print a JSON row."""
import ipaddress
import json
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

TIMEOUT = 10
DOWN_STATUSES = {400, 502, 503, 504}


def probe_urls(target, path):
    """URLs to try, in order. A bare host/IP tries https, then http."""
    if "://" in target:
        parts = urlsplit(target)
        if not parts.netloc:
            raise ValueError(f"no host in {target!r}")
        return [f"{parts.scheme}://{parts.netloc}{path}"]
    host = target.split("/")[0]
    try:
        if ipaddress.ip_address(host).version == 6:
            host = f"[{host}]"
    except ValueError:
        pass
    return [f"https://{host}{path}", f"http://{host}{path}"]


def fetch_status(url):
    req = urllib.request.Request(url, headers={"User-Agent": "site-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def classify(status):
    if status == 200:
        return "TRUE"
    if status in (404, 410):
        return "FALSE"
    if status in DOWN_STATUSES:
        return "DOWN"
    return "ERROR"


def check(target, path):
    status, result = 0, "ERROR"
    for url in probe_urls(target, path):
        try:
            status = fetch_status(url)
        except (urllib.error.URLError, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            status, result = 0, "ERROR" if isinstance(reason, ssl.SSLError) else "DOWN"
            continue
        return status, classify(status)
    return status, result


def main(name, path):
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <ip-or-url>")
    target = sys.argv[1]
    try:
        status, result = check(target, path)
    except Exception:
        status, result = 0, "ERROR"
    print(json.dumps({"check": name, "target": target, "status": status, "result": result}))

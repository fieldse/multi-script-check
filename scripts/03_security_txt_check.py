#!/usr/bin/env python3
"""Check whether a host serves /.well-known/security.txt and print one JSON row.

usage: 03_security_txt_check.py <ip-or-url>
"""
import ipaddress
import json
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

CHECK = "03-security-txt"
PATH = "/.well-known/security.txt"
TIMEOUT = 10
DOWN_STATUSES = {400, 502, 503, 504}


def probe_urls(target):
    """URLs to try, in order. A bare host/IP tries https, then http."""
    if "://" in target:
        parts = urlsplit(target)
        if not parts.netloc:
            raise ValueError(f"no host in {target!r}")
        return [f"{parts.scheme}://{parts.netloc}{PATH}"]
    host = target.split("/")[0]
    try:
        if ipaddress.ip_address(host).version == 6:
            host = f"[{host}]"
    except ValueError:
        pass
    return [f"https://{host}{PATH}", f"http://{host}{PATH}"]


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


def check(target):
    status, result = 0, "ERROR"
    for url in probe_urls(target):
        try:
            status = fetch_status(url)
        except (urllib.error.URLError, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            status, result = 0, "ERROR" if isinstance(reason, ssl.SSLError) else "DOWN"
            continue
        return status, classify(status)
    return status, result


def main():
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <ip-or-url>")
    target = sys.argv[1]
    try:
        status, result = check(target)
    except Exception:
        status, result = 0, "ERROR"
    print(json.dumps({"check": CHECK, "target": target, "status": status, "result": result}))


if __name__ == "__main__":
    main()

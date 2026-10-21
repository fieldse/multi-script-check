#!/usr/bin/env python3
"""Check whether a host answers HTTP at its root (/) and print one JSON row.

usage: 02_ping_check.py <ip-or-url>
"""
from probe import main

if __name__ == "__main__":
    main("02-ping", "/")

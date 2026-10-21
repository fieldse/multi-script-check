#!/usr/bin/env python3
"""Check whether a host serves /.well-known/security.txt and print one JSON row.

usage: 03_security_txt_check.py <ip-or-url>
"""
from probe import main

if __name__ == "__main__":
    main("03-security-txt", "/.well-known/security.txt")

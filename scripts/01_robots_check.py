#!/usr/bin/env python3
"""Check whether a host serves /robots.txt and print one JSON row.

usage: 01_robots_check.py <ip-or-url>
"""
from probe import main

if __name__ == "__main__":
    main("01-robots", "/robots.txt")

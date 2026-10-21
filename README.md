# web-prober

Runs basic, read-only checks against web hosts and prints the results as JSON.

Each check sends one GET request to a fixed path. Nothing is crawled, submitted or modified.

## Quick start

1. `./setup.sh`
   - Creates `.venv` with `uv` if it doesn't exist.
   - Installs `requirements.txt` if it lists any dependencies.
   - Safe to re-run.
2. `source ./activate.sh`
   - Activates `.venv` in the current shell.
3. `python run_checks.py -f urls.txt`

- **Requirements:** Python 3 and `uv`.
- **Dependencies:** none today. Standard library only, so there is no `requirements.txt`.

## Checks

| name              | script                             | requests                    | `TRUE` means                      |
|-------------------|------------------------------------|-----------------------------|-----------------------------------|
| `01-robots`       | `scripts/01_robots_check.py`       | `/robots.txt`               | the host serves a robots.txt      |
| `02-ping`         | `scripts/02_ping_check.py`         | `/`                         | the host answers HTTP at its root |
| `03-security-txt` | `scripts/03_security_txt_check.py` | `/.well-known/security.txt` | the host publishes a security.txt |

- **02-ping:** an HTTP GET, not an ICMP ping.
- **Shared logic:** all three import `scripts/probe.py`. Each script only sets its name and path.

## Batch run

`run_checks.py` runs the three scripts in the table above against every target in a file.

```
python run_checks.py -f urls.txt
python run_checks.py -f urls.txt -o
python run_checks.py -f urls.txt -o results.json
python run_checks.py -f urls.txt | jq '.[] | select(.result == "TRUE")'
```

| flag              | effect                                                                      |
|-------------------|-----------------------------------------------------------------------------|
| `-f, --file FILE` | required. Targets, one per line. Blank lines and `#` lines are skipped.     |
| `-o, --output`    | also saves the JSON to `<input-stem>.results.json` in the current directory |
| `-o PATH`         | also saves the JSON to `PATH`                                               |

- **What runs:** `01_robots_check.py`, `02_ping_check.py` and `03_security_txt_check.py`, once per target.
- **How:** each script is a separate subprocess. The runner collects the row each one prints.
- **Output:** one JSON array on stdout, with one row per check per target.
- **Order:** input-file order, then `01`, `02`, `03` for each target.
- **Empty file:** prints `[]`.
- **stdout:** only the JSON array, so it pipes to `jq`. Progress and warnings go to stderr.
- **Saved file:** written after all targets finish. The path is reported on stderr.
- **Concurrency:** up to 8 checks run at once.
- **Failures:** a check that exits non-zero, runs past 30 seconds or prints invalid JSON becomes an `ERROR` row. The rest of the batch carries on.
- **Unreadable target file:** prints an error to stderr and exits 1.

## Single check

```
python scripts/01_robots_check.py <ip-or-url>
python scripts/02_ping_check.py <ip-or-url>
python scripts/03_security_txt_check.py <ip-or-url>
```

- **One argument:** an IP, a hostname, or a URL. No flags.
- **Bare host or IP:** tries `https://` first, then `http://` if the connection fails.
- **URL with scheme:** uses that scheme and checks the host root only.
- **Bad usage:** no argument, or more than one, prints a usage line to stderr and exits 1.

## Output

```json
{"check": "01-robots", "target": "https://www.python.org", "status": 200, "result": "TRUE"}
```

- **check:** the check name from the table above.
- **target:** the argument as given.
- **status:** the HTTP status code, or `0` when there was no HTTP response.
- **result:** one of the values below.

| result  | when                                                                  |
|---------|-----------------------------------------------------------------------|
| `TRUE`  | the path returns 200                                                  |
| `FALSE` | the path returns 404 or 410                                           |
| `DOWN`  | connection fails, times out, or status is 400, 502, 503 or 504        |
| `ERROR` | anything else: other statuses (401, 403, 500), TLS errors, bad target |

## Notes

- **Timeout:** 10 seconds per request.
- **Redirects:** followed.
- **Soft 404s:** a site that returns 200 with an HTML page for a missing file reports `TRUE`.

## Files

- **`setup.sh`:** creates `.venv` and installs dependencies.
- **`activate.sh`:** activates `.venv`. Must be sourced.
- **`run_checks.py`:** batch runner.
- **`scripts/`:** the three checks and `probe.py`.
- **`urls.txt`:** sample targets.

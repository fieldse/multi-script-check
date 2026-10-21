# web-prober

Runs basic, read-only checks against web hosts and prints the results as JSON.

Each check sends one GET request to a fixed path. Nothing is crawled, submitted or modified.

## TLDR

```
./setup.sh
source ./activate.sh
python3 run_checks.py -f urls.txt -o
```

- **Result:** a JSON array with three rows (robots, ping, security.txt) for each site in `urls.txt`.
- **Saved to:** `urls.results.json`, as well as printed. Use `-o PATH` to pick the file name.

## Quick start

1. `./setup.sh`
   - Creates `.venv` with `uv` if it doesn't exist.
   - Installs `requirements.txt` if it lists any dependencies.
   - Safe to re-run.
2. `source ./activate.sh`
   - Activates `.venv` in the current shell.
3. `python3 run_checks.py -f urls.txt`

- **Requirements:** Python 3 and `uv`.
- **Dependencies:** none today. Standard library only, so there is no `requirements.txt`.

## Checks

| name              | script                             | requests                    | `TRUE` means                      |
|-------------------|------------------------------------|-----------------------------|-----------------------------------|
| `01-robots`       | `scripts/01_robots_check.py`       | `/robots.txt`               | the host serves a robots.txt      |
| `02-ping`         | `scripts/02_ping_check.py`         | `/`                         | the host answers HTTP at its root |
| `03-security-txt` | `scripts/03_security_txt_check.py` | `/.well-known/security.txt` | the host publishes a security.txt |

- **02-ping:** an HTTP GET, not an ICMP ping.
- **Standalone:** each script holds its own request and classification logic. They share no code and import only the standard library.
- **What differs:** only the `CHECK` name and the `PATH` constants near the top of each file.

## Batch run

`run_checks.py` runs the three scripts in the table above against every target in a file.

```
python3 run_checks.py -f urls.txt
python3 run_checks.py -f urls.txt -o
python3 run_checks.py -f urls.txt -o results.json
python3 run_checks.py -f urls.txt | jq '.[] | select(.result == "TRUE")'
```

| flag              | effect                                                                      |
|-------------------|-----------------------------------------------------------------------------|
| `-f, --file FILE` | required. Targets, one per line. Blank lines and `#` lines are skipped.     |
| `-o, --output`    | also saves the JSON to `<input-stem>.results.json` in the current directory |
| `-o PATH`         | also saves the JSON to `PATH`                                               |

- **What runs:** the files listed in `CHECK_SCRIPTS` at the top of `run_checks.py`, once per target.
- **Change the list:** see [Change the scripts](#change-the-scripts).
- **How:** each script is a separate subprocess. The runner collects the row each one prints.
- **Output:** one JSON array on stdout, with one row per check per target.
- **Order:** input-file order, then `01`, `02`, `03` for each target.
- **Empty file:** prints `[]`.
- **stdout:** only the JSON array, so it pipes to `jq`. Progress and warnings go to stderr.
- **Saved file:** written after all targets finish. The path is reported on stderr.
- **Concurrency:** up to 8 checks run at once.
- **Failures:** a check that exits non-zero, runs past 30 seconds or prints invalid JSON becomes an `ERROR` row. The rest of the batch carries on.
- **Unreadable target file:** prints an error to stderr and exits 1.

## Change the scripts

`run_checks.py` runs the files named in `CHECK_SCRIPTS`, an array at the top of the file:

```python
CHECK_SCRIPTS = [
    "01_robots_check.py",
    "02_ping_check.py",
    "03_security_txt_check.py",
]
```

### Swap or remove a script

1. Open `run_checks.py`.
2. Edit the names in `CHECK_SCRIPTS`.
   - Delete a name to stop running that script.
   - Replace a name to run a different script in its place.
3. Run `python3 run_checks.py -f urls.txt`.

- **Location:** every name is a file in `scripts/`.
- **Order:** rows come out in list order for each target.
- **Count:** any number of scripts works. It is not fixed at three.

### Add a new script

1. Copy an existing script: `cp scripts/01_robots_check.py scripts/04_sitemap_check.py`
2. Edit three things in the new file:
   - The docstring: the description and the `usage:` line.
   - `CHECK = "04-sitemap"`
   - `PATH = "/sitemap.xml"`
3. Test it alone: `python3 scripts/04_sitemap_check.py owasp.org`
4. Add `"04_sitemap_check.py"` to `CHECK_SCRIPTS`.
5. Run the batch.

- **Standalone:** each script holds all its own logic and imports only the standard library.
- **Name match:** `CHECK` should equal the name derived from the file name.
  - The runner drops the `_check` ending and swaps `_` for `-`: `04_sitemap_check.py` becomes `04-sitemap`.
  - The runner uses the derived name when it has to write an `ERROR` row for a script that crashed.

### Script contract

- **Language:** Python. The runner starts each script with the same interpreter it runs under.
- **Input:** one argument, the target (IP, host or URL).
- **Output:** one JSON object on stdout, with the keys `check`, `target`, `status` and `result`.
- **Anything else is free:** a script can make its own kind of request or use no HTTP at all, as long as it follows this contract.
- **Failure:** a non-zero exit, a run past 30 seconds or output that isn't JSON becomes an `ERROR` row.

## Single check

```
python3 scripts/01_robots_check.py <ip-or-url>
python3 scripts/02_ping_check.py <ip-or-url>
python3 scripts/03_security_txt_check.py <ip-or-url>
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
- **`scripts/`:** the three standalone checks.
- **`urls.txt`:** sample targets.

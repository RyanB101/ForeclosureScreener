"""Minimal client for Philadelphia's public Carto SQL API (phl.carto.com).

Stdlib only so it runs in a bare cloud container.
"""
import csv
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request

CARTO_URL = "https://phl.carto.com/api/v2/sql"


class CartoError(RuntimeError):
    pass


def query(sql, fmt="json", timeout=120, retries=3):
    """Run a SQL query. Returns a list of dicts. Retries dropped connections."""
    for attempt in range(retries):
        try:
            return _query(sql, fmt, timeout)
        except CartoError as e:
            if attempt == retries - 1 or "HTTP" in str(e):
                raise
            time.sleep(2 ** (attempt + 1))


def _query(sql, fmt, timeout):
    data = urllib.parse.urlencode({"q": sql, "format": fmt}).encode()
    req = urllib.request.Request(CARTO_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        raise CartoError(f"Carto HTTP {e.code}: {e.read().decode()[:500]}") from e
    except urllib.error.URLError as e:
        raise CartoError(
            f"Cannot reach phl.carto.com ({e.reason}). If this is a cloud "
            "environment, add phl.carto.com to its allowed domains."
        ) from e
    if fmt == "csv":
        return list(csv.DictReader(io.StringIO(body)))
    return json.loads(body)["rows"]


def check():
    rows = query("SELECT count(*) AS n FROM rtt_summary")
    return rows[0]["n"]


def sql_list(values):
    """Quote a list of strings for an IN (...) clause."""
    return ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)

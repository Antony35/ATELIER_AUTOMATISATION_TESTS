"""
client.py — Wrapper HTTP avec timeout, retry et mesure de latence.
"""
import time
import requests


TIMEOUT_S = 5       # secondes avant abandon
MAX_RETRIES = 1     # 1 seul retry (comme demandé dans le barème)
RETRY_WAIT_S = 2    # attente avant retry


def http_get(url: str, params: dict = None) -> dict:
    """
    Effectue un GET HTTP avec timeout et 1 retry.
    Retourne un dict :
      {
        "status_code": int,
        "json": dict | None,
        "latency_ms": float,
        "error": str | None,   # message si exception
        "retried": bool
      }
    """
    result = {
        "status_code": None,
        "json": None,
        "latency_ms": 0.0,
        "error": None,
        "retried": False,
    }

    for attempt in range(MAX_RETRIES + 1):
        start = time.perf_counter()
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT_S)
            elapsed = (time.perf_counter() - start) * 1000  # ms

            result["status_code"] = resp.status_code
            result["latency_ms"] = round(elapsed, 1)
            result["error"] = None

            # Gestion 429 — rate limit : on attend et on retry
            if resp.status_code == 429:
                if attempt < MAX_RETRIES:
                    result["retried"] = True
                    time.sleep(RETRY_WAIT_S)
                    continue
                result["error"] = "Rate limited (429)"
                return result

            # Gestion 5xx : retry automatique
            if resp.status_code >= 500:
                if attempt < MAX_RETRIES:
                    result["retried"] = True
                    time.sleep(RETRY_WAIT_S)
                    continue
                result["error"] = f"Server error ({resp.status_code})"
                return result

            # Lecture JSON
            try:
                result["json"] = resp.json()
            except Exception:
                result["json"] = None
                result["error"] = "Invalid JSON response"

            return result

        except requests.exceptions.Timeout:
            elapsed = (time.perf_counter() - start) * 1000
            result["latency_ms"] = round(elapsed, 1)
            if attempt < MAX_RETRIES:
                result["retried"] = True
                time.sleep(RETRY_WAIT_S)
                continue
            result["error"] = "Timeout"
            return result

        except requests.exceptions.ConnectionError as e:
            elapsed = (time.perf_counter() - start) * 1000
            result["latency_ms"] = round(elapsed, 1)
            if attempt < MAX_RETRIES:
                result["retried"] = True
                time.sleep(RETRY_WAIT_S)
                continue
            result["error"] = f"ConnectionError: {e}"
            return result

    return result

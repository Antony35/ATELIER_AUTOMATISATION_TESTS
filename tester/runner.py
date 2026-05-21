"""
runner.py — Exécute tous les tests et calcule les métriques QoS.
"""
import datetime
from .tests import ALL_TESTS


def run_all() -> dict:
    """
    Exécute chaque test et retourne un rapport complet :
    {
      "api": "Weatherstack",
      "timestamp": "2026-...",
      "summary": { "total", "passed", "failed", "errors",
                   "error_rate", "availability",
                   "latency_ms_avg", "latency_ms_p95" },
      "tests": [ {"name", "status", "latency_ms", "details"}, ... ]
    }
    """
    results = []
    for test_fn in ALL_TESTS:
        try:
            res = test_fn()
        except Exception as e:
            res = {
                "name": getattr(test_fn, "__name__", "unknown"),
                "status": "ERROR",
                "latency_ms": 0,
                "details": str(e),
            }
        results.append(res)

    # ── Métriques QoS ──────────────────────────────────────
    total   = len(results)
    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    errors  = sum(1 for r in results if r["status"] == "ERROR")

    latencies = [r["latency_ms"] for r in results if r["latency_ms"] > 0]
    if latencies:
        avg_lat = round(sum(latencies) / len(latencies), 1)
        sorted_lat = sorted(latencies)
        p95_idx = max(0, int(len(sorted_lat) * 0.95) - 1)
        p95_lat = round(sorted_lat[p95_idx], 1)
    else:
        avg_lat = 0
        p95_lat = 0

    error_rate   = round((failed + errors) / total, 3) if total else 0
    availability = round(passed / total, 3) if total else 0

    return {
        "api": "Weatherstack",
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "error_rate": error_rate,
            "availability": availability,
            "latency_ms_avg": avg_lat,
            "latency_ms_p95": p95_lat,
        },
        "tests": results,
    }

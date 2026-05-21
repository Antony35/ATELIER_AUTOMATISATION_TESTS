"""
tests.py — Tests "as code" pour l'API Weatherstack.
Chaque fonction retourne un dict :
  { "name": str, "status": "PASS"|"FAIL"|"ERROR", "latency_ms": float, "details": str }
"""
import os
from .client import http_get

BASE_URL = "http://api.weatherstack.com"

def _get_key():
    key = os.environ.get("WEATHERSTACK_API_KEY", "")
    if not key:
        raise RuntimeError("Variable d'environnement WEATHERSTACK_API_KEY manquante.")
    return key


def _make_result(name, status, latency_ms, details=""):
    return {
        "name": name,
        "status": status,
        "latency_ms": latency_ms,
        "details": details,
    }


# ──────────────────────────────────────────────
# TEST 1 — HTTP 200 pour une ville valide
# ──────────────────────────────────────────────
def test_http_200_valid_city():
    name = "T01 — HTTP 200 ville valide (Paris)"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "Paris"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    if r["status_code"] == 200:
        return _make_result(name, "PASS", r["latency_ms"], "HTTP 200 reçu")
    return _make_result(name, "FAIL", r["latency_ms"], f"HTTP {r['status_code']} attendu 200")


# ──────────────────────────────────────────────
# TEST 2 — Content-Type JSON
# ──────────────────────────────────────────────
def test_content_type_json():
    name = "T02 — Content-Type JSON"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "Paris"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    if r["json"] is not None:
        return _make_result(name, "PASS", r["latency_ms"], "Réponse parsée en JSON")
    return _make_result(name, "FAIL", r["latency_ms"], "Réponse non JSON")


# ──────────────────────────────────────────────
# TEST 3 — Champs obligatoires présents
# ──────────────────────────────────────────────
def test_required_fields():
    name = "T03 — Champs obligatoires (request, location, current)"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "London"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    data = r["json"] or {}
    missing = [f for f in ("request", "location", "current") if f not in data]
    if not missing:
        return _make_result(name, "PASS", r["latency_ms"], "Tous les champs top-level présents")
    return _make_result(name, "FAIL", r["latency_ms"], f"Champs manquants : {missing}")


# ──────────────────────────────────────────────
# TEST 4 — Types des champs weather
# ──────────────────────────────────────────────
def test_field_types():
    name = "T04 — Types champs current (temperature=int, humidity=int, descriptions=list)"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "Paris"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    data = r["json"] or {}
    current = data.get("current", {})
    errors = []
    if not isinstance(current.get("temperature"), (int, float)):
        errors.append("temperature pas numérique")
    if not isinstance(current.get("humidity"), (int, float)):
        errors.append("humidity pas numérique")
    if not isinstance(current.get("weather_descriptions"), list):
        errors.append("weather_descriptions pas une liste")
    elif len(current.get("weather_descriptions", [])) == 0:
        errors.append("weather_descriptions liste vide")
    if errors:
        return _make_result(name, "FAIL", r["latency_ms"], " | ".join(errors))
    return _make_result(name, "PASS", r["latency_ms"],
        f"temp={current.get('temperature')}°C, hum={current.get('humidity')}%")


# ──────────────────────────────────────────────
# TEST 5 — Cas invalide → erreur JSON structurée
# ──────────────────────────────────────────────
def test_invalid_city_returns_error():
    name = "T05 — Ville invalide → error JSON (success:false)"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "XYZVILLE999INVALID"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    data = r["json"] or {}
    # Weatherstack retourne HTTP 200 mais avec success:false
    if r["status_code"] == 200 and data.get("success") is False:
        err = data.get("error", {})
        return _make_result(name, "PASS", r["latency_ms"],
            f"Erreur structurée reçue : code={err.get('code')}")
    return _make_result(name, "FAIL", r["latency_ms"],
        f"Attendu success:false, reçu: {data.get('success')}")


# ──────────────────────────────────────────────
# TEST 6 — Clé API invalide → erreur 101
# ──────────────────────────────────────────────
def test_invalid_api_key():
    name = "T06 — Clé invalide → erreur code 101"
    r = http_get(f"{BASE_URL}/current", params={"access_key": "FAUSSEKEY000", "query": "Paris"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    data = r["json"] or {}
    err_code = data.get("error", {}).get("code")
    if data.get("success") is False and err_code == 101:
        return _make_result(name, "PASS", r["latency_ms"], "Code 101 reçu (invalid_access_key)")
    return _make_result(name, "FAIL", r["latency_ms"],
        f"Attendu code=101, reçu success={data.get('success')} code={err_code}")


# ──────────────────────────────────────────────
# TEST 7 — Latence < 3000 ms
# ──────────────────────────────────────────────
def test_latency_under_3s():
    name = "T07 — Latence < 3000 ms"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "Berlin"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    if r["latency_ms"] < 3000:
        return _make_result(name, "PASS", r["latency_ms"], f"{r['latency_ms']} ms")
    return _make_result(name, "FAIL", r["latency_ms"], f"{r['latency_ms']} ms > seuil 3000 ms")


# ──────────────────────────────────────────────
# TEST 8 — Cohérence location.name et query
# ──────────────────────────────────────────────
def test_location_name_match():
    name = "T08 — location.name cohérent avec la requête (Tokyo)"
    r = http_get(f"{BASE_URL}/current", params={"access_key": _get_key(), "query": "Tokyo"})
    if r["error"]:
        return _make_result(name, "ERROR", r["latency_ms"], r["error"])
    data = r["json"] or {}
    loc_name = data.get("location", {}).get("name", "")
    if "Tokyo" in loc_name:
        return _make_result(name, "PASS", r["latency_ms"], f"location.name = '{loc_name}'")
    return _make_result(name, "FAIL", r["latency_ms"],
        f"'Tokyo' absent de location.name='{loc_name}'")


# ──────────────────────────────────────────────
# Liste de tous les tests à exécuter
# ──────────────────────────────────────────────
ALL_TESTS = [
    test_http_200_valid_city,
    test_content_type_json,
    test_required_fields,
    test_field_types,
    test_invalid_city_returns_error,
    test_invalid_api_key,
    test_latency_under_3s,
    test_location_name_match,
]

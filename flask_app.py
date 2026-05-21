from flask import Flask, render_template, jsonify, request
import json
import os

from tester.runner import run_all
from storage import save_run, list_runs, get_run_by_id

app = Flask(__name__)


# ─────────────────────────────────────────────
# PAGE D'ACCUEIL — Consignes de l'atelier
# ─────────────────────────────────────────────
@app.get("/")
def consignes():
    return render_template("consignes.html")


# ─────────────────────────────────────────────
# /run — Lance un run de tests
# ─────────────────────────────────────────────
@app.route("/run", methods=["GET", "POST"])
def run():
    """Exécute tous les tests, sauvegarde et redirige vers le dashboard."""
    if not os.environ.get("WEATHERSTACK_API_KEY"):
        return jsonify({
            "error": "Variable WEATHERSTACK_API_KEY non définie sur le serveur."
        }), 500

    report = run_all()
    save_run(report)
    return jsonify(report)


# ─────────────────────────────────────────────
# /dashboard — Tableau de bord
# ─────────────────────────────────────────────
@app.get("/dashboard")
def dashboard():
    runs = list_runs(limit=20)
    last = None
    if runs:
        last_details = get_run_by_id(runs[0]["id"])
        last = last_details
    return render_template("dashboard.html", runs=runs, last=last)


# ─────────────────────────────────────────────
# /dashboard/run/<id> — Détail d'un run
# ─────────────────────────────────────────────
@app.get("/dashboard/run/<int:run_id>")
def run_detail(run_id):
    report = get_run_by_id(run_id)
    if not report:
        return "Run introuvable", 404
    return jsonify(report)


# ─────────────────────────────────────────────
# /export — Télécharger l'historique JSON (bonus)
# ─────────────────────────────────────────────
@app.get("/export")
def export_json():
    runs = list_runs(limit=100)
    return jsonify(runs), 200, {
        "Content-Disposition": "attachment; filename=runs_history.json"
    }


# ─────────────────────────────────────────────
# /health — État de santé (bonus)
# ─────────────────────────────────────────────
@app.get("/health")
def health():
    runs = list_runs(limit=1)
    has_key = bool(os.environ.get("WEATHERSTACK_API_KEY"))
    last_run = runs[0] if runs else None
    status = "ok" if has_key else "missing_api_key"
    return jsonify({
        "status": status,
        "api_key_configured": has_key,
        "last_run": last_run["timestamp"] if last_run else None,
        "last_availability": last_run["availability"] if last_run else None,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

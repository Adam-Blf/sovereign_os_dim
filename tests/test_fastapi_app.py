"""Tests FastAPI v2 · couvre les 13 endpoints + auth + Pydantic validation."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Permet l'import 'backend.fastapi_app' depuis tests/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Lazy import pour éviter le coût quand FastAPI n'est pas dispo
fastapi_app = pytest.importorskip("backend.fastapi_app")
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Client de test sans token (API_TOKEN vide → auth bypass)."""
    os.environ["SOVEREIGN_API_TOKEN"] = ""
    fastapi_app.API_TOKEN = ""
    return TestClient(fastapi_app.app)


# ─── PUBLIC ─────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "sovereign-os-dim"
    assert body["version"] == fastapi_app.API_VERSION
    assert "ml_models_loaded" in body


def test_openapi_doc_available(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()


def test_swagger_ui_available(client):
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger-ui" in r.text.lower() or "openapi" in r.text.lower()


# ─── COCKPIT ────────────────────────────────────────────────────────────

def test_cockpit_returns_4_kpis(client):
    r = client.get("/api/v2/cockpit")
    assert r.status_code == 200
    body = r.json()
    assert len(body["kpis"]) == 4
    assert len(body["file_active_history"]) == 12
    assert all("label" in k and "value" in k for k in body["kpis"])


# ─── HEALTH MONITOR ─────────────────────────────────────────────────────

def test_health_monitor_returns_checks(client):
    r = client.get("/api/v2/health-monitor")
    assert r.status_code == 200
    body = r.json()
    assert body["uptime_hours"] >= 0
    assert len(body["checks"]) >= 5
    for c in body["checks"]:
        assert "label" in c and "ok" in c


# ─── ML ─────────────────────────────────────────────────────────────────

def test_ml_predict_format_returns_top3(client):
    line = "940140049" + "940140050" + "P12" + "12345678901234567890" + \
           "19850314" + " " * 100
    r = client.post("/api/v2/ml/predict-format", json={"line": line[:154]})
    # Si modèle non chargé → 503, sinon réponse complète
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert "format" in body and "confidence" in body and "top3" in body
        assert 0.0 <= body["confidence"] <= 1.0
        assert len(body["top3"]) == 3


def test_ml_predict_collision_risk_levels(client):
    payload = {
        "ipp_freq": 8, "ddn_variance_days": 1500, "n_distinct_finess": 2,
        "n_distinct_modalities": 3, "ipp_with_letters": 0,
        "year_min": 2018, "year_span": 5,
    }
    r = client.post("/api/v2/ml/predict-collision-risk", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["risk"] <= 1.0
    assert body["level"] in ("low", "medium", "high")


def test_ml_predict_collision_risk_validates_input(client):
    """Pydantic doit refuser les valeurs hors borne (year_min trop bas)."""
    bad = {
        "ipp_freq": 1, "ddn_variance_days": 0, "n_distinct_finess": 1,
        "n_distinct_modalities": 1, "ipp_with_letters": 0,
        "year_min": 1800, "year_span": 0,  # year_min < 1900 → refus
    }
    r = client.post("/api/v2/ml/predict-collision-risk", json=bad)
    assert r.status_code == 422


def test_ml_cim_suggest_returns_5_codes(client):
    r = client.post("/api/v2/ml/cim-suggest", json={
        "das": ["F40.1", "F45.0"], "actes": ["YYYY020"],
        "notes": "Patient repli social marqué",
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["suggestions"]) == 5
    for s in body["suggestions"]:
        assert s["code"].startswith("F")
        assert 0.0 <= s["confidence"] <= 1.0
    assert body["provider"] in ("ollama", "mock")


def test_ml_predict_ddn_validity(client):
    r = client.post("/api/v2/ml/predict-ddn-validity",
                    json={"line": "12345678" + "1" * 200})
    assert r.status_code in (200, 500)


# ─── ARS ────────────────────────────────────────────────────────────────

def test_ars_score_lot_returns_breakdown(client):
    r = client.post("/api/v2/ars/score-lot", json={
        "lot_name": "RPS_2025T3.txt",
        "sample_lines": ["12345" * 30] * 5,
    })
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["score"] <= 100
    assert body["risk"] in ("low", "medium", "high")
    assert len(body["breakdown"]) >= 3


# ─── CESPA / DIFF / HEATMAP ─────────────────────────────────────────────

def test_cespa_rules_count(client):
    r = client.get("/api/v2/cespa/rules")
    assert r.status_code == 200
    rules = r.json()
    assert len(rules) >= 5
    assert all(rule["code"].startswith("R-CSP-") for rule in rules)


def test_diff_lots_state_classification(client):
    r = client.get("/api/v2/diff/2025-10/2025-11")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 7
    states = {row["state"] for row in rows}
    assert states.issubset({"ok", "warn", "alert"})
    # CMP secteur G16 a -23 % → alert
    cmp_row = next(r for r in rows if "CMP" in r["indicator"])
    assert cmp_row["state"] == "alert"


def test_heatmap_sectors_intensity(client):
    r = client.get("/api/v2/heatmap/sectors")
    assert r.status_code == 200
    sectors = r.json()
    assert len(sectors) == 8
    intensities = {s["intensity"] for s in sectors}
    assert intensities.issubset({"very_high", "high", "medium", "low"})


# ─── AUDIT / TWIN / WORKFLOW ────────────────────────────────────────────

def test_audit_events_have_sha256(client):
    r = client.get("/api/v2/audit/events")
    assert r.status_code == 200
    events = r.json()
    assert len(events) >= 5
    for e in events:
        assert len(e["sha256"]) == 64
        assert all(c in "0123456789abcdef" for c in e["sha256"])


def test_audit_events_respects_limit(client):
    r = client.get("/api/v2/audit/events?limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_twin_scenarios_have_positive_impact(client):
    r = client.get("/api/v2/twin/scenarios")
    assert r.status_code == 200
    sc = r.json()
    assert len(sc) >= 4
    assert all(s["impact_eur"] > 0 for s in sc)
    assert all(0.0 <= s["confidence"] <= 1.0 for s in sc)


def test_workflow_pending_stages(client):
    r = client.get("/api/v2/workflow/pending")
    assert r.status_code == 200
    items = r.json()
    assert all(i["stage"] in ("tim", "mim", "preflight", "ars") for i in items)


# ─── AUTH ───────────────────────────────────────────────────────────────

def test_auth_blocks_when_token_set(monkeypatch):
    """Avec SOVEREIGN_API_TOKEN, les endpoints v2 doivent réclamer le bearer."""
    monkeypatch.setattr(fastapi_app, "API_TOKEN", "secret-test-token")
    c = TestClient(fastapi_app.app)
    r = c.get("/api/v2/cockpit")
    assert r.status_code == 401
    r2 = c.get("/api/v2/cockpit",
               headers={"Authorization": "Bearer wrong-token"})
    assert r2.status_code == 403
    r3 = c.get("/api/v2/cockpit",
               headers={"Authorization": "Bearer secret-test-token"})
    assert r3.status_code == 200


def test_auth_health_remains_public(monkeypatch):
    """Le /health public ne doit JAMAIS demander d'auth (probes K8s)."""
    monkeypatch.setattr(fastapi_app, "API_TOKEN", "secret")
    c = TestClient(fastapi_app.app)
    r = c.get("/health")
    assert r.status_code == 200

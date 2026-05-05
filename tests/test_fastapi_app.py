"""Tests FastAPI v2 PROD · zéro données en dur attendues."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

fastapi_app = pytest.importorskip("backend.fastapi_app")
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Test client · audit DB isolée, auth désactivée."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    os.environ["SOVEREIGN_AUDIT_DB"] = tmp.name
    os.environ["SOVEREIGN_API_TOKEN"] = ""
    fastapi_app.API_TOKEN = ""
    from backend import audit
    audit.AUDIT_DB = tmp.name
    yield TestClient(fastapi_app.app)
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


# ─── PUBLIC ─────────────────────────────────────────────────────────────

def test_health_returns_real_state(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "ml_models_loaded" in body
    assert "audit_events" in body
    assert isinstance(body["audit_events"], int)


def test_openapi_doc_available(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    # Endpoints ML, audit, IDV, ARS, cockpit, monitor doivent être présents
    expected = {
        "/health", "/api/v2/cockpit", "/api/v2/health-monitor",
        "/api/v2/ml/predict-format", "/api/v2/ml/predict-collision-risk",
        "/api/v2/ml/predict-ddn-validity", "/api/v2/ml/cim-suggest",
        "/api/v2/ars/score-lot", "/api/v2/audit/events",
        "/api/v2/audit/verify", "/api/v2/idv/collisions", "/api/v2/idv/stats",
    }
    assert expected.issubset(set(paths.keys()))


# ─── COCKPIT · empty when MPI is empty ──────────────────────────────────

def test_cockpit_empty_state_when_no_data(client):
    r = client.get("/api/v2/cockpit")
    assert r.status_code == 200
    body = r.json()
    assert body["has_data"] is False
    # Pas de chiffres inventés · valeurs '—'
    for k in body["kpis"]:
        assert k["value"] == "—" or k["value"].isdigit() or "," in k["value"]
    assert body["file_active_history"] == []
    assert body["sector_alerts"] == []


# ─── HEALTH MONITOR ─────────────────────────────────────────────────────

def test_health_monitor_reports_ml_state(client):
    r = client.get("/api/v2/health-monitor")
    assert r.status_code == 200
    checks = r.json()["checks"]
    labels = [c["label"] for c in checks]
    assert any("MPI" in l for l in labels)
    assert any("format_detector" in l for l in labels)


# ─── ML · 503 if model missing ──────────────────────────────────────────

def test_ml_predict_collision_risk_validates_input(client):
    bad = {"ipp_freq": 1, "ddn_variance_days": 0, "n_distinct_finess": 1,
           "n_distinct_modalities": 1, "ipp_with_letters": 0,
           "year_min": 1800, "year_span": 0}
    r = client.post("/api/v2/ml/predict-collision-risk", json=bad)
    assert r.status_code == 422


def test_ml_predict_collision_risk_real_or_503(client):
    valid = {"ipp_freq": 5, "ddn_variance_days": 100, "n_distinct_finess": 1,
             "n_distinct_modalities": 1, "ipp_with_letters": 0,
             "year_min": 2020, "year_span": 2}
    r = client.post("/api/v2/ml/predict-collision-risk", json=valid)
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        body = r.json()
        assert 0.0 <= body["risk"] <= 1.0
        assert body["level"] in ("low", "medium", "high")


def test_ml_cim_suggest_disabled_when_no_ollama(client, monkeypatch):
    monkeypatch.setattr(fastapi_app, "OLLAMA_BASE", "")
    r = client.post("/api/v2/ml/cim-suggest", json={"das": [], "actes": [], "notes": ""})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "disabled"
    assert body["suggestions"] == []  # PAS de suggestions inventées


# ─── ARS · empty if no sample provided ──────────────────────────────────

def test_ars_score_empty_when_no_sample(client):
    r = client.post("/api/v2/ars/score-lot",
                    json={"lot_name": "test.txt", "sample_lines": []})
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 0
    assert body["risk"] == "unknown"
    assert body["has_ml"] in (True, False)


def test_ars_score_with_real_lines(client):
    line = "X" * 154
    r = client.post("/api/v2/ars/score-lot",
                    json={"lot_name": "test.txt", "sample_lines": [line] * 3})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["score"] <= 100
    assert body["risk"] in ("low", "medium", "high", "unknown")


# ─── AUDIT · vraie persistance SQLite ────────────────────────────────────

def test_audit_events_persist_and_chain(client):
    # Avant · 0 ou état initial
    r0 = client.get("/api/v2/audit/events")
    assert r0.status_code == 200
    initial = len(r0.json())

    # Trigger un événement via predict-collision-risk (qui logge si le modèle
    # est chargé · en l'absence de modèle, on crée manuellement un événement)
    from backend import audit
    audit.append("TEST_USER", "TEST_ACTION", "test_target")

    r1 = client.get("/api/v2/audit/events")
    assert r1.status_code == 200
    events = r1.json()
    assert len(events) >= initial + 1
    last = events[0]
    assert last["who"] == "TEST_USER"
    assert len(last["sha256"]) == 64


def test_audit_verify_chain_endpoint(client):
    r = client.get("/api/v2/audit/verify")
    assert r.status_code == 200
    body = r.json()
    assert "valid" in body
    assert "total_events" in body


def test_audit_respects_limit(client):
    r = client.get("/api/v2/audit/events?limit=2")
    assert r.status_code == 200
    assert len(r.json()) <= 2


# ─── IDV · lit le vrai MPI ───────────────────────────────────────────────

def test_idv_collisions_real_or_empty(client):
    r = client.get("/api/v2/idv/collisions")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)


def test_idv_stats_real_shape(client):
    r = client.get("/api/v2/idv/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total_ipp" in body
    assert "collisions" in body
    assert isinstance(body["total_ipp"], int)


# ─── AUTH ───────────────────────────────────────────────────────────────

def test_auth_blocks_when_token_set(client, monkeypatch):
    monkeypatch.setattr(fastapi_app, "API_TOKEN", "secret-test")
    r = client.get("/api/v2/cockpit")
    assert r.status_code == 401
    r2 = client.get("/api/v2/cockpit",
                    headers={"Authorization": "Bearer wrong"})
    assert r2.status_code == 403
    r3 = client.get("/api/v2/cockpit",
                    headers={"Authorization": "Bearer secret-test"})
    assert r3.status_code == 200


def test_health_remains_public(client, monkeypatch):
    monkeypatch.setattr(fastapi_app, "API_TOKEN", "secret")
    r = client.get("/health")
    assert r.status_code == 200

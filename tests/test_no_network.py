"""
Garde-fou : l'application est 100% locale, sans serveur ni flux réseau.

Ces tests échouent si quelqu'un réintroduit une couche HTTP (Flask, FastAPI,
uvicorn) ou si le frontend repasse par un fetch réseau au lieu du pont pywebview.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_server_modules_are_removed():
    """Les modules serveur ne doivent plus exister dans le paquet."""
    for mod in ("backend.interfaces.bridge", "backend.interfaces.fastapi_app"):
        assert importlib.util.find_spec(mod) is None, f"{mod} ne doit plus exister"


def test_no_server_files_on_disk():
    assert not (ROOT / "backend" / "interfaces" / "bridge.py").exists()
    assert not (ROOT / "backend" / "interfaces" / "fastapi_app.py").exists()
    assert not (ROOT / "bridge.py").exists()
    assert not (ROOT / "php").exists()


def test_api_exposes_v2_methods():
    """Le pont pywebview doit exposer les features v2 en local."""
    from backend.interfaces.api import Api

    api = Api()
    for method in (
        "get_health",
        "get_cockpit",
        "get_health_monitor",
        "ml_predict_format",
        "ars_score_lot",
        "get_audit_events",
        "cespa_check",
        "get_diff",
        "get_heatmap_sectors",
        "get_twin_scenarios",
        "workflow_pending",
    ):
        assert callable(getattr(api, method, None)), f"Api.{method} manquante"


def test_sentinel_returns_plain_dicts_when_empty():
    """Sur un MPI vide, les écrans v2 renvoient des dicts honnêtes (pas de crash)."""
    from backend.interfaces.api import Api

    api = Api()
    cockpit = api.get_cockpit()
    assert cockpit["has_data"] is False
    assert isinstance(cockpit["kpis"], list)
    assert api.get_health()["status"] == "ok"


def test_frontend_uses_local_bridge_not_http():
    """sentinel-helpers.js ne doit plus faire de fetch réseau vers l'API v2."""
    js = (ROOT / "frontend" / "js" / "sentinel-helpers.js").read_text(encoding="utf-8")
    assert "127.0.0.1:8766" not in js, "fetch HTTP résiduel vers l'ancienne API"
    assert "window.pywebview.api" in js, "le pont local doit être utilisé"


@pytest.mark.parametrize("dep", ["fastapi", "flask", "uvicorn", "pydantic"])
def test_requirements_drop_server_deps(dep):
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert dep not in reqs, f"{dep} ne doit plus être une dépendance"

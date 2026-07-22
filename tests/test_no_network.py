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
        "get_duree_sejour",
        "get_regroupement_patients",
    ):
        assert callable(getattr(api, method, None)), f"Api.{method} manquante"


def test_duree_sejour_returns_plain_dict_with_model():
    """Le prédicteur de durée de séjour lit l'artefact entraîné et le sert tel quel."""
    from backend.interfaces.api import Api

    result = Api().get_duree_sejour()
    assert result["has_model"] is True
    assert "par_groupe" in result
    assert "erreur_absolue_moyenne_jours" in result
    assert "coefficient_determination" in result


def test_duree_sejour_missing_artifact_reports_has_model_false(monkeypatch):
    """Sans artefact entraîné, la fonction renvoie un dict honnête, pas un crash."""
    import pathlib

    original_exists = pathlib.Path.exists

    def fake_exists(self):
        if self.name == "duree_sejour_meta.json":
            return False
        return original_exists(self)

    monkeypatch.setattr(pathlib.Path, "exists", fake_exists)

    from backend.interfaces.api import Api

    result = Api().get_duree_sejour()
    assert result["has_model"] is False
    assert "message" in result


def test_regroupement_patients_returns_plain_dict_with_model():
    """Le regroupement de patients lit l'artefact entraîné et le sert tel quel."""
    from backend.interfaces.api import Api

    result = Api().get_regroupement_patients()
    assert result["has_model"] is True
    assert "points" in result
    assert "archetypes" in result


def test_regroupement_patients_missing_artifact_reports_has_model_false(monkeypatch):
    """Sans artefact entraîné, la fonction renvoie un dict honnête, pas un crash."""
    import pathlib

    original_exists = pathlib.Path.exists

    def fake_exists(self):
        if self.name == "regroupement_patients.json":
            return False
        return original_exists(self)

    monkeypatch.setattr(pathlib.Path, "exists", fake_exists)

    from backend.interfaces.api import Api

    result = Api().get_regroupement_patients()
    assert result["has_model"] is False
    assert "message" in result


def test_cim_suggester_suggest_returns_list_for_french_text():
    """Le suggesteur local renvoie des codes CIM-10 plausibles, sans réseau."""
    from backend.ml.cim_suggester import suggest

    suggestions = suggest("syndrome depressif majeur")
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0
    for s in suggestions:
        assert set(s.keys()) == {"code", "label", "confidence"}
        assert 0.0 <= s["confidence"] <= 1.0
    assert suggestions[0]["code"] == "F32.2"


def test_cim_suggester_top_and_min_confidence_are_parameterizable():
    """top / min_confidence pilotent le nombre et le seuil de suggestions."""
    from backend.ml.cim_suggester import suggest

    top1 = suggest("syndrome depressif majeur", top=1)
    assert len(top1) == 1

    strict = suggest("syndrome depressif majeur", min_confidence=0.99)
    assert len(strict) <= len(suggest("syndrome depressif majeur", min_confidence=0.0))


def test_sentinel_cim_suggest_reads_top_k_and_min_confidence_env(monkeypatch):
    """cim_suggest() transmet CIM_SUGGEST_TOP_K / CIM_SUGGEST_MIN_CONFIDENCE."""
    monkeypatch.setenv("CIM_SUGGEST_TOP_K", "1")
    monkeypatch.setenv("CIM_SUGGEST_MIN_CONFIDENCE", "0.02")
    import importlib

    from backend.interfaces import _sentinel

    importlib.reload(_sentinel)
    try:
        result = _sentinel.cim_suggest({"das": [], "actes": [], "notes": "syndrome depressif majeur"})
        assert result["provider"] == "local"
        assert len(result["suggestions"]) <= 1
    finally:
        monkeypatch.delenv("CIM_SUGGEST_TOP_K", raising=False)
        monkeypatch.delenv("CIM_SUGGEST_MIN_CONFIDENCE", raising=False)
        importlib.reload(_sentinel)


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

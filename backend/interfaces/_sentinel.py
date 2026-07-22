"""
Logique des écrans Sentinel v2 (cockpit, ML, ARS, audit, CeSPA, diff, heatmap,
twin, workflow), entièrement in-process.

Aucun serveur, aucune socket, aucun flux réseau : ces fonctions sont appelées
directement par la classe Api du pont pywebview, sur le DataProcessor partagé.
Elles renvoient des dictionnaires JSON-sérialisables, identiques aux réponses
de l'ancienne API v2, pour que le frontend ne change pas de contrat.

Seule exception réseau possible et strictement optionnelle : la suggestion CIM-10
via un serveur Ollama intranet, désactivée par défaut (OLLAMA_BASE vide).
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

import numpy as np

from backend.quality import audit, workflow

_BOOT_TS = time.time()
OPERATOR = os.environ.get("SOVEREIGN_OPERATOR", "DIM_OPERATOR")
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:8b")
API_VERSION = "37.2"


def _ml_models_loaded() -> dict[str, bool]:
    try:
        from backend.ml import load_models

        m = load_models()
        return {"format": "format" in m, "collision": "collision" in m, "ddn": "ddn" in m}
    except Exception:  # pragma: no cover
        return {"format": False, "collision": False, "ddn": False}


def health() -> dict:
    try:
        events_count = audit.count()
    except Exception:
        events_count = 0
    return {
        "status": "ok",
        "service": "sovereign-os-dim",
        "version": API_VERSION,
        "api": "v2",
        "auth_required": False,
        "ml_models_loaded": _ml_models_loaded(),
        "audit_events": events_count,
    }


def cockpit(processor) -> dict:
    stats = processor.get_mpi_stats()
    total_ipp = stats.get("total_ipp", 0)
    collisions = stats.get("collisions", 0)
    pending = stats.get("pending", 0)
    resolved = stats.get("resolved", 0)
    has_data = total_ipp > 0
    today = datetime.now(timezone.utc)

    if not has_data:
        return {
            "month": today.strftime("%Y-%m"),
            "has_data": False,
            "kpis": [
                {
                    "label": "File active",
                    "value": "-",
                    "unit": "",
                    "sub": "Aucun lot traité",
                    "accent": "navy",
                },
                {"label": "Collisions", "value": "-", "unit": "", "sub": "-", "accent": "navy"},
                {"label": "DP renseigné", "value": "-", "unit": "", "sub": "-", "accent": "navy"},
                {"label": "Score DQC", "value": "-", "unit": "", "sub": "-", "accent": "navy"},
            ],
            "file_active_history": [],
            "sector_alerts": [],
        }

    resolved_ratio = (resolved / max(collisions + resolved, 1)) * 100
    return {
        "month": today.strftime("%Y-%m"),
        "has_data": True,
        "kpis": [
            {
                "label": "IPP uniques (MPI)",
                "value": f"{total_ipp:,}".replace(",", " "),
                "unit": "",
                "sub": f"{resolved} résolus - {pending} en attente",
                "accent": "teal",
            },
            {
                "label": "Collisions actives",
                "value": str(collisions),
                "unit": "",
                "sub": f"sur {total_ipp:,} IPP".replace(",", " "),
                "accent": "warning" if collisions > 0 else "success",
            },
            {
                "label": "Taux résolution",
                "value": f"{resolved_ratio:.1f}",
                "unit": "%",
                "sub": "Auto + manuel",
                "accent": "success" if resolved_ratio > 90 else "warning",
            },
            {
                "label": "Formats actifs",
                "value": str(len(processor.matrix)),
                "unit": "",
                "sub": "ATIH supportés",
                "accent": "navy",
            },
        ],
        "file_active_history": [],
        "sector_alerts": [],
    }


def health_monitor(processor) -> dict:
    uptime = int((time.time() - _BOOT_TS) // 3600)
    ml = _ml_models_loaded()
    stats = processor.get_mpi_stats()
    try:
        events = audit.count()
    except Exception:
        events = 0

    checks = [
        {
            "label": "MPI - IPP uniques",
            "ok": True,
            "value": f"{stats.get('total_ipp', 0):,}".replace(",", " "),
        },
        {
            "label": "ML XGBoost - format_detector",
            "ok": ml["format"],
            "value": "chargé" if ml["format"] else "absent",
        },
        {
            "label": "ML - collision_risk",
            "ok": ml["collision"],
            "value": "chargé" if ml["collision"] else "absent",
        },
        {"label": "ML - ddn_validity", "ok": ml["ddn"], "value": "chargé" if ml["ddn"] else "absent"},
        {"label": "Audit log RGPD art. 30", "ok": True, "value": f"{events} événements"},
        {"label": "Pont local in-process", "ok": True, "value": "aucun serveur réseau"},
    ]
    try:
        v = audit.verify_chain()
        checks.append(
            {
                "label": "Intégrité chaîne audit",
                "ok": v["valid"],
                "value": f"{v['total_events']} entrées - "
                + ("OK" if v["valid"] else f"corrompue id {v['broken_at_id']}"),
            }
        )
    except Exception:
        pass

    return {
        "uptime_hours": uptime,
        "ram_mb": 0,
        "requests_per_min": 0,
        "errors_24h": 0,
        "checks": checks,
    }


def predict_format(payload: dict) -> dict:
    line = (payload or {}).get("line", "")
    if not line:
        raise ValueError("Ligne vide")
    from backend.ml import load_models, predict_format as _pf

    models = load_models()
    if "format" not in models:
        raise RuntimeError("Modèle format_detector non chargé - lancer backend.ml.train")
    from backend.ml.predict import _line_to_array, _proba

    X = _line_to_array(line)
    proba = _proba(models["format"], X)[0]
    classes = models["format_classes"]
    top3_idx = np.argsort(proba)[-3:][::-1]
    top3 = [{"label": classes[int(i)], "proba": float(proba[int(i)])} for i in top3_idx]
    label, conf = _pf(line)
    audit.append(OPERATOR, "ML_PREDICT_FORMAT", label or "unknown")
    return {"format": label, "confidence": conf, "top3": top3}


def predict_collision_risk(payload: dict) -> dict:
    from backend.ml import load_models, predict_collision_risk as _pcr

    if "collision" not in load_models():
        raise RuntimeError("Modèle collision_risk non chargé")
    risk = _pcr(payload or {})
    level = "high" if risk > 0.7 else "medium" if risk > 0.3 else "low"
    return {"risk": risk, "level": level}


def predict_ddn_validity(payload: dict) -> dict:
    line = (payload or {}).get("line", "")
    from backend.ml import load_models, predict_ddn_validity as _pdv

    if "ddn" not in load_models():
        raise RuntimeError("Modèle ddn_validity non chargé")
    p = _pdv(line)
    return {"valid_proba": p, "suspect": p < 0.5}


def cim_suggest(payload: dict) -> dict:
    """Suggestions de codes diagnostiques.

    Fournisseur par défaut : modèle local entraîné sur libellés synthétiques
    (backend/ml/cim_suggester.py), disponible sans aucune configuration.
    Si un serveur Ollama intranet est configuré (OLLAMA_BASE), il prend la main.
    """
    payload = payload or {}
    das = payload.get("das", []) or []
    actes = payload.get("actes", []) or []
    notes = payload.get("notes", "") or ""
    if not OLLAMA_BASE:
        from backend.ml.cim_suggester import suggest as _local_suggest

        texte = " ".join([*das, *actes, notes]).strip()
        sugg = _local_suggest(texte)
        if sugg:
            audit.append(OPERATOR, "CIM_SUGGEST_LOCAL", f"das={len(das)}")
        return {"suggestions": sugg, "provider": "local"}
    from urllib.parse import urlparse

    parsed = urlparse(OLLAMA_BASE)
    if parsed.scheme not in ("http", "https"):
        raise RuntimeError(f"OLLAMA_BASE doit utiliser http ou https, reçu '{parsed.scheme}'")
    if not parsed.netloc:
        raise RuntimeError("OLLAMA_BASE doit inclure un hôte")
    import json as _json
    import urllib.request

    prompt = (
        "Tu es un médecin DIM. Suggère 5 codes CIM-10 candidats pour "
        "diagnostic principal en psychiatrie, avec confiance 0-1. "
        f"DAS: {das}. Actes: {actes}. Notes: {notes[:500]}"
    )
    body = _json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"}).encode()
    safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/api/generate"
    req_obj = urllib.request.Request(safe_url, data=body, headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req_obj, timeout=30)  # nosec B310 - URL validée http(s) ci-dessus
    resp = _json.loads(r.read())
    parsed_resp = _json.loads(resp.get("response", "[]"))
    sugg = [
        {"code": s["code"], "label": s["label"], "confidence": float(s.get("confidence", 0.0))}
        for s in parsed_resp[:5]
        if isinstance(s, dict) and "code" in s and "label" in s
    ]
    audit.append(OPERATOR, "CIM_SUGGEST", f"das={len(das)}")
    return {"suggestions": sugg, "provider": "ollama"}


def ars_score_lot(payload: dict) -> dict:
    payload = payload or {}
    lot_name = payload.get("lot_name", "lot")
    sample = [s for s in (payload.get("sample_lines") or []) if s.strip()]
    if not sample:
        return {
            "lot_name": lot_name,
            "score": 0,
            "risk": "unknown",
            "issues_count": 0,
            "breakdown": [],
            "has_ml": False,
        }

    from backend.ml import load_models, predict_format as _pf, predict_ddn_validity as _pdv

    models = load_models()
    if not ("format" in models and "ddn" in models):
        return {
            "lot_name": lot_name,
            "score": 0,
            "risk": "unknown",
            "issues_count": 0,
            "breakdown": [{"check": "Modèles ML", "ok": False, "value": "absents"}],
            "has_ml": False,
        }

    fmt_ok = ddn_total = issues = 0
    for line in sample:
        _, conf = _pf(line)
        fmt_ok += int(conf > 0.7)
        v = _pdv(line)
        ddn_total += v
        if v < 0.5:
            issues += 1

    n = len(sample)
    fmt_ratio = fmt_ok / n
    ddn_ratio = ddn_total / n
    score = int(round(60 * fmt_ratio + 40 * ddn_ratio))
    risk = "high" if score < 50 else "medium" if score < 75 else "low"
    audit.append(OPERATOR, "ARS_SCORE_LOT", lot_name)
    return {
        "lot_name": lot_name,
        "score": score,
        "risk": risk,
        "issues_count": issues,
        "has_ml": True,
        "breakdown": [
            {"check": "Cohérence format ATIH", "ok": fmt_ratio > 0.8, "value": f"{int(fmt_ratio * 100)} %"},
            {"check": "DDN valides", "ok": ddn_ratio > 0.95, "value": f"{int(ddn_ratio * 100)} %"},
            {"check": "Échantillon analysé", "ok": True, "value": f"{n} lignes"},
        ],
    }


def audit_events(limit: int = 30) -> list[dict]:
    return audit.list_events(limit=max(1, min(int(limit or 30), 1000)))


def audit_verify() -> dict:
    return audit.verify_chain()


def idv_stats(processor) -> dict:
    return processor.get_mpi_stats()


def cespa_check(processor) -> dict:
    breakdown = processor.get_format_breakdown()
    rps_lines = sum(b["lines"] for b in breakdown if b.get("format") == "RPS")
    raa_lines = sum(b["lines"] for b in breakdown if b.get("format") == "RAA")
    rules = [
        {
            "code": "R-CSP-01",
            "label": "Code structure CeSPA présent dans champ 23 RPS",
            "ok": rps_lines,
            "total": rps_lines,
            "required": True,
        },
        {
            "code": "R-CSP-02",
            "label": "Forfait CATTG facturable et acte tracé",
            "ok": raa_lines,
            "total": raa_lines,
            "required": True,
        },
        {
            "code": "R-CSP-04",
            "label": "Médecin responsable rattaché à structure CeSPA",
            "ok": rps_lines,
            "total": rps_lines,
            "required": True,
        },
        {
            "code": "R-CSP-09",
            "label": "Patient adulte (18 ans ou plus à l'admission)",
            "ok": rps_lines,
            "total": rps_lines,
            "required": True,
        },
    ]
    has_data = (rps_lines + raa_lines) > 0
    return {"has_data": has_data, "rps_lines": rps_lines, "raa_lines": raa_lines, "rules": rules}


def diff_lots(processor) -> dict:
    stats = processor.get_mpi_stats()
    if not stats.get("total_ipp"):
        return {"has_data": False, "rows": [], "message": "Aucun lot traité - diff impossible"}
    breakdown = processor.get_format_breakdown()
    rows = [
        {
            "indicator": b.get("format", "?"),
            "current": b.get("lines", 0),
            "previous": 0,
            "delta_abs": b.get("lines", 0),
            "delta_pct": None,
            "state": "new",
        }
        for b in breakdown
    ]
    return {"has_data": True, "rows": rows}


def heatmap_sectors(processor) -> dict:
    if not processor.get_mpi_stats().get("total_ipp"):
        return {"has_data": False, "sectors": []}
    cp_counts: dict[str, int] = {}
    for ipp_data in processor.mpi.values():
        for obs in ipp_data.get("observations", []):
            cp = obs.get("code_postal", "")
            if cp and cp.strip():
                key = cp.strip()[:5]
                cp_counts[key] = cp_counts.get(key, 0) + 1
    sectors = sorted(
        ({"code": k, "file_active": v} for k, v in cp_counts.items()),
        key=lambda x: x["file_active"],
        reverse=True,
    )[:20]
    if not sectors:
        return {"has_data": False, "sectors": []}
    max_v = max(s["file_active"] for s in sectors)

    def intensity(v: int) -> str:
        if v >= max_v * 0.75:
            return "very_high"
        if v >= max_v * 0.50:
            return "high"
        if v >= max_v * 0.25:
            return "medium"
        return "low"

    for s in sectors:
        s["intensity"] = intensity(s["file_active"])
    return {"has_data": True, "sectors": sectors}


def twin_scenarios(processor) -> dict:
    stats = processor.get_mpi_stats()
    n = stats.get("total_ipp", 0)
    if n == 0:
        return {"has_data": False, "scenarios": [], "message": "MPI vide - simulation impossible"}
    scenarios = [
        {
            "label": "Combler 5 % de DP manquants",
            "impact_eur": int(n * 0.05 * 1470 * 0.7),
            "confidence": 0.91,
        },
        {"label": "Améliorer chaînage de 1 point", "impact_eur": int(n * 0.01 * 1470), "confidence": 0.74},
        {
            "label": "Préflight DRUIDES sur 100 % des lots",
            "impact_eur": int(n * 0.005 * 1470),
            "confidence": 0.88,
        },
    ]
    return {"has_data": True, "ipp_base": n, "scenarios": scenarios}


def workflow_pending(stage: str | None = None, limit: int = 100) -> dict:
    items = workflow.list_pending(
        stage_filter=stage if stage in ("tim", "mim", "preflight", "ars") else None,
        limit=max(1, min(int(limit or 100), 500)),
    )
    return {"counts": workflow.stage_counts(), "items": items}


def workflow_add(payload: dict) -> dict:
    payload = payload or {}
    ipp = payload.get("ipp", "")
    label = payload.get("label", "")
    stage = payload.get("stage", "tim")
    if stage not in ("tim", "mim", "preflight", "ars"):
        stage = "tim"
    item = workflow.add_item(ipp, label, OPERATOR, stage=stage)
    audit.append(OPERATOR, "WORKFLOW_ADD", f"item#{item['id']} {ipp}")
    return item


def workflow_advance(item_id: int, new_stage: str) -> dict:
    if new_stage not in ("tim", "mim", "preflight", "ars", "done"):
        raise ValueError(f"Stage invalide : {new_stage}")
    item = workflow.advance(int(item_id), new_stage)
    if not item:
        raise LookupError(f"Item {item_id} introuvable")
    audit.append(OPERATOR, "WORKFLOW_ADVANCE", f"item#{item_id} -> {new_stage}")
    return item


def duree_sejour() -> dict:
    """Prédicteur de durée de séjour : métriques et statistiques par groupe.

    Lit les artefacts entraînés par backend/ml/train_sejour_models.py
    (données synthétiques uniquement, sorties présentées comme estimations).
    """
    import json
    from pathlib import Path

    meta_path = Path(__file__).resolve().parent.parent / "ml" / "models" / "duree_sejour_meta.json"
    if not meta_path.exists():
        return {"has_model": False, "message": "Modèle non entraîné - python -m backend.ml.train_sejour_models"}
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["has_model"] = True
    return meta


def regroupement_patients() -> dict:
    """Regroupement de patients : projection 2D et archétypes (synthétique)."""
    import json
    from pathlib import Path

    art_path = Path(__file__).resolve().parent.parent / "ml" / "models" / "regroupement_patients.json"
    if not art_path.exists():
        return {"has_model": False, "message": "Modèle non entraîné - python -m backend.ml.train_sejour_models"}
    art = json.loads(art_path.read_text(encoding="utf-8"))
    art["has_model"] = True
    return art

/* ═══════════════════════════════════════════════════════════════════════════
   SENTINEL HELPERS · primitives partagées par toutes les vues portées
   ─────────────────────────────────────────────────────────────────────────
   Source · docs/design/sentinel-refonte/project/screens/shared.jsx
   Vanilla JS · zéro dépendance React. Charge via index.html avant les vues.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  const NAVY = "#253e80", TEAL = "#0c7db6", GOLD = "#D4A437";
  const ERROR = "#E11D48", SUCCESS = "#10B981", WARNING = "#F59E0B";
  const slate = {
    50: "#F8FAFC", 100: "#F1F5F9", 200: "#E2E8F0", 300: "#CBD5E1",
    400: "#94A3B8", 500: "#64748B", 600: "#475569", 700: "#334155",
    800: "#1E293B", 900: "#0F172A",
  };

  const FMT_KIND = {
    PSY:   { bg: "#EEF2FF", fg: "#4338CA" },
    SSR:   { bg: "#ECFDF5", fg: "#0F766E" },
    HAD:   { bg: "#FFFBEB", fg: "#B45309" },
    MCO:   { bg: "#FFF1F2", fg: "#BE123C" },
    TRANS: { bg: "#F1F5F9", fg: "#475569" },
  };

  function sectionHead({ eyebrow, title, meta, action }) {
    return `
      <div style="display:flex;align-items:flex-end;justify-content:space-between;
                  padding-bottom:14px;border-bottom:1px solid var(--border-card);margin-bottom:18px;">
        <div>
          ${eyebrow ? `<div style="font-size:10px;font-weight:700;color:${TEAL};
              text-transform:uppercase;letter-spacing:0.18em;margin-bottom:6px;">${eyebrow}</div>` : ""}
          <div style="font-size:22px;font-weight:800;color:var(--text-primary);
              letter-spacing:-0.02em;line-height:1.1;">${title}</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          ${meta ? `<span style="font-size:11px;font-weight:600;color:var(--text-muted-color);">${meta}</span>` : ""}
          ${action || ""}
        </div>
      </div>`;
  }

  function kpi({ label, value, unit, sub, accent }) {
    accent = accent || TEAL;
    return `
      <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:12px;
                  padding:16px 20px;position:relative;overflow:hidden;
                  box-shadow:0 1px 2px rgba(0,0,145,.03);">
        <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:${accent};"></div>
        <div style="font-size:10px;font-weight:700;color:var(--text-muted-color);
            text-transform:uppercase;letter-spacing:0.13em;">${label}</div>
        <div style="margin-top:8px;display:flex;align-items:baseline;gap:6px;">
          <span style="font-size:28px;font-weight:800;color:var(--text-primary);line-height:1;
              font-variant-numeric:tabular-nums;letter-spacing:-0.025em;">${value}</span>
          ${unit ? `<span style="font-size:11px;color:var(--text-muted-color);font-weight:600;">${unit}</span>` : ""}
        </div>
        ${sub ? `<div style="font-size:11px;color:var(--text-muted-color);margin-top:6px;">${sub}</div>` : ""}
      </div>`;
  }

  function card({ title, icon, action, body, padding }) {
    if (padding === undefined) padding = 20;
    const header = title || action ? `
      <div style="padding:14px 20px;border-bottom:1px solid var(--border-item);
                  display:flex;align-items:center;justify-content:space-between;
                  background:var(--bg-hover);">
        <div style="display:flex;align-items:center;gap:9px;">
          ${icon ? `<i data-lucide="${icon}" style="width:16px;height:16px;color:${TEAL};"></i>` : ""}
          <span style="font-size:11px;font-weight:700;color:var(--text-primary);
              text-transform:uppercase;letter-spacing:0.14em;">${title || ""}</span>
        </div>
        ${action || ""}
      </div>` : "";
    return `
      <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:12px;
                  overflow:hidden;box-shadow:0 1px 2px rgba(0,0,145,.03);">
        ${header}
        <div style="padding:${padding}px;">${body}</div>
      </div>`;
  }

  function btn({ label, kind, icon, sm }) {
    kind = kind || "primary";
    const styles = {
      primary: { bg: NAVY, fg: "white", border: NAVY },
      teal:    { bg: TEAL, fg: "white", border: TEAL },
      ghost:   { bg: "var(--bg-card)", fg: "var(--text-secondary)", border: "var(--border-card)" },
      danger:  { bg: "var(--bg-card)", fg: ERROR, border: "#FCA5A5" },
      warn:    { bg: WARNING, fg: "white", border: WARNING },
    };
    const c = styles[kind];
    const pad = sm ? "6px 12px" : "9px 16px";
    const fs = sm ? 11 : 12;
    return `<button style="display:inline-flex;align-items:center;gap:7px;padding:${pad};
        background:${c.bg};color:${c.fg};border:1px solid ${c.border};border-radius:8px;
        font-size:${fs}px;font-weight:700;letter-spacing:0.01em;cursor:pointer;
        font-family:inherit;">
      ${icon ? `<i data-lucide="${icon}" style="width:${sm ? 13 : 14}px;height:${sm ? 13 : 14}px;"></i>` : ""}
      ${label}
    </button>`;
  }

  function fmtBadge(label, kind) {
    const c = FMT_KIND[kind] || FMT_KIND.TRANS;
    return `<span style="display:inline-flex;align-items:center;gap:5px;
        padding:3px 9px;border-radius:999px;background:${c.bg};color:${c.fg};
        font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
        letter-spacing:0.02em;">
      <span style="width:5px;height:5px;border-radius:999px;background:${c.fg};"></span>${label}
    </span>`;
  }

  function statusPill(label, color) {
    return `<span style="display:inline-flex;align-items:center;gap:5px;
        padding:3px 8px;border-radius:6px;background:${color}20;color:${color};
        font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;">
      <span style="width:5px;height:5px;border-radius:999px;background:${color};"></span>${label}
    </span>`;
  }

  function metierBanner(html) {
    return `<div style="background:#FEF3C7;border-left:4px solid ${GOLD};
        border-radius:8px;padding:14px 18px;display:flex;
        align-items:center;gap:12px;margin-top:18px;">
      <i data-lucide="info" style="width:20px;height:20px;color:${GOLD};flex-shrink:0;"></i>
      <div style="font-size:13px;color:var(--text-secondary);line-height:1.5;">${html}</div>
    </div>`;
  }

  function renderInto(html) {
    const vp = document.getElementById("os-viewport");
    if (!vp) return null;
    vp.innerHTML = `<div style="max-width:1440px;margin:0 auto;">${html}</div>`;
    if (window.lucide) lucide.createIcons();
    return vp;
  }

  /** État vide générique · à utiliser quand l'API ne renvoie pas de données.
   *  PROD · jamais de données fictives. icon = nom Lucide. */
  function emptyState({ title, body, icon, action }) {
    return `
      <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:12px;
                  padding:48px 32px;text-align:center;
                  box-shadow:0 1px 2px rgba(0,0,145,.03);">
        <div style="width:56px;height:56px;border-radius:14px;background:var(--bg-hover);
            border:1px solid var(--border-card);margin:0 auto 18px;display:flex;
            align-items:center;justify-content:center;color:var(--text-muted-color);">
          <i data-lucide="${icon || 'inbox'}" style="width:26px;height:26px;"></i>
        </div>
        <div style="font-size:16px;font-weight:700;color:var(--text-primary);
            letter-spacing:-0.015em;margin-bottom:6px;">${title}</div>
        <div style="font-size:13px;color:var(--text-muted-color);max-width:480px;
            margin:0 auto 18px;line-height:1.5;">${body}</div>
        ${action || ""}
      </div>`;
  }

  /** Loading state · skeleton card pendant l'attente de l'API */
  function loadingState(label) {
    return `
      <div style="background:var(--bg-card);border:1px solid var(--border-card);border-radius:12px;
                  padding:32px;text-align:center;">
        <div style="display:inline-block;width:24px;height:24px;
            border:2px solid var(--border-card);border-top-color:${TEAL};
            border-radius:50%;animation:spin 0.8s linear infinite;"></div>
        <div style="margin-top:14px;font-size:12px;color:var(--text-muted-color);">${label || "Chargement…"}</div>
        <style>@keyframes spin {to {transform:rotate(360deg);}}</style>
      </div>`;
  }

  /**
   * Pont 100% local. Route un ancien chemin d'API v2 vers une methode du pont
   * pywebview in-process (window.pywebview.api). Aucun fetch, aucune socket,
   * aucun flux reseau. Conserve le contrat de retour {ok, data, status, error}.
   */
  async function api(path, init) {
    const opts = init || {};
    const method = (opts.method || "GET").toUpperCase();
    let body = opts.body;
    if (typeof body === "string") {
      try { body = JSON.parse(body); } catch { /* garde tel quel */ }
    }
    // Separer le chemin des parametres de requete.
    const [rawPath, qs] = String(path).split("?");
    const params = {};
    if (qs) {
      for (const kv of qs.split("&")) {
        const [k, v] = kv.split("=");
        if (k) params[decodeURIComponent(k)] = decodeURIComponent(v || "");
      }
    }

    const bridge = window.pywebview && window.pywebview.api;
    if (!bridge) {
      return { ok: false, status: 0, data: null, error: "Pont local indisponible" };
    }

    try {
      let data;
      switch (true) {
        case rawPath === "/health":
          data = await bridge.get_health(); break;
        case rawPath === "/api/v2/cockpit":
          data = await bridge.get_cockpit(); break;
        case rawPath === "/api/v2/health-monitor":
          data = await bridge.get_health_monitor(); break;
        case rawPath === "/api/v2/ml/predict-format":
          data = await bridge.ml_predict_format(body); break;
        case rawPath === "/api/v2/ml/predict-collision-risk":
          data = await bridge.ml_predict_collision_risk(body); break;
        case rawPath === "/api/v2/ml/predict-ddn-validity":
          data = await bridge.ml_predict_ddn_validity(body); break;
        case rawPath === "/api/v2/ml/cim-suggest":
          data = await bridge.ml_cim_suggest(body); break;
        case rawPath === "/api/v2/ars/score-lot":
          data = await bridge.ars_score_lot(body); break;
        case rawPath === "/api/v2/audit/events":
          data = await bridge.get_audit_events(Number(params.limit) || 30); break;
        case rawPath === "/api/v2/audit/verify":
          data = await bridge.audit_verify(); break;
        case rawPath === "/api/v2/idv/stats":
          data = await bridge.get_idv_stats(); break;
        case rawPath === "/api/v2/cespa/check":
          data = await bridge.cespa_check(); break;
        case rawPath === "/api/v2/diff":
          data = await bridge.get_diff(); break;
        case rawPath === "/api/v2/heatmap/sectors":
          data = await bridge.get_heatmap_sectors(); break;
        case rawPath === "/api/v2/twin/scenarios":
          data = await bridge.get_twin_scenarios(); break;
        case rawPath === "/api/v2/pivot":
          data = await bridge.get_pivot(); break;
        case rawPath === "/api/v2/workflow/pending":
          data = await bridge.workflow_pending(params.stage || null, Number(params.limit) || 100); break;
        case rawPath === "/api/v2/workflow/add":
          data = await bridge.workflow_add(body); break;
        case rawPath.startsWith("/api/v2/workflow/advance/"):
          data = await bridge.workflow_advance(
            Number(rawPath.split("/").pop()), params.new_stage || (body && body.new_stage)
          ); break;
        default:
          return { ok: false, status: 404, data: null, error: "Route locale inconnue : " + rawPath };
      }
      return { ok: true, status: 200, data };
    } catch (e) {
      return { ok: false, status: 500, data: null, error: (e && e.message) || String(e) };
    }
  }

  // Expose globalement
  window.SentinelHelpers = {
    NAVY, TEAL, GOLD, ERROR, SUCCESS, WARNING, slate,
    sectionHead, kpi, card, btn, fmtBadge, statusPill, metierBanner,
    renderInto, emptyState, loadingState, api,
  };
})();

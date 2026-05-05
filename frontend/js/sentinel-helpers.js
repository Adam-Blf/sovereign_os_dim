/* ═══════════════════════════════════════════════════════════════════════════
   SENTINEL HELPERS · primitives partagées par toutes les vues portées
   ─────────────────────────────────────────────────────────────────────────
   Source · docs/design/sentinel-refonte/project/screens/shared.jsx
   Vanilla JS · zéro dépendance React. Charge via index.html avant les vues.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  const NAVY = "#000091", TEAL = "#00897B", GOLD = "#D4A437";
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
                  padding-bottom:14px;border-bottom:1px solid ${slate[200]};margin-bottom:18px;">
        <div>
          ${eyebrow ? `<div style="font-size:10px;font-weight:700;color:${TEAL};
              text-transform:uppercase;letter-spacing:0.18em;margin-bottom:6px;">${eyebrow}</div>` : ""}
          <div style="font-size:22px;font-weight:800;color:${NAVY};
              letter-spacing:-0.02em;line-height:1.1;">${title}</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          ${meta ? `<span style="font-size:11px;font-weight:600;color:${slate[500]};">${meta}</span>` : ""}
          ${action || ""}
        </div>
      </div>`;
  }

  function kpi({ label, value, unit, sub, accent }) {
    accent = accent || TEAL;
    return `
      <div style="background:white;border:1px solid ${slate[200]};border-radius:12px;
                  padding:16px 20px;position:relative;overflow:hidden;
                  box-shadow:0 1px 2px rgba(0,0,145,.03);">
        <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:${accent};"></div>
        <div style="font-size:10px;font-weight:700;color:${slate[500]};
            text-transform:uppercase;letter-spacing:0.13em;">${label}</div>
        <div style="margin-top:8px;display:flex;align-items:baseline;gap:6px;">
          <span style="font-size:28px;font-weight:800;color:${NAVY};line-height:1;
              font-variant-numeric:tabular-nums;letter-spacing:-0.025em;">${value}</span>
          ${unit ? `<span style="font-size:11px;color:${slate[500]};font-weight:600;">${unit}</span>` : ""}
        </div>
        ${sub ? `<div style="font-size:11px;color:${slate[500]};margin-top:6px;">${sub}</div>` : ""}
      </div>`;
  }

  function card({ title, icon, action, body, padding }) {
    if (padding === undefined) padding = 20;
    const header = title || action ? `
      <div style="padding:14px 20px;border-bottom:1px solid ${slate[100]};
                  display:flex;align-items:center;justify-content:space-between;
                  background:${slate[50]};">
        <div style="display:flex;align-items:center;gap:9px;">
          ${icon ? `<i data-lucide="${icon}" style="width:16px;height:16px;color:${TEAL};"></i>` : ""}
          <span style="font-size:11px;font-weight:700;color:${NAVY};
              text-transform:uppercase;letter-spacing:0.14em;">${title || ""}</span>
        </div>
        ${action || ""}
      </div>` : "";
    return `
      <div style="background:white;border:1px solid ${slate[200]};border-radius:12px;
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
      ghost:   { bg: "white", fg: slate[700], border: slate[300] },
      danger:  { bg: "white", fg: ERROR, border: "#FCA5A5" },
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
      <div style="font-size:13px;color:${slate[700]};line-height:1.5;">${html}</div>
    </div>`;
  }

  function renderInto(html) {
    const vp = document.getElementById("os-viewport");
    if (!vp) return null;
    vp.innerHTML = `<div style="max-width:1440px;margin:0 auto;">${html}</div>`;
    if (window.lucide) lucide.createIcons();
    return vp;
  }

  // Expose globalement
  window.SentinelHelpers = {
    NAVY, TEAL, GOLD, ERROR, SUCCESS, WARNING, slate,
    sectionHead, kpi, card, btn, fmtBadge, statusPill, metierBanner, renderInto,
  };
})();

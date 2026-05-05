/* ═══════════════════════════════════════════════════════════════════════════
   COCKPIT CHEF DIM · vue exécutive mensuelle
   ─────────────────────────────────────────────────────────────────────────
   Portée 1:1 du design Sentinel · Refonte ecrans (artboard 02). Vanilla JS
   qui s'injecte dans #os-viewport, sans React, sans Babel runtime.

   Public · chef de pôle DIM · reporting mensuel auto-publié à M+5.
   Donnees · MPI courant + agrégats par secteur ARS depuis le data_processor.
   Source design · docs/design/sentinel-refonte/project/screens/metier.jsx
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  const NAVY = "#000091", TEAL = "#00897B", GOLD = "#D4A437";
  const SUCCESS = "#10B981", WARNING = "#F59E0B", ERROR = "#E11D48";
  const slate = {
    50: "#F8FAFC", 100: "#F1F5F9", 200: "#E2E8F0", 300: "#CBD5E1",
    400: "#94A3B8", 500: "#64748B", 600: "#475569", 700: "#334155",
    800: "#1E293B", 900: "#0F172A",
  };

  /** Card factory · header + corps. Coherent avec les autres views. */
  function card(title, iconName, body) {
    return `
      <div style="background:white;border:1px solid ${slate[200]};border-radius:16px;
                  box-shadow:0 1px 2px 0 rgba(0,0,145,.04);padding:18px 20px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
          <i data-lucide="${iconName}" style="width:18px;height:18px;color:${TEAL};"></i>
          <span style="font-size:13px;font-weight:700;color:${NAVY};
                       letter-spacing:-0.005em;">${title}</span>
        </div>
        ${body}
      </div>`;
  }

  function kpi(label, value, unit, sub, accent) {
    return `
      <div style="background:white;border:1px solid ${slate[200]};border-radius:16px;
                  padding:16px 18px;position:relative;overflow:hidden;
                  box-shadow:0 1px 2px 0 rgba(0,0,145,.04);">
        <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:${accent};"></div>
        <div style="font-size:11px;font-weight:700;color:${slate[500]};
                    text-transform:uppercase;letter-spacing:0.12em;">${label}</div>
        <div style="font-size:30px;font-weight:800;color:${NAVY};line-height:1.1;
                    margin-top:6px;font-variant-numeric:tabular-nums;">
          ${value}<span style="font-size:14px;color:${slate[500]};margin-left:4px;
                              font-weight:600;">${unit || ""}</span>
        </div>
        <div style="font-size:11px;color:${slate[500]};margin-top:4px;">${sub}</div>
      </div>`;
  }

  function bar(value, label, isLast) {
    const fillColor = isLast ? NAVY : TEAL;
    const opacity = isLast ? 1 : 0.55;
    const labelTop = isLast
      ? `<div style="position:absolute;top:-22px;left:50%;transform:translateX(-50%);
                     font-size:10px;font-weight:800;color:${NAVY};
                     font-family:'JetBrains Mono',monospace;">14,9k</div>`
      : "";
    return `
      <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px;">
        <div style="width:100%;height:${value}%;background:${fillColor};
                    border-radius:4px 4px 0 0;opacity:${opacity};position:relative;">
          ${labelTop}
        </div>
        <span style="font-size:10px;color:${slate[500]};font-weight:600;">${label}</span>
      </div>`;
  }

  function alertRow(sec, val, color, lib, last) {
    const border = last ? "" : `border-bottom:1px solid ${slate[100]};`;
    return `
      <div style="padding:10px 0;${border}">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-size:12px;font-weight:700;color:${slate[800]};
                       font-family:'JetBrains Mono',monospace;">${sec}</span>
          <span style="font-size:13px;font-weight:800;color:${color};
                       font-family:'JetBrains Mono',monospace;">${val}</span>
        </div>
        <div style="font-size:11px;color:${slate[500]};margin-top:2px;">${lib}</div>
      </div>`;
  }

  /** Tente de récupérer les vraies données depuis FastAPI v2, fallback mock. */
  async function fetchData() {
    const FASTAPI_BASE = window.SOVEREIGN_API_BASE || "http://127.0.0.1:8766";
    try {
      const r = await fetch(FASTAPI_BASE + "/api/v2/cockpit", {
        headers: window.SOVEREIGN_API_TOKEN
          ? { Authorization: "Bearer " + window.SOVEREIGN_API_TOKEN } : {},
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      return { live: true, data: await r.json() };
    } catch (e) {
      // Fallback mock · si la FastAPI n'est pas démarrée, l'écran reste utile
      return { live: false, data: null };
    }
  }

  /** Rend la vue Cockpit chef DIM dans le viewport principal. */
  async function render() {
    const vp = document.getElementById("os-viewport");
    if (!vp) return;

    const today = new Date();
    const monthLabel = today.toLocaleString("fr-FR", { month: "long", year: "numeric" });

    const { live, data } = await fetchData();
    const labels = ["D24", "J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N"];
    let months, alerts;
    if (live && data) {
      months = data.file_active_history.map((v, i) => ({ v, l: labels[i] }));
      alerts = data.sector_alerts.map(a => ({
        sec: "Secteur " + a.sector,
        val: (a.delta_pct >= 0 ? "+ " : "− ") + Math.abs(a.delta_pct).toFixed(1) + " %",
        color: Math.abs(a.delta_pct) > 3 ? (a.delta_pct < 0 ? ERROR : WARNING)
                                          : WARNING,
        lib: a.label,
      }));
    } else {
      months = [
        { v: 68, l: "D24" }, { v: 72, l: "J" }, { v: 75, l: "F" }, { v: 71, l: "M" },
        { v: 78, l: "A" },   { v: 82, l: "M" }, { v: 79, l: "J" }, { v: 85, l: "J" },
        { v: 88, l: "A" },   { v: 91, l: "S" }, { v: 87, l: "O" }, { v: 94, l: "N" },
      ];
      alerts = [
        { sec: "Secteur 94G16", val: "+ 4,2 %", color: WARNING, lib: "Hospitalisations psy" },
        { sec: "Secteur 94I02", val: "− 2,8 %", color: ERROR,   lib: "File active pédopsy" },
        { sec: "Secteur 94G09", val: "+ 2,3 %", color: WARNING, lib: "Actes ambulatoires" },
      ];
    }

    vp.innerHTML = `
      <div style="max-width:1440px;margin:0 auto;">
        <!-- Section header -->
        <div style="display:flex;justify-content:space-between;align-items:flex-end;
                    padding-bottom:18px;border-bottom:1px solid ${slate[200]};margin-bottom:24px;">
          <div>
            <div style="font-size:11px;font-weight:700;color:${TEAL};
                        text-transform:uppercase;letter-spacing:0.18em;">Vue mensuelle</div>
            <h2 style="margin:4px 0 0 0;font-size:28px;font-weight:800;color:${NAVY};
                       letter-spacing:-0.02em;line-height:1.1;">
              Activité GHT · ${monthLabel}
            </h2>
            <div style="font-size:12px;color:${slate[500]};font-weight:600;margin-top:6px;">
              MAJ il y a 8 min · auto-publication M+5
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="display:inline-flex;align-items:center;gap:5px;padding:4px 10px;
                border-radius:999px;font-size:10px;font-weight:700;letter-spacing:0.14em;
                text-transform:uppercase;
                background:${live ? "#ECFDF5" : slate[100]};
                color:${live ? SUCCESS : slate[500]};">
              <span style="width:6px;height:6px;border-radius:999px;
                  background:${live ? SUCCESS : slate[400]};"></span>
              ${live ? "API LIVE" : "DONNÉES MOCK"}
            </span>
            <button id="btn-cockpit-export"
                    style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;
                           background:${NAVY};color:white;font-weight:700;font-size:13px;
                           border-radius:12px;border:none;cursor:pointer;
                           box-shadow:0 1px 2px 0 rgba(0,0,145,.06);">
              <i data-lucide="download" style="width:16px;height:16px;"></i>
              Export PDF mensuel
            </button>
          </div>
        </div>

        <!-- 4 KPI cards -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;">
          ${kpi("File active 12 mois", "14 882", "", "+ 3,2 % vs N-1", TEAL)}
          ${kpi("Taux chaînage",        "98,4",   "%", "Cible ≥ 97 %", SUCCESS)}
          ${kpi("DP renseigné",         "96,1",   "%", "Cible ≥ 95 %", SUCCESS)}
          ${kpi("Score DQC",            "A",      "",  "9 mois consécutifs", GOLD)}
        </div>

        <!-- Chart + alertes -->
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-bottom:20px;">
          ${card("File active glissante · 12 mois", "trending-up", `
            <div style="display:flex;align-items:flex-end;gap:10px;height:180px;padding:12px 4px;">
              ${months.map((m, i) => bar(m.v, m.l, i === months.length - 1)).join("")}
            </div>`)}

          ${card("Alertes écart > 2 %", "alert-triangle",
            alerts.map((a, i) => alertRow(a.sec, a.val, a.color, a.lib, i === alerts.length - 1)).join(""))}
        </div>

        <!-- Bandeau gold métier · contexte stratégique -->
        <div style="background:#FEF3C7;border-left:4px solid ${GOLD};
                    border-radius:8px;padding:14px 18px;display:flex;
                    align-items:center;gap:12px;">
          <i data-lucide="info" style="width:20px;height:20px;color:${GOLD};"></i>
          <div style="font-size:13px;color:${slate[700]};line-height:1.5;">
            <strong style="color:${NAVY};">Réforme financement PSY · sécurisation 2029 = 0 %.</strong>
            Score qualité PMSI du mois · 92,4 / 100. Maintenir taux chaînage > 97 %
            pour préserver la DFA 2026 (15 % du financement).
          </div>
        </div>
      </div>`;

    // Réveil des icônes Lucide
    if (window.lucide) lucide.createIcons();

    // Action export PDF · à brancher sur l'API quand dispo
    const btn = document.getElementById("btn-cockpit-export");
    if (btn) {
      btn.addEventListener("click", () => {
        if (window.osToast) {
          window.osToast(
            "Cockpit · export PDF",
            "Le rapport mensuel sera disponible quand l'endpoint /api/cockpit-pdf sera implémenté.",
            "info"
          );
        } else {
          alert("Export PDF mensuel · endpoint à brancher (/api/cockpit-pdf).");
        }
      });
    }
  }

  // Expose la vue au router · app.js l'appelle via window.cockpitView.render()
  window.cockpitView = { render };
})();

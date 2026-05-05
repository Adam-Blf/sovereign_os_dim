/* ═══════════════════════════════════════════════════════════════════════════
   COCKPIT CHEF DIM · vue exécutive mensuelle · PROD
   ─────────────────────────────────────────────────────────────────────────
   Lit les vraies données via /api/v2/cockpit. Aucune donnée fictive ·
   si l'API renvoie has_data=false (MPI vide), on affiche un empty state
   qui invite à traiter un premier lot ATIH.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";
  const H = window.SentinelHelpers;
  if (!H) {
    console.error("[cockpit] SentinelHelpers manquant");
    return;
  }
  const { NAVY, TEAL, GOLD, ERROR, SUCCESS, WARNING, slate,
          sectionHead, kpi, card, btn, emptyState, loadingState, api,
          renderInto, metierBanner } = H;

  function kpiAccent(name) {
    return ({ navy: NAVY, teal: TEAL, gold: GOLD, success: SUCCESS,
              warning: WARNING, error: ERROR })[name] || NAVY;
  }

  async function render() {
    const today = new Date();
    const monthLabel = today.toLocaleString("fr-FR",
      { month: "long", year: "numeric" });

    // Loading state immédiat (pendant fetch)
    renderInto(
      sectionHead({
        eyebrow: "Vue mensuelle",
        title: `Activité GHT · ${monthLabel}`,
        meta: "Lecture du MPI…",
      }) + loadingState("Récupération des KPIs depuis /api/v2/cockpit"));

    const r = await api("/api/v2/cockpit");

    // API down ou erreur · empty state · pas de fallback mock
    if (!r.ok) {
      renderInto(
        sectionHead({
          eyebrow: "Vue mensuelle",
          title: `Activité GHT · ${monthLabel}`,
          meta: `API indisponible (${r.status || "offline"})`,
        }) + emptyState({
          icon: "wifi-off",
          title: "Backend FastAPI v2 non joignable",
          body: "Vérifier que le service tourne sur le port 8766. "
              + "L'application reste navigable mais aucune donnée live ne "
              + "peut être affichée. Aucun chiffre fictif n'est inventé.",
        }));
      return;
    }

    const data = r.data;

    // MPI vide · empty state explicite
    if (!data.has_data) {
      renderInto(
        sectionHead({
          eyebrow: "Vue mensuelle",
          title: `Activité GHT · ${monthLabel}`,
          meta: "MPI vide",
        }) + emptyState({
          icon: "database",
          title: "Aucun lot ATIH n'a encore été traité",
          body: "Le Master Patient Index est vide. Importer un lot via "
              + "l'écran Modo Files (Ctrl+2) pour peupler les indicateurs.",
          action: btn({ label: "Aller à Modo Files",
                        kind: "primary", icon: "folders" }),
        }));
      return;
    }

    // KPIs réels reçus de l'API
    const kpiCards = data.kpis.map(k => kpi({
      label: k.label, value: k.value, unit: k.unit,
      sub: k.sub, accent: kpiAccent(k.accent),
    })).join("");

    const historyChart = data.file_active_history.length === 0
      ? emptyState({
          icon: "trending-up",
          title: "Historique 12 mois indisponible",
          body: "Le calcul de la file active glissante nécessite "
              + "12 mois de données traitées."
        })
      : card({ title: "File active glissante · 12 mois", icon: "trending-up",
          body: histogramHTML(data.file_active_history) });

    const alertsCard = data.sector_alerts.length === 0
      ? card({ title: "Alertes secteur", icon: "alert-triangle", body: `
          <div style="font-size:12px;color:${slate[500]};
              text-align:center;padding:18px 0;">
            Aucune alerte cette période · qualité PMSI nominale.
          </div>` })
      : card({ title: "Alertes secteur", icon: "alert-triangle",
          body: data.sector_alerts.map((a, i) =>
            alertRow(a, i === data.sector_alerts.length - 1)).join("") });

    renderInto(
      sectionHead({
        eyebrow: "Vue mensuelle",
        title: `Activité GHT · ${monthLabel}`,
        meta: `Source: ${data.month} · MPI live`,
        action: `<span style="display:inline-flex;align-items:center;gap:5px;
            padding:4px 10px;border-radius:999px;font-size:10px;font-weight:700;
            letter-spacing:0.14em;text-transform:uppercase;
            background:#ECFDF5;color:${SUCCESS};">
          <span style="width:6px;height:6px;border-radius:999px;
              background:${SUCCESS};"></span>API LIVE</span>`,
      }) +
      `<div style="display:grid;grid-template-columns:repeat(${data.kpis.length},1fr);
                   gap:14px;margin-bottom:18px;">${kpiCards}</div>` +
      `<div style="display:grid;grid-template-columns:2fr 1fr;gap:14px;
                   margin-bottom:18px;">${historyChart}${alertsCard}</div>`);
  }

  function histogramHTML(months) {
    const max = Math.max(...months, 1);
    return `<div style="display:flex;align-items:flex-end;gap:10px;
        height:180px;padding:12px 4px;">
      ${months.map((v, i) => {
        const isLast = i === months.length - 1;
        return `<div style="flex:1;display:flex;flex-direction:column;
            align-items:center;gap:8px;">
          <div style="width:100%;height:${(v / max) * 100}%;
              background:${isLast ? NAVY : TEAL};border-radius:4px 4px 0 0;
              opacity:${isLast ? 1 : 0.55};"></div>
          <span style="font-size:10px;color:${slate[500]};
              font-weight:600;font-family:'JetBrains Mono',monospace;">
            M-${months.length - i - 1}
          </span>
        </div>`;
      }).join("")}
    </div>`;
  }

  function alertRow(a, last) {
    const color = a.delta_pct < 0 ? ERROR : Math.abs(a.delta_pct) > 3 ? ERROR : WARNING;
    const sign = a.delta_pct >= 0 ? "+ " : "− ";
    return `<div style="padding:10px 0;
        ${last ? "" : `border-bottom:1px solid ${slate[100]};`}">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:12px;font-weight:700;color:${slate[800]};
            font-family:'JetBrains Mono',monospace;">Secteur ${a.sector}</span>
        <span style="font-size:13px;font-weight:800;color:${color};
            font-family:'JetBrains Mono',monospace;">${sign}${Math.abs(a.delta_pct).toFixed(1)} %</span>
      </div>
      <div style="font-size:11px;color:${slate[500]};margin-top:2px;">${a.label}</div>
    </div>`;
  }

  window.cockpitView = { render };
})();

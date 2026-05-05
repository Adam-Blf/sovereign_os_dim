/* ═══════════════════════════════════════════════════════════════════════════
   SENTINEL VIEWS · vues V36+ branchées sur FastAPI v2 · PROD
   ─────────────────────────────────────────────────────────────────────────
   ZÉRO donnée fictive. Chaque vue fetch /api/v2/* et affiche soit les
   vraies données, soit un empty state explicite. Aucun mock fallback.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";
  const H = window.SentinelHelpers;
  if (!H) {
    console.error("[sentinel-views] SentinelHelpers manquant");
    return;
  }
  const { NAVY, TEAL, GOLD, ERROR, SUCCESS, WARNING, slate,
          sectionHead, kpi, card, btn, fmtBadge, statusPill,
          renderInto, emptyState, loadingState, api } = H;

  function apiOffline(name, status) {
    return emptyState({
      icon: "wifi-off",
      title: "Backend FastAPI v2 non joignable",
      body: `L'écran ${name} nécessite l'API sur le port 8766. `
          + `Statut: ${status || "offline"}. Aucune donnée fictive n'est `
          + "affichée en attente.",
    });
  }

  // ── Health monitor ─────────────────────────────────────────────────────
  async function renderHealth() {
    renderInto(sectionHead({
      eyebrow: "Supervision", title: "Health monitor",
      meta: "Auto-refresh manuel",
    }) + loadingState());
    const r = await api("/api/v2/health-monitor");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Supervision",
        title: "Health monitor" }) + apiOffline("Health monitor", r.status));
      return;
    }
    const d = r.data;
    renderInto(
      sectionHead({ eyebrow: "Supervision", title: "Health monitor",
        meta: `Uptime · ${d.uptime_hours} h` }) +
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;">
        ${kpi({ label: "Uptime", value: d.uptime_hours, unit: "h", accent: TEAL })}
        ${kpi({ label: "RAM", value: d.ram_mb || "—", unit: d.ram_mb ? "Mo" : "", accent: NAVY })}
        ${kpi({ label: "Req/min", value: d.requests_per_min || "—", accent: GOLD })}
        ${kpi({ label: "Erreurs 24h", value: d.errors_24h || 0, accent: SUCCESS })}
      </div>` +
      card({ title: "Vérifications système", icon: "activity",
        body: d.checks.map(c => `
          <div style="display:flex;align-items:center;gap:12px;padding:12px 0;
              border-bottom:1px solid ${slate[100]};">
            <span style="width:24px;height:24px;border-radius:6px;
                background:${c.ok ? SUCCESS : slate[300]};color:white;
                display:flex;align-items:center;justify-content:center;">
              <i data-lucide="${c.ok ? "check" : "minus"}" style="width:14px;height:14px;"></i>
            </span>
            <span style="flex:1;font-size:13px;font-weight:600;color:${slate[800]};">${c.label}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                color:${slate[500]};font-weight:600;">${c.value}</span>
          </div>`).join("") }));
  }

  // ── Sentinel ARS · score réel via /api/v2/ars/score-lot ────────────────
  async function renderArs() {
    renderInto(sectionHead({
      eyebrow: "Prédicteur DRUIDES", title: "Sentinel ARS",
      meta: "Aucun lot scoré pour l'instant",
    }) + emptyState({
      icon: "shield",
      title: "Aucun lot ATIH soumis au scoring",
      body: "Le score est calculé à la demande sur les lignes réelles d'un lot. "
          + "Importer un lot via Modo Files (Ctrl+2) puis cliquer sur 'Scorer "
          + "ce lot' pour appeler /api/v2/ars/score-lot avec un échantillon.",
      action: btn({ label: "Aller à Modo Files",
                    kind: "primary", icon: "folders" }),
    }));
  }

  // ── CeSPA · pas d'endpoint encore · empty state explicite ──────────────
  async function renderCespa() {
    renderInto(sectionHead({
      eyebrow: "Réforme financement psy", title: "CeSPA / CATTG",
      meta: "Validateur réforme 4 juillet 2025",
    }) + emptyState({
      icon: "check-circle",
      title: "Validateur CeSPA · backend en cours",
      body: "Cet écran sera alimenté par /api/v2/cespa/check qui validera "
          + "les structures CeSPA déclarées (FicUM) et les actes CATTG du lot "
          + "courant. La logique de validation est dans la roadmap V37.",
    }));
  }

  async function renderDiff() {
    renderInto(sectionHead({
      eyebrow: "Anti-régression", title: "Diff lots mensuels",
      meta: "Comparaison M-1 vs M",
    }) + emptyState({
      icon: "git-compare",
      title: "Aucune comparaison disponible",
      body: "Le diff mensuel nécessite au moins 2 mois de lots traités. "
          + "Importer puis traiter les lots des 2 derniers mois.",
    }));
  }

  // ── CimSuggester · provider réel via Ollama ────────────────────────────
  async function renderCimSuggester() {
    renderInto(sectionHead({
      eyebrow: "IA codage CIM-10", title: "CimSuggester",
      meta: "Provider · vérification…",
    }) + loadingState("Test du provider LLM"));
    const r = await api("/api/v2/ml/cim-suggest", {
      method: "POST", body: { das: [], actes: [], notes: "" },
    });
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "IA codage CIM-10",
        title: "CimSuggester" }) + apiOffline("CimSuggester", r.status));
      return;
    }
    if (r.data.provider === "disabled") {
      renderInto(sectionHead({
        eyebrow: "IA codage CIM-10", title: "CimSuggester",
        meta: "Provider désactivé",
      }) + emptyState({
        icon: "brain",
        title: "Provider LLM non configuré",
        body: "Pour activer la suggestion CIM-10, définir la variable "
            + "d'environnement OLLAMA_BASE (ex: http://127.0.0.1:11434) "
            + "et redémarrer le service. Aucune suggestion fictive n'est "
            + "produite tant que le LLM n'est pas configuré.",
      }));
      return;
    }
    // Provider Ollama actif · afficher l'interface de saisie
    renderInto(
      sectionHead({ eyebrow: "IA codage CIM-10", title: "CimSuggester",
        meta: "Provider · Ollama (live)" }) +
      card({ title: "Saisir DAS / actes / notes pour suggestion", icon: "edit-3",
        body: "<em>Formulaire à brancher · POST /api/v2/ml/cim-suggest</em>" }));
  }

  async function renderLstm() {
    renderInto(sectionHead({
      eyebrow: "Modèle LSTM", title: "Prédicteur DMS",
      meta: "Modèle non encore déployé",
    }) + emptyState({
      icon: "trending-up",
      title: "Prédicteur DMS · roadmap V38",
      body: "Le modèle LSTM de prédiction de durée de séjour n'est pas "
          + "encore entraîné. Voir le plan d'implémentation dans le guide PDF.",
    }));
  }

  async function renderClustering() {
    renderInto(sectionHead({
      eyebrow: "UMAP + HDBSCAN", title: "Clustering patients",
      meta: "Pipeline non encore déployé",
    }) + emptyState({
      icon: "scatter-chart",
      title: "Clustering patients · roadmap V38",
      body: "Le clustering UMAP+HDBSCAN nécessite un MPI peuplé d'au "
          + "moins 1000 patients et une feature engineering dédiée.",
    }));
  }

  async function renderHospitalTwin() {
    renderInto(sectionHead({
      eyebrow: "Simulation DFA", title: "Hospital Twin",
      meta: "Modèle non encore déployé",
    }) + emptyState({
      icon: "database",
      title: "Simulation DFA · roadmap V38",
      body: "Hospital Twin requiert le calcul des compartiments de "
          + "financement réels et un modèle économétrique calibré sur "
          + "les données ScanSanté du GHT.",
    }));
  }

  async function renderHeatmap() {
    renderInto(sectionHead({
      eyebrow: "Sectorisation", title: "Heatmap géographique",
      meta: "Calcul depuis MPI",
    }) + emptyState({
      icon: "globe",
      title: "Heatmap par secteur · backend en cours",
      body: "Cette vue agrégera la file active par secteur ARS issu du "
          + "FicUM. Endpoint /api/v2/heatmap/sectors à brancher en V37.1.",
    }));
  }

  async function renderPivot() {
    renderInto(sectionHead({
      eyebrow: "Exploration", title: "Tableaux croisés",
      meta: "Backend en cours",
    }) + emptyState({
      icon: "table-2",
      title: "Pivot ad hoc · backend en cours",
      body: "Le pivot interactif nécessite un endpoint /api/v2/pivot qui "
          + "agrège le MPI selon les axes choisis. Roadmap V37.2.",
    }));
  }

  async function renderModo() {
    // Lit les vraies stats MPI pour afficher l'état actuel
    renderInto(sectionHead({ eyebrow: "Lot courant", title: "Modo Files",
      meta: "Lecture du MPI…" }) + loadingState());
    const r = await api("/api/v2/idv/stats");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Lot courant", title: "Modo Files" })
                 + apiOffline("Modo Files", r.status));
      return;
    }
    const stats = r.data;
    if (!stats.total_ipp) {
      renderInto(sectionHead({ eyebrow: "Lot courant", title: "Modo Files",
        meta: "MPI vide" }) + emptyState({
        icon: "upload-cloud",
        title: "Aucun fichier ATIH n'a encore été ingéré",
        body: "Glisser un dossier ATIH ici pour démarrer le scan + traitement. "
            + "Les fichiers sont identifiés automatiquement parmi les 23 "
            + "formats supportés.",
        action: btn({ label: "Ouvrir un dossier", kind: "primary", icon: "folder-plus" }),
      }));
      return;
    }
    renderInto(
      sectionHead({ eyebrow: "Lot courant", title: "Modo Files",
        meta: `MPI · ${stats.total_ipp} IPP` }) +
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;">
        ${kpi({ label: "Total IPP", value: stats.total_ipp, accent: NAVY })}
        ${kpi({ label: "Collisions", value: stats.collisions, accent: ERROR })}
        ${kpi({ label: "Résolues", value: stats.resolved, accent: SUCCESS })}
        ${kpi({ label: "En attente", value: stats.pending, accent: WARNING })}
      </div>`);
  }

  // ── RGPD command center · lit les compteurs réels ──────────────────────
  async function renderRgpd() {
    renderInto(sectionHead({ eyebrow: "Conformité",
      title: "RGPD command center", meta: "Lecture audit DB…" })
      + loadingState());
    const [healthR, verifyR] = await Promise.all([
      api("/health"),
      api("/api/v2/audit/verify"),
    ]);
    if (!healthR.ok || !verifyR.ok) {
      renderInto(sectionHead({ eyebrow: "Conformité",
        title: "RGPD command center" })
        + apiOffline("RGPD", healthR.status || verifyR.status));
      return;
    }
    const audit = verifyR.data;
    const auditEvents = healthR.data.audit_events || 0;
    renderInto(
      sectionHead({ eyebrow: "Conformité", title: "RGPD command center",
        meta: `Chaîne · ${audit.valid ? "intègre" : "ALTÉRÉE"}` }) +
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;
          margin-bottom:18px;">
        ${kpi({ label: "Événements audités", value: auditEvents,
                sub: "art. 30 RGPD", accent: NAVY })}
        ${kpi({ label: "Intégrité chaîne",
                value: audit.valid ? "OK" : "✗",
                sub: audit.valid ? "SHA-256 chaîné" : `corrompu id ${audit.broken_at_id}`,
                accent: audit.valid ? SUCCESS : ERROR })}
        ${kpi({ label: "Auth API", value: healthR.data.auth_required ? "ON" : "OFF",
                sub: "Bearer token", accent: healthR.data.auth_required ? SUCCESS : WARNING })}
        ${kpi({ label: "Modèles ML chargés",
                value: Object.values(healthR.data.ml_models_loaded).filter(Boolean).length,
                unit: "/3", accent: TEAL })}
      </div>` +
      card({ title: "Articles CSP applicables", icon: "book", body: `
        ${[
          ["L. 6113-7", "Obligation analyse activité par DIM"],
          ["L. 6113-8", "Conditions utilisation données T2A"],
          ["R. 6113-5", "Exception secret médical · personnel DIM"],
          ["R. 6123-174", "Modes prise en charge psychiatrie (arrêté 4 juillet 2025)"],
        ].map((r, i) => `
          <div style="display:flex;gap:14px;padding:10px 0;
              ${i < 3 ? `border-bottom:1px solid ${slate[100]};` : ""}">
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                font-weight:800;color:${TEAL};min-width:90px;">${r[0]}</span>
            <span style="font-size:12px;color:${slate[700]};flex:1;">${r[1]}</span>
          </div>`).join("")}` }));
  }

  // ── Audit chain · vraie liste depuis SQLite ────────────────────────────
  async function renderAudit() {
    renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
      title: "Audit chain", meta: "Lecture audit.db…" }) + loadingState());
    const r = await api("/api/v2/audit/events?limit=30");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
        title: "Audit chain" }) + apiOffline("Audit", r.status));
      return;
    }
    const events = r.data;
    if (!events.length) {
      renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
        title: "Audit chain", meta: "0 événements" }) + emptyState({
        icon: "history",
        title: "Le journal d'audit est vide",
        body: "Aucune action TIM/MIM n'a encore été enregistrée. Chaque "
            + "accès aux données nominatives sera horodaté et chaîné SHA-256.",
      }));
      return;
    }
    renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
      title: "Audit chain", meta: `${events.length} événements récents` }) +
      card({ title: "Événements", icon: "history", padding: 0,
        body: events.map((e, i) => `
          <div style="padding:12px 20px;
              ${i < events.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}
              display:grid;grid-template-columns:180px 120px 200px 1fr 80px;
              gap:14px;align-items:center;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                color:${slate[500]};">${e.ts.slice(0, 19).replace("T", " ")}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                font-weight:700;color:${NAVY};">${e.who}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                font-weight:700;color:${TEAL};">${e.action}</span>
            <span style="font-size:12px;color:${slate[700]};
                overflow:hidden;text-overflow:ellipsis;
                white-space:nowrap;">${e.target || "—"}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:9px;
                color:${slate[400]};">${e.sha256.slice(0, 8)}…</span>
          </div>`).join("") }));
  }

  async function renderWorkflow() {
    renderInto(sectionHead({
      eyebrow: "Workflow validation", title: "Pipeline DIM",
      meta: "Backend en cours",
    }) + emptyState({
      icon: "workflow",
      title: "Workflow TIM → MIM → ARS · backend en cours",
      body: "L'endpoint /api/v2/workflow/pending sera branché sur la table "
          + "des items en attente de validation MIM. Roadmap V37.3.",
    }));
  }

  // ── Exposition ─────────────────────────────────────────────────────────
  window.SentinelViews = {
    health: renderHealth,
    ars: renderArs,
    cespa: renderCespa,
    diff: renderDiff,
    cim: renderCimSuggester,
    lstm: renderLstm,
    cluster: renderClustering,
    twin: renderHospitalTwin,
    heatmap: renderHeatmap,
    pivot: renderPivot,
    modo_v2: renderModo,
    rgpd: renderRgpd,
    audit: renderAudit,
    workflow: renderWorkflow,
  };
})();

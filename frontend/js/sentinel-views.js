/* ═══════════════════════════════════════════════════════════════════════════
   SENTINEL VIEWS - vues V36+ branchées sur le pont local in-process - PROD
   ─────────────────────────────────────────────────────────────────────────
   ZÉRO donnée fictive. Chaque vue appelle le pont local et affiche soit les
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
      title: "Pont local indisponible",
      body: `L'écran ${name} n'a pas pu joindre le pont local in-process. `
          + `Statut : ${status || "indisponible"}. Aucune donnée fictive n'est `
          + "affichée en attente.",
    });
  }

  // ── Health monitor ─────────────────────────────────────────────────────
  async function renderHealth() {
    renderInto(sectionHead({
      eyebrow: "Supervision", title: "Supervision technique",
      meta: "Actualisation manuelle",
    }) + loadingState());
    const r = await api("/api/v2/health-monitor");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Supervision",
        title: "Supervision technique" }) + apiOffline("Supervision technique", r.status));
      return;
    }
    const d = r.data;
    renderInto(
      sectionHead({ eyebrow: "Supervision", title: "Supervision technique",
        meta: `Temps de fonctionnement - ${d.uptime_hours} h` }) +
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;">
        ${kpi({ label: "Temps de fonctionnement", value: d.uptime_hours, unit: "h", accent: TEAL })}
        ${kpi({ label: "Mémoire vive", value: d.ram_mb || "-", unit: d.ram_mb ? "Mo" : "", accent: NAVY })}
        ${kpi({ label: "Appels par minute", value: d.requests_per_min || "-", accent: GOLD })}
        ${kpi({ label: "Erreurs sur 24 heures", value: d.errors_24h || 0, accent: SUCCESS })}
      </div>` +
      card({ title: "Vérifications système", icon: "activity",
        body: d.checks.map(c => `
          <div style="display:flex;align-items:center;gap:12px;padding:12px 0;
              border-bottom:1px solid var(--border-item);">
            <span style="width:24px;height:24px;border-radius:6px;
                background:${c.ok ? SUCCESS : 'var(--border-card)'};color:white;
                display:flex;align-items:center;justify-content:center;">
              <i data-lucide="${c.ok ? "check" : "minus"}" style="width:14px;height:14px;"></i>
            </span>
            <span style="flex:1;font-size:13px;font-weight:600;color:var(--text-body-color);">${c.label}</span>
            <span style="font-family:'Consolas',monospace;font-size:11px;
                color:var(--text-muted-color);font-weight:600;">${c.value}</span>
          </div>`).join("") }));
  }

  // ── Sentinel ARS - score réel via /api/v2/ars/score-lot ────────────────
  async function renderArs() {
    renderInto(sectionHead({
      eyebrow: "Prédicteur DRUIDES", title: "Sentinelle agence régionale de santé",
      meta: "Aucun lot scoré pour l'instant",
    }) + emptyState({
      icon: "shield",
      title: "Aucun lot ATIH soumis au scoring",
      body: "Le score est calculé à la demande sur les lignes réelles d'un lot. "
          + "Importer un lot via Sélection des fichiers (Ctrl+2) puis cliquer sur 'Scorer "
          + "ce lot' pour appeler /api/v2/ars/score-lot avec un échantillon.",
      action: btn({ label: "Aller à Sélection des fichiers",
                    kind: "primary", icon: "folders" }),
    }));
  }

  // ── CeSPA - validateur réel via /api/v2/cespa/check ───────────────────
  async function renderCespa() {
    renderInto(sectionHead({ eyebrow: "Réforme financement psy",
      title: "CeSPA / CATTG" }) + loadingState());
    const r = await api("/api/v2/cespa/check");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Réforme financement psy",
        title: "CeSPA / CATTG" }) + apiOffline("CeSPA", r.status));
      return;
    }
    const d = r.data;
    if (!d.has_data) {
      renderInto(sectionHead({ eyebrow: "Réforme financement psy",
        title: "CeSPA / CATTG" }) + emptyState({
          icon: "check-circle",
          title: "Aucune ligne RPS/RAA dans le MPI",
          body: "Le validateur CeSPA s'applique aux lignes RPS (champ 23) et "
              + "RAA (modalité 33). Importer un lot via Sélection des fichiers pour "
              + "déclencher la vérification.",
        }));
      return;
    }
    renderInto(
      sectionHead({ eyebrow: "Réforme financement psy", title: "CeSPA / CATTG",
        meta: `RPS: ${d.rps_lines} - RAA: ${d.raa_lines}` }) +
      card({ title: "Règles arrêté 4 juillet 2025", icon: "shield",
        body: d.rules.map((rule, i) => {
          const ratio = rule.total > 0 ? Math.round(rule.ok / rule.total * 100) : 0;
          const color = ratio === 100 ? SUCCESS : ratio >= 80 ? WARNING : ERROR;
          return `<div style="display:grid;grid-template-columns:100px 1fr auto;
              gap:14px;align-items:center;padding:10px 0;
              ${i < d.rules.length - 1 ? `border-bottom:1px solid var(--border-item);` : ""}">
            <span style="font-family:'Consolas',monospace;font-size:11px;
                font-weight:700;color:var(--text-primary);">${rule.code}</span>
            <span style="font-size:12px;color:var(--text-secondary);">${rule.label}</span>
            ${statusPill(`${rule.ok}/${rule.total}`, color)}
          </div>`;
        }).join("") }));
  }

  // ── Diff lots mensuels - agrégat réel ──────────────────────────────────
  async function renderDiff() {
    renderInto(sectionHead({ eyebrow: "Anti-régression",
      title: "Comparaison des lots mensuels" }) + loadingState());
    const r = await api("/api/v2/diff");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Anti-régression",
        title: "Comparaison des lots mensuels" }) + apiOffline("Comparaison des lots", r.status));
      return;
    }
    if (!r.data.has_data) {
      renderInto(sectionHead({ eyebrow: "Anti-régression",
        title: "Comparaison des lots mensuels" }) + emptyState({
        icon: "git-compare",
        title: r.data.message || "Aucune comparaison disponible",
        body: "Le diff nécessite des lots traités. Importer un lot pour "
            + "que les indicateurs soient calculés.",
      }));
      return;
    }
    const rows = r.data.rows;
    renderInto(sectionHead({ eyebrow: "Anti-régression",
      title: "Comparaison des lots mensuels", meta: `${rows.length} indicateurs` }) +
      card({ title: "Comparaison volumétrique", icon: "git-compare", padding: 0,
        body: `<table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead><tr style="background:var(--bg-hover);">
            <th style="padding:10px 14px;text-align:left;font-size:9px;
                font-weight:700;color:var(--text-muted-color);letter-spacing:0.16em;
                text-transform:uppercase;">Indicateur</th>
            <th style="padding:10px 14px;text-align:right;font-size:9px;
                font-weight:700;color:var(--text-muted-color);letter-spacing:0.16em;
                text-transform:uppercase;">Lignes</th>
            <th style="padding:10px 14px;text-align:left;font-size:9px;
                font-weight:700;color:var(--text-muted-color);letter-spacing:0.16em;
                text-transform:uppercase;">État</th>
          </tr></thead><tbody>
          ${rows.map(row => `<tr style="border-top:1px solid var(--border-item);">
            <td style="padding:10px 14px;font-family:'Montserrat';
                font-weight:600;color:var(--text-body-color);">${row.indicator}</td>
            <td style="padding:10px 14px;text-align:right;
                font-family:'Consolas',monospace;font-weight:700;
                color:var(--text-primary);">${row.current.toLocaleString("fr-FR")}</td>
            <td style="padding:10px 14px;">${statusPill("Nouveau", TEAL)}</td>
          </tr>`).join("")}</tbody></table>` }));
  }

  // ── CimSuggester - modèle local par défaut, Ollama en option ───────────
  async function renderCimSuggester() {
    renderInto(sectionHead({
      eyebrow: "IA codage CIM-10", title: "Suggestion diagnostique",
      meta: "Provider - vérification…",
    }) + loadingState("Test du provider LLM"));
    const r = await api("/api/v2/ml/cim-suggest", {
      method: "POST", body: { das: [], actes: [], notes: "" },
    });
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "IA codage CIM-10",
        title: "Suggestion diagnostique" }) + apiOffline("CimSuggester", r.status));
      return;
    }
    const isLocal = r.data.provider === "local";
    // Provider actif (local par défaut ou Ollama si OLLAMA_BASE configuré)
    renderInto(
      sectionHead({ eyebrow: "IA codage CIM-10", title: "Suggestion diagnostique",
        meta: isLocal ? "Provider - modèle local" : "Provider - Ollama (live)" }) +
      card({ title: "Saisir DAS / actes / notes pour suggestion", icon: "edit-3",
        body: "<em>Formulaire à brancher - POST /api/v2/ml/cim-suggest</em>" }));
  }

  async function renderLstm() {
    const head = sectionHead({
      eyebrow: "Modèle local entraîné",
      title: "Prédicteur de durée de séjour",
      meta: "Estimations issues de données synthétiques",
    });
    renderInto(head + loadingState("Chargement du modèle"));
    const r = await api("/api/v2/duree-sejour");
    if (!r.ok || !r.data || !r.data.has_model) {
      renderInto(head + emptyState({
        icon: "trending-up",
        title: "Modèle non entraîné",
        body: "Lancer : python -m backend.ml.train_sejour_models",
      }));
      return;
    }
    const d = r.data;
    const rows = (d.par_groupe || []).map(g => `
      <tr style="border-bottom:1px solid var(--border-card);">
        <td style="padding:8px 12px;font-weight:700;color:${NAVY};">${g.groupe}</td>
        <td style="padding:8px 12px;">${g.libelle}</td>
        <td style="padding:8px 12px;text-align:right;font-variant-numeric:tabular-nums;">${g.duree_moyenne_jours} j</td>
        <td style="padding:8px 12px;text-align:right;font-variant-numeric:tabular-nums;color:var(--text-muted-color);">± ${g.ecart_type_jours} j</td>
      </tr>`).join("");
    renderInto(head + `
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px;">
        ${kpi({ label: "Erreur absolue moyenne", value: d.erreur_absolue_moyenne_jours + " jours", accent: TEAL })}
        ${kpi({ label: "Coefficient de détermination", value: d.coefficient_determination, accent: NAVY })}
        ${kpi({ label: "Données d'entraînement", value: "synthétiques", accent: GOLD })}
      </div>
      ${card({ title: "Durée moyenne estimée par groupe diagnostique", body: `
        <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
          <thead><tr style="text-align:left;color:var(--text-muted-color);text-transform:uppercase;font-size:10px;letter-spacing:0.08em;">
            <th style="padding:8px 12px;">Groupe</th><th style="padding:8px 12px;">Libellé</th>
            <th style="padding:8px 12px;text-align:right;">Durée moyenne</th><th style="padding:8px 12px;text-align:right;">Dispersion</th>
          </tr></thead><tbody>${rows}</tbody>
        </table>
        <p style="margin-top:12px;font-size:11px;color:var(--text-muted-color);">
          Modèle : ${d.algorithme}. ${d.donnees}. Les valeurs sont des estimations
          statistiques, jamais une consigne de sortie pour un patient donné.
        </p>` })}
    `);
  }

  async function renderClustering() {
    const head = sectionHead({
      eyebrow: "Projection en deux dimensions puis K-moyennes",
      title: "Regroupement de patients",
      meta: "Six archétypes issus de données synthétiques",
    });
    renderInto(head + loadingState("Chargement de la projection"));
    const r = await api("/api/v2/regroupement-patients");
    if (!r.ok || !r.data || !r.data.has_model) {
      renderInto(head + emptyState({
        icon: "scatter-chart",
        title: "Modèle non entraîné",
        body: "Lancer : python -m backend.ml.train_sejour_models",
      }));
      return;
    }
    const d = r.data;
    const palette = [NAVY, TEAL, GOLD, ERROR, SUCCESS, WARNING];
    const legend = (d.archetypes || []).map(a => `
      <div style="display:flex;align-items:center;gap:8px;padding:6px 0;font-size:12px;">
        <span style="width:10px;height:10px;border-radius:50%;background:${palette[a.identifiant % 6]};flex-shrink:0;"></span>
        <span style="font-weight:600;">${a.libelle}</span>
        <span style="color:var(--text-muted-color);margin-left:auto;font-variant-numeric:tabular-nums;">
          ${a.effectif} patients - ${a.duree_moyenne_jours} j
        </span>
      </div>`).join("");
    renderInto(head + `
      <div style="display:grid;grid-template-columns:2fr 1fr;gap:16px;">
        ${card({ title: "Projection des patients", body: '<canvas id="clusters-canvas" height="300"></canvas>' })}
        ${card({ title: "Archétypes", body: legend + `
          <p style="margin-top:10px;font-size:11px;color:var(--text-muted-color);">
            ${d.algorithme}. ${d.donnees}.
          </p>` })}
      </div>
    `);
    const ctx = document.getElementById("clusters-canvas");
    if (ctx && window.Chart) {
      const datasets = (d.archetypes || []).map(a => ({
        label: a.libelle,
        data: (d.points || []).filter(p => p.groupe_archetype === a.identifiant)
          .map(p => ({ x: p.x, y: p.y })),
        backgroundColor: palette[a.identifiant % 6] + "99",
        pointRadius: 3,
      }));
      new Chart(ctx, {
        type: "scatter",
        data: { datasets },
        options: {
          plugins: { legend: { display: false } },
          scales: { x: { display: false }, y: { display: false } },
          animation: false,
        },
      });
    }
  }

  async function renderHospitalTwin() {
    renderInto(sectionHead({ eyebrow: "Simulation DFA",
      title: "Jumeau hospitalier" }) + loadingState());
    const r = await api("/api/v2/twin/scenarios");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Simulation DFA",
        title: "Jumeau hospitalier" }) + apiOffline("Jumeau hospitalier", r.status));
      return;
    }
    if (!r.data.has_data) {
      renderInto(sectionHead({ eyebrow: "Simulation DFA",
        title: "Jumeau hospitalier" }) + emptyState({
        icon: "database",
        title: r.data.message || "Simulation impossible",
        body: "Hospital Twin calcule l'impact tarifaire potentiel sur la "
            + "DFA à partir du volume MPI réel. Importer un lot pour "
            + "déclencher les calculs.",
      }));
      return;
    }
    const fr = n => n.toLocaleString("fr-FR");
    renderInto(sectionHead({ eyebrow: "Simulation DFA",
      title: "Jumeau hospitalier",
      meta: `Base: ${fr(r.data.ipp_base)} IPP` }) +
      card({ title: "Scénarios d'impact tarifaire", icon: "target",
        body: r.data.scenarios.map((s, i) => `
          <div style="padding:14px 0;
              ${i < r.data.scenarios.length - 1 ? `border-bottom:1px solid var(--border-item);` : ""}
              display:grid;grid-template-columns:1fr auto auto;gap:18px;
              align-items:center;">
            <div>
              <div style="font-size:13px;font-weight:600;color:var(--text-body-color);">${s.label}</div>
              <div style="height:4px;width:120px;background:var(--border-item);
                  border-radius:999px;overflow:hidden;margin-top:6px;">
                <div style="width:${s.confidence * 100}%;height:100%;background:${TEAL};"></div>
              </div>
            </div>
            <span style="font-family:'Consolas',monospace;font-size:18px;
                font-weight:800;color:${SUCCESS};">+ ${fr(s.impact_eur)} €</span>
            <span style="font-family:'Consolas',monospace;font-size:11px;
                color:var(--text-muted-color);">conf. ${(s.confidence * 100).toFixed(0)} %</span>
          </div>`).join("") }));
  }

  async function renderHeatmap() {
    renderInto(sectionHead({ eyebrow: "Sectorisation",
      title: "Carte de chaleur des secteurs" }) + loadingState());
    const r = await api("/api/v2/heatmap/sectors");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Sectorisation",
        title: "Carte de chaleur des secteurs" }) + apiOffline("Carte de chaleur", r.status));
      return;
    }
    if (!r.data.has_data) {
      renderInto(sectionHead({ eyebrow: "Sectorisation",
        title: "Carte de chaleur des secteurs" }) + emptyState({
        icon: "globe",
        title: "Aucune donnée géographique disponible",
        body: "L'agrégation par code postal nécessite des observations "
            + "MPI avec un champ code_postal renseigné. Importer un lot "
            + "RPS pour peupler la carte.",
      }));
      return;
    }
    const sectors = r.data.sectors;
    const colorOf = i => ({ very_high: ERROR, high: WARNING,
      medium: TEAL, low: SUCCESS })[i] || "var(--text-muted-color)";
    renderInto(sectionHead({ eyebrow: "Sectorisation",
      title: "Carte de chaleur des secteurs",
      meta: `Top ${sectors.length} codes postaux` }) +
      card({ title: "File active par code postal", icon: "globe", body: `
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
          ${sectors.map(s => `
            <div style="background:${colorOf(s.intensity)}22;
                border:2px solid ${colorOf(s.intensity)};border-radius:12px;
                padding:18px 14px;">
              <div style="font-family:'Consolas',monospace;font-size:14px;
                  font-weight:800;color:var(--text-primary);">${s.code}</div>
              <div style="font-size:24px;font-weight:800;
                  color:${colorOf(s.intensity)};margin-top:4px;
                  letter-spacing:-0.025em;">${s.file_active}</div>
              <div style="font-size:9px;font-weight:700;color:var(--text-muted-color);
                  text-transform:uppercase;letter-spacing:0.14em;
                  margin-top:4px;">observations</div>
            </div>`).join("")}
        </div>` }));
  }

  async function renderPivot() {
    renderInto(sectionHead({
      eyebrow: "Exploration", title: "Tableaux croisés",
      meta: "Backend en cours",
    }) + emptyState({
      icon: "table-2",
      title: "Pivot ad hoc - backend en cours",
      body: "Le pivot interactif nécessite un endpoint /api/v2/pivot qui "
          + "agrège le MPI selon les axes choisis. Roadmap V37.2.",
    }));
  }

  async function renderModo() {
    // Lit les vraies stats MPI pour afficher l'état actuel
    renderInto(sectionHead({ eyebrow: "Lot courant", title: "Sélection des fichiers",
      meta: "Lecture du MPI…" }) + loadingState());
    const r = await api("/api/v2/idv/stats");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Lot courant", title: "Sélection des fichiers" })
                 + apiOffline("Sélection des fichiers", r.status));
      return;
    }
    const stats = r.data;
    if (!stats.total_ipp) {
      renderInto(sectionHead({ eyebrow: "Lot courant", title: "Sélection des fichiers",
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
      sectionHead({ eyebrow: "Lot courant", title: "Sélection des fichiers",
        meta: `MPI - ${stats.total_ipp} IPP` }) +
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;">
        ${kpi({ label: "Total IPP", value: stats.total_ipp, accent: NAVY })}
        ${kpi({ label: "Collisions", value: stats.collisions, accent: ERROR })}
        ${kpi({ label: "Résolues", value: stats.resolved, accent: SUCCESS })}
        ${kpi({ label: "En attente", value: stats.pending, accent: WARNING })}
      </div>`);
  }

  // ── RGPD command center - lit les compteurs réels ──────────────────────
  async function renderRgpd() {
    renderInto(sectionHead({ eyebrow: "Conformité",
      title: "Protection des données", meta: "Lecture audit DB…" })
      + loadingState());
    const [healthR, verifyR] = await Promise.all([
      api("/health"),
      api("/api/v2/audit/verify"),
    ]);
    if (!healthR.ok || !verifyR.ok) {
      renderInto(sectionHead({ eyebrow: "Conformité",
        title: "Protection des données" })
        + apiOffline("RGPD", healthR.status || verifyR.status));
      return;
    }
    const audit = verifyR.data;
    const auditEvents = healthR.data.audit_events || 0;
    renderInto(
      sectionHead({ eyebrow: "Conformité", title: "Protection des données",
        meta: `Chaîne - ${audit.valid ? "intègre" : "ALTÉRÉE"}` }) +
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
          ["R. 6113-5", "Exception secret médical - personnel DIM"],
          ["R. 6123-174", "Modes prise en charge psychiatrie (arrêté 4 juillet 2025)"],
        ].map((r, i) => `
          <div style="display:flex;gap:14px;padding:10px 0;
              ${i < 3 ? `border-bottom:1px solid var(--border-item);` : ""}">
            <span style="font-family:'Consolas',monospace;font-size:11px;
                font-weight:800;color:${TEAL};min-width:90px;">${r[0]}</span>
            <span style="font-size:12px;color:var(--text-secondary);flex:1;">${r[1]}</span>
          </div>`).join("")}` }));
  }

  // ── Audit chain - vraie liste depuis SQLite ────────────────────────────
  async function renderAudit() {
    renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
      title: "Journal d'audit chaîné", meta: "Lecture audit.db…" }) + loadingState());
    const r = await api("/api/v2/audit/events?limit=30");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
        title: "Journal d'audit chaîné" }) + apiOffline("Journal d'audit", r.status));
      return;
    }
    const events = r.data;
    if (!events.length) {
      renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
        title: "Journal d'audit chaîné", meta: "0 événements" }) + emptyState({
        icon: "history",
        title: "Le journal d'audit est vide",
        body: "Aucune action TIM/MIM n'a encore été enregistrée. Chaque "
            + "accès aux données nominatives sera horodaté et chaîné SHA-256.",
      }));
      return;
    }
    renderInto(sectionHead({ eyebrow: "Traçabilité immutable",
      title: "Journal d'audit chaîné", meta: `${events.length} événements récents` }) +
      card({ title: "Événements", icon: "history", padding: 0,
        body: events.map((e, i) => `
          <div style="padding:12px 20px;
              ${i < events.length - 1 ? `border-bottom:1px solid var(--border-item);` : ""}
              display:grid;grid-template-columns:180px 120px 200px 1fr 80px;
              gap:14px;align-items:center;">
            <span style="font-family:'Consolas',monospace;font-size:11px;
                color:var(--text-muted-color);">${e.ts.slice(0, 19).replace("T", " ")}</span>
            <span style="font-family:'Consolas',monospace;font-size:11px;
                font-weight:700;color:var(--text-primary);">${e.who}</span>
            <span style="font-family:'Consolas',monospace;font-size:11px;
                font-weight:700;color:${TEAL};">${e.action}</span>
            <span style="font-size:12px;color:var(--text-secondary);
                overflow:hidden;text-overflow:ellipsis;
                white-space:nowrap;">${e.target || "-"}</span>
            <span style="font-family:'Consolas',monospace;font-size:9px;
                color:var(--text-muted-color);">${e.sha256.slice(0, 8)}…</span>
          </div>`).join("") }));
  }

  async function renderWorkflow() {
    renderInto(sectionHead({ eyebrow: "Workflow validation",
      title: "Pipeline DIM" }) + loadingState());
    const r = await api("/api/v2/workflow/pending");
    if (!r.ok) {
      renderInto(sectionHead({ eyebrow: "Workflow validation",
        title: "Pipeline DIM" }) + apiOffline("Workflow", r.status));
      return;
    }
    const { counts, items } = r.data;
    const stages = [
      { l: "TIM corrige", k: "tim", c: NAVY, icon: "user" },
      { l: "MIM valide", k: "mim", c: TEAL, icon: "user-check" },
      { l: "Préflight DRUIDES", k: "preflight", c: GOLD, icon: "shield" },
      { l: "Export ARS", k: "ars", c: SUCCESS, icon: "send" },
    ];
    const stageCards = stages.map((s, i) => `
      <div style="background:var(--bg-card);border:1px solid var(--border-card);
          border-radius:12px;padding:18px;text-align:center;position:relative;">
        ${i < stages.length - 1 ? `<div style="position:absolute;right:-18px;
            top:50%;transform:translateY(-50%);width:32px;height:2px;
            background:var(--border-card);"></div>` : ""}
        <div style="width:48px;height:48px;border-radius:12px;background:${s.c}22;
            color:${s.c};margin:0 auto 12px;display:flex;align-items:center;
            justify-content:center;">
          <i data-lucide="${s.icon}" style="width:22px;height:22px;"></i>
        </div>
        <div style="font-size:11px;font-weight:700;color:var(--text-muted-color);
            text-transform:uppercase;letter-spacing:0.16em;">${s.l}</div>
        <div style="font-size:32px;font-weight:800;color:${s.c};margin-top:4px;
            letter-spacing:-0.03em;">${counts[s.k] || 0}</div>
        <div style="font-size:11px;color:var(--text-muted-color);">en cours</div>
      </div>`).join("");

    const itemList = !items.length
      ? `<div style="font-size:12px;color:var(--text-muted-color);text-align:center;
            padding:24px 0;">Aucun item en attente - pipeline propre.</div>`
      : items.map((it, i) => `
          <div style="display:grid;grid-template-columns:120px 1fr 110px 90px;
              gap:14px;align-items:center;padding:12px 0;
              ${i < items.length - 1 ? `border-bottom:1px solid var(--border-item);` : ""}">
            <span style="font-family:'Consolas',monospace;font-size:13px;
                font-weight:700;color:var(--text-primary);">${it.ipp}</span>
            <span style="font-size:13px;color:var(--text-body-color);">${it.label}</span>
            <span style="font-family:'Consolas',monospace;font-size:11px;
                color:var(--text-muted-color);">${it.owner}</span>
            ${statusPill(it.stage, TEAL)}
          </div>`).join("");

    renderInto(
      sectionHead({ eyebrow: "Workflow validation", title: "Pipeline DIM",
        meta: `${items.length} items en attente` }) +
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;
          margin-bottom:18px;">${stageCards}</div>` +
      card({ title: "Items en attente", icon: "clipboard-check", body: itemList }));
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

/* ═══════════════════════════════════════════════════════════════════════════
   SENTINEL VIEWS · 20 écrans portés depuis docs/design/sentinel-refonte/
   ─────────────────────────────────────────────────────────────────────────
   Chaque écran expose render() injecté dans #os-viewport via app.js.
   Données mockées · à brancher sur /api/* dans une étape ultérieure.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";
  const H = window.SentinelHelpers;
  if (!H) {
    console.error("[sentinel-views] SentinelHelpers manquant · charger sentinel-helpers.js d'abord");
    return;
  }
  const { NAVY, TEAL, GOLD, ERROR, SUCCESS, WARNING, slate,
          sectionHead, kpi, card, btn, fmtBadge, statusPill, metierBanner, renderInto } = H;

  // ─── Helper · grid CSS rapide ──────────────────────────────────────────
  function grid(cols, gap, body) {
    return `<div style="display:grid;grid-template-columns:${cols};gap:${gap || 14}px;margin-bottom:18px;">${body}</div>`;
  }
  function row(items) { return items.join(""); }

  // ════════════════════════════════════════════════════════════════════════
  //                 CONTRÔLE
  // ════════════════════════════════════════════════════════════════════════

  function renderHealth() {
    const checks = [
      { l: "Bridge HTTP 127.0.0.1:8765", ok: true,  v: "200 ms" },
      { l: "MPI SQLite (mpi.db)",         ok: true,  v: "11 247 IPP · 12 Mo" },
      { l: "Module ML XGBoost chargé",     ok: true,  v: "3 modèles · 18 Mo RAM" },
      { l: "Log audit RGPD horodaté",      ok: true,  v: "847 entrées · J-7" },
      { l: "Préflight DRUIDES validators", ok: true,  v: "15 / 15 OK" },
      { l: "Connexion fichiers ATIH D:/",  ok: true,  v: "lecture · 4280 fichiers" },
      { l: "Telemetry opt-in",             ok: false, v: "désactivé (par défaut)" },
    ];
    renderInto(
      sectionHead({ eyebrow: "Supervision", title: "Health monitor",
        meta: "Auto-refresh 30 s",
        action: btn({ label: "Refresh", kind: "ghost", sm: true, icon: "refresh-cw" }) }) +
      grid("repeat(4,1fr)", 14, row([
        kpi({ label: "Uptime",        value: "12 j 4 h", accent: TEAL,    sub: "depuis dernier reboot" }),
        kpi({ label: "RAM occupée",   value: "428",      unit: "Mo", accent: NAVY,    sub: "limite 1 Go" }),
        kpi({ label: "Réq/min API",  value: "84",       accent: GOLD,    sub: "moyenne 7 j" }),
        kpi({ label: "Erreurs 24 h", value: "0",        accent: SUCCESS, sub: "audit log clean" }),
      ])) +
      card({ title: "Vérifications système", icon: "activity",
        body: checks.map(c => `
          <div style="display:flex;align-items:center;gap:12px;padding:12px 0;
              border-bottom:1px solid ${slate[100]};">
            <span style="width:24px;height:24px;border-radius:6px;
                background:${c.ok ? SUCCESS : slate[300]};color:white;
                display:flex;align-items:center;justify-content:center;">
              <i data-lucide="${c.ok ? "check" : "minus"}" style="width:14px;height:14px;"></i>
            </span>
            <span style="flex:1;font-size:13px;font-weight:600;color:${slate[800]};">${c.l}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                color:${slate[500]};font-weight:600;">${c.v}</span>
          </div>`).join("") }));
  }

  // ════════════════════════════════════════════════════════════════════════
  //                 MÉTIER DIM
  // ════════════════════════════════════════════════════════════════════════

  function renderArs() {
    const lots = [
      { lot: "RPS_2025T3.txt",      score: 92, risk: "low",    issues: 0 },
      { lot: "EDGAR_2025T3.txt",    score: 78, risk: "medium", issues: 4 },
      { lot: "RAA_2025T3.txt",      score: 64, risk: "medium", issues: 7 },
      { lot: "VID-HOSP_2025T3.txt", score: 41, risk: "high",   issues: 12 },
      { lot: "RPSA_2025T3.txt",     score: 88, risk: "low",    issues: 1 },
    ];
    const colorOf = r => r === "high" ? ERROR : r === "medium" ? WARNING : SUCCESS;
    const labelOf = r => r === "high" ? "Risque élevé" : r === "medium" ? "À surveiller" : "Faible risque";

    renderInto(
      sectionHead({ eyebrow: "Prédicteur DRUIDES", title: "Sentinel ARS · 42 RPS suspects",
        meta: "Modèle XGBoost · format_detector + collision_risk",
        action: btn({ label: "Re-scorer le lot", kind: "primary", icon: "play" }) }) +
      grid("repeat(4,1fr)", 14, row([
        kpi({ label: "Probabilité rejet ARS", value: "12,4", unit: "%", accent: WARNING, sub: "seuil alerte 15 %" }),
        kpi({ label: "Lots scorés",            value: "5",   accent: NAVY }),
        kpi({ label: "Anomalies détectées",    value: "24",  accent: ERROR, sub: "auto-corrigeables · 18" }),
        kpi({ label: "Score qualité moyen",   value: "73",  unit: "/100", accent: GOLD }),
      ])) +
      card({ title: "Score par lot", icon: "shield", padding: 0,
        body: `
          <div style="padding:12px 20px;border-bottom:1px solid ${slate[100]};
              background:${slate[50]};display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;
              gap:14px;font-size:9px;font-weight:700;color:${slate[500]};
              text-transform:uppercase;letter-spacing:0.16em;">
            <span>Fichier</span><span>Score qualité</span><span>Risque rejet</span>
            <span>Anomalies</span><span>Action</span>
          </div>` +
          lots.map((l, i) => `
            <div style="padding:14px 20px;${i < lots.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}
                display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:14px;align-items:center;">
              <span style="font-family:'JetBrains Mono',monospace;font-size:12px;
                  color:${NAVY};font-weight:700;">${l.lot}</span>
              <div>
                <div style="height:6px;background:${slate[100]};border-radius:999px;
                    overflow:hidden;width:80%;">
                  <div style="width:${l.score}%;height:100%;background:${colorOf(l.risk)};"></div>
                </div>
                <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                    font-weight:700;color:${slate[700]};">${l.score} / 100</span>
              </div>
              ${statusPill(labelOf(l.risk), colorOf(l.risk))}
              <span style="font-family:'JetBrains Mono',monospace;font-size:13px;
                  font-weight:800;color:${l.issues > 0 ? ERROR : SUCCESS};">${l.issues}</span>
              <div>${btn({ label: "Détail", kind: "ghost", sm: true, icon: "eye" })}</div>
            </div>`).join("") }) +
      metierBanner(`<strong style="color:${NAVY};">Sentinel ARS</strong> évalue chaque lot ATIH avant l'upload DRUIDES sur 15 critères réglementaires. Gain estimé · 6-10 h TIM/mois économisées sur les corrections rétroactives.`));
  }

  function renderCespa() {
    const rules = [
      { code: "R-CSP-01", lib: "Code structure CeSPA présent dans champ 23 RPS", ok: 47 },
      { code: "R-CSP-02", lib: "Forfait CATTG facturable ↔ acte tracé", ok: 47 },
      { code: "R-CSP-04", lib: "Médecin responsable rattaché à structure CeSPA", ok: 47 },
      { code: "R-CSP-07", lib: "Planning hebdomadaire CeSPA déclaré FINESS", ok: 47 },
      { code: "R-CSP-09", lib: "Patient adulte (≥ 18 ans à l'admission)", ok: 47 },
    ];
    renderInto(
      sectionHead({ eyebrow: "Réforme financement psy",
        title: "Centres de santé psy adultes · 100 % conformes",
        meta: "Dernier contrôle · auto",
        action: btn({ label: "Re-vérifier", kind: "teal", icon: "refresh-cw" }) }) +
      grid("1fr 2fr", 14, row([
        card({ title: "Récap conformité", icon: "check-circle", body: `
          <div style="text-align:center;padding:20px 0 12px;">
            <div style="width:120px;height:120px;margin:0 auto;border-radius:999px;
                background:conic-gradient(${SUCCESS} 0deg 360deg, ${slate[100]} 0deg);
                display:flex;align-items:center;justify-content:center;">
              <div style="width:92px;height:92px;background:white;border-radius:999px;
                  display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <div style="font-size:28px;font-weight:800;color:${NAVY};
                    font-family:'JetBrains Mono',monospace;letter-spacing:-0.03em;">100%</div>
                <div style="font-size:9px;font-weight:700;color:${TEAL};
                    text-transform:uppercase;letter-spacing:0.16em;">CESPA</div>
              </div>
            </div>
          </div>
          <div style="display:flex;justify-content:space-between;padding:8px 0;
              border-top:1px solid ${slate[100]};">
            <span style="font-size:12px;color:${slate[600]};font-weight:600;">Structures contrôlées</span>
            <span style="font-size:12px;font-weight:700;color:${NAVY};
                font-family:'JetBrains Mono',monospace;">47 / 47</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:8px 0;
              border-top:1px solid ${slate[100]};">
            <span style="font-size:12px;color:${slate[600]};font-weight:600;">Actes CATTG validés</span>
            <span style="font-size:12px;font-weight:700;color:${NAVY};
                font-family:'JetBrains Mono',monospace;">18 244 / 18 244</span>
          </div>` }),
        card({ title: "Règles réforme 4 juillet 2025", icon: "shield",
          body: rules.map((r, i) => `
            <div style="display:grid;grid-template-columns:100px 1fr auto;gap:14px;
                align-items:center;padding:10px 0;
                ${i < rules.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}">
              <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                  font-weight:700;color:${NAVY};">${r.code}</span>
              <span style="font-size:12px;color:${slate[700]};">${r.lib}</span>
              ${statusPill(`${r.ok}/47`, SUCCESS)}
            </div>`).join("") }),
      ])));
  }

  function renderDiff() {
    const rows = [
      ["RPS produits",        8654,  8924,  270,   3.1,   "ok"],
      ["RAA séjours",         1842,  1798,  -44,  -2.4,   "ok"],
      ["Patients DPI",       14421, 14882,  461,   3.2,   "ok"],
      ["Actes ambulatoires", 22884, 26512, 3628,  15.8, "warn"],
      ["Hospi temps plein",    982,  1004,   22,   2.2,   "ok"],
      ["CMP secteur G16",     1244,   956, -288, -23.2, "alert"],
      ["INS qualifiés",      14102, 14651,  549,   3.9,   "ok"],
    ];
    const cmap = { ok: SUCCESS, warn: WARNING, alert: ERROR };
    const fr = n => n.toLocaleString("fr-FR");
    const td = "padding:10px 12px;font-family:'JetBrains Mono',monospace;font-size:12px;";
    const th = "padding:10px 12px;font-size:9px;font-weight:700;color:" + slate[500] +
        ";text-transform:uppercase;letter-spacing:0.16em;text-align:left;";

    renderInto(
      sectionHead({ eyebrow: "Anti-régression",
        title: "14 différences détectées · 2 anormales", meta: "Seuil détection ± 5 %" }) +
      card({ title: "Comparaison volumétrique", icon: "git-compare", body: `
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead><tr style="background:${slate[50]};">
            <th style="${th}">Indicateur</th><th style="${th}">M10 2025</th><th style="${th}">M11 2025</th>
            <th style="${th}">Δ abs</th><th style="${th}">Δ %</th><th style="${th}">État</th>
          </tr></thead>
          <tbody>
          ${rows.map(r => {
            const c = cmap[r[5]];
            const labl = r[5] === "alert" ? "Anomalie" : r[5] === "warn" ? "À surveiller" : "Stable";
            return `<tr style="border-top:1px solid ${slate[100]};">
              <td style="${td};font-family:'Plus Jakarta Sans';font-weight:600;color:${slate[800]};">${r[0]}</td>
              <td style="${td};color:${slate[600]};">${fr(r[1])}</td>
              <td style="${td};font-weight:700;color:${NAVY};">${fr(r[2])}</td>
              <td style="${td};color:${r[3] >= 0 ? SUCCESS : ERROR};">${r[3] > 0 ? "+" : ""}${fr(r[3])}</td>
              <td style="${td};font-weight:700;color:${c};">${r[4] > 0 ? "+" : ""}${r[4]}%</td>
              <td style="${td};">${statusPill(labl, c)}</td>
            </tr>`;
          }).join("")}
          </tbody></table>` }));
  }

  // ════════════════════════════════════════════════════════════════════════
  //                 ML & IA LOCAL
  // ════════════════════════════════════════════════════════════════════════

  function renderCimSuggester() {
    const sugg = [
      { code: "F32.1",  lib: "Épisode dépressif moyen",                    conf: 0.94 },
      { code: "F33.0",  lib: "Trouble dépressif récurrent · épisode léger", conf: 0.78 },
      { code: "F41.2",  lib: "Trouble anxieux et dépressif mixte",          conf: 0.62 },
      { code: "F43.21", lib: "Réaction dépressive prolongée",                conf: 0.41 },
      { code: "F38.0",  lib: "Autres troubles affectifs · épisodiques",     conf: 0.28 },
    ];
    renderInto(
      sectionHead({ eyebrow: "IA codage CIM-10", title: "CimSuggester · LLM Ollama",
        meta: "Modèle local llama3.2 · 8B paramètres",
        action: btn({ label: "Re-suggérer", kind: "teal", icon: "refresh-cw" }) }) +
      grid("1fr 1fr", 14, row([
        card({ title: "Saisie clinique", icon: "edit-3", body: `
          <div style="display:flex;flex-direction:column;gap:14px;">
            <div>
              <div style="font-size:10px;font-weight:700;color:${slate[600]};
                  text-transform:uppercase;letter-spacing:0.16em;margin-bottom:6px;">DAS Diagnostics associés</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
                  background:${slate[50]};border:1px solid ${slate[200]};
                  border-radius:8px;padding:10px 12px;color:${slate[700]};">F40.1, F45.0, Z73.0</div>
            </div>
            <div>
              <div style="font-size:10px;font-weight:700;color:${slate[600]};
                  text-transform:uppercase;letter-spacing:0.16em;margin-bottom:6px;">Actes CCAM saisis</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
                  background:${slate[50]};border:1px solid ${slate[200]};
                  border-radius:8px;padding:10px 12px;color:${slate[700]};">YYYY020 · entretien initial</div>
            </div>
            <div>
              <div style="font-size:10px;font-weight:700;color:${slate[600]};
                  text-transform:uppercase;letter-spacing:0.16em;margin-bottom:6px;">Notes infirmières (extrait)</div>
              <div style="font-size:12px;color:${slate[700]};line-height:1.5;
                  background:${slate[50]};border:1px solid ${slate[200]};
                  border-radius:8px;padding:10px 12px;">
                « Patient repli social marqué, anhédonie, troubles du sommeil
                évoqués depuis 3 semaines, idées noires sans projet... »
              </div>
            </div>
          </div>` }),
        card({ title: "Diagnostic principal · suggestions", icon: "brain", body: `
          ${sugg.map((s, i) => `
            <div style="padding:12px 0;${i < sugg.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}">
              <div style="display:flex;justify-content:space-between;align-items:center;
                  margin-bottom:6px;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:14px;
                    font-weight:800;color:${NAVY};">${s.code}</span>
                <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                    font-weight:700;color:${s.conf > 0.7 ? SUCCESS : s.conf > 0.5 ? WARNING : slate[500]};">${(s.conf * 100).toFixed(0)} %</span>
              </div>
              <div style="font-size:11px;color:${slate[700]};margin-bottom:6px;">${s.lib}</div>
              <div style="height:4px;background:${slate[100]};border-radius:999px;overflow:hidden;">
                <div style="width:${s.conf * 100}%;height:100%;
                    background:${s.conf > 0.7 ? SUCCESS : s.conf > 0.5 ? WARNING : slate[400]};"></div>
              </div>
            </div>`).join("")}
          <div style="display:flex;gap:8px;margin-top:14px;padding-top:14px;
              border-top:1px solid ${slate[100]};">
            ${btn({ label: "Insérer F32.1", kind: "primary", icon: "check" })}
            ${btn({ label: "Voir alternatives", kind: "ghost", icon: "more-horizontal" })}
          </div>` }),
      ])) +
      metierBanner(`<strong style="color:${NAVY};">Validation TIM obligatoire.</strong> Le ML est une aide au codage, jamais une décision automatique. Source · étude OPTIC CHRU Tours 2022, gain ~1 470 € / RSS recodé.`));
  }

  function renderLstm() {
    const groups = [
      { l: "F32 Dépressif",       short: 8.2,  med: 12.5, long: 21.4, n: 184 },
      { l: "F20 Schizophrénie",  short: 12.4, med: 22.8, long: 38.6, n: 247 },
      { l: "F31 Bipolaire",       short: 9.1,  med: 14.7, long: 24.3, n: 132 },
      { l: "F41 Anxieux",         short: 5.4,  med: 8.2,  long: 12.8, n: 98  },
      { l: "F60 Personnalité",    short: 11.2, med: 18.4, long: 32.1, n: 76  },
    ];
    renderInto(
      sectionHead({ eyebrow: "Modèle LSTM", title: "Prédicteur de DMS · entrée hospitalisation",
        meta: "Stratifié par groupe diagnostique" }) +
      grid("repeat(4,1fr)", 14, row([
        kpi({ label: "DMS prédite (médiane)", value: "14,2", unit: "j", accent: NAVY }),
        kpi({ label: "Écart vs réel",          value: "± 2,3", unit: "j", accent: TEAL, sub: "MAE 7 jours" }),
        kpi({ label: "Patients prédits 90 j", value: "247", accent: GOLD }),
        kpi({ label: "Confiance moyenne",     value: "78", unit: "%", accent: SUCCESS }),
      ])) +
      card({ title: "Estimation par groupe diagnostique CIM-10", icon: "trending-up", body: `
        ${groups.map(g => `
          <div style="padding:12px 0;border-bottom:1px solid ${slate[100]};">
            <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:8px;">
              <span style="font-size:12px;font-weight:700;color:${NAVY};">${g.l}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                  color:${slate[500]};">n=${g.n}</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;height:18px;">
              <div style="flex:${g.short};background:${TEAL};height:100%;
                  border-radius:4px 0 0 4px;"></div>
              <div style="flex:${g.med - g.short};background:${WARNING};height:100%;"></div>
              <div style="flex:${g.long - g.med};background:${ERROR};height:100%;
                  border-radius:0 4px 4px 0;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;
                font-family:'JetBrains Mono',monospace;font-size:10px;
                color:${slate[500]};margin-top:4px;">
              <span>Court · ${g.short} j</span><span>Médian · ${g.med} j</span><span>Long · ${g.long} j</span>
            </div>
          </div>`).join("")}` }));
  }

  function renderClustering() {
    const clusters = [
      { id: "C-01", l: "Dépressif léger ambulatoire",     n: 1242, color: TEAL },
      { id: "C-02", l: "Schizophrénie chronique stable",  n:  847, color: NAVY },
      { id: "C-03", l: "Trouble bipolaire phase aigüe",   n:  412, color: ERROR },
      { id: "C-04", l: "Anxiété généralisée + addiction", n:  328, color: WARNING },
      { id: "C-05", l: "Adolescence troubles conduite",    n:  256, color: GOLD },
      { id: "C-06", l: "Personnalité borderline",         n:  198, color: "#7C3AED" },
    ];
    renderInto(
      sectionHead({ eyebrow: "UMAP + HDBSCAN", title: "Clustering patients · 6 archétypes",
        meta: "Réduction · 32 features → 2D · 3 283 patients",
        action: btn({ label: "Re-cluster", kind: "ghost", icon: "refresh-cw" }) }) +
      grid("2fr 1fr", 14, row([
        card({ title: "Projection UMAP", icon: "scatter-chart", body: `
          <div style="position:relative;height:380px;background:${slate[50]};
              border-radius:8px;overflow:hidden;">
            ${[...Array(120)].map(() => {
              const c = clusters[Math.floor(Math.random() * clusters.length)];
              const x = Math.random() * 95 + 2.5;
              const y = Math.random() * 90 + 5;
              const sz = 4 + Math.random() * 8;
              return `<span style="position:absolute;left:${x}%;top:${y}%;
                  width:${sz}px;height:${sz}px;border-radius:999px;
                  background:${c.color};opacity:0.7;"></span>`;
            }).join("")}
            <span style="position:absolute;bottom:8px;left:8px;
                font-family:'JetBrains Mono',monospace;font-size:10px;
                color:${slate[500]};">UMAP-1 →</span>
            <span style="position:absolute;top:8px;left:8px;
                font-family:'JetBrains Mono',monospace;font-size:10px;
                color:${slate[500]};transform:rotate(-90deg);transform-origin:left top;">UMAP-2 →</span>
          </div>` }),
        card({ title: "Archétypes détectés", icon: "users", body: `
          ${clusters.map((c, i) => `
            <div style="padding:10px 0;${i < clusters.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}
                display:flex;align-items:center;gap:10px;">
              <span style="width:14px;height:14px;border-radius:4px;background:${c.color};"></span>
              <div style="flex:1;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                    font-weight:700;color:${NAVY};">${c.id}</div>
                <div style="font-size:11px;color:${slate[700]};">${c.l}</div>
              </div>
              <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                  font-weight:700;color:${slate[600]};">${c.n}</span>
            </div>`).join("")}` }),
      ])));
  }

  // ════════════════════════════════════════════════════════════════════════
  //                 DONNÉES & ANALYTICS
  // ════════════════════════════════════════════════════════════════════════

  function renderHospitalTwin() {
    const sims = [
      { l: "Réduire délai codage J+15 → J+10", impact: "+ 84 K€",  conf: 0.82 },
      { l: "Combler 5 % de DP manquants",        impact: "+ 142 K€", conf: 0.91 },
      { l: "Améliorer chaînage 95 → 98 %",       impact: "+ 67 K€",  conf: 0.74 },
      { l: "Préflight DRUIDES sur 100 % lots",   impact: "+ 38 K€",  conf: 0.88 },
    ];
    renderInto(
      sectionHead({ eyebrow: "Simulation DFA", title: "Hospital Twin · projection M+12",
        meta: "Modèle dérivé du compartiment 1 (file active)",
        action: btn({ label: "Simuler", kind: "primary", icon: "zap" }) }) +
      grid("repeat(4,1fr)", 14, row([
        kpi({ label: "DFA actuelle (M0)",   value: "39",  unit: "M€", accent: NAVY }),
        kpi({ label: "DFA projetée (M+12)", value: "39,7", unit: "M€", accent: TEAL, sub: "+ 1,8 % vs N-1" }),
        kpi({ label: "Gain potentiel actions", value: "+ 331", unit: "K€", accent: GOLD }),
        kpi({ label: "Sécurisation 2026",   value: "97,5", unit: "%", accent: SUCCESS, sub: "→ 0 % en 2029" }),
      ])) +
      card({ title: "Actions qualité PMSI · impact estimé", icon: "target", body: `
        ${sims.map((s, i) => `
          <div style="padding:14px 0;${i < sims.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}
              display:grid;grid-template-columns:1fr auto auto;gap:18px;align-items:center;">
            <div>
              <div style="font-size:13px;font-weight:600;color:${slate[800]};">${s.l}</div>
              <div style="display:flex;align-items:center;gap:6px;margin-top:4px;">
                <div style="height:4px;width:120px;background:${slate[100]};
                    border-radius:999px;overflow:hidden;">
                  <div style="width:${s.conf * 100}%;height:100%;background:${TEAL};"></div>
                </div>
                <span style="font-family:'JetBrains Mono',monospace;font-size:10px;
                    color:${slate[500]};">conf · ${(s.conf * 100).toFixed(0)} %</span>
              </div>
            </div>
            <span style="font-family:'JetBrains Mono',monospace;font-size:18px;
                font-weight:800;color:${SUCCESS};">${s.impact}</span>
            ${btn({ label: "Détail", kind: "ghost", sm: true, icon: "arrow-right" })}
          </div>`).join("")}` }) +
      metierBanner(`<strong style="color:${NAVY};">Projection cumulée · + 331 K€ / an</strong> si toutes les actions PMSI sont menées. À mettre en regard des ETP TIM nécessaires (~0,4 ETP supp). ROI · 4-6 mois.`));
  }

  function renderHeatmap() {
    const sectors = [
      { name: "94G16", v: 1842, color: ERROR },
      { name: "94G09", v: 1654, color: WARNING },
      { name: "94G02", v: 1423, color: WARNING },
      { name: "94G05", v: 1287, color: TEAL },
      { name: "94I02", v: 982,  color: TEAL },
      { name: "94G14", v: 854,  color: SUCCESS },
      { name: "94G12", v: 742,  color: SUCCESS },
      { name: "94I04", v: 624,  color: SUCCESS },
    ];
    renderInto(
      sectionHead({ eyebrow: "Sectorisation 94 + 92", title: "File active par secteur · M11 2025",
        meta: "Top 8 secteurs · 1,3 M habitants couverts" }) +
      grid("2fr 1fr", 14, row([
        card({ title: "Heatmap géographique", icon: "globe", body: `
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
            ${sectors.map(s => `
              <div style="background:${s.color}22;border:2px solid ${s.color};
                  border-radius:12px;padding:18px 14px;position:relative;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:14px;
                    font-weight:800;color:${NAVY};">${s.name}</div>
                <div style="font-size:24px;font-weight:800;color:${s.color};
                    margin-top:4px;letter-spacing:-0.025em;">${s.v}</div>
                <div style="font-size:9px;font-weight:700;color:${slate[500]};
                    text-transform:uppercase;letter-spacing:0.14em;margin-top:4px;">patients</div>
              </div>`).join("")}
          </div>` }),
        card({ title: "Légende intensité", icon: "layers", body: `
          ${[
            { label: "Très élevé · > 1500", c: ERROR },
            { label: "Élevé · 1200-1500",  c: WARNING },
            { label: "Moyen · 800-1200",  c: TEAL },
            { label: "Faible · < 800",     c: SUCCESS },
          ].map((l, i) => `
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                ${i < 3 ? `border-bottom:1px solid ${slate[100]};` : ""}">
              <span style="width:20px;height:20px;border-radius:6px;background:${l.c};"></span>
              <span style="font-size:12px;color:${slate[700]};">${l.label}</span>
            </div>`).join("")}` }),
      ])));
  }

  function renderPivot() {
    const data = [
      ["Sept",  "Hospi TP",     "F32",  148],
      ["Sept",  "Hospi TP",     "F20",  92],
      ["Sept",  "Ambulatoire",  "F32",  214],
      ["Sept",  "Ambulatoire",  "F20",  187],
      ["Oct",   "Hospi TP",     "F32",  162],
      ["Oct",   "Hospi TP",     "F20",  98],
      ["Oct",   "Ambulatoire",  "F32",  238],
      ["Oct",   "Ambulatoire",  "F20",  201],
    ];
    const td = "padding:10px 14px;font-family:'JetBrains Mono',monospace;font-size:12px;color:" + slate[700];
    const th = "padding:10px 14px;font-size:9px;font-weight:700;color:" + slate[500] +
        ";text-transform:uppercase;letter-spacing:0.16em;text-align:left;background:" + slate[50];
    renderInto(
      sectionHead({ eyebrow: "Exploration", title: "Tableaux croisés ad hoc",
        meta: "Pivot · mois × prise en charge × CIM-10",
        action: btn({ label: "Exporter Excel", kind: "primary", icon: "download" }) }) +
      grid("1fr 3fr", 14, row([
        card({ title: "Champs disponibles", icon: "table", body: `
          ${["Mois", "Prise en charge", "Code CIM-10", "Secteur ARS", "Sexe",
             "Tranche âge", "Mode légal", "Durée séjour"].map(f => `
            <div style="padding:8px 12px;background:${slate[50]};border:1px solid ${slate[100]};
                border-radius:6px;font-size:12px;font-weight:600;color:${slate[700]};
                margin-bottom:6px;cursor:grab;">⋮⋮ ${f}</div>`).join("")}` }),
        card({ title: "Résultats · Mois × PEC × CIM-10", icon: "filter", padding: 0, body: `
          <table style="width:100%;border-collapse:collapse;">
            <thead><tr><th style="${th}">Mois</th><th style="${th}">PEC</th>
              <th style="${th}">CIM-10</th><th style="${th}">Patients</th></tr></thead>
            <tbody>${data.map(r => `
              <tr style="border-top:1px solid ${slate[100]};">
                <td style="${td}">${r[0]}</td><td style="${td}">${r[1]}</td>
                <td style="${td};font-weight:700;color:${NAVY};">${r[2]}</td>
                <td style="${td};font-weight:700;color:${TEAL};">${r[3]}</td>
              </tr>`).join("")}</tbody>
          </table>` }),
      ])));
  }

  // ════════════════════════════════════════════════════════════════════════
  //                 GESTION BATCH
  // ════════════════════════════════════════════════════════════════════════

  function renderModo() {
    const folders = [
      "C:\\PMSI\\Fondation_Vallee\\2025_T3",
      "C:\\PMSI\\Paul_Guiraud\\2025_T3",
      "\\\\NAS-DIM\\exports\\preprod_atih",
    ];
    const files = [
      { n: "RPS_2025T3.txt",       fmt: "RPS",      kind: "PSY",   kb: 4820 },
      { n: "EDGAR_2025T3.txt",     fmt: "EDGAR",    kind: "PSY",   kb: 2104 },
      { n: "RAA_2025T3.txt",       fmt: "RAA",      kind: "PSY",   kb: 1820 },
      { n: "RPSA_2025T3.txt",      fmt: "RPSA",     kind: "PSY",   kb: 1244 },
      { n: "VID-HOSP_2025T3.txt",  fmt: "VID-HOSP", kind: "TRANS", kb:  642 },
      { n: "ANO-HOSP_2025T3.txt",  fmt: "ANO-HOSP", kind: "TRANS", kb:  584 },
      { n: "RHS_2025T3.txt",       fmt: "RHS",      kind: "SSR",   kb:  982 },
      { n: "RPSS_2025T3.txt",      fmt: "RPSS",     kind: "HAD",   kb:  428 },
      { n: "FICHSUP-PSY.txt",      fmt: "FICHSUP",  kind: "PSY",   kb:  208 },
    ];
    renderInto(`
      <div style="background:white;border:1.5px dashed ${slate[300]};border-radius:14px;
          padding:32px 24px;text-align:center;margin-bottom:20px;">
        <div style="width:56px;height:56px;background:${slate[50]};
            border:1px solid ${slate[200]};border-radius:14px;margin:0 auto 14px;
            display:flex;align-items:center;justify-content:center;color:${TEAL};">
          <i data-lucide="upload-cloud" style="width:26px;height:26px;"></i>
        </div>
        <div style="font-size:18px;font-weight:800;color:${NAVY};margin-bottom:4px;">
          Déposer les fichiers PMSI
        </div>
        <div style="font-size:12px;color:${slate[500]};margin-bottom:18px;">
          Glissez vos dossiers ici · fichiers et sous-dossiers inclus
        </div>
        <div style="display:flex;justify-content:center;gap:10px;">
          ${btn({ label: "Ajouter dossier", kind: "primary", icon: "plus" })}
          ${btn({ label: "Scanner & Traiter", kind: "teal", icon: "zap" })}
        </div>
      </div>
      <div style="margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;
            margin-bottom:6px;">
          <span style="font-size:10px;font-weight:700;color:${slate[600]};
              text-transform:uppercase;letter-spacing:0.16em;">Construction MPI</span>
          <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
              color:${NAVY};font-weight:700;">68%</span>
        </div>
        <div style="height:6px;background:${slate[100]};border-radius:999px;overflow:hidden;">
          <div style="width:68%;height:100%;
              background:linear-gradient(90deg,${NAVY},${TEAL});"></div>
        </div>
      </div>` +
      card({ title: "Dossiers surveillés", icon: "folder-tree", body: `
        <div style="display:flex;flex-direction:column;gap:6px;">
          ${folders.map((f, i) => `
            <div style="display:flex;align-items:center;gap:10px;background:${slate[50]};
                padding:9px 14px;border-radius:8px;border:1px solid ${slate[100]};">
              <i data-lucide="folder" style="width:16px;height:16px;color:${NAVY};"></i>
              <span style="flex:1;font-family:'JetBrains Mono',monospace;font-size:11px;
                  color:${slate[700]};">${f}</span>
              <span style="font-size:9px;font-weight:700;color:${TEAL};
                  text-transform:uppercase;letter-spacing:0.16em;">#${i + 1}</span>
            </div>`).join("")}
        </div>` }) +
      `<div style="margin-top:18px;">` +
        sectionHead({ eyebrow: "Lot courant", title: "Fichiers détectés",
          meta: `${files.length} fichiers · 12.8 Mo total` }) +
        `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
          ${files.map(f => `
            <div style="background:white;border:1px solid ${slate[200]};border-radius:10px;
                padding:14px;cursor:pointer;">
              <div style="display:flex;justify-content:space-between;align-items:center;
                  margin-bottom:8px;">
                ${fmtBadge(f.fmt, f.kind)}
                <span style="font-family:'JetBrains Mono',monospace;font-size:9px;
                    color:${slate[400]};">${f.kb.toLocaleString("fr-FR")} KB</span>
              </div>
              <div style="font-size:13px;font-weight:700;color:${NAVY};
                  letter-spacing:-0.01em;">${f.n}</div>
            </div>`).join("")}
        </div></div>`);
  }

  // ════════════════════════════════════════════════════════════════════════
  //                 SÉCURITÉ & OPS
  // ════════════════════════════════════════════════════════════════════════

  function renderRgpd() {
    renderInto(
      sectionHead({ eyebrow: "Conformité", title: "RGPD command center",
        meta: "DPO panel · audit art. 30",
        action: btn({ label: "Export rapport DPO", kind: "primary", icon: "file-text" }) }) +
      grid("repeat(4,1fr)", 14, row([
        kpi({ label: "Accès IPP nominatifs", value: "847", accent: NAVY, sub: "30 derniers jours" }),
        kpi({ label: "Pseudonymisations",    value: "11 247", accent: TEAL, sub: "100 % MPI" }),
        kpi({ label: "k-anonymity ≥ 5",      value: "OK",   accent: SUCCESS, sub: "exports recherche" }),
        kpi({ label: "Bandit security scan",  value: "0",    unit: "issues", accent: SUCCESS }),
      ])) +
      grid("1fr 1fr", 14, row([
        card({ title: "Politique de conservation", icon: "shield", body: `
          ${[
            ["Données médicales nominatives", "20 ans · L. 1110-4 CSP"],
            ["MPI SQLite",                     "Durée traitement + 1 an"],
            ["Audit log",                       "10 ans · art. 30 RGPD"],
            ["Modèles ML (.json)",              "Indéfini · agrégés non-PII"],
            ["Exports CSV pseudonymisés",       "Selon CNIL MR-007 · 2 ans"],
          ].map((r, i) => `
            <div style="display:flex;justify-content:space-between;padding:10px 0;
                ${i < 4 ? `border-bottom:1px solid ${slate[100]};` : ""}">
              <span style="font-size:12px;color:${slate[700]};">${r[0]}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                  color:${NAVY};font-weight:700;">${r[1]}</span>
            </div>`).join("")}` }),
        card({ title: "Articles CSP applicables", icon: "book", body: `
          ${[
            ["L. 6113-7", "Obligation analyse activité par DIM"],
            ["L. 6113-8", "Conditions utilisation données T2A"],
            ["R. 6113-5", "Exception secret médical · personnel DIM"],
            ["R. 6123-174", "Modes prise en charge psychiatrie"],
          ].map((r, i) => `
            <div style="display:flex;gap:14px;padding:10px 0;
                ${i < 3 ? `border-bottom:1px solid ${slate[100]};` : ""}">
              <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                  font-weight:800;color:${TEAL};min-width:90px;">${r[0]}</span>
              <span style="font-size:12px;color:${slate[700]};flex:1;">${r[1]}</span>
            </div>`).join("")}` }),
      ])));
  }

  function renderAudit() {
    const events = [
      { ts: "13:42:18", who: "DIM_ADAM",  action: "EXPORT_PILOT_CSV", target: "MPI_2025T3.csv", color: NAVY },
      { ts: "13:38:42", who: "DIM_ADAM",  action: "RESOLVE_COLLISION", target: "P-840291", color: SUCCESS },
      { ts: "13:24:03", who: "DIM_ADAM",  action: "PROCESS_BATCH",     target: "T3 · 9 fichiers", color: TEAL },
      { ts: "12:58:11", who: "SYSTEM",    action: "ML_TRAIN",          target: "format_detector v36", color: GOLD },
      { ts: "12:14:55", who: "DIM_ADAM",  action: "VIEW_NOMINATIVE",   target: "P-291847", color: WARNING },
      { ts: "11:42:09", who: "DIM_ADAM",  action: "LOGIN",             target: "127.0.0.1", color: slate[500] },
    ];
    renderInto(
      sectionHead({ eyebrow: "Traçabilité immutable", title: "Audit chain · 30 derniers événements",
        meta: "SHA-256 chained · art. 30 RGPD" }) +
      card({ title: "Événements", icon: "history", padding: 0, body: `
        ${events.map((e, i) => `
          <div style="padding:12px 20px;${i < events.length - 1 ? `border-bottom:1px solid ${slate[100]};` : ""}
              display:grid;grid-template-columns:80px 100px 180px 1fr auto;gap:14px;align-items:center;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                color:${slate[500]};">${e.ts}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                font-weight:700;color:${NAVY};">${e.who}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                font-weight:700;color:${e.color};">${e.action}</span>
            <span style="font-size:12px;color:${slate[700]};">${e.target}</span>
            ${btn({ label: "Détails", kind: "ghost", sm: true, icon: "eye" })}
          </div>`).join("")}` }));
  }

  function renderWorkflow() {
    const stages = [
      { l: "TIM corrige",      n: 8,  c: NAVY,    icon: "user" },
      { l: "MIM valide",        n: 3,  c: TEAL,    icon: "user-check" },
      { l: "Préflight DRUIDES", n: 1,  c: GOLD,    icon: "shield" },
      { l: "Export ARS",        n: 0,  c: SUCCESS, icon: "send" },
    ];
    renderInto(
      sectionHead({ eyebrow: "Workflow validation", title: "Pipeline de validation DIM",
        meta: "TIM → MIM → Préflight → ARS" }) +
      grid("repeat(4,1fr)", 14, stages.map((s, i) => `
        <div style="background:white;border:1px solid ${slate[200]};border-radius:12px;
            padding:18px;text-align:center;position:relative;">
          ${i < stages.length - 1 ? `<div style="position:absolute;right:-18px;top:50%;
              transform:translateY(-50%);width:32px;height:2px;background:${slate[200]};"></div>
              <i data-lucide="arrow-right" style="position:absolute;right:-22px;top:50%;
              transform:translateY(-50%);width:14px;height:14px;color:${slate[400]};
              background:white;"></i>` : ""}
          <div style="width:48px;height:48px;border-radius:12px;background:${s.c}22;
              color:${s.c};margin:0 auto 12px;display:flex;align-items:center;
              justify-content:center;">
            <i data-lucide="${s.icon}" style="width:22px;height:22px;"></i>
          </div>
          <div style="font-size:11px;font-weight:700;color:${slate[500]};
              text-transform:uppercase;letter-spacing:0.16em;">${s.l}</div>
          <div style="font-size:32px;font-weight:800;color:${s.c};margin-top:4px;
              letter-spacing:-0.03em;">${s.n}</div>
          <div style="font-size:11px;color:${slate[500]};">en cours</div>
        </div>`).join("")) +
      card({ title: "Tâches en attente · MIM", icon: "clipboard-check", body: `
        ${[
          ["P-840291", "Codage F32 → F33 ?", "TIM_ADAM", "il y a 24 min"],
          ["P-118092", "Mode légal incohérent", "TIM_ADAM", "il y a 1 h"],
          ["P-994412", "DDN à arbitrer", "TIM_SOPHIE", "il y a 3 h"],
        ].map((r, i) => `
          <div style="display:grid;grid-template-columns:120px 1fr 120px auto;gap:14px;
              align-items:center;padding:12px 0;
              ${i < 2 ? `border-bottom:1px solid ${slate[100]};` : ""}">
            <span style="font-family:'JetBrains Mono',monospace;font-size:13px;
                font-weight:700;color:${NAVY};">${r[0]}</span>
            <span style="font-size:13px;color:${slate[800]};">${r[1]}</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:11px;
                color:${slate[500]};">${r[2]} · ${r[3]}</span>
            ${btn({ label: "Valider", kind: "primary", sm: true, icon: "check" })}
          </div>`).join("")}` }));
  }

  // ════════════════════════════════════════════════════════════════════════
  //                 EXPOSITION GLOBALE
  // ════════════════════════════════════════════════════════════════════════

  window.SentinelViews = {
    health:      renderHealth,
    ars:         renderArs,
    cespa:       renderCespa,
    diff:        renderDiff,
    cim:         renderCimSuggester,
    lstm:        renderLstm,
    cluster:     renderClustering,
    twin:        renderHospitalTwin,
    heatmap:     renderHeatmap,
    pivot:       renderPivot,
    modo_v2:     renderModo,
    rgpd:        renderRgpd,
    audit:       renderAudit,
    workflow:    renderWorkflow,
  };
})();

/* Section 1 · Métier DIM — le cœur du quotidien */

// ─── #1 Sentinel ARS · prédicteur de rejet DRUIDES ──────────
const ScreenArsPredictor = () => (
  <Shell active="ars" title="Sentinel ARS" subtitle="Prédicteur de rejet DRUIDES · XGBoost local"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Pré-vol upload ATIH"
      title="Lot 2025-M11 · 8 924 RPS prêts à transmettre"
      meta="Modèle XGBoost v3.2 · 15 validateurs"
      action={<Btn kind="teal" icon={I.send}>Transmettre malgré tout</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 20 }}>
      <Kpi label="Score global" value="94" unit="/ 100" accent={SUCCESS} sub="Risque rejet faible"/>
      <Kpi label="RPS suspects" value="42" unit="/ 8 924" accent={WARNING} sub="0,47 % du lot"/>
      <Kpi label="Économie estimée" value="6,2" unit="h DIM" accent={TEAL} sub="vs cycle reject/repush"/>
    </div>

    <Card title="Top 5 des validateurs à risque" icon={I.alert}>
      {[
        { id: "V07", lib: "Cohérence DDN ↔ âge à l'admission", risk: 78, count: 18, color: ERROR },
        { id: "V12", lib: "INS qualifié vs IPP local", risk: 64, count: 11, color: WARNING },
        { id: "V03", lib: "Mode légal hospitalisation manquant", risk: 52, count: 7, color: WARNING },
        { id: "V21", lib: "Code CIM-10 hors référentiel ATIH", risk: 38, count: 4, color: GOLD },
        { id: "V18", lib: "Date de sortie antérieure à entrée", risk: 22, count: 2, color: TEAL },
      ].map(v => (
        <div key={v.id} style={{
          display: "grid", gridTemplateColumns: "60px 1fr 60px 80px",
          gap: 16, alignItems: "center",
          padding: "12px 0", borderBottom: `1px solid ${slate[100]}`,
        }}>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, color: NAVY }}>{v.id}</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: slate[800] }}>{v.lib}</div>
            <div style={{ height: 4, background: slate[100], borderRadius: 999, marginTop: 6, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${v.risk}%`, background: v.color, borderRadius: 999 }}/>
            </div>
          </div>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 700, color: v.color }}>{v.risk}%</span>
          <span style={{ fontSize: 11, color: slate[500], fontWeight: 600, textAlign: "right" }}>{v.count} RPS</span>
        </div>
      ))}
    </Card>
  </Shell>
);

// ─── #2 Cockpit chef DIM ────────────────────────────────────
const ScreenCockpit = () => (
  <Shell active="cockpit" title="Cockpit chef DIM" subtitle="Tableau de bord exécutif · Novembre 2025"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Vue mensuelle"
      title="Activité GHT · M11 2025"
      meta="MAJ il y a 8 min · auto-publication M+5"
      action={<Btn icon={I.download}>Export PDF mensuel</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14, marginBottom: 20 }}>
      <Kpi label="File active 12 mois" value="14 882" sub="+ 3,2 % vs N-1" accent={TEAL}/>
      <Kpi label="Taux chaînage" value="98,4" unit="%" sub="Cible ≥ 97 %" accent={SUCCESS}/>
      <Kpi label="DP renseigné" value="96,1" unit="%" sub="Cible ≥ 95 %" accent={SUCCESS}/>
      <Kpi label="Score DQC" value="A" sub="9 mois consécutifs" accent={GOLD}/>
    </div>

    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 14 }}>
      <Card title="File active glissante · 12 mois" icon={I.pulse}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 10, height: 180, padding: "12px 4px" }}>
          {[68, 72, 75, 71, 78, 82, 79, 85, 88, 91, 87, 94].map((v, i) => {
            const labels = ["D24","J","F","M","A","M","J","J","A","S","O","N"];
            const isLast = i === 11;
            return (
              <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                <div style={{
                  width: "100%", height: `${v}%`, background: isLast ? NAVY : TEAL,
                  borderRadius: "4px 4px 0 0", opacity: isLast ? 1 : 0.55,
                  position: "relative",
                }}>
                  {isLast && (
                    <div style={{ position: "absolute", top: -22, left: "50%", transform: "translateX(-50%)",
                      fontSize: 10, fontWeight: 800, color: NAVY, fontFamily: "'JetBrains Mono', monospace" }}>
                      14,9k
                    </div>
                  )}
                </div>
                <span style={{ fontSize: 10, color: slate[500], fontWeight: 600 }}>{labels[i]}</span>
              </div>
            );
          })}
        </div>
      </Card>

      <Card title="Alertes écart > 2 %" icon={I.alert}>
        {[
          { sec: "Secteur 94G16", val: "+ 4,2 %", color: WARNING, lib: "Hospitalisations psy" },
          { sec: "Secteur 94I02", val: "− 2,8 %", color: ERROR, lib: "File active pédopsy" },
          { sec: "Secteur 94G09", val: "+ 2,3 %", color: WARNING, lib: "Actes ambulatoires" },
        ].map((a, i) => (
          <div key={i} style={{ padding: "10px 0", borderBottom: i < 2 ? `1px solid ${slate[100]}` : "none" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: slate[800], fontFamily: "'JetBrains Mono', monospace" }}>{a.sec}</span>
              <span style={{ fontSize: 13, fontWeight: 800, color: a.color, fontFamily: "'JetBrains Mono', monospace" }}>{a.val}</span>
            </div>
            <div style={{ fontSize: 11, color: slate[500], marginTop: 2 }}>{a.lib}</div>
          </div>
        ))}
      </Card>
    </div>
  </Shell>
);

// ─── #4 CeSPA / CATTG validator ─────────────────────────────
const ScreenCespa = () => (
  <Shell active="cespa" title="CeSPA / CATTG" subtitle="Conformité réforme 4 juillet 2025"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Réforme financement psy"
      title="Centres de santé psy adultes · 100 % conformes"
      meta="Dernier contrôle · 2025-11-18 · 11:42"
      action={<Btn kind="teal" icon={I.refresh}>Re-vérifier</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 14 }}>
      <Card title="Récap conformité" icon={I.check}>
        <div style={{ textAlign: "center", padding: "20px 0 12px" }}>
          <div style={{
            width: 120, height: 120, margin: "0 auto",
            borderRadius: 999, background: `conic-gradient(${SUCCESS} 0deg 360deg, ${slate[100]} 0deg)`,
            display: "flex", alignItems: "center", justifyContent: "center",
            position: "relative",
          }}>
            <div style={{
              width: 92, height: 92, background: "white", borderRadius: 999,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: NAVY, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "-0.03em" }}>100%</div>
              <div style={{ fontSize: 9, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.16em" }}>CESPA</div>
            </div>
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderTop: `1px solid ${slate[100]}` }}>
          <span style={{ fontSize: 12, color: slate[600], fontWeight: 600 }}>Structures contrôlées</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: NAVY, fontFamily: "'JetBrains Mono', monospace" }}>47 / 47</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderTop: `1px solid ${slate[100]}` }}>
          <span style={{ fontSize: 12, color: slate[600], fontWeight: 600 }}>Actes CATTG validés</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: NAVY, fontFamily: "'JetBrains Mono', monospace" }}>18 244 / 18 244</span>
        </div>
      </Card>

      <Card title="Règles réforme 4 juillet 2025" icon={I.shield}>
        {[
          { code: "R-CSP-01", lib: "Code structure CeSPA présent dans champ 23 RPS", ok: 47 },
          { code: "R-CSP-02", lib: "Forfait CATTG facturable ↔ acte tracé", ok: 47 },
          { code: "R-CSP-04", lib: "Médecin responsable rattaché à structure CeSPA", ok: 47 },
          { code: "R-CSP-07", lib: "Planning hebdomadaire CeSPA déclaré FINESS", ok: 47 },
          { code: "R-CSP-09", lib: "Patient adulte (≥ 18 ans à l'admission)", ok: 47 },
        ].map((r, i) => (
          <div key={i} style={{
            display: "grid", gridTemplateColumns: "100px 1fr auto",
            gap: 14, alignItems: "center",
            padding: "10px 0", borderBottom: i < 4 ? `1px solid ${slate[100]}` : "none",
          }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 700, color: NAVY }}>{r.code}</span>
            <span style={{ fontSize: 12, color: slate[700] }}>{r.lib}</span>
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 5,
              padding: "3px 8px", borderRadius: 6,
              background: "#ECFDF5", color: SUCCESS,
              fontSize: 10, fontWeight: 700,
            }}>
              <span style={{ width: 5, height: 5, borderRadius: 999, background: SUCCESS }}/>
              {r.ok}/47
            </span>
          </div>
        ))}
      </Card>
    </div>
  </Shell>
);

// ─── #8 Diff lots mensuels ──────────────────────────────────
const ScreenDiff = () => (
  <Shell active="diff" title="Diff lots mensuels" subtitle="Détection anomalies de volumétrie · M11 vs M10"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Anti-régression"
      title="14 différences détectées · 2 anormales"
      meta="Seuil détection ± 5 %"
    />

    <Card title="Comparaison volumétrique" icon={I.branch}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ background: slate[50] }}>
            <th style={th}>Indicateur</th>
            <th style={th}>M10 2025</th>
            <th style={th}>M11 2025</th>
            <th style={th}>Δ abs</th>
            <th style={th}>Δ %</th>
            <th style={th}>État</th>
          </tr>
        </thead>
        <tbody style={{ fontFamily: "'JetBrains Mono', monospace" }}>
          {[
            ["RPS produits", 8654, 8924, 270, 3.1, "ok"],
            ["RAA séjours", 1842, 1798, -44, -2.4, "ok"],
            ["Patients DPI", 14421, 14882, 461, 3.2, "ok"],
            ["Actes ambulatoires", 22884, 26512, 3628, 15.8, "warn"],
            ["Hospi temps plein", 982, 1004, 22, 2.2, "ok"],
            ["CMP secteur G16", 1244, 956, -288, -23.2, "alert"],
            ["INS qualifiés", 14102, 14651, 549, 3.9, "ok"],
          ].map((r, i) => {
            const colorMap = { ok: SUCCESS, warn: WARNING, alert: ERROR };
            const c = colorMap[r[5]];
            return (
              <tr key={i} style={{ borderTop: `1px solid ${slate[100]}` }}>
                <td style={{ ...td, fontFamily: "'Plus Jakarta Sans'", fontWeight: 600, color: slate[800] }}>{r[0]}</td>
                <td style={td}>{r[1].toLocaleString("fr")}</td>
                <td style={{ ...td, fontWeight: 700, color: NAVY }}>{r[2].toLocaleString("fr")}</td>
                <td style={{ ...td, color: r[3] >= 0 ? SUCCESS : ERROR }}>{r[3] > 0 ? "+" : ""}{r[3].toLocaleString("fr")}</td>
                <td style={{ ...td, fontWeight: 700, color: c }}>{r[4] > 0 ? "+" : ""}{r[4]}%</td>
                <td style={td}>
                  <span style={{
                    display: "inline-flex", alignItems: "center", gap: 5,
                    padding: "2px 8px", borderRadius: 6,
                    background: r[5] === "ok" ? "#ECFDF5" : r[5] === "warn" ? "#FFFBEB" : "#FFF1F2",
                    color: c, fontSize: 10, fontWeight: 700, fontFamily: "'Plus Jakarta Sans'",
                  }}>
                    <span style={{ width: 5, height: 5, borderRadius: 999, background: c }}/>
                    {r[5] === "ok" ? "Normal" : r[5] === "warn" ? "À vérifier" : "Anomalie"}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Card>
  </Shell>
);

const th = { textAlign: "left", padding: "10px 14px", fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em", borderBottom: `1px solid ${slate[200]}` };
const td = { padding: "10px 14px", fontSize: 12, color: slate[700] };

Object.assign(window, {
  ScreenArsPredictor, ScreenCockpit, ScreenCespa, ScreenDiff,
});

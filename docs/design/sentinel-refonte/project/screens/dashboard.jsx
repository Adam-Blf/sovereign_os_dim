/* Dashboard screen */
const ScreenDashboard = () => {
  const formats = [
    { label: "RPS", v: 4280, c: "#4338CA" },
    { label: "EDGAR", v: 2150, c: "#6366F1" },
    { label: "RAA", v: 1820, c: "#0F766E" },
    { label: "RPSA", v: 1240, c: "#14B8A6" },
    { label: "RHS", v: 980, c: "#B45309" },
    { label: "VID-HOSP", v: 640, c: "#94A3B8" },
  ];
  const total = formats.reduce((s, f) => s + f.v, 0);
  // build doughnut path strokes
  let acc = 0;
  const R = 60, C = 2 * Math.PI * R;
  const segs = formats.map(f => {
    const len = (f.v / total) * C;
    const seg = { ...f, dash: len, gap: C - len, offset: -acc };
    acc += len;
    return seg;
  });

  const matrix = [
    { k: "RPS", desc: "Résumé Psychiatrique de Séjour", len: 199, ipp: "10:25", ddn: "26:33" },
    { k: "EDGAR", desc: "Activité ambulatoire psy", len: 128, ipp: "8:23", ddn: "24:31" },
    { k: "RHS", desc: "Résumé Hebdomadaire SSR", len: 245, ipp: "12:27", ddn: "28:35" },
    { k: "RPSS", desc: "Résumé Par Séjour Standardisé HAD", len: 187, ipp: "10:25", ddn: "26:33" },
    { k: "RSS", desc: "Résumé Standardisé de Sortie MCO", len: 152, ipp: "9:24", ddn: "25:32" },
    { k: "VID-HOSP", desc: "Identifiants chaînage", len: 89, ipp: "1:16", ddn: "—" },
  ];

  const journeys = [
    { ipp: "P-840291", n: 4, mods: ["RPS", "EDGAR", "RHS", "RPSS"], years: ["2022", "2023", "2024", "2025"] },
    { ipp: "P-291847", n: 3, mods: ["EDGAR", "RPSA", "VID-HOSP"], years: ["2023", "2024", "2025"] },
    { ipp: "P-118092", n: 3, mods: ["RPS", "RAA", "RHS"], years: ["2022", "2024", "2025"] },
    { ipp: "P-557102", n: 2, mods: ["RPS", "EDGAR"], years: ["2024", "2025"] },
  ];
  const allYears = ["2021", "2022", "2023", "2024", "2025"];
  const FIELD_COL = { PSY: "#6366F1", SSR: "#14B8A6", HAD: "#F59E0B", MCO: "#F43F5E", TRANS: "#94A3B8" };
  const FIELD_OF = { RPS: "PSY", RAA: "PSY", RPSA: "PSY", EDGAR: "PSY", RHS: "SSR", RPSS: "HAD", "VID-HOSP": "TRANS" };

  return (
    <Shell active="dashboard" title="Dashboard" subtitle="Tableau de bord de production" badges={{ idv: 12 }}>
      {/* KPI row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 22 }}>
        <Kpi label="Dossiers" value="3" accent={NAVY} sub="Multi-site GHT Sud Paris"/>
        <Kpi label="Fichiers détectés" value="42" unit="ATIH" accent={TEAL} sub="23 formats supportés"/>
        <Kpi label="IPP uniques" value="11 247" accent={GOLD} sub="Master Patient Index"/>
        <Kpi label="Collisions" value="12" accent={ERROR} sub="à résoudre avant export"/>
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 22 }}>
        <Card title="Répartition formats" icon={I.pulse}>
          <div style={{ display: "flex", alignItems: "center", gap: 24, padding: "10px 0" }}>
            <svg width={170} height={170} viewBox="0 0 170 170">
              <g transform="translate(85,85) rotate(-90)">
                <circle r={R} fill="none" stroke={slate[100]} strokeWidth={22}/>
                {segs.map((s, i) => (
                  <circle key={i} r={R} fill="none" stroke={s.c} strokeWidth={22}
                    strokeDasharray={`${s.dash} ${s.gap}`} strokeDashoffset={s.offset}/>
                ))}
              </g>
              <text x={85} y={82} textAnchor="middle" fontSize="22" fontWeight="800" fill={NAVY}
                fontFamily="'JetBrains Mono', monospace" letterSpacing="-0.03em">{total.toLocaleString("fr-FR")}</text>
              <text x={85} y={98} textAnchor="middle" fontSize="9" fontWeight="700" fill={slate[400]}
                letterSpacing="0.18em">LIGNES</text>
            </svg>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 7 }}>
              {formats.map((f, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ width: 9, height: 9, borderRadius: 2, background: f.c }}/>
                  <span style={{ fontSize: 12, fontWeight: 600, color: slate[700], flex: 1 }}>{f.label}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[500], fontWeight: 600 }}>
                    {f.v.toLocaleString("fr-FR")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card title="Matrice ATIH · 6 formats actifs" icon={I.database}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {matrix.map((m, i) => (
              <div key={i} style={{
                background: slate[50], border: `1px solid ${slate[100]}`,
                padding: "10px 12px", borderRadius: 8,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <FmtBadge label={m.k} kind={FIELD_OF[m.k] || "TRANS"}/>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: slate[400] }}>{m.len}c</span>
                </div>
                <div style={{ fontSize: 11, color: slate[600], lineHeight: 1.35 }}>{m.desc}</div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: slate[400], marginTop: 4 }}>
                  IPP[{m.ipp}] · DDN[{m.ddn}]
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* MPI status */}
      <Card title="État MPI" icon={I.fingerprint}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {[
            { l: "Total IPP", v: "11 247", c: NAVY },
            { l: "Collisions", v: "12", c: ERROR },
            { l: "Résolues", v: "847", c: SUCCESS },
            { l: "En attente", v: "12", c: WARNING },
          ].map((x, i) => (
            <div key={i} style={{
              background: slate[50], border: `1px solid ${slate[100]}`,
              padding: "16px 18px", borderRadius: 10, textAlign: "left",
            }}>
              <div style={{ fontSize: 9, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.16em", marginBottom: 6 }}>
                {x.l}
              </div>
              <div style={{ fontSize: 26, fontWeight: 800, color: x.c, fontFeatureSettings: "'tnum'", letterSpacing: "-0.025em", lineHeight: 1 }}>
                {x.v}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Cross-modality */}
      <div style={{ marginTop: 14 }}>
        <Card title="Parcours cross-modalités" icon={I.branch}
          action={<span style={{ fontSize: 10, color: slate[400], fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.1em" }}>
            top {journeys.length} · timeline 2021 → 2025
          </span>}
          padding={0}>
          {/* timeline header */}
          <div style={{
            padding: "10px 20px", borderBottom: `1px solid ${slate[100]}`,
            display: "grid", gridTemplateColumns: "60px 1fr 1.5fr 200px", alignItems: "center", gap: 16,
            fontSize: 9, fontWeight: 700, color: slate[400], textTransform: "uppercase", letterSpacing: "0.18em",
            background: slate[50],
          }}>
            <span>Cmpx.</span><span>IPP</span><span>Modalités</span>
            <span style={{ display: "flex", justifyContent: "space-between" }}>
              {allYears.map(y => <span key={y} style={{ fontFamily: "'JetBrains Mono', monospace" }}>'{y.slice(-2)}</span>)}
            </span>
          </div>
          {journeys.map((j, i) => (
            <div key={i} style={{
              padding: "14px 20px", borderBottom: i < journeys.length - 1 ? `1px solid ${slate[100]}` : "none",
              display: "grid", gridTemplateColumns: "60px 1fr 1.5fr 200px", alignItems: "center", gap: 16,
            }}>
              <div style={{ fontSize: 26, fontWeight: 800, color: j.n >= 4 ? ERROR : j.n === 3 ? WARNING : TEAL, lineHeight: 1, letterSpacing: "-0.04em" }}>
                {j.n}
              </div>
              <div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color: NAVY, fontSize: 13 }}>{j.ipp}</div>
                <div style={{ fontSize: 9, fontWeight: 700, color: slate[400], textTransform: "uppercase", letterSpacing: "0.18em", marginTop: 3 }}>
                  {j.n} modalités · {j.years.length} années
                </div>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                {j.mods.map((m, k) => <FmtBadge key={k} label={m} kind={FIELD_OF[m] || "TRANS"}/>)}
              </div>
              <div style={{ display: "flex", gap: 4 }}>
                {allYears.map(y => (
                  <div key={y} style={{
                    flex: 1, height: 22, borderRadius: 4,
                    background: j.years.includes(y) ? FIELD_COL[FIELD_OF[j.mods[0]] || "TRANS"] : slate[100],
                    opacity: j.years.includes(y) ? 1 : 1,
                  }}/>
                ))}
              </div>
            </div>
          ))}
        </Card>
      </div>
    </Shell>
  );
};
window.ScreenDashboard = ScreenDashboard;

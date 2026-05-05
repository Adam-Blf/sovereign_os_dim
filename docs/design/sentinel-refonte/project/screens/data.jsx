/* Section 3 · Données et analytics */

// ─── #19 Hospital Twin · simulation tarifaire ───────────────
const ScreenHospitalTwin = () => (
  <Shell active="twin" title="Hospital Twin" subtitle="Simulation impact tarifaire DFA"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Arbitrage stratégique"
      title="Scenario · « Améliorer chaînage de 1 pt »"
      meta="Projection M+1 / M+3 / M+12"
      action={<Btn kind="teal" icon={I.play}>Lancer simulation</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 18 }}>
      {[
        { h: "M+1", base: "1,82 M€", proj: "+ 14,2 k€", color: TEAL },
        { h: "M+3", base: "5,46 M€", proj: "+ 41,8 k€", color: TEAL },
        { h: "M+12", base: "21,84 M€", proj: "+ 167,3 k€", color: SUCCESS },
      ].map(s => (
        <div key={s.h} style={{
          background: "white", border: `1px solid ${slate[200]}`, borderRadius: 12,
          padding: 18, position: "relative", overflow: "hidden",
        }}>
          <div style={{ position: "absolute", inset: 0, background: `linear-gradient(135deg, ${s.color}08, transparent)` }}/>
          <div style={{ position: "relative" }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.16em" }}>Horizon {s.h}</div>
            <div style={{ fontSize: 14, color: slate[600], marginTop: 8, fontFamily: "'JetBrains Mono', monospace" }}>{s.base}</div>
            <div style={{ fontSize: 24, fontWeight: 800, color: s.color, marginTop: 4, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "-0.02em" }}>{s.proj}</div>
          </div>
        </div>
      ))}
    </div>

    <Card title="Variables du scenario" icon={I.settings}>
      {[
        { lib: "Taux chaînage cible", v: 99.4, base: 98.4, unit: "%" },
        { lib: "% DP renseigné", v: 96.1, base: 96.1, unit: "%" },
        { lib: "Délai retransmission", v: 3, base: 7, unit: "j" },
        { lib: "Taux INS qualifiée", v: 99.0, base: 96.4, unit: "%" },
      ].map((r, i) => (
        <div key={i} style={{ padding: "12px 0", borderBottom: i < 3 ? `1px solid ${slate[100]}` : "none" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: slate[700] }}>{r.lib}</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[500] }}>
              <span style={{ textDecoration: "line-through", marginRight: 8 }}>{r.base}{r.unit}</span>
              <span style={{ color: NAVY, fontWeight: 700 }}>{r.v}{r.unit}</span>
            </span>
          </div>
          <div style={{ position: "relative", height: 6, background: slate[100], borderRadius: 999 }}>
            <div style={{ position: "absolute", left: 0, top: 0, height: "100%", width: `${r.v}%`, background: TEAL, borderRadius: 999 }}/>
            <div style={{ position: "absolute", left: `${r.v}%`, top: -3, width: 12, height: 12, background: NAVY, borderRadius: 999, transform: "translateX(-50%)", border: "2px solid white", boxShadow: "0 1px 4px rgba(0,0,145,0.3)" }}/>
          </div>
        </div>
      ))}
    </Card>
  </Shell>
);

// ─── #25 Heatmap géographique ───────────────────────────────
const ScreenHeatmap = () => (
  <Shell active="heatmap" title="Sectorisation visuelle" subtitle="File active par code postal · Val-de-Marne"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Carte anonymisée · k ≥ 5"
      title="14 882 patients · 47 communes"
      action={<Btn icon={I.download} kind="ghost">Export GeoJSON</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 14 }}>
      <Card title="Heatmap secteur" icon={I.layout} padding={0}>
        <div style={{ position: "relative", height: 460, background: slate[50] }}>
          <svg viewBox="0 0 400 320" style={{ width: "100%", height: "100%" }}>
            {/* Faux contour Val-de-Marne */}
            <path d="M50,80 L120,40 L200,50 L280,80 L340,140 L320,220 L240,270 L160,260 L80,220 L40,160 Z"
                  fill={slate[100]} stroke={slate[300]} strokeWidth="1.5"/>
            {/* hex bins */}
            {[
              { x: 100, y: 110, v: 0.9 }, { x: 140, y: 100, v: 0.7 }, { x: 180, y: 90, v: 0.5 },
              { x: 220, y: 100, v: 0.6 }, { x: 260, y: 130, v: 0.4 }, { x: 130, y: 140, v: 0.95 },
              { x: 170, y: 140, v: 0.85 }, { x: 210, y: 145, v: 0.7 }, { x: 250, y: 170, v: 0.55 },
              { x: 100, y: 180, v: 0.6 }, { x: 140, y: 180, v: 0.75 }, { x: 180, y: 190, v: 0.5 },
              { x: 220, y: 200, v: 0.45 }, { x: 130, y: 220, v: 0.4 }, { x: 170, y: 230, v: 0.35 },
            ].map((h, i) => {
              const c = `oklch(0.55 0.15 ${260 - h.v * 40} / ${0.3 + h.v * 0.6})`;
              return (
                <g key={i}>
                  <polygon
                    points={`${h.x},${h.y - 18} ${h.x + 16},${h.y - 9} ${h.x + 16},${h.y + 9} ${h.x},${h.y + 18} ${h.x - 16},${h.y + 9} ${h.x - 16},${h.y - 9}`}
                    fill={c} stroke="white" strokeWidth="1"
                  />
                </g>
              );
            })}
          </svg>
          {/* Legend */}
          <div style={{
            position: "absolute", bottom: 16, left: 16,
            background: "white", border: `1px solid ${slate[200]}`, borderRadius: 8,
            padding: "8px 12px", display: "flex", alignItems: "center", gap: 8,
            boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
          }}>
            <span style={{ fontSize: 9, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em" }}>Densité</span>
            <div style={{ width: 100, height: 8, borderRadius: 4, background: `linear-gradient(90deg, oklch(0.55 0.15 260 / 0.3), oklch(0.55 0.15 220 / 0.95))` }}/>
            <span style={{ fontSize: 10, color: slate[500], fontFamily: "'JetBrains Mono', monospace" }}>5 → 1 250</span>
          </div>
        </div>
      </Card>

      <Card title="Top 8 communes" icon={I.users}>
        {[
          { cp: "94400", v: "Vitry-sur-Seine", n: 1842, pct: 12.4 },
          { cp: "94200", v: "Ivry-sur-Seine", n: 1421, pct: 9.5 },
          { cp: "94000", v: "Créteil", n: 1304, pct: 8.8 },
          { cp: "94800", v: "Villejuif", n: 1188, pct: 8.0 },
          { cp: "94340", v: "Joinville-le-Pont", n: 854, pct: 5.7 },
          { cp: "94700", v: "Maisons-Alfort", n: 742, pct: 5.0 },
          { cp: "94120", v: "Fontenay-sous-Bois", n: 622, pct: 4.2 },
          { cp: "94250", v: "Gentilly", n: 548, pct: 3.7 },
        ].map((r, i) => (
          <div key={r.cp} style={{
            display: "grid", gridTemplateColumns: "60px 1fr 60px 50px", gap: 10,
            alignItems: "center", padding: "8px 0",
            borderBottom: i < 7 ? `1px solid ${slate[100]}` : "none",
          }}>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 700, color: NAVY }}>{r.cp}</span>
            <span style={{ fontSize: 12, color: slate[700] }}>{r.v}</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, color: slate[800], textAlign: "right" }}>{r.n.toLocaleString("fr")}</span>
            <span style={{ fontSize: 11, color: slate[500], fontWeight: 600, textAlign: "right" }}>{r.pct}%</span>
          </div>
        ))}
      </Card>
    </div>
  </Shell>
);

// ─── #23 Tableaux croisés dynamiques ────────────────────────
const ScreenPivot = () => (
  <Shell active="pivot" title="Tableaux croisés dynamiques" subtitle="Pivot in-app sur le MPI"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Exploration libre"
      title="Activité × Secteur × Mois · M01 → M11 2025"
      action={<Btn icon={I.download} kind="ghost">Export Excel</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 14 }}>
      <Card title="Champs disponibles" icon={I.filter}>
        {[
          { g: "Lignes", items: ["Secteur", "Mode légal"] },
          { g: "Colonnes", items: ["Mois", "Année"] },
          { g: "Valeurs", items: ["File active", "Σ RSS", "DMS"] },
          { g: "Filtres", items: ["Pôle", "Tranche d'âge"] },
        ].map(g => (
          <div key={g.g} style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.14em", marginBottom: 6 }}>{g.g}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {g.items.map(it => (
                <div key={it} style={{
                  padding: "6px 10px", background: slate[50], border: `1px solid ${slate[200]}`,
                  borderRadius: 6, fontSize: 11, fontWeight: 600, color: slate[700],
                  display: "flex", alignItems: "center", gap: 6,
                }}>
                  <span style={{ width: 4, height: 4, borderRadius: 999, background: TEAL }}/>
                  {it}
                </div>
              ))}
            </div>
          </div>
        ))}
      </Card>

      <Card title="Pivot · file active" icon={I.table} padding={0}>
        <div style={{ overflow: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead>
              <tr style={{ background: slate[50] }}>
                <th style={th}>Secteur</th>
                {["M07","M08","M09","M10","M11"].map(m => <th key={m} style={th}>{m}</th>)}
                <th style={{...th, color: NAVY }}>Total</th>
              </tr>
            </thead>
            <tbody style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              {[
                ["94G01", 482, 491, 502, 488, 511, 2474],
                ["94G09", 622, 631, 645, 658, 667, 3223],
                ["94G16", 1124, 1142, 1158, 1182, 1232, 5838],
                ["94I02", 422, 418, 424, 412, 401, 2077],
                ["94I05", 388, 392, 401, 408, 414, 2003],
              ].map((r, i) => (
                <tr key={i} style={{ borderTop: `1px solid ${slate[100]}` }}>
                  <td style={{ ...td, fontWeight: 700, color: NAVY }}>{r[0]}</td>
                  {r.slice(1, 6).map((v, j) => <td key={j} style={td}>{v.toLocaleString("fr")}</td>)}
                  <td style={{ ...td, fontWeight: 700, color: NAVY, background: slate[50] }}>{r[6].toLocaleString("fr")}</td>
                </tr>
              ))}
              <tr style={{ borderTop: `2px solid ${slate[300]}`, background: slate[50] }}>
                <td style={{ ...td, fontWeight: 800, color: NAVY, fontFamily: "'Plus Jakarta Sans'" }}>Total</td>
                <td style={{...td, fontWeight: 700 }}>3 038</td>
                <td style={{...td, fontWeight: 700 }}>3 074</td>
                <td style={{...td, fontWeight: 700 }}>3 130</td>
                <td style={{...td, fontWeight: 700 }}>3 148</td>
                <td style={{...td, fontWeight: 700 }}>3 225</td>
                <td style={{...td, fontWeight: 800, color: NAVY }}>15 615</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  </Shell>
);

Object.assign(window, {
  ScreenHospitalTwin, ScreenHeatmap, ScreenPivot,
});

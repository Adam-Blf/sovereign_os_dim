/* Identitovigilance screen */
const ScreenIdv = () => {
  const collisions = [
    { ipp: "P-840291", names: "MARTIN Sophie",   ddns: ["1972-03-14", "1972-04-14"], src: 3, status: "pending" },
    { ipp: "P-291847", names: "DUBOIS Jean",     ddns: ["1958-11-02", "1958-11-20"], src: 2, status: "pending" },
    { ipp: "P-118092", names: "LEROY Catherine", ddns: ["1985-07-09", "1985-09-07"], src: 4, status: "pending" },
    { ipp: "P-557102", names: "BERNARD Paul",    ddns: ["1965-02-28", "1965-02-08"], src: 2, status: "resolved", chosen: "1965-02-28" },
    { ipp: "P-672018", names: "PETIT Marie",     ddns: ["1990-12-15", "1990-12-25"], src: 3, status: "pending" },
    { ipp: "P-994412", names: "ROBERT Henri",    ddns: ["1948-06-21", "1948-06-12"], src: 2, status: "resolved", chosen: "1948-06-21" },
  ];

  return (
    <Shell active="idv" title="Identitovigilance" subtitle="Master Patient Index — résolution des collisions" badges={{ idv: 12 }}>
      {/* Header bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 18 }}>
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.18em", marginBottom: 6 }}>
            Master Patient Index
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: NAVY, letterSpacing: "-0.02em", lineHeight: 1.1 }}>
            Conflits d'identité
          </div>
          <div style={{ fontSize: 11, color: slate[500], marginTop: 4 }}>
            11 247 IPP · 12 collisions actives · 847 résolues
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: slate[400], display: "flex" }}>{I.search}</span>
            <input style={{
              padding: "8px 12px 8px 34px", border: `1px solid ${slate[200]}`,
              borderRadius: 8, fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
              background: "white", width: 220, color: slate[700], outline: "none",
            }} placeholder="Rechercher IPP…" defaultValue=""/>
          </div>
          <Btn kind="warn" icon={I.zap}>Auto-résoudre</Btn>
        </div>
      </div>

      {/* KPI strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 18 }}>
        <Kpi label="Collisions DDN" value="9" accent={ERROR}/>
        <Kpi label="Collisions Nom" value="3" accent={WARNING}/>
        <Kpi label="Auto-résolvables" value="7" accent={TEAL} sub="Fréquence majoritaire claire"/>
        <Kpi label="Manuel requis" value="5" accent={NAVY} sub="Arbitrage opérateur"/>
      </div>

      {/* Collision table */}
      <Card title="Conflits détectés" icon={I.alert}
        action={<span style={{ fontSize: 10, color: slate[400], fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.1em" }}>
          tri : par fréquence
        </span>} padding={0}>
        {/* header */}
        <div style={{
          padding: "12px 20px", borderBottom: `1px solid ${slate[100]}`, background: slate[50],
          display: "grid", gridTemplateColumns: "1.2fr 1.4fr 1.6fr 0.6fr 0.8fr 1.2fr", alignItems: "center", gap: 14,
          fontSize: 9, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.18em",
        }}>
          <span>IPP</span><span>Identité</span><span>Dates de naissance</span>
          <span>Sources</span><span>Statut</span><span>Action</span>
        </div>

        {collisions.map((c, i) => (
          <div key={i} style={{
            padding: "14px 20px", borderBottom: i < collisions.length - 1 ? `1px solid ${slate[100]}` : "none",
            display: "grid", gridTemplateColumns: "1.2fr 1.4fr 1.6fr 0.6fr 0.8fr 1.2fr", alignItems: "center", gap: 14,
            background: c.status === "resolved" ? "rgba(16,185,129,0.03)" : "white",
          }}>
            <div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color: NAVY, fontSize: 13 }}>{c.ipp}</div>
            </div>
            <div style={{ fontSize: 12, fontWeight: 600, color: slate[700] }}>{c.names}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {c.ddns.map((d, k) => (
                <div key={k} style={{
                  display: "inline-flex", alignItems: "center", gap: 6, alignSelf: "flex-start",
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
                  padding: "3px 9px", borderRadius: 6,
                  background: c.chosen === d ? "rgba(16,185,129,0.12)" : slate[50],
                  color: c.chosen === d ? "#047857" : slate[700],
                  border: c.chosen === d ? "1px solid rgba(16,185,129,0.35)" : `1px solid ${slate[200]}`,
                  fontWeight: 600,
                }}>
                  {c.chosen === d && <span style={{ display: "flex" }}><Icon size={11} color="#047857" stroke={2.5} d={<path d="M20 6 9 17l-5-5"/>}/></span>}
                  {d}
                </div>
              ))}
            </div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[600], fontWeight: 600 }}>
              {c.src} fichiers
            </div>
            <div>
              {c.status === "resolved" ? (
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 4, fontSize: 10, fontWeight: 700,
                  textTransform: "uppercase", letterSpacing: "0.14em", color: SUCCESS,
                }}>
                  <span style={{ width: 6, height: 6, borderRadius: 999, background: SUCCESS }}/>Résolu
                </span>
              ) : (
                <span style={{
                  display: "inline-flex", alignItems: "center", gap: 4, fontSize: 10, fontWeight: 700,
                  textTransform: "uppercase", letterSpacing: "0.14em", color: WARNING,
                }}>
                  <span style={{ width: 6, height: 6, borderRadius: 999, background: WARNING }}/>En attente
                </span>
              )}
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              {c.status === "pending" ? (
                <>
                  <Btn kind="primary" sm>Arbitrer</Btn>
                  <Btn kind="ghost" sm>Auto</Btn>
                </>
              ) : (
                <Btn kind="ghost" sm icon={I.history}>Historique</Btn>
              )}
            </div>
          </div>
        ))}
      </Card>

      {/* Reconciliation modal preview */}
      <div style={{ marginTop: 18 }}>
        <Card title="Modale de réconciliation · aperçu" icon={I.refresh}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 24, alignItems: "center", padding: "8px 4px 4px" }}>
            <div style={{
              width: 72, height: 72, background: WARNING, borderRadius: 16,
              display: "flex", alignItems: "center", justifyContent: "center", color: "white",
            }}>
              <Icon size={36} color="white" stroke={2} d={<><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>}/>
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: NAVY, letterSpacing: "-0.015em" }}>
                Conflit d'identité — IPP <span style={{ color: ERROR, fontFamily: "'JetBrains Mono', monospace" }}>P-840291</span>
              </div>
              <div style={{ fontSize: 12, color: slate[600], marginTop: 4 }}>
                Cet IPP possède plusieurs dates de naissance. Sélectionnez la date pivot canonique — elle sera réinjectée dans tout le batch et les exports CSV.
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
                <Btn kind="primary">1972-03-14 <span style={{ opacity: 0.7, fontWeight: 500, marginLeft: 4 }}>· 2 sources</span></Btn>
                <Btn kind="ghost">1972-04-14 <span style={{ opacity: 0.7, fontWeight: 500, marginLeft: 4 }}>· 1 source</span></Btn>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </Shell>
  );
};
window.ScreenIdv = ScreenIdv;

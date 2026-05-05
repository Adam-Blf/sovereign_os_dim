/* PMSI Pilot CSV export screen */
const ScreenPilot = () => {
  const exports = [
    { n: "MPI_2025T3_pilot.csv",        rows: 11247, mb: 4.8, when: "il y a 12 min", status: "ok" },
    { n: "Collisions_2025T3.csv",       rows: 12,    mb: 0.1, when: "il y a 12 min", status: "ok" },
    { n: "FileActive_2025T3.csv",       rows: 8420,  mb: 2.1, when: "il y a 14 min", status: "ok" },
    { n: "MPI_2025T2_pilot.csv",        rows: 10882, mb: 4.6, when: "il y a 38 j",   status: "archived" },
  ];

  return (
    <Shell active="pilot" title="PMSI Pilot CSV" subtitle="Export des données réconciliées" badges={{ idv: 12 }}>
      <SectionHead eyebrow="Étape finale" title="Configurer l'export"
        meta="Données réconciliées via MPI · format e-PMSI"
      />

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14 }}>
        {/* Configurator */}
        <Card title="Périmètre de l'export" icon={I.settings}>
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <Field label="Période" hint="Trimestre PMSI">
              <div style={{ display: "flex", gap: 8 }}>
                {["2025-T1", "2025-T2", "2025-T3", "2025-T4"].map(p => (
                  <div key={p} style={{
                    flex: 1, padding: "10px 0", textAlign: "center", borderRadius: 8,
                    border: `1px solid ${p === "2025-T3" ? NAVY : slate[200]}`,
                    background: p === "2025-T3" ? NAVY : "white",
                    color: p === "2025-T3" ? "white" : slate[700],
                    fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: 12,
                    cursor: "pointer",
                  }}>{p}</div>
                ))}
              </div>
            </Field>

            <Field label="Champs PMSI" hint="Sélection multi-modalités">
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {[
                  { k: "PSY", on: true }, { k: "SSR", on: true }, { k: "HAD", on: true },
                  { k: "MCO", on: false }, { k: "TRANS", on: true },
                ].map(o => (
                  <div key={o.k} style={{
                    display: "inline-flex", alignItems: "center", gap: 7,
                    padding: "7px 14px", borderRadius: 999,
                    border: `1px solid ${o.on ? TEAL : slate[200]}`,
                    background: o.on ? "rgba(0,137,123,0.08)" : "white",
                    color: o.on ? "#0F766E" : slate[600],
                    fontWeight: 700, fontSize: 11, cursor: "pointer",
                  }}>
                    <span style={{ width: 14, height: 14, borderRadius: 4, border: `1.5px solid ${o.on ? TEAL : slate[300]}`, background: o.on ? TEAL : "white", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      {o.on && <Icon size={10} color="white" stroke={3} d={<path d="M20 6 9 17l-5-5"/>}/>}
                    </span>
                    {o.k}
                  </div>
                ))}
              </div>
            </Field>

            <Field label="Options" hint="Préférences export">
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <Toggle label="Pseudonymisation IPP" desc="SHA-256 + sel par établissement" on/>
                <Toggle label="Inclure les collisions résolues" desc="Avec horodatage et opérateur" on/>
                <Toggle label="Encodage UTF-8 BOM" desc="Compatible Excel français" on/>
                <Toggle label="Splitter par champ PMSI" desc="Un fichier par modalité" off/>
              </div>
            </Field>

            <div style={{ display: "flex", gap: 10, paddingTop: 6, borderTop: `1px solid ${slate[100]}` }}>
              <Btn kind="primary" icon={I.download}>Générer l'export</Btn>
              <Btn kind="ghost" icon={I.eye}>Aperçu (10 lignes)</Btn>
            </div>
          </div>
        </Card>

        {/* Preview + status */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Card title="Estimation" icon={I.pulse}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                { l: "Lignes", v: "11 247" },
                { l: "Taille estimée", v: "4.8 Mo" },
                { l: "Conflits", v: "0", c: SUCCESS, sub: "tous résolus" },
                { l: "Durée estimée", v: "~ 8 s" },
              ].map((x, i) => (
                <div key={i} style={{
                  background: slate[50], border: `1px solid ${slate[100]}`,
                  borderRadius: 8, padding: "12px 14px",
                }}>
                  <div style={{ fontSize: 9, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.16em" }}>{x.l}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: x.c || NAVY, letterSpacing: "-0.02em", marginTop: 4, fontFeatureSettings: "'tnum'" }}>{x.v}</div>
                  {x.sub && <div style={{ fontSize: 10, color: slate[500], marginTop: 2 }}>{x.sub}</div>}
                </div>
              ))}
            </div>
          </Card>

          <Card title="Préflight DRUIDES" icon={I.shield} action={
            <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 10, fontWeight: 700, color: SUCCESS, textTransform: "uppercase", letterSpacing: "0.14em" }}>
              <span style={{ width: 6, height: 6, borderRadius: 999, background: SUCCESS }}/>15/15 OK
            </span>
          }>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                { l: "FINESS établissement", ok: true },
                { l: "Format IPP", ok: true },
                { l: "Cohérence DDN", ok: true },
                { l: "Codes CIM-10 valides", ok: true },
                { l: "Chaînage VID/ANO-HOSP", ok: true },
                { l: "Mode légal renseigné", ok: true },
              ].map((c, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 9, fontSize: 12 }}>
                  <span style={{ width: 16, height: 16, borderRadius: 4, background: SUCCESS, color: "white", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon size={11} color="white" stroke={3} d={<path d="M20 6 9 17l-5-5"/>}/>
                  </span>
                  <span style={{ color: slate[700], flex: 1 }}>{c.l}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Recent exports */}
      <div style={{ marginTop: 18 }}>
        <Card title="Exports récents" icon={I.history} padding={0}>
          {exports.map((e, i) => (
            <div key={i} style={{
              padding: "14px 20px", borderBottom: i < exports.length - 1 ? `1px solid ${slate[100]}` : "none",
              display: "grid", gridTemplateColumns: "auto 1fr auto auto auto auto", alignItems: "center", gap: 16,
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: e.status === "archived" ? slate[100] : "rgba(0,137,123,0.1)",
                color: e.status === "archived" ? slate[400] : TEAL,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>{I.file}</div>
              <div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color: NAVY, fontSize: 13 }}>{e.n}</div>
                <div style={{ fontSize: 10, color: slate[500], marginTop: 2 }}>{e.when}</div>
              </div>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[600], fontWeight: 600 }}>
                {e.rows.toLocaleString("fr-FR")} lignes
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[600], fontWeight: 600 }}>
                {e.mb} Mo
              </span>
              <span style={{
                fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.14em",
                color: e.status === "archived" ? slate[400] : SUCCESS,
                display: "inline-flex", alignItems: "center", gap: 5,
              }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: e.status === "archived" ? slate[400] : SUCCESS }}/>
                {e.status === "archived" ? "Archivé" : "OK"}
              </span>
              <div style={{ display: "flex", gap: 6 }}>
                <Btn kind="ghost" sm icon={I.download}>Re-télécharger</Btn>
              </div>
            </div>
          ))}
        </Card>
      </div>
    </Shell>
  );
};

const Field = ({ label, hint, children }) => (
  <div>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
      <span style={{ fontSize: 10, fontWeight: 700, color: slate[600], textTransform: "uppercase", letterSpacing: "0.16em" }}>{label}</span>
      {hint && <span style={{ fontSize: 10, color: slate[400] }}>{hint}</span>}
    </div>
    {children}
  </div>
);

const Toggle = ({ label, desc, on }) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 12,
    padding: "10px 12px", border: `1px solid ${slate[200]}`, borderRadius: 8,
    background: "white",
  }}>
    <div style={{
      width: 32, height: 18, borderRadius: 999,
      background: on ? TEAL : slate[200],
      position: "relative", flexShrink: 0,
    }}>
      <div style={{
        width: 14, height: 14, borderRadius: 999, background: "white",
        position: "absolute", top: 2, left: on ? 16 : 2,
        boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
      }}/>
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, lineHeight: 1.2 }}>{label}</div>
      <div style={{ fontSize: 10, color: slate[500], marginTop: 2 }}>{desc}</div>
    </div>
  </div>
);

window.ScreenPilot = ScreenPilot;

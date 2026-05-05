/* CSV Import & Structure & Tutoriel screens */

const ScreenCsv = () => {
  const cols = ["IPP", "DDN", "Sexe", "Date_séjour", "Mode_entrée", "DP_CIM10", "Durée_j"];
  const rows = [
    ["P-840291", "1972-03-14", "F", "2025-08-12", "8", "F33.1", "12"],
    ["P-291847", "1958-11-02", "M", "2025-08-14", "8", "F20.0", "21"],
    ["P-118092", "1985-07-09", "F", "2025-08-15", "6", "F41.2", "5"],
    ["P-557102", "1965-02-28", "M", "2025-08-18", "8", "F32.2", "18"],
    ["P-672018", "1990-12-15", "F", "2025-08-20", "7", "F60.3", "9"],
    ["P-994412", "1948-06-21", "M", "2025-08-22", "8", "F03",   "31"],
    ["P-441207", "1979-04-30", "F", "2025-08-23", "6", "F31.4", "14"],
  ];

  return (
    <Shell active="csv" title="Import CSV" subtitle="Visualiseur de fichiers CSV externes">
      <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 14 }}>
        {/* Side */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Card title="Fichier" icon={I.file}>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, color: NAVY, lineHeight: 1.3 }}>
              extract_BIQuery_2025T3.csv
            </div>
            <div style={{ fontSize: 10, color: slate[500], marginTop: 4 }}>
              8 420 lignes · 1.2 Mo · UTF-8 BOM
            </div>
            <div style={{ height: 1, background: slate[100], margin: "12px 0" }}/>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                ["Séparateur", "; (point-virgule)"],
                ["Encodage", "UTF-8 BOM"],
                ["Décimales", ", (virgule)"],
                ["Date format", "AAAA-MM-JJ"],
              ].map(([k, v], i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                  <span style={{ color: slate[500] }}>{k}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", color: slate[700], fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 6 }}>
              <Btn kind="ghost" sm icon={I.upload}>Charger un autre CSV</Btn>
              <Btn kind="ghost" sm icon={I.download}>Exporter sélection</Btn>
            </div>
          </Card>

          <Card title="Filtres" icon={I.filter}>
            <Field label="Colonne">
              <select style={selectStyle}>
                <option>DP_CIM10</option><option>Sexe</option><option>Mode_entrée</option>
              </select>
            </Field>
            <div style={{ height: 12 }}/>
            <Field label="Valeur contient">
              <input style={inputStyle} placeholder="F33" defaultValue=""/>
            </Field>
            <div style={{ height: 12 }}/>
            <Btn kind="teal" sm icon={I.filter}>Appliquer</Btn>
          </Card>
        </div>

        {/* Table */}
        <Card title="Aperçu · 10 / 8 420" icon={I.table}
          action={<span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: slate[400] }}>page 1 / 843</span>}
          padding={0}
        >
          <div style={{ overflow: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr style={{ background: slate[50], borderBottom: `1px solid ${slate[200]}` }}>
                  <th style={thStyle}>#</th>
                  {cols.map((c, i) => <th key={i} style={thStyle}>{c}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${slate[100]}` }}>
                    <td style={{ ...tdStyle, color: slate[400], width: 36 }}>{i + 1}</td>
                    {r.map((cell, k) => (
                      <td key={k} style={{
                        ...tdStyle,
                        fontFamily: k === 0 || k === 1 || k === 5 ? "'JetBrains Mono', monospace" : "inherit",
                        color: k === 0 ? NAVY : slate[700],
                        fontWeight: k === 0 ? 700 : 500,
                      }}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{
            padding: "12px 18px", borderTop: `1px solid ${slate[100]}`, background: slate[50],
            display: "flex", justifyContent: "space-between", alignItems: "center",
            fontSize: 11, color: slate[500],
          }}>
            <span>Affichage : 10 lignes par page</span>
            <div style={{ display: "flex", gap: 6 }}>
              <Btn kind="ghost" sm>← Préc.</Btn>
              <Btn kind="ghost" sm>Suiv. →</Btn>
            </div>
          </div>
        </Card>
      </div>
    </Shell>
  );
};

const thStyle = {
  textAlign: "left", padding: "10px 14px",
  fontSize: 9, fontWeight: 700, color: slate[500],
  textTransform: "uppercase", letterSpacing: "0.16em",
};
const tdStyle = { padding: "10px 14px", fontSize: 12 };
const selectStyle = { width: "100%", padding: "8px 10px", border: `1px solid ${slate[200]}`, borderRadius: 6, fontSize: 12, fontFamily: "inherit", background: "white", color: slate[700] };
const inputStyle = { width: "100%", padding: "8px 10px", border: `1px solid ${slate[200]}`, borderRadius: 6, fontSize: 12, fontFamily: "'JetBrains Mono', monospace", background: "white", color: slate[700], outline: "none" };

// ────────────────────────────────────────────────────────────
const ScreenStructure = () => {
  const tree = [
    { type: "pole", label: "Pôle 94G16 — Adolescents", count: 4, dormant: 0,
      children: [
        { type: "secteur", label: "Secteur Vitry-Thiais", count: 3, children: [
          { type: "um", code: "9401421", label: "UM Adolescents Hospit.", active: true, ipp: 142 },
          { type: "um", code: "9401422", label: "UM CMP Vitry", active: true, ipp: 318 },
          { type: "um", code: "9401423", label: "UM HDJ Thiais", active: true, ipp: 87 },
        ]},
        { type: "secteur", label: "Secteur Choisy", count: 1, children: [
          { type: "um", code: "9401424", label: "UM CMP Choisy", active: true, ipp: 211 },
        ]},
      ]
    },
    { type: "pole", label: "Pôle 94G17 — Adultes", count: 6, dormant: 1,
      children: [
        { type: "secteur", label: "Secteur Villejuif", count: 4, children: [
          { type: "um", code: "9401501", label: "UM Hospit. Complète", active: true, ipp: 412 },
          { type: "um", code: "9401502", label: "UM CMP Villejuif", active: true, ipp: 605 },
          { type: "um", code: "9401503", label: "UM HDJ Villejuif", active: true, ipp: 142 },
          { type: "um", code: "9401504", label: "UM Crise & Liaison", active: false, ipp: 0 },
        ]},
      ]
    },
  ];

  return (
    <Shell active="structure" title="Structure" subtitle="Pôle / Secteur / UM — Analyse d'activité">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 14 }}>
        {/* Tree */}
        <Card title="Arborescence GHT Sud Paris" icon={I.branch}
          action={<div style={{ display: "flex", gap: 6 }}>
            <Btn kind="ghost" sm icon={I.download}>Export PDF</Btn>
            <Btn kind="ghost" sm icon={I.expand}>Plein écran</Btn>
          </div>} padding={0}>
          <div style={{ padding: 14 }}>
            {tree.map((p, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "10px 12px", background: slate[50], borderRadius: 8,
                  border: `1px solid ${slate[100]}`,
                }}>
                  <span style={{ color: NAVY, display: "flex" }}>{I.chevDown}</span>
                  <div style={{
                    width: 24, height: 24, borderRadius: 6,
                    background: NAVY, color: "white",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 9, fontWeight: 800, letterSpacing: "0.08em",
                  }}>P</div>
                  <span style={{ fontWeight: 700, color: NAVY, fontSize: 13, flex: 1 }}>{p.label}</span>
                  <span style={{ fontSize: 10, color: slate[500], fontFamily: "'JetBrains Mono', monospace" }}>
                    {p.count} UM
                  </span>
                  {p.dormant > 0 && (
                    <span style={{
                      display: "inline-flex", alignItems: "center", gap: 4,
                      background: "#FEE2E2", color: ERROR, padding: "3px 8px", borderRadius: 999,
                      fontSize: 10, fontWeight: 700,
                    }}>
                      <span style={{ width: 5, height: 5, borderRadius: 999, background: ERROR }}/>
                      {p.dormant} dormante
                    </span>
                  )}
                </div>
                {p.children.map((s, k) => (
                  <div key={k} style={{ marginLeft: 28, marginTop: 8 }}>
                    <div style={{
                      display: "flex", alignItems: "center", gap: 9,
                      padding: "8px 12px", background: "white",
                      border: `1px solid ${slate[100]}`, borderRadius: 8, marginBottom: 6,
                    }}>
                      <span style={{ color: slate[500], display: "flex" }}>{I.chevDown}</span>
                      <div style={{
                        width: 22, height: 22, borderRadius: 5, background: TEAL,
                        color: "white", display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 9, fontWeight: 800,
                      }}>S</div>
                      <span style={{ fontWeight: 700, color: slate[700], fontSize: 12, flex: 1 }}>{s.label}</span>
                      <span style={{ fontSize: 10, color: slate[400], fontFamily: "'JetBrains Mono', monospace" }}>
                        {s.count} UM
                      </span>
                    </div>
                    {s.children.map((u, j) => (
                      <div key={j} style={{
                        marginLeft: 28, marginBottom: 4,
                        display: "grid", gridTemplateColumns: "auto 1fr auto auto",
                        gap: 10, alignItems: "center", padding: "8px 12px",
                        background: u.active ? "white" : "rgba(225,29,72,0.04)",
                        border: `1px solid ${u.active ? slate[100] : "rgba(225,29,72,0.2)"}`,
                        borderRadius: 8,
                      }}>
                        <div style={{
                          width: 20, height: 20, borderRadius: 4,
                          background: u.active ? slate[100] : "#FEE2E2",
                          color: u.active ? slate[500] : ERROR,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 9, fontWeight: 800,
                        }}>U</div>
                        <div>
                          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color: u.active ? NAVY : ERROR, fontSize: 11 }}>{u.code}</span>
                          <span style={{ marginLeft: 9, fontSize: 12, color: slate[700] }}>{u.label}</span>
                        </div>
                        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 700, color: u.active ? TEAL : ERROR }}>
                          {u.ipp} IPP
                        </span>
                        <span style={{
                          fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.14em",
                          color: u.active ? SUCCESS : ERROR,
                        }}>
                          {u.active ? "Active" : "Dormante"}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Card>

        {/* Side: drop zone + KPIs */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Card title="Analyse d'activité par UM" icon={I.upload}>
            <div style={{
              border: `1.5px dashed ${slate[300]}`, borderRadius: 10,
              padding: "18px 14px", textAlign: "center", background: slate[50],
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10, background: "white",
                border: `1px solid ${slate[200]}`, margin: "0 auto 10px",
                display: "flex", alignItems: "center", justifyContent: "center", color: TEAL,
              }}>{I.upload}</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, marginBottom: 3 }}>
                Déposer RPS / RAA
              </div>
              <div style={{ fontSize: 10, color: slate[500] }}>
                Détection des UM dormantes par parsing des codes
              </div>
            </div>
            <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
              <Btn kind="ghost" sm icon={I.upload}>Parcourir</Btn>
              <Btn kind="teal" sm icon={I.zap}>Analyser</Btn>
            </div>
          </Card>

          <Card title="Synthèse" icon={I.pulse}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { l: "Pôles", v: 2, c: NAVY },
                { l: "Secteurs", v: 3, c: TEAL },
                { l: "Unités Médicales", v: 10, c: GOLD },
                { l: "UM dormantes", v: 1, c: ERROR },
                { l: "IPP couverts", v: "1 937", c: NAVY },
              ].map((x, i) => (
                <div key={i} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "baseline",
                  padding: "8px 12px", background: slate[50], borderRadius: 6, border: `1px solid ${slate[100]}`,
                }}>
                  <span style={{ fontSize: 11, color: slate[600], fontWeight: 600 }}>{x.l}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 14, fontWeight: 800, color: x.c, fontFeatureSettings: "'tnum'" }}>{x.v}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </Shell>
  );
};

// ────────────────────────────────────────────────────────────
const ScreenTuto = () => {
  const steps = [
    { n: 1, t: "Importer les fichiers ATIH", d: "Glissez vos dossiers PMSI dans la zone Modo Files. Sentinel détecte automatiquement les 23 formats supportés (PSY, MCO, SSR, HAD, transversal).", icon: I.upload, done: true },
    { n: 2, t: "Lancer le scan & traitement", d: "Le moteur compile la matrice positionnelle, parse les fichiers en parallèle (ThreadPool) et construit le Master Patient Index.", icon: I.zap, done: true },
    { n: 3, t: "Résoudre les collisions", d: "Vue Identitovigilance : arbitrez les conflits IPP/DDN par fréquence majoritaire ou manuellement. La date pivot est réinjectée dans tout le batch.", icon: I.users, done: false, current: true },
    { n: 4, t: "Vérifier la structure UM", d: "Vue Structure : repérez les UM dormantes via parsing RPS/RAA. Exportez l'organigramme PDF pour validation pôle.", icon: I.branch, done: false },
    { n: 5, t: "Générer l'export e-PMSI", d: "Vue PMSI Pilot CSV : configurez le périmètre (trimestre, champs), validez le préflight DRUIDES (15 contrôles), exportez.", icon: I.download, done: false },
  ];

  return (
    <Shell active="tuto" title="Tutoriel d'utilisation" subtitle="Guide pas-à-pas Sentinel">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 14 }}>
        <div>
          <SectionHead eyebrow="Workflow standard" title="De l'ingestion à l'export e-PMSI"
            meta="5 étapes · ≈ 12 min par lot trimestriel"
          />

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {steps.map((s, i) => (
              <div key={i} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16,
                background: "white", border: `1px solid ${s.current ? NAVY : slate[200]}`,
                borderRadius: 12, padding: 16, alignItems: "flex-start",
                boxShadow: s.current ? "0 4px 14px -6px rgba(0,0,145,0.18)" : "0 1px 2px rgba(0,0,145,0.03)",
                position: "relative", overflow: "hidden",
              }}>
                {s.current && <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 3, background: NAVY }}/>}
                <div style={{
                  width: 44, height: 44, borderRadius: 10,
                  background: s.done ? "rgba(16,185,129,0.1)" : s.current ? NAVY : slate[50],
                  color: s.done ? SUCCESS : s.current ? "white" : slate[500],
                  border: `1px solid ${s.done ? "rgba(16,185,129,0.3)" : s.current ? NAVY : slate[200]}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {s.done ? <Icon size={20} color={SUCCESS} stroke={2.5} d={<path d="M20 6 9 17l-5-5"/>}/> : s.icon}
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                    <span style={{
                      fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 700,
                      color: slate[400], letterSpacing: "0.1em",
                    }}>ÉTAPE {String(s.n).padStart(2, "0")}</span>
                    {s.done && <span style={{
                      fontSize: 9, fontWeight: 700, color: SUCCESS, textTransform: "uppercase", letterSpacing: "0.16em",
                    }}>Terminé</span>}
                    {s.current && <span style={{
                      fontSize: 9, fontWeight: 700, color: NAVY, textTransform: "uppercase", letterSpacing: "0.16em",
                    }}>En cours</span>}
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: NAVY, letterSpacing: "-0.01em", marginBottom: 5 }}>
                    {s.t}
                  </div>
                  <div style={{ fontSize: 12, color: slate[600], lineHeight: 1.55, textWrap: "pretty" }}>
                    {s.d}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {s.current ? <Btn kind="primary" sm icon={I.arrow}>Continuer</Btn> : s.done ? <Btn kind="ghost" sm>Revoir</Btn> : <Btn kind="ghost" sm>Voir</Btn>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Side panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Card title="Progression" icon={I.pulse}>
            <div style={{
              fontSize: 36, fontWeight: 800, color: NAVY, letterSpacing: "-0.03em",
              fontFeatureSettings: "'tnum'", lineHeight: 1,
            }}>
              2<span style={{ color: slate[400], fontWeight: 600 }}>/5</span>
            </div>
            <div style={{ height: 6, background: slate[100], borderRadius: 999, marginTop: 10, overflow: "hidden" }}>
              <div style={{ width: "40%", height: "100%", background: TEAL }}/>
            </div>
            <div style={{ fontSize: 10, color: slate[500], marginTop: 8, textTransform: "uppercase", letterSpacing: "0.14em", fontWeight: 700 }}>
              Étape 3 en cours
            </div>
          </Card>

          <Card title="Ressources" icon={I.book}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { l: "Guide PDF · 38 pages", icon: I.file },
                { l: "Référentiel ATIH 2026", icon: I.database },
                { l: "Codes CIM-10 PSY", icon: I.book },
                { l: "Vidéo · démarrage rapide", icon: I.play },
              ].map((r, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "9px 12px", background: slate[50], borderRadius: 8,
                  border: `1px solid ${slate[100]}`, cursor: "pointer",
                }}>
                  <span style={{ color: TEAL, display: "flex" }}>{r.icon}</span>
                  <span style={{ flex: 1, fontSize: 12, color: slate[700], fontWeight: 600 }}>{r.l}</span>
                  <span style={{ color: slate[400], display: "flex" }}>{I.chevRight}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Raccourcis" icon={I.zap}>
            <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              {[
                ["Ctrl + 1", "Dashboard"],
                ["Ctrl + 2", "Modo Files"],
                ["Ctrl + 3", "IDV"],
                ["Ctrl + 4", "Pilot CSV"],
                ["Ctrl + K", "Recherche"],
              ].map(([k, v], i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11 }}>
                  <span style={{ color: slate[600] }}>{v}</span>
                  <kbd style={{
                    fontFamily: "'JetBrains Mono', monospace", fontSize: 10, fontWeight: 700,
                    background: slate[50], border: `1px solid ${slate[200]}`, borderRadius: 4,
                    padding: "2px 8px", color: NAVY,
                  }}>{k}</kbd>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </Shell>
  );
};

window.ScreenCsv = ScreenCsv;
window.ScreenStructure = ScreenStructure;
window.ScreenTuto = ScreenTuto;

/* Modo Files screen */
const ScreenModo = () => {
  const folders = [
    "C:\\PMSI\\Fondation_Vallee\\2025_T3",
    "C:\\PMSI\\Paul_Guiraud\\2025_T3",
    "\\\\NAS-DIM\\exports\\preprod_atih",
  ];
  const files = [
    { n: "RPS_2025T3.txt",       fmt: "RPS",      kind: "PSY",   kb: 4820, dir: "Fondation_Vallee\\2025_T3" },
    { n: "EDGAR_2025T3.txt",     fmt: "EDGAR",    kind: "PSY",   kb: 2104, dir: "Fondation_Vallee\\2025_T3" },
    { n: "RAA_2025T3.txt",       fmt: "RAA",      kind: "PSY",   kb: 1820, dir: "Fondation_Vallee\\2025_T3" },
    { n: "RPSA_2025T3.txt",      fmt: "RPSA",    kind: "PSY",   kb: 1244, dir: "Paul_Guiraud\\2025_T3" },
    { n: "VID-HOSP_2025T3.txt",  fmt: "VID-HOSP", kind: "TRANS", kb:  642, dir: "Paul_Guiraud\\2025_T3" },
    { n: "ANO-HOSP_2025T3.txt",  fmt: "ANO-HOSP", kind: "TRANS", kb:  584, dir: "Paul_Guiraud\\2025_T3" },
    { n: "RHS_2025T3.txt",       fmt: "RHS",      kind: "SSR",   kb:  982, dir: "preprod_atih" },
    { n: "RPSS_2025T3.txt",      fmt: "RPSS",     kind: "HAD",   kb:  428, dir: "preprod_atih" },
    { n: "FICHSUP-PSY.txt",      fmt: "FICHSUP",  kind: "PSY",   kb:  208, dir: "Fondation_Vallee\\2025_T3" },
  ];

  return (
    <Shell active="modo" title="Modo Files" subtitle="Ingestion & traitement batch" badges={{ modo: 9, idv: 12 }}>
      {/* drop zone */}
      <div style={{
        background: "white", border: `1.5px dashed ${slate[300]}`,
        borderRadius: 14, padding: "32px 24px", textAlign: "center",
        marginBottom: 20, position: "relative",
      }}>
        <div style={{
          width: 56, height: 56, background: slate[50], border: `1px solid ${slate[200]}`,
          borderRadius: 14, margin: "0 auto 14px",
          display: "flex", alignItems: "center", justifyContent: "center", color: TEAL,
        }}>
          <Icon size={26} color={TEAL} d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>}/>
        </div>
        <div style={{ fontSize: 18, fontWeight: 800, color: NAVY, letterSpacing: "-0.015em", marginBottom: 4 }}>
          Déposer les fichiers PMSI
        </div>
        <div style={{ fontSize: 12, color: slate[500], marginBottom: 18 }}>
          Glissez vos dossiers ici — fichiers et sous-dossiers inclus
        </div>
        <div style={{ display: "flex", justifyContent: "center", gap: 10 }}>
          <Btn kind="primary" icon={I.plus}>Ajouter dossier</Btn>
          <Btn kind="teal" icon={I.zap}>Scanner &amp; Traiter</Btn>
        </div>
      </div>

      {/* progress */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: slate[600], textTransform: "uppercase", letterSpacing: "0.16em" }}>
            Construction MPI
          </span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: NAVY, fontWeight: 700 }}>
            68%
          </span>
        </div>
        <div style={{ height: 6, background: slate[100], borderRadius: 999, overflow: "hidden" }}>
          <div style={{ width: "68%", height: "100%", background: `linear-gradient(90deg, ${NAVY}, ${TEAL})`, borderRadius: 999 }}/>
        </div>
      </div>

      {/* folders */}
      <div style={{ marginBottom: 20 }}>
        <Card title="Dossiers surveillés" icon={I.folder}
          action={<span style={{ fontSize: 10, fontWeight: 700, color: ERROR, textTransform: "uppercase", letterSpacing: "0.16em", cursor: "pointer" }}>Vider</span>}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {folders.map((f, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10,
                background: slate[50], padding: "9px 14px", borderRadius: 8,
                border: `1px solid ${slate[100]}`,
              }}>
                <span style={{ color: NAVY, display: "flex" }}>{I.folder}</span>
                <span style={{ flex: 1, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[700] }}>
                  {f}
                </span>
                <span style={{ fontSize: 9, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.16em" }}>
                  #{i + 1}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* files grid */}
      <div>
        <SectionHead eyebrow="Lot courant" title="Fichiers détectés"
          meta={`${files.length} fichiers · 12.8 Mo total`}
          action={<div style={{ display: "flex", gap: 8 }}>
            <Btn kind="ghost" sm icon={I.filter}>Filtrer</Btn>
            <Btn kind="ghost" sm icon={I.eye}>Voir tous</Btn>
          </div>}
        />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {files.map((f, i) => (
            <div key={i} style={{
              background: "white", border: `1px solid ${slate[200]}`,
              borderRadius: 10, padding: 14,
              boxShadow: "0 1px 2px rgba(0,0,145,0.03)", cursor: "pointer",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <FmtBadge label={f.fmt} kind={f.kind}/>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: slate[400] }}>
                  {f.kb.toLocaleString("fr-FR")} KB
                </span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, letterSpacing: "-0.01em", lineHeight: 1.2 }}>
                {f.n}
              </div>
              <div style={{ fontSize: 10, color: slate[400], fontFamily: "'JetBrains Mono', monospace", marginTop: 5 }}>
                {f.dir}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Shell>
  );
};
window.ScreenModo = ScreenModo;

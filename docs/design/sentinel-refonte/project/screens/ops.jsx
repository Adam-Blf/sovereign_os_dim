/* Section 4 · Sécurité, conformité, gouvernance, ops */

// ─── #31 RGPD command center ────────────────────────────────
const ScreenRgpd = () => (
  <Shell active="rgpd" title="RGPD command center" subtitle="Registre traitements · DPIA · droits patients"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Conformité art. 30 RGPD"
      title="14 traitements actifs · 0 violation ouverte"
      action={<Btn kind="teal" icon={I.shield}>Audit complet</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 18 }}>
      <Kpi label="Traitements" value="14" sub="100 % documentés" accent={SUCCESS}/>
      <Kpi label="DPIA" value="6 / 6" sub="À jour < 12 mois" accent={SUCCESS}/>
      <Kpi label="Demandes patient" value="3" sub="2 en cours · 1 < 48 h" accent={WARNING}/>
      <Kpi label="Violations" value="0" sub="Depuis 412 jours" accent={SUCCESS}/>
    </div>

    <Card title="Registre des traitements" icon={I.book}>
      {[
        { code: "T-001", lib: "Codage médical PMSI psychiatrie", base: "Art. 9.2.h", dpo: "OK", risk: "low" },
        { code: "T-003", lib: "Identitovigilance MPI / INS", base: "Art. 9.2.h", dpo: "OK", risk: "low" },
        { code: "T-007", lib: "Recherche clinique anonymisée", base: "Art. 9.2.j", dpo: "OK", risk: "med" },
        { code: "T-011", lib: "Cluster patients UMAP+HDBSCAN", base: "Art. 9.2.h", dpo: "Review", risk: "med" },
      ].map((t, i) => (
        <div key={t.code} style={{
          display: "grid", gridTemplateColumns: "70px 1fr 110px 80px 90px",
          gap: 14, alignItems: "center",
          padding: "12px 0", borderBottom: i < 3 ? `1px solid ${slate[100]}` : "none",
        }}>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 700, color: NAVY }}>{t.code}</span>
          <span style={{ fontSize: 13, color: slate[800], fontWeight: 600 }}>{t.lib}</span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: slate[600] }}>{t.base}</span>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6,
            background: t.dpo === "OK" ? "#ECFDF5" : "#FFFBEB",
            color: t.dpo === "OK" ? SUCCESS : WARNING, textAlign: "center",
          }}>{t.dpo}</span>
          <span style={{
            fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6,
            background: t.risk === "low" ? "#ECFDF5" : "#FFFBEB",
            color: t.risk === "low" ? SUCCESS : WARNING, textAlign: "center", textTransform: "uppercase", letterSpacing: "0.1em",
          }}>{t.risk === "low" ? "Faible" : "Moyen"}</span>
        </div>
      ))}
    </Card>
  </Shell>
);

// ─── #36 Audit chain · blockchain locale ─────────────────────
const ScreenAudit = () => (
  <Shell active="audit" title="Audit chain" subtitle="Journal append-only · hash SHA-256 chaîné"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Traçabilité totale"
      title="48 192 événements · 100 % vérifiés"
      meta="Genesis bloc · 2024-01-01"
      action={<Btn kind="ghost" icon={I.shield}>Vérifier l'intégrité</Btn>}
    />

    <Card title="Derniers événements" icon={I.activity}>
      {[
        { ts: "14:48:21", who: "dr.martin", act: "VALIDATE_DP", obj: "RSS-2025-M11-04421", hash: "f8a3c1…7b29" },
        { ts: "14:47:55", who: "dim.lead", act: "EXPORT_BATCH", obj: "Lot 2025-M11", hash: "a14c0e…3f88" },
        { ts: "14:46:12", who: "system", act: "MPI_REINDEX", obj: "11 247 IPP", hash: "c204fa…91d4" },
        { ts: "14:42:08", who: "audit.bot", act: "RGPD_CHECK", obj: "T-007", hash: "6e91a3…0c45" },
        { ts: "14:39:44", who: "dr.lambert", act: "MERGE_DOUBLON", obj: "IPP 882144 ↔ 901225", hash: "92f4d8…1a07" },
      ].map((e, i) => (
        <div key={i} style={{
          display: "grid", gridTemplateColumns: "80px 110px 140px 1fr 130px",
          gap: 14, alignItems: "center",
          padding: "10px 0", borderBottom: i < 4 ? `1px solid ${slate[100]}` : "none",
          fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
        }}>
          <span style={{ color: slate[500] }}>{e.ts}</span>
          <span style={{ fontWeight: 700, color: NAVY }}>{e.who}</span>
          <span style={{
            display: "inline-block", padding: "3px 8px", background: "#EEF2FF",
            borderRadius: 6, color: "#4338CA", fontWeight: 700, fontSize: 10, textAlign: "center",
          }}>{e.act}</span>
          <span style={{ color: slate[700] }}>{e.obj}</span>
          <span style={{ color: slate[400] }}>0x{e.hash}</span>
        </div>
      ))}
    </Card>
  </Shell>
);

// ─── #43 Workflow inspiré de Notion ─────────────────────────
const ScreenWorkflow = () => (
  <Shell active="workflow" title="Workflows DIM" subtitle="Kanban · campagnes & tâches récurrentes"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Pilotage équipe"
      title="Campagne « Clôture M11 »"
      meta="14 tâches · 6 contributeurs"
      action={<Btn kind="teal" icon={I.plus}>Nouvelle tâche</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
      {[
        { col: "Backlog", c: slate[400], items: [
          { t: "Mettre à jour matrice CIM-10 v2026", a: "DM" },
          { t: "Audit semestriel RGPD", a: "JL" },
        ]},
        { col: "À faire", c: NAVY, items: [
          { t: "Cleanup MPI · doublons IPP", a: "MD", p: "high" },
          { t: "Validation RPS suspects M11", a: "DM" },
          { t: "Export ATIH preview", a: "JL" },
        ]},
        { col: "En cours", c: TEAL, items: [
          { t: "Clôture comptable M11", a: "MD", p: "high" },
          { t: "DPIA traitement T-007", a: "DPO" },
        ]},
        { col: "Validé", c: SUCCESS, items: [
          { t: "Onboarding Dr Lambert", a: "RH" },
          { t: "Test charge MPI 50k", a: "OPS" },
          { t: "MAJ tokens design", a: "UX" },
        ]},
      ].map(c => (
        <div key={c.col} style={{ background: slate[50], borderRadius: 12, padding: 12 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 8, height: 8, borderRadius: 999, background: c.c }}/>
              <span style={{ fontSize: 11, fontWeight: 700, color: slate[700], textTransform: "uppercase", letterSpacing: "0.13em" }}>{c.col}</span>
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: slate[500], background: "white", padding: "2px 8px", borderRadius: 999 }}>{c.items.length}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {c.items.map((it, i) => (
              <div key={i} style={{
                background: "white", border: `1px solid ${slate[200]}`, borderRadius: 8,
                padding: 10,
              }}>
                {it.p === "high" && (
                  <span style={{ fontSize: 9, fontWeight: 800, color: ERROR, letterSpacing: "0.1em", textTransform: "uppercase" }}>● Priorité haute</span>
                )}
                <div style={{ fontSize: 12, fontWeight: 600, color: slate[800], lineHeight: 1.4, marginTop: it.p ? 4 : 0 }}>{it.t}</div>
                <div style={{ marginTop: 8, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{
                    width: 22, height: 22, borderRadius: 999, background: NAVY, color: "white",
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    fontSize: 9, fontWeight: 800, letterSpacing: "0.05em",
                  }}>{it.a}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </Shell>
);

// ─── #50 Health monitor / Ops ────────────────────────────────
const ScreenHealth = () => (
  <Shell active="health" title="Health monitor" subtitle="Métriques système · 30 dernières minutes"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Ops · 100 % local"
      title="Tous services opérationnels"
      meta="Uptime · 47 j 12 h · last incident · 2025-10-04"
      action={<Btn kind="ghost" icon={I.refresh}>Actualiser</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 18 }}>
      {[
        { l: "API REST", v: "98 ms", s: "p99", color: SUCCESS },
        { l: "Ollama LLM", v: "1,4 s", s: "median", color: SUCCESS },
        { l: "Postgres", v: "12 ms", s: "queries", color: SUCCESS },
        { l: "ATIH push", v: "OK", s: "last 14 min", color: SUCCESS },
      ].map(s => (
        <Kpi key={s.l} label={s.l} value={s.v} sub={s.s} accent={s.color}/>
      ))}
    </div>

    <Card title="Latence API · 30 min glissantes (ms)" icon={I.pulse}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 140, padding: "10px 0" }}>
        {Array.from({ length: 60 }).map((_, i) => {
          const v = 40 + Math.sin(i / 4) * 20 + Math.random() * 30;
          const spike = i === 42;
          const h = (v / 120) * 100;
          return (
            <div key={i} style={{
              flex: 1, height: spike ? "92%" : `${h}%`,
              background: spike ? WARNING : TEAL,
              borderRadius: "2px 2px 0 0", opacity: spike ? 1 : 0.7,
            }}/>
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", borderTop: `1px solid ${slate[100]}`, paddingTop: 10, marginTop: 6, fontSize: 10, color: slate[500], fontFamily: "'JetBrains Mono', monospace" }}>
        <span>−30 min</span><span>−20</span><span>−10</span><span>maintenant</span>
      </div>
    </Card>
  </Shell>
);

Object.assign(window, {
  ScreenRgpd, ScreenAudit, ScreenWorkflow, ScreenHealth,
});

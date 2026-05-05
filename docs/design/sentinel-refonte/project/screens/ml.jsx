/* Section 2 · ML / IA local */

// ─── #11 CimSuggester live · LLM Ollama ─────────────────────
const ScreenCimSuggester = () => (
  <Shell active="cim" title="CimSuggester live" subtitle="LLM local Ollama · Suggestion DP à partir DAS+actes"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Codage assisté · 100 % local"
      title="RSS 2025-M11-04421 · M. D. (47 ans)"
      meta="Ollama llama3.1:8b · 14 ms / token"
      action={<Btn kind="teal" icon={I.check}>Valider DP suggéré</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 14 }}>
      <Card title="Contexte saisi" icon={I.file}>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em", marginBottom: 6 }}>Diagnostics associés</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {["F32.1 · Épisode dépressif moyen", "F41.1 · Anxiété généralisée", "Z63.0 · Difficulté conjugale"].map(d => (
              <span key={d} style={{
                padding: "5px 10px", background: slate[50], border: `1px solid ${slate[200]}`,
                borderRadius: 6, fontSize: 11, fontWeight: 600, color: slate[700],
                fontFamily: "'JetBrains Mono', monospace",
              }}>{d}</span>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em", marginBottom: 6 }}>Actes</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {["YYYY048 · Entretien individuel", "YYYY127 · Thérapie familiale", "ZZZZ010 · Prescription"].map(a => (
              <span key={a} style={{
                padding: "5px 10px", background: "#EEF2FF", border: `1px solid #C7D2FE`,
                borderRadius: 6, fontSize: 11, fontWeight: 600, color: "#4338CA",
                fontFamily: "'JetBrains Mono', monospace",
              }}>{a}</span>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em", marginBottom: 6 }}>Note clinique (anonymisée)</div>
          <div style={{
            padding: 14, background: slate[50], borderLeft: `3px solid ${TEAL}`,
            borderRadius: "0 8px 8px 0", fontSize: 12, color: slate[700], lineHeight: 1.55, fontStyle: "italic",
          }}>
            "Patient suivi depuis 8 mois en CMP. Décompensation anxio-dépressive sur fond
            de séparation. Idéations passives sans projet. Adhésion au suivi correcte,
            réponse partielle aux ISRS. Pas d'antécédent psychotique."
          </div>
        </div>
      </Card>

      <Card title="DP suggérés · Top 3" icon={I.zap}>
        {[
          { code: "F33.1", lib: "Trouble dépressif récurrent · épisode actuel moyen", conf: 87, gain: "1 470 €", best: true },
          { code: "F32.2", lib: "Épisode dépressif sévère sans symptômes psychotiques", conf: 9, gain: "1 670 €", best: false },
          { code: "F32.1", lib: "Épisode dépressif moyen", conf: 4, gain: "1 240 €", best: false },
        ].map((s, i) => (
          <div key={s.code} style={{
            padding: 14, marginBottom: i < 2 ? 10 : 0,
            background: s.best ? "#F0FDF4" : "white",
            border: `1px solid ${s.best ? "#86EFAC" : slate[200]}`,
            borderRadius: 10, position: "relative",
          }}>
            {s.best && (
              <span style={{
                position: "absolute", top: 10, right: 10,
                padding: "3px 8px", background: SUCCESS, color: "white",
                borderRadius: 999, fontSize: 9, fontWeight: 800, letterSpacing: "0.1em",
              }}>RECOMMANDÉ</span>
            )}
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <span style={{
                fontFamily: "'JetBrains Mono', monospace", fontSize: 16, fontWeight: 800,
                color: s.best ? SUCCESS : NAVY,
              }}>{s.code}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color: slate[500] }}>conf. {s.conf}%</span>
            </div>
            <div style={{ fontSize: 12, color: slate[700], marginBottom: 8 }}>{s.lib}</div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ flex: 1, height: 4, background: slate[100], borderRadius: 999, marginRight: 12, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${s.conf}%`, background: s.best ? SUCCESS : slate[400], borderRadius: 999 }}/>
              </div>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 700, color: GOLD }}>
                T2A · {s.gain}
              </span>
            </div>
          </div>
        ))}
      </Card>
    </div>
  </Shell>
);

// ─── #14 Prédicteur DMS · LSTM ──────────────────────────────
const ScreenLstm = () => (
  <Shell active="lstm" title="Prédicteur DMS" subtitle="LSTM · estimation durée séjour à l'admission"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Anticipation capacité"
      title="42 admissions du jour · prédiction live"
      meta="Modèle v2.4 · MAE 1,8 jour · 100 % local"
    />

    <Card title="Distribution prédite · DMS par patient (jours)" icon={I.pulse}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 180, padding: "12px 0", marginBottom: 10 }}>
        {[2, 4, 7, 11, 14, 12, 9, 7, 5, 3, 2, 1, 1].map((v, i) => {
          const pct = (v / 14) * 100;
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <div style={{
                width: "100%", height: `${pct}%`,
                background: i === 4 ? NAVY : i >= 3 && i <= 5 ? TEAL : slate[300],
                borderRadius: "3px 3px 0 0",
              }}/>
              <span style={{ fontSize: 9, color: slate[500], fontWeight: 600 }}>{i + 1}</span>
            </div>
          );
        })}
      </div>
      <div style={{ borderTop: `1px solid ${slate[100]}`, paddingTop: 12, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
        {[
          { l: "DMS médiane", v: "5,2 j" },
          { l: "P75", v: "8,1 j" },
          { l: "Sorties J+7", v: "67 %" },
          { l: "Lits libérés J+3", v: "18" },
        ].map(s => (
          <div key={s.l}>
            <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em" }}>{s.l}</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: NAVY, fontFamily: "'JetBrains Mono', monospace", marginTop: 4, letterSpacing: "-0.02em" }}>{s.v}</div>
          </div>
        ))}
      </div>
    </Card>
  </Shell>
);

// ─── #15 Clustering UMAP+HDBSCAN ────────────────────────────
const ScreenClustering = () => (
  <Shell active="cluster" title="Clustering patients" subtitle="UMAP + HDBSCAN sur le MPI"
         badges={{ modo: 6, idv: 14 }}>
    <SectionHead
      eyebrow="Profils types · 14 882 patients"
      title="6 clusters identifiés · stabilité 0,82"
      action={<Btn icon={I.refresh}>Recalculer</Btn>}
    />

    <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 14 }}>
      <Card title="Projection UMAP 2D" icon={I.microscope} padding={0}>
        <div style={{ position: "relative", height: 380, background: slate[50], overflow: "hidden" }}>
          {[
            { c: NAVY,  x: 25, y: 30, r: 60, n: "Cluster 1 · Hospi longue" },
            { c: TEAL,  x: 70, y: 25, r: 50, n: "Cluster 2 · Ambu fréquent" },
            { c: GOLD,  x: 30, y: 70, r: 45, n: "Cluster 3 · Pédopsy" },
            { c: ERROR, x: 75, y: 65, r: 35, n: "Cluster 4 · Crise" },
            { c: "#7C3AED", x: 50, y: 45, r: 40, n: "Cluster 5 · Précarité" },
            { c: "#0EA5E9", x: 60, y: 80, r: 25, n: "Cluster 6 · Adolescents" },
          ].map((c, i) => (
            <div key={i} style={{
              position: "absolute", left: `${c.x}%`, top: `${c.y}%`,
              width: c.r, height: c.r, transform: "translate(-50%, -50%)",
              borderRadius: 999, background: c.c, opacity: 0.18,
              border: `2px solid ${c.c}`,
            }}/>
          ))}
          {/* dots */}
          {Array.from({ length: 200 }).map((_, i) => {
            const cx = [25, 70, 30, 75, 50, 60][i % 6];
            const cy = [30, 25, 70, 65, 45, 80][i % 6];
            const colors = [NAVY, TEAL, GOLD, ERROR, "#7C3AED", "#0EA5E9"];
            const x = cx + (Math.random() - 0.5) * 18;
            const y = cy + (Math.random() - 0.5) * 18;
            return (
              <div key={i} style={{
                position: "absolute", left: `${x}%`, top: `${y}%`,
                width: 4, height: 4, borderRadius: 999, background: colors[i % 6], opacity: 0.7,
              }}/>
            );
          })}
        </div>
      </Card>

      <Card title="Clusters" icon={I.users}>
        {[
          { c: NAVY, n: "Hospi longue", count: 1842, pct: 12.4 },
          { c: TEAL, n: "Ambu fréquent", count: 4221, pct: 28.3 },
          { c: GOLD, n: "Pédopsy", count: 2104, pct: 14.1 },
          { c: ERROR, n: "Crise / urgence", count: 1452, pct: 9.8 },
          { c: "#7C3AED", n: "Précarité sociale", count: 3221, pct: 21.6 },
          { c: "#0EA5E9", n: "Adolescents", count: 2042, pct: 13.8 },
        ].map((c, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "10px 0", borderBottom: i < 5 ? `1px solid ${slate[100]}` : "none",
          }}>
            <span style={{ width: 10, height: 10, borderRadius: 999, background: c.c, flexShrink: 0 }}/>
            <span style={{ flex: 1, fontSize: 12, fontWeight: 600, color: slate[800] }}>{c.n}</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 700, color: NAVY }}>
              {c.count.toLocaleString("fr")}
            </span>
            <span style={{ fontSize: 11, color: slate[500], fontWeight: 600, width: 44, textAlign: "right" }}>
              {c.pct}%
            </span>
          </div>
        ))}
      </Card>
    </div>
  </Shell>
);

Object.assign(window, {
  ScreenCimSuggester, ScreenLstm, ScreenClustering,
});

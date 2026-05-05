/* Boot screen */
const ScreenBoot = () => (
  <div style={{
    width: 1440, height: 900, background: slate[950],
    display: "flex", alignItems: "center", justifyContent: "center",
    fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
    color: "white", borderRadius: 12, overflow: "hidden",
    boxShadow: "0 24px 60px -20px rgba(15,23,42,0.18)",
    position: "relative",
    border: `1px solid ${slate[200]}`,
  }}>
    {/* subtle grid */}
    <div style={{
      position: "absolute", inset: 0, opacity: 0.04,
      backgroundImage: `linear-gradient(${slate[400]} 1px, transparent 1px),
                        linear-gradient(90deg, ${slate[400]} 1px, transparent 1px)`,
      backgroundSize: "32px 32px",
    }}/>
    <style>{`@keyframes blink { 50% { opacity: 0 } }`}</style>
    <div style={{ width: 540, textAlign: "center", position: "relative", zIndex: 2 }}>
      <div style={{ position: "relative", display: "inline-block", marginBottom: 28 }}>
        <div style={{
          width: 88, height: 88, background: "white", borderRadius: 22,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 24px 60px -10px rgba(0,0,145,0.5)",
        }}>
          <Icon size={44} color={NAVY} stroke={2}
            d={<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></>} />
        </div>
        <div style={{
          position: "absolute", bottom: -6, right: -6, width: 28, height: 28,
          background: SUCCESS, borderRadius: 999,
          display: "flex", alignItems: "center", justifyContent: "center",
          border: `4px solid ${slate[950]}`,
        }}>
          <Icon size={12} color="white" stroke={2.5}
            d={<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>}/>
        </div>
      </div>

      <div style={{ fontSize: 10, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.28em", marginBottom: 12, opacity: 0.85 }}>
        Station DIM · GHT Sud Paris
      </div>
      <div style={{ fontSize: 44, fontWeight: 800, letterSpacing: "-0.025em", lineHeight: 1, marginBottom: 12 }}>
        Sentinel
      </div>
      <div style={{ fontSize: 13, color: "#a5b4fc", opacity: 0.7, marginBottom: 44, fontWeight: 500 }}>
        Traitement local des fichiers ATIH · 100 % offline · RGPD-safe
      </div>

      <div style={{ height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 999, overflow: "hidden", marginBottom: 16 }}>
        <div style={{ width: "72%", height: "100%", background: TEAL, boxShadow: `0 0 16px ${TEAL}` }}/>
      </div>
      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: "rgba(165,180,252,0.55)", textTransform: "uppercase", letterSpacing: "0.25em", height: 16, marginBottom: 28 }}>
        Calibration MPI &amp; détection collisions…
      </div>

      {/* Boot log */}
      <div style={{
        textAlign: "left", background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10,
        padding: "14px 18px", fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11, lineHeight: 1.7, color: "rgba(165,180,252,0.7)",
      }}>
        {[
          { s: "OK",   c: SUCCESS, t: "Initialisation moteur ATIH · v36.0" },
          { s: "OK",   c: SUCCESS, t: "Compilation 23 patterns regex (PSY/MCO/SSR/HAD/TRANS)" },
          { s: "OK",   c: SUCCESS, t: "Activation ThreadPoolExecutor · 8 workers" },
          { s: "OK",   c: SUCCESS, t: "Chargement matrice positionnelle stricte" },
          { s: "WARN", c: WARNING, t: "12 collisions IPP/DDN détectées dans le batch 2025-T3" },
          { s: "RUN",  c: TEAL,    t: "Calibration MPI · 11 247 IPP indexés…" },
        ].map((l, i) => (
          <div key={i} style={{ display: "flex", gap: 10 }}>
            <span style={{ color: "rgba(255,255,255,0.25)", width: 56 }}>14:32:0{i}</span>
            <span style={{ color: l.c, fontWeight: 700, width: 44 }}>[{l.s}]</span>
            <span style={{ flex: 1 }}>{l.t}</span>
          </div>
        ))}
        <div style={{ display: "flex", gap: 10, color: TEAL }}>
          <span style={{ color: "rgba(255,255,255,0.25)", width: 56 }}>14:32:06</span>
          <span style={{ width: 44 }}>›</span>
          <span style={{ flex: 1 }}>
            sentinel <span style={{ background: TEAL, color: slate[950], padding: "0 4px", marginLeft: 2, animation: "blink 1s steps(2) infinite" }}>&nbsp;</span>
          </span>
        </div>
      </div>
    </div>
  </div>
);

window.ScreenBoot = ScreenBoot;

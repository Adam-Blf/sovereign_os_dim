/* Shared design primitives for Sentinel screens */

const NAVY = "#000091";
const NAVY_DARK = "#00006B";
const TEAL = "#00897B";
const GOLD = "#D4A437";
const ERROR = "#E11D48";
const SUCCESS = "#10B981";
const WARNING = "#F59E0B";

const slate = {
  50: "#F8FAFC", 100: "#F1F5F9", 200: "#E2E8F0", 300: "#CBD5E1",
  400: "#94A3B8", 500: "#64748B", 600: "#475569", 700: "#334155",
  800: "#1E293B", 900: "#0F172A", 950: "#020617",
};

// ────────────────────────────────────────────────────────────
// Lucide-style icons (only the ones we actually use, drawn as
// simple stroked SVGs — no fancy artwork, just glyphs)
// ────────────────────────────────────────────────────────────
const Icon = ({ d, size = 18, stroke = 1.75, color = "currentColor", style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color}
       strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" style={style}>
    {d}
  </svg>
);
const I = {
  shield: <Icon d={<><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></>} />,
  layout: <Icon d={<><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></>} />,
  folders: <Icon d={<><path d="M20 17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3l2 3h7a2 2 0 0 1 2 2v1"/><path d="M2 8h20"/></>} />,
  users: <Icon d={<><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>} />,
  download: <Icon d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>} />,
  table: <Icon d={<><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/></>} />,
  branch: <Icon d={<><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></>} />,
  book: <Icon d={<><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></>} />,
  settings: <Icon d={<><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></>} />,
  upload: <Icon d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>} />,
  search: <Icon d={<><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>} />,
  alert: <Icon d={<><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>} />,
  check: <Icon d={<><path d="M20 6 9 17l-5-5"/></>} />,
  x: <Icon d={<><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>} />,
  file: <Icon d={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></>} />,
  folder: <Icon d={<><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></>} />,
  moon: <Icon d={<><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></>} />,
  power: <Icon d={<><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></>} />,
  zap: <Icon d={<><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></>} />,
  pulse: <Icon d={<><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></>} />,
  database: <Icon d={<><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></>} />,
  arrow: <Icon d={<><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>} />,
  arrowRight: <Icon d={<><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>} />,
  filter: <Icon d={<><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></>} />,
  fingerprint: <Icon d={<><path d="M2 12C2 6 6 2 12 2s10 4 10 10"/><path d="M5 19.5C5.5 18 6 15 6 12c0-.7.12-1.37.34-2"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M12 10c-1.5 0-2.5.5-3 2"/><path d="M9 22c.4-3 .8-6 .8-9"/><path d="M14 13.12c0 2.38 0 6.38-1 8.88"/></>} />,
  refresh: <Icon d={<><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></>} />,
  play: <Icon d={<><polygon points="5 3 19 12 5 21 5 3"/></>} />,
  pause: <Icon d={<><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></>} />,
  more: <Icon d={<><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></>} />,
  plus: <Icon d={<><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></>} />,
  chevDown: <Icon d={<><polyline points="6 9 12 15 18 9"/></>} />,
  chevRight: <Icon d={<><polyline points="9 18 15 12 9 6"/></>} />,
  expand: <Icon d={<><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></>} />,
  eye: <Icon d={<><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>} />,
  trash: <Icon d={<><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></>} />,
  send: <Icon d={<><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></>} />,
  cloud: <Icon d={<><path d="M16 16.99H8.5a4.5 4.5 0 0 1-.21-9 6 6 0 0 1 11.5 1.85"/><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/></>} />,
  history: <Icon d={<><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></>} />,
  microscope: <Icon d={<><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></>} />,
  activity: <Icon d={<><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></>} />,
  brain: <Icon d={<><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-1.04Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-1.04Z"/></>} />,
  globe: <Icon d={<><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></>} />,
};

// ────────────────────────────────────────────────────────────
// Layout shell (sidebar + topbar + viewport)
// ────────────────────────────────────────────────────────────
const Shell = ({ active, title, subtitle, children, badges = {} }) => {
  const navItems = [
    { group: "Contrôle", items: [
      { id: "dashboard", label: "Dashboard", icon: I.layout },
      { id: "cockpit", label: "Cockpit chef DIM", icon: I.pulse },
      { id: "health", label: "Health monitor", icon: I.activity },
    ]},
    { group: "Métier DIM", items: [
      { id: "ars", label: "Sentinel ARS", icon: I.shield, badge: 42, badgeColor: WARNING },
      { id: "cespa", label: "CeSPA / CATTG", icon: I.check },
      { id: "diff", label: "Diff lots mensuels", icon: I.branch },
    ]},
    { group: "ML & IA local", items: [
      { id: "cim", label: "CimSuggester", icon: I.brain },
      { id: "lstm", label: "Prédicteur DMS", icon: I.zap },
      { id: "cluster", label: "Clustering UMAP", icon: I.microscope },
    ]},
    { group: "Données & Analytics", items: [
      { id: "twin", label: "Hospital Twin", icon: I.database },
      { id: "heatmap", label: "Heatmap géo", icon: I.globe },
      { id: "pivot", label: "Tableaux croisés", icon: I.table },
    ]},
    { group: "Gestion Batch", items: [
      { id: "modo", label: "Modo Files", icon: I.folders, badge: badges.modo },
      { id: "idv", label: "Identitovigilance", icon: I.users, badge: badges.idv, badgeColor: ERROR },
    ]},
    { group: "Exports", items: [
      { id: "pilot", label: "PMSI Pilot CSV", icon: I.download },
      { id: "csv", label: "Import CSV", icon: I.upload },
      { id: "structure", label: "Structure", icon: I.branch },
    ]},
    { group: "Sécurité & Ops", items: [
      { id: "rgpd", label: "RGPD", icon: I.fingerprint },
      { id: "audit", label: "Audit chain", icon: I.history },
      { id: "workflow", label: "Workflows", icon: I.folder },
    ]},
    { group: "Aide", items: [
      { id: "tuto", label: "Tutoriel", icon: I.book },
    ]},
  ];

  return (
    <div style={{
      width: 1440, height: 900, display: "flex",
      background: slate[50], fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
      color: slate[900], fontSize: 14, letterSpacing: "-0.005em",
      borderRadius: 12, overflow: "hidden",
      boxShadow: "0 24px 60px -20px rgba(15,23,42,0.18), 0 1px 0 rgba(15,23,42,0.04)",
      border: `1px solid ${slate[200]}`,
    }}>
      {/* SIDEBAR */}
      <aside style={{
        width: 248, background: "white", borderRight: `1px solid ${slate[200]}`,
        display: "flex", flexDirection: "column", flexShrink: 0,
      }}>
        {/* Brand */}
        <div style={{
          padding: "20px 22px", borderBottom: `1px solid ${slate[100]}`,
          display: "flex", alignItems: "center", gap: 12,
        }}>
          <div style={{
            width: 40, height: 40, background: `linear-gradient(135deg, ${NAVY} 0%, ${NAVY_DARK} 100%)`,
            borderRadius: 10, position: "relative", flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 6px rgba(0,0,145,0.25), inset 0 1px 0 rgba(255,255,255,0.12)",
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
            <div style={{
              position: "absolute", bottom: -3, right: -3, width: 12, height: 12,
              background: TEAL, borderRadius: 999,
              border: `2px solid white`,
            }}/>
          </div>
          <div style={{ overflow: "hidden" }}>
            <div style={{ fontWeight: 800, fontSize: 16, color: NAVY, letterSpacing: "-0.015em", lineHeight: 1 }}>
              Sentinel
            </div>
            <div style={{ fontSize: 9, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.16em", marginTop: 3 }}>
              GHT Sud Paris · v36
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: "12px 0", overflowY: "auto", minHeight: 0 }}>
          {navItems.map((g, gi) => (
            <div key={gi} style={{ marginBottom: 4 }}>
              <div style={{
                padding: "8px 22px 4px", fontSize: 9, fontWeight: 700,
                color: slate[400], textTransform: "uppercase", letterSpacing: "0.16em",
              }}>
                {g.group}
              </div>
              {g.items.map(it => {
                const isActive = it.id === active;
                return (
                  <div key={it.id} style={{
                    margin: "1px 10px", padding: "7px 12px",
                    display: "flex", alignItems: "center", gap: 10,
                    borderRadius: 8,
                    background: isActive ? slate[50] : "transparent",
                    color: isActive ? NAVY : slate[600],
                    fontWeight: isActive ? 700 : 600, fontSize: 12,
                    position: "relative", cursor: "pointer",
                    borderLeft: isActive ? `2px solid ${NAVY}` : "2px solid transparent",
                    paddingLeft: isActive ? 12 : 14,
                    transition: "background 150ms",
                  }}>
                    <span style={{ color: isActive ? NAVY : slate[500], display: "flex" }}>
                      {React.cloneElement(it.icon, { size: 16 })}
                    </span>
                    <span style={{ flex: 1, lineHeight: 1.2 }}>{it.label}</span>
                    {it.badge != null && (
                      <span style={{
                        background: it.badgeColor || NAVY, color: "white",
                        fontSize: 9, fontWeight: 700, padding: "2px 6px",
                        borderRadius: 999, lineHeight: 1.2,
                      }}>{it.badge}</span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Operator footer */}
        <div style={{
          padding: 14, borderTop: `1px solid ${slate[100]}`,
          background: slate[50],
        }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            background: "white", padding: "10px 12px",
            borderRadius: 10, border: `1px solid ${slate[200]}`,
          }}>
            <div style={{
              width: 32, height: 32, background: NAVY, color: "white",
              borderRadius: 8, display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: 11, fontWeight: 800,
            }}>DIM</div>
            <div style={{ flex: 1, overflow: "hidden" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, lineHeight: 1.2 }}>Opérateur DIM</div>
              <div style={{ fontSize: 9, fontWeight: 700, color: SUCCESS, textTransform: "uppercase", letterSpacing: "0.14em", marginTop: 2, display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: SUCCESS }}/>Station active
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Topbar */}
        <header style={{
          height: 64, background: "white", borderBottom: `1px solid ${slate[200]}`,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "0 28px", flexShrink: 0,
        }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: NAVY, letterSpacing: "-0.015em", lineHeight: 1.1 }}>
              {title}
            </div>
            <div style={{ fontSize: 10, fontWeight: 700, color: slate[400], textTransform: "uppercase", letterSpacing: "0.16em", marginTop: 3 }}>
              {subtitle}
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: NAVY, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "-0.02em" }}>
                14:32:08
              </div>
              <div style={{ fontSize: 9, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.18em", marginTop: 1 }}>
                Connecté
              </div>
            </div>
            <div style={{ width: 1, height: 28, background: slate[200] }}/>
            <button style={iconBtn}>{I.moon}</button>
            <button style={{ ...iconBtn, color: slate[500] }}>{I.power}</button>
          </div>
        </header>

        {/* Viewport */}
        <div style={{ flex: 1, overflow: "auto", padding: 28, background: slate[50] }}>
          {children}
        </div>
      </main>
    </div>
  );
};

const iconBtn = {
  width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center",
  background: slate[50], border: `1px solid ${slate[200]}`, borderRadius: 8,
  color: slate[500], cursor: "pointer",
};

// Section header (eyebrow + title + meta)
const SectionHead = ({ eyebrow, title, meta, action }) => (
  <div style={{
    display: "flex", alignItems: "flex-end", justifyContent: "space-between",
    paddingBottom: 14, borderBottom: `1px solid ${slate[200]}`, marginBottom: 18,
  }}>
    <div>
      {eyebrow && (
        <div style={{ fontSize: 10, fontWeight: 700, color: TEAL, textTransform: "uppercase", letterSpacing: "0.18em", marginBottom: 6 }}>
          {eyebrow}
        </div>
      )}
      <div style={{ fontSize: 22, fontWeight: 800, color: NAVY, letterSpacing: "-0.02em", lineHeight: 1.1 }}>
        {title}
      </div>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {meta && <span style={{ fontSize: 11, fontWeight: 600, color: slate[500] }}>{meta}</span>}
      {action}
    </div>
  </div>
);

// KPI card with left accent on hover (here always-on for primary)
const Kpi = ({ label, value, unit, accent = TEAL, sub }) => (
  <div style={{
    background: "white", border: `1px solid ${slate[200]}`,
    borderRadius: 12, padding: "16px 20px", position: "relative",
    overflow: "hidden", boxShadow: "0 1px 2px rgba(0,0,145,0.03)",
  }}>
    <div style={{
      position: "absolute", left: 0, top: 0, bottom: 0, width: 3,
      background: accent,
    }}/>
    <div style={{ fontSize: 10, fontWeight: 700, color: slate[500], textTransform: "uppercase", letterSpacing: "0.13em" }}>
      {label}
    </div>
    <div style={{ marginTop: 8, display: "flex", alignItems: "baseline", gap: 6 }}>
      <span style={{ fontSize: 28, fontWeight: 800, color: NAVY, lineHeight: 1, fontFeatureSettings: "'tnum'", letterSpacing: "-0.025em" }}>
        {value}
      </span>
      {unit && <span style={{ fontSize: 11, color: slate[500], fontWeight: 600 }}>{unit}</span>}
    </div>
    {sub && (
      <div style={{ fontSize: 11, color: slate[500], marginTop: 6 }}>{sub}</div>
    )}
  </div>
);

// Small "format badge"
const FmtBadge = ({ label, kind = "PSY" }) => {
  const map = {
    PSY:   { bg: "#EEF2FF", fg: "#4338CA" },
    SSR:   { bg: "#ECFDF5", fg: "#0F766E" },
    HAD:   { bg: "#FFFBEB", fg: "#B45309" },
    MCO:   { bg: "#FFF1F2", fg: "#BE123C" },
    TRANS: { bg: "#F1F5F9", fg: "#475569" },
  };
  const c = map[kind] || map.TRANS;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      padding: "3px 9px", borderRadius: 999,
      background: c.bg, color: c.fg,
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 10, fontWeight: 700, letterSpacing: "0.02em",
    }}>
      <span style={{ width: 5, height: 5, borderRadius: 999, background: c.fg }}/>
      {label}
    </span>
  );
};

const Card = ({ title, icon, action, children, padding = 20 }) => (
  <div style={{
    background: "white", border: `1px solid ${slate[200]}`,
    borderRadius: 12, overflow: "hidden",
    boxShadow: "0 1px 2px rgba(0,0,145,0.03)",
  }}>
    {(title || action) && (
      <div style={{
        padding: "14px 20px", borderBottom: `1px solid ${slate[100]}`,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: slate[50],
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          {icon && <span style={{ color: TEAL, display: "flex" }}>{icon}</span>}
          <span style={{ fontSize: 11, fontWeight: 700, color: NAVY, textTransform: "uppercase", letterSpacing: "0.14em" }}>
            {title}
          </span>
        </div>
        {action}
      </div>
    )}
    <div style={{ padding }}>{children}</div>
  </div>
);

const Btn = ({ children, kind = "primary", icon, sm }) => {
  const styles = {
    primary: { bg: NAVY, fg: "white", border: NAVY },
    teal: { bg: TEAL, fg: "white", border: TEAL },
    ghost: { bg: "white", fg: slate[700], border: slate[300] },
    danger: { bg: "white", fg: ERROR, border: "#FCA5A5" },
    warn: { bg: WARNING, fg: "white", border: WARNING },
  };
  const c = styles[kind];
  return (
    <button style={{
      display: "inline-flex", alignItems: "center", gap: 7,
      padding: sm ? "6px 12px" : "9px 16px",
      background: c.bg, color: c.fg, border: `1px solid ${c.border}`,
      borderRadius: 8, fontSize: sm ? 11 : 12, fontWeight: 700,
      letterSpacing: "0.01em", cursor: "pointer",
      boxShadow: kind === "ghost" ? "none" : "0 1px 2px rgba(0,0,145,0.06)",
      fontFamily: "inherit",
    }}>
      {icon && <span style={{ display: "flex" }}>{icon}</span>}
      {children}
    </button>
  );
};

Object.assign(window, {
  NAVY, NAVY_DARK, TEAL, GOLD, ERROR, SUCCESS, WARNING, slate,
  Icon, I, Shell, SectionHead, Kpi, FmtBadge, Card, Btn, iconBtn,
});

/*
 * tuto-overlay.js · contextual help modal per view.
 * Injects a floating "?" button in the top-right of the page.
 * Clicking it opens a tuto card whose content matches the current view.
 * Keyboard shortcut · F1 ou "?"
 */
(function () {
  if (window.__tutoOverlayLoaded) return;
  window.__tutoOverlayLoaded = true;

  const TUTORIALS = {
    dashboard: {
      title: "Tableau de bord",
      steps: [
        "Vue d'ensemble · nombre de fichiers chargés, lignes traitées, IPP uniques, collisions détectées.",
        "Graphiques Chart.js · répartition par format ATIH + par champ PMSI.",
        "Raccourcis · Ctrl+2 = Modo Files · Ctrl+3 = Identitovigilance · Ctrl+4 = PMSI Pilot.",
      ],
    },
    modo: {
      title: "Modo Files · Ingestion",
      steps: [
        "1. Cliquer sur « Sélectionner un dossier » · ouvrir un dossier PMSI (sous l'espace de travail).",
        "2. Le scan récursif identifie RPS, RAA, FICHSUP-PSY, VID-HOSP, FICUM-PSY, etc.",
        "3. « Scanner & Traiter » lance le parsing parallèle + construit le MPI.",
        "4. Les logs temps réel remontent via /api/logs.",
      ],
    },
    idv: {
      title: "Identitovigilance · MPI",
      steps: [
        "Un IPP associé à plusieurs DDN = collision.",
        "Auto-résolution · la DDN la plus fréquente devient pivot. Cliquer « Auto-résoudre ».",
        "Résolution manuelle · sélectionner la bonne DDN dans la colonne « options ».",
        "La DDN pivot est injectée dans l'export CSV et la purification .txt.",
      ],
    },
    pilot: {
      title: "PMSI Pilot · Export CSV",
      steps: [
        "Export du MPI avec DDN pivot injectée, colonnes IPP / DDN_PIVOT / DDN_OBSERVATIONS / SOURCE_FILES.",
        "Séparateur `;` par défaut, compatible Excel FR.",
        "Injection formule Excel bloquée automatiquement (= + - @ \\t \\r neutralisés).",
        "Destination confinée à l'espace de travail (SafePath).",
      ],
    },
    csv: {
      title: "Import CSV/Excel",
      steps: [
        "Drop d'un .csv ou .xlsx · prévisualisation 100 premières lignes.",
        "Détection auto du séparateur CSV (;, tab, pipe).",
        "Pour .xlsx, tous les feuillets sont listés avec nombre de lignes/colonnes.",
      ],
    },
    structure: {
      title: "Structure hospitalière",
      steps: [
        "Charger un fichier de structure CSV/TSV (LEVEL;CODE;PARENT;LABEL).",
        "Arbre expand/collapse · type ARS détecté automatiquement (G/I/D/P/Z).",
        "Propagation du type aux UM enfants · héritage secteur visible en couleur.",
      ],
    },
    preflight: {
      title: "Preflight DRUIDES",
      steps: [
        "Lance 13 validateurs sur les fichiers scannés · FINESS, DDN, chaînage VID-HOSP, NIR, FicUM, FICHSUP, séquences RPS, mode légal, DP, sectorisation, doublons, année.",
        "Les findings sont triés par sévérité (Blocker > Error > Warning > Info).",
        "Chaque finding renvoie code, ligne, format, hint de correction.",
        "Objectif · zéro erreur DRUIDES avant upload e-PMSI.",
      ],
    },
    tuto: {
      title: "Tutoriel complet",
      steps: [
        "Vue dédiée avec le guide opérationnel long.",
        "Pour générer un PDF imprimable · appel `api.open_manual()` puis `api.html_to_pdf(path)`.",
      ],
    },
  };

  function getCurrentView() {
    try {
      return (window.S && window.S.view) ||
             (document.querySelector(".nav-active")?.id?.replace("nav-", "")) ||
             "dashboard";
    } catch { return "dashboard"; }
  }

  function renderTuto(view) {
    const t = TUTORIALS[view] || TUTORIALS.dashboard;
    return `
      <div id="tuto-overlay-card" style="
        position:fixed; z-index:9999; top:50%; left:50%; transform:translate(-50%,-50%);
        width:min(560px, 92vw); max-height:80vh; overflow:auto;
        background:#ffffff; color:#0F172A; border-radius:24px;
        box-shadow:0 20px 60px rgba(0,0,0,0.4); padding:2.5rem; font-family:'Plus Jakarta Sans',sans-serif;
        border:1px solid #E2E8F0;">
        <div style="font-family:'JetBrains Mono',monospace; font-size:10px; letter-spacing:0.3em;
                    color:#00897B; text-transform:uppercase; margin-bottom:0.5rem;">Aide contextuelle</div>
        <h2 style="font-size:1.75rem; font-weight:900; font-style:italic; letter-spacing:-0.02em;
                   text-transform:uppercase; margin:0 0 1.25rem; color:#000091;">${t.title}</h2>
        <ol style="margin:0; padding-left:1.25rem; line-height:1.55;">
          ${t.steps.map(s => `<li style="margin:0.4rem 0;">${s}</li>`).join("")}
        </ol>
        <div style="margin-top:1.5rem; display:flex; justify-content:space-between; align-items:center;
                    font-size:0.75rem; color:#64748B;">
          <span>F1 ou ? pour rouvrir · Esc pour fermer</span>
          <button id="tuto-close" style="border:0; background:#000091; color:#fff; padding:0.5rem 1rem;
                                          border-radius:999px; cursor:pointer;
                                          font-family:'JetBrains Mono',monospace; letter-spacing:0.1em;">FERMER</button>
        </div>
      </div>
      <div id="tuto-backdrop" style="position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9998;"></div>
    `;
  }

  function openTuto() {
    closeTuto();
    const view = getCurrentView();
    const wrap = document.createElement("div");
    wrap.id = "tuto-overlay-root";
    wrap.innerHTML = renderTuto(view);
    document.body.appendChild(wrap);
    document.getElementById("tuto-close")?.addEventListener("click", closeTuto);
    document.getElementById("tuto-backdrop")?.addEventListener("click", closeTuto);
  }

  function closeTuto() {
    document.getElementById("tuto-overlay-root")?.remove();
  }

  function injectButton() {
    if (document.getElementById("tuto-help-button")) return;
    const btn = document.createElement("button");
    btn.id = "tuto-help-button";
    btn.title = "Aide contextuelle (F1)";
    btn.textContent = "?";
    btn.setAttribute("aria-label", "Aide contextuelle");
    btn.style.cssText = `
      position:fixed; z-index:9997; right:24px; bottom:24px; width:52px; height:52px;
      border-radius:50%; border:0; cursor:pointer;
      background:linear-gradient(135deg, #000091 0%, #00897B 100%); color:white;
      font-family:'Plus Jakarta Sans',sans-serif; font-size:24px; font-weight:800;
      box-shadow:0 8px 20px rgba(0,0,138,0.35); transition:transform 0.2s;
    `;
    btn.addEventListener("mouseenter", () => btn.style.transform = "scale(1.1)");
    btn.addEventListener("mouseleave", () => btn.style.transform = "scale(1.0)");
    btn.addEventListener("click", openTuto);
    document.body.appendChild(btn);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "F1" || (e.key === "?" && !e.ctrlKey && !e.altKey)) {
      e.preventDefault();
      openTuto();
    } else if (e.key === "Escape") {
      closeTuto();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectButton);
  } else {
    injectButton();
  }

  // Public API in case app.js wants to trigger programmatically.
  window.sovereignTuto = { open: openTuto, close: closeTuto, tutorials: TUTORIALS };
})();

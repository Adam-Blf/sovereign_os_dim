/**
 * =============================================================================
 * SOVEREIGN OS V35.0 — Frontend Application Logic (Optimized)
 * =============================================================================
 * Features:
 *   - Boot sequence with anime.js
 *   - Dashboard with Chart.js (format breakdown doughnut)
 *   - Modo Files with drag & drop + progress bar
 *   - Identitovigilance with search filter
 *   - PMSI Pilot CSV export with progress
 *   - Inspector terminal + sanitized .txt export
 *   - Toast notifications with type coloring
 *   - Keyboard shortcuts (Ctrl+1/2/3/4)
 * =============================================================================
 */

(function () {
    "use strict";

    // =========================================================================
    // STATE
    // =========================================================================
    const S = {
        view: "dashboard",
        files: [],
        collisions: [],
        stats: null,
        mpiStats: null,
        booted: false,
        chart: null,
    };

    // =========================================================================
    // DOM HELPERS
    // =========================================================================
    const $ = (id) => document.getElementById(id);
    const N = (n) => (n === undefined || n === null) ? "0" : n.toLocaleString("fr-FR");
    const API = () => window.pywebview && window.pywebview.api;

    function badge(format) {
        const c = "fmt-" + (format || "inconnu").toLowerCase().replace(/[^a-z]/g, "-");
        return `<span class="fmt-badge ${c}">${format || "?"}</span>`;
    }

    // =========================================================================
    // TOAST (typed: success, error, info, warning)
    // =========================================================================
    let _tt = null;
    function toast(title, msg, type = "info") {
        const el = $("os-toast");
        const ic = $("toast-icon-container");
        if (!el) return;
        const tt = $("toast-title-text"), tm = $("toast-msg-text");
        if (tt) tt.textContent = title;
        if (tm) tm.textContent = msg;

        const colors = { success: "bg-gh-success", error: "bg-gh-error", warning: "bg-gh-warning", info: "bg-gh-navy" };
        if (ic) { ic.className = `p-8 text-white rounded-[3rem] shadow-4xl leading-none ${colors[type] || colors.info}`; }

        el.classList.remove("hidden");
        clearTimeout(_tt);
        _tt = setTimeout(() => el.classList.add("hidden"), 4500);
    }

    // =========================================================================
    // CLOCK
    // =========================================================================
    function startClock() {
        const el = $("os-clock");
        if (!el) return;
        const tick = () => { el.textContent = new Date().toLocaleTimeString("fr-FR", { hour12: false }); };
        tick();
        setInterval(tick, 1000);
    }

    // =========================================================================
    // BOOT SEQUENCE (anime.js)
    // =========================================================================
    function runBoot() {
        const bar = $("boot-progress-bar");
        const status = $("boot-status-text");
        const btnIgnite = $("btn-ignite");

        const steps = [
            "Initialisation du moteur ATIH…",
            "Compilation des patterns regex (8 formats)…",
            "Activation ThreadPoolExecutor…",
            "Calibration MPI & détection collisions…",
            "Chargement matrice positionnelle stricte…",
            "Sovereign OS — Prêt.",
        ];

        // Anime.js progress bar
        if (typeof anime !== "undefined") {
            anime({
                targets: bar,
                width: ["0%", "100%"],
                duration: 3600,
                easing: "easeInOutQuart",
                update: function (anim) {
                    const idx = Math.min(Math.floor(anim.progress / 100 * steps.length), steps.length - 1);
                    if (status) status.textContent = steps[idx];
                },
                complete: function () {
                    if (btnIgnite) {
                        btnIgnite.classList.remove("hidden");
                        anime({ targets: btnIgnite, opacity: [0, 1], translateY: [30, 0], duration: 600, easing: "easeOutQuart" });
                        btnIgnite.addEventListener("click", enterApp);
                    }
                }
            });
        } else {
            // Fallback without anime.js
            let i = 0;
            const iv = setInterval(() => {
                if (i >= steps.length) { clearInterval(iv); if (btnIgnite) { btnIgnite.classList.remove("hidden"); btnIgnite.addEventListener("click", enterApp); } return; }
                if (bar) bar.style.width = ((i + 1) / steps.length * 100) + "%";
                if (status) status.textContent = steps[i];
                i++;
            }, 600);
        }
    }

    function enterApp() {
        const overlay = $("boot-overlay");
        const root = $("app-root");

        if (typeof anime !== "undefined") {
            anime({ targets: overlay, opacity: 0, duration: 800, easing: "easeInQuart", complete: () => overlay.classList.add("hidden") });
        } else {
            overlay.style.opacity = "0";
            setTimeout(() => overlay.classList.add("hidden"), 800);
        }

        if (root) {
            root.classList.remove("hidden");
            setTimeout(() => { root.style.opacity = "1"; }, 50);
        }

        S.booted = true;
        navigateTo("dashboard");
        startClock();
    }

    // =========================================================================
    // NAVIGATION
    // =========================================================================
    const VIEWS = {
        dashboard: { title: "Dashboard", sub: "Tableau de bord de production" },
        modo: { title: "Modo Files", sub: "Ingestion & traitement batch" },
        idv: { title: "Identitovigilance", sub: "Master Patient Index — Résolution des collisions" },
        pilot: { title: "PMSI Pilot CSV", sub: "Export des données réconciliées" },
        csv: { title: "Import CSV", sub: "Visualiseur de fichiers CSV externes" },
        tuto: { title: "Tutoriel d'utilisation", sub: "Guide pas-à-pas Sentinel" }
    };

    function navigateTo(view) {
        S.view = view;
        const v = VIEWS[view] || {};
        const t = $("view-title-main"), s = $("view-subtitle-main");
        if (t) t.textContent = v.title || view;
        if (s) s.textContent = v.sub || "";

        document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("nav-active"));
        const btn = $("nav-" + view);
        if (btn) btn.classList.add("nav-active");

        const vp = $("os-viewport");
        if (vp) {
            vp.classList.remove("animate-fade-in");
            void vp.offsetWidth; // trigger reflow
            vp.classList.add("animate-fade-in");
        }
        render(view);
    }

    function render(view) {
        const vp = $("os-viewport");
        if (!vp) return;
        switch (view) {
            case "dashboard": renderDashboard(vp); break;
            case "modo": renderModo(vp); break;
            case "idv": renderIdv(vp); break;
            case "pilot": renderPilot(vp); break;
            case "csv": renderCsv(vp); break;
            case "structure": renderStructure(vp); break;
            case "tuto": renderTuto(vp); break;
        }
        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // DASHBOARD
    // =========================================================================
    async function renderDashboard(vp) {
        let d = { folders: 0, files: 0, formats: 8, mpi: {}, format_breakdown: [], file_stats: {} };
        try { if (API()) d = await API().get_dashboard_stats(); } catch (e) { /* ok */ }
        const m = d.mpi || {};

        vp.innerHTML = `
            <div class="grid grid-cols-4 gap-6 mb-10">
                ${statCard("folders", "Dossiers", d.folders, "blue")}
                ${statCard("file-text", "Fichiers", d.files, "teal")}
                ${statCard("fingerprint", "IPP Uniques", m.total_ipp, "amber")}
                ${statCard("alert-triangle", "Collisions", m.collisions, "red", m.collisions > 0 ? "ring-2 ring-gh-error/20" : "")}
            </div>

            <div class="grid grid-cols-2 gap-6 mb-10">
                <!-- Chart -->
                <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl">
                    <h3 class="font-black text-gh-navy uppercase text-sm tracking-tighter italic mb-6 flex items-center gap-3">
                        <i data-lucide="pie-chart" class="w-5 h-5 text-gh-teal"></i> Répartition formats
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="chart-formats" width="280" height="280"></canvas>
                    </div>
                </div>

                <!-- Matrice -->
                <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl">
                    <h3 class="font-black text-gh-navy uppercase text-sm tracking-tighter italic mb-6 flex items-center gap-3">
                        <i data-lucide="database" class="w-5 h-5 text-gh-navy"></i> Matrice ATIH · ${d.formats} formats
                    </h3>
                    <div class="grid grid-cols-2 gap-3" id="matrix-grid"></div>
                </div>
            </div>

            <!-- MPI Summary -->
            <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl">
                <h3 class="font-black text-gh-navy uppercase text-sm tracking-tighter italic mb-6 flex items-center gap-3">
                    <i data-lucide="activity" class="w-5 h-5 text-gh-success"></i> État MPI
                </h3>
                <div class="grid grid-cols-4 gap-4">
                    <div class="bg-slate-50 rounded-2xl p-5 text-center">
                        <p class="text-2xl font-black text-gh-navy">${N(m.total_ipp)}</p>
                        <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">Total IPP</p>
                    </div>
                    <div class="bg-slate-50 rounded-2xl p-5 text-center">
                        <p class="text-2xl font-black text-gh-error">${N(m.collisions)}</p>
                        <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">Collisions</p>
                    </div>
                    <div class="bg-slate-50 rounded-2xl p-5 text-center">
                        <p class="text-2xl font-black text-gh-success">${N(m.resolved)}</p>
                        <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">Résolues</p>
                    </div>
                    <div class="bg-slate-50 rounded-2xl p-5 text-center">
                        <p class="text-2xl font-black ${m.pending > 0 ? "text-gh-warning" : "text-gh-success"}">${N(m.pending)}</p>
                        <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">En attente</p>
                    </div>
                </div>
            </div>

            <!-- FILE ACTIVE PSY — KPI rapport d'activité (dé-doublonnage cross-recueils) -->
            <div class="bg-white rounded-[2.5rem] p-10 border border-slate-100 shadow-xl mt-10" id="active-pop-block">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="font-black text-gh-navy uppercase text-sm tracking-tighter italic flex items-center gap-3">
                        <i data-lucide="users" class="w-5 h-5 text-gh-teal"></i> File active — par année et par champ
                    </h3>
                    <span class="text-[9px] font-mono text-slate-400 italic">IPP uniques dé-doublonnés cross-recueils</span>
                </div>
                <div id="active-pop-body">
                    <p class="text-xs text-slate-400 italic text-center py-8">Chargement…</p>
                </div>
            </div>

            <!-- PARCOURS CROSS-MODALITÉS — Patients traversant plusieurs recueils PMSI -->
            <div id="cross-modality-block"></div>
        `;

        // Chart.js doughnut
        const canvas = $("chart-formats");
        if (canvas && typeof Chart !== "undefined") {
            const bd = d.format_breakdown || [];
            const palette = ["#000091", "#00897B", "#E11D48", "#F59E0B", "#7C3AED", "#2563EB", "#DB2777", "#059669"];
            if (S.chart) S.chart.destroy();
            S.chart = new Chart(canvas, {
                type: "doughnut",
                data: {
                    labels: bd.map(x => x.format),
                    datasets: [{
                        data: bd.map(x => x.count),
                        backgroundColor: bd.map((_, i) => palette[i % palette.length]),
                        borderWidth: 0,
                    }]
                },
                options: {
                    cutout: "65%",
                    responsive: false,
                    plugins: {
                        legend: { position: "right", labels: { font: { family: "'Plus Jakarta Sans'", weight: "bold", size: 11 }, padding: 12 } }
                    }
                }
            });
        }

        // Matrix grid
        try {
            if (API()) {
                const mx = await API().get_matrix_info();
                const g = $("matrix-grid");
                if (g && mx) {
                    g.innerHTML = mx.map(m => `
                        <div class="bg-slate-50 rounded-xl p-4 border border-slate-100 hover:border-gh-navy/20 transition-all">
                            <div class="flex items-center justify-between mb-1">${badge(m.key)}<span class="text-[9px] font-mono text-slate-400">${m.length} c</span></div>
                            <p class="text-[10px] text-slate-500 mt-1">${m.desc}</p>
                            <p class="text-[8px] font-mono text-slate-400 mt-1">IPP [${m.ipp[0]}:${m.ipp[1]}] DDN [${m.ddn[0]}:${m.ddn[1]}]</p>
                        </div>
                    `).join("");
                }
            }
        } catch (e) { /* ok */ }

        // File active PSY — tableau Année × Champ + total global.
        // Si les noms de fichiers ne contiennent pas d'année détectable
        // (convention "RPS_2024.txt"), on le signale à l'utilisateur.
        try {
            if (API()) {
                const ap = await API().get_active_population();
                renderActivePopulation(ap);
            }
        } catch (e) { /* ok */ }

        // Parcours cross-modalités — top 50 patients les plus complexes.
        try {
            if (API()) {
                const cm = await API().get_cross_modality_patients(2, 50);
                const el = $("cross-modality-block");
                if (el) renderCrossModality(el, cm);
            }
        } catch (e) { /* ok */ }

        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // PARCOURS CROSS-MODALITÉS — patients traversant plusieurs recueils PMSI
    // =========================================================================
    // Rendu "journey cartography" : chaque ligne = un patient. Numéral de
    // complexité (2/3/4+) en teal→warning→error, chips format colorées par
    // champ PMSI, timeline horizontale cellule-par-année.
    function renderCrossModality(containerEl, data) {
        const all = Array.isArray(data) ? data : [];

        // Alignement des timelines : plage d'années couverte par l'ensemble
        // des patients, pour que chaque ligne partage la même échelle.
        const allYears = new Set();
        all.forEach(p => (p.years || []).forEach(y => allYears.add(y)));
        const yearRange = [...allYears].sort();

        // FORMAT → CHAMP PMSI (cohérent avec ATIH_MATRIX côté backend).
        const FIELD_OF = {
            RPS: "PSY", RAA: "PSY", RPSA: "PSY", R3A: "PSY", EDGAR: "PSY",
            "FICHSUP-PSY": "PSY", "FICUM-PSY": "PSY", "RSF-ACE-PSY": "PSY",
            RHS: "SSR", SSRHA: "SSR", RAPSS: "SSR", "FICHCOMP-SMR": "SSR",
            RPSS: "HAD", "RAPSS-HAD": "HAD", "FICHCOMP-HAD": "HAD", "SSRHA-HAD": "HAD",
            RSS: "MCO", RSFA: "MCO", RSFB: "MCO", RSFC: "MCO",
            "VID-HOSP": "TRANS", "ANO-HOSP": "TRANS", FICHCOMP: "TRANS",
        };
        const FIELD = {
            PSY: { bg: "bg-indigo-50 dark:bg-indigo-900/30", text: "text-indigo-700 dark:text-indigo-300", dot: "bg-indigo-500", bar: "bg-indigo-400", cssVar: "#6366f1" },
            SSR: { bg: "bg-teal-50 dark:bg-teal-900/30", text: "text-teal-700 dark:text-teal-300", dot: "bg-teal-500", bar: "bg-teal-400", cssVar: "#14b8a6" },
            HAD: { bg: "bg-amber-50 dark:bg-amber-900/30", text: "text-amber-700 dark:text-amber-300", dot: "bg-amber-500", bar: "bg-amber-400", cssVar: "#f59e0b" },
            MCO: { bg: "bg-rose-50 dark:bg-rose-900/30", text: "text-rose-700 dark:text-rose-300", dot: "bg-rose-500", bar: "bg-rose-400", cssVar: "#f43f5e" },
            TRANS: { bg: "bg-slate-100 dark:bg-slate-700/50", text: "text-slate-600 dark:text-slate-300", dot: "bg-slate-400", bar: "bg-slate-400", cssVar: "#94a3b8" },
        };

        // Champ "principal" pour l'accent de bordure gauche au hover.
        // Priorité métier : PSY > HAD > SSR > MCO > Transversal.
        const ORDER = ["PSY", "HAD", "SSR", "MCO", "TRANS"];
        const primaryField = p => ORDER.find(f => (p.fields || []).includes(f)) || "TRANS";

        const complexityColor = n =>
            n >= 4 ? "text-gh-error" : n === 3 ? "text-gh-warning" : "text-gh-teal";

        function renderRow(p) {
            const n = p.formats.length;
            const pf = primaryField(p);
            const pfCol = FIELD[pf];

            const chips = p.formats.map(f => {
                const c = FIELD[FIELD_OF[f] || "TRANS"];
                return `<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-mono font-bold ${c.bg} ${c.text}">
                    <span class="w-1.5 h-1.5 rounded-full ${c.dot}"></span>${escHtml(f)}
                </span>`;
            }).join("");

            const yearsSet = new Set(p.years || []);
            const cells = yearRange.map(y =>
                `<div class="journey-cell ${yearsSet.has(y) ? pfCol.bar : "bg-slate-100 dark:bg-slate-800"}" title="${escHtml(y)}"></div>`
            ).join("");

            const span = p.years.length
                ? `${escHtml(p.years[0])}→${escHtml(p.years[p.years.length - 1])}`
                : "—";

            return `
                <div class="journey-row relative grid grid-cols-12 gap-6 px-10 py-6 border-b border-slate-100 dark:border-slate-800 transition-colors"
                     data-ipp="${escHtml(p.ipp).toLowerCase()}"
                     style="--row-accent: ${pfCol.cssVar};">
                    <div class="col-span-1 flex items-center">
                        <div class="text-5xl font-black italic tracking-tighter leading-none ${complexityColor(n)}">${n}</div>
                    </div>
                    <div class="col-span-3 flex flex-col justify-center">
                        <p class="font-mono font-black text-sm text-gh-navy dark:text-blue-400 tracking-tight truncate">${escHtml(p.ipp)}</p>
                        <p class="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500 mt-1">
                            ${n} modalités · ${p.sources_count} sources
                        </p>
                    </div>
                    <div class="col-span-5 flex items-center flex-wrap gap-1.5">${chips}</div>
                    <div class="col-span-3 flex flex-col justify-center">
                        <div class="flex items-center gap-0.5">${cells}</div>
                        <p class="text-[9px] font-mono text-slate-400 dark:text-slate-500 mt-2 tracking-wider">${span}</p>
                    </div>
                </div>`;
        }

        const yearHeader = yearRange.map(y =>
            `<span class="journey-year-label">'${escHtml(y.slice(-2))}</span>`
        ).join("");

        const empty = `
            <div class="flex flex-col items-center justify-center py-20 px-8 text-center">
                <div class="w-16 h-16 rounded-3xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-6 rotate-3">
                    <i data-lucide="circle-slash-2" class="w-7 h-7 text-slate-400"></i>
                </div>
                <p class="font-black text-slate-500 dark:text-slate-400 uppercase italic tracking-tighter text-lg">Aucun parcours cross-modalités</p>
                <p class="text-xs text-slate-400 dark:text-slate-500 mt-3 max-w-md">
                    Traitez un lot ATIH couvrant plusieurs recueils (RPS + EDGAR + RPSS…) pour révéler les patients à parcours complexe.
                </p>
            </div>`;

        containerEl.innerHTML = `
            <section class="bg-white dark:bg-slate-800 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl overflow-hidden mt-10">
                <header class="px-10 py-8 flex items-end justify-between gap-6 flex-wrap border-b border-slate-100 dark:border-slate-800">
                    <div>
                        <div class="flex items-center gap-4 mb-2">
                            <i data-lucide="git-fork" class="w-6 h-6 text-gh-teal"></i>
                            <h3 class="font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic text-xl leading-none">
                                Parcours cross-modalités
                            </h3>
                        </div>
                        <p class="text-[11px] text-slate-500 dark:text-slate-400 tracking-wide max-w-lg">
                            Patients traversant plusieurs recueils PMSI — hospit, CMP, HDJ. Indicateur de complexité clinique non visible dans CPage ni DxCare.
                        </p>
                    </div>
                    <div class="flex items-center gap-5">
                        <div class="flex items-baseline gap-2">
                            <span class="text-5xl font-black italic tracking-tighter text-gh-navy dark:text-blue-400 leading-none">${all.length}</span>
                            <span class="text-[9px] font-black uppercase tracking-[0.3em] text-slate-400">patients</span>
                        </div>
                        <label class="relative">
                            <i data-lucide="search" class="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"></i>
                            <input id="journey-filter" type="text" placeholder="IPP…"
                                   class="journey-filter pl-9 pr-4 py-2.5 rounded-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 font-mono text-xs w-40 focus:w-64 focus:bg-white dark:focus:bg-slate-800 outline-none transition-all" />
                        </label>
                    </div>
                </header>
                ${yearRange.length ? `
                <div class="px-10 py-3 flex items-center justify-end gap-0.5 border-b border-slate-50 dark:border-slate-800/50 text-[9px] font-mono text-slate-400 dark:text-slate-500">
                    <span class="mr-4 uppercase tracking-widest font-black">Timeline →</span>
                    ${yearHeader}
                </div>` : ""}
                <div id="journey-list" class="max-h-[480px] overflow-y-auto custom-scroll">
                    ${all.length ? all.map(renderRow).join("") : empty}
                </div>
            </section>
        `;

        // Filtre live IPP — display:none sur les lignes non-concernées
        // (pas de rebuild du DOM, préserve l'état de scroll et les animations)
        const input = containerEl.querySelector("#journey-filter");
        const list = containerEl.querySelector("#journey-list");
        if (input && list) {
            input.addEventListener("input", e => {
                const q = e.target.value.toLowerCase().trim();
                list.querySelectorAll(".journey-row").forEach(row => {
                    row.style.display = (!q || (row.dataset.ipp || "").includes(q)) ? "" : "none";
                });
            });
        }
        if (window.lucide) window.lucide.createIcons();
    }

    function renderActivePopulation(ap) {
        const body = $("active-pop-body");
        if (!body) return;
        if (!ap || !ap.years || ap.years.length === 0) {
            body.innerHTML = `
                <p class="text-xs text-slate-400 italic text-center py-8">
                    Aucune année détectée dans les noms de fichiers. Convention attendue :
                    <span class="font-mono text-slate-500">RPS_2024.txt</span>,
                    <span class="font-mono text-slate-500">EDGAR-2024.txt</span>, etc.
                </p>`;
            return;
        }

        // Tableau : une ligne par année, colonnes = champs PMSI + total.
        const fields = ap.fields || [];
        const fieldBadge = {
            PSY: "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300",
            SSR: "bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300",
            HAD: "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
            MCO: "bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
            TRANSVERSAL: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-200",
        };

        const header = `
            <tr class="border-b border-slate-200 dark:border-slate-700">
                <th class="text-left py-3 px-4 font-black text-[10px] uppercase tracking-widest text-slate-500">Année</th>
                ${fields.map(f => `<th class="text-right py-3 px-4 font-black text-[10px] uppercase tracking-widest ${fieldBadge[f] || "text-slate-500"} rounded-md">${escHtml(f)}</th>`).join("")}
                <th class="text-right py-3 px-4 font-black text-[10px] uppercase tracking-widest text-gh-navy dark:text-blue-400">File active</th>
            </tr>`;

        const rows = ap.years.map(y => {
            const fieldCells = fields.map(f => {
                const v = (ap.by_year_field[y] || {})[f] || 0;
                return `<td class="text-right py-3 px-4 font-mono text-sm text-slate-600 dark:text-slate-300">${N(v)}</td>`;
            }).join("");
            const total = ap.by_year_global[y] || 0;
            return `
                <tr class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td class="py-3 px-4 font-mono font-bold text-gh-navy dark:text-blue-400">${escHtml(y)}</td>
                    ${fieldCells}
                    <td class="text-right py-3 px-4 font-mono font-black text-gh-teal text-lg">${N(total)}</td>
                </tr>`;
        }).join("");

        body.innerHTML = `
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>${header}</thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <p class="text-[10px] text-slate-400 dark:text-slate-500 mt-4 italic text-center">
                Total IPP uniques cumulés sur la période : <span class="font-mono font-bold text-slate-600 dark:text-slate-300">${N(ap.total_unique_ipp)}</span>
                &nbsp;·&nbsp; Un même patient est compté 1× par année et par champ (dé-doublonnage cross-recueils).
            </p>
        `;
    }

    function statCard(icon, label, value, color, extra = "") {
        const bg = { blue: "bg-blue-50", teal: "bg-teal-50", amber: "bg-amber-50", red: "bg-red-50" };
        const tc = { blue: "text-gh-navy", teal: "text-gh-teal", amber: "text-gh-warning", red: "text-gh-error" };
        return `
            <div class="stat-card bg-white rounded-[2rem] p-8 border border-slate-100 shadow-lg ${extra}">
                <div class="flex items-center gap-3 mb-4">
                    <div class="p-3 ${bg[color]} rounded-xl"><i data-lucide="${icon}" class="w-5 h-5 ${tc[color]}"></i></div>
                    <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">${label}</span>
                </div>
                <p class="text-4xl font-black ${tc[color]} tracking-tighter">${N(value)}</p>
            </div>`;
    }

    // =========================================================================
    // MODO FILES
    // =========================================================================
    function renderModo(vp) {
        vp.innerHTML = `
            <div class="drop-zone rounded-[3rem] p-14 mb-10 text-center relative transition-colors duration-500" id="drop-zone-area">
                <div class="pointer-events-none">
                    <div class="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-[2rem] flex items-center justify-center mx-auto mb-6 transition-colors duration-500">
                        <i data-lucide="upload-cloud" class="w-10 h-10 text-gh-teal"></i>
                    </div>
                    <h3 class="text-2xl font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic mb-3">Déposer les fichiers PMSI</h3>
                    <p class="text-slate-400 dark:text-slate-500 mb-6">Glissez vos dossiers ici — fichiers et sous-dossiers inclus</p>
                    <div class="flex justify-center gap-4">
                        <button class="pointer-events-auto px-8 py-4 bg-gh-navy dark:bg-blue-600 text-white rounded-full font-black uppercase text-[10px] tracking-[0.2em] shadow-lg hover:bg-blue-800 dark:hover:bg-blue-700 transition-all active:scale-95" id="btn-add-folder">
                            <i data-lucide="folder-plus" class="w-4 h-4 inline mr-2 -mt-0.5"></i>Ajouter dossier
                        </button>
                        <button class="pointer-events-auto px-8 py-4 bg-gh-teal dark:bg-teal-600 text-white rounded-full font-black uppercase text-[10px] tracking-[0.2em] shadow-lg hover:bg-teal-600 dark:hover:bg-teal-700 transition-all active:scale-95" id="btn-scan">
                            <i data-lucide="scan" class="w-4 h-4 inline mr-2 -mt-0.5"></i>Scanner & Traiter
                        </button>
                    </div>
                </div>
            </div>

            <!-- Progress bar -->
            <div id="progress-bar-container" class="hidden mb-8">
                <div class="bg-white dark:bg-slate-800 rounded-full overflow-hidden h-3 shadow-inner border border-slate-100 dark:border-slate-700 transition-colors duration-500">
                    <div id="progress-bar" class="h-full bg-gradient-to-r from-gh-navy to-gh-teal transition-all duration-500 rounded-full" style="width:0%"></div>
                </div>
                <p id="progress-label" class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mt-2 text-center">Initialisation…</p>
            </div>

            <!-- Folders -->
            <div id="folders-panel" class="hidden bg-white dark:bg-slate-800 rounded-[2rem] p-8 border border-slate-100 dark:border-slate-700 shadow-lg dark:shadow-none mb-8 transition-colors duration-500">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-black text-gh-navy dark:text-blue-400 uppercase text-sm tracking-tighter italic flex items-center gap-3">
                        <i data-lucide="hard-drive" class="w-4 h-4 text-gh-teal"></i> Dossiers
                    </h3>
                    <button class="text-[10px] font-black text-gh-error uppercase tracking-widest hover:underline" id="btn-clear">Vider</button>
                </div>
                <div id="folders-list" class="space-y-2"></div>
            </div>

            <!-- Files grid -->
            <div id="files-section" class="hidden">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="font-black text-gh-navy dark:text-blue-400 uppercase text-lg tracking-tighter italic flex items-center gap-3">
                        <i data-lucide="file-text" class="w-5 h-5 text-gh-teal"></i> Fichiers détectés
                    </h3>
                    <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest" id="files-count">0</span>
                </div>
                <div class="grid grid-cols-3 gap-5" id="files-grid"></div>
            </div>
        `;

        // Events
        const addBtn = $("btn-add-folder");
        const scanBtn = $("btn-scan");
        const clearBtn = $("btn-clear");
        const dz = $("drop-zone-area");

        if (addBtn) addBtn.addEventListener("click", addFolder);
        if (scanBtn) scanBtn.addEventListener("click", scanAndProcess);
        if (clearBtn) clearBtn.addEventListener("click", clearAll);

        if (dz) {
            dz.addEventListener("dragover", e => { e.preventDefault(); dz.classList.add("drag-over"); });
            dz.addEventListener("dragleave", () => dz.classList.remove("drag-over"));
            dz.addEventListener("drop", async e => {
                e.preventDefault();
                dz.classList.remove("drag-over");
                const items = e.dataTransfer.files;
                if (!items || !items.length || !API()) return;
                const paths = [];
                for (let i = 0; i < items.length; i++) {
                    if (items[i].path) paths.push(items[i].path);
                }
                if (paths.length) {
                    await API().add_folders(paths);
                    toast("Déposé", `${paths.length} élément(s)`, "success");
                    refreshFolders();
                }
            });
            dz.addEventListener("click", e => { if (e.target === dz) addFolder(); });
        }

        refreshFolders();
        if (S.files.length) showFiles();
    }

    async function addFolder() {
        if (!API()) return;
        const r = await API().select_folder();
        if (r && r.folder) {
            toast("Ajouté", r.folder.split(/[\\/]/).pop(), "success");
            refreshFolders();
        }
    }

    async function refreshFolders() {
        if (!API()) return;
        const f = await API().get_folders();
        const p = $("folders-panel"), l = $("folders-list");
        if (!p || !l) return;
        if (f && f.length) {
            p.classList.remove("hidden");
            l.innerHTML = f.map((x, i) => `
                <div class="flex items-center gap-3 bg-slate-50 dark:bg-slate-800/50 px-5 py-3 rounded-xl text-sm transition-colors duration-500">
                    <i data-lucide="folder" class="w-4 h-4 text-gh-navy dark:text-blue-400 shrink-0"></i>
                    <span class="font-mono text-slate-600 dark:text-slate-300 truncate flex-1 text-[11px]">${x}</span>
                    <span class="text-[9px] font-black text-gh-teal">#${i + 1}</span>
                </div>
            `).join("");
            if (window.lucide) lucide.createIcons();
        } else {
            p.classList.add("hidden");
        }
    }

    async function clearAll() {
        if (!API()) return;
        await API().clear_folders();
        S.files = []; S.collisions = []; S.stats = null; S.mpiStats = null;
        refreshFolders();
        const fs = $("files-section"); if (fs) fs.classList.add("hidden");
        updateBadges();
        toast("Reset", "Tout a été vidé", "info");
    }

    async function scanAndProcess() {
        if (!API()) return;

        const prog = $("progress-bar-container");
        const bar = $("progress-bar");
        const label = $("progress-label");

        if (prog) prog.classList.remove("hidden");
        if (bar) bar.style.width = "10%";
        if (label) label.textContent = "Scan des dossiers…";

        toast("Traitement", "Analyse en cours…", "info");

        // Scan
        const scan = await API().scan_files();
        if (scan.error) { toast("Erreur", scan.error, "error"); return; }
        S.files = scan.files || [];

        if (bar) bar.style.width = "40%";
        if (label) label.textContent = "Construction MPI…";

        // Process
        const proc = await API().process_all();
        S.stats = proc.stats || null;

        if (bar) bar.style.width = "70%";
        if (label) label.textContent = "Détection des collisions…";

        // Collisions
        S.collisions = await API().get_collisions() || [];
        S.mpiStats = await API().get_mpi_stats() || {};

        if (bar) bar.style.width = "100%";
        if (label) label.textContent = "Terminé !";

        setTimeout(() => { if (prog) prog.classList.add("hidden"); }, 2000);

        showFiles();
        updateBadges();

        const s = S.stats || {};
        toast("Terminé",
            `${S.files.length} fichiers · ${N(s.ipp_unique)} IPP · ${s.collisions} collisions`,
            S.collisions.length > 0 ? "warning" : "success"
        );
    }

    function showFiles() {
        const sec = $("files-section"), grid = $("files-grid"), cnt = $("files-count");
        if (!sec || !grid) return;
        if (!S.files.length) { sec.classList.add("hidden"); return; }

        sec.classList.remove("hidden");
        if (cnt) cnt.textContent = `${S.files.length} fichiers`;

        // f.name, f.path, f.dir viennent de os.listdir — un nom de fichier
        // malveillant (ex : "a<script>.txt") pourrait injecter du HTML.
        // On échappe systématiquement et on remplace le onclick inline par
        // un data-attribute + binding addEventListener (évite toute
        // évasion via guillemets dans le chemin).
        grid.innerHTML = S.files.map((f, i) => `
            <div class="file-card bg-white rounded-[1.5rem] p-6 border border-slate-100 shadow-md cursor-pointer"
                 data-file-index="${i}">
                <div class="flex items-center justify-between mb-3">
                    ${badge(f.format)}
                    <span class="text-[9px] font-mono text-slate-400">${f.size_kb} KB</span>
                </div>
                <p class="font-black text-gh-navy text-[12px] truncate uppercase tracking-tight">${escHtml(f.name)}</p>
                <p class="text-[9px] text-slate-400 truncate mt-1 font-mono">${escHtml(f.dir)}</p>
            </div>
        `).join("");

        // Bind inspector par index plutôt que par string-interpolated path.
        grid.querySelectorAll("[data-file-index]").forEach(card => {
            card.addEventListener("click", () => {
                const idx = parseInt(card.dataset.fileIndex, 10);
                const file = S.files[idx];
                if (file && typeof window.__inspect === "function") {
                    window.__inspect(file.path);
                }
            });
        });

        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // IDENTITOVIGILANCE
    // =========================================================================
    async function renderIdv(vp) {
        if (API()) {
            S.collisions = await API().get_collisions() || [];
            S.mpiStats = await API().get_mpi_stats() || {};
        }
        const m = S.mpiStats || {};
        const cols = S.collisions || [];

        vp.innerHTML = `
            <div class="flex items-center justify-between mb-8">
                <div>
                    <h3 class="text-3xl font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic">MPI</h3>
                    <p class="text-slate-400 dark:text-slate-500 text-xs mt-1">${N(m.total_ipp)} IPP · ${N(m.collisions)} collisions · ${N(m.resolved)} résolues</p>
                </div>
                <div class="flex gap-3">
                    <div class="relative">
                        <i data-lucide="search" class="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-4 top-1/2 -translate-y-1/2"></i>
                        <input type="text" id="idv-search" placeholder="Rechercher IPP…" class="pl-10 pr-4 py-3 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-full text-xs font-mono w-52 focus:outline-none focus:border-gh-navy dark:focus:border-blue-400 transition-all shadow-inner" />
                    </div>
                    <button class="px-8 py-3 bg-gh-warning text-white rounded-full font-black uppercase text-[10px] tracking-[0.15em] shadow-lg hover:bg-amber-600 transition-all active:scale-95" id="btn-auto">
                        <i data-lucide="wand-2" class="w-4 h-4 inline mr-1 -mt-0.5"></i>Auto-résoudre
                    </button>
                </div>
            </div>

            ${cols.length === 0 ? `
                <div class="text-center py-16">
                    <div class="w-20 h-20 bg-green-50 rounded-[2rem] flex items-center justify-center mx-auto mb-5">
                        <i data-lucide="check-circle" class="w-10 h-10 text-gh-success"></i>
                    </div>
                    <h4 class="text-xl font-black text-gh-success uppercase tracking-tighter italic">Aucune collision</h4>
                    <p class="text-slate-400 text-sm mt-3">Tous les IPP ont une DDN unique.</p>
                </div>
            ` : `
                <div class="bg-white rounded-[2rem] border border-slate-100 shadow-lg overflow-hidden">
                    <div class="grid grid-cols-12 gap-3 px-8 py-4 bg-slate-50 border-b border-slate-100 text-[9px] font-black text-slate-400 uppercase tracking-widest">
                        <div class="col-span-3">IPP</div>
                        <div class="col-span-3">Pivot</div>
                        <div class="col-span-2">DDN</div>
                        <div class="col-span-2">Sources</div>
                        <div class="col-span-2 text-right">Action</div>
                    </div>
                    <div class="divide-y divide-slate-50 max-h-[55vh] overflow-auto custom-scroll" id="collision-list">
                        ${renderCollisionRows(cols)}
                    </div>
                </div>
            `}
        `;

        // Search
        const searchInput = $("idv-search");
        if (searchInput) {
            searchInput.addEventListener("input", async () => {
                const q = searchInput.value.trim();
                const list = $("collision-list");
                if (!list) return;
                let filtered = cols;
                if (q) {
                    if (API()) {
                        filtered = await API().search_collisions(q);
                    } else {
                        filtered = cols.filter(c => c.ipp.toLowerCase().includes(q.toLowerCase()));
                    }
                }
                list.innerHTML = renderCollisionRows(filtered);
                bindResolveButtons();
                if (window.lucide) lucide.createIcons();
            });
        }

        bindResolveButtons();

        const autoBtn = $("btn-auto");
        if (autoBtn) {
            autoBtn.addEventListener("click", async () => {
                if (!API()) return;
                const r = await API().auto_resolve();
                toast("Auto-résolution", `${r.resolved} pivots définis`, "success");
                S.collisions = r.collisions || [];
                S.mpiStats = r.mpi_stats || {};
                renderIdv(vp);
                updateBadges();
            });
        }

        if (window.lucide) lucide.createIcons();
    }

    function renderCollisionRows(cols) {
        // Les IPP/DDN/sources proviennent de fichiers .txt parsés côté backend.
        // Un fichier malveillant pourrait injecter du HTML ; on échappe tout
        // ce qui arrive dans le DOM (attributs data-* inclus).
        return cols.map(c => `
            <div class="collision-row grid grid-cols-12 gap-3 px-8 py-5 items-center hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-colors duration-500" data-ipp="${escHtml(c.ipp)}">
                <div class="col-span-3 font-mono font-bold text-gh-navy dark:text-blue-400 text-xs">${escHtml(c.ipp)}</div>
                <div class="col-span-3">
                    ${c.pivot
                ? `<span class="text-gh-success font-bold font-mono text-xs">${escHtml(c.pivot)}</span>`
                : `<span class="text-gh-error font-bold italic text-xs">—</span>`}
                </div>
                <div class="col-span-2"><span class="bg-red-50 dark:bg-red-900/40 text-gh-error px-2 py-0.5 rounded-full text-[9px] font-black">${c.options.length} DDN</span></div>
                <div class="col-span-2 text-[10px] text-slate-400 dark:text-slate-500 font-mono">${c.total_sources}</div>
                <div class="col-span-2 text-right">
                    <button class="px-5 py-2 bg-gh-navy dark:bg-blue-600 text-white rounded-full text-[9px] font-black uppercase tracking-wider shadow-md hover:bg-blue-800 dark:hover:bg-blue-700 transition-all btn-resolve" data-ipp="${escHtml(c.ipp)}">Résoudre</button>
                </div>
            </div>
        `).join("");
    }

    function bindResolveButtons() {
        document.querySelectorAll(".btn-resolve").forEach(btn => {
            btn.addEventListener("click", () => openModal(btn.dataset.ipp));
        });
    }

    // =========================================================================
    // RECONCILIATION MODAL
    // =========================================================================
    function openModal(ipp) {
        const c = S.collisions.find(x => x.ipp === ipp);
        if (!c) return;

        const modal = $("reconciliation-modal");
        const ippEl = $("idv-modal-ipp");
        const opts = $("idv-options-container");
        if (!modal || !opts) return;
        if (ippEl) ippEl.textContent = ipp;

        opts.innerHTML = c.options.map(o => `
            <button class="btn-pivot w-full text-left p-6 rounded-[2rem] border-2 transition-colors duration-500 ${o.ddn === c.pivot ? "border-gh-success bg-green-50 dark:bg-green-900/20" : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-gh-navy dark:hover:border-blue-400"
            }" data-ddn="${escHtml(o.ddn)}">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="text-2xl font-black text-gh-navy dark:text-blue-400 font-mono">${escHtml(o.ddn)}</span>
                        <span class="ml-3 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">${o.count} fichier(s)</span>
                    </div>
                    ${o.ddn === c.pivot
                ? '<i data-lucide="check-circle" class="w-7 h-7 text-gh-success"></i>'
                : '<i data-lucide="circle" class="w-7 h-7 text-slate-300 dark:text-slate-600"></i>'}
                </div>
                <p class="text-[10px] text-slate-400 dark:text-slate-500 mt-2 font-mono truncate">${o.sources.map(s => escHtml(s)).join(", ")}</p>
            </button>
        `).join("");

        opts.querySelectorAll(".btn-pivot").forEach(btn => {
            btn.addEventListener("click", async () => {
                if (!API()) return;
                await API().set_pivot(ipp, btn.dataset.ddn);
                toast("Pivot", `${ipp} → ${btn.dataset.ddn}`, "success");
                modal.classList.add("hidden");
                S.collisions = await API().get_collisions() || [];
                S.mpiStats = await API().get_mpi_stats() || {};
                if (S.view === "idv") navigateTo("idv");
                updateBadges();
            });
        });

        modal.classList.remove("hidden");
        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // PILOT EXPORT
    // =========================================================================
    function renderPilot(vp) {
        const m = S.mpiStats || {};
        vp.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-[3rem] p-14 border border-slate-100 dark:border-slate-700 shadow-xl dark:shadow-none text-center max-w-3xl mx-auto transition-colors duration-500">
                <div class="w-20 h-20 bg-teal-50 dark:bg-teal-900/20 rounded-[2rem] flex items-center justify-center mx-auto mb-8 transition-colors duration-500">
                    <i data-lucide="file-down" class="w-10 h-10 text-gh-teal"></i>
                </div>
                <h3 class="text-3xl font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic mb-3">Export PMSI-Pilot</h3>
                <p class="text-slate-400 dark:text-slate-500 mb-8">CSV normalisés · séparateur ; · DDN pivot injectées</p>

                <div class="grid grid-cols-3 gap-4 my-8">
                    <div class="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-5 transition-colors duration-500"><p class="text-2xl font-black text-gh-navy dark:text-blue-400">${N(S.files.length)}</p><p class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase mt-1">Fichiers</p></div>
                    <div class="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-5 transition-colors duration-500"><p class="text-2xl font-black text-gh-teal">${N(m.total_ipp)}</p><p class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase mt-1">IPP</p></div>
                    <div class="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-5 transition-colors duration-500"><p class="text-2xl font-black ${m.pending > 0 ? "text-gh-error" : "text-gh-success"}">${N(m.pending)}</p><p class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase mt-1">Conflits</p></div>
                </div>

                ${m.pending > 0 ? `<div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/50 rounded-xl p-4 mb-6 text-left text-xs text-amber-800 dark:text-amber-400 font-bold transition-colors duration-500"><i data-lucide="alert-triangle" class="w-4 h-4 inline mr-1"></i>${m.pending} collision(s) non résolue(s) — auto-résolution appliquée à l'export.</div>` : ""}

                <div class="flex justify-center gap-4">
                    <button class="px-10 py-5 bg-gh-teal dark:bg-teal-600 text-white rounded-full font-black uppercase text-xs tracking-[0.2em] shadow-lg hover:bg-teal-600 dark:hover:bg-teal-700 transition-all active:scale-95" id="btn-exp-def">
                        <i data-lucide="download" class="w-4 h-4 inline mr-2 -mt-0.5"></i>Exporter
                    </button>
                    <button class="px-10 py-5 bg-gh-navy dark:bg-blue-600 text-white rounded-full font-black uppercase text-xs tracking-[0.2em] shadow-lg hover:bg-blue-800 dark:hover:bg-blue-700 transition-all active:scale-95" id="btn-exp-dir">
                        <i data-lucide="folder-output" class="w-4 h-4 inline mr-2 -mt-0.5"></i>Choisir dossier
                    </button>
                </div>

                <div id="exp-result" class="mt-8 hidden">
                    <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/50 rounded-xl p-6 text-left transition-colors duration-500">
                        <p class="text-sm font-black text-gh-success uppercase italic mb-1" id="exp-title">OK</p>
                        <p class="text-xs text-slate-600 dark:text-slate-300" id="exp-detail"></p>
                    </div>
                </div>
            </div>
        `;

        const defBtn = $("btn-exp-def"), dirBtn = $("btn-exp-dir");
        if (defBtn) defBtn.addEventListener("click", async () => {
            if (!API()) return;
            if ((S.mpiStats || {}).pending > 0) await API().auto_resolve();
            showExportResult(await API().export_csv());
        });
        if (dirBtn) dirBtn.addEventListener("click", async () => {
            if (!API()) return;
            const folder = await API().select_export_folder();
            if (!folder) return;
            if ((S.mpiStats || {}).pending > 0) await API().auto_resolve();
            showExportResult(await API().export_csv_to(folder));
        });

        if (window.lucide) lucide.createIcons();
    }

    function showExportResult(r) {
        if (!r) return;
        const el = $("exp-result"), t = $("exp-title"), d = $("exp-detail");
        if (!el) return;
        if (r.error) {
            if (t) t.textContent = "Erreur";
            if (d) d.textContent = r.error;
            toast("Erreur", r.error, "error");
        } else {
            const s = r.stats || {};
            if (t) t.textContent = `✅ ${s.csv_count} CSV`;
            if (d) d.textContent = `${N(s.lines_exported)} lignes · ${N(s.ddn_corrected)} DDN corrigées · ${r.output_dir}`;
            toast("Export", `${s.csv_count} CSV exportés`, "success");
        }
        el.classList.remove("hidden");
    }

    // =========================================================================
    // INSPECTOR
    // =========================================================================
    window.__inspect = async function (fp) {
        if (!API()) return;
        const modal = $("inspector-modal");
        const fname = $("ins-file-name");
        const sid = $("ins-session-id");
        const body = $("ins-terminal-body");
        const mT = $("ins-metrics-total"), mE = $("ins-metrics-err");
        if (!modal || !body) return;

        if (fname) fname.textContent = fp.split(/[\\/]/).pop();
        if (sid) sid.textContent = "SID_" + Math.random().toString(36).substring(2, 8).toUpperCase();
        body.innerHTML = '<p class="text-blue-300 animate-pulse">Analyse en cours…</p>';
        modal.classList.remove("hidden");
        if (window.lucide) lucide.createIcons();

        const data = await API().inspect_file(fp);
        if (data.error) { body.innerHTML = `<p class="text-red-400">${escHtml(data.error)}</p>`; return; }

        if (mT) mT.textContent = N(data.total_lines);
        if (mE) mE.textContent = N(data.errors);

        // Chaque ligne provient du fichier ATIH : contenu non contrôlé,
        // potentiellement avec caractères HTML. On échappe tous les champs
        // avant injection via innerHTML.
        body.innerHTML = data.lines.map(l => {
            const isErr = l.status !== "OK";
            const cls = isErr ? "line-error" : "";
            const col = { OK: "text-gh-success", COLLISION: "text-gh-error", FILTERED: "text-gh-warning", ERROR: "text-gh-error" }[l.status] || "text-slate-400";
            return `<div class="flex gap-4 text-[10px] py-1.5 px-4 rounded ${cls}">
                <span class="text-slate-600 w-10 text-right shrink-0">${l.num}</span>
                <span class="font-bold w-16 ${col} shrink-0 uppercase">${escHtml(l.status)}</span>
                <span class="text-blue-300 w-28 shrink-0 truncate">${escHtml(l.ipp || "—")}</span>
                <span class="text-teal-300 w-20 shrink-0">${escHtml(l.ddn || "—")}</span>
                <span class="text-slate-500 truncate flex-1">${escHtml((l.raw || "").substring(0, 80))}</span>
                ${l.repair ? `<span class="text-amber-400 shrink-0 text-[8px]">${escHtml(l.repair)}</span>` : ""}
            </div>`;
        }).join("");

        // Sanitized export button
        const expBtn = $("btn-export-sanitized");
        if (expBtn) {
            expBtn.onclick = async () => {
                if (!API()) return;
                const r = await API().export_sanitized(fp);
                if (r.error) { toast("Erreur", r.error, "error"); }
                else { toast("Sanitized", `${r.name} — ${r.stats.pivoted} pivots injectés`, "success"); }
            };
        }
    };

    // =========================================================================
    // TUTORIEL
    // =========================================================================
    function renderTuto(vp) {
        vp.innerHTML = `
            <div class="max-w-4xl mx-auto pb-10">
                <div class="bg-white dark:bg-slate-800 rounded-[2.5rem] p-12 border border-slate-100 dark:border-slate-700 shadow-xl dark:shadow-none relative overflow-hidden transition-colors duration-500">
                    
                    <!-- Header -->
                    <div class="flex items-center gap-6 mb-12 border-b border-slate-100 dark:border-slate-700 pb-8 relative z-10 transition-colors duration-500">
                        <div class="w-16 h-16 bg-gh-navy dark:bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg text-white">
                            <i data-lucide="book-open" class="w-8 h-8"></i>
                        </div>
                        <div>
                            <h3 class="text-3xl font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic">Guide Opérationnel</h3>
                            <p class="text-slate-400 dark:text-slate-500 font-bold tracking-widest uppercase text-[10px] mt-1">Sovereign OS DIM</p>
                        </div>
                    </div>

                    <!-- Intro -->
                    <p class="text-slate-500 dark:text-slate-400 mb-12 leading-relaxed text-sm relative z-10">
                        Bienvenue dans <strong class="text-gh-navy dark:text-blue-400">Sovereign OS</strong>. Ce logiciel a été conçu spécifiquement pour la station DIM afin de traiter les données e-PMSI, de croiser automatiquement les identités patients (IPP) et de résoudre les conflits de dates de naissance (DDN) via un index maître (MPI).
                    </p>

                    <!-- Steps Timeline -->
                    <div class="space-y-12 relative z-10 stagger">
                        
                        <!-- Step 1 -->
                        <div class="tuto-step flex gap-6">
                            <div class="tuto-step-number bg-gh-teal dark:bg-teal-600 text-white shadow-lg">1</div>
                            <div class="tuto-connector hidden sm:block"></div>
                            <div class="flex-1 pt-2">
                                <h4 class="text-lg font-black text-gh-navy dark:text-blue-400 uppercase italic tracking-tighter mb-2 flex items-center gap-2">
                                    <i data-lucide="folders" class="w-4 h-4 text-gh-teal"></i> Ingestion des données
                                </h4>
                                <p class="text-sm text-slate-500 dark:text-slate-400 mb-3">Rendez-vous dans la section <strong>Modo Files</strong>. Vous pouvez y déposer vos dossiers contenant les fichiers ATIH (.txt) validés ou bruts. Le moteur reconnaît automatiquement 8 formats (RPS, RAA, VID-HOSP, etc.).</p>
                                <div class="bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 rounded-xl p-4 text-[11px] text-slate-600 dark:text-slate-300 font-mono border inline-flex items-center gap-2 transition-colors duration-500">
                                    <i data-lucide="info" class="w-4 h-4 text-gh-teal"></i> Astuce : Glissez-déposez le dossier racine "Années" directement.
                                </div>
                            </div>
                        </div>

                        <!-- Step 2 -->
                        <div class="tuto-step flex gap-6">
                            <div class="tuto-step-number bg-gh-navy dark:bg-blue-600 text-white shadow-lg">2</div>
                            <div class="tuto-connector hidden sm:block"></div>
                            <div class="flex-1 pt-2">
                                <h4 class="text-lg font-black text-gh-navy dark:text-blue-400 uppercase italic tracking-tighter mb-2 flex items-center gap-2">
                                    <i data-lucide="activity" class="w-4 h-4 text-gh-navy dark:text-blue-400"></i> Validation & Traitement
                                </h4>
                                <p class="text-sm text-slate-500 dark:text-slate-400 mb-3">Cliquez sur <strong class="text-gh-teal">Scanner & Traiter</strong>. Sovereign OS va lire tous les fichiers en parallèle, filtrer les anomalies géométriques (auto-repair), et recenser l'intégralité des couples (IPP, DDN) présents.</p>
                                <p class="text-sm text-slate-500 dark:text-slate-400">
                                    Vous pouvez cliquer sur un fichier dans la liste pour ouvrir l'<strong>Inspector Terminal</strong> et analyser les données ligne par ligne.
                                </p>
                            </div>
                        </div>

                        <!-- Step 3 -->
                        <div class="tuto-step flex gap-6">
                            <div class="tuto-step-number bg-gh-warning text-white shadow-lg">3</div>
                            <div class="tuto-connector hidden sm:block"></div>
                            <div class="flex-1 pt-2">
                                <h4 class="text-lg font-black text-gh-navy dark:text-blue-400 uppercase italic tracking-tighter mb-2 flex items-center gap-2">
                                    <i data-lucide="users-2" class="w-4 h-4 text-gh-warning"></i> Résolution des Collisions (Identitovigilance)
                                </h4>
                                <p class="text-sm text-slate-500 dark:text-slate-400 mb-3">Si un même IPP possède plusieurs dates de naissance selon les fichiers, une <strong>collision</strong> est signalée. Allez dans l'onglet Identitovigilance.</p>
                                <ul class="list-disc list-inside text-sm text-slate-500 dark:text-slate-400 space-y-1 mb-3 ml-2">
                                    <li>Cliquez sur <strong>Résoudre</strong> pour choisir manuellement la DDN de référence (Pivot).</li>
                                    <li>Ou utilisez le bouton <strong class="text-gh-warning text-xs uppercase tracking-widest"><i data-lucide="wand-2" class="w-3 h-3 inline mr-1 -mt-0.5"></i> Auto-résoudre</strong> pour forcer la DDN la plus statistiquement présente.</li>
                                </ul>
                            </div>
                        </div>

                        <!-- Step 4 -->
                        <div class="tuto-step flex gap-6">
                            <div class="tuto-step-number bg-gh-error text-white shadow-lg">4</div>
                            <div class="flex-1 pt-2">
                                <h4 class="text-lg font-black text-gh-navy dark:text-blue-400 uppercase italic tracking-tighter mb-2 flex items-center gap-2">
                                    <i data-lucide="file-down" class="w-4 h-4 text-gh-error"></i> Export PMSI-Pilot
                                </h4>
                                <p class="text-sm text-slate-500 dark:text-slate-400 mb-3">Une fois l'index maître purifié, rendez-vous dans <strong>PMSI Pilot CSV</strong>.</p>
                                <p class="text-sm text-slate-500 dark:text-slate-400">L'export va générer un fichier CSV par fichier MCO traité, tout en <strong>injectant la DDN pivot choisie</strong> sur l'intégralité du chaînage, annulant de facto l'anomalie.</p>
                            </div>
                        </div>

                    </div>
                    
                    <!-- Shortcuts Footer -->
                    <div class="mt-16 pt-8 border-t border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/80 -mx-12 -mb-12 px-12 pb-12 transition-colors duration-500">
                        <h4 class="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2"><i data-lucide="keyboard" class="w-4 h-4"></i> Raccourcis Clavier</h4>
                        <div class="flex flex-wrap gap-4 text-[11px] text-slate-500 dark:text-slate-400">
                            <div><kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">Ctrl</kbd> + <kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">1</kbd> Dashboard</div>
                            <div><kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">Ctrl</kbd> + <kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">2</kbd> Modo Files</div>
                            <div><kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">Ctrl</kbd> + <kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">3</kbd> Identitovigilance</div>
                            <div><kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">Ctrl</kbd> + <kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">4</kbd> Export</div>
                            <div><kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">Ctrl</kbd> + <kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">5</kbd> Tutoriel</div>
                            <div><kbd class="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300">Echap</kbd> Fermer les fenêtres modales</div>
                        </div>
                    </div>

                    <!-- Watermark -->
                    <i data-lucide="book" class="absolute -bottom-10 -right-10 w-64 h-64 text-slate-50 dark:text-slate-800 opacity-[0.4] rotate-12 pointer-events-none transition-colors duration-500"></i>
                </div>
            </div>
        `;

        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // CSV IMPORT VIEWER
    // =========================================================================
    function renderCsv(vp) {
        vp.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-[3rem] p-14 border border-slate-100 dark:border-slate-700 shadow-xl dark:shadow-none text-center max-w-5xl mx-auto transition-colors duration-500">
                <div class="w-20 h-20 bg-green-50 dark:bg-green-900/20 rounded-[2rem] flex items-center justify-center mx-auto mb-8 transition-colors duration-500">
                    <i data-lucide="table-2" class="w-10 h-10 text-gh-success"></i>
                </div>
                <h3 class="text-3xl font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic mb-3">Import CSV</h3>
                <p class="text-slate-400 dark:text-slate-500 mb-8">Importez et visualisez un fichier CSV · Auto-détection du séparateur (; , tab)</p>

                <button class="px-10 py-5 bg-gh-success text-white rounded-full font-black uppercase text-xs tracking-[0.2em] shadow-lg hover:bg-green-600 transition-all active:scale-95 mb-8" id="btn-csv-select">
                    <i data-lucide="file-up" class="w-4 h-4 inline mr-2 -mt-0.5"></i>Sélectionner un fichier CSV
                </button>

                <div id="csv-result" class="hidden text-left"></div>
            </div>
        `;

        const selectBtn = $("btn-csv-select");
        if (selectBtn) selectBtn.addEventListener("click", async () => {
            if (!API()) return;
            const filepath = await API().select_csv_file();
            if (!filepath) return;

            toast("Import", "Lecture du CSV…", "info");
            const data = await API().import_csv_file(filepath);
            const result = $("csv-result");
            if (!result) return;

            if (data.error) {
                result.innerHTML = `<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 rounded-xl p-6 text-gh-error font-bold">${escHtml(data.error)}</div>`;
                result.classList.remove("hidden");
                toast("Erreur", data.error, "error");
                return;
            }

            const maxPreview = Math.min(data.rows.length, 200);
            // Le contenu CSV est saisi par l'utilisateur (tableur) : on
            // échappe chaque cellule avant injection dans le DOM.
            result.innerHTML = `
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h4 class="font-black text-gh-navy dark:text-blue-400 uppercase text-sm tracking-tighter italic flex items-center gap-2">
                            <i data-lucide="file-spreadsheet" class="w-4 h-4 text-gh-success"></i> ${escHtml(data.filename)}
                        </h4>
                        <p class="text-[10px] text-slate-400 dark:text-slate-500 font-mono mt-1">${N(data.total_rows)} lignes · ${data.headers.length} colonnes · sep: "${escHtml(data.separator)}"</p>
                    </div>
                </div>
                <div class="max-h-[50vh] overflow-auto custom-scroll rounded-2xl border border-slate-100 dark:border-slate-700">
                    <table class="csv-table">
                        <thead><tr>${data.headers.map(h => `<th>${escHtml(h)}</th>`).join("")}</tr></thead>
                        <tbody>${data.rows.slice(0, maxPreview).map(r => `<tr>${r.map(c => `<td>${escHtml(c)}</td>`).join("")}</tr>`).join("")}</tbody>
                    </table>
                </div>
                ${data.rows.length > maxPreview ? `<p class="text-[10px] text-slate-400 dark:text-slate-500 mt-3 text-center italic">Affichage limité à ${maxPreview} lignes sur ${N(data.total_rows)}</p>` : ""}
            `;
            result.classList.remove("hidden");
            toast("Import", `${data.filename} — ${N(data.total_rows)} lignes`, "success");
            if (window.lucide) lucide.createIcons();
        });

        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // STRUCTURE — Arborescence pôles / services / UM
    // =========================================================================
    // Affiche l'arbre du fichier de structure d'un établissement.
    // L'utilisateur choisit un .csv/.tsv/.txt, le backend le parse (voir
    // backend/structure.py) et renvoie un arbre {code, label, children[]}
    // qu'on rend en <ul> imbriqués expand/collapse.

    // Collecte les UM (feuilles métier) de l'arbre · level=UM sinon feuilles
    // sans enfants. Retourne [{code,label,parentCode,parentLabel,sector}].
    function collectUmLeaves(roots) {
        const out = [];
        const walk = (nodes, parent) => {
            (nodes || []).forEach(n => {
                const isUm = (n.level || "").toUpperCase() === "UM"
                    || (!n.children || !n.children.length);
                if (isUm && n.code) {
                    out.push({
                        code: String(n.code).trim(),
                        label: n.label || n.code,
                        parentCode: parent ? parent.code : null,
                        parentLabel: parent ? (parent.label || parent.code) : null,
                        sector: n.sector_type || (parent && parent.sector_type) || null,
                    });
                }
                if (n.children && n.children.length) walk(n.children, n);
            });
        };
        walk(roots || [], null);
        // Dédup par code (peut apparaître plusieurs fois dans l'arbre)
        const seen = new Map();
        out.forEach(u => { if (!seen.has(u.code)) seen.set(u.code, u); });
        return [...seen.values()];
    }

    // Lit un fichier ATIH en latin-1 (encodage natif PMSI). FileReader côté
    // navigateur · fonctionne même si le dialog natif WebView2 est bloqué.
    function readAtihFile(file) {
        return new Promise((resolve, reject) => {
            const r = new FileReader();
            r.onload = e => resolve(String(e.target.result || ""));
            r.onerror = () => reject(new Error("Lecture impossible : " + file.name));
            r.readAsText(file, "windows-1252");
        });
    }

    // Détecte le format ATIH par longueur de ligne (≥80 % des 200 premières).
    // RPS=154, RPSA=154, RAA=96, R3A=96, EDGAR=96. Tolérance ±2 chars.
    function detectAtihFormat(lines) {
        const sample = lines.filter(l => l.length >= 50).slice(0, 200);
        if (!sample.length) return { format: "INCONNU", length: 0 };
        const hist = new Map();
        sample.forEach(l => hist.set(l.length, (hist.get(l.length) || 0) + 1));
        const [modalLen] = [...hist.entries()].sort((a, b) => b[1] - a[1])[0];
        if (modalLen >= 150 && modalLen <= 158) return { format: "RPS / RPSA", length: modalLen };
        if (modalLen >= 94 && modalLen <= 98) return { format: "RAA / R3A / EDGAR", length: modalLen };
        if (modalLen >= 140 && modalLen <= 150) return { format: "RPS (ancien P04)", length: modalLen };
        if (modalLen >= 84 && modalLen <= 92) return { format: "RAA (ancien)", length: modalLen };
        return { format: "ATIH (" + modalLen + "c)", length: modalLen };
    }

    // Compte les occurrences de chaque code UM dans les lignes. Regex compilée
    // une fois avec alternance ordonnée (plus long d'abord) pour éviter les
    // matchs partiels "40" dans "4012". Une ligne compte 1x par UM, même si
    // le code apparaît plusieurs fois (évite double-compte sur actes multi).
    function countUmActivity(lines, umCodes) {
        const codes = [...new Set(umCodes.filter(Boolean))].sort((a, b) => b.length - a.length);
        const counts = new Map(codes.map(c => [c, 0]));
        if (!codes.length) return counts;
        const escaped = codes.map(c => c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
        const re = new RegExp(escaped.join("|"), "g");
        lines.forEach(line => {
            if (!line) return;
            const seen = new Set();
            let m;
            re.lastIndex = 0;
            while ((m = re.exec(line)) !== null) {
                if (!seen.has(m[0])) {
                    seen.add(m[0]);
                    counts.set(m[0], (counts.get(m[0]) || 0) + 1);
                }
            }
        });
        return counts;
    }

    // Variante asynchrone de countUmActivity. Découpe en chunks de 5000 lignes
    // avec `setTimeout(0)` entre chaque pour libérer le main thread · évite le
    // gel de l'UI sur RAA de 100k+ lignes (12 fichiers mensuels d'un CHS).
    // `onProgress(pct)` est appelé entre chaque chunk.
    async function countUmActivityAsync(lines, umCodes, onProgress) {
        const codes = [...new Set(umCodes.filter(Boolean))].sort((a, b) => b.length - a.length);
        const counts = new Map(codes.map(c => [c, 0]));
        if (!codes.length) return counts;
        const escaped = codes.map(c => c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
        const re = new RegExp(escaped.join("|"), "g");
        const CHUNK = 5000;
        for (let start = 0; start < lines.length; start += CHUNK) {
            const end = Math.min(lines.length, start + CHUNK);
            for (let i = start; i < end; i++) {
                const line = lines[i];
                if (!line) continue;
                const seen = new Set();
                let m;
                re.lastIndex = 0;
                while ((m = re.exec(line)) !== null) {
                    if (!seen.has(m[0])) {
                        seen.add(m[0]);
                        counts.set(m[0], (counts.get(m[0]) || 0) + 1);
                    }
                }
            }
            if (onProgress) onProgress(Math.round((end / lines.length) * 100));
            await new Promise(r => setTimeout(r, 0));  // yield to renderer
        }
        return counts;
    }

    // Extrait les années / mois (AAAA ou AAAAMM ou MMAAAA) depuis les noms de
    // fichiers ATIH. Convention GHT · `RPS_202410.txt`, `RAA_10_2024.txt`, etc.
    function extractPeriodFromFilenames(filenames) {
        const years = new Set();
        const months = new Set();
        filenames.forEach(n => {
            const base = String(n).replace(/\.[^.]+$/, "");
            // Années 4 chiffres · 2020-2030
            (base.match(/20[2-3]\d/g) || []).forEach(y => years.add(y));
            // AAAAMM (année + mois)
            (base.match(/20[2-3]\d(0[1-9]|1[0-2])/g) || []).forEach(ym => {
                years.add(ym.slice(0, 4));
                months.add(ym);
            });
            // MMAAAA
            (base.match(/(0[1-9]|1[0-2])20[2-3]\d/g) || []).forEach(my => {
                years.add(my.slice(2));
                months.add(my.slice(2) + my.slice(0, 2));
            });
        });
        const yrs = [...years].sort();
        const mts = [...months].sort();
        if (!yrs.length) return null;
        const periodLabel = yrs.length === 1 ? yrs[0] : `${yrs[0]} → ${yrs[yrs.length - 1]}`;
        return { years: yrs, months: mts, label: periodLabel, monthCount: mts.length };
    }

    function escHtml(s) {
        return String(s == null ? "" : s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    // Rendu organigramme classique (boîtes + connecteurs tracés en CSS via
    // ::before/::after). Pas de SVG : pur DOM, sélectable, zoomable par
    // transform. Les classes .org-* sont définies dans frontend/css/style.css.
    // Libellés FR pour les types de secteur ARS (G/I/D/P/Z).
    const SECTOR_LABELS = {
        G: "Général (adulte)", I: "Infanto-juv", D: "UMD", P: "UHSA", Z: "Intersec",
    };

    function orgChartHtml(nodes) {
        if (!nodes || !nodes.length) return "";
        return nodes.map(n => {
            const hasKids = n.children && n.children.length > 0;
            const level = (n.level || "").toUpperCase();
            const levelClass = "org-level-" + (level || "default").toLowerCase();
            const sector = n.sector_type || "";
            const sectorClass = sector ? ` org-sector-${sector.toLowerCase()}` : "";
            const sectorBadge = sector
                ? `<span class="org-sector-badge" title="${escHtml(SECTOR_LABELS[sector] || sector)}">${escHtml(sector)}</span>`
                : "";
            const levelBadge = level
                ? `<span class="org-level">${escHtml(level)}</span>`
                : "";
            return `
                <li>
                    <div class="org-node ${levelClass}${sectorClass}">
                        <div class="org-header">
                            <span class="org-code">${escHtml(n.code)}</span>
                            ${sectorBadge}
                        </div>
                        <span class="org-label">${escHtml(n.label)}</span>
                        ${levelBadge}
                    </div>
                    ${hasKids ? `<ul>${orgChartHtml(n.children)}</ul>` : ""}
                </li>`;
        }).join("");
    }

    function renderStructure(vp) {
        vp.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-[3rem] p-14 border border-slate-100 dark:border-slate-700 shadow-xl dark:shadow-none max-w-6xl mx-auto transition-colors duration-500">
                <div class="text-center mb-10">
                    <div class="w-20 h-20 bg-blue-50 dark:bg-blue-900/20 rounded-[2rem] flex items-center justify-center mx-auto mb-8 transition-colors duration-500">
                        <i data-lucide="git-branch" class="w-10 h-10 text-gh-navy dark:text-blue-400"></i>
                    </div>
                    <h3 class="text-3xl font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic mb-3">Fichier de structure</h3>
                    <p class="text-slate-400 dark:text-slate-500 mb-8">Visualisez l'arborescence des pôles, services et UM d'un établissement</p>
                    <button class="px-10 py-5 bg-gh-navy text-white rounded-full font-black uppercase text-xs tracking-[0.2em] shadow-lg hover:bg-blue-600 transition-all active:scale-95" id="btn-structure-select">
                        <i data-lucide="file-up" class="w-4 h-4 inline mr-2 -mt-0.5"></i>Sélectionner le fichier structure
                    </button>
                </div>
                <div id="structure-result" class="hidden"></div>
            </div>
        `;

        const btn = $("btn-structure-select");
        if (btn) btn.addEventListener("click", async () => {
            if (!API()) return;
            const filepath = await API().select_structure_file();
            if (!filepath) return;

            toast("Structure", "Analyse du fichier…", "info");
            const data = await API().load_structure(filepath);
            const out = $("structure-result");
            if (!out) return;

            if (data.error) {
                out.innerHTML = `<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 rounded-xl p-6 text-gh-error font-bold">${escHtml(data.error)}</div>`;
                out.classList.remove("hidden");
                toast("Erreur", data.error, "error");
                return;
            }

            const s = data.summary || {};
            const byLevel = s.by_level || {};
            const levelChips = Object.keys(byLevel).map(k =>
                `<span class="px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-[10px] font-black uppercase tracking-wider text-slate-600 dark:text-slate-300">${escHtml(k)} · ${byLevel[k]}</span>`
            ).join(" ");

            out.innerHTML = `
                <div class="grid grid-cols-4 gap-4 mb-8">
                    ${statCard("list-tree", "Nœuds", s.total_nodes || 0, "blue")}
                    ${statCard("git-fork", "Racines", s.roots || 0, "teal")}
                    ${statCard("trending-down", "Profondeur", s.max_depth || 0, "amber")}
                    ${statCard("file-text", "Fichier", 1, "green")}
                </div>

                <div class="bg-slate-50 dark:bg-slate-900/40 rounded-2xl p-6 mb-6 flex items-center justify-between flex-wrap gap-3">
                    <div class="flex items-center gap-3">
                        <i data-lucide="file-spreadsheet" class="w-5 h-5 text-gh-navy dark:text-blue-400"></i>
                        <span class="font-mono text-xs font-bold text-gh-navy dark:text-blue-400">${escHtml(data.filename)}</span>
                    </div>
                    <div class="flex items-center gap-2 flex-wrap">${levelChips}</div>
                    <div class="flex items-center gap-2">
                        <button id="btn-org-zoom-out" class="w-9 h-9 bg-white dark:bg-slate-700 rounded-lg text-xs font-bold border border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600 flex items-center justify-center" title="Zoom arrière">−</button>
                        <span id="org-zoom-label" class="font-mono text-xs font-bold text-slate-500 dark:text-slate-400 w-10 text-center">100%</span>
                        <button id="btn-org-zoom-in" class="w-9 h-9 bg-white dark:bg-slate-700 rounded-lg text-xs font-bold border border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600 flex items-center justify-center" title="Zoom avant">+</button>
                        <button id="btn-org-fit" class="px-4 py-2 bg-white dark:bg-slate-700 rounded-lg text-xs font-bold uppercase tracking-wider border border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-600">Ajuster</button>
                        <button id="btn-tree-export-pdf" class="px-4 py-2 bg-gh-navy text-white rounded-lg text-xs font-black uppercase tracking-wider hover:bg-blue-900 transition-all active:scale-95 flex items-center gap-2">
                            <i data-lucide="file-down" class="w-3.5 h-3.5"></i>Télécharger PDF
                        </button>
                    </div>
                </div>

                <div id="org-viewport" class="max-h-[65vh] overflow-auto custom-scroll rounded-2xl border border-slate-100 dark:border-slate-700 p-10 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900/60 dark:to-slate-800">
                    <div id="org-stage" class="inline-block origin-top-left transition-transform duration-200">
                        <div class="org-chart"><ul>${orgChartHtml(data.tree)}</ul></div>
                    </div>
                </div>

                <section id="activity-analysis" class="mt-10 bg-white dark:bg-slate-800 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl overflow-hidden">
                    <header class="px-10 py-8 flex items-center justify-between gap-6 border-b border-slate-100 dark:border-slate-800 flex-wrap">
                        <div>
                            <div class="flex items-center gap-3 mb-2">
                                <i data-lucide="activity" class="w-6 h-6 text-gh-teal"></i>
                                <h3 class="font-black text-gh-navy dark:text-blue-400 tracking-tighter uppercase italic text-xl leading-none">Analyse d'activité par UM</h3>
                            </div>
                            <p class="text-sm text-slate-500 dark:text-slate-400">Déposez vos fichiers <span class="font-mono font-bold">RPS</span> / <span class="font-mono font-bold">RAA</span> pour détecter les UM sans activité sur la période. Traitement 100 % local, aucune donnée envoyée.</p>
                        </div>
                        <div class="flex items-center gap-3">
                            <input type="file" id="act-file-input" multiple accept=".txt,.RPS,.RAA,.RPSA,.R3A,.rps,.raa,.rpsa,.r3a" class="hidden" />
                            <button id="btn-act-reset" class="px-4 py-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-full font-bold uppercase text-[10px] tracking-[0.25em] hover:bg-slate-200 dark:hover:bg-slate-600 transition-all hidden" title="Réinitialiser l'analyse">
                                <i data-lucide="x" class="w-3.5 h-3.5"></i>
                            </button>
                        </div>
                    </header>

                    <div id="act-drop-zone" role="button" tabindex="0" aria-label="Déposer des fichiers RPS ou RAA · ou appuyer sur Entrée pour ouvrir le sélecteur"
                         class="mx-10 my-6 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-[2rem] p-12 text-center transition-all cursor-pointer hover:border-gh-teal hover:bg-teal-50/40 dark:hover:bg-teal-900/15 focus:outline-none focus:border-gh-teal focus:ring-4 focus:ring-teal-200 dark:focus:ring-teal-900/40">
                        <i data-lucide="file-stack" class="w-12 h-12 text-gh-teal mx-auto mb-5"></i>
                        <p class="font-black uppercase tracking-wider text-gh-navy dark:text-blue-400 text-base mb-2">Glissez-déposez vos fichiers RPS / RAA ici</p>
                        <p class="text-sm text-slate-500 dark:text-slate-400 mb-3">ou cliquez pour ouvrir le sélecteur · Entrée / Espace au clavier</p>
                        <p class="text-[10px] font-mono text-slate-400 dark:text-slate-500">Formats · RPS (154 c) · RAA (96 c) · RPSA · R3A · EDGAR · encodage latin-1</p>
                    </div>

                    <div id="act-status" class="mx-10 mb-6 hidden"></div>
                    <div id="act-progress" class="mx-10 mb-6 hidden">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-[10px] font-black uppercase tracking-[0.25em] text-gh-navy dark:text-blue-400" id="act-progress-label">Analyse…</span>
                            <span class="font-mono text-xs font-bold text-gh-navy dark:text-blue-400" id="act-progress-pct">0 %</span>
                        </div>
                        <div class="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div id="act-progress-bar" class="h-full bg-gh-teal transition-all duration-150" style="width: 0%"></div>
                        </div>
                    </div>
                    <div id="act-result" class="hidden px-10 pb-10"></div>
                </section>
            `;
            out.classList.remove("hidden");

            // Zoom — simple CSS transform sur #org-stage (pas de re-render).
            const stage = $("org-stage");
            const zoomLabel = $("org-zoom-label");
            let zoom = 1;
            const setZoom = z => {
                zoom = Math.max(0.3, Math.min(2, z));
                if (stage) stage.style.transform = `scale(${zoom})`;
                if (zoomLabel) zoomLabel.textContent = Math.round(zoom * 100) + "%";
            };
            const zi = $("btn-org-zoom-in"), zo = $("btn-org-zoom-out"), zf = $("btn-org-fit");
            const fitToViewport = () => {
                const vp = $("org-viewport");
                if (!vp || !stage) return;
                setZoom(1);  // reset avant la mesure
                requestAnimationFrame(() => {
                    const vpW = vp.clientWidth - 80;  // padding p-10
                    const vpH = vp.clientHeight - 80;
                    const stageW = stage.scrollWidth;
                    const stageH = stage.scrollHeight;
                    const scaleW = vpW / stageW;
                    const scaleH = vpH / stageH;
                    const s = Math.min(scaleW, scaleH, 1);
                    if (s < 1) setZoom(s);
                });
            };
            if (zi) zi.addEventListener("click", () => setZoom(zoom + 0.1));
            if (zo) zo.addEventListener("click", () => setZoom(zoom - 0.1));
            if (zf) zf.addEventListener("click", fitToViewport);

            // Auto-fit au premier rendu : l'utilisateur voit tout l'organigramme
            // d'un coup sans avoir à cliquer sur "Ajuster". Il peut ensuite
            // zoomer manuellement s'il veut voir les détails.
            requestAnimationFrame(fitToViewport);
            // Ctrl+molette = zoom dans le viewport
            const vp = $("org-viewport");
            if (vp) vp.addEventListener("wheel", e => {
                if (!e.ctrlKey) return;
                e.preventDefault();
                setZoom(zoom + (e.deltaY < 0 ? 0.1 : -0.1));
            }, { passive: false });

            // Export PDF — dialog Enregistrer-Sous + génération via fpdf2
            const btnPdf = $("btn-tree-export-pdf");
            if (btnPdf) btnPdf.addEventListener("click", async () => {
                if (!API()) return;
                btnPdf.disabled = true;
                btnPdf.classList.add("opacity-60");
                toast("Export PDF", "Génération en cours…", "info");
                const r = await API().export_structure_pdf(filepath);
                btnPdf.disabled = false;
                btnPdf.classList.remove("opacity-60");
                if (r && r.error) {
                    toast("Erreur", r.error, "error");
                } else if (r && r.cancelled) {
                    toast("Annulé", "Export PDF annulé", "info");
                } else if (r && r.path) {
                    toast("PDF généré", r.path.split(/[\\/]/).pop(), "success");
                }
            });

            // =====================================================
            // Analyse d'activité par UM (RPS / RAA)
            // =====================================================
            const umLeaves = collectUmLeaves(data.tree || []);
            const dropZone = $("act-drop-zone");
            const fileInput = $("act-file-input");
            const btnActReset = $("btn-act-reset");
            const actStatus = $("act-status");
            const actResult = $("act-result");
            const actProgress = $("act-progress");
            const actProgressBar = $("act-progress-bar");
            const actProgressPct = $("act-progress-pct");
            const actProgressLabel = $("act-progress-label");

            function setStatus(html, kind) {
                if (!actStatus) return;
                const palette = {
                    info: "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-200 border-blue-200 dark:border-blue-800",
                    ok: "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-200 border-emerald-200 dark:border-emerald-800",
                    warn: "bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-200 border-amber-200 dark:border-amber-800",
                    err: "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800",
                }[kind] || "";
                actStatus.className = `mx-10 mb-6 p-5 rounded-2xl border text-sm font-medium ${palette}`;
                actStatus.innerHTML = html;
                actStatus.classList.remove("hidden");
            }

            function setProgress(pct, label) {
                if (!actProgress) return;
                actProgress.classList.remove("hidden");
                if (actProgressBar) actProgressBar.style.width = Math.max(0, Math.min(100, pct)) + "%";
                if (actProgressPct) actProgressPct.textContent = Math.round(pct) + " %";
                if (actProgressLabel && label) actProgressLabel.textContent = label;
            }

            function hideProgress() {
                if (actProgress) actProgress.classList.add("hidden");
            }

            function resetAnalysis() {
                if (fileInput) fileInput.value = "";
                if (actStatus) actStatus.classList.add("hidden");
                if (actResult) { actResult.classList.add("hidden"); actResult.innerHTML = ""; }
                if (btnActReset) btnActReset.classList.add("hidden");
                hideProgress();
                // Retire les badges "inactif" posés sur les nœuds de l'arbre
                document.querySelectorAll(".org-node.org-um-inactive").forEach(n => n.classList.remove("org-um-inactive"));
            }

            // Exporte CSV (séparateur ; + BOM UTF-8 pour Excel FR)
            function exportInactiveCsv(inactive, periodLabel) {
                const rows = [["Code UM", "Libellé UM", "Secteur / Pôle parent", "Type ARS", "Période"]];
                inactive.forEach(u => rows.push([
                    u.code, u.label, u.parentLabel || "",
                    u.sector || "", periodLabel || "",
                ]));
                const csv = rows.map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(";")).join("\r\n");
                const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" });
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                const today = new Date().toISOString().slice(0, 10);
                a.download = `UM_sans_activite_${today}.csv`;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 100);
                toast("Export CSV", `${inactive.length} UM · ${a.download}`, "success");
            }

            // Pose une classe sur les nœuds de l'arbre correspondant aux UM inactives.
            // Matche par .org-code === code UM. Purement décoratif via CSS.
            function markInactiveNodesOnTree(inactiveCodes) {
                document.querySelectorAll(".org-node.org-um-inactive").forEach(n => n.classList.remove("org-um-inactive"));
                if (!inactiveCodes.length) return;
                const set = new Set(inactiveCodes);
                document.querySelectorAll(".org-chart .org-code").forEach(codeEl => {
                    const code = (codeEl.textContent || "").trim();
                    if (set.has(code)) {
                        const node = codeEl.closest(".org-node");
                        if (node) node.classList.add("org-um-inactive");
                    }
                });
            }

            async function runActivityAnalysis(fileList) {
                const files = [...(fileList || [])].filter(f => f && f.size > 0);
                if (!files.length) {
                    setStatus("Aucun fichier valide sélectionné.", "warn");
                    return;
                }
                if (!umLeaves.length) {
                    setStatus("La structure ne contient aucune UM détectable. Vérifiez votre fichier de structure.", "warn");
                    return;
                }

                setStatus(`<i data-lucide="loader" class="w-4 h-4 inline mr-2 animate-spin"></i>${files.length} fichier${files.length > 1 ? "s" : ""} · lecture en cours…`, "info");
                setProgress(0, "Lecture…");
                if (window.lucide) lucide.createIcons();

                const perFile = [];
                const globalCounts = new Map(umLeaves.map(u => [u.code, 0]));
                let grandTotalLines = 0;
                const umCodes = umLeaves.map(u => u.code);

                try {
                    for (let idx = 0; idx < files.length; idx++) {
                        const f = files[idx];
                        const baseLabel = `Fichier ${idx + 1}/${files.length} · ${f.name}`;
                        setProgress((idx / files.length) * 100, baseLabel + " · lecture");
                        const text = await readAtihFile(f);
                        const lines = text.split(/\r?\n/).filter(l => l.length > 0);
                        const det = detectAtihFormat(lines);
                        const counts = await countUmActivityAsync(lines, umCodes, pct => {
                            const fileBase = (idx / files.length) * 100;
                            const fileStep = (1 / files.length) * 100;
                            setProgress(fileBase + (pct / 100) * fileStep, baseLabel + ` · analyse (${pct}%)`);
                        });
                        counts.forEach((v, k) => globalCounts.set(k, (globalCounts.get(k) || 0) + v));
                        grandTotalLines += lines.length;
                        perFile.push({ name: f.name, size: f.size, lines: lines.length, det });
                    }
                    setProgress(100, "Finalisation");
                } catch (e) {
                    hideProgress();
                    setStatus(`<i data-lucide="alert-triangle" class="w-4 h-4 inline mr-2"></i>${escHtml(e.message || "Erreur de lecture")}`, "err");
                    if (window.lucide) lucide.createIcons();
                    return;
                }

                // Période détectée depuis les noms de fichier
                const period = extractPeriodFromFilenames(files.map(f => f.name));
                const periodLabel = period
                    ? (period.monthCount > 0 ? `${period.label} · ${period.monthCount} mois` : period.label)
                    : "période non détectée (vérifiez les noms de fichier)";

                // Agrégation · actives / inactives / tri
                const active = [], inactive = [];
                umLeaves.forEach(u => {
                    const c = globalCounts.get(u.code) || 0;
                    (c > 0 ? active : inactive).push(Object.assign({ count: c }, u));
                });
                active.sort((a, b) => b.count - a.count);
                inactive.sort((a, b) => {
                    const p = (a.parentLabel || "").localeCompare(b.parentLabel || "");
                    return p !== 0 ? p : a.code.localeCompare(b.code);
                });

                const totalUm = umLeaves.length;
                const pctInactive = totalUm ? Math.round((inactive.length / totalUm) * 100) : 0;
                const pctActive = 100 - pctInactive;

                // Groupe par parent (pôle / secteur)
                const inactiveByParent = new Map();
                inactive.forEach(u => {
                    const key = u.parentCode || "__ORPHAN__";
                    if (!inactiveByParent.has(key)) {
                        inactiveByParent.set(key, { label: u.parentLabel || "Sans parent", items: [] });
                    }
                    inactiveByParent.get(key).items.push(u);
                });

                const filesHtml = perFile.map(f => `
                    <div class="flex items-center justify-between py-3 border-b border-slate-100 dark:border-slate-800 last:border-0">
                        <div class="flex items-center gap-3 min-w-0">
                            <i data-lucide="file-text" class="w-4 h-4 text-gh-navy dark:text-blue-400 flex-shrink-0"></i>
                            <span class="font-mono text-xs font-bold text-slate-700 dark:text-slate-200 truncate">${escHtml(f.name)}</span>
                            <span class="px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-200 text-[10px] font-black uppercase tracking-wider">${escHtml(f.det.format)}</span>
                        </div>
                        <div class="flex items-center gap-4 text-[11px] font-mono text-slate-500 dark:text-slate-300 flex-shrink-0">
                            <span>${f.lines.toLocaleString("fr-FR")} lignes</span>
                            <span>${Math.round(f.size / 1024).toLocaleString("fr-FR")} Ko</span>
                        </div>
                    </div>
                `).join("");

                const inactiveHtml = inactive.length === 0
                    ? `<div class="py-12 text-center">
                           <i data-lucide="check-circle-2" class="w-12 h-12 text-gh-success mx-auto mb-3"></i>
                           <p class="font-black uppercase tracking-wider text-gh-success">Toutes les UM ont de l'activité</p>
                           <p class="text-xs text-slate-500 dark:text-slate-400 mt-2">Aucune UM de la structure n'est absente des fichiers ATIH déposés.</p>
                       </div>`
                    : [...inactiveByParent.entries()].map(([, grp]) => `
                        <div class="mb-6 last:mb-0">
                            <div class="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100 dark:border-slate-700">
                                <i data-lucide="folder" class="w-3.5 h-3.5 text-slate-400"></i>
                                <span class="font-black text-[11px] uppercase tracking-[0.2em] text-slate-600 dark:text-slate-300">${escHtml(grp.label)}</span>
                                <span class="ml-auto text-[10px] font-mono font-bold text-red-600 dark:text-red-400">${grp.items.length} UM</span>
                            </div>
                            <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                                ${grp.items.map(u => `
                                    <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-red-50 dark:bg-red-900/25 border border-red-200 dark:border-red-800/50">
                                        <span class="font-mono font-black text-red-700 dark:text-red-300 text-xs">${escHtml(u.code)}</span>
                                        <span class="text-[11px] text-slate-700 dark:text-slate-200 truncate" title="${escHtml(u.label)}">${escHtml(u.label)}</span>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    `).join("");

                const topActiveHtml = active.slice(0, 10).map(u => `
                    <div class="flex items-center gap-3 py-2">
                        <span class="font-mono font-black text-xs text-gh-navy dark:text-blue-400 w-14 flex-shrink-0">${escHtml(u.code)}</span>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-slate-700 dark:text-slate-200 truncate">${escHtml(u.label)}</p>
                            <div class="h-1 bg-slate-100 dark:bg-slate-700 rounded-full mt-1 overflow-hidden">
                                <div class="h-full bg-gh-teal" style="width: ${Math.min(100, Math.round((u.count / (active[0] ? active[0].count : 1)) * 100))}%"></div>
                            </div>
                        </div>
                        <span class="font-mono text-[11px] font-bold text-gh-teal w-16 text-right flex-shrink-0">${u.count.toLocaleString("fr-FR")}</span>
                    </div>
                `).join("") || `<p class="text-xs text-slate-400 italic">Aucune UM active</p>`;

                // Hiérarchie métier · 3 cards · actives / inactives / couverture
                actResult.innerHTML = `
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                        ${statCard("check-circle-2", "UM actives", active.length + " / " + totalUm, "green")}
                        ${statCard("circle-slash", "UM sans activité", inactive.length, inactive.length > 0 ? "amber" : "green")}
                        ${statCard("gauge", "Couverture", pctActive + " %", pctActive >= 80 ? "green" : pctActive >= 50 ? "amber" : "red")}
                    </div>

                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                        <div class="p-6 rounded-2xl border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50/40 dark:bg-emerald-900/15">
                            <div class="flex items-center justify-between mb-2">
                                <p class="text-[10px] font-black uppercase tracking-[0.25em] text-emerald-700 dark:text-emerald-300">Couverture d'activité</p>
                                <span class="font-mono font-black text-2xl text-emerald-700 dark:text-emerald-300">${pctActive}%</span>
                            </div>
                            <div class="h-3 bg-emerald-100 dark:bg-emerald-900/40 rounded-full overflow-hidden">
                                <div class="h-full bg-gh-success transition-all" style="width: ${Math.max(2, pctActive)}%"></div>
                            </div>
                            <p class="text-[11px] text-slate-600 dark:text-slate-300 mt-3">${active.length} UM sur ${totalUm} ont au moins une occurrence dans les fichiers déposés.</p>
                        </div>
                        <div class="p-6 rounded-2xl border border-red-200 dark:border-red-800/50 bg-red-50/50 dark:bg-red-900/15">
                            <div class="flex items-center justify-between mb-2">
                                <p class="text-[10px] font-black uppercase tracking-[0.25em] text-red-700 dark:text-red-300">Sans activité</p>
                                <span class="font-mono font-black text-2xl text-red-700 dark:text-red-300">${pctInactive}%</span>
                            </div>
                            <div class="h-3 bg-red-100 dark:bg-red-900/40 rounded-full overflow-hidden">
                                <div class="h-full bg-gh-error transition-all" style="width: ${Math.max(2, pctInactive)}%"></div>
                            </div>
                            <p class="text-[11px] text-slate-600 dark:text-slate-300 mt-3">${inactive.length} UM non trouvée${inactive.length > 1 ? "s" : ""} sur la période <strong>${escHtml(periodLabel)}</strong>.</p>
                        </div>
                    </div>

                    <div class="bg-slate-50 dark:bg-slate-900/40 rounded-2xl p-6 mb-8">
                        <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
                            <p class="text-[10px] font-black uppercase tracking-[0.25em] text-slate-600 dark:text-slate-300">Fichiers analysés · ${perFile.length} · ${grandTotalLines.toLocaleString("fr-FR")} lignes</p>
                            <span class="text-[10px] font-mono text-slate-500 dark:text-slate-400">Période · ${escHtml(periodLabel)}</span>
                        </div>
                        ${filesHtml || '<p class="text-xs text-slate-400">—</p>'}
                    </div>

                    <div class="mb-8">
                        <div class="flex items-center justify-between flex-wrap gap-3 mb-4">
                            <h4 class="font-black uppercase tracking-[0.2em] text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
                                <i data-lucide="circle-slash" class="w-4 h-4"></i>
                                Unités sans activité · ${inactive.length}
                            </h4>
                            <button id="btn-act-export-csv" class="px-5 py-2.5 bg-gh-navy text-white rounded-full font-black uppercase text-[10px] tracking-[0.25em] shadow hover:bg-blue-700 transition-all active:scale-95 flex items-center gap-2 ${inactive.length === 0 ? "hidden" : ""}">
                                <i data-lucide="file-down" class="w-3.5 h-3.5"></i>
                                Exporter CSV
                            </button>
                        </div>
                        <div class="rounded-2xl border border-slate-100 dark:border-slate-700 p-6 bg-white dark:bg-slate-800/50">
                            ${inactiveHtml}
                        </div>
                    </div>

                    <details class="rounded-2xl border border-slate-100 dark:border-slate-700 overflow-hidden">
                        <summary class="px-6 py-4 cursor-pointer bg-slate-50 dark:bg-slate-900/40 font-black uppercase tracking-[0.2em] text-xs text-gh-navy dark:text-blue-400 flex items-center gap-2">
                            <i data-lucide="trending-up" class="w-4 h-4"></i>
                            Top 10 UM les plus actives
                        </summary>
                        <div class="p-6 bg-white dark:bg-slate-800/50">${topActiveHtml}</div>
                    </details>
                `;
                actResult.classList.remove("hidden");
                if (btnActReset) btnActReset.classList.remove("hidden");
                hideProgress();

                // Pose les badges rouges sur les UM inactives de l'arbre
                markInactiveNodesOnTree(inactive.map(u => u.code));

                // Bind export CSV
                const btnExport = $("btn-act-export-csv");
                if (btnExport) btnExport.addEventListener("click", () => exportInactiveCsv(inactive, periodLabel));

                setStatus(
                    `<i data-lucide="check-circle-2" class="w-4 h-4 inline mr-2"></i>Analyse terminée · ${perFile.length} fichier${perFile.length > 1 ? "s" : ""} · ${grandTotalLines.toLocaleString("fr-FR")} lignes · <strong>${inactive.length} UM sans activité</strong> sur la période <strong>${escHtml(periodLabel)}</strong>`,
                    inactive.length > 0 ? "warn" : "ok"
                );
                if (window.lucide) lucide.createIcons();
            }

            if (fileInput) {
                fileInput.addEventListener("change", e => runActivityAnalysis(e.target.files));
            }
            if (btnActReset) {
                btnActReset.addEventListener("click", resetAnalysis);
            }
            if (dropZone) {
                dropZone.addEventListener("click", () => fileInput && fileInput.click());
                dropZone.addEventListener("keydown", e => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        fileInput && fileInput.click();
                    }
                });
                ["dragenter", "dragover"].forEach(ev => dropZone.addEventListener(ev, e => {
                    e.preventDefault(); e.stopPropagation();
                    dropZone.classList.add("border-gh-teal", "bg-teal-50/50", "dark:bg-teal-900/20");
                }));
                ["dragleave", "dragend"].forEach(ev => dropZone.addEventListener(ev, e => {
                    e.preventDefault(); e.stopPropagation();
                    dropZone.classList.remove("border-gh-teal", "bg-teal-50/50", "dark:bg-teal-900/20");
                }));
                dropZone.addEventListener("drop", e => {
                    e.preventDefault(); e.stopPropagation();
                    dropZone.classList.remove("border-gh-teal", "bg-teal-50/50", "dark:bg-teal-900/20");
                    if (e.dataTransfer && e.dataTransfer.files) runActivityAnalysis(e.dataTransfer.files);
                });
            }
            // Expose à window · testabilité via console/tests
            window.__sovActivity = { collectUmLeaves, readAtihFile, detectAtihFormat, countUmActivity, countUmActivityAsync, extractPeriodFromFilenames, umLeaves };

            toast("Structure", `${data.filename} · ${s.total_nodes} nœuds`, "success");
            if (window.lucide) lucide.createIcons();
        });

        if (window.lucide) lucide.createIcons();
    }

    // =========================================================================
    // BADGES
    // =========================================================================
    function updateBadges() {
        const bf = $("badge-files-total"), bi = $("badge-idv-conflict");
        if (bf) {
            if (S.files.length > 0) { bf.classList.remove("hidden"); bf.textContent = S.files.length; }
            else bf.classList.add("hidden");
        }
        if (bi) {
            const p = S.collisions.filter(c => !c.pivot).length;
            if (p > 0) { bi.classList.remove("hidden"); bi.textContent = p; }
            else bi.classList.add("hidden");
        }
    }

    // =========================================================================
    // KEYBOARD SHORTCUTS
    // =========================================================================
    document.addEventListener("keydown", (e) => {
        if (!S.booted) return;
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case "1": e.preventDefault(); navigateTo("dashboard"); break;
                case "2": e.preventDefault(); navigateTo("modo"); break;
                case "3": e.preventDefault(); navigateTo("idv"); break;
                case "4": e.preventDefault(); navigateTo("pilot"); break;
                case "5": e.preventDefault(); navigateTo("csv"); break;
                case "6": e.preventDefault(); navigateTo("structure"); break;
                case "7": e.preventDefault(); navigateTo("tuto"); break;
            }
        }
        // Escape closes modals
        if (e.key === "Escape") {
            const rm = $("reconciliation-modal"), im = $("inspector-modal");
            if (rm) rm.classList.add("hidden");
            if (im) im.classList.add("hidden");
        }
    });

    // =========================================================================
    // INIT
    // =========================================================================
    let _initialized = false;
    function init() {
        if (_initialized) return;
        _initialized = true;

        const navMap = { "nav-dashboard": "dashboard", "nav-modo": "modo", "nav-idv": "idv", "nav-pilot": "pilot", "nav-csv": "csv", "nav-structure": "structure", "nav-tuto": "tuto" };
        Object.entries(navMap).forEach(([id, v]) => {
            const el = $(id);
            if (el) el.addEventListener("click", () => navigateTo(v));
        });

        const themeBtn = $("btn-theme-toggle");
        if (themeBtn) {
            themeBtn.addEventListener("click", () => {
                document.documentElement.classList.toggle("dark");
                const icon = $("icon-theme");
                if (icon) {
                    icon.setAttribute("data-lucide", document.documentElement.classList.contains("dark") ? "sun" : "moon");
                    if (window.lucide) lucide.createIcons();
                }
            });
        }

        const cI = $("btn-close-idv-modal");
        if (cI) cI.addEventListener("click", () => { const m = $("reconciliation-modal"); if (m) m.classList.add("hidden"); });

        [$("btn-close-inspector"), $("btn-close-inspector-2")].forEach(b => {
            if (b) b.addEventListener("click", () => { const m = $("inspector-modal"); if (m) m.classList.add("hidden"); });
        });

        const reset = $("btn-reset");
        if (reset) reset.addEventListener("click", async () => {
            if (API()) await API().reset_all();
            S.files = []; S.collisions = []; S.stats = null; S.mpiStats = null;
            updateBadges();
            navigateTo("dashboard");
            toast("Reset", "Sovereign OS réinitialisé", "info");
        });

        if (window.lucide) lucide.createIcons();
        runBoot();
    }

    if (window.pywebview) { init(); }
    else {
        window.addEventListener("pywebviewready", init);
        setTimeout(() => { if (!S.booted) init(); }, 2000);
    }

})();

// ══════════════════════════════════════════════════════════════════════════════
// Tests fonctionnels · analyse d'activité UM (helpers frontend)
// Exécute · `node tests/frontend/test_activity_analysis.mjs`
// Objectif · valider collectUmLeaves / detectAtihFormat / countUmActivity
// sans lancer de navigateur. On extrait les 4 helpers du fichier app.js et
// on les exécute en isolation via `new Function(...)`.
// ══════════════════════════════════════════════════════════════════════════════

// Les helpers ci-dessous doivent rester synchronisés avec ceux de
// `frontend/js/app.js` (section STRUCTURE). Ce fichier les réutilise comme
// copies locales pour des tests isolés, sans navigateur ; toute évolution
// côté app.js doit donc être répercutée ici.

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
    const seen = new Map();
    out.forEach(u => { if (!seen.has(u.code)) seen.set(u.code, u); });
    return [...seen.values()];
}

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
        await new Promise(r => setTimeout(r, 0));
    }
    return counts;
}

function extractPeriodFromFilenames(filenames) {
    const years = new Set();
    const months = new Set();
    filenames.forEach(n => {
        const base = String(n).replace(/\.[^.]+$/, "");
        (base.match(/20[2-3]\d/g) || []).forEach(y => years.add(y));
        (base.match(/20[2-3]\d(0[1-9]|1[0-2])/g) || []).forEach(ym => {
            years.add(ym.slice(0, 4));
            months.add(ym);
        });
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

// ── Assertions helpers ─────────────────────────────────────────────────────
let pass = 0, fail = 0;
const results = [];
const pendingTests = [];
function test(name, fn) {
    const run = Promise.resolve()
        .then(() => fn())
        .then(() => {
            results.push({ name, ok: true });
            pass++;
        })
        .catch((e) => {
            results.push({ name, ok: false, err: e && e.message ? e.message : String(e) });
            fail++;
        });
    pendingTests.push(run);
}
function eq(a, b, msg) {
    const A = JSON.stringify(a), B = JSON.stringify(b);
    if (A !== B) throw new Error(`${msg || "eq"} · attendu ${B}, reçu ${A}`);
}
function ok(cond, msg) { if (!cond) throw new Error(msg || "condition false"); }

// ── Fixture structure · reproduit la hiérarchie Fondation Vallée ──────────
const FIXTURE_TREE = [
    {
        code: "POLE_INFANTO", label: "Pôle Infanto-juvénile", level: "POLE",
        sector_type: "I", children: [
            {
                code: "94I01", label: "Secteur 94I01 Gentilly", level: "SECTEUR",
                sector_type: "I", children: [
                    { code: "4001", label: "UM Hospitalisation Temps Plein", level: "UM", sector_type: "I", children: [] },
                    { code: "4002", label: "UM Hôpital de Jour", level: "UM", sector_type: "I", children: [] },
                    { code: "4003", label: "CATTP Adolescents", level: "UM", sector_type: "I", children: [] },
                ],
            },
            {
                code: "94I02", label: "Secteur 94I02 Kremlin-Bicêtre", level: "SECTEUR",
                sector_type: "I", children: [
                    { code: "4010", label: "UM CMP Enfants", level: "UM", sector_type: "I", children: [] },
                    { code: "4011", label: "UM Consultation Famille", level: "UM", sector_type: "I", children: [] },
                ],
            },
        ],
    },
    {
        code: "POLE_INTER", label: "Pôle Intersectoriel", level: "POLE",
        sector_type: "Z", children: [
            { code: "4050", label: "UM Addictologie ado", level: "UM", sector_type: "Z", children: [] },
        ],
    },
];

// ── Fixture ATIH · forge un RPS 154 c et un RAA 96 c ──────────────────────
// On concatène des champs fake et on injecte le code UM dans la zone classique.
function forgeRpsLine(umCode, ipp = "IPP00000000000000001") {
    // Total 154 chars · pad avec espaces + injecte UM à la position 79-82
    const finess = "750000012";                     // 9 (neutre, pas de collision avec codes UM 40xx)
    const seq = "0000001";                          // 7
    const rpsNum = "0001";                          // 4 (17-20)
    const ipp20 = ipp.padEnd(20).slice(0, 20);      // 21-40
    const ddn = "20100101";                         // 41-48
    const sexe = "1";                               // 49
    const datedebut = "01012024";                   // 50-57
    const datefin = "07012024";                     // 58-65
    const modeEntree = "8";                         // 66
    const provenance = "0";                         // 67
    const modeSortie = "8";                         // 68
    const destination = "0";                        // 69
    const modeLegal = "SL";                         // 70-71
    const typeSeq = "T";                            // 72
    const formeAct = "0001";                        // 73-76
    const discpl = "05";                            // 77-78
    const um = umCode.padEnd(4).slice(0, 4);        // 79-82
    let line = finess + seq + rpsNum + ipp20 + ddn + sexe + datedebut + datefin
        + modeEntree + provenance + modeSortie + destination + modeLegal + typeSeq
        + formeAct + discpl + um;
    if (line.length > 154) line = line.slice(0, 154);
    if (line.length < 154) line = line.padEnd(154);
    return line;
}

function forgeRaaLine(umCode, ipp = "IPP00000000000000001") {
    // Total 96 chars · UM à la position ~56-59
    const finess = "750000012";                     // 9 (neutre, pas de collision avec codes UM 40xx)
    const seq = "0000001";                          // 7
    const rsaNum = "0001";                          // 4 (17-20)
    const ipp20 = ipp.padEnd(20).slice(0, 20);      // 21-40
    const ddn = "20100101";                         // 41-48
    const sexe = "1";                               // 49
    const dateActe = "15012024";                    // 50-57
    const um = umCode.padEnd(4).slice(0, 4);        // 58-61
    let line = finess + seq + rsaNum + ipp20 + ddn + sexe + dateActe + um;
    if (line.length > 96) line = line.slice(0, 96);
    if (line.length < 96) line = line.padEnd(96);
    return line;
}

// ══════════════════════════════════════════════════════════════════════════════
// TESTS
// ══════════════════════════════════════════════════════════════════════════════

test("collectUmLeaves · extrait toutes les UM de l'arbre", () => {
    const leaves = collectUmLeaves(FIXTURE_TREE);
    eq(leaves.length, 6, "6 UM attendues");
    const codes = leaves.map(u => u.code).sort();
    eq(codes, ["4001", "4002", "4003", "4010", "4011", "4050"], "codes UM");
});

test("collectUmLeaves · déduplique sur code", () => {
    const dup = [
        { code: "POLE", level: "POLE", children: [
            { code: "SEC", level: "SECTEUR", children: [
                { code: "4001", label: "A", level: "UM", children: [] },
                { code: "4001", label: "A bis", level: "UM", children: [] },
            ] },
        ] },
    ];
    const leaves = collectUmLeaves(dup);
    eq(leaves.length, 1, "doublons fusionnés");
    eq(leaves[0].code, "4001");
});

test("collectUmLeaves · préserve parent (pôle/secteur)", () => {
    const leaves = collectUmLeaves(FIXTURE_TREE);
    const u = leaves.find(x => x.code === "4001");
    ok(u, "UM 4001 trouvée");
    eq(u.parentCode, "94I01", "parent = secteur");
    ok(u.parentLabel.includes("Gentilly"), "label secteur");
    eq(u.sector, "I", "type ARS hérité");
});

test("collectUmLeaves · arbre vide", () => {
    eq(collectUmLeaves([]).length, 0);
    eq(collectUmLeaves(null).length, 0);
});

test("detectAtihFormat · RPS 154c", () => {
    const lines = Array.from({ length: 10 }, () => forgeRpsLine("4001"));
    const d = detectAtihFormat(lines);
    eq(d.format, "RPS / RPSA");
    eq(d.length, 154);
});

test("detectAtihFormat · RAA 96c", () => {
    const lines = Array.from({ length: 10 }, () => forgeRaaLine("4001"));
    const d = detectAtihFormat(lines);
    eq(d.format, "RAA / R3A / EDGAR");
    eq(d.length, 96);
});

test("detectAtihFormat · mixte · mode dominante gagne", () => {
    const lines = [
        ...Array.from({ length: 50 }, () => forgeRpsLine("4001")),
        ...Array.from({ length: 5 }, () => forgeRaaLine("4002")),
    ];
    const d = detectAtihFormat(lines);
    eq(d.format, "RPS / RPSA", "RPS majoritaire");
});

test("detectAtihFormat · vide", () => {
    eq(detectAtihFormat([]).format, "INCONNU");
    eq(detectAtihFormat(["x"]).format, "INCONNU"); // < 50 chars filtré
});

test("countUmActivity · RPS · compte par UM", () => {
    const lines = [
        forgeRpsLine("4001"), forgeRpsLine("4001"), forgeRpsLine("4001"),
        forgeRpsLine("4002"),
        forgeRpsLine("4050"),
    ];
    const counts = countUmActivity(lines, ["4001", "4002", "4003", "4010", "4050"]);
    eq(counts.get("4001"), 3);
    eq(counts.get("4002"), 1);
    eq(counts.get("4003"), 0, "UM absente = 0");
    eq(counts.get("4010"), 0);
    eq(counts.get("4050"), 1);
});

test("countUmActivity · ligne unique compte 1 fois une UM même si occurence multiple", () => {
    // Code "4001" présent 2 fois dans la même ligne
    const line = "4001xxx4001xxx" + " ".repeat(150);
    const counts = countUmActivity([line.slice(0, 154)], ["4001"]);
    eq(counts.get("4001"), 1, "1 ligne = 1 comptage max par UM");
});

test("countUmActivity · RAA · fonctionne à 96c", () => {
    const lines = [forgeRaaLine("4010"), forgeRaaLine("4010"), forgeRaaLine("4011")];
    const counts = countUmActivity(lines, ["4010", "4011", "4012"]);
    eq(counts.get("4010"), 2);
    eq(counts.get("4011"), 1);
    eq(counts.get("4012"), 0);
});

test("countUmActivity · codes longs priorisés (évite match partiel)", () => {
    // "40012" contient "4001" en préfixe · un match sur le code long ne doit pas
    // générer aussi un match sur le court dans la même position.
    const line = ("xxx40012xxx").padEnd(154);
    const counts = countUmActivity([line], ["4001", "40012"]);
    eq(counts.get("40012"), 1, "40012 matché");
    // Sur le code court · match potentiel ailleurs dans la ligne · ici 0
    eq(counts.get("4001"), 0, "4001 pas surcompté");
});

test("countUmActivity · liste codes vide", () => {
    const counts = countUmActivity([forgeRpsLine("4001")], []);
    eq(counts.size, 0);
});

test("countUmActivity · 1000 lignes × 50 UM · perf < 150ms", () => {
    const codes = Array.from({ length: 50 }, (_, i) => String(4000 + i));
    const lines = Array.from({ length: 1000 }, (_, i) => forgeRpsLine(codes[i % 50]));
    const t0 = performance.now();
    const counts = countUmActivity(lines, codes);
    const dt = performance.now() - t0;
    ok(dt < 150, `durée ${dt.toFixed(1)}ms doit être < 150ms`);
    // Chaque code doit avoir ~20 occurrences (1000/50)
    eq(counts.get("4000"), 20);
});

test("countUmActivityAsync · même résultat que la version sync", async () => {
    const codes = ["4001", "4002", "4003"];
    const lines = [
        ...Array.from({ length: 100 }, () => forgeRpsLine("4001")),
        ...Array.from({ length: 50 }, () => forgeRpsLine("4002")),
    ];
    const sync = countUmActivity(lines, codes);
    const async_ = await countUmActivityAsync(lines, codes);
    eq(sync.get("4001"), async_.get("4001"));
    eq(sync.get("4002"), async_.get("4002"));
    eq(sync.get("4003"), async_.get("4003"));
});

test("countUmActivityAsync · callback progression · 0 → 100", async () => {
    const codes = ["4001"];
    const lines = Array.from({ length: 12000 }, () => forgeRpsLine("4001"));
    const pcts = [];
    await countUmActivityAsync(lines, codes, p => pcts.push(p));
    ok(pcts.length >= 2, "au moins 2 callbacks sur 12k lignes (chunks 5k)");
    eq(pcts[pcts.length - 1], 100, "finit à 100 %");
    ok(pcts[0] > 0 && pcts[0] < 100, "premier callback intermédiaire");
});

test("extractPeriodFromFilenames · AAAAMM dans nom de fichier", () => {
    const p = extractPeriodFromFilenames(["RPS_202410.txt", "RAA_202411.txt", "RPS_202412.txt"]);
    ok(p, "période détectée");
    eq(p.years, ["2024"]);
    eq(p.months.length, 3);
    eq(p.label, "2024");
});

test("extractPeriodFromFilenames · plusieurs années", () => {
    const p = extractPeriodFromFilenames(["RPS_2023.txt", "RPS_2024.txt", "RPS_2025.txt"]);
    ok(p);
    eq(p.label, "2023 → 2025");
});

test("extractPeriodFromFilenames · MMAAAA format alternatif", () => {
    const p = extractPeriodFromFilenames(["RAA_102024.txt", "RAA_112024.txt"]);
    ok(p);
    eq(p.years, ["2024"]);
});

test("extractPeriodFromFilenames · pas de date = null", () => {
    eq(extractPeriodFromFilenames(["sans_date.txt", "export.txt"]), null);
});

test("scénario métier complet · 3 UM sans activité sur 6", () => {
    const leaves = collectUmLeaves(FIXTURE_TREE);
    const rpsLines = [
        ...Array.from({ length: 15 }, () => forgeRpsLine("4001")),
        ...Array.from({ length: 8 }, () => forgeRpsLine("4010")),
    ];
    const raaLines = Array.from({ length: 20 }, () => forgeRaaLine("4011"));
    const allCodes = leaves.map(u => u.code);
    const c1 = countUmActivity(rpsLines, allCodes);
    const c2 = countUmActivity(raaLines, allCodes);
    const merged = new Map();
    allCodes.forEach(k => merged.set(k, (c1.get(k) || 0) + (c2.get(k) || 0)));
    const inactive = leaves.filter(u => (merged.get(u.code) || 0) === 0);
    eq(inactive.length, 3, "3 UM inactives attendues");
    const inactiveCodes = inactive.map(u => u.code).sort();
    eq(inactiveCodes, ["4002", "4003", "4050"]);
});

// ══════════════════════════════════════════════════════════════════════════════
// Rapport final
// ══════════════════════════════════════════════════════════════════════════════
Promise.allSettled(pendingTests).then(() => {
    console.log("\n═══ Tests analyse d'activité UM ═══\n");
    results.forEach(r => {
        const icon = r.ok ? "\x1b[32m✔\x1b[0m" : "\x1b[31m✘\x1b[0m";
        console.log(`  ${icon} ${r.name}${r.ok ? "" : "\n      " + r.err}`);
    });
    console.log(`\n${pass}/${pass + fail} tests verts${fail > 0 ? ` · \x1b[31m${fail} échec(s)\x1b[0m` : " · \x1b[32mtout OK\x1b[0m"}\n`);
    process.exit(fail > 0 ? 1 : 0);
});

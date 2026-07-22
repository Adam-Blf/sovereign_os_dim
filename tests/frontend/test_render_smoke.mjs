// ══════════════════════════════════════════════════════════════════════════════
// Smoke test de rendu - frontend/index.html
// Exécute - `node tests/frontend/test_render_smoke.mjs`
// Objectif - attraper la classe de bug qu'aucun test existant ne couvre :
// page qui ne rend pas, police auto-hébergée qui ne résout pas, erreur
// console au chargement. Playwright headless, aucun réseau réel (mock
// window.pywebview.api inline + interception /api/**), pas de dépendance à
// bridge-shim.js (supprimé du frontend).
// ══════════════════════════════════════════════════════════════════════════════

import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const INDEX_HTML = path.join(ROOT, "frontend", "index.html");

let pass = 0, fail = 0;
const results = [];
function record(name, ok, err) {
    results.push({ name, ok, err });
    if (ok) pass++; else fail++;
}

async function main() {
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    const consoleErrors = [];
    page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(String(err)));

    // Mock minimal du pont - juste ce qu'il faut pour que le dashboard boot
    // sans erreur. Pas de dependance a bridge-shim.js (supprime).
    await context.route("**/api/**", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: "{}" }));
    await context.route("**/health", (route) =>
        route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok" }) }));

    await page.addInitScript(() => {
        window.pywebview = { api: new Proxy({}, { get: () => () => Promise.resolve({}) }) };
    });

    await page.goto("file://" + INDEX_HTML.replace(/\\/g, "/"));
    await page.waitForTimeout(2000);
    // Skip le boot screen si present (meme pattern que tools/capture_screenshots.py)
    await page.evaluate(() => {
        const btn = document.getElementById("btn-ignite");
        if (btn && btn.offsetParent !== null) btn.click();
        const overlay = document.getElementById("boot-overlay");
        if (overlay) overlay.style.display = "none";
        const root = document.getElementById("app-root");
        if (root) { root.classList.remove("hidden"); root.style.opacity = "1"; }
    });
    await page.waitForTimeout(500);

    try {
        const title = await page.title();
        record("page charge sans exception", true);
        void title;
    } catch (e) {
        record("page charge sans exception", false, String(e));
    }

    try {
        if (consoleErrors.length > 0) {
            throw new Error(`${consoleErrors.length} erreur(s) console : ${consoleErrors.slice(0, 3).join(" | ")}`);
        }
        record("zero erreur console au chargement", true);
    } catch (e) {
        record("zero erreur console au chargement", false, e.message);
    }

    try {
        const montserratLoaded = await page.evaluate(() => document.fonts.check("1em Montserrat"));
        if (!montserratLoaded) throw new Error("document.fonts.check('1em Montserrat') = false - police auto-hebergee non resolue");
        record("police Montserrat auto-hebergee resout", true);
    } catch (e) {
        record("police Montserrat auto-hebergee resout", false, e.message);
    }

    try {
        const rootHTML = await page.evaluate(() => {
            const root = document.getElementById("app-root");
            return root ? root.innerHTML.trim().length : 0;
        });
        if (!rootHTML || rootHTML < 50) throw new Error(`app-root quasi vide (${rootHTML} caracteres) - ecran non rendu`);
        record("ecran par defaut rend du contenu non vide", true);
    } catch (e) {
        record("ecran par defaut rend du contenu non vide", false, e.message);
    }

    await browser.close();

    console.log("\n═══ Smoke test rendu frontend ═══\n");
    results.forEach((r) => {
        const icon = r.ok ? "\x1b[32m✔\x1b[0m" : "\x1b[31m✘\x1b[0m";
        console.log(`  ${icon} ${r.name}${r.ok ? "" : "\n      " + r.err}`);
    });
    console.log(`\n${pass}/${pass + fail} tests verts${fail > 0 ? ` - \x1b[31m${fail} echec(s)\x1b[0m` : " - \x1b[32mtout OK\x1b[0m"}\n`);
    process.exit(fail > 0 ? 1 : 0);
}

main().catch((e) => {
    console.error("Erreur fatale du smoke test :", e);
    process.exit(1);
});

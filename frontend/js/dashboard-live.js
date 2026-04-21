/*
 * dashboard-live.js · overlay "Live Stats" avec 4 graphiques Chart.js
 * alimentés par /api/dashboard (derrière le bouton 📊 · F4).
 *
 * Pourquoi overlay et non extension du Dashboard existant ·
 *   app.js est fermé en IIFE, toute extension du rendu Dashboard
 *   demande un fork. L'overlay permet d'ajouter la valeur sans risque.
 */
(function () {
  if (window.__dashboardLiveLoaded) return;
  window.__dashboardLiveLoaded = true;

  const PALETTE = {
    navy: '#000091',
    teal: '#00897B',
    error: '#E11D48',
    success: '#10B981',
    warning: '#F59E0B',
    violet: '#7C3AED',
    pink: '#EC4899',
    orange: '#F97316',
    blue: '#2563EB',
  };
  const SECTOR_COLOURS = {
    PSY: PALETTE.pink,
    MCO: PALETTE.blue,
    SSR: PALETTE.teal,
    HAD: PALETTE.warning,
    TRANSVERSAL: PALETTE.navy,
  };

  let charts = [];

  function injectButton() {
    if (document.getElementById('dashboard-live-button')) return;
    const btn = document.createElement('button');
    btn.id = 'dashboard-live-button';
    btn.title = 'Dashboard live (F4)';
    btn.innerHTML = '<span style="font-size:20px;">📊</span>';
    btn.style.cssText = `
      position:fixed; z-index:9994; right:24px; bottom:222px; width:52px; height:52px;
      border-radius:50%; border:0; cursor:pointer;
      background:linear-gradient(135deg,#F59E0B 0%,#F97316 100%); color:white;
      box-shadow:0 8px 20px rgba(245,158,11,0.35); transition:transform .2s;
    `;
    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.1)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1.0)');
    btn.addEventListener('click', openPanel);
    document.body.appendChild(btn);
  }

  async function openPanel() {
    closePanel();
    const wrap = document.createElement('div');
    wrap.id = 'dashboard-live-overlay';
    wrap.innerHTML = `
      <div style="position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:9998;"
           id="dashlive-backdrop"></div>
      <div style="position:fixed; z-index:9999; top:5vh; left:5vw; width:90vw; height:90vh;
                  background:#F8FAFC; color:#0F172A; border-radius:24px;
                  box-shadow:0 20px 60px rgba(0,0,0,.4); display:flex; flex-direction:column;
                  overflow:hidden; font-family:'Plus Jakarta Sans',sans-serif;">
        <header style="padding:1.5rem 2rem;
                       background:linear-gradient(135deg,#F59E0B 0%,#F97316 100%); color:#fff;
                       display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:10px;
                        letter-spacing:0.4em; text-transform:uppercase; opacity:0.8;">Live Stats</div>
            <h2 style="font-size:1.75rem; font-weight:900; font-style:italic; letter-spacing:-0.02em;
                       text-transform:uppercase; margin:0.25rem 0 0;">Dashboard · Analytics</h2>
          </div>
          <div style="display:flex; gap:0.75rem;">
            <button id="dashlive-refresh" style="border:0; background:rgba(255,255,255,0.25); color:#fff;
                   padding:0.5rem 1.2rem; border-radius:999px; cursor:pointer;
                   font-family:'JetBrains Mono',monospace; letter-spacing:0.1em;">RAFRAÎCHIR</button>
            <button id="dashlive-close" style="border:0; background:rgba(255,255,255,0.2); color:#fff;
                   padding:0.5rem 1.2rem; border-radius:999px; cursor:pointer;
                   font-family:'JetBrains Mono',monospace; letter-spacing:0.1em;">FERMER</button>
          </div>
        </header>
        <div id="dashlive-kpis" style="padding:1rem 2rem; background:#ffffff;
                                       border-bottom:1px solid #E2E8F0; display:grid;
                                       grid-template-columns:repeat(4,1fr); gap:1rem;"></div>
        <div style="flex:1; padding:1.5rem 2rem; overflow:auto;
                    display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;">
          <div class="dashlive-card">
            <h3 style="margin:0 0 1rem; font-size:13px; text-transform:uppercase; letter-spacing:0.1em; color:#475569;">
              Répartition par champ PMSI</h3>
            <canvas id="dashlive-chart-field" height="180"></canvas>
          </div>
          <div class="dashlive-card">
            <h3 style="margin:0 0 1rem; font-size:13px; text-transform:uppercase; letter-spacing:0.1em; color:#475569;">
              Distribution DDN par décennie</h3>
            <canvas id="dashlive-chart-ddn" height="180"></canvas>
          </div>
          <div class="dashlive-card">
            <h3 style="margin:0 0 1rem; font-size:13px; text-transform:uppercase; letter-spacing:0.1em; color:#475569;">
              Tailles des fichiers ATIH</h3>
            <canvas id="dashlive-chart-sizes" height="180"></canvas>
          </div>
          <div class="dashlive-card">
            <h3 style="margin:0 0 1rem; font-size:13px; text-transform:uppercase; letter-spacing:0.1em; color:#475569;">
              Top 10 IPP · nombre d'observations</h3>
            <div id="dashlive-top-ipp" style="font-family:'JetBrains Mono',monospace; font-size:12px;"></div>
          </div>
        </div>
      </div>
      <style>
        .dashlive-card {
          background:#ffffff; border:1px solid #E2E8F0; border-radius:16px;
          padding:1.25rem; display:flex; flex-direction:column;
        }
      </style>
    `;
    document.body.appendChild(wrap);
    document.getElementById('dashlive-backdrop').addEventListener('click', closePanel);
    document.getElementById('dashlive-close').addEventListener('click', closePanel);
    document.getElementById('dashlive-refresh').addEventListener('click', refresh);
    await refresh();
  }

  function closePanel() {
    charts.forEach(c => { try { c.destroy(); } catch { /* ignore */ } });
    charts = [];
    document.getElementById('dashboard-live-overlay')?.remove();
  }

  async function refresh() {
    if (!window.pywebview?.api?.dashboard_live) {
      alert('API dashboard_live non disponible · bridge pas démarré ?');
      return;
    }
    let data;
    try {
      data = await window.pywebview.api.dashboard_live();
    } catch (e) {
      alert('Erreur · ' + e.message);
      return;
    }

    // KPIs
    const kpis = document.getElementById('dashlive-kpis');
    const kpiCard = (label, value, color) => `
      <div style="padding:0.9rem 1rem; border-radius:12px;
                  background:linear-gradient(135deg, ${color}15, ${color}05);
                  border-left:4px solid ${color};">
        <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.15em; color:#64748B;">
          ${label}</div>
        <div style="font-size:1.8rem; font-weight:900; color:#0F172A; margin-top:0.25rem;">${value}</div>
      </div>`;
    kpis.innerHTML =
      kpiCard('Fichiers traités', data.totalFiles || 0, PALETTE.navy) +
      kpiCard('IPP uniques', (data.totalIpp || 0).toLocaleString('fr-FR'), PALETTE.teal) +
      kpiCard('Collisions', data.totalCollisions || 0, PALETTE.error) +
      kpiCard('Taux collision', (data.collisionRate || 0) + ' %', PALETTE.warning);

    charts.forEach(c => { try { c.destroy(); } catch { /* ignore */ } });
    charts = [];

    if (typeof Chart === 'undefined') {
      console.warn('[dashboard-live] Chart.js pas chargé · graphes skip.');
      return;
    }

    // Chart 1 · champ PMSI (doughnut)
    const byField = data.byField || {};
    const fieldLabels = Object.keys(byField);
    const fieldColours = fieldLabels.map(f => SECTOR_COLOURS[f] || PALETTE.navy);
    charts.push(new Chart(document.getElementById('dashlive-chart-field'), {
      type: 'doughnut',
      data: {
        labels: fieldLabels,
        datasets: [{ data: Object.values(byField), backgroundColor: fieldColours, borderWidth: 0 }],
      },
      options: { responsive: true, plugins: { legend: { position: 'right' } } },
    }));

    // Chart 2 · DDN par décennie (bar)
    const decades = data.ddnDecades || {};
    charts.push(new Chart(document.getElementById('dashlive-chart-ddn'), {
      type: 'bar',
      data: {
        labels: Object.keys(decades),
        datasets: [{ data: Object.values(decades), backgroundColor: PALETTE.teal, borderRadius: 8 }],
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    }));

    // Chart 3 · tailles fichiers (bar horizontal)
    const sizes = data.sizeBuckets || {};
    charts.push(new Chart(document.getElementById('dashlive-chart-sizes'), {
      type: 'bar',
      data: {
        labels: Object.keys(sizes),
        datasets: [{ data: Object.values(sizes), backgroundColor: PALETTE.violet, borderRadius: 8 }],
      },
      options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } },
    }));

    // Top 10 IPP · rendu liste
    const container = document.getElementById('dashlive-top-ipp');
    const topIpp = data.topIpp || [];
    container.innerHTML = topIpp.length === 0
      ? '<div style="color:#94A3B8;">Aucun IPP encore indexé. Lance un process d\'abord.</div>'
      : `<table style="width:100%; border-collapse:collapse;">
          <thead><tr style="font-size:10px; text-transform:uppercase; letter-spacing:0.1em; color:#64748B;">
            <th style="text-align:left; padding:0.3rem 0;">IPP</th>
            <th style="text-align:right;">Obs</th>
            <th style="text-align:right;">Collisions</th>
          </tr></thead>
          <tbody>${topIpp.map(r => `<tr style="border-top:1px solid #F1F5F9;">
            <td style="padding:0.3rem 0;">${escapeHtml(r.ipp)}</td>
            <td style="text-align:right; color:${PALETTE.teal};">${r.observations}</td>
            <td style="text-align:right; color:${r.collisions > 1 ? PALETTE.error : '#94A3B8'};">${r.collisions}</td>
          </tr>`).join('')}</tbody>
        </table>`;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'F4') {
      e.preventDefault();
      openPanel();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButton);
  } else {
    injectButton();
  }

  window.sovereignDashboard = { open: openPanel, close: closePanel, refresh };
})();

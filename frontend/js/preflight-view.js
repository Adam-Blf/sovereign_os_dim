/*
 * preflight-view.js · Preflight DRUIDES findings grid overlay.
 * Injects a button in the bottom-right stack (below the "?" help button)
 * that opens a full-screen panel showing all validator findings from
 * /api/validate, filterable by severity and code. No app.js modifications.
 */
(function () {
  if (window.__preflightViewLoaded) return;
  window.__preflightViewLoaded = true;

  const SEV_ORDER = { Blocker: 0, Error: 1, Warning: 2, Info: 3 };
  const SEV_STYLE = {
    Blocker: { bg: '#7F1D1D', fg: '#ffffff', label: 'BLOCKER' },
    Error:   { bg: '#DC2626', fg: '#ffffff', label: 'ERROR' },
    Warning: { bg: '#F59E0B', fg: '#1F2937', label: 'WARNING' },
    Info:    { bg: '#0EA5E9', fg: '#ffffff', label: 'INFO' },
  };

  let state = { findings: [], filter: null, search: '' };

  function injectButton() {
    if (document.getElementById('preflight-button')) return;
    const btn = document.createElement('button');
    btn.id = 'preflight-button';
    btn.title = 'Preflight DRUIDES';
    btn.innerHTML = '<span style="font-size:20px;">✓</span>';
    btn.setAttribute('aria-label', 'Ouvrir le preflight DRUIDES');
    btn.style.cssText = `
      position:fixed; z-index:9996; right:24px; bottom:90px; width:52px; height:52px;
      border-radius:50%; border:0; cursor:pointer;
      background:linear-gradient(135deg,#00897B 0%,#10B981 100%); color:white;
      box-shadow:0 8px 20px rgba(0,137,123,0.35); transition:transform .2s;
    `;
    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.1)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1.0)');
    btn.addEventListener('click', openPanel);
    document.body.appendChild(btn);
  }

  async function runValidation() {
    try {
      if (!window.pywebview?.api?.validate_preflight) {
        alert('API non disponible · bridge pas démarré ?');
        return;
      }
      const r = await window.pywebview.api.validate_preflight();
      state.findings = r.findings || [];
      renderPanel();
    } catch (e) {
      alert('Erreur preflight · ' + e.message);
    }
  }

  function openPanel() {
    closePanel();
    const wrap = document.createElement('div');
    wrap.id = 'preflight-overlay';
    wrap.innerHTML = `
      <div style="position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:9998;"
           id="preflight-backdrop"></div>
      <div style="position:fixed; z-index:9999; top:5vh; left:5vw; width:90vw; height:90vh;
                  background:#F8FAFC; color:#0F172A; border-radius:24px;
                  box-shadow:0 20px 60px rgba(0,0,0,.4); display:flex; flex-direction:column;
                  overflow:hidden; font-family:'Plus Jakarta Sans',sans-serif;">
        <header style="padding:1.5rem 2rem; border-bottom:1px solid #E2E8F0;
                       display:flex; justify-content:space-between; align-items:center;
                       background:linear-gradient(135deg,#000091 0%,#00897B 100%); color:#fff;">
          <div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:10px;
                        letter-spacing:0.4em; text-transform:uppercase; opacity:0.7;">Preflight</div>
            <h2 style="font-size:1.75rem; font-weight:900; font-style:italic; letter-spacing:-0.02em;
                       text-transform:uppercase; margin:0.25rem 0 0;">DRUIDES · Findings</h2>
          </div>
          <div style="display:flex; gap:0.75rem;">
            <button id="preflight-run" style="border:0; background:#10B981; color:#fff;
                   padding:0.6rem 1.2rem; border-radius:999px; cursor:pointer;
                   font-family:'JetBrains Mono',monospace; letter-spacing:0.1em; font-weight:700;">
              LANCER</button>
            <button id="preflight-close" style="border:0; background:rgba(255,255,255,0.2); color:#fff;
                   padding:0.6rem 1.2rem; border-radius:999px; cursor:pointer;
                   font-family:'JetBrains Mono',monospace; letter-spacing:0.1em;">FERMER</button>
          </div>
        </header>
        <div id="preflight-filters" style="padding:1rem 2rem; border-bottom:1px solid #E2E8F0;
                                           background:#ffffff; display:flex; gap:0.75rem;
                                           align-items:center; flex-wrap:wrap;"></div>
        <div id="preflight-grid" style="flex:1; overflow:auto; padding:1rem 2rem;"></div>
      </div>
    `;
    document.body.appendChild(wrap);
    document.getElementById('preflight-backdrop').addEventListener('click', closePanel);
    document.getElementById('preflight-close').addEventListener('click', closePanel);
    document.getElementById('preflight-run').addEventListener('click', runValidation);
    renderPanel();
  }

  function closePanel() {
    document.getElementById('preflight-overlay')?.remove();
  }

  function renderPanel() {
    const filters = document.getElementById('preflight-filters');
    const grid = document.getElementById('preflight-grid');
    if (!filters || !grid) return;

    const counts = { Blocker: 0, Error: 0, Warning: 0, Info: 0 };
    state.findings.forEach(f => { counts[f.Severity] = (counts[f.Severity] || 0) + 1; });

    const chip = (sev, active) => {
      const s = SEV_STYLE[sev];
      return `<button data-sev="${sev}" style="
        border:0; padding:0.4rem 0.9rem; border-radius:999px; cursor:pointer;
        font-family:'JetBrains Mono',monospace; letter-spacing:0.1em; font-size:11px; font-weight:700;
        background:${active ? s.bg : '#E2E8F0'}; color:${active ? s.fg : '#475569'};
        opacity:${counts[sev] === 0 ? 0.4 : 1}; transition:all .15s;">
        ${s.label} · ${counts[sev] || 0}</button>`;
    };

    filters.innerHTML = `
      ${chip('Blocker', state.filter === 'Blocker')}
      ${chip('Error', state.filter === 'Error')}
      ${chip('Warning', state.filter === 'Warning')}
      ${chip('Info', state.filter === 'Info')}
      <button data-sev="" style="border:0; padding:0.4rem 0.9rem; border-radius:999px; cursor:pointer;
              font-family:'JetBrains Mono',monospace; letter-spacing:0.1em; font-size:11px;
              background:${state.filter === null ? '#000091' : '#E2E8F0'};
              color:${state.filter === null ? '#fff' : '#475569'};">TOUT · ${state.findings.length}</button>
      <input id="preflight-search" placeholder="Filtre code/message..." value="${escapeHtml(state.search)}"
             style="flex:1; min-width:200px; padding:0.4rem 0.8rem; border-radius:8px;
                    border:1px solid #CBD5E1; font-family:inherit;">
    `;
    filters.querySelectorAll('button[data-sev]').forEach(b =>
      b.addEventListener('click', () => {
        state.filter = b.dataset.sev || null;
        renderPanel();
      }));
    const si = document.getElementById('preflight-search');
    if (si) si.addEventListener('input', (e) => { state.search = e.target.value.toLowerCase(); renderPanel(); });

    let filtered = state.findings;
    if (state.filter) filtered = filtered.filter(f => f.Severity === state.filter);
    if (state.search) {
      const q = state.search;
      filtered = filtered.filter(f =>
        (f.Code || '').toLowerCase().includes(q) ||
        (f.Message || '').toLowerCase().includes(q) ||
        (f.SourceFile || '').toLowerCase().includes(q));
    }
    filtered.sort((a, b) => (SEV_ORDER[a.Severity] ?? 9) - (SEV_ORDER[b.Severity] ?? 9));

    if (filtered.length === 0) {
      grid.innerHTML = `<div style="padding:3rem; text-align:center; color:#64748B;
                             font-family:'JetBrains Mono',monospace;">
        ${state.findings.length === 0
          ? 'Cliquer sur LANCER pour exécuter le preflight · nécessite un scan préalable.'
          : 'Aucun finding correspond aux filtres.'}
      </div>`;
      return;
    }

    grid.innerHTML = `
      <table style="width:100%; border-collapse:collapse; font-size:13px;">
        <thead><tr style="background:#F1F5F9; text-transform:uppercase; font-size:10px;
                          letter-spacing:0.1em; color:#475569;">
          <th style="padding:0.6rem 0.8rem; text-align:left;">Sév</th>
          <th style="padding:0.6rem 0.8rem; text-align:left;">Code</th>
          <th style="padding:0.6rem 0.8rem; text-align:left;">Message</th>
          <th style="padding:0.6rem 0.8rem; text-align:left;">Fichier</th>
          <th style="padding:0.6rem 0.8rem; text-align:right;">Ligne</th>
        </tr></thead>
        <tbody>${filtered.map(f => {
          const s = SEV_STYLE[f.Severity] || SEV_STYLE.Info;
          const fname = (f.SourceFile || '').split(/[\\/]/).pop() || '';
          return `<tr style="border-bottom:1px solid #E2E8F0;">
            <td style="padding:0.5rem 0.8rem;">
              <span style="background:${s.bg}; color:${s.fg}; padding:2px 8px;
                           border-radius:4px; font-size:10px; font-family:'JetBrains Mono',monospace;
                           letter-spacing:0.1em;">${s.label}</span></td>
            <td style="padding:0.5rem 0.8rem; font-family:'JetBrains Mono',monospace; font-size:12px;">
              ${escapeHtml(f.Code || '')}</td>
            <td style="padding:0.5rem 0.8rem;">${escapeHtml(f.Message || '')}
              ${f.FixHint ? `<div style="font-size:11px; color:#64748B; margin-top:2px;">
                💡 ${escapeHtml(f.FixHint)}</div>` : ''}</td>
            <td style="padding:0.5rem 0.8rem; font-family:'JetBrains Mono',monospace;
                       font-size:11px; color:#64748B;" title="${escapeHtml(f.SourceFile || '')}">
              ${escapeHtml(fname)}</td>
            <td style="padding:0.5rem 0.8rem; text-align:right; color:#64748B;">
              ${Number.isFinite(Number(f.LineNumber)) ? Number(f.LineNumber) : ''}</td>
          </tr>`;
        }).join('')}</tbody>
      </table>
    `;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'F2') {
      e.preventDefault();
      openPanel();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButton);
  } else {
    injectButton();
  }

  window.sovereignPreflight = { open: openPanel, close: closePanel };
})();

/*
 * htmlpdf-view.js · HTML → PDF conversion overlay with drag-drop zone.
 * Calls /api/html-to-pdf (Landscape=true for BIQuery dashboards).
 * Floating button anchored above the Preflight button.
 */
(function () {
  if (window.__htmlPdfViewLoaded) return;
  window.__htmlPdfViewLoaded = true;

  function injectButton() {
    if (document.getElementById('htmlpdf-button')) return;
    const btn = document.createElement('button');
    btn.id = 'htmlpdf-button';
    btn.title = 'HTML → PDF';
    btn.innerHTML = '<span style="font-size:20px;">📄</span>';
    btn.setAttribute('aria-label', 'Ouvrir HTML vers PDF');
    btn.style.cssText = `
      position:fixed; z-index:9995; right:24px; bottom:156px; width:52px; height:52px;
      border-radius:50%; border:0; cursor:pointer;
      background:linear-gradient(135deg,#7C3AED 0%,#EC4899 100%); color:white;
      box-shadow:0 8px 20px rgba(124,58,237,0.35); transition:transform .2s;
    `;
    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.1)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1.0)');
    btn.addEventListener('click', openPanel);
    document.body.appendChild(btn);
  }

  function openPanel() {
    closePanel();
    const wrap = document.createElement('div');
    wrap.id = 'htmlpdf-overlay';
    wrap.innerHTML = `
      <div style="position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:9998;"
           id="htmlpdf-backdrop"></div>
      <div style="position:fixed; z-index:9999; top:50%; left:50%; transform:translate(-50%,-50%);
                  width:min(640px,92vw); background:#F8FAFC; color:#0F172A;
                  border-radius:24px; box-shadow:0 20px 60px rgba(0,0,0,.4);
                  font-family:'Plus Jakarta Sans',sans-serif; overflow:hidden;">
        <header style="padding:1.5rem 2rem;
                       background:linear-gradient(135deg,#7C3AED 0%,#EC4899 100%); color:#fff;">
          <div style="font-family:'JetBrains Mono',monospace; font-size:10px;
                      letter-spacing:0.4em; text-transform:uppercase; opacity:0.8;">HTML → PDF</div>
          <h2 style="font-size:1.5rem; font-weight:900; font-style:italic; letter-spacing:-0.02em;
                     text-transform:uppercase; margin:0.25rem 0 0;">Conversion dashboard</h2>
        </header>
        <div style="padding:2rem;">
          <div id="htmlpdf-drop" style="border:3px dashed #CBD5E1; border-radius:16px;
                                        padding:2.5rem; text-align:center; cursor:pointer;
                                        transition:all .2s; background:#ffffff;">
            <div style="font-size:48px; margin-bottom:1rem;">📂</div>
            <p style="margin:0; font-size:15px; color:#475569;">
              Glissez un fichier <code>.html</code> ici<br>
              <span style="font-size:13px; color:#94A3B8;">
                ou cliquez pour choisir depuis l'espace de travail</span>
            </p>
          </div>
          <label style="display:flex; align-items:center; gap:0.5rem; margin-top:1rem;
                       font-size:13px; color:#475569;">
            <input type="checkbox" id="htmlpdf-landscape" checked>
            Paysage + nettoyage dashboard (recommandé pour BIQuery, Looker Studio)
          </label>
          <div id="htmlpdf-status" style="margin-top:1rem; min-height:24px; font-size:13px;
                                          font-family:'JetBrains Mono',monospace;"></div>
        </div>
        <footer style="padding:1rem 2rem; background:#F1F5F9; display:flex;
                       justify-content:flex-end; gap:0.75rem;">
          <button id="htmlpdf-close" style="border:0; background:#CBD5E1; color:#0F172A;
                 padding:0.5rem 1.2rem; border-radius:999px; cursor:pointer;
                 font-family:'JetBrains Mono',monospace; letter-spacing:0.1em;">FERMER</button>
        </footer>
      </div>
    `;
    document.body.appendChild(wrap);

    const drop = document.getElementById('htmlpdf-drop');
    const status = document.getElementById('htmlpdf-status');
    const closer = () => closePanel();
    document.getElementById('htmlpdf-backdrop').addEventListener('click', closer);
    document.getElementById('htmlpdf-close').addEventListener('click', closer);

    drop.addEventListener('click', pickFromHost);
    drop.addEventListener('dragover', (e) => {
      e.preventDefault();
      drop.style.borderColor = '#7C3AED';
      drop.style.background = '#F5F3FF';
    });
    drop.addEventListener('dragleave', () => {
      drop.style.borderColor = '#CBD5E1';
      drop.style.background = '#ffffff';
    });
    drop.addEventListener('drop', async (e) => {
      e.preventDefault();
      drop.style.borderColor = '#CBD5E1';
      drop.style.background = '#ffffff';
      const file = e.dataTransfer?.files?.[0];
      if (!file) return;
      status.textContent = 'Drag-drop ne fournit pas un chemin absolu côté WebView2.\n' +
                          'Cliquez sur la zone pour utiliser le sélecteur natif.';
      status.style.color = '#DC2626';
    });

    async function pickFromHost() {
      if (!window.pywebview?.api?.select_structure_file && !window.pywebview?.api?.select_csv_file) {
        status.textContent = 'API dialog non disponible.';
        return;
      }
      // Reuse select_structure_file or select_csv_file with a tweak · the host dialog accepts any filter.
      const picker = window.pywebview.api.select_structure_file || window.pywebview.api.select_csv_file;
      let path;
      try { path = await picker(); } catch { path = null; }
      if (!path) { status.textContent = 'Annulé.'; status.style.color = '#94A3B8'; return; }
      await convert(path);
    }

    async function convert(htmlPath) {
      const landscape = document.getElementById('htmlpdf-landscape').checked;
      status.textContent = 'Conversion en cours...';
      status.style.color = '#475569';
      try {
        const r = await window.pywebview.api.html_to_pdf(htmlPath, null, landscape);
        const out = r?.payload?.output || r?.output || '(inconnu)';
        status.innerHTML = `✅ PDF généré · <code style="font-size:12px;">${escapeHtml(out)}</code>`;
        status.style.color = '#10B981';
      } catch (e) {
        status.textContent = '❌ ' + (e.message || e);
        status.style.color = '#DC2626';
      }
    }
  }

  function closePanel() {
    document.getElementById('htmlpdf-overlay')?.remove();
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'F3') {
      e.preventDefault();
      openPanel();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButton);
  } else {
    injectButton();
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  window.sovereignHtmlPdf = { open: openPanel, close: closePanel };
})();

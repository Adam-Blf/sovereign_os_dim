/*
 * bridge-shim.js · adapts the frontend to the C# ASP.NET Core bridge
 * and the native WebView2 host. When loaded, it exposes
 * window.pywebview.api.<method>() shims that translate to fetch('/api/...')
 * calls, and forwards native-dialog methods to the host via postMessage.
 * Include this BEFORE app.js in the C# build. No-op when real pywebview
 * is already present (Python build keeps working unchanged).
 */
(function () {
  if (window.pywebview && window.pywebview.api) return;

  const BRIDGE = 'http://127.0.0.1:8787';
  // Injected by the WPF host via AddScriptToExecuteOnDocumentCreatedAsync.
  const TOKEN = (typeof window !== 'undefined' && window.__SOVEREIGN_TOKEN) || null;

  async function call(method, path, body) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (TOKEN) opts.headers.Authorization = 'Bearer ' + TOKEN;
    if (body !== undefined) opts.body = JSON.stringify(body);
    const r = await fetch(BRIDGE + path, opts);
    if (!r.ok) {
      let detail = '';
      try { detail = await r.text(); } catch { /* ignore */ }
      throw new Error('bridge ' + r.status + ' ' + path + ' :: ' + detail);
    }
    const ct = r.headers.get('content-type') || '';
    return ct.includes('application/json') ? r.json() : r.text();
  }

  // ── Host bridge for native Windows dialogs ─────────────────────────────
  // The C# MainWindow listens on WebMessageReceived and replies on
  // PostWebMessageAsJson. We resolve pending requests by id.
  const host = {
    enabled: !!(window.chrome && window.chrome.webview),
    pending: new Map(),
    nextId: 1,
  };

  if (host.enabled) {
    window.chrome.webview.addEventListener('message', (event) => {
      try {
        const raw = event.data;
        const data = typeof raw === 'string' ? JSON.parse(raw) : raw;
        const { id, payload } = data || {};
        const resolver = host.pending.get(id);
        if (!resolver) return;
        host.pending.delete(id);
        resolver(payload);
      } catch (e) {
        console.warn('[bridge-shim] host reply parse error', e);
      }
    });
  }

  function callHost(type, extra) {
    if (!host.enabled) {
      return Promise.resolve({ error: 'host not available (no WebView2)' });
    }
    const id = 'req_' + (host.nextId++);
    const msg = Object.assign({ type, id }, extra || {});
    return new Promise((resolve) => {
      host.pending.set(id, resolve);
      window.chrome.webview.postMessage(JSON.stringify(msg));
      // Safety timeout: clear pending after 5 min so we never leak
      setTimeout(() => host.pending.delete(id), 5 * 60 * 1000);
    });
  }

  const api = {
    // Folders
    get_folders: () => call('GET', '/api/folders'),
    add_folders: (list) => call('POST', '/api/folders', { Folders: list }),
    clear_folders: () => call('DELETE', '/api/folders'),

    // Scan / process
    scan_files: () => call('POST', '/api/scan'),
    process_all: () => call('POST', '/api/process'),
    scan_and_process: () => call('POST', '/api/scan-and-process'),

    // Matrix
    get_matrix_info: () => call('GET', '/api/matrix'),
    identify_format: (filename) => call('POST', '/api/identify', { Filename: filename }),

    // MPI
    get_collisions: () => call('GET', '/api/collisions'),
    set_pivot: (ipp, ddn) => call('POST', '/api/resolve', { Ipp: ipp, Ddn: ddn }),
    auto_resolve: () => call('POST', '/api/auto-resolve'),

    // Stats
    get_dashboard_stats: () => call('GET', '/api/stats'),

    // Export
    export_csv: (outputPath) => call('POST', '/api/export', { OutputPath: outputPath }),
    export_csv_to: (outputPath) => call('POST', '/api/export', { OutputPath: outputPath }),
    export_sanitized: (sourceFile, outputFile) =>
      call('POST', '/api/export-sanitized', { SourceFile: sourceFile, OutputFile: outputFile }),

    // Structure
    parse_structure: (filePath) => call('POST', '/api/structure', { FilePath: filePath }),

    // DRUIDES pre-flight · catches errors before e-PMSI upload
    validate_preflight: () => call('POST', '/api/validate'),

    // Drain log buffer (pattern de pywebview-style progress stream)
    get_pending_logs: () => call('GET', '/api/logs'),

    // Diagnostic line-by-line · retourne la décomposition champ par champ
    inspect_line: (filePath, lineNumber) =>
      call('POST', '/api/inspect', { FilePath: filePath, LineNumber: lineNumber }),

    // Prévisualisation Excel · 100 premières lignes du premier feuillet
    import_excel: (filePath, maxRows = 100) =>
      call('POST', '/api/import-excel', { FilePath: filePath, MaxRows: maxRows }),

    // IA suggestion DP · quand ERR-DIAG-ABSENT détecté
    suggest_dp: (umLabel, sectorType, modeLegal, freeText, topK = 3) =>
      call('POST', '/api/suggest-dp', { UmLabel: umLabel, SectorType: sectorType, ModeLegal: modeLegal, FreeText: freeText, TopK: topK }),

    // Persistance MPI SQLite
    mpi_save: () => call('POST', '/api/mpi/save'),
    mpi_load: () => call('POST', '/api/mpi/load'),
    mpi_stats: () => call('GET', '/api/mpi/stats'),
    mpi_clear: () => call('POST', '/api/mpi/clear'),

    // Dashboard live · agrégats MPI pour Chart.js
    dashboard_live: () => call('GET', '/api/dashboard'),

    // HTML → PDF (for BIQuery dashboards saved as .html, and the bundled manual)
    html_to_pdf: (htmlPath, outputPath, landscape = false) =>
      call('POST', '/api/html-to-pdf', { HtmlPath: htmlPath, OutputPath: outputPath, Landscape: landscape }),
    open_manual: () => call('GET', '/api/manual'),

    // System
    reset_all: () => call('POST', '/api/reset'),
    health: () => call('GET', '/health'),

    // Native dialogs (proxied to the WPF host)
    select_folder: async () => {
      const result = await callHost('selectFolder');
      if (!result || result.cancelled) return null;
      if (result.folder) {
        // Auto-register the folder so the rest of the UI behaves as in pywebview.
        const added = await api.add_folders([result.folder]);
        return { folder: result.folder, all_folders: added.folders };
      }
      return null;
    },

    select_csv_file: async () => {
      const result = await callHost('selectFile', {
        filter: 'CSV;TSV|*.csv;*.tsv|Tous les fichiers|*.*',
      });
      if (!result || result.cancelled) return null;
      return result.file || null;
    },

    select_structure_file: async () => {
      const result = await callHost('selectFile', {
        filter: 'Structure (CSV/TSV)|*.csv;*.tsv|Tous les fichiers|*.*',
      });
      if (!result || result.cancelled) return null;
      return result.file || null;
    },

    get_pending_logs: () => Promise.resolve([]),
  };

  window.pywebview = window.pywebview || {};
  window.pywebview.api = api;
  console.info('[bridge-shim] pywebview.api → http bridge at ' + BRIDGE + ' · host dialogs ' + (host.enabled ? 'ON' : 'OFF'));
})();

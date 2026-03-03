# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — API v3.0
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V32.0 — Station DIM GHT Sud Paris
#  Date    : 2026-03-02
#
#  Description:
#    Classe API exposée au JavaScript via window.pywebview.api (js_api).
#    Chaque méthode publique de cette classe est callable depuis le frontend
#    via `await window.pywebview.api.method_name(args)`.
#
#  Endpoints exposés :
#    - Gestion des dossiers : select_folder, add_folders, get_folders, clear
#    - Scan & Process : scan_files, process_all, scan_and_process (batch)
#    - MPI : get_collisions, set_pivot, auto_resolve, search_collisions
#    - Inspection : inspect_file (terminal line-by-line)
#    - Export : export_csv, export_csv_to, export_sanitized
#    - Stats : get_dashboard_stats, get_matrix_info, get_mpi_stats
#    - Import CSV : import_csv_file (nouveau — import de CSV externes)
#    - Système : reset_all, get_pending_logs
# ══════════════════════════════════════════════════════════════════════════════

import os
import csv
import webview
from backend.data_processor import DataProcessor


class Api:
    """
    API pywebview exposée au frontend JavaScript.

    Convention pywebview : toutes les méthodes publiques de cette classe
    sont automatiquement disponibles dans le frontend via :
        window.pywebview.api.<method_name>(args)

    Les méthodes retournent des dict JSON-serializable qui sont
    automatiquement convertis en objets JavaScript côté frontend.
    """

    def __init__(self):
        # Le processor est le moteur métier (ATIH engine)
        self.processor = DataProcessor()
        # Dossiers actuellement chargés par l'utilisateur
        self.current_folders = []
        # Fichiers .txt/.csv détectés lors du scan
        self.current_files = []

    # ──────────────────────────────────────────────────────────────────────────
    # GESTION DES DOSSIERS — Sélection, ajout, vidage
    # ──────────────────────────────────────────────────────────────────────────

    def select_folder(self):
        """
        Ouvre un dialog natif pour sélectionner un dossier.
        Le dossier est ajouté à la liste s'il n'y figure pas déjà.
        """
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            folder = result[0]
            if folder not in self.current_folders:
                self.current_folders.append(folder)
            return {"folder": folder, "all_folders": self.current_folders}
        return None

    def add_folders(self, folder_list):
        """
        Ajoute plusieurs dossiers ou fichiers déposés par drag & drop.
        Si un fichier est déposé, on ajoute son dossier parent.
        """
        added = []
        for f in folder_list:
            f = f.strip()
            if os.path.isdir(f) and f not in self.current_folders:
                self.current_folders.append(f)
                added.append(f)
            elif os.path.isfile(f):
                # Si c'est un fichier, on remonte au dossier parent
                parent = os.path.dirname(f)
                if parent not in self.current_folders:
                    self.current_folders.append(parent)
                    added.append(parent)
        return {"added": added, "all_folders": self.current_folders}

    def get_folders(self):
        """Retourne la liste des dossiers actuellement chargés."""
        return self.current_folders

    def clear_folders(self):
        """Vide tous les dossiers, fichiers et recrée un processor vierge."""
        self.current_folders.clear()
        self.current_files.clear()
        self.processor = DataProcessor()
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # SCAN & PROCESS — Pipeline de traitement batch
    # ──────────────────────────────────────────────────────────────────────────

    def scan_files(self):
        """
        Scanne tous les dossiers chargés pour trouver les fichiers PMSI.
        Détecte automatiquement les .txt et .csv.
        """
        if not self.current_folders:
            return {"error": "Aucun dossier sélectionné", "files": []}
        self.current_files = self.processor.scan_multiple_directories(
            self.current_folders
        )
        return {
            "files": self.current_files,
            "count": len(self.current_files),
            "logs": self.processor.get_logs(),
        }

    def process_all(self):
        """Traite tous les fichiers scannés (extraction MPI parallèle)."""
        if not self.current_files:
            return {"error": "Aucun fichier à traiter"}
        stats = self.processor.process_files(self.current_files)
        return {"stats": stats, "logs": self.processor.get_logs()}

    def scan_and_process(self):
        """
        Batch : scan + traitement en un seul appel.
        Raccourci pour le bouton "Scanner & Traiter" du frontend.
        """
        scan = self.scan_files()
        if scan.get("error"):
            return scan
        proc = self.process_all()
        return {
            "files": self.current_files,
            "stats": proc.get("stats"),
            "logs": self.processor.get_logs(),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # IMPORT CSV — Lecture et affichage de fichiers CSV externes
    # ──────────────────────────────────────────────────────────────────────────

    def select_csv_file(self):
        """
        Ouvre un dialog natif pour sélectionner un fichier CSV.
        Retourne le chemin du fichier sélectionné.
        """
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Fichiers CSV (*.csv)",),
        )
        if result and len(result) > 0:
            return result[0]
        return None

    def import_csv_file(self, filepath):
        """
        Lit un fichier CSV et retourne ses données pour affichage.
        Supporte les séparateurs ; et , (auto-détection).
        Limité à 5000 lignes pour ne pas saturer le frontend.
        """
        if not filepath or not os.path.isfile(filepath):
            return {"error": "Fichier introuvable"}

        try:
            # Auto-détection du séparateur (sniff les premières lignes)
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                sample = f.read(4096)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
                    sep = dialect.delimiter
                except csv.Error:
                    sep = ";"  # Fallback PMSI standard

            rows = []
            headers = []
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter=sep)
                for i, row in enumerate(reader):
                    if i == 0:
                        headers = row
                        continue
                    if i > 5000:
                        break
                    rows.append(row)

            return {
                "filename": os.path.basename(filepath),
                "path": filepath,
                "headers": headers,
                "rows": rows,
                "total_rows": len(rows),
                "separator": sep,
            }
        except (OSError, UnicodeDecodeError) as e:
            return {"error": str(e)}

    # ──────────────────────────────────────────────────────────────────────────
    # MPI — Master Patient Index (résolution des collisions)
    # ──────────────────────────────────────────────────────────────────────────

    def get_collisions(self):
        """Retourne la liste des collisions IPP/DDN non résolues."""
        return self.processor.get_collisions()

    def set_pivot(self, ipp, ddn):
        """Définit manuellement la DDN pivot pour un IPP donné."""
        ok = self.processor.set_pivot(ipp, ddn)
        return {"success": ok, "logs": self.processor.get_logs()}

    def auto_resolve(self):
        """
        Résout automatiquement toutes les collisions non résolues.
        Utilise la DDN la plus fréquente comme pivot.
        """
        count = self.processor.auto_resolve_all()
        return {
            "resolved": count,
            "collisions": self.processor.get_collisions(),
            "mpi_stats": self.processor.get_mpi_stats(),
            "logs": self.processor.get_logs(),
        }

    def get_mpi_stats(self):
        """Retourne les stats globales du MPI (total, collisions, résolues)."""
        return self.processor.get_mpi_stats()

    def search_collisions(self, query):
        """Recherche dans les collisions par IPP partiel (filtre live)."""
        q = query.strip().lower()
        all_cols = self.processor.get_collisions()
        if not q:
            return all_cols
        return [c for c in all_cols if q in c["ipp"].lower()]

    # ──────────────────────────────────────────────────────────────────────────
    # INSPECTION — Analyse ligne par ligne pour le terminal
    # ──────────────────────────────────────────────────────────────────────────

    def inspect_file(self, filepath):
        """Ouvre l'Inspector Terminal pour un fichier donné."""
        return self.processor.inspect_file(filepath)

    # ──────────────────────────────────────────────────────────────────────────
    # EXPORT CSV — Données normalisées avec DDN pivot injectée
    # ──────────────────────────────────────────────────────────────────────────

    def export_csv(self):
        """Exporte les CSV dans le sous-dossier PILOT_OUTPUT du 1er dossier."""
        if not self.current_files:
            return {"error": "Aucun fichier"}
        if not self.current_folders:
            return {"error": "Aucun dossier"}
        out = os.path.join(self.current_folders[0], "PILOT_OUTPUT")
        result = self.processor.export_csv(self.current_files, out)
        result["logs"] = self.processor.get_logs()
        return result

    def select_export_folder(self):
        """Ouvre un dialog natif pour choisir le dossier d'export."""
        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            return result[0]
        return None

    def export_csv_to(self, output_dir):
        """Exporte les CSV dans un dossier choisi par l'utilisateur."""
        if not self.current_files:
            return {"error": "Aucun fichier"}
        result = self.processor.export_csv(self.current_files, output_dir)
        result["logs"] = self.processor.get_logs()
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # EXPORT SANITIZED — Fichier .txt purifié avec pivot injecté
    # ──────────────────────────────────────────────────────────────────────────

    def export_sanitized(self, filepath):
        """Exporte un .txt purifié avec DDN pivot injectée."""
        if not self.current_folders:
            return {"error": "Aucun dossier"}
        out = os.path.join(self.current_folders[0], "PILOT_OUTPUT")
        return self.processor.export_sanitized_txt(filepath, out)

    # ──────────────────────────────────────────────────────────────────────────
    # STATISTIQUES — Dashboard et matrice ATIH
    # ──────────────────────────────────────────────────────────────────────────

    def get_matrix_info(self):
        """Retourne les détails de la matrice ATIH pour le dashboard."""
        return [
            {"key": k, "length": v["length"],
             "ipp": list(v["ipp"]), "ddn": list(v["ddn"]),
             "desc": v.get("desc", "")}
            for k, v in self.processor.matrix.items()
        ]

    def get_dashboard_stats(self):
        """
        Stats globales pour le dashboard :
        dossiers, fichiers, formats, MPI, répartition, stats par fichier.
        """
        mpi = self.processor.get_mpi_stats()
        return {
            "folders": len(self.current_folders),
            "files": len(self.current_files),
            "formats": len(self.processor.matrix),
            "mpi": mpi,
            "format_breakdown": self.processor.get_format_breakdown(),
            "file_stats": self.processor.file_stats,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # SYSTÈME — Reset et logs
    # ──────────────────────────────────────────────────────────────────────────

    def reset_all(self):
        """Réinitialise complètement l'application (nouveau processor)."""
        self.processor = DataProcessor()
        self.current_folders.clear()
        self.current_files.clear()
        return True

    def get_pending_logs(self):
        """Récupère les logs en attente (drain pattern)."""
        return self.processor.get_logs()

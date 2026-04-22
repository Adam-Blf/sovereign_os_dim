# ══════════════════════════════════════════════════════════════════════════════
#  SOVEREIGN OS DIM — Tests unitaires du Data Processor
# ══════════════════════════════════════════════════════════════════════════════
#  Author  : Adam Beloucif
#  Project : Sovereign OS V34.0 — Station DIM GHT Sud Paris
#  Date    : 2026-03-03
#
#  Couverture :
#    - Identification de format ATIH (23 formats)
#    - Validation de ligne
#    - Normalisation IPP (cohérence BIQuery)
#    - Extraction IPP/DDN (tous champs : PSY, MCO, SSR, HAD)
#    - Auto-détection de variantes 2021
#    - Collisions MPI et résolution
#    - Export CSV et .txt purifié
# ══════════════════════════════════════════════════════════════════════════════

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data_processor import DataProcessor, ATIH_MATRIX, ATIH_FORMAT_VARIANTS, _csv_safe


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — IDENTIFICATION DE FORMAT (23 formats ATIH)
# ══════════════════════════════════════════════════════════════════════════════

class TestIdentifyFormat:
    """
    Vérifie que chaque nom de fichier ATIH est correctement identifié.
    
    Pourquoi c'est critique ? L'identification du format est la première
    étape du pipeline. Une erreur ici propage des positions IPP/DDN
    incorrectes dans tout le traitement.
    """

    # ─── PSY ──────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("filename,expected", [
        ("rps_2024.txt", "RPS"),
        ("RPS_FondationVallee_2021.txt", "RPS"),
        ("mon_fichier_rps.txt", "RPS"),
        ("raa_2024.txt", "RAA"),
        ("RAA_2021_fondation.txt", "RAA"),
        ("rpsa_2024.txt", "RPSA"),
        ("RPSA_anonyme.txt", "RPSA"),
        ("r3a_2024.txt", "R3A"),
        ("R3A_ambulatoire.txt", "R3A"),
        ("fichsup_psy_2024.txt", "FICHSUP-PSY"),
        ("fichsup-psy.txt", "FICHSUP-PSY"),
        ("fichsup.txt", "FICHSUP-PSY"),
        ("edgar_2024.txt", "EDGAR"),
        ("ficum-psy.txt", "FICUM-PSY"),
        ("ficum_psy_2024.txt", "FICUM-PSY"),
        ("rsf-ace-psy.txt", "RSF-ACE-PSY"),
        ("rsf_ace_psy_2024.txt", "RSF-ACE-PSY"),
    ])
    def test_psy_formats(self, filename, expected):
        """Identifie tous les formats PSY (natifs + anonymisés + complémentaires)."""
        assert DataProcessor.identify_format(filename) == expected

    # ─── MCO ──────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("filename,expected", [
        ("rss_2024.txt", "RSS"),
        ("rum_2024.txt", "RSS"),
        ("RSS_MCO_2023.txt", "RSS"),
        ("rsfa_2024.txt", "RSFA"),
        ("rsf-a_2024.txt", "RSFA"),
        ("rsf_ace_mco.txt", "RSFA"),
        ("rsfb_2024.txt", "RSFB"),
        ("rsf-b.txt", "RSFB"),
        ("rsfc_2024.txt", "RSFC"),
        ("rsf_c_2024.txt", "RSFC"),
    ])
    def test_mco_formats(self, filename, expected):
        """Identifie tous les formats MCO (RSS, RSF-A/B/C)."""
        assert DataProcessor.identify_format(filename) == expected

    # ─── SSR / SMR ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("filename,expected", [
        ("rhs_2024.txt", "RHS"),
        ("RHS_SMR.txt", "RHS"),
        ("ssrha_2024.txt", "SSRHA"),
        ("rapss_2024.txt", "RAPSS"),
        ("fichcomp_smr.txt", "FICHCOMP-SMR"),
        ("fichcomp-ssr.txt", "FICHCOMP-SMR"),
    ])
    def test_ssr_formats(self, filename, expected):
        """Identifie tous les formats SSR/SMR."""
        assert DataProcessor.identify_format(filename) == expected

    # ─── HAD ──────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("filename,expected", [
        ("rpss_2024.txt", "RPSS"),
        ("rapss_had.txt", "RAPSS-HAD"),
        ("rapss-had_2024.txt", "RAPSS-HAD"),
        ("fichcomp-had.txt", "FICHCOMP-HAD"),
        ("fichcomp_had_2024.txt", "FICHCOMP-HAD"),
        ("ssrha-had.txt", "SSRHA-HAD"),
        ("ssrha_had_2024.txt", "SSRHA-HAD"),
    ])
    def test_had_formats(self, filename, expected):
        """Identifie tous les formats HAD."""
        assert DataProcessor.identify_format(filename) == expected

    # ─── Transversaux ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("filename,expected", [
        ("vidhosp_2024.txt", "VID-HOSP"),
        ("vid-hosp.txt", "VID-HOSP"),
        ("vid_hosp_2024.txt", "VID-HOSP"),
        ("anohosp_2024.txt", "ANO-HOSP"),
        ("ano-hosp.txt", "ANO-HOSP"),
        ("fichcomp_2024.txt", "FICHCOMP"),
    ])
    def test_transversal_formats(self, filename, expected):
        """Identifie les formats transversaux (VID-HOSP, ANO-HOSP, FICHCOMP)."""
        assert DataProcessor.identify_format(filename) == expected

    # ─── Inconnu ──────────────────────────────────────────────────────────

    @pytest.mark.parametrize("filename", [
        "random_file.txt",
        "export_excel.csv",
        "notes.docx",
        "readme.md",
    ])
    def test_unknown_format(self, filename):
        """Les fichiers non-ATIH retournent None."""
        assert DataProcessor.identify_format(filename) is None

    # ─── Priorité (RPSA avant RPS, etc.) ──────────────────────────────────

    def test_rpsa_priority_over_rps(self):
        """RPSA doit être détecté avant RPS (sous-chaîne)."""
        assert DataProcessor.identify_format("rpsa_2024.txt") == "RPSA"

    def test_r3a_priority_over_raa(self):
        """R3A doit être détecté avant RAA (sous-chaîne)."""
        assert DataProcessor.identify_format("r3a_2024.txt") == "R3A"

    def test_rapss_had_priority_over_rapss(self):
        """RAPSS-HAD doit être détecté avant RAPSS (sous-chaîne)."""
        assert DataProcessor.identify_format("rapss_had.txt") == "RAPSS-HAD"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — VALIDATION DE LIGNE
# ══════════════════════════════════════════════════════════════════════════════

class TestLineValidation:
    """
    Vérifie le filtrage des lignes invalides (padding, trop courtes).
    """

    def test_valid_line(self, processor):
        """Une ligne de 60+ chars avec du contenu est valide."""
        assert processor._is_line_valid("A" * 60) is True

    def test_short_line_rejected(self, processor):
        """Les lignes <50 chars sont rejetées (artefacts d'export)."""
        assert processor._is_line_valid("A" * 30) is False

    def test_empty_line_rejected(self, processor):
        """Les lignes vides sont rejetées."""
        assert processor._is_line_valid("") is False

    def test_zero_padding_rejected(self, processor):
        """Les lignes de zéros (padding ATIH) sont rejetées."""
        assert processor._is_line_valid("0" * 100) is False

    def test_space_padding_rejected(self, processor):
        """Les lignes d'espaces sont rejetées."""
        assert processor._is_line_valid(" " * 100) is False

    def test_mixed_zero_space_rejected(self, processor):
        """Les lignes de zéros et espaces mélangés sont rejetées."""
        assert processor._is_line_valid("0 0 0 0 0 " * 10) is False


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — NORMALISATION IPP (cohérence BIQuery)
# ══════════════════════════════════════════════════════════════════════════════

class TestNormalizeIPP:
    """
    Vérifie la normalisation des numéros de dossier (IPP).
    
    Critique pour résoudre le problème Fondation Vallée 2021 :
    les mêmes patients avaient des IPP dans deux formats distincts.
    """

    def test_numeric_strip_zeros(self):
        """IPP numérique : les zéros de tête sont supprimés."""
        assert DataProcessor.normalize_ipp("00000000000000012345") == "12345"

    def test_numeric_single_zero(self):
        """IPP '000' devient '0' (pas de chaîne vide)."""
        assert DataProcessor.normalize_ipp("000") == "0"

    def test_numeric_no_zeros(self):
        """IPP sans zéros de tête reste inchangé."""
        assert DataProcessor.normalize_ipp("12345") == "12345"

    def test_strip_spaces(self):
        """Les espaces en début/fin sont toujours supprimés."""
        assert DataProcessor.normalize_ipp("  12345  ") == "12345"

    def test_alphanumeric_preserved(self):
        """IPP alphanumérique : les zéros internes sont conservés."""
        assert DataProcessor.normalize_ipp("ABC-2021-00042") == "ABC-2021-00042"

    def test_alphanumeric_strip_spaces(self):
        """IPP alphanumérique paddé d'espaces est nettoyé."""
        assert DataProcessor.normalize_ipp("ABC-001      ") == "ABC-001"

    def test_empty_returns_empty(self):
        """IPP vide reste vide."""
        assert DataProcessor.normalize_ipp("") == ""

    def test_spaces_only_returns_empty(self):
        """IPP d'espaces uniquement retourne vide."""
        assert DataProcessor.normalize_ipp("     ") == ""

    def test_consistency_2021_format_a(self):
        """Format A (zéros) et Format B (normal) donnent le même résultat."""
        ipp_a = DataProcessor.normalize_ipp("00000000000000012345")
        ipp_b = DataProcessor.normalize_ipp("12345")
        assert ipp_a == ipp_b == "12345"

    def test_consistency_2021_padded_spaces(self):
        """IPP paddé espaces et IPP normal donnent le même résultat."""
        ipp_a = DataProcessor.normalize_ipp("12345               ")
        ipp_b = DataProcessor.normalize_ipp("12345")
        assert ipp_a == ipp_b == "12345"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — EXTRACTION IPP/DDN (tous formats)
# ══════════════════════════════════════════════════════════════════════════════

class TestExtraction:
    """
    Vérifie l'extraction correcte des IPP et DDN depuis les fichiers ATIH.
    """

    def test_rps_extraction(self, processor, sample_rps_file, temp_dir):
        """Extraction RPS : 3 IPP uniques depuis 4 lignes."""
        files = processor.scan_directory(temp_dir)
        stats = processor.process_files(files)
        assert stats["ipp_unique"] == 3  # 12345, 67890, 11111
        assert stats["lines_valid"] == 4
        assert stats["collisions"] == 0

    def test_raa_extraction(self, processor, sample_raa_file, temp_dir):
        """Extraction RAA : 2 IPP uniques."""
        files = processor.scan_directory(temp_dir)
        stats = processor.process_files(files)
        assert stats["ipp_unique"] == 2

    def test_rss_mco_extraction(self, processor, sample_rss_file, temp_dir):
        """Extraction RSS MCO : positions IPP/DDN différentes de PSY."""
        files = processor.scan_directory(temp_dir)
        stats = processor.process_files(files)
        # MCO001 et MCO002 = 2 IPP uniques
        assert stats["ipp_unique"] == 2
        assert stats["lines_valid"] == 3

    def test_mixed_psy_mco(self, processor, sample_rps_file, sample_rss_file, temp_dir):
        """Traitement mixte PSY + MCO dans le même dossier."""
        files = processor.scan_directory(temp_dir)
        stats = processor.process_files(files)
        # RPS: 12345, 67890, 11111 + RSS: MCO001, MCO002 = 5 IPP 
        assert stats["ipp_unique"] == 5
        assert stats["files_processed"] == 2


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — AUTO-DÉTECTION VARIANTES 2021
# ══════════════════════════════════════════════════════════════════════════════

class TestFormatVariants:
    """
    Vérifie l'auto-détection des variantes de format pour 2021.
    
    Le scénario Fondation Vallée : fichiers RPS 2021 avec des lignes
    de 142 chars (ancien format P04) au lieu de 154 (format P05 standard).
    """

    def test_2021_rps_variant_detection(self, processor, sample_rps_2021_variant, temp_dir):
        """Les fichiers RPS 2021 (142 chars) sont détectés comme variante."""
        spec = processor._detect_format_variant(sample_rps_2021_variant, "RPS")
        assert spec["length"] == 142
        assert "_variant" in spec

    def test_2021_raa_variant_detection(self, processor, sample_raa_2021_variant, temp_dir):
        """Les fichiers RAA 2021 (86 chars) sont détectés comme variante."""
        spec = processor._detect_format_variant(sample_raa_2021_variant, "RAA")
        assert spec["length"] == 86
        assert "_variant" in spec

    def test_standard_format_not_variant(self, processor, sample_rps_file, temp_dir):
        """Les fichiers standard (154 chars) ne sont PAS des variantes."""
        spec = processor._detect_format_variant(sample_rps_file, "RPS")
        assert spec["length"] == 154
        assert "_variant" not in spec

    def test_variant_cache(self, processor, sample_rps_2021_variant, temp_dir):
        """Le résultat de la détection est mis en cache."""
        # Première détection : aucun cache
        spec1 = processor._detect_format_variant(sample_rps_2021_variant, "RPS")
        # Deuxième détection : depuis le cache
        spec2 = processor._detect_format_variant(sample_rps_2021_variant, "RPS")
        assert spec1 is spec2  # Même objet (cache hit)

    def test_ipp_normalization_resolves_duplicates(self, processor, sample_rps_2021_variant, temp_dir):
        """
        Test critique : un IPP '00000000000000012345' et '12345' dans le
        même fichier 2021 doivent être normalisés vers le même identifiant.
        """
        files = processor.scan_directory(temp_dir)
        stats = processor.process_files(files)
        # Les 3 lignes ont le même patient (12345) après normalisation
        assert stats["ipp_unique"] == 2  # 12345 et 67890


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6 — COLLISIONS MPI ET RÉSOLUTION
# ══════════════════════════════════════════════════════════════════════════════

class TestCollisions:
    """
    Vérifie la détection et résolution des collisions d'identité.
    
    Une collision = un même IPP trouvé avec plusieurs DDN différentes.
    Cela arrive quand un patient a des erreurs de saisie sur sa DDN
    dans certains fichiers ATIH.
    """

    def test_collision_detected(self, processor, collision_files, temp_dir):
        """Deux fichiers avec le même IPP et des DDN différentes = collision."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        collisions = processor.get_collisions()
        assert len(collisions) == 1
        assert collisions[0]["ipp"] == "12345"
        assert len(collisions[0]["options"]) == 2  # Deux DDN candidates

    def test_auto_resolve(self, processor, collision_files, temp_dir):
        """
        Auto-résolution : en cas d'égalité de sources, choisit la DDN
        la plus grande (récente en format AAAAMMJJ) comme tiebreaker.
        """
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        resolved = processor.auto_resolve_all()
        assert resolved == 1
        # Les deux DDN viennent chacune d'1 source, donc le tiebreaker
        # choisit la plus grande lexicographiquement : 19850316
        assert processor.mpi["12345"]["pivot"] == "19850316"

    def test_manual_pivot(self, processor, collision_files, temp_dir):
        """Pivot manuel : l'utilisateur peut forcer une DDN."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        ok = processor.set_pivot("12345", "19850316")  # Force la DDN erronée
        assert ok is True
        assert processor.mpi["12345"]["pivot"] == "19850316"

    def test_mpi_stats(self, processor, collision_files, temp_dir):
        """Les stats MPI reflètent correctement l'état des collisions."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        stats = processor.get_mpi_stats()
        assert stats["total_ipp"] == 1
        assert stats["collisions"] == 1
        assert stats["resolved"] == 0
        assert stats["pending"] == 1

        # Après résolution
        processor.auto_resolve_all()
        stats = processor.get_mpi_stats()
        assert stats["resolved"] == 1
        assert stats["pending"] == 0

    def test_no_collision_single_ddn(self, processor, sample_rps_file, temp_dir):
        """Pas de collision quand un IPP n'a qu'une seule DDN."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        collisions = processor.get_collisions()
        assert len(collisions) == 0


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7 — EXPORT CSV
# ══════════════════════════════════════════════════════════════════════════════

class TestExportCSV:
    """
    Vérifie l'export CSV PILOT (données normalisées avec pivot injecté).
    """

    def test_csv_export_creates_files(self, processor, sample_rps_file, temp_dir):
        """L'export CSV crée un fichier par fichier source."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        output_dir = os.path.join(temp_dir, "PILOT_OUTPUT")
        result = processor.export_csv(files, output_dir)
        assert result["stats"]["csv_count"] == 1
        assert result["stats"]["lines_exported"] > 0
        assert os.path.isdir(output_dir)

    def test_csv_content_has_header(self, processor, sample_rps_file, temp_dir):
        """Le CSV exporté contient le header IPP;DDN;FORMAT;..."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        output_dir = os.path.join(temp_dir, "PILOT_OUTPUT")
        result = processor.export_csv(files, output_dir)
        csv_path = result["files"][0]["path"]
        with open(csv_path, "r", encoding="utf-8") as f:
            header = f.readline().strip()
        assert header == "IPP;DDN;FORMAT;NOM_FICHIER;LIGNE_BRUTE"

    def test_csv_pivot_injection(self, processor, collision_files, temp_dir):
        """L'export CSV injecte la DDN pivot quand elle est définie."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        # Résolution automatique (choisit 19850315 car 3 occurrences)
        processor.auto_resolve_all()
        output_dir = os.path.join(temp_dir, "PILOT_OUTPUT")
        result = processor.export_csv(files, output_dir)
        # La DDN erronée (19850316) doit avoir été corrigée
        assert result["stats"]["ddn_corrected"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# TEST 8 — EXPORT SANITIZED TXT
# ══════════════════════════════════════════════════════════════════════════════

class TestExportSanitized:
    """
    Vérifie l'export .txt purifié (fichier ATIH conforme, prêt pour e-PMSI).
    """

    def test_sanitized_export(self, processor, sample_rps_file, temp_dir):
        """L'export sanitized crée un fichier _SANITIZED.txt."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        output_dir = os.path.join(temp_dir, "PILOT_OUTPUT")
        result = processor.export_sanitized_txt(sample_rps_file, output_dir)
        assert "error" not in result
        assert result["stats"]["out"] > 0
        assert os.path.isfile(result["path"])
        assert "_SANITIZED" in result["name"]

    def test_sanitized_pivot_injection(self, processor, collision_files, temp_dir):
        """Le fichier sanitized injecte la DDN pivot in-place."""
        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        processor.set_pivot("12345", "19850315")  # Force la DDN correcte
        output_dir = os.path.join(temp_dir, "PILOT_OUTPUT")
        result = processor.export_sanitized_txt(collision_files[1], output_dir)
        assert result["stats"]["pivoted"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# TEST 9 — SCAN ET PROCESSING BATCH
# ══════════════════════════════════════════════════════════════════════════════

class TestScanAndProcess:
    """
    Vérifie le pipeline complet : scan → process → stats.
    """

    def test_scan_empty_directory(self, processor, temp_dir):
        """Scan d'un dossier vide retourne une liste vide."""
        files = processor.scan_directory(temp_dir)
        assert len(files) == 0

    def test_scan_nonexistent_directory(self, processor):
        """Scan d'un dossier inexistant retourne une liste vide."""
        files = processor.scan_directory("/this/does/not/exist")
        assert len(files) == 0

    def test_scan_detects_format(self, processor, sample_rps_file, temp_dir):
        """Le scan identifie correctement le format de chaque fichier."""
        files = processor.scan_directory(temp_dir)
        assert len(files) == 1
        assert files[0]["format"] == "RPS"

    def test_scan_multiple_directories(self, processor, sample_rps_file, temp_dir):
        """Scan de plusieurs dossiers déduplique les fichiers."""
        files = processor.scan_multiple_directories([temp_dir, temp_dir])
        assert len(files) == 1  # Dédupliqué

    def test_process_unknown_format_skipped(self, processor, temp_dir):
        """Les fichiers de format inconnu sont ignorés lors du processing."""
        unknown_file = os.path.join(temp_dir, "random_data.txt")
        with open(unknown_file, "w") as f:
            f.write("A" * 200 + "\n" + "B" * 200 + "\n")
        files = processor.scan_directory(temp_dir)
        stats = processor.process_files(files)
        assert stats["files_skipped"] == 1
        assert stats["files_processed"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# TEST 10 — MATRICE ATIH (intégrité)
# ══════════════════════════════════════════════════════════════════════════════

class TestATIHMatrix:
    """
    Vérifie l'intégrité de la matrice ATIH : positions, longueurs, cohérence.
    """

    @pytest.mark.parametrize("fmt", list(ATIH_MATRIX.keys()))
    def test_matrix_positions_valid(self, fmt):
        """Toutes les positions IPP/DDN sont dans les limites de la longueur."""
        spec = ATIH_MATRIX[fmt]
        assert spec["ipp"][0] < spec["ipp"][1]
        assert spec["ddn"][0] < spec["ddn"][1]
        assert spec["ipp"][1] <= spec["length"]
        assert spec["ddn"][1] <= spec["length"]

    @pytest.mark.parametrize("fmt", list(ATIH_MATRIX.keys()))
    def test_matrix_has_required_keys(self, fmt):
        """Chaque format a les clés obligatoires."""
        spec = ATIH_MATRIX[fmt]
        assert "length" in spec
        assert "ipp" in spec
        assert "ddn" in spec
        assert "desc" in spec
        assert "field" in spec

    def test_23_formats_in_matrix(self):
        """La matrice contient exactement 23 formats ATIH."""
        assert len(ATIH_MATRIX) == 23

    @pytest.mark.parametrize("fmt", list(ATIH_FORMAT_VARIANTS.keys()))
    def test_variants_reference_existing_formats(self, fmt):
        """Chaque variante référence un format existant dans la matrice."""
        assert fmt in ATIH_MATRIX

    @pytest.mark.parametrize("fmt", list(ATIH_FORMAT_VARIANTS.keys()))
    def test_variants_have_valid_positions(self, fmt):
        """Toutes les variantes ont des positions IPP/DDN valides."""
        for var in ATIH_FORMAT_VARIANTS[fmt]:
            assert var["ipp"][0] < var["ipp"][1]
            assert var["ddn"][0] < var["ddn"][1]
            assert var["ipp"][1] <= var["length"]
            assert var["ddn"][1] <= var["length"]


# ══════════════════════════════════════════════════════════════════════════════
# TEST 11 — LOGGING
# ══════════════════════════════════════════════════════════════════════════════

class TestLogging:
    """
    Vérifie le système de logging (buffer drain pattern).
    """

    def test_log_adds_message(self, processor):
        """Les logs sont ajoutés au buffer."""
        processor._log("Test message")
        logs = processor.get_logs()
        assert len(logs) == 1
        assert logs[0]["msg"] == "Test message"
        assert logs[0]["level"] == "INFO"

    def test_get_logs_drains_buffer(self, processor):
        """get_logs() vide le buffer (drain pattern)."""
        processor._log("Message 1")
        processor._log("Message 2")
        logs = processor.get_logs()
        assert len(logs) == 2
        # Deuxième appel : buffer vide
        logs = processor.get_logs()
        assert len(logs) == 0

    def test_log_levels(self, processor):
        """Le niveau de log est correctement enregistré."""
        processor._log("Info", "INFO")
        processor._log("Error", "ERROR")
        processor._log("Warning", "WARN")
        logs = processor.get_logs()
        assert logs[0]["level"] == "INFO"
        assert logs[1]["level"] == "ERROR"
        assert logs[2]["level"] == "WARN"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 12 — CSV FORMULA INJECTION PROTECTION
# ══════════════════════════════════════════════════════════════════════════════

class TestCsvSafe:
    """
    Vérifie que _csv_safe() neutralise les préfixes d'injection de formules
    avant l'écriture des champs dans le CSV PILOT.
    """

    @pytest.mark.parametrize("raw,expected", [
        ("=SUM(A1)", "'=SUM(A1)"),
        ("+cmd", "'+cmd"),
        ("-1", "'-1"),
        ("@SUM", "'@SUM"),
        ("\t leading", "'\t leading"),
        ("\r leading", "'\r leading"),
        ("12345", "12345"),
        ("19850315", "19850315"),
        ("RPS", "RPS"),
        ("", ""),
        ("normal text", "normal text"),
    ])
    def test_csv_safe_prefixes_formula_triggers(self, raw, expected):
        assert _csv_safe(raw) == expected

    def test_export_csv_sanitizes_formula_filename(self, processor, temp_dir):
        """Un fichier source dont le nom commence par '=' est préfixé par ' dans le CSV."""
        spec = ATIH_MATRIX["RPS"]
        length = spec["length"]

        def make_line(ipp, ddn, filler="A"):
            line = filler * 21 + ipp.ljust(20) + ddn.ljust(8)
            return (line + filler * length)[:length]

        fname = "=evil_rps_2024.txt"
        filepath = os.path.join(temp_dir, fname)
        with open(filepath, "w", encoding="latin-1") as f:
            f.write(make_line("12345", "19850315") + "\n")

        files = processor.scan_directory(temp_dir)
        processor.process_files(files)
        output_dir = os.path.join(temp_dir, "PILOT_OUTPUT")
        result = processor.export_csv(files, output_dir)

        assert result["stats"]["lines_exported"] > 0
        csv_path = result["files"][0]["path"]
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()

        for line in content.splitlines()[1:]:
            src_field = line.split(";")[3]
            assert not src_field.startswith("="), (
                f"Formula injection not neutralized in src field: {src_field!r}"
            )
            assert src_field.startswith("'"), (
                f"Expected ' prefix for formula-trigger filename, got: {src_field!r}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# TEST 13 — INSPECT FILE
# ══════════════════════════════════════════════════════════════════════════════

class TestInspectFile:
    """
    Vérifie que inspect_file utilise la spec variant-aware, comme process_files.

    Sans le fix, un fichier RPS 2021 (142 chars) est inspecté avec la spec
    standard (154 chars), ce qui génère de fausses annotations "Paddée 142->154"
    sur chaque ligne valide.
    """

    def test_standard_file_no_false_repair(self, processor, sample_rps_file):
        """Fichier standard (154 chars) : aucune annotation de repair sur les lignes OK."""
        result = processor.inspect_file(sample_rps_file)
        assert "error" not in result
        ok_lines = [l for l in result["lines"] if l["status"] == "OK"]
        assert len(ok_lines) > 0
        for line in ok_lines:
            assert line["repair"] is None, f"False repair on standard line: {line['repair']!r}"

    def test_variant_2021_no_false_repair(self, processor, sample_rps_2021_variant):
        """
        Fichier variante RPS 2021 (142 chars) : inspect_file doit utiliser la
        spec variante et non la spec standard, donc aucune fausse annotation
        "Paddée" sur les lignes de longueur correcte pour ce format.
        """
        result = processor.inspect_file(sample_rps_2021_variant)
        assert "error" not in result
        ok_lines = [l for l in result["lines"] if l["status"] == "OK"]
        assert len(ok_lines) > 0
        for line in ok_lines:
            assert line["repair"] is None, (
                f"inspect_file used wrong spec for 2021 variant: repair={line['repair']!r}"
            )

    def test_inspect_extracts_correct_ipp_ddn(self, processor, sample_rps_file):
        """Les IPP et DDN extraits par inspect_file sont corrects."""
        result = processor.inspect_file(sample_rps_file)
        ok_lines = [l for l in result["lines"] if l["status"] == "OK"]
        ipps = {l["ipp"] for l in ok_lines}
        ddns = {l["ddn"] for l in ok_lines}
        assert "12345" in ipps
        assert "19850315" in ddns

    def test_inspect_unknown_format_returns_error(self, processor, temp_dir):
        """Un fichier de format inconnu retourne une erreur explicite."""
        unknown = os.path.join(temp_dir, "unknown_data.txt")
        with open(unknown, "w", encoding="latin-1") as f:
            f.write("X" * 100 + "\n")
        result = processor.inspect_file(unknown)
        assert "error" in result

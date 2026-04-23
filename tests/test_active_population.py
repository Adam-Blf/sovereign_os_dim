# Tests pour compute_active_population() — KPI "file active" du DIM PSY.
# On monte un MPI factice en bypassant le scan, pour contrôler exactement
# les couples (IPP, année, format) et vérifier le dé-dédoublonnage.


from backend.data_processor import DataProcessor


def _seed(proc: DataProcessor, entries: list[tuple[str, str, str, str]]) -> None:
    """
    Injecte des (ipp, ddn, nom_fichier, format) dans le MPI + file_stats
    comme le ferait un scan réel. DDN factice mais cohérente.
    """
    for ipp, ddn, src, fmt in entries:
        proc.mpi.setdefault(ipp, {"pivot": None, "history": {}})
        proc.mpi[ipp]["history"].setdefault(ddn, []).append(src)
        proc.file_stats[src] = {
            "format": fmt,
            "lines_total": 1,
            "lines_valid": 1,
            "lines_filtered": 0,
        }


def test_empty_mpi_returns_zero_state():
    out = DataProcessor().compute_active_population()
    assert out["years"] == []
    assert out["total_unique_ipp"] == 0
    assert out["by_year_global"] == {}


def test_single_year_single_format():
    proc = DataProcessor()
    _seed(proc, [
        ("A", "20000101", "RPS_2024.txt", "RPS"),
        ("B", "19800505", "RPS_2024.txt", "RPS"),
        ("C", "19950312", "RPS_2024.txt", "RPS"),
    ])
    out = proc.compute_active_population()
    assert out["years"] == ["2024"]
    assert out["by_year_global"]["2024"] == 3
    assert out["by_year_field"]["2024"]["PSY"] == 3
    assert out["by_year_format"]["2024"]["RPS"] == 3


def test_same_ipp_multiple_formats_same_year_counted_once_globally():
    # A est vu en RPS (PSY hospit) ET EDGAR (PSY ambu) en 2024.
    # Global 2024 = 1 (dé-doublonné). PSY 2024 = 1. RPS = 1, EDGAR = 1.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "20000101", "RPS_2024.txt", "RPS"),
        ("A", "20000101", "EDGAR_2024.txt", "EDGAR"),
    ])
    out = proc.compute_active_population()
    assert out["by_year_global"]["2024"] == 1
    assert out["by_year_field"]["2024"]["PSY"] == 1
    assert out["by_year_format"]["2024"]["RPS"] == 1
    assert out["by_year_format"]["2024"]["EDGAR"] == 1


def test_same_ipp_spans_multiple_years_counted_per_year():
    # B est suivi 3 ans de suite : compte 1 par an, pas 3 en 2024.
    proc = DataProcessor()
    _seed(proc, [
        ("B", "19800505", "RPS_2022.txt", "RPS"),
        ("B", "19800505", "RPS_2023.txt", "RPS"),
        ("B", "19800505", "RPS_2024.txt", "RPS"),
    ])
    out = proc.compute_active_population()
    assert out["years"] == ["2022", "2023", "2024"]
    for y in ["2022", "2023", "2024"]:
        assert out["by_year_global"][y] == 1


def test_cross_field_mixing_psy_ssr_had():
    # Patient partagé entre champs (prise en charge HAD puis hospit PSY).
    proc = DataProcessor()
    _seed(proc, [
        ("X", "19700101", "RPS_2024.txt", "RPS"),        # PSY
        ("X", "19700101", "RHS_2024.txt", "RHS"),        # SSR
        ("X", "19700101", "RPSS_2024.txt", "RPSS"),      # HAD
        ("Y", "19800101", "RPS_2024.txt", "RPS"),        # PSY uniquement
    ])
    out = proc.compute_active_population()
    assert out["by_year_global"]["2024"] == 2  # X + Y dé-doublonné
    assert out["by_year_field"]["2024"]["PSY"] == 2  # X et Y
    assert out["by_year_field"]["2024"]["SSR"] == 1  # X seul
    assert out["by_year_field"]["2024"]["HAD"] == 1  # X seul


def test_filename_without_year_is_skipped():
    # Un fichier sans année dans son nom ne contribue à aucune file active
    # (mais reste présent dans le MPI global).
    proc = DataProcessor()
    _seed(proc, [
        ("A", "20000101", "RPS.txt", "RPS"),              # pas d'année
        ("B", "19800505", "RPS_2024.txt", "RPS"),         # année OK
    ])
    out = proc.compute_active_population()
    assert out["years"] == ["2024"]
    assert out["by_year_global"]["2024"] == 1
    # L'IPP A est quand même dans le MPI → comptabilisé dans total_unique_ipp
    assert out["total_unique_ipp"] == 2


def test_year_extraction_handles_various_naming_patterns():
    # Couvre les conventions de nommage usuelles : "_2024", "-2024",
    # "2024-", préfixe UM, suffixe, etc.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "D", "RPS_2023.txt", "RPS"),
        ("B", "D", "RPS-2024-v2.txt", "RPS"),
        ("C", "D", "UM3_RPS_2024.txt", "RPS"),
        ("D", "D", "2025_export_final.txt", "RPS"),
    ])
    out = proc.compute_active_population()
    assert set(out["years"]) == {"2023", "2024", "2025"}
    assert out["by_year_global"]["2024"] == 2  # B + C


def test_ipp_with_multiple_ddn_still_counted_once():
    # Même patient avec collision DDN : file active compte 1, pas 2.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "20000101", "RPS_2024.txt", "RPS"),
        ("A", "20000102", "RAA_2024.txt", "RAA"),  # collision DDN même IPP
    ])
    out = proc.compute_active_population()
    assert out["by_year_global"]["2024"] == 1

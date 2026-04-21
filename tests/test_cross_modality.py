# Tests pour get_cross_modality_patients() — parcours PSY cross-recueils.
# Scénarios métier réels : patient hospit + CMP, patient uniquement hospit,
# patient partagé entre champs PSY / SSR, dé-doublonnage source multi-fichiers.

from backend.data_processor import DataProcessor


def _seed(proc: DataProcessor, entries):
    for ipp, ddn, src, fmt in entries:
        proc.mpi.setdefault(ipp, {"pivot": None, "history": {}})
        proc.mpi[ipp]["history"].setdefault(ddn, []).append(src)
        proc.file_stats[src] = {
            "format": fmt,
            "lines_total": 1,
            "lines_valid": 1,
            "lines_filtered": 0,
        }


def test_no_patients_no_results():
    assert DataProcessor().get_cross_modality_patients() == []


def test_patient_single_format_excluded():
    # Patient vu uniquement en RPS → exclu (min_formats=2 par défaut).
    proc = DataProcessor()
    _seed(proc, [
        ("A", "20000101", "RPS_2024.txt", "RPS"),
        ("A", "20000101", "RPS_2023.txt", "RPS"),
    ])
    assert proc.get_cross_modality_patients() == []


def test_patient_cross_hospit_ambu_included():
    # Patient vu en RPS (hospit) + EDGAR (CMP) → parcours cross-modalités.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "20000101", "RPS_2024.txt", "RPS"),
        ("A", "20000101", "EDGAR_2024.txt", "EDGAR"),
    ])
    out = proc.get_cross_modality_patients()
    assert len(out) == 1
    entry = out[0]
    assert entry["ipp"] == "A"
    assert set(entry["formats"]) == {"RPS", "EDGAR"}
    assert entry["fields"] == ["PSY"]
    assert entry["years"] == ["2024"]
    assert entry["sources_count"] == 2


def test_sorting_by_most_modalities_first():
    proc = DataProcessor()
    # A : 3 modalités, B : 2, C : 1 (exclu)
    _seed(proc, [
        ("A", "D", "RPS_2024.txt", "RPS"),
        ("A", "D", "EDGAR_2024.txt", "EDGAR"),
        ("A", "D", "RPSS_2024.txt", "RPSS"),
        ("B", "D", "RPS_2024.txt", "RPS"),
        ("B", "D", "RAA_2024.txt", "RAA"),
        ("C", "D", "RPS_2024.txt", "RPS"),
    ])
    out = proc.get_cross_modality_patients()
    assert [p["ipp"] for p in out] == ["A", "B"]
    assert len(out[0]["formats"]) == 3


def test_cross_field_patient_psy_had():
    # Patient PSY avec épisode HAD → fields contient PSY et HAD.
    proc = DataProcessor()
    _seed(proc, [
        ("X", "D", "RPS_2024.txt", "RPS"),         # PSY
        ("X", "D", "RPSS_2024.txt", "RPSS"),       # HAD
    ])
    out = proc.get_cross_modality_patients()
    assert len(out) == 1
    assert set(out[0]["fields"]) == {"PSY", "HAD"}


def test_min_formats_parameter():
    # Avec min_formats=3, seuls les patients en 3+ formats passent.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "D", "RPS_2024.txt", "RPS"),
        ("A", "D", "EDGAR_2024.txt", "EDGAR"),     # 2 formats
        ("B", "D", "RPS_2024.txt", "RPS"),
        ("B", "D", "EDGAR_2024.txt", "EDGAR"),
        ("B", "D", "RPSS_2024.txt", "RPSS"),       # 3 formats
    ])
    out = proc.get_cross_modality_patients(min_formats=3)
    assert [p["ipp"] for p in out] == ["B"]


def test_limit_parameter():
    proc = DataProcessor()
    # 5 patients avec 2 formats chacun.
    for i in range(5):
        _seed(proc, [
            (f"P{i}", "D", "RPS_2024.txt", "RPS"),
            (f"P{i}", "D", "EDGAR_2024.txt", "EDGAR"),
        ])
    out = proc.get_cross_modality_patients(limit=3)
    assert len(out) == 3


def test_unknown_format_not_counted():
    # Les formats INCONNU ne comptent pas comme modalité.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "D", "unknown.txt", "INCONNU"),
        ("A", "D", "RPS_2024.txt", "RPS"),
    ])
    # Un seul format valide → exclu (min_formats=2).
    assert proc.get_cross_modality_patients() == []


def test_multi_year_journey():
    # Patient suivi sur plusieurs années : years agrège tout.
    proc = DataProcessor()
    _seed(proc, [
        ("A", "D", "RPS_2022.txt", "RPS"),
        ("A", "D", "EDGAR_2023.txt", "EDGAR"),
        ("A", "D", "RPSS_2024.txt", "RPSS"),
    ])
    out = proc.get_cross_modality_patients()
    assert out[0]["years"] == ["2022", "2023", "2024"]

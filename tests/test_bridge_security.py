"""
Tests for bridge.py import endpoint extension allowlist.

Without these checks, any bearer-token holder could read arbitrary files
(e.g. /etc/shadow, private keys) by passing an arbitrary path to
/api/import-csv or /api/import-excel.
"""
import os
import pytest
from backend.bridge import create_app, _ext_ok, _CSV_EXTS, _EXCEL_EXTS


@pytest.fixture
def client():
    # BRIDGE_TOKEN defaults to "" (env not set) -> auth disabled in tests.
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestExtOk:
    def test_csv_ext_accepted(self):
        assert _ext_ok("/data/patients.csv", _CSV_EXTS)

    def test_txt_ext_accepted(self):
        assert _ext_ok("/data/export.TXT", _CSV_EXTS)

    def test_tsv_ext_accepted(self):
        assert _ext_ok("/data/file.tsv", _CSV_EXTS)

    def test_json_ext_rejected_from_csv(self):
        assert not _ext_ok("/etc/secrets.json", _CSV_EXTS)

    def test_no_ext_rejected_from_csv(self):
        assert not _ext_ok("/etc/passwd", _CSV_EXTS)

    def test_xlsx_ext_accepted(self):
        assert _ext_ok("/data/report.xlsx", _EXCEL_EXTS)

    def test_xls_ext_accepted(self):
        assert _ext_ok("/data/old.XLS", _EXCEL_EXTS)

    def test_ods_ext_accepted(self):
        assert _ext_ok("/data/calc.ods", _EXCEL_EXTS)

    def test_csv_ext_rejected_from_excel(self):
        assert not _ext_ok("/data/file.csv", _EXCEL_EXTS)


class TestImportCsvExtension:
    def test_valid_csv_accepted(self, client, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("col1;col2\nval1;val2\n")
        r = client.post("/api/import-csv", json={"path": str(f)})
        assert r.status_code == 200

    def test_valid_txt_accepted(self, client, tmp_path):
        f = tmp_path / "export.txt"
        f.write_text("col1;col2\nval1;val2\n")
        r = client.post("/api/import-csv", json={"path": str(f)})
        assert r.status_code == 200

    def test_json_extension_rejected(self, client, tmp_path):
        f = tmp_path / "config.json"
        f.write_text('{"key": "value"}')
        r = client.post("/api/import-csv", json={"path": str(f)})
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_no_extension_rejected(self, client, tmp_path):
        f = tmp_path / "passwd"
        f.write_bytes(b"root:x:0:0:root:/root:/bin/bash\n")
        r = client.post("/api/import-csv", json={"path": str(f)})
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_py_extension_rejected(self, client, tmp_path):
        f = tmp_path / "secret.py"
        f.write_text("API_KEY = 'hardcoded'")
        r = client.post("/api/import-csv", json={"path": str(f)})
        assert r.status_code == 400


class TestImportExcelExtension:
    def test_xlsx_accepted(self, client, tmp_path):
        f = tmp_path / "data.xlsx"
        # Minimal fake xlsx (openpyxl will fail, but extension check passes)
        f.write_bytes(b"PK\x03\x04")
        r = client.post("/api/import-excel", json={"path": str(f)})
        data = r.get_json()
        # Extension check passes; openpyxl raises an error -> 400 or 500, not "Extension"
        assert "Extension non autorisee" not in data.get("error", "")

    def test_xml_extension_rejected(self, client, tmp_path):
        f = tmp_path / "config.xml"
        f.write_text("<root><secret>value</secret></root>")
        r = client.post("/api/import-excel", json={"path": str(f)})
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_csv_extension_rejected_for_excel(self, client, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("col1;col2\nval1;val2\n")
        r = client.post("/api/import-excel", json={"path": str(f)})
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")


class TestChartFromExcelExtension:
    def test_json_extension_rejected(self, client, tmp_path):
        f = tmp_path / "secrets.json"
        f.write_text('{"key": "value"}')
        r = client.post(
            "/api/chart-from-excel",
            json={"path": str(f), "label": "Month", "value": "Count"},
        )
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_xlsx_path_passes_extension_check(self, client, tmp_path):
        f = tmp_path / "report.xlsx"
        f.write_bytes(b"PK\x03\x04")
        r = client.post(
            "/api/chart-from-excel",
            json={"path": str(f), "label": "Month", "value": "Count"},
        )
        data = r.get_json()
        # Extension check passes; openpyxl or read failure gives a different error
        assert "Extension non autorisee" not in data.get("error", "")

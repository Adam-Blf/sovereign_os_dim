import pytest

import backend.bridge as _bridge
from backend.bridge import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(_bridge, "BRIDGE_TOKEN", "")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _post(client, path):
    return client.post("/api/structure", json={"path": path})


class TestStructureExtensionGuard:
    def test_csv_passes_guard(self, client, tmp_path):
        p = tmp_path / "struct.csv"
        p.write_text("LEVEL;CODE;PARENT;LABEL\n")
        r = _post(client, str(p))
        assert r.status_code != 400

    def test_tsv_passes_guard(self, client, tmp_path):
        p = tmp_path / "struct.tsv"
        p.write_text("LEVEL\tCODE\tPARENT\tLABEL\n")
        r = _post(client, str(p))
        assert r.status_code != 400

    def test_txt_rejected(self, client, tmp_path):
        p = tmp_path / "notes.txt"
        p.write_text("some content")
        r = _post(client, str(p))
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_no_extension_rejected(self, client, tmp_path):
        p = tmp_path / "passwd"
        p.write_text("root:x:0:0:root:/root:/bin/bash")
        r = _post(client, str(p))
        assert r.status_code == 400

    def test_json_rejected(self, client, tmp_path):
        p = tmp_path / "config.json"
        p.write_text('{"key": "value"}')
        r = _post(client, str(p))
        assert r.status_code == 400

    def test_xlsx_rejected(self, client, tmp_path):
        p = tmp_path / "tableau.xlsx"
        p.write_bytes(b"PK\x03\x04")
        r = _post(client, str(p))
        assert r.status_code == 400

    def test_uppercase_csv_passes(self, client, tmp_path):
        p = tmp_path / "STRUCT.CSV"
        p.write_text("LEVEL;CODE;PARENT;LABEL\n")
        r = _post(client, str(p))
        assert r.status_code != 400

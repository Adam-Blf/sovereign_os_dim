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


def _inspect(client, path):
    return client.post("/api/inspect", json={"path": path})


def _export(client, path):
    return client.post("/api/export-sanitized", json={"path": path, "output_dir": "/tmp"})


class TestInspectExtensionGuard:
    def test_txt_passes_guard(self, client, tmp_path):
        p = tmp_path / "rps.txt"
        p.write_text("A" * 154 + "\n")
        r = _inspect(client, str(p))
        assert r.status_code in {200, 404}

    def test_csv_rejected(self, client, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("col1,col2\n")
        r = _inspect(client, str(p))
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_py_rejected(self, client, tmp_path):
        p = tmp_path / "exploit.py"
        p.write_text("print('hello')\n")
        r = _inspect(client, str(p))
        assert r.status_code == 400

    def test_no_extension_rejected(self, client, tmp_path):
        p = tmp_path / "passwd"
        p.write_text("root:x:0:0:root:/root:/bin/bash\n")
        r = _inspect(client, str(p))
        assert r.status_code == 400

    def test_uppercase_txt_passes(self, client, tmp_path):
        p = tmp_path / "RPS.TXT"
        p.write_text("A" * 154 + "\n")
        r = _inspect(client, str(p))
        assert r.status_code in {200, 404}

    def test_non_string_path_rejected(self, client):
        r = client.post("/api/inspect", json={"path": 42})
        assert r.status_code == 400


class TestExportSanitizedExtensionGuard:
    def test_txt_passes_guard(self, client, tmp_path):
        p = tmp_path / "rps.txt"
        p.write_text("A" * 154 + "\n")
        r = _export(client, str(p))
        assert r.status_code in {200, 404, 500}

    def test_csv_rejected(self, client, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("col1,col2\n")
        r = _export(client, str(p))
        assert r.status_code == 400
        assert "Extension" in r.get_json().get("error", "")

    def test_no_extension_rejected(self, client, tmp_path):
        p = tmp_path / "private_key"
        p.write_text("-----BEGIN RSA PRIVATE KEY-----\n")
        r = _export(client, str(p))
        assert r.status_code == 400

    def test_json_rejected(self, client, tmp_path):
        p = tmp_path / "config.json"
        p.write_text('{"key": "value"}\n')
        r = _export(client, str(p))
        assert r.status_code == 400

    def test_uppercase_txt_passes(self, client, tmp_path):
        p = tmp_path / "EXPORT.TXT"
        p.write_text("A" * 154 + "\n")
        r = _export(client, str(p))
        assert r.status_code in {200, 404, 500}

    def test_non_string_path_rejected(self, client):
        r = client.post("/api/export-sanitized", json={"path": {"evil": "payload"}, "output_dir": "/tmp"})
        assert r.status_code == 400

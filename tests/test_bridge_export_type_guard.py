import sys
import os
import json

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.bridge import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# /api/export · output_dir type guard
# ---------------------------------------------------------------------------

class TestExportOutputDirTypeGuard:
    def test_string_output_dir_not_rejected_by_guard(self, client, tmp_path):
        # With no current_files the request hits the "Aucun fichier" gate,
        # but the type guard must have passed (no 400 from the guard).
        r = client.post(
            "/api/export",
            data=json.dumps({"output_dir": str(tmp_path)}),
            content_type="application/json",
        )
        # 400 is acceptable here (no files loaded), but the error must NOT
        # be the type-guard message.
        assert r.status_code in (200, 400)
        if r.status_code == 400:
            assert b"must be a string" not in r.data

    def test_dict_output_dir_rejected_with_400(self, client):
        r = client.post(
            "/api/export",
            data=json.dumps({"output_dir": {"path": "/tmp"}}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "string" in body.get("error", "").lower()

    def test_list_output_dir_rejected_with_400(self, client):
        r = client.post(
            "/api/export",
            data=json.dumps({"output_dir": ["/tmp"]}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "string" in body.get("error", "").lower()

    def test_int_output_dir_rejected_with_400(self, client):
        r = client.post(
            "/api/export",
            data=json.dumps({"output_dir": 42}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "string" in body.get("error", "").lower()

    def test_null_output_dir_passes_type_guard(self, client):
        # null (None) is the "not provided" case and must not be rejected by
        # the type guard - the existing fallback logic handles it.
        r = client.post(
            "/api/export",
            data=json.dumps({"output_dir": None}),
            content_type="application/json",
        )
        assert r.status_code in (200, 400)
        if r.status_code == 400:
            assert b"must be a string" not in r.data


# ---------------------------------------------------------------------------
# /api/export-sanitized · output_dir type guard
# ---------------------------------------------------------------------------

class TestExportSanitizedOutputDirTypeGuard:
    def test_string_output_dir_not_rejected_by_guard(self, client, tmp_path):
        # "path" is required; send a dummy path so we reach the output_dir check.
        r = client.post(
            "/api/export-sanitized",
            data=json.dumps({"path": "dummy.txt", "output_dir": str(tmp_path)}),
            content_type="application/json",
        )
        # May fail for other reasons (file not found) but not type guard.
        assert r.status_code in (200, 400, 404, 500)
        assert b"must be a string" not in r.data

    def test_dict_output_dir_rejected_with_400(self, client):
        r = client.post(
            "/api/export-sanitized",
            data=json.dumps({"path": "dummy.txt", "output_dir": {"x": 1}}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "string" in body.get("error", "").lower()

    def test_list_output_dir_rejected_with_400(self, client):
        r = client.post(
            "/api/export-sanitized",
            data=json.dumps({"path": "dummy.txt", "output_dir": ["/tmp"]}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "string" in body.get("error", "").lower()

    def test_int_output_dir_rejected_with_400(self, client):
        r = client.post(
            "/api/export-sanitized",
            data=json.dumps({"path": "dummy.txt", "output_dir": 0}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "string" in body.get("error", "").lower()

    def test_null_output_dir_passes_type_guard(self, client):
        r = client.post(
            "/api/export-sanitized",
            data=json.dumps({"path": "dummy.txt", "output_dir": None}),
            content_type="application/json",
        )
        assert r.status_code in (200, 400, 404, 500)
        assert b"must be a string" not in r.data

    def test_missing_path_still_returns_400(self, client):
        r = client.post(
            "/api/export-sanitized",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "path" in body.get("error", "").lower()
